import argparse
import os
import sys


def resolve_schematic_only_mode(argv: list[str] | None = None) -> bool:
    """Resolve whether the launcher should open the schematic-only UI.

    The dedicated `slicap-schematics` entry point starts in schematic-only
    mode. The regular `slicap` entry point opens the full GUI.
    """
    if argv is None:
        argv = sys.argv
    if not argv:
        return False
    return os.path.basename(argv[0]) == "slicap-schematics"


def resolve_startup_config(config: str | None, file: str | None) -> str | None:
    """Resolve the initial schematic mode from explicit config and optional file.

    Precedence is:
    1. explicit config, if provided
    2. file extension, if a schematic file is provided
    3. None, which leaves the app in its interactive default mode

    If the explicit config and the file extension disagree, a ValueError is raised.
    """
    if config is not None:
        if file is None:
            return config
        if config == "basic":
            return config
        inferred = _infer_schematic_kind(file)
        if inferred is not None and inferred != config:
            raise ValueError(
                f"Conflicting startup mode: --config={config} does not match file extension for {file}"
            )
        return config

    if file is None:
        return None

    return _infer_schematic_kind(file)


def _infer_schematic_kind(file: str | None) -> str | None:
    if file is None:
        return None
    suffix = file.lower().rsplit(".", 1)[-1] if "." in file else ""
    if suffix == "slicap_sch":
        return "slicap"
    if suffix == "spice_sch":
        return "ngspice"
    return None


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    if prog is None:
        prog = os.path.basename(sys.argv[0]) if sys.argv else "slicap"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Opens the SLiCAP GUI.",
        epilog=(
            "Related commands:\n"
            "  slicap                      Full GUI: both schematic types + analysis panels\n"
            "  slicap-schematics           Schematic-only editor (no analysis panels)\n"
            "  python -m SLiCAP.schematic.cli netlist|svg|pdf FILE\n"
            "                              Headless export to .cir / .svg / .pdf (no GUI)\n"
            "\n"
            "From Python:\n"
            "  import SLiCAP as sl;  sl.startSchematic(config=..., file=...)\n"
            "\n"
            "Examples:\n"
            "  slicap\n"
            "  slicap-schematics --config basic\n"
            "  slicap-schematics --config ngspice mycircuit.spice_sch\n"
            "  python -m SLiCAP.schematic.cli netlist mycircuit.slicap_sch"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--config",
        choices=["basic", "slicap", "ngspice"],
        default=None,
        help=(
            "Capture mode — symbol library and permitted schematic type:\n"
            "\n"
            "  config   symbol set            schematic type\n"
            "  -------  --------------------  ----------------\n"
            "  (none)   chosen per schematic  SLiCAP + NGspice\n"
            "  basic    Symbols.svg only      SLiCAP only\n"
            "  slicap   full SLiCAP library   SLiCAP only\n"
            "  ngspice  NGspice library       NGspice only\n"
            "\n"
            "A canvas is shown only when a FILE is also given; otherwise\n"
            "the editor starts empty and the File menu creates or opens\n"
            "a schematic in this mode.\n"
        ),
    )
    # Internal plumbing for sl.startSchematic() and other '-m' launch paths
    # that cannot be recognised by launcher name; users get schematic-only
    # mode via the 'slicap-schematics' entry point, so keep the flag out of
    # the user-facing help.
    parser.add_argument(
        "--schematic-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Schematic file to open at startup\n"
             "(.slicap_sch = SLiCAP, .spice_sch = NGspice).",
    )
    return parser


def main():
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QCoreApplication, Qt as _Qt

    from . import logfile
    from .symbol_library import SymbolError
    from .window import MainWindow

    # Tee stdout/stderr so terminal output is also captured to the current
    # schematic's txt/<name>.log (see project.set_current / logfile).
    logfile.install()
    parser = build_parser()
    args = parser.parse_args()

    try:
        resolved_config = resolve_startup_config(args.config, args.file)
    except ValueError as exc:
        parser.error(str(exc))

    schematic_only = args.schematic_only or resolve_schematic_only_mode(sys.argv)

    # NOTHING is initialised here (Anton, 2026-08-16). Starting the GUI used
    # to call initProject("GUI"), which created a whole project tree in
    # whatever directory the user happened to type `slicap` in - and renamed
    # any project later opened to "GUI". A project is created by
    # File -> New project (initProject) and opened by File -> Select project
    # folder (loadProject); the schematic-only editor needs neither, because
    # it cannot build a circuit object.

    # Avoid using the desktop-native menu integration so menus render
    # inside the application window (helpful on GNOME/Ubuntu).
    try:
        QCoreApplication.setAttribute(_Qt.AA_DontUseNativeMenuBar, True)
    except Exception:
        pass
    # Some Linux desktops inject GTK modules into every process via
    # GTK_MODULES; Qt's GTK platform theme initialises GTK during
    # QApplication construction, which then fails to load modules that
    # don't apply to a Qt app and prints "Gtk-Message: Failed to load
    # module …" noise. Strip them ONLY around that construction and
    # restore afterwards, so child processes (runner, NGspice, files
    # opened with desktop GTK apps) inherit the unmodified environment.
    # No-op on Windows/macOS (GTK_MODULES unset); Qt's own accessibility
    # bridge is unaffected by NO_AT_BRIDGE (GTK-internal only).
    _saved = {k: os.environ.get(k) for k in ("GTK_MODULES", "NO_AT_BRIDGE")}
    if _saved["GTK_MODULES"] is not None:
        os.environ["GTK_MODULES"] = ":".join(
            m for m in _saved["GTK_MODULES"].split(":")
            if m and m not in ("xapp-gtk3-module", "gail", "atk-bridge"))
    os.environ.setdefault("NO_AT_BRIDGE", "1")
    app = QApplication(sys.argv)
    for _k, _v in _saved.items():
        if _v is None:
            os.environ.pop(_k, None)
        else:
            os.environ[_k] = _v
    try:
        window = MainWindow(
            config=resolved_config,
            file=args.file,
            schematic_only=schematic_only,
        )
    except SymbolError as exc:
        # A malformed symbol definition is the user's to fix, in the SVG file —
        # we report it clearly and stop rather than guessing a correction.
        print(f"Symbol library error: {exc}", file=sys.stderr)
        QMessageBox.critical(
            None, "Symbol library error",
            f"{exc}\n\nPlease fix the symbol SVG file, then restart.",
        )
        sys.exit(1)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
