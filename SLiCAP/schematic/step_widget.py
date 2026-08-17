"""Shared parameter-stepping widget for the instruction dialogs.

Methods ``lin`` / ``log`` (start, stop, num), ``list`` (explicit values) and
``array`` (several parameters, one value set per run).  The emitted step-dict
literal follows the back-end's key convention:

- key_style ``"slicap"``  → key ``"params"`` (always plural); array values
  are emitted with one row **per parameter** (``stepArray[j][i]``: variable
  j, run i).  Values may be expressions/suffix notation → quoted strings.
- key_style ``"ngspice"`` → key ``"param"`` (singular) for lin/log/list and
  ``"params"`` for array; array values are emitted with one row **per run**
  (``_step_values``: shape (n_runs, n_params)) — the widget transposes its
  per-parameter rows.  All values must be plain numbers (the NGspice step
  path converts with ``dtype=float``).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal

from .value_fields import watch
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QStackedWidget, QWidget, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView,
)

from .param_table import PARAM_NAME_WIDTH


class StepWidget(QGroupBox):
    """Checkable "Parameter stepping" group box; see the module docstring."""

    changed = Signal()

    def __init__(self, param_candidates=(), key_style: str = "slicap",
                 methods=("lin", "log", "list", "array"), parent=None):
        super().__init__("Parameter stepping", parent)
        self._style = key_style
        self._numeric_only = key_style == "ngspice"
        self._candidates = [str(p) for p in param_candidates]
        # TEMP is a whole-circuit property in NGspice (swept via `option temp`,
        # not a .param) — offer it as a ready-made choice so the reserved name
        # is never mistyped.  SLiCAP's symbolic back-end has no such step.
        if self._style == "ngspice" and not any(
                c.lower() == "temp" for c in self._candidates):
            self._candidates.append("TEMP")
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(lambda *_: self.changed.emit())

        outer = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Method"))
        self._method = QComboBox()
        self._method.addItems(list(methods))
        self._method.currentIndexChanged.connect(self._on_method)
        self._method.setMaximumWidth(80)
        row.addWidget(self._method)
        self._param_lbl = QLabel("Parameter")
        row.addSpacing(12)
        row.addWidget(self._param_lbl)
        self._param = QComboBox()
        self._param.setEditable(True)
        self._param.addItems(self._candidates)
        self._param.setCurrentText("")
        self._param.setMinimumWidth(120)
        self._param.currentTextChanged.connect(lambda *_: self.changed.emit())
        row.addWidget(self._param)
        row.addStretch(1)
        outer.addLayout(row)

        self._stack = QStackedWidget()

        # page 0 — lin/log range
        rng = QWidget()
        rg = QGridLayout(rng)
        self._start = QLineEdit()
        self._stop = QLineEdit()
        self._num = QLineEdit()
        for r, (lbl, edit, ph) in enumerate([("Start", self._start, "e.g. 100"),
                                             ("Stop", self._stop, "e.g. 1k"),
                                             ("Num", self._num, "e.g. 11")]):
            rg.addWidget(QLabel(lbl), r, 0, Qt.AlignmentFlag.AlignRight)
            edit.setPlaceholderText(ph)
            edit.setMaximumWidth(120)
            edit.textChanged.connect(lambda *_: self.changed.emit())
            # marked while the text is not a number in SLiCAP notation; the
            # value was already refused by dict_literal(), this makes the
            # refusal visible where it happens (value_fields)
            watch(edit, "number")
            rg.addWidget(edit, r, 1)
        rg.setColumnStretch(2, 1)
        rg.setRowStretch(3, 1)              # keep the rows together at the top
        self._stack.addWidget(rng)

        # page 1 — value list
        lst = QWidget()
        lv = QVBoxLayout(lst)
        ll = QHBoxLayout()
        ll.addWidget(QLabel("Values:"))
        self._values = QLineEdit()
        self._values.setPlaceholderText("space-separated, e.g. 100 200 500 1000")
        self._values.textChanged.connect(lambda *_: self.changed.emit())
        watch(self._values, "numbers")
        ll.addWidget(self._values)
        lv.addLayout(ll)
        lv.addStretch(1)
        self._stack.addWidget(lst)

        # page 2 — array: one row per parameter, one value set per run
        arr = QWidget()
        al = QVBoxLayout(arr)
        self._array = QTableWidget(0, 2)
        self._array.setHorizontalHeaderLabels(
            ["Parameter", "Values (space-separated, one per run)"])
        hh = self._array.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)   # user-resizable
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self._array.setColumnWidth(0, PARAM_NAME_WIDTH)
        self._array.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._array.setMinimumHeight(90)
        self._array.itemChanged.connect(lambda *_: self.changed.emit())
        al.addWidget(self._array)
        ab = QHBoxLayout()
        add_btn = QPushButton("Add parameter")
        add_btn.clicked.connect(lambda: self._array_add_row())
        rem_btn = QPushButton("Remove parameter")
        rem_btn.clicked.connect(self._array_remove_row)
        ab.addWidget(add_btn)
        ab.addWidget(rem_btn)
        ab.addStretch(1)
        al.addLayout(ab)
        self._stack.addWidget(arr)

        outer.addWidget(self._stack)
        self._on_method(self._method.currentIndex())

    # ── UI plumbing ───────────────────────────────────────────────────────────

    def _on_method(self, _idx: int) -> None:
        m = self._method.currentText()
        page = 0 if m in ("lin", "log") else (1 if m == "list" else 2)
        self._stack.setCurrentIndex(page)
        single = m != "array"
        self._param_lbl.setVisible(single)
        self._param.setVisible(single)
        self.changed.emit()

    def _array_add_row(self, name: str = "", values: str = "") -> None:
        row = self._array.rowCount()
        self._array.insertRow(row)
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(self._candidates)
        combo.setCurrentText(str(name))
        combo.currentTextChanged.connect(lambda *_: self.changed.emit())
        self._array.setCellWidget(row, 0, combo)
        self._array.setItem(row, 1, QTableWidgetItem(str(values)))
        self.changed.emit()

    def _array_remove_row(self) -> None:
        rows = sorted({i.row() for i in self._array.selectedIndexes()},
                      reverse=True)
        if not rows and self._array.rowCount():
            rows = [self._array.rowCount() - 1]
        for r in rows:
            self._array.removeRow(r)
        self.changed.emit()

    def _array_entries(self) -> list[tuple[str, list[str]]]:
        out = []
        for r in range(self._array.rowCount()):
            w = self._array.cellWidget(r, 0)
            name = w.currentText().strip() if w else ""
            it = self._array.item(r, 1)
            vals = it.text().split() if it else []
            if name:
                out.append((name, vals))
        return out

    # ── emission ──────────────────────────────────────────────────────────────

    def _fmt(self, v: str) -> str | None:
        """Number → raw text; expression → quoted string (SLiCAP only).

        NGspice (numeric-only) values accept SLiCAP scale factors: '5p' is
        emitted as its float value (5e-12)."""
        v = v.strip()
        try:
            float(v)
            return v
        except ValueError:
            pass
        if self._numeric_only:
            try:
                from SLiCAP.SLiCAPlex import _scale_float
                return repr(_scale_float(v))
            except ValueError:
                return None
        return '"' + v.replace('"', "'") + '"'

    def is_valid(self) -> bool:
        return not self.isChecked() or self.dict_literal() is not None

    def set_from_dict(self, d: dict | None) -> None:
        """Prefill from a parsed step dict (append-only editing, SLNG.md).

        *d* is the evaluated ``step=`` / ``stepdict=`` value of an existing
        instruction; None or a malformed dict unchecks the group."""
        if not isinstance(d, dict) or "method" not in d:
            self.setChecked(False)
            return
        self.setChecked(True)
        method = str(d.get("method", "lin"))
        if self._method.findText(method) >= 0:
            self._method.setCurrentText(method)
        param = d.get("param", d.get("params"))
        if method == "array":
            self._array.setRowCount(0)
            names = param if isinstance(param, list) else [param]
            values = d.get("values", [])
            # values: one row of run values per parameter (SLiCAP layout) or
            # rows-per-run (NGspice layout, transposed back for display)
            if values and isinstance(values[0], (list, tuple)) \
                    and len(values) != len(names):
                values = [list(col) for col in zip(*values)]
            for i, name in enumerate(names):
                vals = values[i] if i < len(values) else []
                if not isinstance(vals, (list, tuple)):
                    vals = [vals]
                self._array_add_row(str(name),
                                    " ".join(str(v) for v in vals))
            return
        if isinstance(param, list):
            param = param[0] if param else ""
        self._param.setCurrentText(str(param or ""))
        if method == "list":
            vals = d.get("values", [])
            self._values.setText(" ".join(str(v) for v in vals))
        else:
            self._start.setText(str(d.get("start", "")))
            self._stop.setText(str(d.get("stop", "")))
            self._num.setText(str(d.get("num", "")))

    def dict_literal(self) -> str | None:
        """Step-dict literal for the current state; None if off or incomplete."""
        if not self.isChecked():
            return None
        m = self._method.currentText()
        single_key = "params" if self._style == "slicap" else "param"

        if m in ("lin", "log"):
            p = self._param.currentText().strip()
            s, e, n = (self._start.text().strip(), self._stop.text().strip(),
                       self._num.text().strip())
            if not (p and s and e and n):
                return None
            try:
                int(n)
            except ValueError:
                return None
            fs, fe = self._fmt(s), self._fmt(e)
            if fs is None or fe is None:
                return None
            return (f'{{"method": "{m}", "{single_key}": "{p}", '
                    f'"start": {fs}, "stop": {fe}, "num": {n}}}')

        if m == "list":
            p = self._param.currentText().strip()
            vals = [self._fmt(v) for v in self._values.text().split()]
            if not (p and vals) or None in vals:
                return None
            return (f'{{"method": "list", "{single_key}": "{p}", '
                    f'"values": [{", ".join(vals)}]}}')

        # array
        rows = self._array_entries()
        if not rows:
            return None
        names = [name for name, _ in rows]
        if len(set(names)) != len(names):
            return None
        lengths = {len(vals) for _, vals in rows}
        if len(lengths) != 1 or 0 in lengths:
            return None
        fmt_rows = [[self._fmt(v) for v in vals] for _, vals in rows]
        if any(None in r for r in fmt_rows):
            return None
        if self._style != "slicap":                    # rows per run: transpose
            n_runs = len(fmt_rows[0])
            fmt_rows = [[fmt_rows[j][i] for j in range(len(fmt_rows))]
                        for i in range(n_runs)]
        params_body = ", ".join(f'"{n}"' for n in names)
        rows_body = ",\n               ".join(
            "[" + ", ".join(r) + "]" for r in fmt_rows)
        return (f'{{"method": "array", "params": [{params_body}],\n'
                f'    "values": [{rows_body}]}}')
