"""NGspice Nutmeg raw-file parser (Phase 4).

Reads the binary or ASCII Nutmeg format produced by:

    ngspice -b netlist.sp -r output.raw

Supports multiple analysis blocks in one file (e.g. ``.op`` followed
by ``.tran``).  No Qt dependency — safe for CLI use.

Public API::

    analyses = RawFile.load("output.raw")   # list[Analysis]

    a = analyses[0]
    a.name       # "Transient Analysis"
    a.x_name     # "time"
    a.x_data     # np.ndarray, shape (M,), always real
    a.signals    # {"v(out)": np.ndarray, ...}  complex for AC
    a.is_complex # True for AC / noise spectral density
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path


# ── data model ────────────────────────────────────────────────────────────────

@dataclass
class Analysis:
    """One analysis block from an NGspice raw file."""

    name:      str                       # "Transient Analysis", "AC Analysis", …
    x_name:    str                       # independent variable name ("time", "frequency")
    x_data:    np.ndarray                # shape (M,), real
    signals:   dict[str, np.ndarray]     # name → array shape (M,); complex for AC
    var_names: list[str] = field(default_factory=list)  # all names in file order

    def is_complex(self) -> bool:
        """True when signal arrays are complex (AC / noise spectral density)."""
        return any(np.iscomplexobj(v) for v in self.signals.values())


# ── parser ────────────────────────────────────────────────────────────────────

_BINARY_MARKER = b"Binary:"
_VALUES_MARKER = b"Values:"


def _find_raw_marker(raw: bytes, marker: bytes, start: int):
    """Find *marker* on its own line at/after *start*, tolerant of LF and CRLF
    (NGspice on Windows writes the raw header with CRLF, so ``b"Binary:\\n"``
    would miss ``Binary:\\r\\n`` — the Windows-only bias-annotation failure).
    Returns (marker_start, data_start), or (-1, -1) when absent."""
    pos = start
    while True:
        i = raw.find(marker, pos)
        if i == -1:
            return -1, -1
        end = i + len(marker)
        if end < len(raw) and raw[end:end + 1] in (b"\r", b"\n"):
            if raw[end:end + 1] == b"\r":
                end += 1
            if raw[end:end + 1] == b"\n":
                end += 1
            return i, end
        pos = i + len(marker)


class RawFile:
    """Static-method parser for NGspice Nutmeg raw files."""

    @staticmethod
    def load(path: str | Path) -> list[Analysis]:
        """Parse *path* and return all analysis blocks in file order."""
        raw = Path(path).read_bytes()
        analyses: list[Analysis] = []
        pos = 0
        while pos < len(raw):
            result = RawFile._parse_block(raw, pos)
            if result is None:
                break
            analysis, pos = result
            if analysis is not None:
                analyses.append(analysis)
        return analyses

    # ── internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_block(
        raw: bytes, start: int
    ) -> tuple[Analysis | None, int] | None:
        """Parse the next analysis block starting at byte offset *start*.

        Returns (Analysis, next_start) or None when no more blocks exist.
        """
        bi, bi_end = _find_raw_marker(raw, _BINARY_MARKER, start)
        vi, vi_end = _find_raw_marker(raw, _VALUES_MARKER, start)

        if bi == -1 and vi == -1:
            return None

        is_binary  = (bi != -1) and (vi == -1 or bi <= vi)
        marker_pos = bi if is_binary else vi
        marker_end = bi_end if is_binary else vi_end

        header_text = raw[start:marker_pos].decode("ascii", errors="replace")
        hdr = RawFile._parse_header(header_text)
        if not hdr:
            return None, marker_end

        plotname  = hdr.get("plotname", "Unknown")
        flags     = hdr.get("flags", "real").lower()
        n_vars    = int(hdr.get("no. of variables", 0))
        n_pts     = int(hdr.get("no. of points", 0))
        var_info  = hdr.get("variables", [])     # list of (name, kind)

        if n_vars == 0 or n_pts == 0:
            return None, marker_end

        is_complex = "complex" in flags

        if is_binary:
            analysis, next_pos = RawFile._read_binary(
                raw, marker_end, n_pts, n_vars, is_complex,
                plotname, var_info,
            )
        else:
            analysis, next_pos = RawFile._read_ascii(
                raw, marker_end, n_pts, n_vars, is_complex,
                plotname, var_info,
            )

        return analysis, next_pos

    @staticmethod
    def _parse_header(text: str) -> dict:
        """Parse the ASCII header block into a dict."""
        hdr: dict = {}
        in_vars   = False
        var_list:  list[tuple[str, str]] = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if in_vars:
                parts = stripped.split()
                if len(parts) >= 3:
                    # "  0  name  type"  (tabs or spaces)
                    var_list.append((parts[1], parts[2]))
                elif len(parts) == 2:
                    var_list.append((parts[1], ""))
                else:
                    # End of variables section (unexpected line)
                    in_vars = False
                continue

            if stripped.lower() == "variables:":
                in_vars = True
                continue

            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip().lower()
                val = val.strip()
                # Accept both "No. of Variables" (older Nutmeg) and
                # "No. Variables" (NGspice-42+); normalise to the same key.
                if key in ("no. of variables", "no. variables"):
                    try:
                        hdr["no. of variables"] = int(val)
                    except ValueError:
                        hdr["no. of variables"] = 0
                elif key in ("no. of points", "no. points"):
                    try:
                        hdr["no. of points"] = int(val)
                    except ValueError:
                        hdr["no. of points"] = 0
                else:
                    hdr[key] = val

        if var_list:
            hdr["variables"] = var_list

        return hdr

    @staticmethod
    def _read_binary(
        raw: bytes, data_start: int,
        n_pts: int, n_vars: int, is_complex: bool,
        plotname: str, var_info: list,
    ) -> tuple[Analysis | None, int]:
        """Read and reshape binary data; return (Analysis, next_byte_pos)."""
        elem_bytes = 16 if is_complex else 8
        data_size  = n_pts * n_vars * elem_bytes
        chunk      = raw[data_start : data_start + data_size]

        if len(chunk) < data_size:
            return None, len(raw)   # truncated file

        dtype  = np.complex128 if is_complex else np.float64
        matrix = np.frombuffer(chunk, dtype=dtype).reshape(n_pts, n_vars)

        return RawFile._build_analysis(plotname, var_info, matrix, n_vars), \
               data_start + data_size

    @staticmethod
    def _read_ascii(
        raw: bytes, data_start: int,
        n_pts: int, n_vars: int, is_complex: bool,
        plotname: str, var_info: list,
    ) -> tuple[Analysis | None, int]:
        """Read the ASCII Values: block.

        The format has one data point per indented block:
          0   <val0>
              <val1>
              ...
          1   <val0>
              ...
        """
        # Find the end of this block: next Title: header or EOF
        next_block = raw.find(b"Title:", data_start)
        end = next_block if next_block != -1 else len(raw)
        block = raw[data_start:end].decode("ascii", errors="replace")

        dtype  = np.complex128 if is_complex else np.float64
        matrix = np.zeros((n_pts, n_vars), dtype=dtype)
        pt     = -1
        col    = 0

        for line in block.splitlines():
            parts = line.split()
            if not parts:
                continue
            # Check if a new data point is starting (line has an integer index
            # as its first token, followed by a value)
            try:
                int(parts[0])
                # New data point
                pt  += 1
                col  = 0
                if pt >= n_pts:
                    break
                val_str = parts[1] if len(parts) > 1 else ""
            except ValueError:
                # Continuation line: the only token is the value
                val_str = parts[0] if parts else ""

            if not val_str:
                continue

            try:
                if is_complex:
                    # NGspice ASCII complex is "real,imag" (comma-separated), NOT
                    # Python's "real+imagj" — complex(val_str) raises here and the
                    # value would be silently dropped as 0.  This is the Windows
                    # bug: that build writes ASCII raws (Linux writes binary), so
                    # a stepped AC there parsed as all-zeros.
                    re_s, _, im_s = val_str.partition(",")
                    val = complex(float(re_s), float(im_s) if im_s else 0.0)
                else:
                    val = float(val_str)
            except ValueError:
                continue

            if pt >= 0 and col < n_vars:
                matrix[pt, col] = val
            col += 1

        return RawFile._build_analysis(plotname, var_info, matrix, n_vars), end

    @staticmethod
    def _build_analysis(
        plotname: str,
        var_info: list[tuple[str, str]],
        matrix: np.ndarray,
        n_vars: int,
    ) -> Analysis:
        """Assemble an Analysis from a parsed (n_pts, n_vars) matrix."""
        all_names = [info[0] for info in var_info] if var_info \
                    else [f"var{i}" for i in range(n_vars)]

        x_name = all_names[0] if all_names else ""
        x_data = matrix[:, 0].real.copy() if matrix.shape[1] > 0 else np.array([])

        signals: dict[str, np.ndarray] = {}
        for j in range(1, n_vars):
            name = all_names[j] if j < len(all_names) else f"var{j}"
            signals[name] = matrix[:, j].copy()

        return Analysis(
            name=plotname,
            x_name=x_name,
            x_data=x_data,
            signals=signals,
            var_names=all_names,
        )
