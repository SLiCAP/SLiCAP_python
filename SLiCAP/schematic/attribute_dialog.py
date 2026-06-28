"""Single-attribute editor.

Opened by double-clicking one of a component's text attributes (refdes,
reference, model or a parameter) on the canvas.  It edits just that attribute's
value and its on-canvas visibility — a focused alternative to the full
PropertiesDialog.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLineEdit, QCheckBox,
    QDialogButtonBox, QLabel,
)

from .component_item import ComponentItem, strip_braces


class AttributeDialog(QDialog):
    """Edit one attribute (value + show-value/show-name) of a ComponentItem."""

    def __init__(self, item: ComponentItem, prop_key: str, parent=None):
        super().__init__(parent)
        self._item = item
        self._key = prop_key
        self.setWindowTitle(f"{prop_key} — {item.instance_id}")

        outer = QVBoxLayout(self)
        grid = QGridLayout()
        outer.addLayout(grid)

        grid.addWidget(QLabel(prop_key), 0, 0)
        self._edit = QLineEdit(self._current_value())
        grid.addWidget(self._edit, 0, 1)

        sv, sn = item.prop_display.get(prop_key, (False, False))
        self._sv = QCheckBox("Show value")
        self._sn = QCheckBox("Show name")
        self._sv.setChecked(sv)
        self._sn.setChecked(sn)
        self._sn.setEnabled(sv)
        self._sv.toggled.connect(self._on_show_value)
        grid.addWidget(self._sv, 1, 1)
        grid.addWidget(self._sn, 2, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_show_value(self, on: bool) -> None:
        self._sn.setEnabled(on)
        if not on:
            self._sn.setChecked(False)

    # ── value plumbing ──────────────────────────────────────────────────────────

    def _current_value(self) -> str:
        k = self._key
        if k == "refdes":
            return self._item.instance_id
        if k == "model":
            return self._item.model
        if k.startswith("ref "):
            try:
                idx = int(k.split()[1]) - 1
                return self._item.refs[idx] if idx < len(self._item.refs) else ""
            except (ValueError, IndexError):
                return ""
        return strip_braces(self._item.params.get(k, ""))

    def apply(self) -> None:
        text = self._edit.text().strip()
        k = self._key
        if k == "refdes":
            self._item.instance_id = text
        elif k == "model":
            self._item.model = text
        elif k.startswith("ref "):
            try:
                idx = int(k.split()[1]) - 1
                if 0 <= idx < len(self._item.refs):
                    self._item.refs[idx] = text
            except (ValueError, IndexError):
                pass
        else:
            # Parameter values are stored bare; braces are added at render/netlist.
            self._item.params[k] = strip_braces(text)
        self._item.prop_display[k] = (self._sv.isChecked(), self._sn.isChecked())
        self._item._save_label_offsets()
        self._item.update_labels()
