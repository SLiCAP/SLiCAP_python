"""
Add / Edit a .model definition.

Workflow (Anton, 2026-07-12, same pattern as the Circuit-parameters dialog):
- "Show on schematic" checked (new definition): the action button reads
  "Place"; with LaTeX rendering enabled it first shows the modal LaTeX
  preview (Close = back to editing, OK = accept), then the caller runs the
  click-to-place ghost.
- Unchecked: the button reads "OK" — the definition is accepted without
  placement; the (hidden) item still netlists its .model line.
- Edit mode: the button reads "OK"; changes apply in place.  Entering the
  name of an EXISTING model in the Place-menu dialog edits that definition
  in place (the route back to a hidden one), like the library-link dialog.

The block's on-canvas SCALE is a schematic preference (Preferences →
"Scaling defaults"), deliberately not settable here.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QDialogButtonBox,
    QCheckBox, QFileDialog, QApplication, QLayout,
)
from PySide6.QtCore import Qt


def _slicap_model_types() -> list:
    try:
        from SLiCAP.SLiCAPprotos import _MODELS
        return sorted(_MODELS.keys())
    except Exception:
        return []


def _model_param_names(model_type: str) -> list:
    """Standard SLiCAP parameter names for the given model type."""
    try:
        from SLiCAP.SLiCAPprotos import _MODELS
        m = _MODELS.get(model_type)
        if m:
            return list(m.params.keys())
    except Exception:
        pass
    return []


def _find_slicap_preamble() -> str:
    from .parameter_dialog import _find_slicap_preamble as _find
    return _find()


class ModelDialog(QDialog):
    """Add / Edit a .model definition."""

    def __init__(self, model_name: str = "", model_type: str = "",
                 simulator: str = "SLiCAP", params=None,
                 preamble_path: str = "",
                 show: bool = True,
                 edit_mode: bool = False,
                 style=None,
                 parent=None):
        super().__init__(parent, Qt.Window)
        from .config import default_style
        from .latex_label import LATEX_INSTALLED
        self._style = style or default_style()
        # Preview rendering needs the tools AND the schematic's preference.
        self._latex_ok = LATEX_INSTALLED and self._style.LATEX_RENDERING_ENABLED
        self._edit_mode = edit_mode
        self.setWindowTitle("Add / Edit Model Definition")
        self.setMinimumWidth(520)
        self._is_editing = bool(params)

        outer = QVBoxLayout(self)
        outer.setSizeConstraint(QLayout.SetMinimumSize)

        # ── type / name ───────────────────────────────────────────────────────
        form = QFormLayout()

        self._type_combo = QComboBox()
        form.addRow("Model type:", self._type_combo)

        self._name_edit = QLineEdit(model_name)
        form.addRow("Model name:", self._name_edit)

        outer.addLayout(form)

        # ── preamble row ──────────────────────────────────────────────────────
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preamble:"))
        self._preamble_edit = QLineEdit(preamble_path or _find_slicap_preamble())
        self._preamble_edit.setReadOnly(True)
        self._preamble_edit.setPlaceholderText("(default: amsmath + amssymb)")
        self._preamble_edit.setMinimumWidth(260)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_preamble)
        clear_btn  = QPushButton("Clear")
        clear_btn.clicked.connect(self._preamble_edit.clear)
        prow.addWidget(self._preamble_edit, stretch=1)
        prow.addWidget(browse_btn)
        prow.addWidget(clear_btn)
        outer.addLayout(prow)

        # ── parameter table ───────────────────────────────────────────────────
        outer.addWidget(QLabel("Parameters (name = value):"))
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Name", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(120)
        outer.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self._add_row)
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_selected_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        outer.addLayout(btn_row)

        # ── show on schematic ─────────────────────────────────────────────────
        self._show_cb = QCheckBox("Show on schematic (the .model line is always netlisted)")
        self._show_cb.setChecked(show)
        self._show_cb.toggled.connect(self._update_action_button)
        outer.addWidget(self._show_cb)

        # ── action buttons ────────────────────────────────────────────────────
        self._btn_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self._action_btn = QPushButton()
        self._btn_box.addButton(self._action_btn, QDialogButtonBox.AcceptRole)
        self._btn_box.accepted.connect(self._on_action)
        self._btn_box.rejected.connect(self.reject)
        outer.addWidget(self._btn_box)
        self._update_action_button()

        # Populate type combo first (without triggering signals) then connect.
        self._populate_type_combo(model_type)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)

        if self._is_editing:
            for name, value in (params or []):
                self._add_row(name, value)
        else:
            self._refill_params()

    # ── type-combo helpers ────────────────────────────────────────────────────

    def _populate_type_combo(self, select: str = "") -> None:
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        self._type_combo.addItems(_slicap_model_types())
        if select:
            idx = self._type_combo.findText(select)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
        self._type_combo.blockSignals(False)

    def _refill_params(self) -> None:
        self._table.setRowCount(0)
        for name in _model_param_names(self._type_combo.currentText()):
            self._add_row(name, "")

    def _on_type_changed(self, _: str) -> None:
        if not self._is_editing:
            self._refill_params()

    # ── table helpers ─────────────────────────────────────────────────────────

    def _add_row(self, name: str = "", value: str = "") -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name or ""))
        self._table.setItem(row, 1, QTableWidgetItem(value or ""))

    def _remove_selected_row(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()},
                      reverse=True)
        if rows:
            for r in rows:
                self._table.removeRow(r)
        else:
            rc = self._table.rowCount()
            if rc > 0:
                self._table.removeRow(rc - 1)

    # ── preamble helpers ──────────────────────────────────────────────────────

    def _browse_preamble(self) -> None:
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Preamble File",
            self._preamble_edit.text() or str(Path.home()),
            "LaTeX Files (*.tex);;All Files (*)",
        )
        if path:
            self._preamble_edit.setText(path)

    # ── action ────────────────────────────────────────────────────────────────

    def _update_action_button(self) -> None:
        place = self._show_cb.isChecked() and not self._edit_mode
        self._action_btn.setText("Place" if place else "OK")

    def _on_action(self) -> None:
        if self._latex_ok:
            from .latex_label import render_latex_raw
            from .model_item import ModelItem
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                svg, error = render_latex_raw(
                    ModelItem.build_latex(self.model_name(), self.model_type(),
                                          self._current_params()),
                    self._preamble_edit.text())
            finally:
                QApplication.restoreOverrideCursor()
            if self._action_btn.text() == "Place":
                # Modal LaTeX preview: Close returns to editing, OK accepts.
                from .latex_preview_dialog import LatexPreviewDialog
                if not LatexPreviewDialog(svg, error, self).exec():
                    return                  # back to editing
            elif svg is None:
                # OK mode: surface the error, allow accept-with-fallback.
                from PySide6.QtWidgets import QMessageBox
                if QMessageBox.warning(
                        self, "LaTeX error",
                        "The model definition does not compile:\n\n"
                        f"{error}\n\n"
                        "Accept anyway? (The canvas shows plain text.)",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No) != QMessageBox.Yes:
                    return                  # back to editing
        self.accept()

    # ── result accessors ──────────────────────────────────────────────────────

    def _current_params(self) -> list:
        result = []
        for row in range(self._table.rowCount()):
            n = self._table.item(row, 0)
            v = self._table.item(row, 1)
            name  = n.text().strip() if n else ""
            value = v.text().strip() if v else ""
            if name:
                result.append([name, value])
        return result

    def model_name(self) -> str:
        return self._name_edit.text().strip()

    def model_type(self) -> str:
        return self._type_combo.currentText()

    def simulator(self) -> str:
        return "SLiCAP"

    def get_params(self) -> list:
        return self._current_params()

    def preamble_path(self) -> str:
        return self._preamble_edit.text()

    def show_on_schematic(self) -> bool:
        return self._show_cb.isChecked()
