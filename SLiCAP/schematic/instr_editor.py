from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit,
    QSizePolicy, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QFont

# A fresh instruction file starts empty; "Add … instruction" seeds the header
# (import SLiCAP, and for a SLiCAP schematic the `cir = sl.makeCircuit(...)` line).
_TEMPLATE = ""


class InstrEditor(QDockWidget):
    """Dock widget for editing and running a plain-Python instruction script."""

    run_requested  = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Instructions", parent)
        self._path: Path | None = None

        container = QWidget()
        layout = QVBoxLayout(container)
        # Same chrome metrics as the log panel, so the two bottom docks align.
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        self._btn_run  = QPushButton("▶ Run")
        self._btn_stop = QPushButton("■ Stop")
        self._btn_open = QPushButton("Open…")
        self._btn_save = QPushButton("Save")
        self._btn_stop.setEnabled(False)
        for btn in (self._btn_run, self._btn_stop, self._btn_open,
                    self._btn_save):
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(22)
        # Order follows the workflow (Anton): open a file, run it, stop it,
        # save it.
        btn_row.addWidget(self._btn_open)
        btn_row.addWidget(self._btn_run)
        btn_row.addWidget(self._btn_stop)
        btn_row.addWidget(self._btn_save)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self._editor = QPlainTextEdit()
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(10)
        self._editor.setFont(mono)
        self._editor.setPlainText(_TEMPLATE)
        self._editor.document().setModified(False)
        layout.addWidget(self._editor)

        self.setWidget(container)

        self._btn_open.clicked.connect(self._on_open_dialog)
        self._btn_save.clicked.connect(self._on_save_dialog)
        self._btn_run.clicked.connect(self.run_requested)
        self._btn_stop.clicked.connect(self.stop_requested)

    def set_running(self, running: bool) -> None:
        """Toggle Run↔Stop button state to reflect whether a run is in progress."""
        self._btn_run.setEnabled(not running)
        self._btn_stop.setEnabled(running)

    def load(self, path: Path) -> None:
        """Load *path* into the editor; use the template if the file does not exist."""
        self._path = path
        self.setWindowTitle(path.name)
        if path.is_file():
            self._editor.setPlainText(path.read_text(encoding="utf-8"))
        else:
            self._editor.setPlainText(_TEMPLATE)
        self._editor.document().setModified(False)

    def unload(self) -> None:
        """Clear the editor and remove the associated path (no schematic open)."""
        self._path = None
        self.setWindowTitle("Instructions")
        self._editor.setPlainText(_TEMPLATE)
        self._editor.document().setModified(False)

    def ensure_header(self, sch_type: str, schematic_relpath: str | None) -> None:
        """Prepend the instruction-file header (import, and for SLiCAP the
        ``cir = sl.makeCircuit(...)`` line) if it is not already present."""
        from .instr_file import ensure_header
        cur = self._editor.toPlainText()
        new = ensure_header(cur, sch_type, schematic_relpath)
        if new != cur:
            self._editor.setPlainText(new)

    def text(self) -> str:
        """Current editor content (e.g. to derive unique result names)."""
        return self._editor.toPlainText()

    def insert_snippet(self, text: str) -> None:
        """Append *text* to the end of the editor content."""
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        block_text = cursor.block().text().strip()
        if block_text:
            cursor.insertText("\n")
        cursor.insertText(text)
        if not text.endswith("\n"):
            cursor.insertText("\n")
        self._editor.setTextCursor(cursor)

    def _on_open_dialog(self) -> None:
        """Open an existing instruction file; newly added instructions are
        appended to it."""
        if self.panel_dirty():
            resp = QMessageBox.question(
                self, "Unsaved changes",
                "The instruction editor has unsaved changes.\n"
                "Save them before opening another file?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel)
            if resp == QMessageBox.StandardButton.Cancel:
                return
            if (resp == QMessageBox.StandardButton.Save
                    and not self.panel_save()):
                return
        start = str(self._path.parent) if self._path else ""
        if not start:
            try:
                from . import project
                start = str(project.project_root())
            except Exception:
                start = ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open instruction file", start,
            "Python files (*.py);;All files (*)")
        if path:
            self.load(Path(path))

    def _on_save_dialog(self) -> None:
        """Open a file-save dialog, write the editor content, update title."""
        default = str(self._path) if self._path else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save instruction file", default,
            "Python files (*.py);;All files (*)",
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".py":
            p = p.with_suffix(".py")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(self._editor.toPlainText(), encoding="utf-8")
            self._path = p
            self.setWindowTitle(p.name)
            self._editor.document().setModified(False)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def save(self) -> bool:
        """Write editor contents to the current path silently (used before Run).

        Returns False if no path is set.
        """
        if self._path is None:
            return False
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._editor.toPlainText(), encoding="utf-8")
        self._editor.document().setModified(False)
        return True

    @property
    def path(self) -> Path | None:
        return self._path

    # -- closable-panel protocol (dirty-check on close) -----------------------

    def panel_dirty(self) -> bool:
        return self._editor.document().isModified()

    def panel_name(self) -> str:
        return self._path.name if self._path else "Instructions"

    def panel_save(self) -> bool:
        """Save the instruction content. Return True if saved, False if the
        user cancelled the Save-As dialog."""
        if self._path is None:
            self._on_save_dialog()
            return self._path is not None
        return self.save()
