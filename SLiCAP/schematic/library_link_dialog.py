from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QDialogButtonBox, QFileDialog,
)
from PySide6.QtCore import Qt


class LibraryLinkDialog(QDialog):
    """Add / Edit a .lib or .inc library link."""

    def __init__(self, directive: str = "lib", simulator: str = "SLiCAP",
                 file_path: str = "", corner: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Add / Edit Library Link")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._directive_combo = QComboBox()
        self._directive_combo.addItems([".lib", ".inc"])
        self._directive_combo.setCurrentText(f".{directive}")
        form.addRow("Directive:", self._directive_combo)

        self._sim_combo = QComboBox()
        self._sim_combo.addItems(["SLiCAP", "SPICE"])
        self._sim_combo.setCurrentText(simulator)
        form.addRow("Simulator:", self._sim_combo)

        file_row = QHBoxLayout()
        self._file_edit = QLineEdit(file_path)
        self._file_edit.setPlaceholderText("Library file path…")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self._file_edit, 1)
        file_row.addWidget(browse_btn)
        form.addRow("File:", file_row)

        self._corner_label = QLabel("Corner:")
        self._corner_edit = QLineEdit(corner)
        self._corner_edit.setPlaceholderText("optional, e.g. TT")
        form.addRow(self._corner_label, self._corner_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._directive_combo.currentTextChanged.connect(self._update_corner_visibility)
        self._sim_combo.currentTextChanged.connect(self._update_corner_visibility)
        self._update_corner_visibility()

    def _update_corner_visibility(self) -> None:
        show = (self._directive_combo.currentText() == ".lib"
                and self._sim_combo.currentText() == "SPICE")
        self._corner_label.setVisible(show)
        self._corner_edit.setVisible(show)

    def _browse(self) -> None:
        from . import project
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Library File",
            self._file_edit.text() or str(project.subdir("lib")),
            "Library Files (*.lib *.spi *.sp *.inc);;All Files (*)",
        )
        if path:
            self._file_edit.setText(path)

    # ── result accessors ──────────────────────────────────────────────────────

    def directive(self) -> str:
        return self._directive_combo.currentText().lstrip(".")

    def simulator(self) -> str:
        return self._sim_combo.currentText()

    def file_path(self) -> str:
        return self._file_edit.text().strip()

    def corner(self) -> str:
        if self.directive() == "lib" and self.simulator() == "SPICE":
            return self._corner_edit.text().strip()
        return ""
