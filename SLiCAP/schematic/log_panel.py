"""Log panel — scrollable read-only output area for the NGspice subprocess."""
from PySide6.QtWidgets import (
    QDockWidget, QPlainTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
)
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor


class LogPanel(QDockWidget):
    """Collapsible dock widget showing NGspice stdout/stderr line by line.

    Error lines (containing 'error') are coloured red; warning lines
    (containing 'warning') are coloured orange.  Auto-scrolls to the
    bottom on each new line.  Cleared at the start of each new run.

    Toolbar buttons: Clear log | Save log…
    """

    def __init__(self, parent=None):
        super().__init__("Log", parent)
        self.setObjectName("ngspice_log_panel")
        self._dirty = False

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # ── button bar ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        btn_clear = QPushButton("Clear log")
        btn_clear.setFixedHeight(22)
        btn_clear.clicked.connect(self.clear)
        btn_row.addWidget(btn_clear)

        btn_save = QPushButton("Save log…")
        btn_save.setFixedHeight(22)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── text area ─────────────────────────────────────────────────────────
        self._edit = QPlainTextEdit()
        self._edit.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(9)
        self._edit.setFont(font)
        layout.addWidget(self._edit)

        self.setWidget(container)

        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

    def set_name(self, filename: str) -> None:
        """Update the panel title to *filename* (e.g. 'VampQspice.log')."""
        self.setWindowTitle(filename)

    def clear(self):
        self._edit.clear()
        self._dirty = False

    def _on_save(self) -> bool:
        """Write the log to a file. Return True if saved, False if the user
        cancelled or the write failed."""
        from . import project
        base = project.current()
        if base is not None:
            default = str(project.subdir("txt") / (base.stem + ".log"))
        else:
            default = ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", default, "Text files (*.txt *.log);;All files (*)"
        )
        if not path:
            return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._edit.toPlainText())
        except OSError as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Save log failed", str(exc))
            return False
        self._dirty = False
        return True

    # -- closable-panel protocol (dirty-check on close) -----------------------

    def panel_dirty(self) -> bool:
        """Always False: the log is DERIVED output, regenerated on every run
        (it is even cleared at run start). Treating appended lines as unsaved
        work made the close button ask "Save before closing?" and Close
        Project sweep the log along with real documents (Anton, 2026-08-03:
        "closing the log panel behaves differently from the others").
        "Save log..." is an export convenience, not persistence."""
        return False

    def panel_name(self) -> str:
        return self.windowTitle() or "Log"

    def panel_save(self) -> bool:
        return self._on_save()

    def append_line(self, text: str):
        fmt = QTextCharFormat()
        lo = text.lower()
        if "error" in lo:
            fmt.setForeground(QColor("#cc0000"))
        elif "warning" in lo:
            fmt.setForeground(QColor("#b85c00"))

        cursor = self._edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self._edit.setTextCursor(cursor)
        self._edit.ensureCursorVisible()
        self._dirty = True
