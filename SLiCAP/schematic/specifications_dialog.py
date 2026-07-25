"""Create / Edit specifications dialog (SLNG.md "Specifications GUI — FINAL
SPEC", 2026-07-15).

A pure CSV editor: it reads a spec CSV with ``csv2specs`` and writes it with
``specs2csv`` (the core functions are the only builders). It emits NOTHING
into the instruction file — assigning specs to a circuit (``specs2circuit``)
lives in the user's design-step scripts, per command, per Anton's
iterative-flow decision.

The value field takes any SLiCAP expression, validated with
``_checkExpression`` on OK (empty allowed — a spec without an assigned value
is legitimate). 0/1 can serve as boolean flags; a first-class typed-value
model (boolean/enum/integer/min-typ-max) is an ACDE Phase 3 concern
(ACDE.md "Typed specification values"), deliberately not faked here.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QComboBox, QDialogButtonBox, QFileDialog, QMessageBox, QWidget,
)
from PySide6.QtGui import QColor

# canonical specType suggestions (manual "Work with Specifications"); the
# field is editable — the type is free (specItem.specType is a free string)
_CANONICAL_TYPES = ["Interface", "Performance", "Functional",
                    "Environment", "Design"]

_COLS = ["Symbol", "Description", "Value", "Units", "Type"]
_C_SYMBOL, _C_DESC, _C_VALUE, _C_UNITS, _C_TYPE = range(5)


class SpecificationsDialog(QDialog):
    """Editor for one spec CSV file in the project csv/ folder."""

    def __init__(self, csv_dir: str, file_name: str = "specs.csv",
                 parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit specifications")
        self.resize(760, 420)
        self._csv_dir = csv_dir

        outer = QVBoxLayout(self)

        # ── file row ─────────────────────────────────────────────────────
        frow = QHBoxLayout()
        frow.addWidget(QLabel("File:"))
        self._file = QLineEdit(file_name)
        frow.addWidget(self._file, 1)
        load_btn = QPushButton("Load…")
        load_btn.clicked.connect(self._on_load)
        frow.addWidget(load_btn)
        outer.addLayout(frow)

        # ── table ────────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(_C_DESC, QHeaderView.Stretch)
        for c in (_C_SYMBOL, _C_VALUE, _C_UNITS, _C_TYPE):
            hdr.setSectionResizeMode(c, QHeaderView.Interactive)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        outer.addWidget(self._table, 1)

        brow = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self._add_row())
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_row)
        brow.addWidget(add_btn)
        brow.addWidget(del_btn)
        brow.addStretch(1)
        outer.addLayout(brow)

        hint = QLabel("Value: any SLiCAP expression (blank = no assigned "
                      "value). Use 0 or 1 for boolean flags. Specifications "
                      "are grouped by Type in reports and the viewer.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(hint)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save
                                         | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self._on_save)
        self._buttons.rejected.connect(self.reject)
        outer.addWidget(self._buttons)

        # auto-load if the default file exists (Create/Edit = one flow)
        path = os.path.join(csv_dir, file_name)
        if os.path.isfile(path):
            self._load_file(path)
        else:
            self._add_row()

    # ── rows ─────────────────────────────────────────────────────────────

    def _type_suggestions(self) -> list:
        """Types already used in the table, then the canonical SE types not
        yet present — so a custom type coined in one row is offered in every
        row (Anton, 2026-07-15: free typing must not fragment into typo'd
        specTypes, which would split into separate report tables). The
        canonical five stay as the structured-design nudge."""
        used = []
        for r in range(self._table.rowCount()):
            w = self._table.cellWidget(r, _C_TYPE)
            t = w.currentText().strip() if w else ""
            if t and t not in used:
                used.append(t)
        return used + [t for t in _CANONICAL_TYPES if t not in used]

    def _type_combo(self, value=""):
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(self._type_suggestions())
        combo.setCurrentText(value)
        # when a row's type changes, refresh every combo's suggestion list
        combo.editTextChanged.connect(self._refresh_type_suggestions)
        return combo

    def _refresh_type_suggestions(self, *_):
        suggestions = self._type_suggestions()
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, _C_TYPE)
            if combo is None:
                continue
            cur = combo.currentText()
            combo.blockSignals(True)          # no re-entrant refresh cascade
            combo.clear()
            items = list(suggestions)
            if cur and cur not in items:       # keep what's being typed
                items.insert(0, cur)
            combo.addItems(items)
            combo.setEditText(cur)
            combo.blockSignals(False)

    def _add_row(self, symbol="", desc="", value="", units="", spectype=""):
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setItem(r, _C_SYMBOL, QTableWidgetItem(symbol))
        self._table.setItem(r, _C_DESC, QTableWidgetItem(desc))
        self._table.setItem(r, _C_VALUE, QTableWidgetItem(value))
        self._table.setItem(r, _C_UNITS, QTableWidgetItem(units))
        self._table.setCellWidget(r, _C_TYPE, self._type_combo(spectype))
        self._refresh_type_suggestions()

    def _remove_row(self):
        r = self._table.currentRow()
        if r >= 0:
            self._table.removeRow(r)

    # ── file operations ──────────────────────────────────────────────────

    def _on_load(self):
        fn, _ = QFileDialog.getOpenFileName(
            self, "Load specifications", self._csv_dir, "CSV files (*.csv)")
        if fn:
            self._file.setText(os.path.basename(fn))
            self._table.setRowCount(0)
            self._load_file(fn)

    def _load_file(self, path):
        from SLiCAP.SLiCAPdesignData import csv2specs
        # csv2specs reads from ini.csv_path; call it with the bare name when
        # the file is in the project csv/ dir, else parse the given path
        try:
            import SLiCAP.SLiCAPconfigure as ini
            if os.path.dirname(os.path.abspath(path)) == \
                    os.path.abspath(self._csv_dir):
                specs = csv2specs(os.path.basename(path))
            else:
                specs = _read_specs_any(path)
        except Exception as e:
            QMessageBox.critical(self, "Load failed",
                                 f"Could not read {path}:\n{e}")
            return
        for s in specs:
            self._add_row(str(s.symbol), s.description,
                          "" if s.value == "" else str(s.value),
                          s.units, s.specType)
        if self._table.rowCount() == 0:
            self._add_row()

    def _collect(self):
        """(rows, error) — rows as specItem, or a validation error string."""
        from SLiCAP.SLiCAPdesignData import specItem
        from SLiCAP.SLiCAPmath import _checkExpression
        import sympy as sp
        rows, seen = [], set()
        # clear prior highlights
        for r in range(self._table.rowCount()):
            for c in (_C_SYMBOL, _C_VALUE):
                it = self._table.item(r, c)
                if it:
                    it.setBackground(QColor(0, 0, 0, 0))
        for r in range(self._table.rowCount()):
            sym = (self._table.item(r, _C_SYMBOL).text().strip()
                   if self._table.item(r, _C_SYMBOL) else "")
            if not sym:
                continue                      # skip blank rows silently
            if not sym.isidentifier():
                self._mark(r, _C_SYMBOL)
                return None, f"Row {r + 1}: '{sym}' is not a valid symbol."
            if sym in seen:
                self._mark(r, _C_SYMBOL)
                return None, f"Row {r + 1}: symbol '{sym}' is duplicated."
            seen.add(sym)
            val = (self._table.item(r, _C_VALUE).text().strip()
                   if self._table.item(r, _C_VALUE) else "")
            if val:
                # _checkExpression returns None on a parse failure (it does
                # not raise) — test identity, since a valid "0" is sympy
                # Zero (falsy but valid)
                if _checkExpression(val) is None:
                    self._mark(r, _C_VALUE)
                    return None, f"Row {r + 1}: '{val}' is not a valid value."
            desc = (self._table.item(r, _C_DESC).text()
                    if self._table.item(r, _C_DESC) else "")
            units = (self._table.item(r, _C_UNITS).text().strip()
                     if self._table.item(r, _C_UNITS) else "")
            spectype = self._table.cellWidget(r, _C_TYPE).currentText().strip()
            rows.append(specItem(sym, desc, val, units, spectype))
        return rows, None

    def _mark(self, row, col):
        it = self._table.item(row, col)
        if it:
            it.setBackground(QColor(255, 210, 210))

    def _on_save(self):
        from SLiCAP.SLiCAPdesignData import specs2csv
        name = self._file.text().strip()
        if not name:
            QMessageBox.warning(self, "No file name",
                                "Enter a file name for the specifications.")
            return
        if not name.endswith(".csv"):
            name += ".csv"
        rows, err = self._collect()
        if err:
            QMessageBox.warning(self, "Invalid specification", err)
            return
        try:
            specs2csv(rows, name)          # writes to ini.csv_path
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return
        self.saved_name = name
        self.accept()


def _read_specs_any(path):
    """csv2specs for a file OUTSIDE the project csv/ dir (Load… browse)."""
    from SLiCAP.SLiCAPdesignData import specItem
    out = []
    with open(path) as f:
        lines = f.readlines()
    for line in lines[1:]:
        args = line.rstrip("\n").split(",")
        if len(args) < 5 or not args[0].strip():
            continue
        item = specItem(args[0], args[1], args[2], args[3], args[4])
        item.description = item.description.replace("&#44;", ",")
        out.append(item)
    return out
