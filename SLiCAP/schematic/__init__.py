"""
SLiCAP schematic capture package.

GUI entry point:  slicap-schematic  (console script)
Python API:       from SLiCAP.schematic import make_schematic, export_images
"""

from pathlib import Path


def schematic_properties(sch_path):
    """The document properties of a schematic file (title, is_subcircuit,
    subcircuit_ports, ...), read from the JSON - no Qt involved."""
    from .schematic_data import SchematicData
    return SchematicData.load(Path(sch_path)).properties


def _netlist_output(sch_path: Path, title=None) -> Path:
    """The netlist file the export writes for ``sch_path``: cir/<stem>.cir
    for a circuit, lib/<name>.slicap_lib (or .spice_lib) for a subcircuit
    schematic, with <name> the given title, else the schematic's title,
    else its stem - the rule the CLI applies (Anton, 2026-09-16)."""
    from . import project
    if project.doc_type(sch_path) == "poster":
        return None                     # a poster is a drawing: no netlist
    props = schematic_properties(sch_path)
    if props.is_subcircuit:
        from .subcircuit import lib_path_for
        name = title or props.title or sch_path.stem
        sch_type = "ngspice" if sch_path.suffix.lower() == ".spice_sch" else "slicap"
        return lib_path_for(sch_path, name, sch_type)
    return project.subdir_for(sch_path, "cir") / sch_path.with_suffix(".cir").name


def _image_paths(sch_path: Path):
    """The SVG and PDF the image export writes for ``sch_path``, in the img
    folder of its own project."""
    from . import project
    img = project.subdir_for(sch_path, "img")
    return img / sch_path.with_suffix(".svg").name, img / sch_path.with_suffix(".pdf").name


def _current(outputs, since: float) -> bool:
    """True when every output exists and is not older than *since*, the
    newest input (Anton, 2026-07-16: an unchanged schematic is not
    re-exported on every dialog open). None entries are skipped (a poster
    writes no netlist)."""
    try:
        for out in outputs:
            if out is not None and (not out.exists() or out.stat().st_mtime < since):
                return False
    except OSError:
        return False
    return True


def _images_current(sch_path: Path) -> bool:
    """The SVG and PDF are newer than the sources of the drawing
    (provenance.source_mtime) and were exported by SLiCAP FROM THIS
    schematic (provenance markers; 2026-09-13: a newer image made by
    another tool, e.g. the KiCad path, does not count). A pure test: the
    editor asks it for the drawings on an open poster."""
    from .provenance import source_mtime, svg_source, pdf_is_export
    svg, pdf = _image_paths(sch_path)
    return (_current((svg, pdf), source_mtime(sch_path))
            and svg_source(svg) == sch_path.name and pdf_is_export(pdf))


def _netlist_current(sch_path: Path, title=None) -> bool:
    """The netlist is newer than its inputs (provenance.input_mtime). These
    include SLiCAP itself, so a netlister fix reaches every netlist."""
    from .provenance import input_mtime
    return _current((_netlist_output(sch_path, title),), input_mtime(sch_path))


def _outputs_current(sch_path: Path, title=None) -> "Path | None":
    """Return the netlist path (see _netlist_output), or the SVG for a
    poster, when the netlist, SVG and PDF are all current; else None."""
    if not (_images_current(sch_path) and _netlist_current(sch_path, title)):
        return None
    cir = _netlist_output(sch_path, title)
    return cir if cir is not None else _image_paths(sch_path)[0]


_exporting: set = set()      # posters whose children are being exported


def _export_children(sch_path: Path, force: bool) -> list:
    """A poster shows other drawings: their images are brought up to date
    first, children before parents, each once (a poster that contains itself
    through a chain is stopped here, the dialog refuses it too). Every
    drawing is tried. Returns (drawing, error) for each failed export."""
    from .provenance import poster_children
    if sch_path in _exporting:
        return []
    _exporting.add(sch_path)
    failed = []
    try:
        for child in poster_children(sch_path):
            failed += _update_images(Path(child).resolve(), force)
    finally:
        _exporting.discard(sch_path)
    return failed


def _update_images(sch_path: Path, force: bool) -> list:
    """Bring the images of one drawing up to date: the drawings a poster
    shows first, then its own, each only when out of date or *force*.
    Changes no state of the calling process. Returns (drawing, error) for
    each failed export. A drawing whose export failed keeps its images."""
    failed = _export_children(sch_path, force)
    if force or not _images_current(sch_path):
        try:
            _run_cli("images", sch_path)
        except RuntimeError as exc:
            failed.append((sch_path, str(exc)))
    return failed


def _failures(failed) -> str:
    """The error text of failed exports, one paragraph per drawing."""
    return "\n\n".join(f"{path.name}: {error}" for path, error in failed)


def update_drawings(paths) -> list:
    """Bring the images of the drawings *paths* up to date, each only when
    one of its sources changed (provenance.source_mtime), the drawings a
    poster shows first. For the editor: a poster shows its drawings by
    their file name, so it follows those files (Anton, 2026-10-21). Unlike
    ``export_images`` it changes no state of the editor, such as the
    current schematic and its log.

    :param paths: the source files of the drawings (schematics, posters).
    :returns:     (drawing, error) for each drawing whose export failed;
                  its old images stay.
    """
    failed = []
    for path in paths:
        failed += _update_images(Path(path).resolve(), False)
    return failed


def _run_cli(command: str, sch_path: Path, extra=()) -> None:
    """Run one command of SLiCAP.schematic.cli in a child process. The
    Qt-heavy scene rendering stays out of any calling thread that has no Qt
    event dispatcher (e.g. a GUI background worker), which would otherwise
    produce QBasicTimer warnings and could corrupt the parent application's
    display state."""
    import sys
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", command, str(sch_path)] + list(extra),
        capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # no console flash on Windows
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(f"Schematic export failed:\n{result.stderr or result.stdout}")


def export_images(sch_path, force=False) -> Path:
    """Export a schematic or poster to SVG and PDF, headlessly. The images
    are drawings: no netlist is built and the circuit is not checked, so a
    drawing that is not a valid circuit exports as well (Anton, 2026-10-11).
    A poster first exports the drawings it shows. The export is skipped when
    the images are newer than the sources of the drawing
    (provenance.source_mtime): an install of SLiCAP changes no source.

    :param sch_path: Path to the ``.slicap_sch``, ``.spice_sch`` or
                     ``.slicap_poster`` file.
    :param force:    True exports even when the images are current.
    :returns:        ``Path`` of the SVG.
    :raises RuntimeError: when an export failed, after every drawing was
                          tried.
    """
    from . import project
    sch_path = Path(sch_path).resolve()
    project.set_current(sch_path)
    failed = _update_images(sch_path, force)
    if failed:
        raise RuntimeError(_failures(failed))
    return _image_paths(sch_path)[0]


def make_schematic(sch_path, cir_title=None, force=False):
    """Export a schematic to netlist, SVG and PDF, headlessly: the bundle
    for ``sl.makeCircuit()``, which always needs all three. Netlist and
    images are written in ONE child process, so the cold Python+Qt import
    and the scene load (~1.1 s) are paid once (Anton, 2026-07-16). The
    images are written also when the netlist fails; the netlist errors are
    then raised. For the images alone use ``export_images``.

    The images and the netlist have their own inputs (provenance): the
    images follow the sources of the drawing, the netlist also SLiCAP
    itself. After an install only the netlist is rebuilt, by the
    ``netlist`` command, and the images stay as they are.

    :param sch_path:  Path to the ``.slicap_sch`` or ``.spice_sch`` file.
    :param cir_title: Circuit title override.  Defaults to the title stored
                      in the schematic or, if empty, to the file stem.
    :param force:     True exports even when the outputs are current.
    :returns:         ``Path`` to the generated ``.cir`` netlist file, or to
                      the generated ``lib/<title>.slicap_lib`` when the
                      schematic is a subcircuit (no ``.cir`` is written).
    """
    from . import project
    sch_path = Path(sch_path).resolve()
    project.set_current(sch_path)
    failed = _export_children(sch_path, force)
    images = force or not _images_current(sch_path)
    netlist = force or not _netlist_current(sch_path, cir_title)
    if images or netlist:
        _run_cli("export" if images else "netlist", sch_path,
                 ["--title", cir_title] if cir_title else [])
    if failed:
        raise RuntimeError(_failures(failed))
    # Derive the output path without creating any Qt objects.
    out = _netlist_output(sch_path, cir_title)
    return out if out is not None else _image_paths(sch_path)[0]
