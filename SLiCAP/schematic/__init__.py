"""
SLiCAP schematic capture package.

GUI entry point:  slicap-schematic  (console script)
Python API:       from SLiCAP.schematic import make_schematic
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
    props = schematic_properties(sch_path)
    if props.is_subcircuit:
        from .subcircuit import lib_path_for
        name = title or props.title or sch_path.stem
        sch_type = "ngspice" if sch_path.suffix.lower() == ".spice_sch" else "slicap"
        return lib_path_for(sch_path, name, sch_type)
    return project.subdir("cir") / sch_path.with_suffix(".cir").name


def _outputs_current(sch_path: Path, title=None) -> "Path | None":
    """Return the netlist path (see _netlist_output) when regeneration can
    be skipped: the netlist,
    SVG and PDF exist, the SVG and PDF were exported by SLiCAP FROM THIS
    schematic (provenance markers), and all three are newer than every
    input of the export - the schematic, its sidecars, the symbol libraries
    and the schematic package (Anton, 2026-07-16: an unchanged schematic
    is not re-exported on every dialog open; 2026-09-13: a newer image
    made by another tool, e.g. the KiCad path, no longer counts as
    current, and an install or a symbol change re-exports once). Returns
    None when anything is missing, foreign or stale."""
    from . import project
    from .provenance import svg_source, pdf_is_export, input_mtime
    project.set_current(sch_path)
    cir = _netlist_output(sch_path, title)
    svg = project.subdir("img") / sch_path.with_suffix(".svg").name
    pdf = project.subdir("img") / sch_path.with_suffix(".pdf").name
    try:
        src = input_mtime(sch_path)
        for out in (cir, svg, pdf):
            if not out.exists() or out.stat().st_mtime < src:
                return None
    except OSError:
        return None
    if svg_source(svg) != sch_path.name or not pdf_is_export(pdf):
        return None
    return cir


def make_schematic(sch_path, cir_title=None, force=False):
    """Export a .slicap_sch schematic to netlist, SVG and PDF.

    Runs headlessly (no GUI window).  Call this before ``sl.makeCircuit()``
    or let ``makeCircuit()`` call it automatically when it receives a
    ``.slicap_sch`` filename.

    The Qt-heavy scene rendering is delegated to a child process via the
    ``SLiCAP.schematic.cli`` entry point.  This keeps Qt objects out of any
    calling thread that has no Qt event dispatcher (e.g. a GUI background
    worker), which would otherwise produce QBasicTimer warnings and could
    corrupt the parent application's display state.

    :param sch_path:  Path to the ``.slicap_sch`` source file.
    :param cir_title: Circuit title override.  Defaults to the title stored
                      in the schematic or, if empty, to the file stem.
    :returns:         ``Path`` to the generated ``.cir`` netlist file, or to
                      the generated ``lib/<title>.slicap_lib`` when the
                      schematic is a subcircuit (no ``.cir`` is written).
    """
    import sys
    import subprocess

    sch_path = Path(sch_path).resolve()

    # Skip regeneration when the outputs are already current (biggest win:
    # no subprocess at all when the schematic hasn't changed).
    if not force:
        current = _outputs_current(sch_path, cir_title)
        if current is not None:
            return current

    title_args = ["--title", cir_title] if cir_title else []

    # ── netlist + SVG + PDF in ONE subprocess ─────────────────────────────────
    # The cold Python+Qt import (~1.1 s) and the scene load are paid once
    # here instead of three times (Anton, 2026-07-16). Netlist failure is
    # fatal; SVG/PDF failures are reported but non-fatal.
    result = subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", "export",
         str(sch_path)] + title_args,
        capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # no console flash on Windows
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(
            f"Schematic export failed:\n{result.stderr or result.stdout}"
        )

    # Derive the output path without creating any Qt objects.
    from . import project
    project.set_current(sch_path)
    return _netlist_output(sch_path, cir_title)
