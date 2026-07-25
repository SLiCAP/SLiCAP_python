#!/usr/bin/env python3
"""
SLiCAP schematic command-line tools.

Usage
-----
  python -m SLiCAP.schematic.cli netlist  sch/design.slicap_sch [-o cir/design.cir]
  python -m SLiCAP.schematic.cli svg      sch/design.slicap_sch [-o img/design.svg]
  python -m SLiCAP.schematic.cli pdf      sch/design.slicap_sch [-o img/design.pdf]

The input may be a ``.slicap_sch`` (SLiCAP netlist) or a ``.spice_sch``
(NGspice netlist); the builder is chosen from the file extension.

Netlist and SVG/PDF export work without opening the GUI window.
The grid is suppressed in SVG/PDF output.  When -o is omitted the output lands
in the project's cir/ (netlist) or img/ (svg/pdf) directory.

This CLI is invoked as a subprocess by ``SLiCAP.makeCircuit`` /
``make_schematic`` / ``SLiCAPngspice.make_netlist``; it is not the GUI
launcher (that is the ``slicap`` / ``slicap-schematics`` command).
"""
import argparse
import os
import sys
from pathlib import Path

_SYMBOLS_SVG         = Path(__file__).parent.parent / "files" / "symbols" / "slicap"  / "Symbols.svg"
_NGSPICE_SYMBOLS_SVG = Path(__file__).parent.parent / "files" / "symbols" / "ngspice" / "Symbols.svg"


# ── Qt bootstrap ─────────────────────────────────────────────────────────────

def _qt_app():
    """Return (or create) a headless QApplication.

    Only sets QT_QPA_PLATFORM=offscreen when there is no existing app — never
    when called from inside a running GUI, because that would corrupt the
    parent's environment and cause all subsequent subprocesses to be invisible.
    """
    from PySide6.QtWidgets import QApplication
    if QApplication.instance() is None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication(sys.argv[:1])


# ── shared scene loader ───────────────────────────────────────────────────────

def _load_scene(input_path: Path):
    """Load a .slicap_sch or .spice_sch file and return (SchematicScene, SchematicData).

    The symbol library is selected automatically based on the file extension:
    ``.slicap_sch`` → SLiCAP symbols; ``.spice_sch`` → NGspice symbols.
    """
    from .schematic_data import SchematicData
    from .symbol_library import SymbolLibrary
    from .canvas import SchematicScene
    from . import project

    is_ngspice = input_path.suffix.lower() == ".spice_sch"
    symbols_svg = _NGSPICE_SYMBOLS_SVG if is_ngspice else _SYMBOLS_SVG

    project.set_current(input_path)   # project-root fallback + sidecar migration
    from .config import Style
    data    = SchematicData.load(input_path)
    library = SymbolLibrary(symbols_svg)
    library.add_bundle(project.symbols_path_for(input_path))  # frozen symbols
    scene   = SchematicScene()
    scene.style = Style(project.ini_path_for(input_path))     # saved style
    scene.cache_dir = project.cache_path_for(input_path)      # render cache
    scene.from_data(data, library)
    return scene, data


# ── subcommands ───────────────────────────────────────────────────────────────

def _default_output(input_path: Path, kind: str, suffix: str) -> Path:
    """Default output path in the project's <kind> subdir (cir/img).

    Must be called after _load_scene so the project root is set from the input.
    """
    from . import project
    return project.subdir(kind) / input_path.with_suffix(suffix).name


def _write_netlist(input_path, scene, data, output_path, title):
    """Build and write the netlist for an ALREADY-LOADED scene (the file
    extension selects the SLiCAP or NGspice builder). Shared by the
    ``netlist`` and ``export`` commands so the scene is loaded once."""
    from .component_item import ComponentItem
    from .wire_item import WireItem
    from .library_item import LibraryItem
    from .parameter_item import ParameterItem
    from .netlist import NetlistError

    items = scene.items()
    comps = [i for i in items if isinstance(i, ComponentItem)]
    wires = [i for i in items if isinstance(i, WireItem)]
    libs  = [i for i in items if isinstance(i, LibraryItem)]
    prms  = [i for i in items if isinstance(i, ParameterItem)]
    try:
        if input_path.suffix.lower() == ".spice_sch":
            from .ngspice_netlist import build_ngspice_netlist
            text = build_ngspice_netlist(
                comps, wires, title, libs=libs, params=prms,
                program_netlist=True)
        else:
            from .command_item import CommandItem
            from .analysis_item import AnalysisItem
            from .netlist import build_netlist
            cmds = [i for i in items
                    if isinstance(i, (CommandItem, AnalysisItem))]
            text = build_netlist(comps, wires, cmds, title,
                                 libs=libs, params=prms)
    except NetlistError as exc:
        print("Netlist not generated — unresolved '?' placeholders remain:",
              file=sys.stderr)
        for err in exc.errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"Netlist  →  {output_path}")


def cmd_netlist(args):
    """Generate the .cir netlist (extension picks the SLiCAP/NGspice builder)."""
    _qt_app()
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = (Path(args.output) if args.output
                   else _default_output(input_path, "cir", ".cir"))
    title = getattr(args, "title", None) or data.properties.title or input_path.stem
    _write_netlist(input_path, scene, data, output_path, title)


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


def cmd_export(args):
    """Netlist + SVG + PDF in ONE process — the scene is loaded once, so the
    cold Python+Qt import (≈1.1 s) is paid once instead of three times
    (Anton, 2026-07-16: this is 60% of make_schematic's cost)."""
    _qt_app()
    from .export import export_svg, export_pdf
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    title = getattr(args, "title", None) or data.properties.title or input_path.stem
    _write_netlist(input_path, scene, data,
                   _default_output(input_path, "cir", ".cir"), title)
    svg = _default_output(input_path, "img", ".svg")
    export_svg(scene, svg, data.properties.title or input_path.stem)
    print(f"SVG      →  {svg}")
    pdf = _default_output(input_path, "img", ".pdf")
    export_pdf(scene, pdf)
    print(f"PDF      →  {pdf}")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="python -m SLiCAP.schematic.cli",
        description="SLiCAP headless schematic export (netlist / SVG / PDF). "
                    "Not the GUI launcher — that is 'slicap' / 'slicap-schematics'.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    _input_help = "Schematic file: .slicap_sch (SLiCAP) or .spice_sch (NGspice)"

    p_net = sub.add_parser(
        "netlist",
        help="Generate a .cir netlist (.slicap_sch → SLiCAP, .spice_sch → NGspice)")
    p_net.add_argument("input", help=_input_help)
    p_net.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.cir)")
    p_net.add_argument("--title", metavar="TITLE", default=None,
                       help="Circuit title (default: from schematic or file stem)")

    p_svg = sub.add_parser("svg", help="Export schematic to SVG")
    p_svg.add_argument("input", help=_input_help)
    p_svg.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.svg)")

    p_pdf = sub.add_parser("pdf", help="Export schematic to PDF")
    p_pdf.add_argument("input", help=_input_help)
    p_pdf.add_argument("-o", "--output", metavar="FILE",
                       help="Output file (default: <input>.pdf)")

    p_exp = sub.add_parser(
        "export",
        help="Netlist + SVG + PDF in one pass (scene loaded once)")
    p_exp.add_argument("input", help=_input_help)
    p_exp.add_argument("--title", metavar="TITLE", default=None,
                       help="Circuit title (default: from schematic or file stem)")

    args = parser.parse_args()
    from .symbol_library import SymbolError
    try:
        {"netlist": cmd_netlist, "svg": cmd_svg, "pdf": cmd_pdf,
         "export": cmd_export}[args.command](args)
    except SymbolError as exc:
        # A malformed symbol definition is the user's to fix in the SVG file.
        sys.exit(f"Symbol library error: {exc}")


if __name__ == "__main__":
    main()
