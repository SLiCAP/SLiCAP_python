"""Create / Edit Axes dialog (TRACES.md phase 7).

Second of the three post-processing dialogs: Traces build the DATA, an axis
gives it a PRESENTATION, a figure places axes on a canvas. It emits ONE
statement per object (TRACES.md 7.3), so append-only editing keeps working::

    AX1 = sl.traceAxis("Magnitude", "semilogx", [TR1, TR2],
                       xName="frequency", xUnits="Hz",
                       yName="magnitude", yUnits="dB")

Three kinds of axis (Anton, 2026-08-02):

    XY from traces          traceAxis, axis type lin / semilogx / …
    polar from traces       traceAxis, axis type polar
    pole-zero from SLiCAP   pzAxis - a scatter plot with dedicated markers,
                            built from a result, never from traces

Four kinds since 2026-08-03: **"Auto-create frequency/time sweep from SLiCAP
results"** is ``sweepAxis`` - removed on 2026-08-02 ("one route into an
axis") and REINSTATED a day later, because Anton's walkthrough showed the
trace-dictionary route is MORE work for the standard SLiCAP plot, the common
case. The automatic route (funcType, sweep, everything else derived from the
result) and the composed route (trace dictionaries) coexist; ``plotSweep``
is ``sweepAxis`` plus the figure.

**The SCALE FACTOR lives here, on the axis, never on a trace** (Anton,
2026-07-30). Trace data is in base units, the axis divides for display, so
the same trace reads correctly on a kHz axis and on a Hz axis. UNITS, by
contrast, are a property of the trace variable (Anton, 2026-08-02): they are
set on the trace and only DISPLAYED here, so this dialog reads them from the
traces it places instead of deriving them again. Where a trace states none,
the field stays empty - ``frequency`` is Hz and ``dB(laplace)`` is dB, but ``V_out*I_V1`` gets an
empty field rather than a guess.

The units themselves are NOT derived here: they are read from the traces
being placed (their ``xUnits``/``yUnits``), because units belong to the
trace variable and only the trace knows them.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QWidget,
    QPushButton,
)

from .instr_file import parse_calls
from .value_fields import watch
from .param_table import PARAM_NAME_WIDTH
from .traces_dialog import (next_name, trace_entries, result_entries,
                            is_symbolic, _abscissa, _lit, _q)

from SLiCAP.SLiCAPplots import _SCALEFACTORS

# A pole-zero axis comes from a SLiCAP result: poles and zeros are treated in
# their own way (markers, conjugate pairs) and NGspice does not deliver them,
# so the two data paths are not mixed here (Anton, 2026-08-02).
_PZ_FUNCS = {"doPZ", "doPoles", "doZeros"}

_XY, _POLAR, _PZ, _SWEEP = "xy", "polar", "pz", "sweep"
_KINDS = [("Auto-create frequency/time sweep from SLiCAP results", _SWEEP),
          ("XY from traces", _XY),
          ("Polar from traces", _POLAR),
          ("Pole-zero from SLiCAP results", _PZ)]

# what plotSweep can plot, and the axis types it accepts ('auto' = derived
# from the funcType, exactly as plotSweep derives it)
from SLiCAP.SLiCAPplots import _FUNC_TYPES, _AXIS_TYPES

# The dataType of each SLiCAP analysis, and the funcTypes that CAN plot it
# (Anton, 2026-08-03: the Quantity combo offers only what fits the selected
# result). 'param' plots step parameters against each other and is
# meaningful for any stepped result, so it is offered everywhere.
_RESULT_DATA_TYPE = {"doLaplace": "laplace", "doNumer": "numer",
                     "doDenom": "denom", "doNoise": "noise",
                     "doTime": "time", "doImpulse": "impulse",
                     "doStep": "step"}
_FUNCS_FOR = {"laplace": ["mag", "dBmag", "phase", "delay"],
              "numer":   ["mag", "dBmag", "phase", "delay"],
              "denom":   ["mag", "dBmag", "phase", "delay"],
              "noise":   ["onoise", "inoise"],
              "time":    ["time"],
              "impulse": ["time"],
              "step":    ["time"]}

# axis types of an XY axis; 'polar' is a kind of its own, so it is not here
_XY_TYPES = ["lin", "semilogx", "semilogy", "log"]

_SCALES = [""] + list(_SCALEFACTORS.keys())


def pz_entries(calls: list[dict]) -> list[dict]:
    """SLiCAP results that hold poles and/or zeros."""
    return [c for c in calls if c["func"] in _PZ_FUNCS and c["assigned"]]


def axis_entries(calls: list[dict]) -> list[dict]:
    """Existing named axes (``traceAxis`` / ``pzAxis`` / ``sweepAxis``)."""
    return [c for c in calls
            if c["func"] in ("traceAxis", "pzAxis", "sweepAxis")
            and c["assigned"]]


# What plotSweep calls the plotted quantity, so an axis built here reads
# like the axes SLiCAP has always produced ("magnitude [dB]", not
# "dB_20(V_out) [dB]"). Only the wrapper is recognised; anything else keeps
# the expression, which the user can overwrite.
_QUANTITY_NAMES = {"dB": "magnitude", "dB_10": "magnitude",
                   "dB_20": "magnitude", "abs": "magnitude",
                   "phase": "phase", "delay": "group delay",
                   "groupDelay": "group delay"}


def _quantity_name(expression) -> str:
    """The name of the quantity an expression plots."""
    import ast
    text = str(expression or "").strip()
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return text
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return _QUANTITY_NAMES.get(node.func.id, text)
    return text


def parse_data_argument(source) -> list[str]:
    """The trace sets a traceAxis call was given: ``TR1`` or ``TR1["label"]``.

    Read with the PARSER, not by splitting on commas: the entries are
    variables, and a label may hold commas and brackets of its own
    ("V_out vs frequency  C_a=1e-09").
    """
    import ast
    try:
        node = ast.parse(str(source).strip(), mode="eval").body
    except SyntaxError:
        return []

    def one(item):
        if isinstance(item, ast.Name):
            return item.id
        if (isinstance(item, ast.Subscript)
                and isinstance(item.value, ast.Name)
                and isinstance(item.slice, ast.Constant)):
            return "{0}[{1}]".format(item.value.id, _q(item.slice.value))
        return ""

    if isinstance(node, (ast.List, ast.Tuple)):
        return [name for name in (one(item) for item in node.elts) if name]
    name = one(node)
    return [name] if name else []


def _trace_text(entry: dict) -> str:
    """What a trace PLOTS: 'y vs x', with its legend label after it.

    The tree used to show the label alone, which does not identify a trace -
    a magnitude and a phase of one transfer are both called "gain".
    """
    y = str(entry.get("y", "") or "")
    x = str(entry.get("x", "") or "")
    name = str(entry.get("name", "") or "")
    plotted = "{0} vs {1}".format(y, x) if (y and x) else (y or name)
    return "{0}   [{1}]".format(plotted, name) if name else plotted


def _trace_units(entry: dict) -> tuple:
    """(xUnits, yUnits) a run recorded for one trace."""
    units = {a.get("name"): a.get("value", "")
             for a in entry.get("attributes", [])}
    def one(name):
        value = units.get(name, "")
        return "" if value in (None, "not set") else str(value)
    return one("xUnits"), one("yUnits")


def _number(text: str):
    """A field's text as a plain number, or None when it is not one.

    Axis limits are numbers for matplotlib, so SLiCAP notation is converted
    HERE, at the boundary: the user types ``1M`` and the instruction file
    gets ``1000000.0``. One notation for input, plain numbers in the emitted
    call (the rule of reference_number_notation).
    """
    from SLiCAP.SLiCAPlex import _scale_float
    text = str(text).strip()
    if not text:
        return None
    try:
        return float(_scale_float(text))
    except (ValueError, TypeError):
        return None


class AxesDialog(QDialog):
    """Create or edit ONE named axis."""

    def __init__(self, existing_text: str = "", results_dir=None,
                 parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit Axes")

        calls = parse_calls(existing_text or "")
        # What a RUN recorded: the traces of each dictionary, with their
        # labels and their units. A label is made when the trace is made -
        # "y vs x" plus the step value per run - so the individual traces can
        # only be offered after a run, the rule already set for signals
        # (Anton, 2026-08-03).
        try:
            from .design_data import read_manifest
            self._manifest = read_manifest(results_dir)
        except Exception:
            self._manifest = {"sections": {}}
        self._traces = trace_entries(calls)
        self._results = result_entries(calls)
        self._pz = pz_entries(calls)
        self._existing = axis_entries(calls)
        self._taken = {c["name"] for c in calls}
        self._suggested = {}          # field -> what WE last put in it

        outer = QVBoxLayout(self)
        head = QGridLayout()
        outer.addLayout(head)

        head.addWidget(QLabel("Edit existing:"), 0, 0)
        self._edit = QComboBox()
        self._edit.addItem("(new axis)")
        self._edit.addItems([c["name"] for c in self._existing])
        self._edit.currentIndexChanged.connect(self._on_load_existing)
        head.addWidget(self._edit, 0, 1)

        head.addWidget(QLabel("Axis variable name:"), 1, 0)
        self._name = QLineEdit(next_name("AX", self._taken))
        self._name.setMaximumWidth(PARAM_NAME_WIDTH)
        self._name.textChanged.connect(self._update)
        head.addWidget(self._name, 1, 1)

        head.addWidget(QLabel("Title:"), 2, 0)
        self._title = QLineEdit()
        self._title.setPlaceholderText("placed above the axis")
        self._title.textChanged.connect(self._update)
        head.addWidget(self._title, 2, 1)

        head.addWidget(QLabel("Axis kind:"), 3, 0)
        self._kind = QComboBox()
        for label, key in _KINDS:
            self._kind.addItem(label, key)
        self._kind.currentIndexChanged.connect(self._on_kind_changed)
        head.addWidget(self._kind, 3, 1)

        head.addWidget(QLabel("Axis type:"), 4, 0)
        self._type = QComboBox()
        self._type.addItems(_XY_TYPES)
        self._type.setCurrentText("lin")
        self._type.currentIndexChanged.connect(self._update)
        head.addWidget(self._type, 4, 1)
        self._type_label = head.itemAtPosition(4, 0).widget()

        # ── the automatic sweep (kind "sweep": sl.sweepAxis) ──────────────
        #
        # The plotSweep experience: pick results, a funcType and the sweep -
        # labels, scales and gain colours all follow from the result. Values
        # are SLiCAP notation, like the sweep row of the Traces dialog.
        self._sweep_row = QWidget()
        sweep = QHBoxLayout(self._sweep_row)
        sweep.setContentsMargins(0, 0, 0, 0)
        # the funcType combo is created here but LIVES in the labels grid,
        # in the y-axis Quantity cell: the quantity on y IS the funcType
        # (Anton, 2026-08-03), and x shows 'auto' - frequency or time,
        # derived from the result
        self._func = QComboBox()
        self._func.addItem("auto")
        self._func.addItems(list(_FUNC_TYPES))
        self._func.currentIndexChanged.connect(self._on_func_changed)
        sweep.addWidget(QLabel("Sweep:"))
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
        sweep.addWidget(self._sweep_start)
        sweep.addWidget(QLabel("to"))
        sweep.addWidget(self._sweep_stop)
        sweep.addWidget(QLabel("in"))
        sweep.addWidget(self._sweep_num)
        sweep.addWidget(QLabel("points"))
        sweep.addStretch(1)
        outer.addWidget(self._sweep_row)

        # funcType 'param' sweeps a parameter and plots another: it is the
        # one function that needs names the result cannot supply
        self._param_row = QWidget()
        param = QHBoxLayout(self._param_row)
        param.setContentsMargins(0, 0, 0, 0)
        param.addWidget(QLabel("Sweep parameter:"))
        self._sweep_var = QLineEdit()
        self._sweep_var.setMaximumWidth(PARAM_NAME_WIDTH)
        self._sweep_var.textChanged.connect(self._update)
        param.addWidget(self._sweep_var)
        param.addWidget(QLabel("Plot parameter:"))
        self._y_var = QLineEdit()
        self._y_var.setMaximumWidth(PARAM_NAME_WIDTH)
        self._y_var.textChanged.connect(self._update)
        param.addWidget(self._y_var)
        param.addStretch(1)
        outer.addWidget(self._param_row)

        # ── what goes on the axis ─────────────────────────────────────────
        #
        # An axis COMBINES: several trace sets, or several results whose
        # poles and zeros belong in one picture (TRACES.md phase 7 - "this
        # functionality goes to the creation of axes"). Checked in list
        # order, which is the drawing order.
        self._pick_label = QLabel("Trace sets on this axis:")
        outer.addWidget(self._pick_label)
        # A dictionary is a checkable PARENT and its traces are checkable
        # children: a set holding a magnitude and a phase must be splittable
        # over two axes (Anton, 2026-08-03).
        self._pick = QTreeWidget()
        self._pick.setHeaderHidden(True)
        self._pick.setMaximumHeight(160)
        self._pick.itemChanged.connect(self._on_pick_changed)
        outer.addWidget(self._pick)

        pick_buttons = QHBoxLayout()
        select_all = QPushButton("Select all")
        select_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        deselect_all = QPushButton("Deselect all")
        deselect_all.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        pick_buttons.addWidget(select_all)
        pick_buttons.addWidget(deselect_all)
        pick_buttons.addStretch(1)
        outer.addLayout(pick_buttons)

        # ── axis labels: name, scale factor, units ────────────────────────
        grid = QGridLayout()
        outer.addLayout(grid)
        grid.addWidget(QLabel("Quantity"), 0, 1)
        grid.addWidget(QLabel("Scale factor"), 0, 2)
        grid.addWidget(QLabel("Units"), 0, 3)
        grid.addWidget(QLabel("Axis label"), 0, 4)
        grid.addWidget(QLabel("From"), 0, 5)
        grid.addWidget(QLabel("To"), 0, 6)

        self._x_name, self._x_scale, self._x_units = self._axis_row(grid, 1,
                                                                    "x axis:")
        self._y_name, self._y_scale, self._y_units = self._axis_row(grid, 2,
                                                                    "y axis:")
        # sweep kind: the funcType sits where the y quantity sits, because
        # it IS the y quantity; visibility is toggled per kind
        grid.addWidget(self._func, 2, 1)
        self._x_label = QLabel()
        self._y_label = QLabel()
        grid.addWidget(self._x_label, 1, 4)
        grid.addWidget(self._y_label, 2, 4)

        self._x_min, self._x_max = self._limit_fields(grid, 1)
        self._y_min, self._y_max = self._limit_fields(grid, 2)

        self._warning = QLabel()
        self._warning.setWordWrap(True)
        self._warning.setStyleSheet("color: #b34700; font-size: 9pt;")
        outer.addWidget(self._warning)

        self._hint = QLabel(
            "Trace data is in base units; the scale factor divides for "
            "DISPLAY only, so the same trace can be placed on any axis.")
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

        self._on_kind_changed()

    # ── construction helpers ──────────────────────────────────────────────

    def _axis_row(self, grid, row, label):
        grid.addWidget(QLabel(label), row, 0)
        name = QLineEdit()
        name.setMaximumWidth(PARAM_NAME_WIDTH)
        name.textChanged.connect(self._update)
        grid.addWidget(name, row, 1)
        scale = QComboBox()
        scale.addItems(_SCALES)
        scale.setMaximumWidth(70)
        scale.currentIndexChanged.connect(self._update)
        grid.addWidget(scale, row, 2)
        units = QLineEdit()
        units.setMaximumWidth(80)
        units.textChanged.connect(self._update)
        grid.addWidget(units, row, 3)
        return name, scale, units

    def _limit_fields(self, grid, row):
        low, high = QLineEdit(), QLineEdit()
        for edit, column in ((low, 5), (high, 6)):
            edit.setMaximumWidth(80)
            edit.setPlaceholderText("auto")
            watch(edit, "number")
            edit.textChanged.connect(self._update)
            grid.addWidget(edit, row, column)
        return low, high

    # ── state ─────────────────────────────────────────────────────────────

    def _kind_key(self) -> str:
        return self._kind.currentData()

    def _sources(self) -> list[dict]:
        """The objects the current kind can place on an axis."""
        kind = self._kind_key()
        if kind == _PZ:
            return self._pz
        if kind == _SWEEP:
            # what plotSweep takes: SLiCAP results (a formula plus a sweep)
            return [entry for entry in self._results if is_symbolic(entry)]
        return self._traces

    def _checked_data_types(self) -> list:
        """dataTypes of the CHECKED results, in tree order, duplicates kept
        out."""
        result_types = {entry["name"]: _RESULT_DATA_TYPE.get(entry["func"])
                        for entry in self._sources()}
        out = []
        for i in range(self._pick.topLevelItemCount()):
            item = self._pick.topLevelItem(i)
            if item.checkState(0) != Qt.Checked:
                continue
            data_type = result_types.get(item.text(0))
            if data_type and data_type not in out:
                out.append(data_type)
        return out

    def _refresh_func_choices(self):
        """Offer only the funcTypes the selected results can plot.

        A noise result has spectra, not a transfer: 'dBmag' of it is not a
        thing, and offering it anyway is how a wrong statement gets written
        (Anton, 2026-08-03). No selection yet offers the full set.
        """
        if self._kind_key() != _SWEEP:
            return
        types = self._checked_data_types()
        if types:
            allowed = list(_FUNCS_FOR.get(types[0], [])) + ["param"]
        else:
            allowed = list(_FUNC_TYPES)
        current = self._func.currentText()
        self._func.blockSignals(True)
        self._func.clear()
        self._func.addItem("auto")
        self._func.addItems(allowed)
        self._func.setCurrentText(current if current in ["auto"] + allowed
                                  else "auto")
        self._func.blockSignals(False)
        self._on_func_changed()

    def _on_func_changed(self, *_args):
        self._param_row.setVisible(self._kind_key() == _SWEEP
                                   and self._func.currentText() == "param")
        self._update()

    def _traces_of(self, name: str) -> list[dict]:
        """The traces a RUN recorded for this dictionary: (label, units)."""
        for section in (self._manifest.get("sections") or {}).values():
            for variable in section.get("variables", []):
                if variable.get("name") == name:
                    return [a for a in variable.get("attributes", [])
                            if a.get("kind") == "trace"]
        return []

    def _selected(self) -> list[tuple]:
        """(dictionary, trace entry or None) for everything ticked.

        A parent whose children are ALL ticked yields the dictionary itself,
        so the statement stays short in the ordinary case.
        """
        out = []
        for i in range(self._pick.topLevelItemCount()):
            parent = self._pick.topLevelItem(i)
            name = parent.text(0)
            children = [parent.child(j) for j in range(parent.childCount())]
            if not children:
                if parent.checkState(0) == Qt.Checked:
                    out.append((name, None))
                continue
            ticked = [c for c in children
                      if c.checkState(0) == Qt.Checked]
            if not ticked:
                continue
            if len(ticked) == len(children):
                out.append((name, None))
            else:
                out += [(name, c.data(0, Qt.ItemDataRole.UserRole))
                        for c in ticked]
        return out

    def _picked(self) -> list[str]:
        """What goes into the call: ``TR1`` or ``TR1["label"]``."""
        out = []
        for name, entry in self._selected():
            out.append(name if entry is None
                       else '{0}[{1}]'.format(name, _q(entry.get("name", ""))))
        return out

    def _set_all(self, state):
        self._pick.blockSignals(True)
        for i in range(self._pick.topLevelItemCount()):
            parent = self._pick.topLevelItem(i)
            parent.setCheckState(0, state)
            for j in range(parent.childCount()):
                parent.child(j).setCheckState(0, state)
        self._pick.blockSignals(False)
        self._suggest()
        self._update()

    def _on_kind_changed(self, *_args):
        kind = self._kind_key()
        self._pick_label.setText(
            "SLiCAP results on this axis:" if kind == _PZ else
            "SLiCAP results (and traces to add) on this axis:"
            if kind == _SWEEP else "Trace sets on this axis:")
        self._pick.blockSignals(True)
        self._pick.clear()
        sources = self._sources()
        if kind == _SWEEP:
            # traces are added at AXIS level (Anton, 2026-08-03): the sweep
            # kind offers the trace dictionaries BELOW the results, so a
            # measured NGspice curve can sit beside the SLiCAP transfers -
            # emitted as sweepAxis(..., traces=[...])
            sources = sources + self._traces
        for entry in sources:
            item = QTreeWidgetItem([entry["name"]])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            item.setToolTip(0, "sl.{0}(…)".format(entry["func"]))
            self._pick.addTopLevelItem(item)
            if kind == _PZ or (kind == _SWEEP
                               and entry["func"] != "make_traces"):
                continue          # a whole result: it has no trace children
            for trace in self._traces_of(entry["name"]):
                # WHAT IT PLOTS, not what it is called: the label is for the
                # legend, and both halves of a Bode pair are called "gain"
                # (Anton, 2026-08-03). The key stays the identity - it is
                # what the statement addresses - and lives in UserRole.
                child = QTreeWidgetItem([_trace_text(trace)])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.ItemDataRole.UserRole, trace)
                x_units, y_units = _trace_units(trace)
                child.setToolTip(0, "legend label: {0}   |   {1}[{2}]"
                                 .format(trace.get("name", ""),
                                         trace.get("y", ""),
                                         y_units or "?"))
                item.addChild(child)
            item.setExpanded(True)
        self._pick.blockSignals(False)
        # the type combo carries the choices of the kind: plotSweep accepts
        # 'auto' (derived from the funcType) and polar; a trace axis does not
        self._type.blockSignals(True)
        self._type.clear()
        if kind == _SWEEP:
            self._type.addItem("auto")
            self._type.addItems(list(_AXIS_TYPES))
            self._type.setCurrentText("auto")
        else:
            self._type.addItems(_XY_TYPES)
            self._type.setCurrentText("lin")
        self._type.blockSignals(False)
        show_type = kind in (_XY, _SWEEP)
        self._type.setVisible(show_type)
        self._type_label.setVisible(show_type)
        self._sweep_row.setVisible(kind == _SWEEP)
        self._on_func_changed()
        # a pole-zero axis is Re/Im with pzAxis's own scales; a SWEEP axis
        # names its own labels (that is the point of the automatic route):
        # its y QUANTITY is the funcType combo, its x quantity reads 'auto'
        self._func.setVisible(kind == _SWEEP)
        self._y_name.setVisible(kind != _SWEEP)
        if kind == _SWEEP:
            self._x_name.clear()
            self._x_name.setPlaceholderText("auto")
        else:
            self._x_name.setPlaceholderText("")
        # empty units on the sweep kind MEAN automatic (sweepAxis derives
        # them where it can); the field says so instead of looking forgotten
        for widget in (self._x_units, self._y_units):
            widget.setPlaceholderText("auto" if kind == _SWEEP else "")
        self._refresh_func_choices()
        for widget in (self._x_name, self._y_name):
            widget.setEnabled(kind not in (_PZ, _SWEEP))
        for widget in (self._x_units, self._y_units):
            widget.setEnabled(kind != _PZ)
        self._suggest()
        self._update()

    def _on_pick_changed(self, item, _column=0):
        """A dictionary ticks or unticks all of its traces."""
        if item is not None and item.childCount():
            state = item.checkState(0)
            self._pick.blockSignals(True)
            for j in range(item.childCount()):
                item.child(j).setCheckState(0, state)
            self._pick.blockSignals(False)
        # results of DIFFERENT dataTypes cannot share one sweep: refused at
        # the tick, with the reason, and the tick is undone (Anton,
        # 2026-08-03). sweepData/plotSweep would refuse at run time; the
        # dialog must not emit what the core rejects.
        if (item is not None and self._kind_key() == _SWEEP
                and item.checkState(0) == Qt.Checked
                and len(self._checked_data_types()) > 1):
            types = self._checked_data_types()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Different data types",
                "The selected results hold different data types "
                "({0}): one sweep axis plots ONE of them. Make a second "
                "axis for the other.".format(", ".join(types)))
            self._pick.blockSignals(True)
            item.setCheckState(0, Qt.Unchecked)
            self._pick.blockSignals(False)
        self._refresh_func_choices()
        self._suggest()
        self._update()

    # ── suggestions ───────────────────────────────────────────────────────

    def _specs_of(self, trace_name: str) -> list:
        """The trace specifications of a named trace set."""
        entry = next((c for c in self._traces if c["name"] == trace_name),
                     None)
        args = (entry or {}).get("args") or []
        specs = _lit(args[1]) if len(args) > 1 else None
        return specs if isinstance(specs, list) else []

    def _result_of(self, trace_name: str) -> dict | None:
        """The result a trace set was built from - its first argument names
        it, whether directly (``AC1``) or through ``sl.sweepData(LAPLACE1,
        …)``."""
        entry = next((c for c in self._traces if c["name"] == trace_name),
                     None)
        args = (entry or {}).get("args") or []
        text = args[0] if args else ""
        for result in self._results:
            if result["name"] in str(text):
                return result
        return None

    def _quantities(self) -> tuple[list, list]:
        """(x, y) of everything checked, as (expression, units) pairs.

        The UNITS come from the traces themselves - the ``xUnits``/``yUnits``
        of their specifications - and are never re-derived here (Anton,
        2026-08-02: "we should not suggest units that don't belong to
        traces"). Units are a property of the trace variable; the axis only
        displays them. Where a trace states none, the field stays empty.
        """
        xs, ys = [], []
        for name, entry in self._selected():
            if entry is not None:               # one trace, as the RUN made it
                x_units, y_units = _trace_units(entry)
                ys.append((entry.get("y", ""), y_units))
                xs.append((entry.get("x", ""), x_units))
                continue
            traces = self._traces_of(name)
            if traces:                          # the whole dictionary, ditto
                for trace in traces:
                    x_units, y_units = _trace_units(trace)
                    ys.append((trace.get("y", ""), y_units))
                    xs.append((trace.get("x", ""), x_units))
                continue
            result = self._result_of(name)      # before a run: its statement
            for spec in self._specs_of(name):
                if isinstance(spec, str):
                    spec = {"y": spec}
                if not isinstance(spec, dict):
                    continue
                ys.append((spec.get("y", ""), spec.get("yUnits") or ""))
                xs.append((spec.get("x") or (_abscissa(result) if result
                                             else ""),
                           spec.get("xUnits") or ""))
        return xs, ys

    def _suggest(self):
        """Pre-fill names and units where a naming convention knows them.

        Only fields the user has not typed in are touched: what WE put there
        is remembered, so a suggestion is replaced by the next suggestion but
        an edited field is left alone.
        """
        if self._kind_key() == _SWEEP:
            return                 # sweepAxis names its own labels
        if self._kind_key() == _PZ:
            import SLiCAP.SLiCAPconfigure as ini
            self._fill(self._x_name, "real")
            self._fill(self._y_name, "imag")
            units = "Hz" if ini.hz else "rad/s"
            self._fill(self._x_units, units)
            self._fill(self._y_units, units)
            return
        xs, ys = self._quantities()
        if xs:
            self._fill(self._x_name, str(xs[0][0]))
            self._fill(self._x_units, xs[0][1])
        if ys:
            self._fill(self._y_name, _quantity_name(ys[0][0]))
            self._fill(self._y_units, ys[0][1])

    def _fill(self, widget, text):
        text = str(text or "")
        if widget.text().strip() in ("", self._suggested.get(widget, "")):
            widget.setText(text)
            self._suggested[widget] = text

    def _units_warning(self) -> str:
        """Two different units on one axis: allowed, but said out loud
        (Anton, 2026-08-02 - warn, do not refuse)."""
        if self._kind_key() in (_PZ, _SWEEP):
            return ""
        _xs, ys = self._quantities()
        found = []
        for _expression, units in ys:
            if units and units not in found:
                found.append(units)
        if len(found) > 1:
            return ("Warning: the selected traces carry different units ({0})"
                    " - one axis shows one quantity.".format(", ".join(found)))
        return ""

    # ── editing an existing axis ──────────────────────────────────────────

    def _on_load_existing(self, index: int):
        if index <= 0:
            return
        entry = self._existing[index - 1]
        args = entry.get("args") or []
        kwargs = entry.get("kwargs") or {}
        is_pz = entry["func"] == "pzAxis"
        is_sweep = entry["func"] == "sweepAxis"
        if is_sweep:
            self._load_sweep(entry, args, kwargs)
            return
        self._kind.setCurrentIndex(self._kind.findData(
            _PZ if is_pz else _XY))
        self._name.setText(entry["name"])
        self._title.setText(str(_lit(args[0]) or "") if args else "")
        if not is_pz and len(args) > 1:
            axis_type = _lit(args[1]) or "lin"
            self._kind.setCurrentIndex(self._kind.findData(
                _POLAR if axis_type == "polar" else _XY))
            if axis_type in _XY_TYPES:
                self._type.setCurrentText(axis_type)
        data = args[2] if (not is_pz and len(args) > 2) else (
            args[1] if (is_pz and len(args) > 1) else "")
        # entries are TR1 or TR1["label"], so a dictionary is wanted whole
        # only when it appears bare
        wanted = set(parse_data_argument(data))
        self._pick.blockSignals(True)
        for i in range(self._pick.topLevelItemCount()):
            parent = self._pick.topLevelItem(i)
            name = parent.text(0)
            whole = name in wanted
            parent.setCheckState(0, Qt.Checked if whole else Qt.Unchecked)
            for j in range(parent.childCount()):
                child = parent.child(j)
                stored = child.data(0, Qt.ItemDataRole.UserRole) or {}
                one = '{0}[{1}]'.format(name, _q(stored.get("name", "")))
                child.setCheckState(0, Qt.Checked
                                    if whole or one in wanted
                                    else Qt.Unchecked)
        self._pick.blockSignals(False)
        if is_pz:
            self._x_scale.setCurrentText(str(_lit(kwargs.get("xscale")) or ""))
            self._y_scale.setCurrentText(str(_lit(kwargs.get("yscale")) or ""))
            pairs = (("xmin", self._x_min), ("xmax", self._x_max),
                     ("ymin", self._y_min), ("ymax", self._y_max))
            for key, widget in pairs:
                value = _lit(kwargs.get(key))
                widget.setText("" if value is None else str(value))
        else:
            for key, widget in (("xName", self._x_name),
                                ("xUnits", self._x_units),
                                ("yName", self._y_name),
                                ("yUnits", self._y_units)):
                widget.setText(str(_lit(kwargs.get(key)) or ""))
                self._suggested[widget] = None
            self._x_scale.setCurrentText(str(_lit(kwargs.get("xScale")) or ""))
            self._y_scale.setCurrentText(str(_lit(kwargs.get("yScale")) or ""))
            for key, low, high in (("xLim", self._x_min, self._x_max),
                                   ("yLim", self._y_min, self._y_max)):
                limits = _lit(kwargs.get(key)) or []
                low.setText(str(limits[0]) if len(limits) == 2 else "")
                high.setText(str(limits[1]) if len(limits) == 2 else "")
        self._update()

    # ── emission ──────────────────────────────────────────────────────────

    def _data_argument(self) -> str:
        picked = self._picked()
        if len(picked) == 1:
            return picked[0]
        return "[" + ", ".join(picked) + "]"

    def _limits(self, low, high) -> list | None:
        first, second = _number(low.text()), _number(high.text())
        if first is None or second is None:
            return None
        return [first, second]

    def generated_snippet(self) -> str:
        picked = self._picked()
        if not picked:
            return ""
        name = self._name.text().strip() or "AX1"
        title = self._title.text().strip()
        data = self._data_argument()
        if self._kind_key() == _SWEEP:
            return self._sweep_snippet(name, title, data)
        if self._kind_key() == _PZ:
            parts = []
            for key, widget in (("xmin", self._x_min), ("xmax", self._x_max),
                                ("ymin", self._y_min), ("ymax", self._y_max)):
                value = _number(widget.text())
                if value is not None:
                    parts.append("{0}={1}".format(key, value))
            for key, widget in (("xscale", self._x_scale),
                                ("yscale", self._y_scale)):
                if widget.currentText():
                    parts.append("{0}={1}".format(key,
                                                  _q(widget.currentText())))
            extra = (", " + ", ".join(parts)) if parts else ""
            return "{0} = sl.pzAxis({1}, {2}{3})".format(name, _q(title),
                                                         data, extra)
        axis_type = ("polar" if self._kind_key() == _POLAR
                     else self._type.currentText())
        parts = []
        for key, widget in (("xName", self._x_name), ("xUnits", self._x_units),
                            ("yName", self._y_name),
                            ("yUnits", self._y_units)):
            if widget.text().strip():
                parts.append("{0}={1}".format(key, _q(widget.text().strip())))
        for key, widget in (("xScale", self._x_scale),
                            ("yScale", self._y_scale)):
            if widget.currentText():
                parts.append("{0}={1}".format(key, _q(widget.currentText())))
        for key, low, high in (("xLim", self._x_min, self._x_max),
                               ("yLim", self._y_min, self._y_max)):
            limits = self._limits(low, high)
            if limits:
                parts.append("{0}={1}".format(key, limits))
        extra = (", " + ", ".join(parts)) if parts else ""
        return "{0} = sl.traceAxis({1}, {2}, {3}{4})".format(
            name, _q(title), _q(axis_type), data, extra)

    def _load_sweep(self, entry, args, kwargs):
        """Read a ``sweepAxis`` statement back into the sweep kind."""
        self._kind.setCurrentIndex(self._kind.findData(_SWEEP))
        self._name.setText(entry["name"])
        self._title.setText(str(_lit(args[0]) or "") if args else "")
        wanted = set(parse_data_argument(args[1])) if len(args) > 1 else set()
        wanted |= set(parse_data_argument(kwargs.get("traces") or ""))
        self._pick.blockSignals(True)
        for i in range(self._pick.topLevelItemCount()):
            item = self._pick.topLevelItem(i)
            whole = item.text(0) in wanted
            item.setCheckState(0, Qt.Checked if whole else Qt.Unchecked)
            for j in range(item.childCount()):
                child = item.child(j)
                stored = child.data(0, Qt.ItemDataRole.UserRole) or {}
                one = '{0}[{1}]'.format(item.text(0),
                                        _q(stored.get("name", "")))
                child.setCheckState(0, Qt.Checked if whole or one in wanted
                                    else Qt.Unchecked)
        self._pick.blockSignals(False)
        self._refresh_func_choices()
        if len(args) > 2:
            self._sweep_start.setText(str(_lit(args[2]) or ""))
        if len(args) > 3:
            self._sweep_stop.setText(str(_lit(args[3]) or ""))
        if len(args) > 4:
            self._sweep_num.setText(str(_lit(args[4]) or ""))
        self._func.setCurrentText(str(_lit(kwargs.get("funcType")) or "auto"))
        self._type.setCurrentText(str(_lit(kwargs.get("axisType")) or "auto"))
        self._sweep_var.setText(str(_lit(kwargs.get("sweepVar")) or ""))
        self._y_var.setText(str(_lit(kwargs.get("yVar")) or ""))
        self._x_scale.setCurrentText(str(_lit(kwargs.get("sweepScale")) or ""))
        self._y_scale.setCurrentText(str(_lit(kwargs.get("yScale")) or ""))
        self._x_units.setText(str(_lit(kwargs.get("xUnits")) or ""))
        self._y_units.setText(str(_lit(kwargs.get("yUnits")) or ""))
        for key, low, high in (("xLim", self._x_min, self._x_max),
                               ("yLim", self._y_min, self._y_max)):
            limits = _lit(kwargs.get(key)) or []
            low.setText(str(limits[0]) if len(limits) == 2 else "")
            high.setText(str(limits[1]) if len(limits) == 2 else "")
        self._update()

    def _sweep_snippet(self, name, title, data) -> str:
        """``NAME = sl.sweepAxis(title, results, start, stop, num, …)``.

        Defaults are not emitted: 'auto' IS the automatic route, so the
        statement stays as short as the plotSweep call it replaces.
        """
        start = self._sweep_start.text().strip()
        stop = self._sweep_stop.text().strip()
        num = self._sweep_num.text().strip() or "200"
        if not (start and stop):
            return ""
        # the checked items split into RESULTS (swept by sweepAxis) and
        # trace references (added to the same axis via traces=)
        result_names = {entry["name"] for entry in self._sources()}
        results, refs = [], []
        # NOT "for name, ...": that would rebind the axis-variable-name
        # parameter and the statement came out "TR1 = sl.sweepAxis(...)"
        for picked, entry in self._selected():
            if picked in result_names and entry is None:
                results.append(picked)
            else:
                refs.append(picked if entry is None else '{0}[{1}]'.format(
                    picked, _q(entry.get("name", ""))))
        if not results:
            return ""             # the sweep needs a result to sweep
        data = (results[0] if len(results) == 1
                else "[" + ", ".join(results) + "]")
        parts = []
        if refs:
            parts.append("traces={0}".format(
                refs[0] if len(refs) == 1
                else "[" + ", ".join(refs) + "]"))
        func = self._func.currentText()
        if func == "param":
            # the one funcType that needs names the result cannot supply
            if not (self._sweep_var.text().strip()
                    and self._y_var.text().strip()):
                return ""
            parts.append("sweepVar={0}".format(
                _q(self._sweep_var.text().strip())))
            parts.append("yVar={0}".format(_q(self._y_var.text().strip())))
        if func != "auto":
            parts.append("funcType={0}".format(_q(func)))
        if self._type.currentText() not in ("", "auto"):
            parts.append("axisType={0}".format(_q(self._type.currentText())))
        # the x scale factor IS plotSweep's sweepScale: it scales the sweep
        # values and the axis display together, the old path's own coupling
        if self._x_scale.currentText():
            parts.append("sweepScale={0}".format(
                _q(self._x_scale.currentText())))
        if self._y_scale.currentText():
            parts.append("yScale={0}".format(_q(self._y_scale.currentText())))
        for key, widget in (("xUnits", self._x_units),
                            ("yUnits", self._y_units)):
            if widget.text().strip():
                parts.append("{0}={1}".format(key, _q(widget.text().strip())))
        for key, low, high in (("xLim", self._x_min, self._x_max),
                               ("yLim", self._y_min, self._y_max)):
            limits = self._limits(low, high)
            if limits:
                parts.append("{0}={1}".format(key, limits))
        extra = (", " + ", ".join(parts)) if parts else ""
        return "{0} = sl.sweepAxis({1}, {2}, {3}, {4}, {5}{6})".format(
            name, _q(title), data, _q(start), _q(stop), num, extra)

    def _update(self, *_args):
        snippet = self.generated_snippet()
        self._preview.setText(snippet or "")
        self._warning.setText(self._units_warning())
        for widget, name, scale, units in (
                (self._x_label, self._x_name, self._x_scale, self._x_units),
                (self._y_label, self._y_name, self._y_scale, self._y_units)):
            text = name.text().strip()
            unit = scale.currentText() + units.text().strip()
            widget.setText("{0} [{1}]".format(text, unit) if (text or unit)
                           else "")
        self._add_btn.setEnabled(bool(snippet)
                                 and bool(self._name.text().strip()))
