"""Provenance of exported schematic images, and the inputs they depend on.

An exported SVG carries a comment naming the schematic it was made from; an
exported PDF carries the same in its creator and subject fields. The
currency check of ``make_schematic`` requires both: a file that is merely
NEWER than the schematic is not enough, because an image written by another
tool (the KiCad path, an older SLiCAP) passes a date test and then hides a
missing export (Anton, 2026-09-13). No Qt import here: the check runs in
the caller's process, the export in a headless subprocess.
"""
from pathlib import Path

CREATOR = "SLiCAP schematic export"
_MARKER = "SLiCAP schematic export:"


def svg_marker(source: str) -> str:
    """The comment text written into an exported SVG."""
    from SLiCAP import __version__
    return " {0} {1}, SLiCAP {2} ".format(_MARKER, source, __version__)


def svg_source(path: Path) -> "str | None":
    """The schematic file name an SVG was exported from, or None when the
    file is not a SLiCAP schematic export."""
    try:
        head = Path(path).read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    pos = head.find(_MARKER)
    if pos < 0:
        return None
    rest = head[pos + len(_MARKER):].strip()
    return rest.split(",")[0].strip() or None


def pdf_is_export(path: Path) -> bool:
    """True when the PDF names SLiCAP's schematic export as its creator."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return False
    return CREATOR.encode("ascii") in data


def input_mtime(sch_path: Path) -> float:
    """The newest modification time of everything an export depends on:
    the schematic, its style and frozen-symbols sidecars, the symbol
    libraries (system and project) and the schematic package itself, so
    that an install or a symbol change re-exports every schematic once."""
    from . import project
    sch_path = Path(sch_path)
    candidates = [sch_path,
                  project.ini_path_for(sch_path),
                  project.symbols_path_for(sch_path)]
    here = Path(__file__).parent
    kind = "ngspice" if sch_path.suffix.lower() == ".spice_sch" else "slicap"
    candidates += list((here.parent / "files" / "symbols" / kind).glob("*.svg"))
    candidates += list(here.glob("*.py"))
    lib = project.root_for(sch_path) / "lib"
    if lib.is_dir():
        candidates += list(lib.glob("*"))
    # The operating-point results drawn on an NGspice schematic (bias
    # annotations): a newer sl.op() run re-exports the image (2026-09-21).
    candidates.append(project.subdir_for(sch_path, "cir")
                      / (sch_path.stem + "_op.raw"))
    newest = 0.0
    for p in candidates:
        try:
            if p is not None and Path(p).is_file():
                newest = max(newest, Path(p).stat().st_mtime)
        except OSError:
            pass
    return newest
