from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QDialogButtonBox,
)
from PySide6.QtCore import Qt


def _slicap_model_types() -> list:
    try:
        from SLiCAP.SLiCAPprotos import _MODELS
        return sorted(_MODELS.keys())
    except Exception:
        return []


def _spice_model_types() -> list:
    try:
        from SLiCAP.SLiCAPprotos import _SPICEMODELS
        return sorted(_SPICEMODELS.keys())
    except Exception:
        return []


def _model_param_names(simulator: str, model_type: str) -> list:
    """Standard parameter names for the given model type."""
    try:
        if simulator == "SLiCAP":
            from SLiCAP.SLiCAPprotos import _MODELS
            m = _MODELS.get(model_type)
            if m:
                return list(m.params.keys())
        else:
            from SLiCAP.SLiCAPprotos import _SPICEMODELS
            return list(_SPICEMODELS.get(model_type, []))
    except Exception:
        pass
    return []


class ModelDialog(QDialog):
    """Add / Edit a .model definition."""

    def __init__(self, model_name: str = "", model_type: str = "",
                 simulator: str = "SLiCAP", params=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Add / Edit Model Definition")
        self.setMinimumWidth(480)
        self._is_editing = bool(params)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._name_edit = QLineEdit(model_name)
        self._name_edit.setPlaceholderText("e.g. NMOS_small")
        form.addRow("Model name:", self._name_edit)

        self._sim_combo = QComboBox()
        self._sim_combo.addItems(["SLiCAP", "SPICE"])
        self._sim_combo.setCurrentText(simulator)
        form.addRow("Simulator:", self._sim_combo)

        self._type_combo = QComboBox()
        form.addRow("Model type:", self._type_combo)
        layout.addLayout(form)

        layout.addWidget(QLabel("Parameters (name = value):"))
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Name", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(120)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self._add_empty_row)
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_selected_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Populate the type combo first (without triggering signals) then
        # connect signals so initial fill does not fire _on_type_changed.
        self._populate_type_combo(simulator, model_type)
        self._sim_combo.currentTextChanged.connect(self._on_sim_changed)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)

        if self._is_editing:
            for name, value in (params or []):
                self._add_row(name, value)
        else:
            self._refill_params()

    # ── private ───────────────────────────────────────────────────────────────

    def _populate_type_combo(self, simulator: str, select: str = "") -> None:
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        items = (_slicap_model_types() if simulator == "SLiCAP"
                 else _spice_model_types())
        self._type_combo.addItems(items)
        if select:
            idx = self._type_combo.findText(select)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
        self._type_combo.blockSignals(False)

    def _refill_params(self) -> None:
        self._table.setRowCount(0)
        for name in _model_param_names(self._sim_combo.currentText(),
                                        self._type_combo.currentText()):
            self._add_row(name, "")

    def _on_sim_changed(self, sim: str) -> None:
        self._populate_type_combo(sim, self._type_combo.currentText())
        if not self._is_editing:
            self._refill_params()

    def _on_type_changed(self, _: str) -> None:
        if not self._is_editing:
            self._refill_params()

    def _add_row(self, name: str = "", value: str = "") -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        self._table.setItem(row, 1, QTableWidgetItem(value))

    def _add_empty_row(self) -> None:
        self._add_row()

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

    # ── result accessors ──────────────────────────────────────────────────────

    def model_name(self) -> str:
        return self._name_edit.text().strip()

    def model_type(self) -> str:
        return self._type_combo.currentText()

    def simulator(self) -> str:
        return self._sim_combo.currentText()

    def get_params(self) -> list:
        result = []
        for row in range(self._table.rowCount()):
            n = self._table.item(row, 0)
            v = self._table.item(row, 1)
            name  = n.text().strip() if n else ""
            value = v.text().strip() if v else ""
            if name:
                result.append([name, value])
        return result
