from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
    QCheckBox, QDialogButtonBox, QLayout,
)


class BorderDialog(QDialog):
    """Dialog for setting export border dimensions and visibility."""

    def __init__(self, width: int = 400, height: int = 300,
                 show_in_export: bool = True, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Border")
        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)

        self._w_spin = QSpinBox()
        self._w_spin.setRange(10, 10000)
        self._w_spin.setValue(width)
        self._w_spin.setSuffix(" units")
        grid.addWidget(QLabel("Width"),  0, 0)
        grid.addWidget(self._w_spin,     0, 1)

        self._h_spin = QSpinBox()
        self._h_spin.setRange(10, 10000)
        self._h_spin.setValue(height)
        self._h_spin.setSuffix(" units")
        grid.addWidget(QLabel("Height"), 1, 0)
        grid.addWidget(self._h_spin,     1, 1)

        outer.addLayout(grid)

        hint = QLabel("(1 grid square = 5 units,  resistor pin-to-pin = 50 units)")
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(hint)

        self._show_cb = QCheckBox("Include border line in export")
        self._show_cb.setChecked(show_in_export)
        outer.addWidget(self._show_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def border_width(self) -> int:
        return self._w_spin.value()

    def border_height(self) -> int:
        return self._h_spin.value()

    def show_in_export(self) -> bool:
        return self._show_cb.isChecked()
