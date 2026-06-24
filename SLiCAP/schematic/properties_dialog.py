from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QCheckBox, QDialogButtonBox, QPushButton,
    QLabel, QWidget, QFrame, QLayout,
)
from PySide6.QtCore import Qt

import html

from . import project
from .component_item import (
    ComponentItem, available_models, params_for_symbol,
    fixed_params_for_symbol, refs_for_symbol, strip_braces,
    SYMBOL_DESCRIPTION, SYMBOL_INFO, SYMBOL_PREFIX,
)

_HDR_ROW    = 0
_SEP_ROW    = 1
_REFDES_ROW = 2
_MODEL_ROW  = 3


class PropertiesDialog(QDialog):
    """
    Edit all properties of a ComponentItem.

    Columns: Property | Edit value | Show value | Show name

    "Show value" controls whether a label appears at all for that property.
    "Show name" prefixes the value with "<name>: " — only active when
    "Show value" is also on (the checkbox is disabled otherwise).
    """

    def __init__(self, item: ComponentItem, parent=None):
        super().__init__(parent, Qt.Window)
        self._item = item
        self.setWindowTitle(f"Properties — {item.instance_id}")

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        # ── description + clickable info link (from the symbol's data-* meta) ──
        desc = SYMBOL_DESCRIPTION.get(item.symbol_name, "")
        info = SYMBOL_INFO.get(item.symbol_name, "")
        if desc or info:
            head = QLabel()
            head.setTextFormat(Qt.RichText)
            head.setOpenExternalLinks(True)        # open the link in the browser
            head.setWordWrap(True)
            head.setMaximumWidth(360)
            lines = []
            if desc:
                lines.append(f"<b>{html.escape(desc)}</b>")
            if info:
                url = html.escape(info, quote=True)
                lines.append(f'<a href="{url}">{html.escape(info)}</a>')
            head.setText("<br>".join(lines))
            outer.addWidget(head)
            outer.addWidget(_hline())

        # ── single grid for all property rows ─────────────────────────────────
        # Using one shared QGridLayout ensures columns 2 & 3 (checkboxes) align
        # across headers, refdes, model and params rows.
        self._grid = QGridLayout()
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnMinimumWidth(2, 72)
        self._grid.setColumnMinimumWidth(3, 72)

        # Headers
        for col, text in enumerate(("<b>Property</b>", "<b>Value</b>",
                                    "<b>Show val.</b>", "<b>Show name</b>")):
            lbl = QLabel(text)
            if col >= 2:
                lbl.setAlignment(Qt.AlignCenter)
            self._grid.addWidget(lbl, _HDR_ROW, col)
        self._grid.addWidget(_hline(), _SEP_ROW, 0, 1, 4)

        # Refdes row
        self._ref_edit = QLineEdit(item.instance_id)
        sv_ref, sn_ref = item.prop_display.get("refdes", (True, False))
        self._ref_sv, self._ref_sn = _make_pair(sv_ref, sn_ref)
        self._grid.addWidget(QLabel("refdes"), _REFDES_ROW, 0)
        self._grid.addWidget(self._ref_edit,   _REFDES_ROW, 1)
        self._grid.addWidget(self._ref_sv,     _REFDES_ROW, 2, Qt.AlignCenter)
        self._grid.addWidget(self._ref_sn,     _REFDES_ROW, 3, Qt.AlignCenter)

        # Model row — a free text field: the model is the SLiCAP model name (or,
        # for an X block, the subcircuit name) and the user must be able to type
        # any value, not just pick from the symbol's single data-model default.
        self._models = available_models(item.symbol_name)
        if self._models:
            self._model_edit = QLineEdit(item.model)
            sv_mod, sn_mod = item.prop_display.get("model", (False, False))
            self._model_sv, self._model_sn = _make_pair(sv_mod, sn_mod)
            self._grid.addWidget(QLabel("model"),  _MODEL_ROW, 0)
            self._grid.addWidget(self._model_edit, _MODEL_ROW, 1)
            self._grid.addWidget(self._model_sv,   _MODEL_ROW, 2, Qt.AlignCenter)
            self._grid.addWidget(self._model_sn,   _MODEL_ROW, 3, Qt.AlignCenter)
            self._params_start = _MODEL_ROW + 1
        else:
            self._model_edit = None
            self._model_sv = self._model_sn = None
            self._params_start = _MODEL_ROW

        # Dynamic params rows
        self._param_edits:   dict[str, QLineEdit] = {}
        self._param_sv:      dict[str, QCheckBox] = {}
        self._param_sn:      dict[str, QCheckBox] = {}
        self._param_widgets: list[QWidget]        = []
        self._params_count:  int                  = 0
        # Dynamic refs rows (live inside self._grid after params)
        self._ref_edits:     list[QLineEdit]      = []
        self._ref_sv_checks: list[QCheckBox]      = []
        self._ref_sn_checks: list[QCheckBox]      = []
        self._ref_widgets:   list[QWidget]        = []
        current_model = self._model_edit.text() if self._model_edit else item.model
        self._rebuild_params(current_model, item.params, item.prop_display)
        self._rebuild_refs(current_model, item.refs, item.prop_display)

        outer.addLayout(self._grid)

        # ── orientation section ───────────────────────────────────────────────
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

        # ── descend hierarchy (subcircuit blocks only) ──────────────────────────
        # An X block's source is sch/<model>.slicap_sch; descending opens it in a
        # new editable window so the user can inspect and edit the subcircuit.
        self._descend_path: Path | None = None
        if SYMBOL_PREFIX.get(item.symbol_name) == "X":
            src = project.subdir("sch") / f"{item.model}.slicap_sch"
            btn = QPushButton("Descend into subcircuit")
            if src.is_file():
                btn.clicked.connect(lambda: self._descend(src))
            else:
                btn.setEnabled(False)
                btn.setToolTip(f"Source schematic not found: sch/{src.name}")
            outer.addWidget(btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _descend(self, src: Path) -> None:
        """Close the dialog and signal the caller to open ``src`` for editing."""
        self._descend_path = src
        self.reject()

    def descend_path(self) -> "Path | None":
        return self._descend_path

    # ── helpers ───────────────────────────────────────────────────────────────

    def _rebuild_params(
        self,
        model_name: str,
        existing_values: dict[str, str],
        existing_display: dict[str, tuple[bool, bool]],
    ) -> None:
        for w in self._param_widgets:
            self._grid.removeWidget(w)
            w.deleteLater()
        self._param_widgets.clear()
        self._param_edits.clear()
        self._param_sv.clear()
        self._param_sn.clear()

        param_keys = list(params_for_symbol(self._item.symbol_name).keys()) or list(fixed_params_for_symbol(self._item.symbol_name).keys())
        for i, name in enumerate(param_keys):
            row = self._params_start + i
            sv_val, sn_val = existing_display.get(name, (True, False) if name == "value" else (False, False))
            lbl  = QLabel(name)
            edit = QLineEdit(strip_braces(existing_values.get(name, "")))
            sv, sn = _make_pair(sv_val, sn_val)
            self._grid.addWidget(lbl,  row, 0)
            self._grid.addWidget(edit, row, 1)
            self._grid.addWidget(sv,   row, 2, Qt.AlignCenter)
            self._grid.addWidget(sn,   row, 3, Qt.AlignCenter)
            self._param_widgets.extend([lbl, edit, sv, sn])
            self._param_edits[name] = edit
            self._param_sv[name]    = sv
            self._param_sn[name]    = sn
        self._params_count = len(param_keys)

    def _rebuild_refs(self, model_name: str, existing: list[str],
                      existing_display: dict | None = None) -> None:
        if existing_display is None:
            existing_display = self._item.prop_display
        for w in self._ref_widgets:
            self._grid.removeWidget(w)
            w.deleteLater()
        self._ref_widgets.clear()
        self._ref_edits.clear()
        self._ref_sv_checks.clear()
        self._ref_sn_checks.clear()

        n = refs_for_symbol(self._item.symbol_name)
        start = self._params_start + self._params_count
        for i in range(n):
            key  = f"ref {i + 1}"
            row  = start + i
            sv_val, sn_val = existing_display.get(key, (True, False))
            lbl  = QLabel(key)
            edit = QLineEdit(existing[i] if i < len(existing) else "")
            sv, sn = _make_pair(sv_val, sn_val)
            self._grid.addWidget(lbl,  row, 0)
            self._grid.addWidget(edit, row, 1)
            self._grid.addWidget(sv,   row, 2, Qt.AlignCenter)
            self._grid.addWidget(sn,   row, 3, Qt.AlignCenter)
            self._ref_widgets.extend([lbl, edit, sv, sn])
            self._ref_edits.append(edit)
            self._ref_sv_checks.append(sv)
            self._ref_sn_checks.append(sn)

    # ── apply ─────────────────────────────────────────────────────────────────

    def apply(self) -> None:
        self._item.instance_id = self._ref_edit.text().strip()

        disp: dict[str, tuple[bool, bool]] = {}
        disp["refdes"] = (self._ref_sv.isChecked(), self._ref_sn.isChecked())

        if self._model_edit is not None:
            self._item.model = self._model_edit.text().strip()
            disp["model"] = (self._model_sv.isChecked(), self._model_sn.isChecked())

        self._item.params = {n: strip_braces(e.text()) for n, e in self._param_edits.items()}
        for name in self._param_sv:
            disp[name] = (self._param_sv[name].isChecked(),
                          self._param_sn[name].isChecked())

        self._item.refs = [e.text().strip() for e in self._ref_edits]
        for i in range(len(self._ref_edits)):
            key = f"ref {i + 1}"
            disp[key] = (self._ref_sv_checks[i].isChecked(),
                         self._ref_sn_checks[i].isChecked())

        self._item.setRotation(self._rotation_combo.currentIndex() * 90)
        self._item.h_flip = self._hflip_cb.isChecked()
        self._item.v_flip = self._vflip_cb.isChecked()
        self._item.apply_transform()

        self._item._save_label_offsets()
        self._item.prop_display = disp
        self._item.update_labels()


# ── helpers ───────────────────────────────────────────────────────────────────

def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def _make_pair(sv_checked: bool, sn_checked: bool) -> tuple[QCheckBox, QCheckBox]:
    """
    Create a linked (show-value, show-name) checkbox pair.
    'show name' is disabled whenever 'show value' is off.
    """
    sv = QCheckBox()
    sn = QCheckBox()
    sv.setChecked(sv_checked)
    sn.setChecked(sn_checked)
    sn.setEnabled(sv_checked)

    def _on_sv(state):
        enabled = bool(state)
        sn.setEnabled(enabled)
        if not enabled:
            sn.setChecked(False)

    sv.stateChanged.connect(_on_sv)
    return sv, sn
