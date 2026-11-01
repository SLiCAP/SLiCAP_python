"""Parameter-source table of the SLiCAP instruction dialog (SLNG.md
"Instruction files, the main script and selectPars()", 2026-11-01).

One row per circuit parameter, defined and undefined, with four radio
positions that say where the analysis takes the value from:

- **undefined**: no definition is substituted, the element keeps its value
  attribute (``C_f`` stays ``C_f``).  Equals ``pardefs=None``.  "Defining a
  value zero does not make it symbolic" (Anton) - which is why the position
  is named after ``cir.params``, the undefined parameters.
- **circuit**: the definition of the circuit (``cir.parDefs``), read when
  the instruction RUNS.  Enabled only where the circuit defines the
  parameter.
- **specs**: the value of the specification item with the same symbol in the
  selected spec CSV, read when the instruction runs - so a value a design
  script writes to the CSV later is used.  Enabled only where the CSV holds
  the symbol with a non-empty value.
- **user**: a value typed here, emitted as a literal.  Always enabled.

"Set all to" applies one of three presets to every row at once (specs
first / circuit first / all undefined); single rows are then changed by
hand.  The dialog opens in the preset from Preferences.

Emission keeps the file readable: all undefined -> no ``pardefs``; every
defined parameter from the circuit and nothing else -> ``pardefs='circuit'``
(the same meaning); anything else -> ``pardefs=sl.selectPars(...)`` with
the names per source.

The NGspice instruction dialog uses the same table with ``positions``
circuit / specs / user: NGspice cannot run with an undefined parameter, so
that column is absent, and "circuit" means the ``.param`` definitions of
the ``.cir`` generated from the schematic.  The NGspice dialog writes
``params=sl.selectPars("<cir>", ...)`` for mode "select" and nothing for
mode "circuit" (the netlist definitions apply as they are) - the SAME
method as for SLiCAP (Anton, 2026-11-01).  The old table of VALUE literals ("Load circuit
definitions") was REPLACED: it copied values into the file at compose
time, so a value could not follow the CSV.
"""
from __future__ import annotations

import ast
import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QRadioButton,
    QButtonGroup, QLineEdit, QWidget, QSizePolicy,
)

from .value_fields import is_value
from .sizing import name_width
from .instr_file import spec_var_name

UNDEFINED, CIRCUIT, SPECS, USER = "undefined", "circuit", "specs", "user"
POSITIONS = (UNDEFINED, CIRCUIT, SPECS, USER)

# preference key -> label; the order in which a preset tries the sources
PRESETS = {"specs": "specs first", "circuit": "circuit first",
           "undefined": "all undefined"}
_PRESET_ORDER = {"specs": (SPECS, CIRCUIT, UNDEFINED),
                 "circuit": (CIRCUIT, UNDEFINED),
                 "undefined": (UNDEFINED,)}
NO_FILE = "(none)"


def read_spec_values(csv_dir: str, file_name: str) -> dict[str, str]:
    """``{symbol: value text}`` of the items WITH a value in a spec CSV, the
    text as written (SLiCAP notation).  Same field split as ``csv2specs``
    (descriptions escape their commas as ``&#44;``).  ``{}`` when the file
    cannot be read."""
    if not file_name or file_name == NO_FILE:
        return {}
    path = os.path.join(csv_dir, file_name) if csv_dir else file_name
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return {}
    out = {}
    for line in lines[1:]:
        fields = line.strip().split(",")
        if len(fields) >= 3 and fields[0].strip() and fields[2].strip():
            out[fields[0].strip()] = fields[2].strip()
    return out


def _q(text: str) -> str:
    return '"' + str(text).replace('"', "'") + '"'


def display_value(text: str) -> str:
    """A circuit definition or a spec value AS DISPLAYED in the table: SLiCAP
    notation read, rounded to the project's display digits with ``roundN``
    (the one SLiCAP display rule), so ``1/100000000000`` shows as
    ``1.000e-11`` and ``q`` as ``1.602e-19``.  Text SLiCAP cannot read (an
    NGspice ``agauss(...)``) is shown as written.  Display only: the emitted
    call names parameters, never these values (Anton, 2026-11-01)."""
    text = str(text).strip()
    if not text:
        return text
    try:
        import sympy as sp
        from SLiCAP.SLiCAPlex import _replaceScaleFactors
        from SLiCAP.SLiCAPmath import roundN
        return str(roundN(sp.sympify(_replaceScaleFactors(text)), numeric=True))
    except Exception:
        return text


class ParSourceTable(QGroupBox):
    """See the module docstring.  *par_defs*: ``{name: value text}`` of the
    circuit's defined parameters; *undefined*: names of its undefined ones;
    *spec_files*: the spec CSV names of the project; *preset*: the key the
    table opens in (``PRESETS``)."""

    changed = Signal()

    def __init__(self, par_defs: dict | None = None, undefined=(),
                 spec_files=(), csv_dir: str = "", preset: str = "specs",
                 positions=POSITIONS,
                 title: str = "Parameter substitution (pardefs)",
                 parent=None):
        super().__init__(title, parent)
        self._positions = tuple(positions)
        self._par_defs = {str(k): str(v) for k, v in (par_defs or {}).items()}
        self._names = list(self._par_defs) + [
            str(p) for p in undefined if str(p) not in self._par_defs]
        self._csv_dir = csv_dir
        self._spec_values: dict[str, str] = {}
        self._rows: dict[str, dict] = {}

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Spec file:"))
        self._file = QComboBox()
        self._file.addItem(NO_FILE)
        self._file.addItems([str(f) for f in spec_files])
        self._file.setToolTip(
            "Specification CSV of the project csv/ folder. Its values are "
            "read when the instruction runs.")
        top.addWidget(self._file)
        top.addSpacing(12)
        top.addWidget(QLabel("Set all to:"))
        self._preset = QComboBox()
        for key, label in PRESETS.items():
            if key == "undefined" and UNDEFINED not in self._positions:
                continue
            self._preset.addItem(label, key)
        self._preset.setToolTip(
            "Apply one choice to every parameter; single rows can then be "
            "changed.")
        top.addWidget(self._preset)
        top.addStretch(1)
        layout.addLayout(top)

        ncol = len(self._positions)
        self._table = QTableWidget(len(self._names), ncol + 1)
        self._table.setHorizontalHeaderLabels(["Parameter"] + list(self._positions))
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        for col in range(1, ncol):
            hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(ncol, QHeaderView.Stretch)
        self._table.setColumnWidth(0, name_width(self._table))
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)
        for row, name in enumerate(self._names):
            self._build_row(row, name)
        # Opens showing up to eight rows, scrolls beyond that, and grows with
        # the dialog: the group takes the stretch of the dialog's layout, so
        # a taller window shows more rows (Anton, 2026-11-01).
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        if self._names:
            self._table.resizeRowsToContents()
            row_h = self._table.rowHeight(0)
            shown = min(len(self._names), 8)
            self._table.setMinimumHeight(
                self._table.horizontalHeader().height() + shown * row_h
                + 2 * self._table.frameWidth())

        if not self._names:
            lbl = QLabel("This circuit has no parameters.")
            lbl.setStyleSheet("color: grey; font-size: 9pt;")
            layout.addWidget(lbl)
        self._reason = QLabel("")
        self._reason.setStyleSheet("color: #b00020; font-size: 9pt;")
        self._reason.setVisible(False)
        layout.addWidget(self._reason)

        self._file.currentTextChanged.connect(self._on_file_changed)
        self._preset.currentIndexChanged.connect(
            lambda *_: self.apply_preset(self._preset.currentData()))
        self._select_default_file()
        self._reload_specs()
        self.apply_preset(preset)

    def rows_beyond_minimum_height(self) -> int:
        """Pixels the table needs above its minimum to show EVERY row."""
        if len(self._names) <= 8:
            return 0
        return (len(self._names) - 8) * self._table.rowHeight(0)

    # ── rows ─────────────────────────────────────────────────────────────

    def _build_row(self, row: int, name: str) -> None:
        item = QTableWidgetItem(name)
        item.setFlags(Qt.ItemIsEnabled)
        self._table.setItem(row, 0, item)
        group = QButtonGroup(self)
        radios = {}
        for col, pos in enumerate(self._positions, start=1):
            cell = QWidget()
            lay = QHBoxLayout(cell)
            lay.setContentsMargins(4, 0, 4, 0)
            rb = QRadioButton()
            group.addButton(rb)
            radios[pos] = rb
            lay.addWidget(rb)
            if pos == USER:
                edit = QLineEdit()
                edit.setPlaceholderText("value")
                edit.setEnabled(False)
                edit.textChanged.connect(lambda *_: self.changed.emit())
                lay.addWidget(edit, 1)
                rb.toggled.connect(edit.setEnabled)
            rb.toggled.connect(self._on_toggled)
            self._table.setCellWidget(row, col, cell)
        radios[CIRCUIT].setText(display_value(self._par_defs.get(name, "")))
        radios[CIRCUIT].setEnabled(name in self._par_defs)
        # the resting position: undefined where it exists; otherwise user,
        # so that a parameter no preset can serve asks for a value
        radios[UNDEFINED if UNDEFINED in radios else USER].setChecked(True)
        self._rows[name] = {"group": group, "radios": radios,
                            "user": self._table.cellWidget(
                                row, len(self._positions)).findChild(QLineEdit)}

    def _on_toggled(self, checked: bool) -> None:
        if checked:
            self.changed.emit()

    def _select_default_file(self) -> None:
        """Preselect specs.csv, else the first spec file of the project."""
        if self._file.count() <= 1:
            return
        idx = self._file.findText("specs.csv")
        self._file.setCurrentIndex(idx if idx > 0 else 1)

    def _on_file_changed(self, *_) -> None:
        self._reload_specs()
        # a specs row whose value is gone falls back to the resting position
        rest = UNDEFINED if UNDEFINED in self._positions else USER
        for name, r in self._rows.items():
            if r["radios"][SPECS].isChecked() and not r["radios"][SPECS].isEnabled():
                r["radios"][rest].setChecked(True)
        self.changed.emit()

    def _reload_specs(self) -> None:
        self._spec_values = read_spec_values(self._csv_dir,
                                             self._file.currentText())
        for name, r in self._rows.items():
            rb = r["radios"][SPECS]
            rb.setText(display_value(self._spec_values.get(name, "")))
            rb.setEnabled(name in self._spec_values)

    # ── state ─────────────────────────────────────────────────────────────

    def apply_preset(self, key: str) -> None:
        """Set every row to the first position of the preset that has a
        value (``_PRESET_ORDER``); the user position is never preset."""
        order = [pos for pos in _PRESET_ORDER.get(key, _PRESET_ORDER["specs"])
                 if pos in self._positions]
        self.blockSignals(True)
        for r in self._rows.values():
            for pos in order:
                if r["radios"][pos].isEnabled():
                    r["radios"][pos].setChecked(True)
                    break
        idx = self._preset.findData(key)
        if idx >= 0:
            self._preset.blockSignals(True)
            self._preset.setCurrentIndex(idx)
            self._preset.blockSignals(False)
        self.blockSignals(False)
        self.changed.emit()

    def position(self, name: str) -> str:
        for pos, rb in self._rows[name]["radios"].items():
            if rb.isChecked():
                return pos
        return self._positions[0]

    def set_position(self, name: str, pos: str, user_value=None) -> bool:
        """False when *name* has no row or *pos* has no value there."""
        r = self._rows.get(name)
        if r is None or pos not in r["radios"] or not r["radios"][pos].isEnabled():
            return False
        r["radios"][pos].setChecked(True)
        if pos == USER and user_value is not None:
            r["user"].setText(str(user_value))
        return True

    def spec_file(self) -> str:
        text = self._file.currentText()
        return "" if text == NO_FILE else text

    def set_spec_file(self, file_name: str) -> bool:
        idx = self._file.findText(file_name)
        if idx < 0:
            return False
        self._file.setCurrentIndex(idx)
        return True

    def selection(self) -> dict:
        """``{"circuit": [names], "specs": [names], "user": {name: text},
        "undefined": [names]}`` in row order."""
        out = {CIRCUIT: [], SPECS: [], USER: {}, UNDEFINED: []}
        for name in self._names:
            pos = self.position(name)
            if pos == USER:
                out[USER][name] = self._rows[name]["user"].text().strip()
            else:
                out[pos].append(name)
        return out

    def is_valid(self) -> bool:
        return not self.reason()

    def reason(self) -> str:
        """Why the selection cannot be emitted, or ``""``."""
        for name, value in self.selection()[USER].items():
            if not value:
                return f"'{name}': give a user value, or choose another source."
            if not is_value(value):
                return f"'{name}': '{value}' is not a value or expression."
        return ""

    def show_reason(self) -> None:
        text = self.reason()
        self._reason.setText(text)
        self._reason.setVisible(bool(text))

    # ── emission ──────────────────────────────────────────────────────────

    def mode(self) -> str:
        """``"none"`` (all undefined), ``"circuit"`` (every defined parameter
        from the circuit, nothing else) or ``"select"``."""
        sel = self.selection()
        if not sel[CIRCUIT] and not sel[SPECS] and not sel[USER]:
            return "none"
        if (not sel[SPECS] and not sel[USER]
                and set(sel[CIRCUIT]) == set(self._par_defs)):
            return "circuit"
        return "select"

    def spec_var(self) -> str:
        """The variable the emitted call reads the specs from, or ``""``
        when no row takes its value from the specs."""
        return spec_var_name(self.spec_file()) if self.selection()[SPECS] else ""

    def emission(self, cir_var: str) -> str | None:
        """The ``pardefs`` value: ``None`` to omit it, ``"'circuit'"`` or the
        ``sl.selectPars(...)`` call."""
        mode = self.mode()
        if mode == "none":
            return None
        if mode == "circuit":
            return "'circuit'"
        sel = self.selection()
        parts = [cir_var]
        if sel[SPECS]:
            parts.append(self.spec_var())
        if sel[CIRCUIT]:
            parts.append("circuit=[" + ", ".join(_q(n) for n in sel[CIRCUIT]) + "]")
        if sel[SPECS]:
            parts.append("specs=[" + ", ".join(_q(n) for n in sel[SPECS]) + "]")
        if sel[USER]:
            parts.append("user={" + ", ".join(
                f"{_q(n)}: {_q(v)}" for n, v in sel[USER].items()) + "}")
        return "sl.selectPars(" + ", ".join(parts) + ")"

    # ── read-back (append-only editing) ──────────────────────────────────

    def load_from_source(self, src: str | None) -> None:
        """Set the rows from the source text of an existing ``pardefs=`` or
        ``params=`` argument: absent/None -> the resting preset (all
        undefined, or circuit first without that column); ``'circuit'`` ->
        circuit first; a dict or a list of pairs (the pre-6.4.4 tables) ->
        user rows; an ``sl.selectPars(...)`` call -> its lists.  Names
        without a row are skipped: the circuit no longer has them."""
        self.apply_preset("undefined" if UNDEFINED in self._positions else "circuit")
        if src is None:
            return
        try:
            node = ast.parse(src.strip(), mode="eval").body
        except SyntaxError:
            return
        try:
            value = ast.literal_eval(node)
        except (ValueError, SyntaxError):
            value = node
        if value == "circuit":
            self.apply_preset("circuit")
            return
        if isinstance(value, dict):
            for name, v in value.items():
                self.set_position(str(name), USER, v)
            return
        if isinstance(value, (list, tuple)):
            for pair in value:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    self.set_position(str(pair[0]), USER, pair[1])
            return
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "selectPars"):
            return

        def lit(n, default=None):
            try:
                return ast.literal_eval(n)
            except (ValueError, SyntaxError):
                return default

        if len(node.args) > 1 and isinstance(node.args[1], ast.Name):
            var = node.args[1].id
            for i in range(1, self._file.count()):
                if spec_var_name(self._file.itemText(i)) == var:
                    self._file.setCurrentIndex(i)
                    break
        for kw in node.keywords:
            v = lit(kw.value)
            if kw.arg == CIRCUIT:
                names = list(self._par_defs) if v == "all" else (v or [])
                for n in names:
                    self.set_position(str(n), CIRCUIT)
            elif kw.arg == SPECS:
                names = list(self._spec_values) if v == "all" else (v or [])
                for n in names:
                    self.set_position(str(n), SPECS)
            elif kw.arg == USER and isinstance(v, dict):
                for n, val in v.items():
                    self.set_position(str(n), USER, val)
        self.changed.emit()
