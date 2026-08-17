"""Create / Edit Traces dialog (TRACES.md phase 6).

First of the three post-processing dialogs; Axes and Figures follow in phase
7. Traces are the DATA layer of Figure -> Axes -> Traces: a named trace set
built from ONE simulation result, which appears in the variable explorer and
can be placed on any axis.

The dialog emits ONE statement per object (TRACES.md 7.3)::

    TR1 = sl.make_traces(TRAN1, [{"y": "RMS(I_V1**2*R_a)"},
                                 {"y": "V_out - V_outDC", "color": "r"}])

so append-only editing keeps working: no attribute-mutation lines that a
later definition could not undo.

A trace is ONE EXPRESSION (Anton, 2026-07-29). The goal function is part of
it - ``RMS(I_V1**2*R_a)`` - rather than a separate field, so the whole
mathematics of a trace is written and read in one place. The expression
editor therefore builds from three sources, each with its own insert button:

    Insert Signal             named output of the selected result
    Insert Circuit Parameter  parameter as SIMULATED (netlist + params=)
    Insert Goal Function      reduction of one run to one number

**Vocabulary** (Anton, 2026-07-29): a SIGNAL is named numeric data coming out
of a simulation - what NGspice calls a vector - and a TRACE is what this
dialog builds from it. The two words are never interchanged, even though
LTspice and SIMetrix call a raw vector a trace.

EVERY vector the run produced is offerable. One whose name is not a Python
identifier (``v(out)``, ``@q1[gm]``, ``x1.mid``) gets a Python name in the
assignment table when it is picked; the expressions use that name, and it is
emitted as ``variables={...}`` (TRACES.md phase 6d).

The names offered come from the CORE - the signal names from the design-data
manifest, the parameters from the NGspice netlist reader, the goal functions
from :func:`SLiCAP.SLiCAPtraces.goal_names` - so the dialog cannot disagree
with what ``make_traces`` accepts.
"""
from __future__ import annotations

import ast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDialogButtonBox, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMenu, QColorDialog, QWidget,
    QTabWidget,
)

from .instr_file import parse_calls
from .value_fields import watch, is_latex_safe, mark_item, LATEX_HINT
from .param_table import PARAM_NAME_WIDTH

from SLiCAP.SLiCAPtraces import (goal_names, function_names, reduces,
                                 units_of, automatic_color)

# {expression name: [(parameter label, default), …]}
_GOALS = goal_names()
# {name: what it does} - dB_20, phase, real, … (SLiCAPtraces._TRACE_FUNCTIONS)
_FUNCTIONS = function_names()

# Results that carry numeric arrays straight away.
_NG_FUNCS = {"op", "dc", "ac", "tran", "noise"}
# SLiCAP results are SYMBOLIC: they hold a formula, so they need a sweep
# before there are numbers (TRACES.md phase 6f). sl.sweepData() supplies it,
# which is why these results show a sweep row and the NGspice ones do not.
_SLICAP_FUNCS = {"doLaplace": "frequency", "doNumer": "frequency",
                 "doDenom": "frequency", "doNoise": "frequency",
                 "doTime": "t", "doImpulse": "t", "doStep": "t"}
# ... and what their signals are called: the result's own attributes, which
# are already Python identifiers, so no assignment table is needed.
_SLICAP_COMPLEX = {"doLaplace", "doNumer", "doDenom"}
# Complex-valued results: without a function in the expression these show
# their MAGNITUDE (Anton, 2026-07-31), and the hint says so.
_COMPLEX_KINDS = {"ac", "fft", "noise"}
# What an old trace_type= means as an expression. A trace set written before
# the types were dropped is MIGRATED on load - since 2026-08-03 make_traces
# no longer accepts the argument at all, so loading the statement here and
# re-adding it is ALSO how an old file becomes runnable again.
_TYPE_AS_FUNCTION = {"dBmag": "dB_20({0})", "phase": "phase({0})",
                     "mag": "abs({0})", "real": "real({0})",
                     "imag": "imag({0})", "delay": "delay({0})"}

# The result FOLLOWS the selected object instead of being overwritten by it
# (Anton, 2026-08-02).
_AUTOSELECT = "Autoselect from selected trace or measurement"

# Units sit next to the expression they belong to: units are a property
# of the trace VARIABLE (Anton, 2026-08-02), the scale factor is not.
_YEXPR, _YUNITS, _XEXPR, _XUNITS, _LABEL, _COLOR = 0, 1, 2, 3, 4, 5
_MNAME, _MEXPR, _MCOND, _MUNITS = 0, 1, 2, 3
_EXPRESSION_COLUMNS = (_YEXPR, _XEXPR)

# Abscissa of an analysis that does NOT reduce: what the simulator swept.
_SWEEP_NAME = {"ac": "frequency", "noise": "frequency", "tran": "time",
               "fft": "frequency"}

# matplotlib's one-letter colours as Qt knows them, for the swatch only: the
# emitted value stays whatever matplotlib understands ('#rrggbb' or 'r').
_COLOUR_NAMES = {"r": "red", "b": "blue", "g": "green", "c": "cyan",
                 "m": "magenta", "y": "yellow", "k": "black", "w": "white"}


def _next_meas_name(taken) -> str:
    """MEAS1, MEAS2, … - a measurement is a variable like any other."""
    return next_name("MEAS", taken)


def _python_name(vector: str) -> str:
    """A usable Python name for a simulator vector: ``v(out)`` -> ``V_out``,
    ``@r.x1.r1[i]`` -> ``I_r_x1_r1``. Only a starting point - the user edits
    it in the assignment table."""
    text = str(vector).strip()
    if not text:
        return ""
    kind = ""
    if text.lower().startswith("v(") or text.lower().startswith("i("):
        kind = text[0].upper() + "_"
        text = text[2:-1] if text.endswith(")") else text[2:]
    inner = "".join(c if (c.isalnum() or c == "_") else "_" for c in text)
    while "__" in inner:            # i(@q1[ic]) -> I_q1_ic, not I__q1_ic:
        inner = inner.replace("__", "_")     # the I_/V_ convention must
    name = (kind + inner.strip("_")).strip("_")   # survive the derivation
    if name and name[0].isdigit():
        name = "_" + name
    return name or "x"


def gain_type_of(entry) -> str:
    """The gain type a result statement asks for, '' for data that has none.

    A SLiCAP analysis carries one - ``transfer='asymptotic'``, defaulting to
    'gain' - and it decides the automatic COLOUR (ini.gaincolors). An NGspice
    run has none.
    """
    if not entry or not is_symbolic(entry):
        return ""
    transfer = _lit((entry.get("kwargs") or {}).get("transfer"))
    return str(transfer) if transfer else "gain"


def _lit(src):
    try:
        return ast.literal_eval(src) if src else None
    except (ValueError, SyntaxError):
        return None


def _q(text) -> str:
    return '"' + str(text).replace('"', "'") + '"'


def result_entries(calls: list[dict]) -> list[dict]:
    """The result variables a trace can be built from: NGspice runs and
    SLiCAP (symbolic) analyses."""
    return [c for c in calls
            if (c["func"] in _NG_FUNCS or c["func"] in _SLICAP_FUNCS)
            and c["assigned"]]


def is_symbolic(entry: dict) -> bool:
    """True for a SLiCAP result: a formula, so it needs a sweep."""
    return entry.get("func") in _SLICAP_FUNCS


def trace_entries(calls: list[dict]) -> list[dict]:
    """Existing named trace sets (``NAME = sl.make_traces(…)``)."""
    return [c for c in calls if c["func"] == "make_traces" and c["assigned"]]


def measurement_entries(calls: list[dict]) -> list[dict]:
    """Existing named measurements (``NAME = sl.measure(…)``)."""
    return [c for c in calls if c["func"] == "measure" and c["assigned"]]


def _result_kind(entry: dict) -> str:
    """Analysis kind, with 'fft' for a transient carrying fft=."""
    if entry["func"] == "tran" and entry.get("kwargs", {}).get("fft"):
        return "fft"
    return entry["func"]


def _abscissa(entry: dict) -> str:
    """The sweep variable this result provides."""
    if is_symbolic(entry):
        return _SLICAP_FUNCS[entry["func"]]
    return _SWEEP_NAME.get(_result_kind(entry), "")


def next_name(base: str, taken) -> str:
    i = 1
    while f"{base}{i}" in taken:
        i += 1
    return f"{base}{i}"


def signal_names(entry: dict, manifest: dict) -> list[str]:
    """Signals of a result: what the RUN recorded, and nothing else.

    The manifest holds the keys the result actually produced. Two other
    sources were tried and REVERTED (Anton, 2026-08-01): deriving them from
    the netlist, and falling back to the analysis's ``save=`` list. A signal
    "can only exist after a run" - before that the dialog offers nothing, and
    says so.
    """
    names = []
    for section in (manifest.get("sections") or {}).values():
        for variable in section.get("variables", []):
            if variable.get("name") == entry["name"]:
                names += [a.get("name", "") for a in
                          variable.get("attributes", [])]
    return [n for n in names if n]


def param_names(entry: dict) -> list[str]:
    """Circuit parameters an expression of this result may use.

    Read from the CORE netlist reader with the call's own ``params=``
    overrides applied, so the dialog offers exactly the names
    ``make_traces`` will resolve (they reach the factory through
    ``instr.circuit.parDefs``).
    """
    from SLiCAP.SLiCAPngspice import _netlist_par_defs
    args = entry.get("args") or []
    circuit = _lit(args[0]) if args else None
    if not isinstance(circuit, str):
        return []
    overrides = []
    for pair in _lit(entry["kwargs"].get("params")) or []:
        if isinstance(pair, (tuple, list)) and len(pair) == 2:
            overrides.append((str(pair[0]), str(pair[1])))
    try:
        par_defs = _netlist_par_defs(circuit, overrides)
    except Exception:
        return []
    return sorted(str(key) for key in par_defs)


def _is_stepped(entry: dict) -> bool:
    """True when the analysis steps, so its signals are 2-D and a goal
    function has more than one run to reduce."""
    return bool(entry.get("kwargs", {}).get("step"))


class TracesDialog(QDialog):
    """Create or edit ONE named trace set from ONE simulation result."""

    def __init__(self, existing_text: str = "", results_dir=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit Traces and Measurements")
        self.setMinimumWidth(720)

        calls = parse_calls(existing_text or "")
        self._results = result_entries(calls)
        self._existing = trace_entries(calls)
        self._measurements = measurement_entries(calls)
        self._taken = {c["name"] for c in calls}
        try:
            from .design_data import read_manifest
            self._manifest = read_manifest(results_dir)
        except Exception:
            self._manifest = {"sections": {}}

        outer = QVBoxLayout(self)
        head = QGridLayout()
        outer.addLayout(head)

        # The head holds what BOTH objects use (Anton, 2026-08-02): which
        # analysis, and what its signals are called. The identity of the
        # object being built - trace dictionary or measurement - lives on
        # its own tab.
        head.addWidget(QLabel("Analysis result:"), 0, 0)
        self._result = QComboBox()
        # Selecting an existing object USED to overwrite this field silently.
        # It is a mode now: on 'autoselect' the result FOLLOWS the selected
        # trace dictionary or measurement, and picking a result explicitly
        # re-targets those specifications at it - which is a legitimate
        # thing to want (the same traces on another run).
        self._result.addItem(_AUTOSELECT, None)
        for entry in self._results:
            self._result.addItem(f"{entry['name']}  (sl.{entry['func']})",
                                 entry["name"])
        self._result.currentIndexChanged.connect(self._on_result_selected)
        head.addWidget(self._result, 0, 1)

        # ── the sweep, for a SYMBOLIC result (TRACES.md phase 6f) ─────────
        #
        # A SLiCAP result is a formula and has no sweep of its own, so this
        # row supplies one; sl.sweepData() evaluates it. NGspice results
        # arrive as numbers and hide the row. Values are SLiCAP notation and
        # end up as plain numbers - scaling belongs to the axis, so there is
        # no counterpart of plotSweep's sweepScale (Anton, 2026-08-01).
        self._sweep_row = QWidget()
        sweep = QHBoxLayout(self._sweep_row)
        sweep.setContentsMargins(0, 0, 0, 0)
        self._sweep_lbl = QLabel("Sweep:")
        self._sweep_start = QLineEdit("1")
        self._sweep_stop = QLineEdit("1M")
        self._sweep_num = QLineEdit("200")
        for edit, width, tip in ((self._sweep_start, 90, "start"),
                                 (self._sweep_stop, 90, "stop"),
                                 (self._sweep_num, 70, "points")):
            edit.setMaximumWidth(width)
            edit.setPlaceholderText(tip)
            edit.textChanged.connect(self._update)
            watch(edit, "number")
        self._sweep_method = QComboBox()
        self._sweep_method.addItems(["log", "lin"])
        self._sweep_method.currentIndexChanged.connect(self._update)
        sweep.addWidget(self._sweep_lbl)
        sweep.addWidget(self._sweep_start)
        sweep.addWidget(QLabel("to"))
        sweep.addWidget(self._sweep_stop)
        sweep.addWidget(QLabel("in"))
        sweep.addWidget(self._sweep_num)
        sweep.addWidget(QLabel("points"))
        sweep.addWidget(self._sweep_method)
        sweep.addStretch(1)
        outer.addWidget(self._sweep_row)

        # ── simulation results -> Python variables (TRACES.md phase 6d) ───
        #
        # The simulator writes its own vector names; an expression needs
        # Python identifiers. The mapping is made HERE, after the run, when
        # the vectors are known - it used to sit in the analysis call, where
        # it could only guess (Anton, 2026-08-01). Empty by default: rows
        # appear when a signal is picked.
        # The direction of this sentence matters: each SIGNAL of the run gets
        # a Python name, not the other way round (Anton, 2026-08-02). And it
        # is a SIGNAL, the one word this GUI uses for named numeric data out
        # of a simulation - not vector, not variable (TRACES.md section 1).
        self._names_label = QLabel(
            "Assign Python variables to the simulated signals:")
        outer.addWidget(self._names_label)
        self._names_table = QTableWidget(0, 2)
        self._names_table.setHorizontalHeaderLabels(
            ["Python variable", "Simulated signal"])
        names_header = self._names_table.horizontalHeader()
        names_header.setSectionResizeMode(0, QHeaderView.Interactive)
        names_header.setSectionResizeMode(1, QHeaderView.Stretch)
        self._names_table.setColumnWidth(0, PARAM_NAME_WIDTH)
        self._names_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._names_table.setMaximumHeight(110)
        self._names_table.itemChanged.connect(lambda *_: self._update())
        outer.addWidget(self._names_table)

        self._names_buttons = QWidget()
        names_buttons = QHBoxLayout(self._names_buttons)
        names_buttons.setContentsMargins(0, 0, 0, 0)
        add_name = QPushButton("Add assignment")
        add_name.clicked.connect(lambda: self._add_name_row())
        drop_name = QPushButton("Remove assignment")
        drop_name.clicked.connect(self._remove_name_row)
        names_buttons.addWidget(add_name)
        names_buttons.addWidget(drop_name)
        names_buttons.addStretch(1)
        outer.addWidget(self._names_buttons)

        # ── one tab per object (Anton, 2026-08-02) ────────────────────────
        #
        # A trace dictionary and a series of measurements are two different
        # objects, so they get a tab each; that also keeps the dialog on a
        # normal screen. The assignment table stays ABOVE the tabs because
        # both objects use it: variables={...} is emitted on the make_traces
        # statement AND on every sl.measure statement.
        self._tabs = QTabWidget()
        outer.addWidget(self._tabs)

        traces_tab = QWidget()
        traces_lay = QVBoxLayout(traces_tab)
        trace_head = QGridLayout()
        traces_lay.addLayout(trace_head)
        trace_head.addWidget(QLabel("Select trace dictionary:"), 0, 0)
        self._edit = QComboBox()
        self._edit.addItem("New trace dictionary")
        self._edit.addItems([c["name"] for c in self._existing])
        self._edit.currentIndexChanged.connect(self._on_load_existing)
        trace_head.addWidget(self._edit, 0, 1)
        trace_head.addWidget(QLabel("Trace dictionary name:"), 1, 0)
        self._name = QLineEdit(next_name("TR", self._taken))
        self._name.setMaximumWidth(PARAM_NAME_WIDTH)
        self._name.textChanged.connect(self._update)
        trace_head.addWidget(self._name, 1, 1)
        traces_lay.addWidget(QLabel(
            "Create a trace from the assigned signals, the circuit "
            "parameters and the (goal) functions:"))
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Y expression", "Y units", "X expression", "X units", "Label",
             "Color"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(_YEXPR, QHeaderView.Stretch)
        header.setSectionResizeMode(_XEXPR, QHeaderView.Stretch)
        for column in (_YUNITS, _XUNITS, _LABEL, _COLOR):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
        self._table.setColumnWidth(_YUNITS, 70)
        self._table.setColumnWidth(_XUNITS, 70)
        self._table.setColumnWidth(_LABEL, 140)
        self._table.setColumnWidth(_COLOR, 60)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(140)
        self._table.itemChanged.connect(self._on_cell_changed)
        traces_lay.addWidget(self._table)

        row = QHBoxLayout()
        add = QPushButton("Add trace")
        add.clicked.connect(lambda: self._add_row())
        remove = QPushButton("Remove trace")
        remove.clicked.connect(self._remove_row)
        # The cell itself stays editable - a quick 'V_out' needs no window.
        # This button is for COMPOSING, and it is where the explanations are.
        self._trace_expr_btn = QPushButton("Create / Edit expression…")
        self._trace_expr_btn.clicked.connect(self._edit_trace_expression)
        # the expression comes FIRST: it is what a trace is (Anton,
        # 2026-08-03); adding and removing rows is the housekeeping around it
        row.addWidget(self._trace_expr_btn)
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch(1)
        traces_lay.addLayout(row)
        self._tabs.addTab(traces_tab, "Traces")

        # ── measurements: n x 1, one condition (TRACES.md phase 6e) ───────
        meas_tab = QWidget()
        meas_lay = QVBoxLayout(meas_tab)
        meas_head = QGridLayout()
        meas_lay.addLayout(meas_head)
        # No name field beside it: a measurement's name lives in the Name
        # column, because this tab holds n objects where the other holds one.
        meas_head.addWidget(QLabel("Select measurement:"), 0, 0)
        self._meas_edit = QComboBox()
        self._meas_edit.addItem("New measurement")
        self._meas_edit.addItems([c["name"] for c in self._measurements])
        self._meas_edit.currentIndexChanged.connect(self._on_load_measurement)
        meas_head.addWidget(self._meas_edit, 0, 1)
        meas_lay.addWidget(QLabel(
            "Create a measurement (one value each) from the assigned "
            "signals, the circuit parameters and the (goal) functions:"))
        self._meas = QTableWidget(0, 4)
        # NOT "Condition": Y_AT_X(y, 1e3) is a condition too, and this column
        # is only ever the run a measurement is taken from - "C_c=18p"
        # (a step value) or "2" (a run number). Anton, 2026-08-02.
        self._meas.setHorizontalHeaderLabels(
            ["Name", "Expression", "Step value / run number", "Units"])
        meas_header = self._meas.horizontalHeader()
        meas_header.setSectionResizeMode(_MNAME, QHeaderView.Interactive)
        meas_header.setSectionResizeMode(_MEXPR, QHeaderView.Stretch)
        meas_header.setSectionResizeMode(_MCOND, QHeaderView.Interactive)
        meas_header.setSectionResizeMode(_MUNITS, QHeaderView.Interactive)
        self._meas.setColumnWidth(_MNAME, PARAM_NAME_WIDTH)
        self._meas.setColumnWidth(_MCOND, 160)
        self._meas.setColumnWidth(_MUNITS, 70)
        self._meas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._meas.setMinimumHeight(140)
        self._meas.itemChanged.connect(self._on_meas_changed)
        meas_lay.addWidget(self._meas)

        meas_row = QHBoxLayout()
        add_meas = QPushButton("Add measurement")
        add_meas.clicked.connect(lambda: self._add_meas_row())
        drop_meas = QPushButton("Remove measurement")
        drop_meas.clicked.connect(self._remove_meas_row)
        self._meas_expr_btn = QPushButton("Create / Edit expression…")
        self._meas_expr_btn.clicked.connect(self._edit_meas_expression)
        meas_row.addWidget(self._meas_expr_btn)
        meas_row.addWidget(add_meas)
        meas_row.addWidget(drop_meas)
        meas_row.addStretch(1)
        meas_lay.addLayout(meas_row)
        self._tabs.addTab(meas_tab, "Measurements")

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(self._hint)

        self._preview = QLabel()
        self._preview.setWordWrap(True)
        self._preview.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._preview.setStyleSheet("font-family: monospace; font-size: 9pt;")
        outer.addWidget(self._preview)

        buttons = QDialogButtonBox()
        self._add_btn = buttons.addButton(
            "Add instruction", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._complex_result = False
        self._previous_result = self._result.currentIndex()
        self._loaded_trace = None
        self._loaded_measurement = None
        self._tabs.currentChanged.connect(self._on_result_changed)
        self._add_row()
        self._on_result_changed()

    # ── table plumbing ────────────────────────────────────────────────────

    def _selected_entry(self) -> dict | None:
        """The result the statements read from.

        On 'autoselect' it FOLLOWS the object selected on the active tab -
        a statement names its own result - and on an explicit choice it is
        that result, which re-targets the specifications at it.
        """
        name = self._result.currentData()
        if name is None:
            return self._autoselected()
        return next((e for e in self._results if e["name"] == name), None)

    def _result_of_data(self, text) -> dict | None:
        """The result a statement's data argument names - directly (``AC1``)
        or through ``sl.sweepData(LAPLACE1, …)``."""
        for entry in self._results:
            if entry["name"] in str(text or ""):
                return entry
        return None

    def _autoselected(self) -> dict | None:
        """The result of the selected object, or the first one when nothing
        is selected yet - a new trace dictionary must have somewhere to
        start."""
        loaded = (self._loaded_measurement if self._tabs.currentIndex() == 1
                  else self._loaded_trace)
        loaded = loaded or self._loaded_trace or self._loaded_measurement
        if loaded is not None:
            args = loaded.get("args") or []
            entry = self._result_of_data(args[0] if args else "")
            if entry is not None:
                return entry
        return self._results[0] if self._results else None

    def _refresh_autoselect(self):
        """Show WHICH result autoselect resolved to: the mode is only honest
        if the answer is visible."""
        entry = self._autoselected()
        self._result.setItemText(
            0, _AUTOSELECT + ("  ({0})".format(entry["name"]) if entry
                              else ""))

    def _candidates(self) -> list[str]:
        entry = self._selected_entry()
        return signal_names(entry, self._manifest) if entry else []

    def _add_row(self, expression="", x_expression="", label="", color="",
                 y_units="", x_units=""):
        r = self._table.rowCount()
        self._table.insertRow(r)
        for column, text in ((_YEXPR, expression), (_XEXPR, x_expression),
                             (_LABEL, label), (_YUNITS, y_units),
                             (_XUNITS, x_units)):
            self._table.setItem(r, column, QTableWidgetItem(str(text)))
        self._table.setCellWidget(r, _COLOR, self._colour_button(str(color)))
        self._table.setCurrentCell(r, _YEXPR)
        self._refresh_x(r)
        self._refresh_units(r)
        self._refresh_labels()
        self._refresh_colours()
        self._update()

    # ── colour ───────────────────────────────────────────────────────────
    #
    # A swatch, not a text box: a colour is picked, not spelled. EMPTY means
    # automatic - the axis then gives the trace the next colour of the
    # ini.default_colors cycle (red, blue, green, …), which is what makes the
    # runs of a stepped trace distinguishable - and the swatch shows which
    # colour that will be, so the default is visible without being pinned
    # (TRACES.md decision 4).

    def _colour_button(self, colour: str = ""):
        """The colour cell: **auto** until a colour is picked, the colour
        itself afterwards (Anton, 2026-08-01).

        A click opens the colour dialog straight away - no menu in between -
        and the right-click menu puts the trace back to automatic.
        """
        button = QPushButton()
        button.setFlat(True)
        button.setMaximumHeight(20)
        button._colour = colour.strip()
        button.clicked.connect(lambda *_a, b=button: self._pick_colour(b))
        button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        button.customContextMenuRequested.connect(
            lambda pos, b=button: self._colour_menu(b, pos))
        return button

    def _colour_menu(self, button, pos):
        """Right-click: back to automatic, or pick a colour."""
        menu = QMenu(button)
        menu.addAction("Automatic", lambda b=button: self._set_colour(b, ""))
        menu.addAction("Select colour…", lambda b=button: self._pick_colour(b))
        menu.exec(button.mapToGlobal(pos))

    def _set_colour(self, button, colour: str):
        button._colour = colour
        self._refresh_colours()
        self._update()

    def _pick_colour(self, button):
        from PySide6.QtGui import QColor
        current = QColor(_COLOUR_NAMES.get(button._colour, button._colour))
        chosen = QColorDialog.getColor(current if current.isValid() else
                                       QColor("red"), self, "Trace colour")
        if chosen.isValid():
            self._set_colour(button, chosen.name())

    def _automatic_colour(self, row: int) -> str:
        """The colour this trace will get when its spec names none.

        Asked of the CORE, so the swatch cannot disagree with the plot: a
        single trace of a named gain type gets the gain colour, everything
        else the ini.default_colors cycle (Anton, 2026-08-03).
        """
        entry = self._selected_entry()
        single = (len([r for r in self._rows()]) <= 1
                  and not (entry and _is_stepped(entry)))
        return automatic_color(row, gain_type_of(entry), single)

    def _refresh_colours(self):
        """Show each row's colour, and whether it was CHOSEN or is automatic.

        A full swatch for a chosen colour; a pale one labelled "auto" for the
        colour the axis would give. Filling the cell solidly in both cases
        reads as a choice that was never made (Anton, 2026-08-01) - and an
        automatic colour is not a property of the trace: it follows the row,
        and the axis assigns it when the trace is plotted.
        """
        from PySide6.QtGui import QColor
        for r in range(self._table.rowCount()):
            button = self._table.cellWidget(r, _COLOR)
            if button is None:
                continue
            chosen = getattr(button, "_colour", "")
            shown = chosen or self._automatic_colour(r)
            colour = QColor(_COLOUR_NAMES.get(shown, shown))
            if not colour.isValid():
                colour = QColor("white")
            if chosen:
                button.setText("")
                button.setStyleSheet(
                    "QPushButton {{ background-color: {0}; border: 1px solid "
                    "#888; }}".format(colour.name()))
                button.setToolTip("{0}  —  click to change, right-click for "
                                  "automatic".format(chosen))
            else:
                # no colour shown at all: a tinted cell reads as a choice that
                # was never made. The axis assigns one when the trace is
                # plotted, and the tooltip says which.
                button.setText("auto")
                button.setStyleSheet("QPushButton { color: #555; "
                                     "font-size: 9pt; }")
                button.setToolTip(
                    "automatic: the axis gives this trace {0}. Click to select "
                    "a colour.".format(_COLOUR_NAMES.get(shown, shown)))

    def _remove_row(self):
        rows = sorted({i.row() for i in self._table.selectedIndexes()},
                      reverse=True) or ([self._table.rowCount() - 1]
                                        if self._table.rowCount() else [])
        for r in rows:
            self._table.removeRow(r)
        self._refresh_colours()      # the automatic cycle follows the row
        self._refresh_labels()
        self._update()

    def _cell(self, r, c) -> str:
        item = self._table.item(r, c)
        return item.text().strip() if item else ""

    def _rows(self) -> list[dict]:
        out = []
        for r in range(self._table.rowCount()):
            expression = self._cell(r, _YEXPR)
            if not expression:
                continue
            button = self._table.cellWidget(r, _COLOR)
            out.append({"y": expression,
                        "x": self._cell(r, _XEXPR),
                        "label": self._cell(r, _LABEL),
                        "color": getattr(button, "_colour", ""),
                        "yUnits": self._cell(r, _YUNITS),
                        "xUnits": self._cell(r, _XUNITS)})
        return out

    # ── measurements ─────────────────────────────────────────────────────
    #
    # A measurement is n x 1: variables at ONE condition, where a trace is
    # 1 x m. The condition is data SELECTION, not mathematics, so it is a
    # column here and an argument of sl.measure() - not a function in the
    # expression (TRACES.md phase 6e).

    def _add_meas_row(self, name="", expression="", condition="", units=""):
        r = self._meas.rowCount()
        self._meas.insertRow(r)
        self._meas.blockSignals(True)
        for column, text in ((_MNAME, name or _next_meas_name(self._taken)),
                             (_MEXPR, expression), (_MCOND, condition),
                             (_MUNITS, units)):
            self._meas.setItem(r, column, QTableWidgetItem(str(text)))
        self._meas.blockSignals(False)
        self._meas.setCurrentCell(r, _MEXPR)
        self._update()

    def _remove_meas_row(self):
        rows = sorted({i.row() for i in self._meas.selectedIndexes()},
                      reverse=True) or ([self._meas.rowCount() - 1]
                                        if self._meas.rowCount() else [])
        for r in rows:
            self._meas.removeRow(r)
        self._update()

    def _on_meas_changed(self, _item):
        self._update()

    def _meas_rows(self) -> list:
        out = []
        for r in range(self._meas.rowCount()):
            def cell(c):
                it = self._meas.item(r, c)
                return it.text().strip() if it else ""
            if cell(_MNAME) and cell(_MEXPR):
                out.append({"name": cell(_MNAME), "y": cell(_MEXPR),
                            "condition": cell(_MCOND), "units": cell(_MUNITS)})
        return out

    def _measurement_statements(self, result_name: str) -> list:
        """One statement per measurement - one object, one line."""
        assignments = self._assignments()
        names = ""
        if assignments:
            names = ", variables={" + ", ".join(
                "{0}: {1}".format(_q(n), _q(v)) for n, v in assignments) + "}"
        out = []
        for row in self._meas_rows():
            condition = ""
            text = row["condition"]
            if text:
                # "C_c=18p" -> step={"C_c": "18p"}; "2" -> run=2
                if "=" in text:
                    key, _, value = text.partition("=")
                    condition = ", step={{{0}: {1}}}".format(
                        _q(key.strip()), _q(value.strip()))
                else:
                    condition = ", run={0}".format(text)
            units = ", units={0}".format(_q(row["units"])) if row["units"] else ""
            out.append("{0} = sl.measure({1}, {2}{3}{4}{5})".format(
                row["name"], result_name, _q(row["y"]), condition, names,
                units))
        return out

    # ── simulation result -> Python variable ─────────────────────────────

    def _add_name_row(self, python_name: str = "", vector: str = ""):
        """One assignment. The Python name is auto-derived from the signal
        (``v(out)`` -> ``V_out``) but stays editable - a name is the user's.

        The signal is PICKED from a drop-down of what the run produced
        (Anton, 2026-08-02); a row is a pair, so a widget per row is the
        right shape here.
        """
        r = self._names_table.rowCount()
        self._names_table.insertRow(r)
        self._names_table.blockSignals(True)
        self._names_table.setItem(r, 0, QTableWidgetItem(
            str(python_name or _python_name(vector))))
        self._names_table.blockSignals(False)
        self._names_table.setCellWidget(r, 1, self._signal_combo(str(vector)))
        self._names_table.setCurrentCell(r, 0)
        self._update()

    def _signal_combo(self, signal: str = ""):
        """Drop-down of the signals this run produced.

        A stored signal the run no longer has is kept as an item rather than
        dropped, so loading an old trace set cannot silently lose it; the
        core says so at run time if it is really gone.
        """
        combo = QComboBox()
        combo.addItem("")
        for name in self._candidates():
            combo.addItem(name)
        if signal and combo.findText(signal) < 0:
            combo.addItem(signal)
        combo.setCurrentText(signal)
        combo.currentTextChanged.connect(
            lambda text, c=combo: self._on_signal_picked(c, text))
        return combo

    def _on_signal_picked(self, combo, signal: str):
        """Fill an EMPTY Python name with the derived one; a name the user
        typed is never overwritten."""
        for r in range(self._names_table.rowCount()):
            if self._names_table.cellWidget(r, 1) is combo:
                item = self._names_table.item(r, 0)
                if item is None or not item.text().strip():
                    self._names_table.blockSignals(True)
                    self._names_table.setItem(
                        r, 0, QTableWidgetItem(_python_name(signal)))
                    self._names_table.blockSignals(False)
                break
        self._update()

    def _refresh_signal_menus(self):
        """Offer the signals of the SELECTED result in every row."""
        signals = self._candidates()
        for r in range(self._names_table.rowCount()):
            combo = self._names_table.cellWidget(r, 1)
            if combo is None:
                continue
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("")
            for name in signals:
                combo.addItem(name)
            if current and combo.findText(current) < 0:
                combo.addItem(current)
            combo.setCurrentText(current)
            combo.blockSignals(False)

    def _remove_name_row(self):
        rows = sorted({i.row() for i in self._names_table.selectedIndexes()},
                      reverse=True) or ([self._names_table.rowCount() - 1]
                                        if self._names_table.rowCount() else [])
        for r in rows:
            self._names_table.removeRow(r)
        self._update()

    def _assignments(self) -> list:
        """(python_name, vector) per complete row, in table order."""
        out = []
        for r in range(self._names_table.rowCount()):
            name = self._names_table.item(r, 0)
            combo = self._names_table.cellWidget(r, 1)
            name = name.text().strip() if name else ""
            signal = combo.currentText().strip() if combo else ""
            if name and signal:
                out.append((name, signal))
        return out

    # ── the abscissa the analysis gives by itself ────────────────────────

    def _default_x(self, y_expression: str) -> str:
        """The x the analysis provides for this y (Anton, 2026-07-30).

        The sweep variable for a swept analysis, the step parameter or the run
        number for a stepped OP - and the step parameter as soon as y REDUCES
        each run to one number, because then the runs are the abscissa.

        Whether y reduces is judged by the core from the expression's
        structure (``sl.reduces``), not by looking for the word RMS:
        ``V_out/MAX(V_out)`` mentions a goal but stays a curve against the
        sweep variable.
        """
        entry = self._selected_entry()
        if entry is None:
            return ""
        kind = _result_kind(entry)
        step = _lit(entry["kwargs"].get("step")) or {}
        step_name = step.get("param") or step.get("params")
        if isinstance(step_name, (list, tuple)):
            step_name = step_name[0] if len(step_name) == 1 else None
        # the expression speaks PYTHON names (the assignment table), not the
        # simulator's vectors; with none assigned yet, reduces() falls back to
        # its conservative reading
        assigned = [name for name, _vector in self._assignments()]
        reduced = reduces(y_expression, assigned or None)
        if kind == "op" or reduced:
            return str(step_name) if step_name else "run"
        if kind == "dc":
            # the swept source is the second argument of sl.dc(...)
            args = entry.get("args") or []
            source = _lit(args[1]) if len(args) > 1 else None
            return "v-sweep" if not isinstance(source, str) else source
        return _abscissa(entry)

    def _refresh_x(self, row: int):
        """Re-derive the X cell of *row* unless the user typed there.

        The derived text is remembered on the item (UserRole), so a cell the
        user has edited is left alone while an untouched one keeps following
        the result and the y expression.
        """
        item = self._table.item(row, _XEXPR)
        if item is None:
            return
        derived = self._default_x(self._cell(row, _YEXPR))
        previous = item.data(Qt.ItemDataRole.UserRole)
        if item.text().strip() and item.text().strip() != (previous or ""):
            return                                   # the user owns this cell
        self._table.blockSignals(True)
        item.setText(derived)
        item.setData(Qt.ItemDataRole.UserRole, derived)
        self._table.blockSignals(False)

    def _refresh_all_x(self):
        for row in range(self._table.rowCount()):
            self._refresh_x(row)
            self._refresh_units(row)
        self._refresh_labels()

    def _default_label(self) -> str:
        """The label ``plotSweep`` gives a trace of this result.

        Its rule (SLiCAPplots, _sweepAxis): the instruction's own label if it
        has one, the DETECTOR for a plain v/i transfer, and otherwise the
        GAIN TYPE - which is what makes a plot of the five transfers of the
        asymptotic-gain model readable ("gain", "asymptotic", "loopgain",
        "servo", "direct"). Anton, 2026-08-03: the new path left every trace
        with "dB_20(laplace) vs frequency" instead.

        Given to EVERY row: the magnitude and the phase of one transfer are
        the same thing seen twice and land on different axes, so both read
        "gain". Duplicate labels no longer cost a trace - make_traces keys
        them uniquely while keeping the label (Anton, 2026-08-03).
        """
        entry = self._selected_entry()
        gain = gain_type_of(entry)
        if not gain:
            return ""
        if gain == "vi":
            detector = _lit((entry.get("kwargs") or {}).get("detector"))
            return str(detector) if detector else ""
        return gain

    def _refresh_labels(self):
        """Fill the Label cells with the automatic label, leaving a label the
        user typed alone."""
        derived = self._default_label()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, _LABEL)
            if item is None:
                continue
            previous = item.data(Qt.ItemDataRole.UserRole)
            if item.text().strip() and item.text().strip() != (previous or ""):
                continue                             # the user owns this cell
            self._table.blockSignals(True)
            item.setText(derived)
            item.setData(Qt.ItemDataRole.UserRole, derived)
            self._table.blockSignals(False)

    def _refresh_units(self, row: int):
        """Suggest the units of what this trace plots, never overwriting a
        cell the user typed in.

        Only what a convention or a producer KNOWS is suggested - an
        expression like ``V_out*I_V1`` gets an empty field rather than a
        guess (Anton, 2026-08-02). What the dialog leaves empty is filled by
        ``make_traces`` at run time from the dataset, which knows more (a
        SLiCAP transfer is detector units over source units).
        """
        for column, source in ((_YUNITS, _YEXPR), (_XUNITS, _XEXPR)):
            item = self._table.item(row, column)
            if item is None:
                continue
            derived = units_of(self._cell(row, source))
            previous = item.data(Qt.ItemDataRole.UserRole)
            if item.text().strip() and item.text().strip() != (previous or ""):
                continue                             # the user owns this cell
            self._table.blockSignals(True)
            item.setText(derived)
            item.setData(Qt.ItemDataRole.UserRole, derived)
            self._table.blockSignals(False)

    # ── expression editor ─────────────────────────────────────────────────
    #
    # The table cell is the single source of truth; the editor is a view of
    # the selected row, so nothing can drift between the two.

    def _current_row(self) -> int:
        row = self._table.currentRow()
        if row < 0 and self._table.rowCount():
            row = 0
        return row

    def _current_column(self) -> int:
        """The expression column being edited: Y unless an X cell is
        selected, so the creator acts on what the user clicked (TRACES.md
        phase 6b)."""
        column = self._table.currentColumn()
        return column if column in _EXPRESSION_COLUMNS else _YEXPR

    def _on_cell_changed(self, item):
        if item.column() in (_YEXPR, _XEXPR):
            if item.column() == _YEXPR:
                self._refresh_x(item.row())
            self._refresh_units(item.row())
        if item.column() == _LABEL:
            # a label CLEARED comes back automatic, like a cleared X cell
            self._refresh_labels()
        self._update()

    # ── the expression creator ────────────────────────────────────────────
    #
    # ONE sub-dialog for both tabs (Anton, 2026-08-02): a trace expression
    # and a measurement expression are the same kind of expression over the
    # same sources, so there is one implementation of the four insert menus.
    # The caller passes what differs - the caption, the sources, and what a
    # goal function MEANS here.

    def _assign_signal(self, signal: str) -> str:
        """The Python name of a signal, assigning one when it has none.

        Called by the creator when a signal is picked: the assignment table
        lives HERE, so its rows are created here (TRACES.md phase 6d).
        """
        for name, assigned in self._assignments():
            if assigned == signal:
                return name
        name = signal if signal.isidentifier() else _python_name(signal)
        self._add_name_row(name, signal)
        return name

    def _expression_dialog(self, caption: str, text: str, hint: str):
        """The creator, filled from the SELECTED result. Built apart from
        running it, so what it is given can be checked without a modal
        window."""
        from .expression_dialog import ExpressionDialog
        entry = self._selected_entry()
        return ExpressionDialog(
            caption, text,
            signals=self._candidates(),
            assigned={vector: name for name, vector in self._assignments()},
            on_signal=self._assign_signal,
            params=param_names(entry) if entry else [],
            goal_enabled=bool(entry) and _is_stepped(entry),
            hint=hint, parent=self)

    def _open_expression(self, caption: str, text: str, hint: str):
        """Run the creator; the new expression, or None when cancelled."""
        dialog = self._expression_dialog(caption, text, hint)
        return dialog.expression() if dialog.exec() else None

    def _edit_trace_expression(self):
        row, column = self._current_row(), self._current_column()
        if row < 0:
            return
        axis = "Y" if column == _YEXPR else "X"
        text = self._open_expression(
            "{0} expression of trace {1}:".format(axis, row + 1),
            self._cell(row, column), self._expression_hint(False))
        if text is None:
            return
        self._table.blockSignals(True)
        self._table.setItem(row, column, QTableWidgetItem(text))
        self._table.blockSignals(False)
        if column == _YEXPR:
            # a reducing y moves the natural abscissa to the step parameter
            self._refresh_x(row)
        self._refresh_units(row)
        self._update()

    def _edit_meas_expression(self):
        row = self._meas.currentRow()
        if row < 0 and self._meas.rowCount():
            row = 0
        if row < 0:
            return
        item = self._meas.item(row, _MEXPR)
        text = self._open_expression(
            "Expression of measurement {0}:".format(row + 1),
            item.text() if item else "", self._expression_hint(True))
        if text is None:
            return
        self._meas.blockSignals(True)
        self._meas.setItem(row, _MEXPR, QTableWidgetItem(text))
        self._meas.blockSignals(False)
        self._update()

    def _expression_hint(self, for_measurement: bool) -> str:
        """What applies to the expression being written HERE.

        The same facts used to sit permanently under the dialog; they belong
        with the expression, which is where they are read (Anton,
        2026-08-02).
        """
        entry = self._selected_entry()
        if not self._candidates():
            return ("No signals known for this result yet: run the "
                    "instruction file once - the dialog then offers exactly "
                    "what the simulation produced.")
        named = [name for name, _v in self._assignments()]
        parameters = param_names(entry) if entry else []
        text = ("Numpy syntax over the Python variables assigned in the "
                "dialog"
                + (": " + ", ".join(named) if named else
                   " - pick a signal with Insert Signal to assign one")
                + (" | parameters: " + ", ".join(parameters)
                   if parameters else "") + ".")
        if self._complex_result:
            text += ("\nThis result is complex: without a function the "
                     "MAGNITUDE is used. Write dB_20(...), phase(...), "
                     "real(...), imag(...) or delay(...) for the rest.")
        if for_measurement:
            text += ("\nA measurement is ONE value: the goal function is "
                     "what reduces a run to it, e.g. RMS(I_V1**2*R_a).")
        elif entry is not None and not _is_stepped(entry):
            text += ("\nThis analysis is not stepped, so a goal function "
                     "would reduce it to a single number - a measurement, "
                     "not a trace.")
        return text

    # ── state ─────────────────────────────────────────────────────────────

    def _data_expression(self) -> str:
        """What the statements read from: the result itself, or the result
        wrapped in sl.sweepData() when it is a SYMBOLIC one."""
        entry = self._selected_entry()
        if entry is None:
            return ""
        if not is_symbolic(entry):
            return entry["name"]
        method = self._sweep_method.currentText()
        return 'sl.sweepData({0}, {1}, {2}, {3}{4})'.format(
            entry["name"], _q(self._sweep_start.text().strip()),
            _q(self._sweep_stop.text().strip()),
            self._sweep_num.text().strip() or "200",
            ', "{0}"'.format(method) if method != "log" else "")

    def _on_result_selected(self, *_args):
        """Changing the analysis result CLEARS what was built from the
        previous one.

        A trace dictionary is built from ONE result: the statement names it
        once, for every row. Rows made for another result would silently be
        re-targeted at signals this one may not have, which is what happened
        before (Anton, 2026-08-03: "changing the analysis result must clear
        the created traces"). Cleared without asking - the dialog emits
        nothing until Add instruction, so nothing in the file is lost.
        """
        if self._built_anything():
            self._clear_built()
        self._previous_result = self._result.currentIndex()
        self._on_result_changed()

    def _built_anything(self) -> bool:
        """True when this dialog holds work made for the current result."""
        return bool(self._rows() or self._meas_rows()
                    or self._assignments())

    def _clear_built(self):
        """Empty the tables: one blank trace row, no measurements, no
        assignments."""
        self._table.setRowCount(0)
        self._meas.setRowCount(0)
        self._names_table.setRowCount(0)
        self._loaded_trace = None
        self._loaded_measurement = None
        for combo in (self._edit, self._meas_edit):
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self._add_row()

    def _on_result_changed(self, *_args):
        """Refill the insert menus and the hint for the new result."""
        entry = self._selected_entry()
        symbolic = entry is not None and is_symbolic(entry)
        # a formula needs a sweep; numbers do not. And a symbolic result's
        # signals are its own attributes, already Python names, so the
        # assignment table has nothing to do (TRACES.md phase 6f)
        self._sweep_row.setVisible(symbolic)
        self._names_table.setVisible(not symbolic)
        self._names_buttons.setVisible(not symbolic)
        self._names_label.setVisible(not symbolic)
        self._complex_result = (entry is not None
                                and (_result_kind(entry) in _COMPLEX_KINDS
                                     or entry["func"] in _SLICAP_COMPLEX))
        self._refresh_autoselect()
        self._refresh_all_x()
        self._refresh_signal_menus()
        if not self._candidates():
            text = ("No signals known for this result yet: run the "
                    "instruction file once - the dialog then offers exactly "
                    "what the simulation produced.")
        else:
            text = ("Use Create / Edit expression… to compose from the "
                    "assigned signals, the circuit parameters and the "
                    "(goal) functions.")
        self._hint.setText(text)
        self._update()

    def _on_load_existing(self, index: int):
        if index <= 0:
            return
        entry = self._existing[index - 1]
        args = entry["args"]
        # NOT setCurrentIndex on the result: on autoselect it follows this
        # object, and an explicit choice is the user's (Anton, 2026-08-02).
        self._loaded_trace = entry
        self._on_result_changed()
        self._table.setRowCount(0)
        # A set written before the trace types were dropped carries
        # trace_type=; it becomes the equivalent FUNCTION in every expression,
        # so what is plotted is visible in the table instead of hiding in an
        # argument the dialog no longer offers (Anton, 2026-07-31).
        wrap = _TYPE_AS_FUNCTION.get(_lit(entry["kwargs"].get("trace_type")))
        self._names_table.setRowCount(0)
        for python_name, vector in (_lit(entry["kwargs"].get("variables")) or
                                    {}).items():
            self._add_name_row(str(python_name), str(vector))
        for spec in (_lit(args[1]) if len(args) > 1 else []) or []:
            if isinstance(spec, str):
                spec = {"y": spec}
            if not isinstance(spec, dict):
                continue
            expression = spec.get("y", "")
            if wrap and expression:
                expression = wrap.format(expression)
            self._add_row(expression=expression,
                          x_expression=spec.get("x") or "",
                          label=spec.get("label") or "",
                          color=spec.get("color") or "",
                          y_units=spec.get("yUnits") or "",
                          x_units=spec.get("xUnits") or "")
        if not self._table.rowCount():
            self._add_row()
        self._name.setText(entry["name"])
        self._update()

    def _on_load_measurement(self, index: int):
        """Read an existing ``NAME = sl.measure(…)`` back into a row.

        Until now a measurement could be created and never edited again: the
        dialog read make_traces statements back but not measure ones (Anton,
        2026-08-02).
        """
        if index <= 0:
            return
        entry = self._measurements[index - 1]
        args = entry.get("args") or []
        kwargs = entry.get("kwargs") or {}
        self._loaded_measurement = entry
        self._on_result_changed()
        self._names_table.setRowCount(0)
        for python_name, signal in (_lit(kwargs.get("variables")) or
                                    {}).items():
            self._add_name_row(str(python_name), str(signal))
        step = _lit(kwargs.get("step")) or {}
        run = _lit(kwargs.get("run"))
        if step:
            key, value = list(step.items())[0]
            condition = "{0}={1}".format(key, value)
        else:
            condition = "" if run is None else str(run)
        self._add_meas_row(entry["name"],
                           str(_lit(args[1]) or "") if len(args) > 1 else "",
                           condition, str(_lit(kwargs.get("units")) or ""))
        self._tabs.setCurrentIndex(1)
        self._update()

    def _flag_names(self):
        """Flag a Python name that LaTeX would misrepresent - it is still
        emitted (Anton, 2026-08-03: flag it, do not refuse)."""
        table = self._names_table
        table.blockSignals(True)          # marking a cell IS an item change
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if item is not None:
                mark_item(item, is_latex_safe(item.text()), LATEX_HINT)
        table.blockSignals(False)

    def _update(self, *_args):
        self._flag_names()
        snippet = self.generated_snippet()
        self._preview.setText(snippet or "")
        ok = (self._selected_entry() is not None
              and (bool(self._rows()) and bool(self._name.text().strip())
                   or bool(self._meas_rows())))
        self._add_btn.setEnabled(ok)

    # ── emission ──────────────────────────────────────────────────────────

    def _spec_literal(self, row: dict) -> str:
        parts = [f'"y": {_q(row["y"])}']
        if row["x"]:
            parts.append(f'"x": {_q(row["x"])}')
        if row["label"]:
            parts.append(f'"label": {_q(row["label"])}')
        if row["color"]:
            parts.append(f'"color": {_q(row["color"])}')
        # Empty units are NOT emitted: make_traces then fills what the
        # producer knows, which beats an empty string from the dialog.
        for key in ("yUnits", "xUnits"):
            if row[key]:
                parts.append('"{0}": {1}'.format(key, _q(row[key])))
        return "{" + ", ".join(parts) + "}"

    def generated_snippet(self) -> str:
        entry = self._selected_entry()
        rows = self._rows()
        if entry is None or (not rows and not self._meas_rows()):
            return ""
        name = self._name.text().strip() or "TR1"
        specs = [self._spec_literal(r) for r in rows]
        if len(specs) == 1:
            spec_text = "[" + specs[0] + "]"
        else:
            pad = " " * (len(name) + len(entry["name"]) + 21)
            spec_text = "[" + (",\n" + pad).join(specs) + "]"
        # No trace_type=: what a trace is, is written in its expression, and
        # complex data without a function shows its magnitude. names= carries
        # the Python variables assigned to this result's vectors.
        assignments = self._assignments()
        names = ""
        if assignments:
            names = ", variables={" + ", ".join(
                "{0}: {1}".format(_q(n), _q(v)) for n, v in assignments) + "}"
        data = self._data_expression()
        statements = []
        if rows:
            statements.append(f'{name} = sl.make_traces({data}, '
                              f'{spec_text}{names})')
        statements += self._measurement_statements(data)
        return "\n".join(statements)
