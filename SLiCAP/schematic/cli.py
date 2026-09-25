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
in the project's cir/ (netlist) or img/ (svg/pdf) directory. A subcircuit
schematic yields its library in lib/ instead of a netlist.

This CLI is invoked as a subprocess by ``SLiCAP.makeCircuit`` /
``make_schematic`` / ``SLiCAPngspice.make_netlist``; it is not the GUI
launcher (that is the ``slicap`` / ``slicap-schematics`` command).
"""
import argparse
import os
import sys
from pathlib import Path

_SYMBOLS_SVG         = Path(__file__).parent.parent / "files" / "symbols" / "slicap"  / "Symbols.slicap_sym"
_NGSPICE_SYMBOLS_SVG = Path(__file__).parent.parent / "files" / "symbols" / "ngspice" / "Symbols.spice_sym"


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
    from .symbol_library import build_library
    from .canvas import SchematicScene
    from . import project

    is_ngspice = input_path.suffix.lower() == ".spice_sch"

    project.set_current(input_path)   # project-root fallback + sidecar migration
    from .config import Style
    data    = SchematicData.load(input_path)
    # The SAME library the editor builds (symbol_library.build_library): the
    # netlister used to load the system symbols plus the frozen bundle ONLY,
    # so it could not see Symbols-extended.svg - where OV lives - nor the
    # project's lib/. A symbol's pin ORDER then came from the frozen bundle
    # instead of the library, and deleting that cache left the netlister
    # unable to find the symbol at all (Anton, 2026-08-03).
    library = build_library(input_path,
                            sch_type="ngspice" if is_ngspice else "slicap")
    scene   = SchematicScene()
    scene.sch_type = "ngspice" if is_ngspice else "slicap"    # as the editor sets it
    scene.style = Style(project.ini_path_for(input_path))     # saved style
    scene.cache_dir = project.cache_path_for(input_path)      # render cache
    missing = scene.from_data(data, library)
    if is_ngspice and not missing:
        scene.load_op_raw(input_path)     # bias annotations in the export
    if missing:
        # NEVER silently: a component whose symbol cannot be found used to be
        # skipped, and the netlist came out without that device.
        raise SystemExit(
            "Error: no symbol definition for: {0}. The netlist would be "
            "missing {1}. Check the symbol libraries (files/symbols, the "
            "project lib/) and the schematic's .symbols cache."
            .format(", ".join(sorted(set(missing))),
                    "that device" if len(set(missing)) == 1 else
                    "those devices"))
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
    ``netlist`` and ``export`` commands so the scene is loaded once.

    A subcircuit schematic (Subcircuit checked in Schematic Properties)
    gets its library, lib/<title>.slicap_lib or .spice_lib - the file the
    GUI's Save-as-subcircuit writes - and NO circuit netlist: its internal
    nodes have no ground, so the flat .cir that was written before only
    failed makeCircuit's ground check (Anton, 2026-09-16). ``output_path``
    None selects the default location, cir/ or lib/."""
    from .component_item import ComponentItem
    from .wire_item import WireItem
    from .library_item import LibraryItem
    from .parameter_item import ParameterItem
    from .model_item import ModelItem
    from .netlist import NetlistError

    items  = scene.items()
    comps  = [i for i in items if isinstance(i, ComponentItem)]
    wires  = [i for i in items if isinstance(i, WireItem)]
    libs   = [i for i in items if isinstance(i, LibraryItem)]
    prms   = [i for i in items if isinstance(i, ParameterItem)]
    # .model blocks were missing from the HEADLESS netlist (only the
    # window's Save-netlist passed them): makeCircuit() then failed on
    # "missing definition of model" and the analysis dialog had no
    # candidates to offer (Anton, 2026-09-14).
    models = [i for i in items if isinstance(i, ModelItem)]
    sch_type = "ngspice" if input_path.suffix.lower() == ".spice_sch" else "slicap"
    props = getattr(data, "properties", None)
    label = "Netlist "
    try:
        if props is not None and props.is_subcircuit:
            from .subcircuit import build_lib, lib_path_for
            from .netlist import schematic_ports
            # The saved port order, completed with ports added since - the
            # default the GUI's Create-subcircuit dialog shows.
            present = schematic_ports(comps, wires)
            saved   = [p for p in props.subcircuit_ports if p in present]
            ports   = saved + [p for p in present if p not in saved]
            text = build_lib(sch_type, comps, wires, title, ports,
                             props.subcircuit_params, params_items=prms,
                             libs=libs, model_defs=models)
            default = lib_path_for(input_path, title, sch_type)
            label = "Library "
        elif sch_type == "ngspice":
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
                                 libs=libs, params=prms, model_defs=models)
        if props is None or not props.is_subcircuit:
            default = _default_output(input_path, "cir", ".cir")
    except NetlistError as exc:
        print("Netlist not generated:", file=sys.stderr)
        for err in exc.errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(output_path) if output_path else default
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"{label} --> {output_path}")


def cmd_netlist(args):
    """Generate the .cir netlist (extension picks the SLiCAP/NGspice builder)."""
    _qt_app()
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else None
    title = getattr(args, "title", None) or data.properties.title or input_path.stem
    _write_netlist(input_path, scene, data, output_path, title)


def cmd_svg(args):
    _qt_app()
    from .export import export_svg
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else _default_output(input_path, "img", ".svg")
    export_svg(scene, output_path, data.properties.title or input_path.stem,
               source=input_path.name)
    print(f"SVG      --> {output_path}")


def cmd_pdf(args):
    _qt_app()
    from .export import export_pdf
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    output_path = Path(args.output) if args.output else _default_output(input_path, "img", ".pdf")
    export_pdf(scene, output_path, source=input_path.name,
               title=data.properties.title or input_path.stem)
    print(f"PDF      --> {output_path}")


def cmd_export(args):
    """Netlist + SVG + PDF in ONE process — the scene is loaded once, so the
    cold Python+Qt import (≈1.1 s) is paid once instead of three times
    (Anton, 2026-07-16: this is 60% of make_schematic's cost)."""
    _qt_app()
    from .export import export_svg, export_pdf
    input_path  = Path(args.input)
    scene, data = _load_scene(input_path)
    title = getattr(args, "title", None) or data.properties.title or input_path.stem
    _write_netlist(input_path, scene, data, None, title)
    svg = _default_output(input_path, "img", ".svg")
    export_svg(scene, svg, data.properties.title or input_path.stem,
               source=input_path.name)
    print(f"SVG      --> {svg}")
    pdf = _default_output(input_path, "img", ".pdf")
    export_pdf(scene, pdf, source=input_path.name, title=title)
    print(f"PDF      --> {pdf}")


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
