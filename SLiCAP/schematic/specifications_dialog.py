"""Create / Edit specifications dialog (SLNG.md "Specifications GUI — FINAL
SPEC", 2026-07-15).

A pure CSV editor: it reads a spec CSV with ``csv2specs`` and writes it with
``specs2csv`` (the core functions are the only builders). It emits NOTHING
into the instruction file.  Spec values reach an analysis per instruction,
through ``pardefs=sl.selectPars(...)`` composed in the analysis dialog
(SLNG.md "Instruction files, the main script and selectPars()",
2026-11-01); ``specs2circuit`` stays a function for the user's main script.

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
    QTableWidgetItem, QAbstractItemView, QHeaderView, QStyledItemDelegate,
    QComboBox, QDialogButtonBox, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QColor

from .row_table import RowTable
from .sizing import chars

# canonical specType suggestions (manual "Work with Specifications"); the
# field is editable — the type is free (specItem.specType is a free string)
_CANONICAL_TYPES = ["Interface", "Performance", "Functional",
                    "Environment", "Design"]

_COLS = ["Symbol", "Description", "Value", "Units", "Type"]
_C_SYMBOL, _C_DESC, _C_VALUE, _C_UNITS, _C_TYPE = range(5)


class _TypeEditor(QStyledItemDelegate):
    """The cell editor of the Type column: an editable list of the types
    in use and the canonical ones, open only while the cell is edited. The
    value is the cell's own text, so Tab and sorting treat it as any other
    cell. A combo box placed in every cell was the first form and was
    REPLACED (workshop of 2026-11-17): Tab left the table from it, sorting
    could not see its text and the column was narrower than the box."""

    def __init__(self, suggestions, parent=None):
        super().__init__(parent)
        self._suggestions = suggestions

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(True)
        combo.addItems(self._suggestions())
        return combo

    def setEditorData(self, editor, index):
        editor.setCurrentText(index.data() or "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText().strip())


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
        # Tab on the last cell adds a row, a header click sorts the rows
        # (row_table). Every column can be dragged wider, the last one fills
        # the rest: a stretched Description column in the middle made the
        # Type column narrower than its text and moved the widths
        # strangely when the last one was dragged (workshop of 2026-11-17).
        self._table = RowTable(0, len(_COLS), add_row=self._add_row, sortable=True)
        self._table.setHorizontalHeaderLabels(_COLS)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(True)
        self._table.setColumnWidth(_C_DESC, chars(self._table, 32))
        self._table.setItemDelegateForColumn(
            _C_TYPE, _TypeEditor(self._type_suggestions, self._table))
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
            item = self._table.item(r, _C_TYPE)
            t = item.text().strip() if item is not None else ""
            if t and t not in used:
                used.append(t)
        return used + [t for t in _CANONICAL_TYPES if t not in used]

    def _add_row(self, symbol="", desc="", value="", units="", spectype=""):
        r = self._table.rowCount()
        self._table.insertRow(r)
        for col, text in ((_C_SYMBOL, symbol), (_C_DESC, desc), (_C_VALUE, value),
                          (_C_UNITS, units), (_C_TYPE, spectype)):
            self._table.setItem(r, col, QTableWidgetItem(text))

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
            spectype = (self._table.item(r, _C_TYPE).text().strip()
                        if self._table.item(r, _C_TYPE) else "")
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
