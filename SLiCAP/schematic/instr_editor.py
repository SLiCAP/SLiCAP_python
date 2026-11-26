from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSizePolicy, QFileDialog, QMessageBox,
)

from .code_editor import CodeEditor

# A fresh instruction file starts empty. Every insert adds the header (import
# SLiCAP as sl) when it is missing, in the same undo step (_seed_header).
# Circuit objects are created explicitly, one per schematic, and appended
# (Anton, 2026-08-16).
_TEMPLATE = ""


def _utf16(text: str, i: int) -> int:
    """The position of character *i* of *text* in UTF-16 units, the form
    of a QTextDocument position: a character outside the BMP (an emoji)
    takes two."""
    return len(text[:i].encode("utf-16-le")) // 2


def run_script_clash(path) -> str:
    """Why an instruction file cannot be saved as *path*, or "": the run
    script of a system diagram is <project root>/<diagram stem>.py, so
    an instruction file of that name in the project root is written over
    by the next sl.makeCircuit() of the diagram (Anton, 2026-11-18: a
    test project lost its instruction file so; SystemExtensionSpecs.md
    10.3.9)."""
    from . import project
    from .dialects import SYSTEM
    path = Path(path)
    try:
        root = project.root_for(path)
    except Exception:
        return ""
    if path.parent.resolve() != Path(root).resolve():
        return ""
    diagram = project.folder("sch", root) / (path.stem + SYSTEM.sch_ext)
    if diagram.exists():
        return ("%s is the run script of the system diagram %s, written by "
                "sl.makeCircuit(). Save the instruction file under another "
                "name." % (path.name, diagram.name))
    return ""


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

        # line numbers and zoom (code_editor, workshop of 2026-11-17)
        self._editor = CodeEditor()
        self._editor.setPlainText(_TEMPLATE)
        self._editor.document().setModified(False)
        layout.addWidget(self._editor)

        self.setWidget(container)

        self._btn_open.clicked.connect(self.open_dialog)
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

    def _seed_header(self) -> None:
        """Insert the instruction-file header where
        instr_file.header_insertion puts it, when the file lacks it. Only
        ``import SLiCAP as sl``, never a circuit object (Anton, 2026-08-16).

        Every insert calls it inside its open edit block, AFTER its edit.
        The header and the line are then one undo step. The header goes
        where the resulting file needs it. A caller passes positions of the
        text it read, and they stay valid.

        It inserts with a cursor, not with setPlainText. That reset the
        modified flag and the undo history of the whole file, so typing not
        yet saved was later discarded without a prompt (a review,
        2026-11-21).

        REPLACED 2026-11-22: the add-instruction handlers seeded the header
        themselves with a public InstrEditor.ensure_header() before their
        insert (SLNG.md, 2026-07-07). That was an undo step of its own, so
        one Ctrl+Z took back the line and left the header. The dialogs of
        Traces, Axes, Figures and snippets did not seed it at all. An outer
        edit block in every handler was considered and REJECTED: the rule
        would stay in ten consumers instead of the editor."""
        from PySide6.QtGui import QTextCursor
        from .instr_file import header_insertion
        full = self.text()
        insertion = header_insertion(full)
        if insertion is None:
            return
        position, line = insertion
        cursor = QTextCursor(self._editor.document())
        cursor.setPosition(_utf16(full, position))
        cursor.insertText(line)

    def text(self) -> str:
        """The editor content as written (``CodeEditor.text``). Save and
        Run write it, and every reader of the instructions takes it here."""
        return self._editor.text()

    def put(self, placement) -> None:
        """Write a placement (instr_file.place) as one undo step, with the
        header when it is missing (_seed_header): new statements appended,
        edited ones replaced where they stand and their old copies removed.
        A placement with problems writes nothing.

        The positions are those of text(), converted to the UTF-16 units of
        the document, and applied from the end so that each stays valid.
        Block numbers were the first form and were REPLACED on 2026-11-21:
        a line separator (U+2028) inside a block made the lines of the
        parsed text and the blocks of the document disagree.
        ``replace_range()``, the system run dialog's single replacement of
        2026-11-21, is REPLACED by this (2026-11-25): every dialog edits in
        place now."""
        from PySide6.QtGui import QTextCursor
        if placement.problems:
            return
        if placement.append:
            self.insert_snippet(placement.append)
            return
        if not placement.edits:
            return
        full = self.text()
        cursor = QTextCursor(self._editor.document())
        cursor.beginEditBlock()
        for start, end, text in reversed(placement.edits):
            cursor.setPosition(_utf16(full, start))
            cursor.setPosition(_utf16(full, end), QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(text)
        self._seed_header()
        cursor.endEditBlock()
        self._editor.setTextCursor(cursor)

    def put_dialog_result(self, dialog, parent=None) -> bool:
        """Write what an instruction dialog composed, its
        generated_snippet(), where it belongs (instr_file.place): a new
        object at the end, an object loaded with "Edit existing"
        (dialog.editing()) in place. The text is taken as it is NOW, so a
        non-modal dialog that was open while the file changed is refused
        (dialog.loaded()). A refusal says why and changes nothing. True
        when something was written."""
        from .instr_file import place
        snippet = dialog.generated_snippet()
        if not snippet:
            return False
        placement = place(self.text(), snippet, dialog.editing(), dialog.loaded())
        if placement.problems:
            QMessageBox.warning(parent or self, dialog.windowTitle(),
                                placement.problems[0] + "\n\nNothing was changed.")
            return False
        self.put(placement)
        return True

    def insert_at(self, position: int, text: str) -> bool:
        """Insert *text* at character *position* of ``text()``, as one undo
        step with the header when it is missing (a line before a given
        statement: Create run script puts the makeCircuit line before the
        first run of its diagram, 2026-11-21)."""
        return self._replace(position, position, text)

    def _replace(self, start: int, end: int, text: str) -> bool:
        """Replace the characters *start* to *end* of ``text()`` with *text*
        as one undo step with the header when it is missing. The positions
        are converted to the document's UTF-16 units. False when the range
        lies outside the text."""
        from PySide6.QtGui import QTextCursor
        full = self.text()
        if not 0 <= start <= end <= len(full):
            return False
        cursor = QTextCursor(self._editor.document())
        cursor.setPosition(_utf16(full, start))
        cursor.setPosition(_utf16(full, end), QTextCursor.MoveMode.KeepAnchor)
        cursor.beginEditBlock()
        cursor.insertText(text)
        self._seed_header()
        cursor.endEditBlock()
        self._editor.setTextCursor(cursor)
        return True

    def insert_snippet(self, text: str) -> None:
        """Append *text* to the end of the editor content, on a line of its
        own at column 0, as one undo step with the header when it is
        missing (_seed_header). A last line of only blanks (an editor's
        auto-indent) is cleared first: the snippet landed on it, indented,
        and the file no longer parsed or the line ran inside the block
        above it (a review, 2026-11-21)."""
        cursor = self._editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.MoveOperation.End)
        block_text = cursor.block().text()
        if block_text.strip():
            cursor.insertText("\n")
        elif block_text:
            cursor.movePosition(cursor.MoveOperation.StartOfBlock,
                                cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        cursor.insertText(text)
        if not text.endswith("\n"):
            cursor.insertText("\n")
        self._seed_header()
        cursor.endEditBlock()
        self._editor.setTextCursor(cursor)

    def maybe_save(self) -> bool:
        """Offer to save unsaved edits before the buffer is replaced (open,
        project switch, tree double-click).  False when the user cancels."""
        if not self.panel_dirty():
            return True
        resp = QMessageBox.question(
            self, "Unsaved changes",
            "The instruction editor has unsaved changes.\n"
            "Save them before opening another file?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel)
        if resp == QMessageBox.StandardButton.Cancel:
            return False
        if (resp == QMessageBox.StandardButton.Save
                and not self.panel_save()):
            return False
        return True

    def open_dialog(self) -> None:
        """Open an existing instruction file; newly added instructions are
        appended to it."""
        if not self.maybe_save():
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
        if self._path is None or not self._path.exists():
            # A fresh buffer - or a file moved/deleted behind our back - is
            # offered in the PROJECT ROOT, never in the schematic's sch/
            # folder: an instruction file is project-level and may carry
            # instructions for several schematics, so it is not bound to one
            # (Anton, 2026-08-19). Without an explicit directory the dialog
            # reuses the folder last used - which is sch/, because that is
            # where the schematic was opened.
            try:
                from . import project
                if self._path is not None:
                    # The project of the FILE, not of whichever schematic is
                    # open - the rule instruction_run_context() follows too.
                    default = str(project.root_for(self._path)
                                  / self._path.name)
                else:
                    default = str(project.project_root())
            except Exception:
                pass
        path, _ = QFileDialog.getSaveFileName(
            self, "Save instruction file", default,
            "Python files (*.py);;All files (*)",
        )
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".py":
            p = p.with_suffix(".py")
        clash = run_script_clash(p)
        if clash:
            QMessageBox.warning(self, "Save instruction file", clash)
            return
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(self.text(), encoding="utf-8")
            self._path = p
            self.setWindowTitle(p.name)
            self._editor.document().setModified(False)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def save(self) -> bool:
        """Write editor contents to the current path silently (used before Run).

        Asks where to save when the file has been moved or deleted outside the
        editor; returns False if no path is set or the user cancelled.
        """
        if self._path is None:
            return False
        if not self._path.exists():
            # Moved or deleted behind our back. Do NOT recreate it at the old
            # location: Run wrote the instruction file back into the
            # schematic's sch/ folder every time, undoing the relocation
            # (Anton, 2026-08-19). Ask instead - the dialog defaults to the
            # project root.
            self._on_save_dialog()
            return self._path is not None and self._path.exists()
        self._path.write_text(self.text(), encoding="utf-8")
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
