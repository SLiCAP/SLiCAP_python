from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
    QLabel, QFrame, QLayout,
)
from PySide6.QtCore import Qt

from .component_item import ComponentItem


class PowerSymbolDialog(QDialog):
    """
    Minimal properties dialog for power symbols (ground, port).
    Only exposes the net name and orientation — no refdes, no model, no params.
    """

    def __init__(self, item: ComponentItem, parent=None):
        super().__init__(parent, Qt.Window)
        self._item = item
        self.setWindowTitle(f"Net name — {item.symbol_name}")

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        # ── net name ──────────────────────────────────────────────────────────
        name_grid = QGridLayout()
        name_grid.setColumnStretch(1, 1)
        _name = item.params.get("name") or ("0" if item.symbol_name == "ground" else "")
        self._name_edit = QLineEdit(_name)
        name_grid.addWidget(QLabel("Net name"), 0, 0)
        name_grid.addWidget(self._name_edit, 0, 1)
        outer.addLayout(name_grid)

        # ── orientation ───────────────────────────────────────────────────────
        outer.addWidget(_hline())
        orient = QGridLayout()

        self._rotation_combo = QComboBox()
        self._rotation_combo.addItems(["0°", "90°", "180°", "270°"])
        _rot = round(item.rotation()) % 360
        self._rotation_combo.setCurrentIndex(_rot // 90)
        orient.addWidget(QLabel("Rotation"),          0, 0)
        orient.addWidget(self._rotation_combo,         0, 1)

        self._hflip_cb = QCheckBox()
        self._hflip_cb.setChecked(item.h_flip)
        orient.addWidget(QLabel("Mirror horizontal"), 1, 0)
        orient.addWidget(self._hflip_cb,              1, 1)

        self._vflip_cb = QCheckBox()
        self._vflip_cb.setChecked(item.v_flip)
        orient.addWidget(QLabel("Mirror vertical"),   2, 0)
        orient.addWidget(self._vflip_cb,              2, 1)

        outer.addLayout(orient)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._name_edit.setFocus()
        self._name_edit.selectAll()

    def apply(self) -> None:
        self._item.params["name"] = self._name_edit.text().strip()

        self._item.setRotation(self._rotation_combo.currentIndex() * 90)
        self._item.h_flip = self._hflip_cb.isChecked()
        self._item.v_flip = self._vflip_cb.isChecked()
        self._item.apply_transform()

        self._item._save_label_offsets()
        self._item.update_labels()


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line
