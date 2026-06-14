"""
SLiCAP schematic capture package.

GUI entry point:  slicap-schematic  (console script)
Python API:       from SLiCAP.schematic import make_schematic
"""

from pathlib import Path


def make_schematic(sch_path, cir_title=None):
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

    title_args = ["--title", cir_title] if cir_title else []

    # ── netlist (required) ────────────────────────────────────────────────────
    result = subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", "netlist",
         str(sch_path)] + title_args,
        capture_output=True, text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(
            f"Schematic-to-netlist conversion failed:\n"
            f"{result.stderr or result.stdout}"
        )

    # ── SVG (non-fatal) ───────────────────────────────────────────────────────
    r = subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", "svg", str(sch_path)],
        capture_output=True, text=True,
    )
    if r.stdout:
        print(r.stdout, end="")

    # ── PDF (non-fatal) ───────────────────────────────────────────────────────
    subprocess.run(
        [sys.executable, "-m", "SLiCAP.schematic.cli", "pdf", str(sch_path)],
        capture_output=True, text=True,
    )

    # Derive the .cir path without creating any Qt objects.
    from . import project
    project.set_current(sch_path)
    return project.subdir("cir") / sch_path.with_suffix(".cir").name
