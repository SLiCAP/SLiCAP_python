"""Shared key-value parameter table for the instruction dialogs.

Two modes (see SLNG.md — "one shared widget, two modes"):

- **dict mode** (SLiCAP ``pardefs=``): row order irrelevant (substitution is
  recursive).  Optional "Load circuit definitions" button.  Emits a Python
  dict literal.  A pardefs dict *replaces* the circuit parameter definitions,
  so parameters not listed stay symbolic.
- **ordered mode** (NGspice ``params=``): row order is significant — SPICE
  evaluates ``.param`` lines non-recursively, so every parameter must be
  numerically evaluable when defined.  Up/Down reorder buttons.  Emits a
  list of ``(name, value)`` tuples.

Keys are editable dropdowns pre-filled with known parameter names (reduces
typing errors); values are free text in SLiCAP / SPICE expression syntax and
are emitted as quoted strings (``18p`` or ``1/(2*pi*R*C)`` are not valid
Python literals).
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QComboBox,
)


class ParamTable(QGroupBox):
    """Two-column (Parameter, Value) table; see the module docstring."""

    changed = Signal()

    def __init__(self, title: str, key_candidates=(), ordered: bool = False,
                 load_values: dict | None = None, hint: str = "",
                 checkable: bool = False, parent=None):
        super().__init__(title, parent)
        self._candidates = [str(k) for k in key_candidates]
        self._ordered = bool(ordered)
        self._load_values = dict(load_values) if load_values else None
        if checkable:
            self.setCheckable(True)
            self.setChecked(False)
            self.toggled.connect(lambda *_: self.changed.emit())

        outer = QVBoxLayout(self)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(110)
        self._table.itemChanged.connect(lambda *_: self.changed.emit())
        outer.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self.add_row())
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_selected_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        if self._ordered:
            up_btn = QPushButton("Up")
            up_btn.clicked.connect(lambda: self._move(-1))
            down_btn = QPushButton("Down")
            down_btn.clicked.connect(lambda: self._move(+1))
            btn_row.addWidget(up_btn)
            btn_row.addWidget(down_btn)
        if self._load_values is not None:
            load_btn = QPushButton("Load circuit definitions")
            load_btn.clicked.connect(self._load)
            btn_row.addWidget(load_btn)
        btn_row.addStretch(1)
        outer.addLayout(btn_row)

        if hint:
            lbl = QLabel(hint)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: grey; font-size: 9pt;")
            outer.addWidget(lbl)

    # ── rows ──────────────────────────────────────────────────────────────────

    def add_row(self, name: str = "", value: str = "") -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(self._candidates)
        combo.setCurrentText(str(name))
        combo.currentTextChanged.connect(lambda *_: self.changed.emit())
        self._table.setCellWidget(row, 0, combo)
        self._table.setItem(row, 1, QTableWidgetItem(str(value)))
        self.changed.emit()

    def set_entries(self, entries, active: bool = True) -> None:
        """Prefill from parsed (name, value) pairs (append-only editing).

        *entries* may be a dict or a list of pairs; empty/None unchecks a
        checkable table."""
        self._table.setRowCount(0)
        pairs = list(entries.items()) if isinstance(entries, dict) \
            else list(entries or [])
        for name, value in pairs:
            self.add_row(str(name), str(value))
        if self.isCheckable():
            self.setChecked(active and bool(pairs))
        self.changed.emit()

    def _remove_selected_row(self) -> None:
        rows = sorted({i.row() for i in self._table.selectedIndexes()},
                      reverse=True)
        if not rows and self._table.rowCount():
            rows = [self._table.rowCount() - 1]
        for r in rows:
            self._table.removeRow(r)
        self.changed.emit()

    def _row_name(self, row: int) -> str:
        w = self._table.cellWidget(row, 0)
        return w.currentText().strip() if w else ""

    def _row_value(self, row: int) -> str:
        it = self._table.item(row, 1)
        return it.text().strip() if it else ""

    def _set_row(self, row: int, name: str, value: str) -> None:
        w = self._table.cellWidget(row, 0)
        if w:
            w.setCurrentText(name)
        it = self._table.item(row, 1)
        if it is None:
            self._table.setItem(row, 1, QTableWidgetItem(value))
        else:
            it.setText(value)

    def _move(self, delta: int) -> None:
        r = self._table.currentRow()
        t = r + delta
        if r < 0 or t < 0 or t >= self._table.rowCount():
            return
        a = (self._row_name(r), self._row_value(r))
        b = (self._row_name(t), self._row_value(t))
        self._set_row(r, *b)
        self._set_row(t, *a)
        self._table.setCurrentCell(t, max(self._table.currentColumn(), 0))
        self.changed.emit()

    def _load(self) -> None:
        self._table.setRowCount(0)
        for name, value in (self._load_values or {}).items():
            self.add_row(name, value)
        self.changed.emit()

    # ── state & validation ────────────────────────────────────────────────────

    def active(self) -> bool:
        """False when the group box is checkable and unchecked."""
        return self.isChecked() if self.isCheckable() else True

    def entries(self) -> list[tuple[str, str]]:
        """(name, value) per row with a non-empty name, in table order."""
        out = []
        for r in range(self._table.rowCount()):
            name = self._row_name(r)
            if name:
                out.append((name, self._row_value(r)))
        return out

    def duplicate_names(self) -> set[str]:
        seen: set[str] = set()
        dups: set[str] = set()
        for name, _ in self.entries():
            (dups if name in seen else seen).add(name)
        return dups

    def is_valid(self) -> bool:
        """When active: at least one complete row, no duplicate names."""
        if not self.active():
            return True
        entries = self.entries()
        return (bool(entries) and not self.duplicate_names()
                and all(v for _, v in entries))

    # ── emission ──────────────────────────────────────────────────────────────

    @staticmethod
    def _q(text: str) -> str:
        return '"' + str(text).replace('"', "'") + '"'

    def dict_literal(self) -> str | None:
        """Python dict literal (dict mode); multi-line beyond 2 entries."""
        entries = self.entries()
        if not entries:
            return None
        items = [f"{self._q(n)}: {self._q(v)}" for n, v in entries]
        if len(items) <= 2:
            return "{" + ", ".join(items) + "}"
        return "{\n    " + ",\n    ".join(items) + "}"

    def list_literal(self) -> str | None:
        """(name, value) tuple-list literal (ordered mode)."""
        entries = self.entries()
        if not entries:
            return None
        items = [f"({self._q(n)}, {self._q(v)})" for n, v in entries]
        if len(items) <= 2:
            return "[" + ", ".join(items) + "]"
        return "[\n    " + ",\n    ".join(items) + "]"
