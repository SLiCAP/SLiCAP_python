import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from .window import MainWindow
from .symbol_library import SymbolError


def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
    except SymbolError as exc:
        # A malformed symbol definition is the user's to fix, in the SVG file —
        # we report it clearly and stop rather than guessing a correction.
        QMessageBox.critical(
            None, "Symbol library error",
            f"{exc}\n\nPlease fix the symbol SVG file, then restart.",
        )
        sys.exit(1)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
