"""
SLiCAP schematic capture package.

GUI entry point:  slicap-schematic  (console script)
Python API:       from SLiCAP.schematic import make_schematic
"""

from pathlib import Path


def _outputs_current(sch_path: Path) -> "Path | None":
    """Return the .cir path when the netlist, SVG and PDF are all newer than
    the schematic source AND its style sidecar — i.e. regeneration can be
    skipped (Anton, 2026-07-16: images stay in sync, but an unchanged
    schematic is not re-exported on every dialog open). Returns None when
    anything is missing or stale."""
    from . import project
    project.set_current(sch_path)
    cir = project.subdir("cir") / sch_path.with_suffix(".cir").name
    svg = project.subdir("img") / sch_path.with_suffix(".svg").name
    pdf = project.subdir("img") / sch_path.with_suffix(".pdf").name
    try:
        src = sch_path.stat().st_mtime
        sidecar = project.ini_path_for(sch_path)
        if sidecar and Path(sidecar).is_file():
            src = max(src, Path(sidecar).stat().st_mtime)
    except OSError:
        return None
    for out in (cir, svg, pdf):
        if not out.exists() or out.stat().st_mtime < src:
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
    :returns:         ``Path`` to the generated ``.cir`` netlist file.
    """
    import sys
    import subprocess

    sch_path = Path(sch_path).resolve()

    # Skip regeneration when the outputs are already current (biggest win:
    # no subprocess at all when the schematic hasn't changed).
    if not force:
        current = _outputs_current(sch_path)
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

    # Derive the .cir path without creating any Qt objects.
    from . import project
    project.set_current(sch_path)
    return project.subdir("cir") / sch_path.with_suffix(".cir").name
