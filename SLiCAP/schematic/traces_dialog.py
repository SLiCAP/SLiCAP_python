"""Create / Edit Traces dialog (TRACES.md phases 6 and 9).

First of the three post-processing dialogs; Axes and Figures follow in phase
7. Traces are the DATA layer of Figure -> Axes -> Traces: a named trace set
that appears in the variable explorer and can be placed on any axis.

A trace set may use SEVERAL results of the file (phase 9, Anton,
2026-11-25). Its expressions name what they use with the dotted names of
the Design data - ``AC1.V_out``, ``FLT1.H_fs``, ``LAPLACE1.laplace``,
``R1.Ix``, ``HS`` - and the sources follow from those names; there is no
"Analysis result" choice any more. The dialog emits ONE statement per
object (TRACES.md 7.3), the sources combined by ``sl.makeDataset()``::

    TR1 = sl.make_traces(sl.makeDataset({"AC1": AC1, "LAPLACE1": LAPLACE1}),
                         [{"y": "dB(mag(AC1.V_out)) - dB(mag(LAPLACE1.laplace))"}],
                         variables={"AC1.V_out": "AC1.v(out)"})

so append-only editing keeps working: no attribute-mutation lines that a
later definition could not undo. A trace set written before phase 9, from
ONE result, is rewritten in this form when it is edited (Anton,
2026-11-25); unedited it keeps working.

A trace is ONE EXPRESSION (Anton, 2026-07-29). The goal function is part of
it - ``RMS(I_V1**2*R_a)`` - rather than a separate field, so the whole
mathematics of a trace is written and read in one place. The expression
editor builds from four sources, each with its own insert button:

    Insert Signal             a signal of any result, per result
    Insert Circuit Parameter  parameter as SIMULATED (netlist + params=)
    Insert Function           dB, mag, phase, ...
    Insert Goal Function      reduction of one run to one number

**Vocabulary** (Anton, 2026-07-29): a SIGNAL is named numeric data coming out
of a simulation - what NGspice calls a vector - and a TRACE is what this
dialog builds from it. The two words are never interchanged, even though
LTspice and SIMetrix call a raw vector a trace.

EVERY vector a run produced is offerable. One whose name is not a Python
identifier (``v(out)``, ``@q1[gm]``, ``x1.mid``) gets a Python name in the
assignment table when it is picked; the expressions use that name, and it is
emitted as ``variables={...}`` (TRACES.md phase 6d).

The names offered come from the CORE - the signal names from the design-data
manifest, the parameters from the NGspice netlist reader, the goal functions
from :func:`SLiCAP.SLiCAPtraces.goal_names` - so the dialog cannot disagree
with what ``make_traces`` accepts. Which sources combine is the core's rule
too (``makeDataset``); :mod:`.trace_sources` says it beforehand.
"""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDialogButtonBox, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMenu, QColorDialog, QWidget,
    QTabWidget,
)

from .instr_file import (parse_calls, pardef_sources, spec_var_name, quoted,
                         bound_names, literal as _lit)
from .cell_button import CellButtonDelegate
from .edit_note import EditNote
from .par_source_table import display_value
from .param_field import ParamField
from .value_fields import watch, all_valid, is_number, is_latex_safe, mark_item, LATEX_HINT
from .sizing import name_width, cap_chars, chars, scroll_body, fit_to_screen
# The results of a file and how they combine live in trace_sources.
from .trace_sources import (file_sources, statement, dataset_call, read_data,
                            names_in, SYSTEM_X, NGSPICE, SYSTEM, SLICAP,
                            FILTER, DATA_KINDS)

from SLiCAP.SLiCAPtraces import (goal_names, function_names, reduces,
                                 units_of, automatic_color)

# {expression name: [(parameter label, default), …]}
_GOALS = goal_names()
# {name: what it does} - dB_20, phase, real, … (SLiCAPtraces._TRACE_FUNCTIONS)
_FUNCTIONS = function_names()

# What an old trace_type= means as an expression. A trace set written before
# the types were dropped is MIGRATED on load - since 2026-08-03 make_traces
# no longer accepts the argument at all, so loading the statement here and
# re-adding it is ALSO how an old file becomes runnable again.
_TYPE_AS_FUNCTION = {"dBmag": "dB_20({0})", "phase": "phase({0})",
                     "mag": "abs({0})", "real": "real({0})",
                     "imag": "imag({0})", "delay": "delay({0})"}

# Units sit next to the expression they belong to: units are a property
# of the trace VARIABLE (Anton, 2026-08-02), the scale factor is not.
_YEXPR, _YUNITS, _XEXPR, _XUNITS, _LABEL, _COLOR = 0, 1, 2, 3, 4, 5
# a cell of a loaded trace holds what the statement says, an empty one too:
# the suggestions (x, units, label) do not fill it. They did, so OK without
# a change rewrote every loaded trace set that left them to make_traces()
# (Anton, 2026-11-25: editing in place; OK without a change leaves the
# statement as written)
_AS_WRITTEN = Qt.ItemDataRole.UserRole + 1
_MNAME, _MEXPR, _MCOND, _MUNITS = 0, 1, 2, 3
_EXPRESSION_COLUMNS = (_YEXPR, _XEXPR)
# the assignment table: the result, the Python name within it, its signal
_NRESULT, _NNAME, _NSIGNAL = 0, 1, 2

# matplotlib's one-letter colours as Qt knows them, for the swatch only: the
# emitted value stays whatever matplotlib understands ('#rrggbb' or 'r').
_COLOUR_NAMES = {"r": "red", "b": "blue", "g": "green", "c": "cyan",
                 "m": "magenta", "y": "yellow", "k": "black", "w": "white"}

_NO_RESULTS = ("No results known yet: run the instruction file once - the "
               "dialog then offers exactly what the simulations produced.")


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


def trace_entries(calls: list[dict]) -> list[dict]:
    """Existing named trace sets (``NAME = sl.make_traces(…)``)."""
    return [c for c in calls if c["func"] == "make_traces" and c["assigned"]]


def recorded_trace_sets(section: dict, known=()) -> list[dict]:
    """The trace sets a RUN recorded that no ``sl.*`` call names: variables
    of kind "traces" in the file's manifest *section*
    (``design_data.manifest_section``), such as ``TR1 = R1.traces`` of a
    system run (SystemExtensionSpecs.md 6.9.4). Entries are shaped like
    those of :func:`trace_entries`, with an empty ``func``. A trace set is
    a top-level variable, however it was made: offering a result's
    ``traces`` attribute as an item of its own was tried and REVERTED
    (Anton, 2026-11-17), a patch per holder of traces."""
    out = []
    for variable in section.get("variables", []):
        name = variable.get("name", "")
        if (variable.get("kind") == "traces" and name
                and name not in known
                and name not in {e["name"] for e in out}):
            out.append({"name": name, "func": "", "args": [],
                        "kwargs": {}, "assigned": True})
    return out


def measurement_entries(calls: list[dict]) -> list[dict]:
    """Existing named measurements (``NAME = sl.measure(…)``)."""
    return [c for c in calls if c["func"] == "measure" and c["assigned"]]


def next_name(base: str, taken) -> str:
    i = 1
    while f"{base}{i}" in taken:
        i += 1
    return f"{base}{i}"


class TracesDialog(QDialog):
    """Create or edit ONE named trace set, and measurements, from the
    results of the file."""

    def __init__(self, existing_text: str = "", results_dir=None, parent=None,
                 csv_dir: str = "", source_name: str = ""):
        """*csv_dir*: the project csv/ folder; its spec files feed the
        *specs* source of the sweep limits (Anton, 2026-11-09: a spec the
        instruction did not select must be selectable for the sweep).
        *source_name*: the instruction file being edited, whose manifest
        section is the only one the dialog reads."""
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit Traces and Measurements")
        self.setMinimumWidth(chars(self, 103))
        self._existing_text = existing_text or ""
        self._csv_dir = csv_dir
        self._spec_file = ""              # the spec file of the sweep limits
        calls = parse_calls(existing_text or "")
        self._existing = trace_entries(calls)
        self._measurements = measurement_entries(calls)
        # every name the file binds, not only the sl.* calls: a hand-merged
        # TR3 = {**TR1, **TR2} is taken too (instr_file.bound_names). The
        # names of the sl.* calls were the taken set until 2026-11-22.
        # REPLACED 2026-11-22: they missed every other binding.
        self._taken = bound_names(self._existing_text)
        try:
            from .design_data import read_manifest, manifest_section
            self._section = manifest_section(read_manifest(results_dir), source_name)
        except Exception:
            self._section = {}
        # every result of the file a trace may use (phase 9): the "Analysis
        # result" choice of ONE result was REPLACED (Anton, 2026-11-25)
        self._sources = file_sources(calls, self._section)

        frame, outer, self._scroll = scroll_body(self)
        from .doc_link import help_label
        outer.addWidget(help_label(
            "Composes <code>sl.make_traces()</code> and "
            "<code>sl.measure()</code> calls", "GUI/plots/plots.html",
            "traces-and-measurements", "help: traces and measurements"))

        # ── the range, when no data fixes the points (TRACES.md phase 9) ──
        #
        # A function - a SLiCAP result, a filter, an expression - has no
        # points of its own, so this row supplies them when no data source
        # (an NGspice or system run) does; sl.makeDataset() evaluates them.
        # Values are SLiCAP notation and end up as plain numbers - scaling
        # belongs to the axis, so there is no counterpart of plotSweep's
        # sweepScale (Anton, 2026-08-01).
        self._sweep_row = QWidget()
        sweep = QHBoxLayout(self._sweep_row)
        sweep.setContentsMargins(0, 0, 0, 0)
        self._sweep_lbl = QLabel("Sweep:")
        # start and stop take a number or a parameter (param_field):
        # sl.makeDataset() resolves the name from params= (Anton, 2026-11-09)
        # no preset numbers: the limits are the user's (Anton, 2026-11-09)
        self._sweep_start = ParamField("e.g. 1", 12)
        self._sweep_stop = ParamField("e.g. 1M", 12)
        self._sweep_start.textChanged.connect(self._update)
        self._sweep_stop.textChanged.connect(self._update)
        # the number of points, 500 by default; "in ... points" read as
        # ticks of the axis and was REPLACED by "no. pts:" (Anton,
        # 2026-11-25)
        self._sweep_num = QLineEdit("500")
        cap_chars(self._sweep_num, 9)
        self._sweep_num.setToolTip("The number of points of the sweep")
        self._sweep_num.textChanged.connect(self._update)
        watch(self._sweep_num, "number")
        self._sweep_method = QComboBox()
        self._sweep_method.addItems(["log", "lin"])
        self._sweep_method.currentIndexChanged.connect(self._update)
        # lin/log follows the axis (log in frequency, lin in time) until
        # the user chooses, or a loaded statement gives it
        self._method_chosen = False
        self._sweep_method.activated.connect(self._on_method_chosen)
        self._sweep_points = QLabel("no. pts:")
        sweep.addWidget(self._sweep_lbl)
        sweep.addWidget(self._sweep_start)
        sweep.addWidget(QLabel("to"))
        sweep.addWidget(self._sweep_stop)
        sweep.addWidget(self._sweep_points)
        sweep.addWidget(self._sweep_num)
        sweep.addWidget(self._sweep_method)
        sweep.addStretch(1)
        self._sweep_row.setVisible(False)
        outer.addWidget(self._sweep_row)

        # ── the x axis of a SYSTEM run ────────────────────────────────────
        #
        # The signals of a system run lie in clock domains, each with its
        # own sample instants. The domain follows from the signals an
        # expression uses (R1.Ix lies in one domain); the x axis is a choice
        # at plotting time: time, the integer master tick, or the sample
        # index of the domain (SystemExtensionSpecs.md 6.9.4, 6.9.5).
        self._system_row = QWidget()
        system_row = QHBoxLayout(self._system_row)
        system_row.setContentsMargins(0, 0, 0, 0)
        self._x_axis = QComboBox()
        self._x_axis.addItems(list(SYSTEM_X))
        self._x_axis.currentIndexChanged.connect(self._on_x_axis_changed)
        system_row.addWidget(QLabel("X axis of the system run:"))
        system_row.addWidget(self._x_axis)
        system_row.addStretch(1)
        self._system_row.setVisible(False)
        outer.addWidget(self._system_row)

        # ── simulation results -> Python variables (TRACES.md phase 6d) ───
        #
        # The simulator writes its own vector names; an expression needs
        # Python identifiers. The mapping is made HERE, after the run, when
        # the vectors are known (Anton, 2026-08-01). Empty by default: rows
        # appear when a signal is picked. Each SIGNAL of a run gets a Python
        # name, not the other way round (Anton, 2026-08-02); the name lies
        # in its result, AC1.V_out (phase 9).
        self._names_label = QLabel(
            "Assign Python variables to the simulated signals:")
        outer.addWidget(self._names_label)
        self._names_table = QTableWidget(0, 3)
        self._names_table.setHorizontalHeaderLabels(
            ["Result", "Python variable", "Simulated signal"])
        names_header = self._names_table.horizontalHeader()
        names_header.setSectionResizeMode(_NRESULT, QHeaderView.Interactive)
        names_header.setSectionResizeMode(_NNAME, QHeaderView.Interactive)
        names_header.setSectionResizeMode(_NSIGNAL, QHeaderView.Stretch)
        self._names_table.setColumnWidth(_NRESULT, name_width(self._names_table))
        self._names_table.setColumnWidth(_NNAME, name_width(self._names_table))
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
        # the table is for simulator vectors: shown when a run has them
        has_runs = any(s.kind in DATA_KINDS for s in self._sources.values())
        for widget in (self._names_label, self._names_table, self._names_buttons):
            widget.setVisible(has_runs)

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
        self._name.setMaximumWidth(name_width(self._name))
        # what "Select trace dictionary" and "Select measurement" edit, in
        # place (instr_file.place, Anton 2026-11-25)
        self._note = EditNote(self._existing_text)
        self._note.follow(self._name, lambda: next_name("TR", self._taken))
        self._name.textChanged.connect(self._update)
        trace_head.addWidget(self._name, 1, 1)
        traces_lay.addWidget(QLabel(
            "Create a trace from the signals of the results, the circuit "
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
        # The cell itself stays editable - a quick 'AC1.V_out' needs no
        # window. The button IN the cell is for COMPOSING, and it is where
        # the explanations are. It sits in the cell it writes, so there is no
        # doubt which expression it edits (Anton, 2026-11-25). The button
        # below the table did that from the current cell and was REMOVED
        # the same day.
        self._trace_cells = CellButtonDelegate(
            tooltip="Create / Edit expression…", parent=self)
        self._trace_cells.clicked.connect(self._edit_trace_expression)
        for column in _EXPRESSION_COLUMNS:
            self._table.setItemDelegateForColumn(column, self._trace_cells)
        traces_lay.addWidget(self._table)

        row = QHBoxLayout()
        add = QPushButton("Add trace")
        add.clicked.connect(lambda: self._add_row())
        remove = QPushButton("Remove trace")
        remove.clicked.connect(self._remove_row)
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
            "Create a measurement (one value each) from the signals of the "
            "results, the circuit parameters and the (goal) functions:"))
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
        self._meas.setColumnWidth(_MNAME, name_width(self._meas))
        self._meas.setColumnWidth(_MCOND, 160)
        self._meas.setColumnWidth(_MUNITS, 70)
        self._meas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._meas.setMinimumHeight(140)
        self._meas.itemChanged.connect(self._on_meas_changed)
        self._meas_cells = CellButtonDelegate(
            tooltip="Create / Edit expression…", parent=self)
        self._meas_cells.clicked.connect(
            lambda row, _column: self._edit_meas_expression(row))
        self._meas.setItemDelegateForColumn(_MEXPR, self._meas_cells)
        meas_lay.addWidget(self._meas)

        meas_row = QHBoxLayout()
        add_meas = QPushButton("Add measurement")
        add_meas.clicked.connect(lambda: self._add_meas_row())
        drop_meas = QPushButton("Remove measurement")
        drop_meas.clicked.connect(self._remove_meas_row)
        meas_row.addWidget(add_meas)
        meas_row.addWidget(drop_meas)
        meas_row.addStretch(1)
        meas_lay.addLayout(meas_row)
        self._tabs.addTab(meas_tab, "Measurements")

        # why the statement cannot be built: shown, never hidden behind a
        # disabled button (TRACES.md phase 9, 9.4 item 4)
        self._reason = QLabel()
        self._reason.setWordWrap(True)
        self._reason.setStyleSheet("color: #b34700; font-size: 9pt;")
        self._reason.setVisible(False)
        outer.addWidget(self._reason)
        outer.addWidget(self._note)

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
        frame.addWidget(buttons)

        self._range_axis = ""            # the axis the range row was offered for
        self._add_row()
        self._hint.setText(
            "Click … in an expression cell to compose from the signals of the "
            "results, the circuit parameters and the (goal) functions. A name "
            "is result.signal, as in the Design data; one trace may combine "
            "several results." if self._offers_anything() else _NO_RESULTS)
        self._update()
        fit_to_screen(self, self._scroll)

    # ── the sources a statement reads ─────────────────────────────────────

    def _trace_texts(self) -> list:
        """The y and x expressions of the trace rows."""
        return [t for r in self._rows() for t in (r["y"], r["x"]) if t]

    def _trace_statement(self):
        return statement(self._trace_texts(), self._sources,
                         x_axis=self._x_axis.currentText())

    def _meas_statement(self, row: dict):
        return statement([row["y"]], self._sources,
                         x_axis=self._x_axis.currentText())

    def _statements(self) -> list:
        """Every statement the dialog would write: the trace set, then each
        measurement."""
        out = [self._trace_statement()] if self._rows() else []
        return out + [self._meas_statement(r) for r in self._meas_rows()]

    def _on_x_axis_changed(self, *_args):
        self._refresh_all_x()
        self._update()

    def _on_method_chosen(self, *_args):
        self._method_chosen = True

    def _range_statement(self):
        """The first statement that needs the range row, or None."""
        return next((st for st in self._statements() if st.range), None)

    def _show_rows(self):
        """The range row when a statement has no data to fix its points, the
        x axis of a system run when one is used."""
        st = self._range_statement()
        self._sweep_row.setVisible(st is not None)
        if st is not None:
            self._sweep_lbl.setText("Frequency:" if st.axis == "frequency"
                                    else "Time:")
            full = st.range == "full"
            for widget in (self._sweep_points, self._sweep_num, self._sweep_method):
                widget.setVisible(full)
            if st.axis != self._range_axis and not self._method_chosen:
                # lin for a time axis, log for a frequency axis, until chosen
                self._sweep_method.blockSignals(True)
                self._sweep_method.setCurrentText(
                    "log" if st.axis == "frequency" else "lin")
                self._sweep_method.blockSignals(False)
                self._range_axis = st.axis
            self._offer_sweep_parameters(st)
        uses_system = any(self._sources[n].kind == SYSTEM
                          for s in self._statements() for n in s.used)
        self._system_row.setVisible(uses_system)

    # ── table plumbing ────────────────────────────────────────────────────

    def _add_row(self, expression="", x_expression="", label="", color="",
                 y_units="", x_units="", as_written=False):
        """A trace row. *as_written*: a row loaded from a statement, whose
        x, label and units cells keep what the statement says (_AS_WRITTEN)."""
        r = self._table.rowCount()
        self._table.insertRow(r)
        # setItem() emits itemChanged, which would take the cell as typed;
        # the refreshes below do what _on_cell_changed does
        self._table.blockSignals(True)
        for column, text in ((_YEXPR, expression), (_XEXPR, x_expression),
                             (_LABEL, label), (_YUNITS, y_units),
                             (_XUNITS, x_units)):
            item = QTableWidgetItem(str(text))
            if as_written and column != _YEXPR:
                item.setData(_AS_WRITTEN, True)
            self._table.setItem(r, column, item)
        self._table.blockSignals(False)
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
        else the ini.default_colors cycle (Anton, 2026-08-03). The gain type
        is that of a SLiCAP result that is the ONLY source of the set, as
        makeDataset() gives it.
        """
        used = self._trace_statement().used if self._rows() else []
        only = self._sources[used[0]] if len(used) == 1 else None
        gain = only.gain if only is not None and only.kind == SLICAP else ""
        stepped = any(self._sources[n].stepped for n in used)
        single = len(self._rows()) <= 1 and not stepped
        return automatic_color(row, gain, single)

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
        if not name:
            # free in the file AND in this table, so two new rows are MEAS1
            # and MEAS2 (2026-11-22). The name column is read directly:
            # _meas_rows() skips a row without an expression.
            listed = {self._meas.item(r, _MNAME).text().strip()
                      for r in range(self._meas.rowCount())
                      if self._meas.item(r, _MNAME)}
            name = _next_meas_name(self._taken | listed)
        r = self._meas.rowCount()
        self._meas.insertRow(r)
        self._meas.blockSignals(True)
        for column, text in ((_MNAME, name),
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
            item = self._meas.item(r, _MNAME)
            if item is not None and item.text().strip() in self._note.names():
                self._note.drop(item.text().strip())    # no longer edited
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

    def _measurement_statements(self) -> list:
        """One statement per measurement - one object, one line - each on
        the dataset of the sources IT uses."""
        out = []
        for row in self._meas_rows():
            st = self._meas_statement(row)
            condition = ""
            text = row["condition"]
            if text:
                # "C_c=18p" -> step={"C_c": "18p"}; "2" -> run=2
                if "=" in text:
                    key, _, value = text.partition("=")
                    condition = ", step={{{0}: {1}}}".format(
                        quoted(key.strip()), quoted(value.strip()))
                else:
                    condition = ", run={0}".format(text)
            units = ", units={0}".format(quoted(row["units"])) if row["units"] else ""
            out.append("{0} = sl.measure({1}, {2}{3}{4}{5})".format(
                row["name"], self._data_expression(st), quoted(row["y"]),
                condition, self._variables_kwarg(st.used), units))
        return out

    # ── simulation result -> Python variable ─────────────────────────────

    def _runs(self) -> list:
        """The results whose signals may need a Python name: the runs."""
        return [n for n, s in self._sources.items() if s.kind in DATA_KINDS]

    def _add_name_row(self, result: str = "", python_name: str = "",
                      vector: str = ""):
        """One assignment: a signal of *result* gets a Python name, auto-
        derived from the signal (``v(out)`` -> ``V_out``) but editable - a
        name is the user's. The result and the signal are PICKED from
        drop-downs of what the runs produced (Anton, 2026-08-02)."""
        r = self._names_table.rowCount()
        self._names_table.insertRow(r)
        self._names_table.blockSignals(True)
        self._names_table.setItem(r, _NNAME, QTableWidgetItem(
            str(python_name or _python_name(vector))))
        self._names_table.blockSignals(False)
        result = result or (self._runs()[0] if self._runs() else "")
        combo = QComboBox()
        combo.addItems(self._runs())
        if result and combo.findText(result) < 0:
            combo.addItem(result)
        combo.setCurrentText(result)
        combo.currentTextChanged.connect(
            lambda _t, c=combo: self._on_result_picked(c))
        self._names_table.setCellWidget(r, _NRESULT, combo)
        self._names_table.setCellWidget(r, _NSIGNAL,
                                        self._signal_combo(result, str(vector)))
        self._names_table.setCurrentCell(r, _NNAME)
        self._update()

    def _signal_combo(self, result: str, signal: str = ""):
        """Drop-down of the signals *result* produced.

        A stored signal the run no longer has is kept as an item rather than
        dropped, so loading an old trace set cannot silently lose it; the
        core says so at run time if it is really gone.
        """
        combo = QComboBox()
        combo.addItem("")
        source = self._sources.get(result)
        for name in (source.signals if source else []):
            combo.addItem(name)
        if signal and combo.findText(signal) < 0:
            combo.addItem(signal)
        combo.setCurrentText(signal)
        combo.currentTextChanged.connect(
            lambda text, c=combo: self._on_signal_picked(c, text))
        return combo

    def _row_of(self, widget, column) -> int:
        for r in range(self._names_table.rowCount()):
            if self._names_table.cellWidget(r, column) is widget:
                return r
        return -1

    def _on_result_picked(self, combo):
        """Another result has other signals: the signal is chosen anew."""
        r = self._row_of(combo, _NRESULT)
        if r >= 0:
            self._names_table.setCellWidget(
                r, _NSIGNAL, self._signal_combo(combo.currentText()))
        self._update()

    def _on_signal_picked(self, combo, signal: str):
        """Fill an EMPTY Python name with the derived one; a name the user
        typed is never overwritten."""
        r = self._row_of(combo, _NSIGNAL)
        if r >= 0:
            item = self._names_table.item(r, _NNAME)
            if item is None or not item.text().strip():
                self._names_table.blockSignals(True)
                self._names_table.setItem(
                    r, _NNAME, QTableWidgetItem(_python_name(signal)))
                self._names_table.blockSignals(False)
        self._update()

    def _remove_name_row(self):
        rows = sorted({i.row() for i in self._names_table.selectedIndexes()},
                      reverse=True) or ([self._names_table.rowCount() - 1]
                                        if self._names_table.rowCount() else [])
        for r in rows:
            self._names_table.removeRow(r)
        self._update()

    def _assignments(self) -> list:
        """``(result, python_name, signal)`` per complete row, in table
        order."""
        out = []
        for r in range(self._names_table.rowCount()):
            result = self._names_table.cellWidget(r, _NRESULT)
            name = self._names_table.item(r, _NNAME)
            combo = self._names_table.cellWidget(r, _NSIGNAL)
            result = result.currentText().strip() if result else ""
            name = name.text().strip() if name else ""
            signal = combo.currentText().strip() if combo else ""
            if result and name and signal:
                out.append((result, name, signal))
        return out

    def _variables_kwarg(self, used) -> str:
        """``, variables={"AC1.V_out": "AC1.v(out)"}`` for the assignments
        of the results *used*, "" without."""
        pairs = ["{0}: {1}".format(quoted(result + "." + name),
                                   quoted(result + "." + signal))
                 for result, name, signal in self._assignments()
                 if result in used]
        return ", variables={" + ", ".join(pairs) + "}" if pairs else ""

    # ── the abscissa the sources give by themselves ──────────────────────

    def _default_x(self, y_expression: str) -> str:
        """The x the sources of this y provide (Anton, 2026-07-30).

        The sweep variable of the data (``frequency``, ``time``, the swept
        source of a DC sweep), the x axis of a system run, ``frequency`` or
        ``t`` for functions alone, and the step parameter or the run number
        as soon as y REDUCES each run to one number, because then the runs
        are the abscissa. Whether y reduces is judged by the core from the
        expression's structure (``sl.reduces``).
        """
        st = statement([y_expression], self._sources,
                       x_axis=self._x_axis.currentText())
        if not st.used or st.reason:
            return ""
        used = [self._sources[n] for n in st.used]
        data_names = [n for n in names_in(y_expression)
                      if n.partition(".")[0] in st.used]
        steps = [s.step_name for s in used if s.stepped]
        if reduces(y_expression, data_names or None):
            return next((n for n in steps if n), "run")
        data = [s for s in used if s.kind in DATA_KINDS]
        if data:
            if data[0].kind == SYSTEM:
                return self._x_axis.currentText()
            if data[0].axis:
                return data[0].axis
            return next((n for n in steps if n), "run")       # a stepped OP
        return {"frequency": "frequency", "time": "t"}.get(st.axis, "")

    def _refresh_x(self, row: int):
        """Re-derive the X cell of *row* unless the user typed there.

        The derived text is remembered on the item (UserRole), so a cell the
        user has edited is left alone while an untouched one keeps following
        the y expression.
        """
        item = self._table.item(row, _XEXPR)
        if item is None or item.data(_AS_WRITTEN):
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

    def _default_label(self, row: int) -> str:
        """The label ``plotSweep`` gives a trace of a SLiCAP result: the
        DETECTOR for a plain v/i transfer, otherwise the GAIN TYPE - which
        makes a plot of the five transfers of the asymptotic-gain model
        readable (Anton, 2026-08-03). Only for a trace of ONE SLiCAP
        result; others get none."""
        st = statement([self._cell(row, _YEXPR)], self._sources)
        if len(st.used) != 1:
            return ""
        source = self._sources[st.used[0]]
        if source.kind != SLICAP or not source.gain:
            return ""
        if source.gain == "vi":
            detector = _lit((source.entry.get("kwargs") or {}).get("detector"))
            return str(detector) if detector else ""
        return source.gain

    def _refresh_labels(self):
        """Fill the Label cells with the automatic label, leaving a label the
        user typed alone."""
        for row in range(self._table.rowCount()):
            item = self._table.item(row, _LABEL)
            if item is None or item.data(_AS_WRITTEN):
                continue
            derived = self._default_label(row)
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
            if item is None or item.data(_AS_WRITTEN):
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
    # The table cell is the single source of truth. The creator opens from
    # the button in the cell and writes back into that cell, so nothing can
    # drift between the two.

    def _on_cell_changed(self, item):
        if item.data(_AS_WRITTEN):
            # the user edits a loaded cell: it is the user's now, and
            # cleared it follows the suggestions again
            self._table.blockSignals(True)
            item.setData(_AS_WRITTEN, None)
            self._table.blockSignals(False)
        if item.column() in (_YEXPR, _XEXPR):
            if item.column() == _YEXPR:
                self._refresh_x(item.row())
                self._refresh_labels()
            self._refresh_units(item.row())
            self._refresh_colours()
        if item.column() == _LABEL:
            # a label CLEARED comes back automatic, like a cleared X cell
            self._refresh_labels()
        self._update()

    # ── the expression creator ────────────────────────────────────────────
    #
    # ONE sub-dialog for both tabs (Anton, 2026-08-02): a trace expression
    # and a measurement expression are the same kind of expression over the
    # same sources, so there is one implementation of the four insert menus.

    def _signal_groups(self) -> list:
        """The signal list of the creator: one submenu per result, every
        result of the file (TRACES.md phase 9). A run's signal shows the
        Python name it was given; a system run lists its signals per clock
        domain; the expression variables in s, f or t come last."""
        assigned = {(result, signal): name
                    for result, name, signal in self._assignments()}
        groups, expressions = [], []
        for name, source in self._sources.items():
            if source.kind == NGSPICE:
                items = []
                for signal in source.signals:
                    given = assigned.get((name, signal))
                    label = ("{0}   [{1}.{2}]".format(signal, name, given)
                             if given else signal)
                    items.append((label, (name, signal)))
                groups.append((name, items))
            elif source.kind == SYSTEM:
                for domain, signals in source.domains.items():
                    groups.append(("{0} ({1})".format(name, domain),
                                   [(s, (name, s)) for s in signals]))
            elif source.kind in (SLICAP, FILTER):
                groups.append((name, [(s, (name, s)) for s in source.signals]))
            else:
                expressions.append((name, (name, None)))
        if expressions:
            groups.append(("Expressions", expressions))
        return groups

    def _offers_anything(self) -> bool:
        """True when some result offers a signal: a run only after it ran."""
        return any(items for _group, items in self._signal_groups())

    def _param_groups(self) -> list:
        """The circuit parameters of the runs, as the dataset names them."""
        return [(name, ["{0}.{1}".format(name, p) for p in source.params])
                for name, source in self._sources.items() if source.params]

    def _assign_signal(self, payload) -> str:
        """The Python name of a picked signal, assigning one when it has
        none.

        Called by the creator: the assignment table lives HERE, so its rows
        are created here (TRACES.md phase 6d). A signal of a SLiCAP result,
        a filter or a system run, and a run's signal that is an identifier,
        is already a Python name: nothing is assigned. An identity row such
        as ``{"H_z": "H_z"}`` WAS added (Anton, 2026-11-25).
        """
        result, signal = payload
        if signal is None:
            return result                            # an expression variable
        source = self._sources.get(result)
        if source is None or source.kind != NGSPICE:
            return "{0}.{1}".format(result, signal)
        for given_result, name, given in self._assignments():
            if given_result == result and given == signal:
                return "{0}.{1}".format(result, name)
        if str(signal).isidentifier():
            return "{0}.{1}".format(result, signal)
        name = _python_name(signal)
        self._add_name_row(result, name, signal)
        return "{0}.{1}".format(result, name)

    def _expression_dialog(self, caption: str, text: str, hint: str,
                           for_measurement: bool = False):
        """The creator, filled from the results of the file. Built apart
        from running it, so what it is given can be checked without a modal
        window."""
        from .expression_dialog import ExpressionDialog
        # a goal reduces a run: a trace needs runs to reduce, a measurement
        # reduces even one run to its value
        goals = for_measurement or any(s.stepped for s in self._sources.values())
        return ExpressionDialog(
            caption, text,
            signals=self._signal_groups(),
            on_signal=self._assign_signal,
            params=self._param_groups(),
            goal_enabled=goals,
            hint=hint, parent=self)

    def _open_expression(self, caption: str, text: str, hint: str,
                         for_measurement: bool = False):
        """Run the creator; the new expression, or None when cancelled."""
        dialog = self._expression_dialog(caption, text, hint, for_measurement)
        return dialog.expression() if dialog.exec() else None

    def _edit_trace_expression(self, row: int, column: int):
        """The creator for the Y or X expression cell (*row*, *column*)."""
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
            self._refresh_labels()
        self._refresh_units(row)
        self._refresh_colours()
        self._update()

    def _edit_meas_expression(self, row: int):
        """The creator for the expression cell of measurement *row*."""
        item = self._meas.item(row, _MEXPR)
        text = self._open_expression(
            "Expression of measurement {0}:".format(row + 1),
            item.text() if item else "", self._expression_hint(True), True)
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
        if not self._offers_anything():
            return _NO_RESULTS
        text = ("Numpy syntax over the signals of the results, named "
                "result.signal as in the Design data (AC1.V_out, FLT1.H_fs). "
                "One expression may combine several results: functions are "
                "evaluated where the data lie, and data of two runs must lie "
                "on the same points.")
        text += ("\nA complex signal - a transfer, an AC run - shows its "
                 "MAGNITUDE without a function. mag(...), dB(mag(...)), "
                 "phase(...) and delay(...) give the magnitude, the magnitude "
                 "in dB, the phase and the group delay; real(...) and "
                 "imag(...) its parts.")
        if any(s.kind == FILTER for s in self._sources.values()):
            text += ("\nA filter: H_fs is its Laplace transfer and H_fz the "
                     "filter as the run computes it, in frequency; impulse "
                     "(divided by Ts) and stepResp are its responses at the "
                     "sample times k*Ts, drawn as points.")
        if for_measurement:
            text += ("\nA measurement is ONE value: the goal function is "
                     "what reduces a run to it, e.g. RMS(TRAN1.I_V1**2).")
        elif not any(s.stepped for s in self._sources.values()):
            text += ("\nNo result is stepped, so a goal function would reduce "
                     "a trace to a single number - a measurement, not a trace.")
        return text

    # ── the range ─────────────────────────────────────────────────────────

    def _single_slicap(self, st):
        """The SLiCAP result a statement uses when it is the only one: its
        circuit gives the 'circuit' source of a sweep limit."""
        slicap = [n for n in st.used if self._sources[n].kind == SLICAP]
        return self._sources[slicap[0]].entry if len(slicap) == 1 else None

    def _offer_sweep_parameters(self, st) -> None:
        """The sources of the simulation dialogs, circuit and specs, for a
        limit that names a parameter (Anton, 2026-11-09). The circuit is that
        of the one SLiCAP result the statement uses; its names come from the
        result's selectPars call, or are free when they are not in the file
        (pardefs='circuit', "all"). The specs source offers EVERY numeric
        item of the spec file (_sweep_params_kwarg passes it as params=)."""
        from pathlib import Path
        from .design_data_panel import find_spec_csvs
        from .par_source_table import read_spec_values
        entry = self._single_slicap(st)
        srcs = (pardef_sources(entry["kwargs"].get("pardefs")) if entry
                else pardef_sources(None))
        files = [p.name for p in find_spec_csvs(Path(self._csv_dir))] if self._csv_dir else []
        self._spec_file = next((f for f in files if spec_var_name(f) == srcs["spec_var"]),
                               "specs.csv" if "specs.csv" in files else (files[0] if files else ""))
        spec_values = read_spec_values(self._csv_dir, self._spec_file)
        choices = [("circuit", n, "") for n in (srcs["circuit"] or [])]
        choices += [("specs", n, v) for n, v in spec_values.items()
                    if is_number(display_value(v))]
        offered = (["circuit"] if entry is not None and
                   (srcs["circuit"] is None or srcs["circuit"]) else [])
        offered += ["specs"] if spec_values else []
        for field in (self._sweep_start, self._sweep_stop):
            field.set_choices(choices, sources=offered,
                              any_name=entry is not None and srcs["circuit"] is None)

    def _sweep_params_kwarg(self, st) -> str:
        """``sl.selectPars(<cir>, SPECS_<stem>, ...)`` for the limits that
        name a parameter, "" without. The circuit is that of the one SLiCAP
        result the statement uses; ``None`` for specs alone."""
        if not st.range:
            return ""
        entry = self._single_slicap(st)
        # every named limit is passed: makeDataset() resolves a name from
        # params= only, not from the pardefs of a result
        circuit, specs = [], []
        for field in (self._sweep_start, self._sweep_stop):
            name = field.parameter()
            if name is None or name in circuit + specs:
                continue
            if field._source.currentText() == "circuit":
                if entry is not None:
                    circuit.append(name)
            else:
                specs.append(name)
        if not circuit and not specs:
            return ""
        cir = str(entry["args"][0]) if entry is not None and entry["args"] else "None"
        parts = [cir]
        if specs:
            parts.append(spec_var_name(self._spec_file))
        if circuit:
            parts.append("circuit=[" + ", ".join(quoted(n) for n in circuit) + "]")
        if specs:
            parts.append("specs=[" + ", ".join(quoted(n) for n in specs) + "]")
        return "sl.selectPars(" + ", ".join(parts) + ")"

    def _data_expression(self, st) -> str:
        """The data a statement reads: ``sl.makeDataset({...}, ...)`` of the
        sources it uses (TRACES.md phase 9)."""
        return dataset_call(st, self._sources, self._x_axis.currentText(),
                            self._sweep_start.text().strip(),
                            self._sweep_stop.text().strip(),
                            self._sweep_num.text().strip(),
                            self._sweep_method.currentText(),
                            self._sweep_params_kwarg(st))

    def _restore_range(self, data) -> None:
        """The range and the system x axis of a loaded statement. They WERE
        not read back, so editing a trace set lost its range (Anton,
        2026-11-25)."""
        if data.start:
            self._sweep_start.setText(data.start)
        if data.stop:
            self._sweep_stop.setText(data.stop)
        if data.num and data.num != "0":
            self._sweep_num.setText(data.num)
        if data.method in ("lin", "log"):
            self._sweep_method.blockSignals(True)
            self._sweep_method.setCurrentText(data.method)
            self._sweep_method.blockSignals(False)
            self._method_chosen = True          # keep it: it was written
        if data.x_axis in SYSTEM_X:
            self._x_axis.blockSignals(True)
            self._x_axis.setCurrentText(data.x_axis)
            self._x_axis.blockSignals(False)

    # ── loading an existing statement ─────────────────────────────────────

    def _load_assignments(self, variables: dict) -> None:
        """``{"AC1.V_out": "AC1.v(out)"}`` back into the table."""
        for key, value in variables.items():
            result, _, name = str(key).partition(".")
            _same, _, signal = str(value).partition(".")
            if not name:                           # not in the new form
                continue
            if any(r == result and n == name for r, n, _s in self._assignments()):
                continue
            self._add_name_row(result, name, signal)

    def _on_load_existing(self, index: int):
        """Read an existing trace set back. One written before phase 9, from
        ONE result, comes back in the new form: its names dotted, its data
        made by makeDataset() (Anton, 2026-11-25). OK replaces it where it
        stands (instr_file.place); "New trace dictionary" makes a new one
        under a free name."""
        if index <= 0:
            self._note.stop()
            return
        entry = self._existing[index - 1]
        args = entry["args"]
        data = read_data(args[0] if args else "", self._sources,
                         _lit(entry["kwargs"].get("variables")) or {})
        self._restore_range(data)
        self._table.setRowCount(0)
        # A set written before the trace types were dropped carries
        # trace_type=; it becomes the equivalent FUNCTION in every expression,
        # so what is plotted is visible in the table instead of hiding in an
        # argument the dialog no longer offers (Anton, 2026-07-31).
        wrap = _TYPE_AS_FUNCTION.get(_lit(entry["kwargs"].get("trace_type")))
        self._names_table.setRowCount(0)
        self._load_assignments(data.variables)
        for spec in (_lit(args[1]) if len(args) > 1 else []) or []:
            if isinstance(spec, str):
                spec = {"y": spec}
            if not isinstance(spec, dict):
                continue
            expression = data.rename(spec.get("y", ""))
            if wrap and expression:
                expression = wrap.format(expression)
            self._add_row(expression=expression,
                          x_expression=data.rename(spec.get("x") or ""),
                          label=spec.get("label") or "",
                          color=spec.get("color") or "",
                          y_units=spec.get("yUnits") or "",
                          x_units=spec.get("xUnits") or "",
                          as_written=True)
        if not self._table.rowCount():
            self._add_row()
        self._note.start(entry["name"])
        self._update()

    def editing(self) -> tuple:
        """The trace set and the measurements loaded for editing, for
        InstrEditor.put_dialog_result."""
        return self._note.names()

    def loaded(self) -> dict:
        return self._note.loaded()

    def _on_load_measurement(self, index: int):
        """Read an existing ``NAME = sl.measure(…)`` back into a row, in the
        new form like a trace set.

        Until 2026-08-02 a measurement could be created and never edited
        again: the dialog read make_traces statements back but not measure
        ones.
        """
        if index <= 0:
            return
        entry = self._measurements[index - 1]
        for r in range(self._meas.rowCount()):
            item = self._meas.item(r, _MNAME)
            if item is not None and item.text().strip() == entry["name"]:
                self._meas.setCurrentCell(r, _MEXPR)      # loaded already
                self._tabs.setCurrentIndex(1)
                return
        args = entry.get("args") or []
        kwargs = entry.get("kwargs") or {}
        data = read_data(args[0] if args else "", self._sources,
                         _lit(kwargs.get("variables")) or {})
        self._restore_range(data)
        self._load_assignments(data.variables)
        step = _lit(kwargs.get("step")) or {}
        run = _lit(kwargs.get("run"))
        if step:
            key, value = list(step.items())[0]
            condition = "{0}={1}".format(key, value)
        else:
            condition = "" if run is None else str(run)
        self._add_meas_row(entry["name"],
                           data.rename(str(_lit(args[1]) or "")) if len(args) > 1 else "",
                           condition, str(_lit(kwargs.get("units")) or ""))
        # the name is fixed while editing (Anton, 2026-11-25)
        item = self._meas.item(self._meas.rowCount() - 1, _MNAME)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._tabs.setCurrentIndex(1)
        self._note.start(entry["name"], in_field=False)
        self._update()

    # ── state ─────────────────────────────────────────────────────────────

    def _flag_names(self):
        """Flag a Python name that LaTeX would misrepresent - it is still
        emitted (Anton, 2026-08-03: flag it, do not refuse)."""
        table = self._names_table
        table.blockSignals(True)          # marking a cell IS an item change
        for r in range(table.rowCount()):
            item = table.item(r, _NNAME)
            if item is not None:
                mark_item(item, is_latex_safe(item.text()), LATEX_HINT)
        table.blockSignals(False)

    def _why_not(self) -> str:
        """Why the statements cannot be written, or ""."""
        for st in self._statements():
            if st.reason:
                return st.reason
            if not st.used:
                return ("An expression names no result: write result.signal, "
                        "e.g. AC1.V_out, or pick one with … and Insert Signal.")
        st = self._range_statement()
        if st is not None:
            fields = [self._sweep_start, self._sweep_stop]
            if st.range == "full":
                fields.append(self._sweep_num)
            if not all(w.text().strip() for w in fields) or not all_valid(self._sweep_row):
                return ("Give the range: no data source fixes the points of "
                        "these functions.")
        return ""

    def _update(self, *_args):
        self._flag_names()
        self._show_rows()
        reason = self._why_not()
        self._reason.setText(reason)
        self._reason.setVisible(bool(reason))
        snippet = self.generated_snippet()
        self._preview.setText(snippet or "")
        ok = (bool(self._rows()) and bool(self._name.text().strip())
              or bool(self._meas_rows()))
        allowed = self._note.check(snippet)
        self._add_btn.setEnabled(ok and not reason and allowed)

    # ── emission ──────────────────────────────────────────────────────────

    def _spec_literal(self, row: dict) -> str:
        parts = [f'"y": {quoted(row["y"])}']
        if row["x"]:
            parts.append(f'"x": {quoted(row["x"])}')
        if row["label"]:
            parts.append(f'"label": {quoted(row["label"])}')
        if row["color"]:
            parts.append(f'"color": {quoted(row["color"])}')
        # Empty units are NOT emitted: make_traces then fills what the
        # producer knows, which beats an empty string from the dialog.
        for key in ("yUnits", "xUnits"):
            if row[key]:
                parts.append("{0}: {1}".format(quoted(key), quoted(row[key])))
        return "{" + ", ".join(parts) + "}"

    def generated_snippet(self) -> str:
        rows = self._rows()
        if not rows and not self._meas_rows():
            return ""
        statements = []
        data_texts = []
        if rows:
            st = self._trace_statement()
            data = self._data_expression(st)
            data_texts.append(data)
            name = self._name.text().strip() or "TR1"
            specs = [self._spec_literal(r) for r in rows]
            pad = " " * (len(name) + len(" = sl.make_traces("))
            spec_text = "[" + (",\n" + pad + " ").join(specs) + "]"
            # No trace_type=: what a trace is, is written in its expression,
            # and complex data without a function shows its magnitude.
            statements.append("{0} = sl.make_traces({1},\n{2}{3}{4})".format(
                name, data, pad, spec_text, self._variables_kwarg(st.used)))
        measurements = self._measurement_statements()
        statements += measurements
        data_texts += measurements
        # the spec CSV is loaded once per file into SPECS_<stem>, before
        # its first reader (the instruction dialogs' convention)
        var = spec_var_name(self._spec_file) if self._spec_file else ""
        if var and any("params=" in d and var in d for d in data_texts) and not re.search(
                r"^\s*" + re.escape(var) + r"\s*=", self._existing_text, re.M):
            statements.insert(0, f"{var} = sl.csv2specs({quoted(self._spec_file)})")
        return "\n".join(statements)
