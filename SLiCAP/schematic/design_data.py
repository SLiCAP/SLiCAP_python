"""Design-data manifest (SLNG.md "Design data panel", 2026-07-11).

The instruction runner writes ``results/design_data.json`` after every run:
the generated ``main.py`` imports the instruction file as a module and then
calls :func:`write_manifest` on the module's namespace. The Design data
panel only READS the manifest (:func:`read_manifest`).

Files stay the source of truth (ACDE.md): the manifest is a rebuildable
index — variable name, runtime type, preview data, artifact pointer — and
is never the only holder of design information. Sympy content persists as
``srepr`` (re-parseable text) plus the rendered LaTeX string, NEVER as
pickles. Figures need no persistence of their own: every plot is saved to
the img folder anyway.

Manifest structure (one per project, sections keyed by instruction file)::

    {"version": 1,
     "sections": {
        "GUItest.py": {
            "hash": "<sha1 of the source at run time>",
            "timestamp": <epoch seconds>,
            "variables": [
                {"name": "LAPLACE1", "kind": "result",
                 "class": "SLiCAPinstruction.instruction", ...preview...},
                ...]}}}

The per-section source hash gives the panel its staleness test: when the
current instruction file no longer hashes to the recorded value, the
section is shown greyed. Writes are atomic (temp file + rename), so two
runs cannot corrupt the manifest. This module must stay import-light on
the Qt side: no PySide imports here.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

MANIFEST_NAME = "design_data.json"

# Friendly type keys ("kinds") the view preferences filter on. Anything not
# classified below is reported as kind "other" with its class name, so the
# panel can COUNT it as hidden — nothing silently disappears — and the
# preferences can enable it once it is added there.
KNOWN_KINDS = ["result", "circuit", "figure", "traces", "expression",
               "matrix", "snippet", "number", "array", "list", "text",
               "other"]

# Result attributes worth exposing as expandable children of a result
# entry (Anton, 2026-07-12: the reference documents these per instruction
# under "Return value attributes" — e.g. doPZ → poles, zeros, DCvalue).
# Only attributes with a non-empty value are listed.
_RESULT_ATTRS = ["laplace", "numer", "denom", "poles", "zeros", "DCvalue",
                 "dc", "dcSolve", "onoise", "inoise", "ovar", "ivar",
                 "time", "impulse", "stepResp", "solve", "M", "Iv", "Dv"]


def _class_name(value) -> str:
    c = type(value)
    return f"{c.__module__}.{c.__qualname__}"


def classify(value) -> str:
    """Friendly type key of an instruction-file variable."""
    import sympy as sp
    import numpy as np
    cname = _class_name(value)
    if cname.endswith("SLiCAPinstruction.instruction"):
        return "result"
    if cname.endswith("SLiCAPprotos.circuit"):
        return "circuit"
    if cname.endswith("SLiCAPplots.figure"):
        return "figure"
    if cname.endswith("SLiCAPprotos.Snippet"):
        return "snippet"
    if isinstance(value, dict) and value and all(
            _class_name(v).endswith("SLiCAPplots.trace")
            for v in value.values()):
        return "traces"
    if isinstance(value, sp.MatrixBase):
        return "matrix"
    if isinstance(value, sp.Basic):
        return "expression"
    if isinstance(value, bool):
        return "other"
    if isinstance(value, (int, float, complex)):
        return "number"
    if isinstance(value, np.ndarray):
        return "array"
    if isinstance(value, (list, tuple)):
        return "list"
    if isinstance(value, str):
        return "text"
    return "other"


def _slicap_latex(expr) -> str:
    """LaTeX via SLiCAP's own chokepoint (engineering notation + IEEE
    upright subscripts — the same typesetting as the schematic labels);
    plain sympy.latex as fallback. Raw sympy would print numeric
    coefficients as giant exact rationals."""
    import sympy as sp
    try:
        from SLiCAP.SLiCAPhtml import _latex_ENG
        from SLiCAP.SLiCAPlatex import sub2rm
        s = _latex_ENG(expr)
        return sub2rm(s) if s else sp.latex(expr)
    except Exception:
        return sp.latex(expr)


def _sympy_preview(expr) -> dict:
    import sympy as sp
    # LaTeX math must stay WHOLE. Truncating it mid-expression breaks brace
    # balance, so pdflatex aborts with "File ended while scanning \frac" and
    # the data viewer cannot typeset it — even though the HTML report renders
    # the same (full) string with MathJax. Keep the latex complete; only for a
    # pathologically large expression drop it entirely, so the viewer falls
    # back to the pprint text cleanly instead of to invalid LaTeX. (pprint and
    # srepr are plain text — truncating those is harmless.)
    latex = _slicap_latex(expr)
    if len(latex) > 200_000:
        latex = ""
    return {"pprint": sp.pretty(sp.N(expr, 4))[:2000],
            "latex":  latex,
            "srepr":  sp.srepr(expr)[:5000]}


def _preview(value, kind: str) -> dict:
    """Kind-specific preview data for the manifest; must stay JSON-safe."""
    import sympy as sp
    try:
        if kind in ("expression", "matrix"):
            return _sympy_preview(value)
        if kind == "result":
            out = {}
            for attr in ("dataType", "gainType", "detLabel", "simType"):
                v = getattr(value, attr, None)
                if isinstance(v, str):
                    out[attr] = v
            out["step"] = bool(getattr(value, "step", False))
            expr = getattr(value, "laplace", None)
            if isinstance(expr, sp.Basic):
                out.update(_sympy_preview(expr))
            # expandable children: all non-empty return-value attributes
            # (Anton, 2026-07-12 — poles/zeros/DCvalue etc. of a doPZ)
            out["attributes"] = _attr_entries(value)
            return out
        if kind == "snippet":
            return {"value": str(getattr(value, "snippet", value))[:5000],
                    "format": str(getattr(value, "format", "")),
                    "path": str(getattr(value, "saved_path", ""))}
        if kind == "list":
            items = list(value)[:6]
            parts = []
            for it in items:
                if isinstance(it, sp.Basic):
                    parts.append(sp.pretty(sp.N(it, 4)))
                else:
                    parts.append(repr(it))
            if len(value) > 6:
                parts.append(f"… ({len(value)} items in total)")
            return {"value": f"{len(value)} items",
                    "pprint": "\n".join(parts)[:2000]}
        if kind == "figure":
            return {"fileName": getattr(value, "fileName", ""),
                    "fileType": getattr(value, "fileType", ""),
                    "traces": list(getattr(value, "traceDict", {}))[:100]}
        if kind == "traces":
            return {"labels": list(value)[:100]}
        if kind == "number":
            return {"value": repr(value)}
        if kind == "array":
            import numpy as np
            return {"shape": list(value.shape), "dtype": str(value.dtype),
                    "pprint": np.array2string(value, precision=4,
                                              threshold=24)[:2000]}
        if kind == "text":
            return {"value": value[:500]}
    except Exception as e:               # preview must never kill the run
        return {"error": str(e)[:200]}
    return {}


def _attr_entries(result) -> list[dict]:
    """Child entries for a result's non-empty return-value attributes."""
    out = []
    # NGspice results carry their result DICT on the instruction's
    # <dataType> slot ({signal: scalar | array}, incl. the sweep vector) —
    # expose every signal as a child row (Anton, 2026-07-12: "where does
    # the result dictionary go?"). SLiCAP results are unaffected: their
    # dataType slots hold sympy objects, not dicts.
    data_type = getattr(result, "dataType", "")
    sig_dict = getattr(result, data_type, None) if data_type else None
    if isinstance(sig_dict, dict):
        for name, v in sig_dict.items():
            kind = classify(v)
            entry = {"name": str(name), "kind": kind, "class": _class_name(v)}
            entry.update(_preview(v, kind))
            out.append(entry)
    # Fourier harmonics table (sl.tran(..., fourier=…)): attached NEXT TO
    # the time-domain result on instr.fourier — mag/phase/normalized arrays
    # per harmonic + THD scalars (build-order items 3/4, 2026-07-12).
    four = getattr(result, "fourier", None)
    if isinstance(four, dict):
        for name, v in four.items():
            kind = classify(v)
            entry = {"name": f"fourier: {name}", "kind": kind,
                     "class": _class_name(v)}
            entry.update(_preview(v, kind))
            if isinstance(v, str):
                # the verbatim harmonics table: keep it whole (the generic
                # text preview caps at 500 chars)
                entry["value"] = v[:5000]
            out.append(entry)
    for attr in _RESULT_ATTRS:
        v = getattr(result, attr, None)
        if v is None:
            continue
        if isinstance(v, (list, tuple, dict)) and not v:
            continue
        kind = classify(v)
        entry = {"name": attr, "kind": kind, "class": _class_name(v)}
        entry.update(_preview(v, kind))
        out.append(entry)
    return out


def _source_hash(path: Path) -> str:
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def variables_of(namespace: dict) -> list[dict]:
    """Manifest entries for the plottable/viewable variables of an executed
    instruction-file namespace. Dunders, modules, callables and classes are
    not design data and are skipped entirely."""
    import types
    out = []
    for name, value in namespace.items():
        if name.startswith("_"):
            continue
        if isinstance(value, (types.ModuleType, types.FunctionType,
                              types.BuiltinFunctionType, type)):
            continue
        if value is None:
            continue
        kind = classify(value)
        entry = {"name": name, "kind": kind, "class": _class_name(value)}
        entry.update(_preview(value, kind))
        out.append(entry)
    return out


def manifest_path(results_dir=None) -> Path:
    if results_dir is None:
        import SLiCAP.SLiCAPconfigure as ini
        results_dir = ini.results_path
    return Path(results_dir) / MANIFEST_NAME


def read_manifest(results_dir=None) -> dict:
    """The manifest, or an empty skeleton when none exists / unreadable."""
    path = manifest_path(results_dir)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("sections"), dict):
            return data
    except (OSError, ValueError):
        pass
    return {"version": 1, "sections": {}}


def write_manifest(namespace: dict, source_name: str,
                   results_dir=None, source_dir=None) -> Path:
    """Merge one instruction file's section into the project manifest.

    Called by the generated ``main.py`` after importing the instruction
    file: ``write_manifest(vars(GUItest), "GUItest.py")``. *results_dir*
    and *source_dir* default to the project's results path and the current
    working directory (main.py runs from the project root).
    """
    path = manifest_path(results_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    src = Path(source_dir or os.getcwd()) / source_name
    data = read_manifest(results_dir)
    data["sections"][source_name] = {
        "hash": _source_hash(src),
        "timestamp": time.time(),
        "variables": variables_of(namespace),
    }
    # atomic: two runs must not corrupt the manifest
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def section_is_stale(section: dict, source_path: Path) -> bool:
    """True when the instruction file changed since the recorded run."""
    return _source_hash(Path(source_path)) != section.get("hash", "")
