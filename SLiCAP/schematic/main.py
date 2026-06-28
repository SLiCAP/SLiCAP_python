import sys
import argparse

from PySide6.QtWidgets import QApplication, QMessageBox
from .window import MainWindow
from .symbol_library import SymbolError
from . import logfile


def main():
    # Tee stdout/stderr so terminal output is also captured to the current
    # schematic's txt/<name>.log (see project.set_current / logfile).
    logfile.install()
    parser = argparse.ArgumentParser(prog="slicap-schematic-gui")
    parser.add_argument(
        "--config",
        choices=["basic", "full"],
        default="full",
        help="Symbol library set: 'basic' loads only Symbols.svg; 'full' loads all system SVGs (default).",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Schematic file to open at startup (.slicap_sch).",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    try:
        window = MainWindow(config=args.config, file=args.file)
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
