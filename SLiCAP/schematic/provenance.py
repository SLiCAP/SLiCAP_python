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


def poster_children(path) -> list:
    """The drawings a poster shows, as source files: the schematics and
    posters its link items name (a schematic by its source path in sch/ or
    lib/, a poster by name in posters/), those that exist. A schematic
    has none."""
    import json
    from . import project
    path = Path(path)
    if path.suffix.lower() != project.POSTER_SUFFIX:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    root = project.root_for(path)
    out = []
    for img in data.get("images", []) or []:
        link = img.get("link", "") if isinstance(img, dict) else ""
        kind, _, name = link.partition(":")
        child = None
        if kind == "schematic":
            child = project.schematic_file_for(name, root)
        elif kind == "poster":
            child = project.poster_file_for(name, root)
        if child is not None and child not in out:
            out.append(child)
    return out


def poster_contains(path, target) -> bool:
    """True when the poster *path* shows *target* directly or through nested
    posters, or IS it: the guard against a poster containing itself (Anton,
    2026-10-06: "a poster can include other posters")."""
    path, target = Path(path).resolve(), Path(target).resolve()
    seen = set()
    stack = [path]
    while stack:
        p = stack.pop()
        if p == target:
            return True
        if p in seen:
            continue
        seen.add(p)
        stack.extend(c.resolve() for c in poster_children(p))
    return False


def own_exports(sch_path) -> set:
    """The schematic's own export images, which it must never link: a link
    to its own output would make the export its own input, stale on every
    run and nested in every export (Anton, 2026-10-06)."""
    from . import project
    sch_path = Path(sch_path)
    img = project.folder("img", project.root_for(sch_path))
    return {(img / (sch_path.stem + ext)).resolve() for ext in (".svg", ".pdf")}


def linked_images(sch_path) -> list:
    """The files the schematic's links depend on: the images of image and
    Figure items, resolved from the project root, the schematic's own
    exports excluded, and the run manifest when a snippet item takes its
    text from it; [] when the file cannot be read."""
    import json
    from . import project
    try:
        data = json.loads(Path(sch_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    own = own_exports(sch_path)
    out = []
    for img in data.get("images", []) or []:
        fp = img.get("file_path") if isinstance(img, dict) else None
        if fp:
            p = project.resolve_from_root(fp, sch_path)
            if p.resolve() not in own:
                out.append(p)
    # a snippet item's text lives in the run manifest (Design data): a run
    # that changed it must re-export the schematic
    if any(isinstance(f, dict) and f.get("snippet")
           for f in data.get("latex_fragments", []) or []):
        from .design_data import manifest_path
        out.append(manifest_path(project.folder("results", project.root_for(sch_path))))
    return out


def source_mtime(sch_path: Path) -> float:
    """The newest modification time of the SOURCES of a drawing: the file
    itself, its style and frozen-symbols sidecars, the operating-point
    results it draws and the files it places by their file name. The
    images of a drawing are current when they are newer than this.

    The rule (Anton, 2026-10-21): an object placed by its file name
    follows that file, and with it what that file places. The frozen
    symbol cache defines the symbols, so a symbol library is no source,
    and an install of SLiCAP changes no source either: an image changes
    only when its drawing changes (``force=True`` exports on request).
    Counting the libraries and the package for the images as well, so
    that an install re-exported every image once (2026-09-13), was
    REVERTED for that reason. A netlist still counts them: see
    input_mtime."""
    from . import project
    sch_path = Path(sch_path)
    candidates = [sch_path,
                  project.ini_path_for(sch_path),
                  project.symbols_path_for(sch_path)]
    # The operating-point results drawn on an NGspice schematic (bias
    # annotations): a newer sl.op() run re-exports the image (2026-09-21).
    candidates.append(project.subdir_for(sch_path, "cir")
                      / (sch_path.stem + "_op.raw"))
    # The images the schematic links (a plot written by the simulation):
    # the export inlines their content, so a newer plot re-exports the
    # schematic (Anton, 2026-10-06). Without this a run that rewrote the
    # plots left the exported schematic current and stale.
    candidates += linked_images(sch_path)
    return _newest(candidates)


def input_mtime(sch_path: Path) -> float:
    """The newest modification time of everything a NETLIST depends on:
    the sources of the drawing (source_mtime), the symbol libraries
    (system and project) and the schematic package itself. A netlist is
    derived by SLiCAP's netlister, so an install or a symbol change
    rebuilds every netlist once: a netlister fix must reach it."""
    from . import project
    sch_path = Path(sch_path)
    here = Path(__file__).parent
    kind = "ngspice" if sch_path.suffix.lower() == ".spice_sch" else "slicap"
    candidates = list((here.parent / "files" / "symbols" / kind).glob("*.svg"))
    candidates += list(here.glob("*.py"))
    lib = project.folder("lib", project.root_for(sch_path))
    if lib.is_dir():
        candidates += list(lib.glob("*"))
    return max(source_mtime(sch_path), _newest(candidates))


def _newest(paths) -> float:
    """The newest modification time of the files among *paths*, 0 for none."""
    newest = 0.0
    for p in paths:
        try:
            if p is not None and Path(p).is_file():
                newest = max(newest, Path(p).stat().st_mtime)
        except OSError:
            pass
    return newest
