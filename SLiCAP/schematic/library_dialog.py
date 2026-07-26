from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QDialogButtonBox, QFileDialog,
)
from PySide6.QtCore import Qt


def _project_relative(path: str) -> str:
    """Store a library reference relative to the project root (POSIX) when it
    lives inside the project tree, so it stays portable when the same project is
    opened on another machine (Linux/Windows share drives differ, e.g. Z: vs
    /home/…); an external file is kept absolute."""
    try:
        from . import project
        root = Path(project.project_root()).resolve()
        p = Path(path).resolve()
        if p.is_relative_to(root):
            return p.relative_to(root).as_posix()
    except Exception:
        pass
    return path


class _LibRow(QWidget):
    """One library line.  SLiCAP: file only (always .lib, no corner).
    NGspice/SPICE: .inc/.lib selector + file + corner (corner only on .lib)."""

    def __init__(self, spice: bool, entry: dict, on_delete,
                 browse_title: str, browse_dir: str):
        super().__init__()
        self._spice = spice
        self._browse_title = browse_title
        self._browse_dir = browse_dir

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        self._dir = None
        self._corner = None
        if spice:
            self._dir = QComboBox()
            self._dir.addItems([".lib", ".inc"])
            self._dir.setCurrentText("." + (entry.get("directive") or "lib"))
            self._dir.setFixedWidth(70)
            row.addWidget(self._dir)

        self._file = QLineEdit(entry.get("file", ""))
        self._file.setPlaceholderText("Library file path…")
        row.addWidget(self._file, 1)

        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(browse)

        if spice:
            self._corner = QLineEdit(entry.get("corner", ""))
            self._corner.setPlaceholderText("corner")
            self._corner.setFixedWidth(90)
            row.addWidget(self._corner)
            self._dir.currentTextChanged.connect(self._sync_corner)
            self._sync_corner()

        delete = QPushButton("Delete")
        delete.clicked.connect(lambda: on_delete(self))
        row.addWidget(delete)

    def _sync_corner(self) -> None:
        if self._corner is not None:
            self._corner.setEnabled(self._dir.currentText() == ".lib")

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, self._browse_title,
            self._file.text() or self._browse_dir,
            "Library Files (*.lib *.spi *.sp *.inc);;All Files (*)")
        if path:
            self._file.setText(_project_relative(path))

    def value(self) -> dict:
        directive = self._dir.currentText().lstrip(".") if self._dir else "lib"
        corner = ""
        if self._corner is not None and directive == "lib":
            corner = self._corner.text().strip()
        return {"directive": directive,
                "file": self._file.text().strip(),
                "corner": corner}


class LibraryDialog(QDialog):
    """Add / edit the schematic's library block (one line per library)."""

    def __init__(self, entries=None, sch_type: str = "slicap",
                 show: bool = True, parent=None):
        super().__init__(parent, Qt.Window)
        self._spice = (sch_type == "ngspice")
        self.setWindowTitle("Add / Edit libraries")
        self.setMinimumWidth(560)

        from . import project
        try:
            self._browse_dir = str(project.subdir("lib"))
        except Exception:
            self._browse_dir = ""
        self._browse_title = ("Select SPICE library" if self._spice
                              else "Select SLiCAP library")

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(
            "Choose .lib or .inc per line; .lib may take a corner."
            if self._spice else
            "SLiCAP libraries are included with .lib (no corner)."))

        self._rows: list = []
        self._rows_box = QVBoxLayout()
        self._rows_box.setSpacing(3)
        self._rows_box.addStretch(1)                 # rows insert before this
        container = QWidget()
        container.setLayout(self._rows_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        add = QPushButton("Add library")
        add.clicked.connect(lambda: self._add_row())
        outer.addWidget(add, 0, Qt.AlignLeft)

        self._show_cb = QCheckBox(
            "Show on schematic  (libraries are always netlisted)")
        self._show_cb.setChecked(bool(show))
        outer.addWidget(self._show_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        for e in (entries or []):
            self._add_row(e)
        if not self._rows:
            self._add_row()

    def _add_row(self, entry=None) -> None:
        row = _LibRow(self._spice, entry or {}, self._delete_row,
                      self._browse_title, self._browse_dir)
        self._rows.append(row)
        self._rows_box.insertWidget(self._rows_box.count() - 1, row)

    def _delete_row(self, row) -> None:
        if row in self._rows:
            self._rows.remove(row)
            self._rows_box.removeWidget(row)
            row.deleteLater()

    def entries(self) -> list:
        return [v for r in self._rows
                if (v := r.value())["file"]]

    def show_on_schematic(self) -> bool:
        return self._show_cb.isChecked()
