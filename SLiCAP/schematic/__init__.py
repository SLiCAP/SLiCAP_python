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

    :param sch_path:  Path to the ``.slicap_sch`` source file.
    :param cir_title: Circuit title override.  Defaults to the title stored
                      in the schematic or, if empty, to the file stem.
    :returns:         ``Path`` to the generated ``.cir`` netlist file.
    """
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv[:1])

    from .cli import _load_scene, _default_output
    from .component_item import ComponentItem
    from .wire_item import WireItem
    from .command_item import CommandItem
    from .analysis_item import AnalysisItem
    from .library_item import LibraryItem
    from .parameter_item import ParameterItem
    from .netlist import build_netlist
    from .export import export_svg, export_pdf

    sch_path = Path(sch_path)
    scene, data = _load_scene(sch_path)
    title = cir_title or data.properties.title or sch_path.stem

    items = scene.items()
    comps = [i for i in items if isinstance(i, ComponentItem)]
    wires = [i for i in items if isinstance(i, WireItem)]
    cmds  = [i for i in items if isinstance(i, (CommandItem, AnalysisItem))]
    libs  = [i for i in items if isinstance(i, LibraryItem)]
    prms  = [i for i in items if isinstance(i, ParameterItem)]

    cir_path = _default_output(sch_path, "cir", ".cir")
    svg_path = _default_output(sch_path, "img", ".svg")
    pdf_path = _default_output(sch_path, "img", ".pdf")

    cir_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    cir_path.write_text(
        build_netlist(comps, wires, cmds, title, libs=libs, params=prms),
        encoding="utf-8",
    )
    print(f"Netlist  →  {cir_path}")

    export_svg(scene, svg_path, title)
    print(f"SVG      →  {svg_path}")

    try:
        export_pdf(scene, pdf_path)
        print(f"PDF      →  {pdf_path}")
    except ImportError:
        pass  # cairosvg not installed — PDF skipped silently

    return cir_path
