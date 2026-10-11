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
    return project.subdir("cir") / sch_path.with_suffix(".cir").name


def _image_paths(sch_path: Path):
    """The SVG and PDF the image export writes for ``sch_path``."""
    from . import project
    img = project.subdir("img")
    return img / sch_path.with_suffix(".svg").name, img / sch_path.with_suffix(".pdf").name


def _current(sch_path: Path, outputs) -> bool:
    """True when every output exists and is newer than every input of the
    export - the schematic, its sidecars, the symbol libraries and the
    schematic package (Anton, 2026-07-16: an unchanged schematic is not
    re-exported on every dialog open; 2026-09-13: an install or a symbol
    change re-exports once). None entries are skipped (a poster writes no
    netlist)."""
    from .provenance import input_mtime
    try:
        src = input_mtime(sch_path)
        for out in outputs:
            if out is not None and (not out.exists() or out.stat().st_mtime < src):
                return False
    except OSError:
        return False
    return True


def _images_current(sch_path: Path) -> bool:
    """The SVG and PDF are current (_current) and were exported by SLiCAP
    FROM THIS schematic (provenance markers; 2026-09-13: a newer image made
    by another tool, e.g. the KiCad path, does not count)."""
    from . import project
    from .provenance import svg_source, pdf_is_export
    project.set_current(sch_path)
    svg, pdf = _image_paths(sch_path)
    return (_current(sch_path, (svg, pdf))
            and svg_source(svg) == sch_path.name and pdf_is_export(pdf))


def _outputs_current(sch_path: Path, title=None) -> "Path | None":
    """Return the netlist path (see _netlist_output), or the SVG for a
    poster, when the netlist, SVG and PDF are all current; else None."""
    if not _images_current(sch_path):
        return None
    cir = _netlist_output(sch_path, title)
    if not _current(sch_path, (cir,)):
        return None
    return cir if cir is not None else _image_paths(sch_path)[0]


_exporting: set = set()      # posters whose children are being exported


def _export_children(sch_path: Path, force: bool) -> None:
    """A poster shows other drawings: their images are brought up to date
    first, children before parents, each once (a poster that contains itself
    through a chain is stopped here, the dialog refuses it too)."""
    from .provenance import poster_children
    if sch_path in _exporting:
        return
    _exporting.add(sch_path)
    try:
        for child in poster_children(sch_path):
            export_images(child, force=force)
    finally:
        _exporting.discard(sch_path)


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
    the images are current.

    :param sch_path: Path to the ``.slicap_sch``, ``.spice_sch`` or
                     ``.slicap_poster`` file.
    :param force:    True exports even when the images are current.
    :returns:        ``Path`` of the SVG.
    """
    sch_path = Path(sch_path).resolve()
    _export_children(sch_path, force)
    if force or not _images_current(sch_path):
        _run_cli("images", sch_path)
    from . import project
    project.set_current(sch_path)
    return _image_paths(sch_path)[0]


def make_schematic(sch_path, cir_title=None, force=False):
    """Export a schematic to netlist, SVG and PDF, headlessly: the bundle
    for ``sl.makeCircuit()``, which always needs all three. Netlist and
    images are written in ONE child process, so the cold Python+Qt import
    and the scene load (~1.1 s) are paid once (Anton, 2026-07-16). The
    images are written also when the netlist fails; the netlist errors are
    then raised. For the images alone use ``export_images``.

    :param sch_path:  Path to the ``.slicap_sch`` or ``.spice_sch`` file.
    :param cir_title: Circuit title override.  Defaults to the title stored
                      in the schematic or, if empty, to the file stem.
    :param force:     True exports even when the outputs are current.
    :returns:         ``Path`` to the generated ``.cir`` netlist file, or to
                      the generated ``lib/<title>.slicap_lib`` when the
                      schematic is a subcircuit (no ``.cir`` is written).
    """
    sch_path = Path(sch_path).resolve()
    _export_children(sch_path, force)
    if not force:
        current = _outputs_current(sch_path, cir_title)
        if current is not None:
            return current
    _run_cli("export", sch_path, ["--title", cir_title] if cir_title else [])
    # Derive the output path without creating any Qt objects.
    from . import project
    project.set_current(sch_path)
    out = _netlist_output(sch_path, cir_title)
    return out if out is not None else _image_paths(sch_path)[0]
