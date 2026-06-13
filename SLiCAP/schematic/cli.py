#!/usr/bin/env python3
"""
SLiCAP schematic command-line tools.

Usage
-----
  python -m app.cli netlist  sch/design.slicap_sch [-o cir/design.cir]
  python -m app.cli svg      sch/design.slicap_sch [-o img/design.svg]
  python -m app.cli pdf      sch/design.slicap_sch [-o img/design.pdf]

Netlist and SVG/PDF export work without opening the GUI window.
The grid is suppressed in SVG/PDF output.  When -o is omitted the output lands
in the project's cir/ (netlist) or img/ (svg/pdf) directory.
"""
import argparse
import os
import sys
from pathlib import Path

_SYMBOLS_SVG = Path(__file__).parent.parent / "files" / "symbols" / "slicap" / "Symbols.svg"


# ── Qt bootstrap ─────────────────────────────────────────────────────────────

def _qt_app():
    """Return (or create) a headless QApplication."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication(sys.argv[:1])


# ── shared scene loader ───────────────────────────────────────────────────────

def _load_scene(input_path: Path):
    """Load a .slicap_sch file and return (SchematicScene, SchematicData)."""
    from .schematic_data import SchematicData
    from .symbol_library import SymbolLibrary
    from .canvas import SchematicScene
    from . import project

    project.set_current(input_path)   # LaTeX cache → <name>.cache, not a temp dir
    data    = SchematicData.load(input_path)
    library = SymbolLibrary(_SYMBOLS_SVG)
    library.add_bundle(project.symbols_path())   # this schematic's frozen symbols
    library.inject_into_component_item()
    scene   = SchematicScene()
    scene.from_data(data, library)
    return scene, data


# ── subcommands ───────────────────────────────────────────────────────────────

def _default_output(input_path: Path, kind: str, suffix: str) -> Path:
    """Default output path in the project's <kind> subdir (cir/img).

    Must be called after _load_scene so the project root is set from the input.
    """
    from . import project
    return project.subdir(kind) / input_path.with_suffix(suffix).name


def cmd_netlist(args):
    _qt_app()
    input_path  = Path(args.input)

    from .component_item import ComponentItem
    from .wire_item import WireItem
    from .command_item import CommandItem
    from .analysis_item import AnalysisItem
    from .library_item import LibraryItem
    from .parameter_item import ParameterItem
    from .netlist import build_netlist

    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else _default_output(input_path, "cir", ".cir")
    items = scene.items()
    comps = [i for i in items if isinstance(i, ComponentItem)]
    wires = [i for i in items if isinstance(i, WireItem)]
    cmds  = [i for i in items if isinstance(i, (CommandItem, AnalysisItem))]
    libs  = [i for i in items if isinstance(i, LibraryItem)]
    prms  = [i for i in items if isinstance(i, ParameterItem)]
    title = data.properties.title or input_path.stem

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_netlist(comps, wires, cmds, title, libs=libs, params=prms),
        encoding="utf-8",
    )
    print(f"Netlist  →  {output_path}")


def cmd_svg(args):
    _qt_app()
    from .export import export_svg
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else _default_output(input_path, "img", ".svg")
    export_svg(scene, output_path, data.properties.title or input_path.stem)
    print(f"SVG      →  {output_path}")


def cmd_pdf(args):
    _qt_app()
    from .export import export_pdf
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else _default_output(input_path, "img", ".pdf")
    export_pdf(scene, output_path)
    print(f"PDF      →  {output_path}")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="slicap",
        description="SLiCAP schematic command-line tools",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_net = sub.add_parser("netlist", help="Generate .cir netlist from .slicap_sch")
    p_net.add_argument("input")
    p_net.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.cir)")

    p_svg = sub.add_parser("svg", help="Export schematic to SVG")
    p_svg.add_argument("input")
    p_svg.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.svg)")

    p_pdf = sub.add_parser("pdf", help="Export schematic to PDF")
    p_pdf.add_argument("input")
    p_pdf.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.pdf)")

    args = parser.parse_args()
    from .symbol_library import SymbolError
    try:
        {"netlist": cmd_netlist, "svg": cmd_svg, "pdf": cmd_pdf}[args.command](args)
    except SymbolError as exc:
        # A malformed symbol definition is the user's to fix in the SVG file.
        sys.exit(f"Symbol library error: {exc}")


if __name__ == "__main__":
    main()
