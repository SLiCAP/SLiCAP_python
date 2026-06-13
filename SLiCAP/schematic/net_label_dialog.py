from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLayout,
    QLineEdit, QCheckBox, QDialogButtonBox, QLabel,
)
from PySide6.QtCore import Qt


class NetLabelDialog(QDialog):
    def __init__(self, current_name: str | None, display: bool,
                 locked: bool = False, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Net Label")
        self.setMinimumWidth(280)

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        form = QFormLayout()
        self._name_edit = QLineEdit(current_name or "")

        if locked:
            self._name_edit.setEnabled(False)   # disables input and greys out reliably
            form.addRow("Net name (port):", self._name_edit)
            outer.addLayout(form)
            note = QLabel("Name is set by the connected port and cannot be changed.")
            note.setWordWrap(True)
            note.setAlignment(Qt.AlignLeft)
            note.setStyleSheet("color: grey; font-style: italic;")
            outer.addWidget(note)
        else:
            self._name_edit.setPlaceholderText("leave blank for auto-number")
            form.addRow("Net name:", self._name_edit)
            outer.addLayout(form)

        self._display_cb = QCheckBox("Display net name on schematic")
        self._display_cb.setChecked(display)
        outer.addWidget(self._display_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        if not locked:
            self._name_edit.setFocus()
        else:
            self._display_cb.setFocus()

    def net_name(self) -> str | None:
        text = self._name_edit.text().strip()
        return text if text else None

    def display(self) -> bool:
        return self._display_cb.isChecked()
