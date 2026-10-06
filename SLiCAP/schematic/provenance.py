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
    posters its link items name (sch/<name>.slicap_sch or .spice_sch,
    posters/<name>.slicap_poster), those that exist. A schematic has none."""
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
    img = project.root_for(sch_path) / "img"
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
        out.append(manifest_path(project.root_for(sch_path) / "results"))
    return out


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
    # The images the schematic links (a plot written by the simulation):
    # the export inlines their content, so a newer plot re-exports the
    # schematic (Anton, 2026-10-06). Without this a run that rewrote the
    # plots left the exported schematic current and stale.
    candidates += linked_images(sch_path)
    newest = 0.0
    for p in candidates:
        try:
            if p is not None and Path(p).is_file():
                newest = max(newest, Path(p).stat().st_mtime)
        except OSError:
            pass
    return newest
