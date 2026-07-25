"""Create / edit plot dialog (SLNG.md, "Plot-instruction dialog").

Generates a plot call from named analysis results defined in the instruction
file:

- NGspice results (sl.op/dc/ac/tran/noise)   → ``sl.plot(...)`` over
  ``sl.ngspice_instr2traces(...)`` trace dicts;
- SLiCAP x-y results (sl.doLaplace, doNoise…) → ``sl.plotSweep(...)``;
- SLiCAP pole/zero results (doPoles/doZeros/doPZ) → ``sl.plotPZ(...)``.

Note the asymmetry (Anton): ``sl.plot()`` is the GENERIC trace plotter — it
serves SLiCAP traces just as well (csv2traces, figure trace dicts,
measurement data, …). It is
simply the ONLY route for NGspice results, which reach it through trace
conversion; SLiCAP results additionally have their native ``plotSweep`` /
``plotPZ``, which is what this dialog generates for them.

The dialog is rules-table driven (SLNG.md "Decisions and build order
(2026-07-11)"): the funcType choices and the visible axes/label fields
follow the plotSweep dataType class of the selected result (freq / noise /
time / params, via ``_SL_CLASS`` + ``_CLASS_FUNC_TYPES``), and the
axis-type combo offers "auto" for plotSweep only (plot() takes the axis
type positionally).

Wizard structure (SLNG.md "Plot dialog rework", 2026-07-11):
``SelectPlotDialog`` (step 1) picks WHICH plot — new (with its source mode:
from simulation results / from other plots) or an existing one — and
``PlotDialog`` (step 2) is the mode-tailored editor, itself TWO PAGES
(Back / Next / Add plot in one window):

- page 1 — WHAT to plot. "From simulation results": ONE result, picked
  from a dropdown (one result per plot — combining results in one figure
  goes through "from other plots" overlays); the result's family/dataType
  determines the plot type (plotSweep / plotPZ / plot) and the core
  options shown (funcType, sweep range, trace selection, params
  variables, noise sources). "From other plots": the figure checkboxes
  with per-figure trace selection, plus the axis type.
- page 2 — presentation: plot name/title, labels, scales, units, limits
  and the show/save/cursors flags, only the fields relevant for the
  chosen plot type.

"From other plots" composes ``sl.plot()`` overlays from any existing
figure's traces via the core helper ``sl.fig2traces(FIG, [labels])`` —
including traces that only exist inside a plotSweep figure. To make figures
referenceable, every generated plot call is an ASSIGNMENT
(``DBMAG = sl.plotSweep("dBmag", …)``); legacy bare calls become assigned
the next time they are edited.

Editing is append-only: the fields prefill from the parsed call, and the
regenerated call is appended to the instruction file — a later definition
of the same figure simply re-plots; removing the superseded line is the
user's job in the editor.
"""
from __future__ import annotations

import ast
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
    QRadioButton, QButtonGroup, QListWidget, QStackedWidget,
    QPushButton, QWidget,
)

from .instr_file import parse_calls

# Goal-function registry (SLiCAPmath._GOAL_FUNCTIONS, Anton's plan): the
# drop-down adapts automatically to goal functions added there.
# name → (python name for the snippet, [(param label, default), …]) —
# a LIST because factories may need several parameters (goal_x_at_nth_y).
from SLiCAP.SLiCAPmath import _GOAL_FUNCTIONS
_GOALS = {name: (fn.__name__, list(params))
          for name, fn, params in _GOAL_FUNCTIONS}
_NO_GOAL = "(none)"


class _CheckCombo(QComboBox):
    """Drop-down with checkable items (multi-select). Empty selection shows
    the placeholder; the closed combo displays the checked items joined."""

    def __init__(self, placeholder: str = "all traces", parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(placeholder)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self._on_pressed)

    def set_names(self, names: list[str]):
        m = self.model()
        m.clear()
        for n in names:
            it = QStandardItem(n)
            # checkable but not selectable: clicking toggles, the popup
            # is not closed by an item activation
            it.setFlags(Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemIsEnabled)
            it.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
            m.appendRow(it)
        self._refresh()

    def names(self) -> list[str]:
        m = self.model()
        return [m.item(i).text() for i in range(m.rowCount())]

    def checked(self) -> list[str]:
        m = self.model()
        return [m.item(i).text() for i in range(m.rowCount())
                if m.item(i).checkState() == Qt.CheckState.Checked]

    def set_checked(self, names: list[str]):
        m = self.model()
        for i in range(m.rowCount()):
            it = m.item(i)
            it.setCheckState(Qt.CheckState.Checked if it.text() in names
                             else Qt.CheckState.Unchecked)
        self._refresh()

    def _on_pressed(self, index):
        it = self.model().itemFromIndex(index)
        it.setCheckState(Qt.CheckState.Unchecked
                         if it.checkState() == Qt.CheckState.Checked
                         else Qt.CheckState.Checked)
        self._refresh()

    def _refresh(self):
        self.lineEdit().setText(", ".join(self.checked()))

_NG_FUNCS    = {"op", "dc", "ac", "tran", "noise"}
# Assignments producing a trace dict — sl.plot()'s native input.
_TRACE_FUNCS = {"csv2traces", "ngspice_instr2traces",
                "LTspiceAC2SLiCAPtraces", "Cadence2traces"}
# doDC / doDCvar are deliberately absent: their dataTypes ('dc', 'dcvar')
# are not in plotSweep's plotDataTypes — those results are table material
# (SLNG.md 2026-07-11 decisions), not plot sources.
_SL_XY_FUNCS = {"doLaplace", "doNoise", "doTime", "doImpulse", "doStep",
                "doNumer", "doDenom", "doParams"}
_SL_PZ_FUNCS = {"doPoles", "doZeros", "doPZ"}
_PLOT_FUNCS  = {"plot", "plotSweep", "plotPZ"}

_TRACE_TYPES = ["real", "mag", "dBmag", "phase", "delay", "imag"]

# Rules table (SLNG.md 2026-07-11): plotSweep's dataType class per producing
# function, and the funcType choices valid for each class (first = default).
# Mirrors plotSweep's own dispatch — plotSweep does NOT resolve 'auto' for
# dataType 'params', so the params class carries the explicit "param" only.
_SL_CLASS = {"doLaplace": "freq", "doNumer": "freq", "doDenom": "freq",
             "doNoise": "noise",
             "doTime": "time", "doImpulse": "time", "doStep": "time",
             "doParams": "params"}
_CLASS_FUNC_TYPES = {"freq":   ["auto", "mag", "dBmag", "phase", "delay"],
                     "noise":  ["auto", "onoise", "inoise"],
                     "time":   ["auto", "time"],
                     "params": ["param"]}

# plotSweep resolves axisType 'auto' from funcType/dataType; plot() takes the
# axis type as a positional argument and accepts no 'auto'.
_AXIS_TYPES_SL = ["auto", "lin", "log", "semilogx", "semilogy", "polar"]
_AXIS_TYPES_NG = ["lin", "log", "semilogx", "semilogy", "polar"]

# Smart defaults per producing function (SLNG.md spec).
_NG_DEFAULTS = {"ac":    ("semilogx", "dBmag"),
                "noise": ("log",      "mag"),
                "tran":  ("lin",      "real"),
                "fft":   ("semilogx", "dBmag"),   # tran with fft= (spectrum)
                "dc":    ("lin",      "real"),
                "op":    ("lin",      "real")}


def _ng_kind(entry) -> "str | None":
    """Effective NGspice analysis kind of a parsed call: the producing
    function name, except that ``sl.tran(..., fft=...)`` returns a
    FREQUENCY-domain result (dataType 'fft') and gets the ac-like
    treatment (SLNG.md item 3)."""
    if entry is None or entry["func"] not in _NG_FUNCS:
        return None
    if entry["func"] == "tran" and entry.get("kwargs", {}).get("fft"):
        return "fft"
    return entry["func"]


def _names_keys(entry: dict) -> list[str]:
    """Keys of a parsed names= kwarg — the statically known trace names."""
    try:
        d = ast.literal_eval(entry["kwargs"].get("names") or "")
    except (ValueError, SyntaxError):
        return []
    return [str(k) for k in d] if isinstance(d, dict) else []


def _family(func: str) -> str | None:
    # "ngspice" is the sl.plot() family: NGspice results (their only route
    # is trace conversion) plus ready trace-dict variables of any origin.
    if func in _NG_FUNCS or func in _TRACE_FUNCS:
        return "ngspice"
    if func in _SL_XY_FUNCS:
        return "slicap"
    if func in _SL_PZ_FUNCS:
        return "pz"
    return None


def _lit_str(src: str | None) -> str | None:
    try:
        v = ast.literal_eval(src) if src else None
    except (ValueError, SyntaxError):
        return None
    return v if isinstance(v, str) else None


def _fig_label(entry: dict) -> str:
    """Display label of a plot entry: its figure fileName."""
    return _lit_str(entry["args"][0] if entry["args"] else None) \
        or entry["name"]


def plot_entries(calls: list[dict]) -> list[dict]:
    """Existing plots, deduped by figure fileName (last definition wins) —
    a legacy bare call superseded by its assigned regeneration is not
    listed twice."""
    plots: dict[str, dict] = {}
    for c in calls:
        if c["func"] in _PLOT_FUNCS:
            plots[_fig_label(c)] = c
    return list(plots.values())


def _infer_mode(entry: dict) -> str:
    """Source mode of an existing plot call: overlays built from other
    figures contain fig2traces; everything else edits as simulation
    results."""
    if entry["func"] == "plot" and len(entry["args"]) > 3 \
            and "fig2traces" in (entry["args"][3] or ""):
        return "figures"
    return "results"


class SelectPlotDialog(QDialog):
    """Step 1 of the plot wizard: WHICH plot — a new one (and its source
    mode) or an existing one to edit. Call ``selection()`` after ``exec()``
    returns True; it yields ``(mode, edit_name)`` where mode is "results"
    or "figures" and edit_name is the parse_calls key of the existing plot
    (None for a new plot)."""

    def __init__(self, existing_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select / Create Plot")
        self.setMinimumWidth(380)
        calls = parse_calls(existing_text or "")
        self._plots = plot_entries(calls)
        has_figs = any(c["func"] in _PLOT_FUNCS and c["assigned"]
                       for c in calls)

        lay = QVBoxLayout(self)
        self._new = QRadioButton("New plot")
        self._edit = QRadioButton("Edit existing plot:")
        which = QButtonGroup(self)
        which.addButton(self._new)
        which.addButton(self._edit)
        self._new.setChecked(True)

        lay.addWidget(self._new)
        self._from_results = QRadioButton("From simulation results")
        self._from_figs = QRadioButton("From other plots")
        # Placeholder for the coming redefinition of plot composition
        # (Anton, 2026-07-12): a figure editor driving the full SLiCAP
        # figure object — a grid of axes of different types, each holding
        # traces from ANY origin (results, figures, measurement data,
        # functions). Needs the trace-metadata spec round (units + scale
        # factors + provenance on the trace object) first; until then the
        # entry announces the capability and stays disabled. "From other
        # plots" remains the interim single-axis overlay and will be
        # absorbed by the figure editor.
        self._user_figs = QRadioButton("Create / edit user-defined figures")
        self._user_figs.setEnabled(False)
        self._user_figs.setToolTip(
            "Planned: compose figures with multiple axes and traces from "
            "any source (simulations, other figures, measurement data).")
        src = QButtonGroup(self)
        src.addButton(self._from_results)
        src.addButton(self._from_figs)
        src.addButton(self._user_figs)
        self._from_results.setChecked(True)
        for rb in (self._from_results, self._from_figs, self._user_figs):
            row = QHBoxLayout()
            row.addSpacing(24)
            row.addWidget(rb)
            lay.addLayout(row)
        if not has_figs:
            self._from_figs.setEnabled(False)
            self._from_figs.setToolTip(
                "No plots defined yet — a plot must exist before its "
                "traces can be reused.")

        lay.addWidget(self._edit)
        self._list = QListWidget()
        for p in self._plots:
            self._list.addItem(f'{_fig_label(p)}  (sl.{p["func"]})')
        self._list.itemClicked.connect(
            lambda *_: self._edit.setChecked(True))
        self._list.itemDoubleClicked.connect(self.accept)
        row = QHBoxLayout()
        row.addSpacing(24)
        row.addWidget(self._list)
        lay.addLayout(row)
        if not self._plots:
            self._edit.setEnabled(False)
            self._list.setEnabled(False)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def selection(self) -> tuple[str, str | None]:
        if self._edit.isChecked() and self._list.currentRow() >= 0:
            return "results", self._plots[self._list.currentRow()]["name"]
        return ("figures" if self._from_figs.isChecked() else "results",
                None)


class PlotDialog(QDialog):
    """Step 2 of the plot wizard: the mode-tailored, two-page editor.

    *mode* is "results" (ONE simulation result, picked from a dropdown —
    plotSweep / plot / plotPZ per family) or "figures" (an sl.plot()
    overlay from other figures' traces via fig2traces). *edit_name*
    prefills from the existing plot with that parse_calls key; its mode is
    then inferred from the parsed call and *mode* is ignored.

    Page 1 holds WHAT is plotted (result / figures + type-specific core
    options), page 2 the presentation (name, labels, scales, limits,
    flags). Call ``generated_snippet()`` after ``exec()`` returns True.
    """

    def __init__(self, existing_text: str = "", mode: str = "results",
                 edit_name: str | None = None, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(480)
        calls = parse_calls(existing_text or "")
        self._plots = plot_entries(calls)
        self._taken = {c["name"] for c in calls}
        self._edit_entry = next((p for p in self._plots
                                 if p["name"] == edit_name), None)
        if self._edit_entry is not None:
            mode = _infer_mode(self._edit_entry)
        self._mode = mode
        if mode == "figures":
            # sources = assigned figures (referenceable as variables),
            # never the figure being edited itself
            self._results = [c for c in calls
                             if c["func"] in _PLOT_FUNCS and c["assigned"]
                             and (self._edit_entry is None
                                  or c["name"] != self._edit_entry["name"])]
        else:
            self._results = [c for c in calls if _family(c["func"])]
        self._prefilling = False
        # Combo contents depend on the selected family/class; repopulated on
        # a family or class CHANGE only, so reselections keep the user's pick.
        self._fam_shown: str | None = None
        self._cls_shown: str | None = None
        if self._edit_entry is not None:
            self.setWindowTitle(f"Edit Plot: {_fig_label(self._edit_entry)}")
        else:
            self.setWindowTitle("New Plot — from other plots"
                                if mode == "figures" else
                                "New Plot — from simulation results")

        layout = QVBoxLayout(self)
        self._stack = QStackedWidget()
        self._page1 = self._build_page1()
        self._page2 = self._build_page2()
        self._stack.addWidget(self._page1)
        self._stack.addWidget(self._page2)
        layout.addWidget(self._stack)

        nav = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._back_btn.clicked.connect(lambda: self._go(0))
        nav.addWidget(self._back_btn)
        nav.addStretch()
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.reject)
        nav.addWidget(close_btn)
        self._next_btn = QPushButton("Next →")
        self._next_btn.clicked.connect(lambda: self._go(1))
        nav.addWidget(self._next_btn)
        self._add_btn = QPushButton("Add plot")
        self._add_btn.clicked.connect(self.accept)
        nav.addWidget(self._add_btn)
        for b in (self._back_btn, close_btn, self._next_btn, self._add_btn):
            b.setAutoDefault(False)
        layout.addLayout(nav)

        if self._edit_entry is not None:
            self._prefilling = True
            try:
                self._prefill(self._edit_entry)
            finally:
                self._prefilling = False
        else:
            self._on_selection_changed()
        self._go(0)
        # Discard protection: anything the user changes makes the generated
        # call differ from this baseline ("" for a new plot, the regenerated
        # call for an edited one) — reject() then asks before discarding.
        self._baseline = self.generated_snippet()

    # ── page construction ──────────────────────────────────────────────────

    @staticmethod
    def _mini(width=80):
        e = QLineEdit()
        e.setMaximumWidth(width)
        return e

    def _build_page1(self) -> QWidget:
        """Page 1 — WHAT to plot: the result (dropdown) or the source
        figures (checkboxes), plus the type-specific core options."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        self._checks: list[QCheckBox] = []
        self._ykeys: dict[str, QLineEdit] = {}
        if self._mode == "figures":
            box = QGroupBox("Plots to take traces from")
            box_lay = QVBoxLayout(box)
            for c in self._results:
                cb = QCheckBox(f'{_fig_label(c)}  (sl.{c["func"]})')
                cb.toggled.connect(self._on_selection_changed)
                box_lay.addWidget(cb)
                self._checks.append(cb)
                # Figure trace labels are runtime values — statically
                # unknown, hence the bare placeholder.
                yk = QLineEdit()
                yk.setPlaceholderText("all traces")
                yk.setToolTip("Comma-separated trace labels; empty takes "
                              "every trace of the figure.")
                row = QHBoxLayout()
                row.addSpacing(24)
                row.addWidget(QLabel("traces:"))
                row.addWidget(yk)
                box_lay.addLayout(row)
                yk.setVisible(False)
                self._ykeys[c["name"]] = yk
            if not self._results:
                box_lay.addWidget(QLabel(
                    "No other plots defined yet —\ncreate a plot from "
                    "simulation results first."))
            lay.addWidget(box)

        grid = QGridLayout()
        r = 0
        if self._mode != "figures":
            grid.addWidget(QLabel("Result:"), r, 0)
            self._result_combo = QComboBox()
            self._result_combo.addItems(
                [f'{c["name"]}  (sl.{c["func"]})' for c in self._results])
            self._result_combo.setCurrentIndex(-1)
            self._result_combo.currentIndexChanged.connect(
                self._on_selection_changed)
            grid.addWidget(self._result_combo, r, 1)
            r += 1
            self._ptype_cap = QLabel("Plot type:")
            self._ptype_lbl = QLabel("—")
            grid.addWidget(self._ptype_cap, r, 0)
            grid.addWidget(self._ptype_lbl, r, 1)
            r += 1
            if not self._results:
                self._result_combo.setEnabled(False)
                grid.addWidget(QLabel(
                    "No analysis instructions defined yet — add one via "
                    "the schematic's Instruction menu first."), r, 0, 1, 2)
                r += 1

        self._ftype_lbl = QLabel("Function type:")
        self._ftype = QComboBox()
        grid.addWidget(self._ftype_lbl, r, 0)
        grid.addWidget(self._ftype, r, 1)
        r += 1

        self._ttype_lbl = QLabel("Trace type:")
        self._ttype = QComboBox()
        self._ttype.addItems(_TRACE_TYPES)
        grid.addWidget(self._ttype_lbl, r, 0)
        grid.addWidget(self._ttype, r, 1)
        r += 1

        # Trace selection (y_keys): a checkable drop-down when the variable
        # names are statically known (the instruction's names= dict); a free
        # text field otherwise. Empty selection = all captured signals.
        self._ng_traces_lbl = QLabel("Traces:")
        self._ng_traces_combo = _CheckCombo("all traces")
        self._ng_names_shown: list[str] = []
        grid.addWidget(self._ng_traces_lbl, r, 0)
        grid.addWidget(self._ng_traces_combo, r, 1)
        r += 1
        self._ng_traces = QLineEdit()
        self._ng_traces.setPlaceholderText("all traces")
        self._ng_traces.setToolTip(
            "Comma-separated trace selection (y_keys); empty plots every "
            "captured signal.")
        grid.addWidget(self._ng_traces, r, 1)
        r += 1

        # Goal function (STEPPED NGspice results only): reduce each run to
        # one value — x becomes the step parameter, y the goal result.
        self._goal_lbl = QLabel("Goal function:")
        self._goal = QComboBox()
        self._goal.addItems([_NO_GOAL] + list(_GOALS))
        self._goal.currentIndexChanged.connect(self._on_goal_changed)
        grid.addWidget(self._goal_lbl, r, 0)
        grid.addWidget(self._goal, r, 1)
        r += 1
        # Parameter fields, built per registry entry (a factory may need
        # several parameters — goal_x_at_nth_y takes two).
        self._goal_par_box = QWidget()
        par_lay = QHBoxLayout(self._goal_par_box)
        par_lay.setContentsMargins(0, 0, 0, 0)
        par_lay.addStretch()
        self._goal_pars: list[tuple[str, QLineEdit]] = []
        self._goal_shown: str | None = None
        grid.addWidget(self._goal_par_box, r, 1)
        r += 1

        self._axis_lbl = QLabel("Axis type:")
        self._axis = QComboBox()
        self._axis.addItems(_AXIS_TYPES_NG)
        grid.addWidget(self._axis_lbl, r, 0)
        grid.addWidget(self._axis, r, 1)
        r += 1

        self._sweep_lbl = QLabel("Sweep start / stop / points:")
        self._sw_start = QLineEdit("10")
        self._sw_stop  = QLineEdit("10e6")
        self._sw_num   = QLineEdit("200")
        sweep_row = QHBoxLayout()
        for w in (self._sw_start, self._sw_stop, self._sw_num):
            w.setMaximumWidth(90)
            w.textChanged.connect(self._update)
            sweep_row.addWidget(w)
        sweep_row.addStretch()
        grid.addWidget(self._sweep_lbl, r, 0)
        grid.addLayout(sweep_row, r, 1)
        r += 1

        # dataType 'params' plots parameters against each other: the swept
        # parameter and the plotted parameter(s) are content, hence page 1;
        # plotSweep errors without sweepVar and yVar.
        self._sweepvar_lbl = QLabel("Sweep variable:")
        self._sweepvar = self._mini(140)
        self._sweepvar.textChanged.connect(self._update)
        grid.addWidget(self._sweepvar_lbl, r, 0)
        grid.addWidget(self._sweepvar, r, 1)
        r += 1
        self._xvar_lbl = QLabel("x variable:")
        self._xvar = self._mini(140)
        self._xvar.setPlaceholderText("sweep variable")
        grid.addWidget(self._xvar_lbl, r, 0)
        grid.addWidget(self._xvar, r, 1)
        r += 1
        self._yvar_lbl = QLabel("y variable(s):")
        self._yvar = QLineEdit()
        self._yvar.setPlaceholderText("parameter, or comma-separated list")
        self._yvar.textChanged.connect(self._update)
        grid.addWidget(self._yvar_lbl, r, 0)
        grid.addWidget(self._yvar, r, 1)
        r += 1

        self._noise_lbl = QLabel("Noise sources:")
        self._noise = QLineEdit()
        self._noise.setPlaceholderText(
            "all when empty; comma-separated for a selection")
        grid.addWidget(self._noise_lbl, r, 0)
        grid.addWidget(self._noise, r, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        lay.addStretch()
        return page

    def _build_page2(self) -> QWidget:
        """Page 2 — presentation: name/title, labels, scales, limits,
        flags. Only the fields relevant for the chosen plot type show."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        # What was chosen on page 1, as a title — not selectable here.
        self._p2_header = QLabel("")
        font = self._p2_header.font()
        font.setBold(True)
        self._p2_header.setFont(font)
        lay.addWidget(self._p2_header)
        grid = QGridLayout()
        grid.addWidget(QLabel("Plot name:"), 0, 0)
        self._name = QLineEdit()
        self._name.setPlaceholderText("figure file name, e.g. VampStep")
        self._name.textChanged.connect(self._update)
        grid.addWidget(self._name, 0, 1)
        grid.addWidget(QLabel("Title:"), 1, 0)
        self._title = QLineEdit()
        grid.addWidget(self._title, 1, 1)
        lay.addLayout(grid)

        self._ax_box = QGroupBox("Labels && scales  (optional)")
        ag = QGridLayout(self._ax_box)
        self._sweepscale_lbl = QLabel("Sweep scale:")
        self._sweepscale = self._mini(50)
        self._sweepscale.setPlaceholderText("M")
        ag.addWidget(self._sweepscale_lbl, 0, 0)
        ag.addWidget(self._sweepscale,     0, 1)

        self._xname_lbl = QLabel("x name:")
        self._xname  = self._mini(110)
        self._xscale = self._mini(50)
        self._xscale.setPlaceholderText("scale")
        self._xunits = self._mini(70)
        self._xunits.setPlaceholderText("units")
        ag.addWidget(self._xname_lbl, 1, 0)
        ag.addWidget(self._xname,     1, 1)
        ag.addWidget(self._xscale,    1, 2)
        ag.addWidget(self._xunits,    1, 3)

        self._yname_lbl = QLabel("y name:")
        self._yname  = self._mini(110)
        self._yscale = self._mini(50)
        self._yscale.setPlaceholderText("scale")
        self._yunits = self._mini(70)
        self._yunits.setPlaceholderText("units")
        ag.addWidget(self._yname_lbl, 2, 0)
        ag.addWidget(self._yname,     2, 1)
        ag.addWidget(self._yscale,    2, 2)
        ag.addWidget(self._yunits,    2, 3)

        self._xlim_lbl = QLabel("x limits:")
        self._xlim_lo, self._xlim_hi = self._mini(), self._mini()
        ag.addWidget(self._xlim_lbl, 3, 0)
        ag.addWidget(self._xlim_lo,  3, 1)
        ag.addWidget(self._xlim_hi,  3, 2)

        self._ylim_lbl = QLabel("y limits:")
        self._ylim_lo, self._ylim_hi = self._mini(), self._mini()
        ag.addWidget(self._ylim_lbl, 4, 0)
        ag.addWidget(self._ylim_lo,  4, 1)
        ag.addWidget(self._ylim_hi,  4, 2)
        ag.setColumnStretch(4, 1)
        lay.addWidget(self._ax_box)

        flags = QHBoxLayout()
        self._show = QCheckBox("Show on screen")
        self._show.setChecked(True)
        self._save = QCheckBox("Save to img folder")
        self._save.setChecked(True)
        self._cursors = QCheckBox("Cursors")
        self._cursors.setChecked(True)
        flags.addWidget(self._show)
        flags.addWidget(self._save)
        flags.addWidget(self._cursors)
        flags.addStretch()
        lay.addLayout(flags)
        lay.addStretch()
        return page

    # ── navigation / state ─────────────────────────────────────────────────

    def reject(self):
        """Ask before discarding actual input — Cancel must not silently
        eat a half-configured plot (Anton, 2026-07-11). Covers the Cancel
        button, Esc and the window close button (all route here)."""
        from PySide6.QtWidgets import QMessageBox
        if self.generated_snippet() != getattr(self, "_baseline", ""):
            answer = QMessageBox.question(
                self, "Discard plot?",
                "The plot has not been added yet — discard your input?",
                QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel)
            if answer != QMessageBox.StandardButton.Discard:
                return
        super().reject()

    def _go(self, page: int):
        if page == 1:
            sel = self._selected()
            if self._mode == "figures":
                self._p2_header.setText(
                    "Overlay from:  "
                    + ", ".join(_fig_label(c) for c in sel))
            elif sel:
                self._p2_header.setText(
                    f'{sel[0]["name"]}  (sl.{sel[0]["func"]})   —   '
                    + self._ptype_lbl.text())
                # suggest the plot name so "Add plot" is one click away
                if not self._name.text().strip():
                    self._name.setText(sel[0]["name"])
        self._stack.setCurrentIndex(page)
        self._back_btn.setVisible(page == 1)
        self._next_btn.setVisible(page == 0)
        self._add_btn.setVisible(page == 1)
        self._update()

    def _selected(self) -> list[dict]:
        if self._mode == "figures":
            return [c for c, cb in zip(self._results, self._checks)
                    if cb.isChecked()]
        idx = self._result_combo.currentIndex()
        return [self._results[idx]] if 0 <= idx < len(self._results) else []

    def _active_family(self) -> str | None:
        sel = self._selected()
        if self._mode == "figures":
            return "figures" if sel else None
        return _family(sel[0]["func"]) if sel else None

    def _active_class(self) -> str | None:
        """plotSweep dataType class of the selection (slicap family only)."""
        for c in self._selected():
            cls = _SL_CLASS.get(c["func"])
            if cls:
                return cls
        return None

    @staticmethod
    def _repop(combo: QComboBox, items: list[str]):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.blockSignals(False)

    def _on_selection_changed(self, *_args):
        fam = self._active_family()
        cls = self._active_class()
        sel = self._selected()
        entry = sel[0] if sel else None
        is_ng, is_sl = fam == "ngspice", fam == "slicap"
        is_fig = self._mode == "figures"
        is_pz = fam == "pz"
        is_params = is_sl and cls == "params"
        sl_np = is_sl and not is_params      # slicap, dataType != 'params'
        is_ng_instr = entry is not None and entry["func"] in _NG_FUNCS
        # Trace type applies to COMPLEX data: ac results and fft spectra
        # (tran with fft=; ngspice_instr2traces applies trace_type to
        # complex arrays only — real data passes through untouched).
        is_ac = _ng_kind(entry) in ("ac", "fft")

        if is_fig:
            for c, cb in zip(self._results, self._checks):
                yk = self._ykeys.get(c["name"])
                if yk is not None:
                    yk.setVisible(cb.isChecked())
        else:
            # The plot type follows the result's family (rules table);
            # plotSweep sweeps frequency, time or a parameter — which one
            # follows from the dataType (Anton, 2026-07-11).
            sweep_kind = {"freq": "frequency sweep", "noise":
                          "frequency sweep", "time": "time sweep",
                          "params": "parameter sweep"}.get(cls, "sweep")
            self._ptype_lbl.setText(
                f"plotSweep  ({sweep_kind})" if is_sl else
                "plotPZ  (pole-zero map)" if is_pz else
                "plot  (traces)" if is_ng else "—")

        # ── page 1: type-specific core options ────────────────────────────
        for w in (self._ftype_lbl, self._ftype, self._sweep_lbl,
                  self._sw_start, self._sw_stop, self._sw_num):
            w.setVisible(is_sl)
        self._sweep_lbl.setText(
            {"freq":   "Frequency sweep start / stop / points:",
             "noise":  "Frequency sweep start / stop / points:",
             "time":   "Time sweep start / stop / points:",
             "params": "Sweep start / stop / points:"}.get(
                 cls, "Sweep start / stop / points:"))
        for w in (self._ttype_lbl, self._ttype):
            w.setVisible(is_ac)
        # trace selection: drop-down when the variable names are known
        # statically (names= dict), free text otherwise
        ng_names = _names_keys(entry) if is_ng_instr else []
        self._ng_traces_lbl.setVisible(is_ng_instr)
        self._ng_traces_combo.setVisible(is_ng_instr and bool(ng_names))
        self._ng_traces.setVisible(is_ng_instr and not ng_names)
        if ng_names != self._ng_names_shown:
            # also clears the model when the new result has no names, so
            # generation cannot read stale checks
            self._ng_traces_combo.set_names(ng_names)
            self._ng_names_shown = ng_names
        # goal functions apply to STEPPED NGspice results only
        self._goal_stepped = is_ng_instr and "step" in entry["kwargs"]
        for w in (self._goal_lbl, self._goal):
            w.setVisible(self._goal_stepped)
        self._on_goal_changed()
        # TRAN sweeps time linearly — the axis is always 'lin', nothing
        # to select (Anton, 2026-07-11). tran with fft= is a SPECTRUM:
        # the axis combo stays.
        is_tran = _ng_kind(entry) == "tran"
        for w in (self._axis_lbl, self._axis):
            w.setVisible((is_fig or (fam is not None and not is_pz))
                         and not is_tran)
        for w in (self._sweepvar_lbl, self._sweepvar, self._xvar_lbl,
                  self._xvar, self._yvar_lbl, self._yvar):
            w.setVisible(is_params)
        for w in (self._noise_lbl, self._noise):
            w.setVisible(is_sl and cls == "noise")
        # Rules table: axis-type and funcType combo contents follow the
        # family/class; repopulate only on a CHANGE so reselections keep the
        # user's pick ("auto" exists for plotSweep only — plot() takes the
        # axis type positionally and accepts no 'auto').
        # (figures mode keeps the init _AXIS_TYPES_NG list for its lifetime)
        if is_sl and fam != self._fam_shown:
            self._repop(self._axis, _AXIS_TYPES_SL)
        elif is_ng and fam != self._fam_shown:
            self._repop(self._axis, _AXIS_TYPES_NG)
        if fam is not None:
            self._fam_shown = fam
        if is_sl and cls != self._cls_shown:
            items = _CLASS_FUNC_TYPES[cls]
            self._repop(self._ftype, items)
            self._ftype.setEnabled(len(items) > 1)
        if cls is not None:
            self._cls_shown = cls

        # ── page 2: labels & scales relevant for the plot type ─────────────
        # sweepVar/xVar/yVar are page-1 content for 'params'; for the other
        # plotSweep classes the x axis derives from the sweep itself
        # (sweepScale is its scale factor) and only y scale/units can be
        # overridden. pz reuses the x/y scale fields as its axis scales.
        for w in (self._sweepscale_lbl, self._sweepscale):
            w.setVisible(is_sl)
        show_xy_names = is_ng or is_fig
        self._xname.setVisible(show_xy_names)
        self._xname_lbl.setVisible(show_xy_names or is_params)
        self._xname_lbl.setText("x name:" if show_xy_names
                                else "x scale / units:")
        self._xscale.setVisible(show_xy_names or is_params or is_pz)
        self._xunits.setVisible(show_xy_names or is_params)
        self._yname.setVisible(show_xy_names)
        self._yname_lbl.setVisible(show_xy_names or is_params or sl_np)
        self._yname_lbl.setText("y name:" if show_xy_names
                                else "y scale / units:")
        self._yunits.setVisible(not is_pz)
        self._xlim_lbl.setText("x min / max:" if is_pz else "x limits:")
        self._ylim_lbl.setText("y min / max:" if is_pz else "y limits:")
        self._cursors.setVisible(not is_pz)
        # Smart defaults from the selected result — but never during
        # prefill, which restores the values parsed from the existing call.
        if is_ng_instr and not self._prefilling:
            axis, ttype = _NG_DEFAULTS.get(_ng_kind(entry), ("lin", "real"))
            self._axis.setCurrentText(axis)
            if is_ac:
                self._ttype.setCurrentText(ttype)
        self._update()

    def _on_goal_changed(self, *_args) -> None:
        """Rebuild the parameter fields for the selected goal function —
        one labelled input per registry parameter, prefilled with its
        default (a factory may need several: goal_x_at_nth_y takes two)."""
        name = self._goal.currentText()
        params = _GOALS.get(name, (None, []))[1]
        if name != self._goal_shown:
            self._goal_shown = name
            lay = self._goal_par_box.layout()
            while lay.count():
                w = lay.takeAt(0).widget()
                if w is not None:
                    w.deleteLater()
            self._goal_pars = []
            for label, default in params:
                lay.addWidget(QLabel(f"{label}:"))
                edit = self._mini(70)
                edit.setText(str(default))
                lay.addWidget(edit)
                self._goal_pars.append((label, edit))
            lay.addStretch()
        self._goal_par_box.setVisible(
            getattr(self, "_goal_stepped", False) and bool(params))

    def _page1_ok(self) -> bool:
        if not self._selected():
            return False
        if self._active_family() == "slicap":
            if not all(w.text().strip() for w in
                       (self._sw_start, self._sw_stop, self._sw_num)):
                return False
            if self._active_class() == "params":
                # plotSweep errors without sweepVar and yVar for 'params'
                return bool(self._sweepvar.text().strip()) \
                    and bool(self._yvar.text().strip())
        return True

    def _update(self, *_args):
        ok = self._page1_ok()
        self._next_btn.setEnabled(ok)
        self._add_btn.setEnabled(ok and bool(self._name.text().strip()))

    # ── snippet generation ────────────────────────────────────────────────────

    def _kw_str(self, key: str, edit) -> str:
        v = edit.text().strip()
        return f', {key}="{v}"' if v else ""

    def _kw_num(self, key: str, edit) -> str:
        v = edit.text().strip()
        return f", {key}={v}" if v else ""

    def _kw_lim(self, key: str, lo, hi) -> str:
        vlo, vhi = lo.text().strip(), hi.text().strip()
        return f", {key}=[{vlo}, {vhi}]" if vlo and vhi else ""

    def _axes_kwargs(self, fam: str) -> str:
        if fam == "pz":
            return (self._kw_num("xmin", self._xlim_lo)
                    + self._kw_num("xmax", self._xlim_hi)
                    + self._kw_num("ymin", self._ylim_lo)
                    + self._kw_num("ymax", self._ylim_hi)
                    + self._kw_str("xscale", self._xscale)
                    + self._kw_str("yscale", self._yscale))
        out = ""
        cls = self._active_class()
        if fam == "slicap":
            if cls == "params":
                out += (self._kw_str("sweepVar", self._sweepvar)
                        + self._kw_str("sweepScale", self._sweepscale)
                        + self._kw_str("xVar", self._xvar))
                yv = [s.strip() for s in self._yvar.text().split(",")
                      if s.strip()]
                if len(yv) == 1:
                    out += f', yVar="{yv[0]}"'
                elif yv:
                    out += ", yVar=[" + ", ".join(f'"{v}"' for v in yv) + "]"
            else:
                out += self._kw_str("sweepScale", self._sweepscale)
            noise = self._noise.text().strip()
            if noise and cls == "noise":
                items = [n.strip() for n in noise.split(",") if n.strip()]
                out += (f', noiseSources="{items[0]}"' if len(items) == 1
                        else ", noiseSources=[" +
                             ", ".join(f'"{n}"' for n in items) + "]")
        else:
            out += (self._kw_str("xName", self._xname)
                    + self._kw_str("yName", self._yname))
        if not (fam == "slicap" and cls != "params"):
            # non-params plotSweep derives the x axis from the sweep:
            # xScale/xUnits would be silently ignored there
            out += (self._kw_str("xScale", self._xscale)
                    + self._kw_str("xUnits", self._xunits))
        out += (self._kw_str("yScale", self._yscale)
                + self._kw_str("yUnits", self._yunits)
                + self._kw_lim("xLim", self._xlim_lo, self._xlim_hi)
                + self._kw_lim("yLim", self._ylim_lo, self._ylim_hi))
        return out

    def _var_name(self) -> str:
        """Assignment target for the generated plot call — every plot call
        is assigned so its figure stays referenceable ("from other plots").
        An edited assigned plot keeps its variable; otherwise the plot name
        is sanitized to an identifier, FIG_-prefixed on collision."""
        if self._edit_entry is not None and self._edit_entry["assigned"]:
            return self._edit_entry["name"]
        var = re.sub(r"\W", "_", self._name.text().strip())
        if not var or var[0].isdigit():
            var = "FIG_" + var
        taken = self._taken - ({self._edit_entry["name"]}
                               if self._edit_entry is not None else set())
        while var in taken:
            var = "FIG_" + var
        return var

    def generated_snippet(self) -> str:
        sel = self._selected()
        if not sel:
            return ""
        fam   = self._active_family()
        var   = self._var_name()
        name  = self._name.text().strip()
        title = self._title.text().strip() or name
        show  = ", show=True" if self._show.isChecked() else ""
        save  = "" if self._save.isChecked() else ", save=False"
        curs  = ("" if self._cursors.isChecked() or fam == "pz"
                 else ", cursors=False")
        axes  = self._axes_kwargs(fam)

        if fam == "figures":
            conv = []
            for c in sel:
                yk_edit = self._ykeys.get(c["name"])
                yk_txt = yk_edit.text().strip() if yk_edit else ""
                keys = [k.strip() for k in yk_txt.split(",") if k.strip()]
                arg = (", [" + ", ".join(f'"{k}"' for k in keys) + "]"
                       if keys else "")
                conv.append(f'sl.fig2traces({c["name"]}{arg})')
            traces = conv[0] if len(conv) == 1 \
                else "{" + ", ".join(f"**{c}" for c in conv) + "}"
            return (f'{var} = sl.plot("{name}", "{title}", '
                    f'"{self._axis.currentText()}", {traces}'
                    f'{axes}{show}{save}{curs})')

        if fam == "ngspice":
            c = sel[0]
            if c["func"] in _NG_FUNCS:
                # trace_type for the complex-valued results: ac and fft
                tt = ""
                if _ng_kind(c) in ("ac", "fft"):
                    ttype = self._ttype.currentText()
                    tt = f", trace_type='{ttype}'" if ttype != "real" else ""
                if self._ng_traces_combo.names():   # drop-down active
                    keys = self._ng_traces_combo.checked()
                else:
                    yk_txt = self._ng_traces.text().strip()
                    keys = [k.strip() for k in yk_txt.split(",")
                            if k.strip()]
                yk = (", y_keys=[" + ", ".join(f'"{k}"' for k in keys) + "]"
                      if keys else "")
                # goal function (stepped results): registry-driven
                gf = ""
                if "step" in c["kwargs"]:
                    gname = self._goal.currentText()
                    if gname in _GOALS:
                        py, params = _GOALS[gname]
                        if not params:
                            gf = f", goal_fn=sl.{py}"
                        else:
                            vals = ", ".join(
                                edit.text().strip() or str(default)
                                for (_lbl, edit), (_l, default)
                                in zip(self._goal_pars, params))
                            gf = f", goal_fn=sl.{py}({vals})"
                traces = f"sl.ngspice_instr2traces({c['name']}{tt}{yk}{gf})"
            else:
                traces = c["name"]              # ready trace dict
            # TRAN sweeps time linearly — axis always 'lin' (a tran
            # with fft= is a spectrum and keeps the chosen axis)
            axis = "lin" if _ng_kind(c) == "tran" \
                else self._axis.currentText()
            return (f'{var} = sl.plot("{name}", "{title}", '
                    f'"{axis}", {traces}'
                    f'{axes}{show}{save}{curs})')

        result = sel[0]["name"]
        if fam == "pz":
            return (f'{var} = sl.plotPZ("{name}", "{title}", {result}'
                    f'{axes}{show}{save})')

        # "auto" is plotSweep's own default for both kwargs; anything else
        # (including an explicit "lin") is emitted. For dataType 'params'
        # the combo holds only "param", so it is always emitted — plotSweep
        # does not resolve 'auto' for that dataType.
        ftype = self._ftype.currentText()
        ft = f', funcType="{ftype}"' if ftype != "auto" else ""
        axis = self._axis.currentText()
        ax = f', axisType="{axis}"' if axis != "auto" else ""
        return (f'{var} = sl.plotSweep("{name}", "{title}", {result}, '
                f'{self._sw_start.text().strip()}, '
                f'{self._sw_stop.text().strip()}, '
                f'{self._sw_num.text().strip()}{ft}{ax}'
                f'{axes}{show}{save}{curs})')

    # ── append-only edit: prefill from a parsed plot call ─────────────────────

    def _prefill(self, entry: dict):
        args, kw = entry["args"], entry["kwargs"]

        def lit(src, default=None):
            try:
                return ast.literal_eval(src) if src is not None else default
            except (ValueError, SyntaxError):
                return default

        self._name.setText(str(lit(args[0], entry["name"])) if args
                           else entry["name"])
        self._title.setText(str(lit(args[1], "")) if len(args) > 1 else "")
        self._show.setChecked(bool(lit(kw.get("show"), False)))
        self._save.setChecked(bool(lit(kw.get("save"), True)))
        self._cursors.setChecked(bool(lit(kw.get("cursors"), True)))

        def _fill(edit, src, default=""):
            v = lit(src, default)
            edit.setText("" if v in (None, "") else str(v))

        def _fill_lim(lo_edit, hi_edit, src):
            v = lit(src)
            if isinstance(v, (list, tuple)) and len(v) == 2:
                lo_edit.setText(str(v[0]))
                hi_edit.setText(str(v[1]))

        if entry["func"] == "plotPZ":
            _fill(self._xlim_lo, kw.get("xmin"))
            _fill(self._xlim_hi, kw.get("xmax"))
            _fill(self._ylim_lo, kw.get("ymin"))
            _fill(self._ylim_hi, kw.get("ymax"))
            _fill(self._xscale, kw.get("xscale"))
            _fill(self._yscale, kw.get("yscale"))
        else:
            _fill(self._xname, kw.get("xName"))
            _fill(self._yname, kw.get("yName"))
            _fill(self._xvar, kw.get("xVar"))
            yv = lit(kw.get("yVar"))
            if isinstance(yv, (list, tuple)):     # yVar list ('params')
                self._yvar.setText(", ".join(str(v) for v in yv))
            else:
                self._yvar.setText("" if yv in (None, "") else str(yv))
            _fill(self._xscale, kw.get("xScale"))
            _fill(self._xunits, kw.get("xUnits"))
            _fill(self._yscale, kw.get("yScale"))
            _fill(self._yunits, kw.get("yUnits"))
            _fill_lim(self._xlim_lo, self._xlim_hi, kw.get("xLim"))
            _fill_lim(self._ylim_lo, self._ylim_hi, kw.get("yLim"))
            _fill(self._sweepvar, kw.get("sweepVar"))
            _fill(self._sweepscale, kw.get("sweepScale"))
            noise = lit(kw.get("noiseSources"))
            if isinstance(noise, str):
                self._noise.setText(noise)
            elif isinstance(noise, (list, tuple)):
                self._noise.setText(", ".join(str(n) for n in noise))

        # Combo values are applied AFTER the selection below: selecting the
        # result repopulates the axis/funcType combos for the parsed call's
        # family/class, which would wipe anything set now.
        pend_axis: str | None = None
        pend_ftype: str | None = None
        pend_ykeys: list[str] = []
        pend_goal: tuple[str, list[str]] | None = None
        wanted: set[str] = set()
        if entry["func"] == "plot":
            if len(args) > 2:
                pend_axis = lit(args[2])
            # plotData: collect sl.ngspice_instr2traces(NAME, trace_type=…)
            # (results mode) or sl.fig2traces(FIG, [labels]) (figures mode)
            if len(args) > 3 and args[3]:
                try:
                    tree = ast.parse(args[3], mode="eval")
                except SyntaxError:
                    tree = None
                trace_vars = {c["name"] for c in self._results
                              if c["func"] in _TRACE_FUNCS}
                for node in (ast.walk(tree) if tree else ()):
                    if (self._mode == "figures"
                            and isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "fig2traces"
                            and node.args
                            and isinstance(node.args[0], ast.Name)):
                        wanted.add(node.args[0].id)
                        if (len(node.args) > 1
                                and isinstance(node.args[1], ast.List)):
                            keys = [e.value for e in node.args[1].elts
                                    if isinstance(e, ast.Constant)]
                            yk = self._ykeys.get(node.args[0].id)
                            if yk is not None:
                                yk.setText(", ".join(map(str, keys)))
                    elif (isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "ngspice_instr2traces"
                            and node.args
                            and isinstance(node.args[0], ast.Name)):
                        wanted.add(node.args[0].id)
                        for k in node.keywords:
                            if (k.arg == "trace_type"
                                    and isinstance(k.value, ast.Constant)
                                    and k.value.value in _TRACE_TYPES):
                                self._ttype.setCurrentText(k.value.value)
                            if (k.arg == "y_keys"
                                    and isinstance(k.value, ast.List)):
                                pend_ykeys = [str(e.value)
                                              for e in k.value.elts
                                              if isinstance(e, ast.Constant)]
                            if k.arg == "goal_fn":
                                v = k.value
                                if (isinstance(v, ast.Call)
                                        and isinstance(v.func,
                                                       ast.Attribute)):
                                    pend_goal = (v.func.attr,
                                                 [ast.unparse(a)
                                                  for a in v.args])
                                elif isinstance(v, ast.Attribute):
                                    pend_goal = (v.attr, [])
                    elif (isinstance(node, ast.Name)
                            and node.id in trace_vars):
                        wanted.add(node.id)
        else:
            if len(args) > 2 and args[2]:
                try:
                    node = ast.parse(args[2], mode="eval").body
                except SyntaxError:
                    node = None
                if isinstance(node, ast.Name):
                    wanted.add(node.id)
                elif isinstance(node, ast.List):
                    # legacy multi-result call: prefill the first result
                    wanted |= {e.id for e in node.elts
                               if isinstance(e, ast.Name)}
            if entry["func"] == "plotSweep":
                for i, field in ((3, self._sw_start), (4, self._sw_stop),
                                 (5, self._sw_num)):
                    if len(args) > i:
                        # keep the source text verbatim (10e6 stays 10e6);
                        # only unquote actual string literals like "1n"
                        v = lit(args[i], args[i])
                        field.setText(v if isinstance(v, str) else args[i])
                pend_ftype = lit(kw.get("funcType"))
                pend_axis = lit(kw.get("axisType"))

        if self._mode == "figures":
            for c, cb in zip(self._results, self._checks):
                cb.setChecked(c["name"] in wanted)
        else:
            idx = next((i for i, c in enumerate(self._results)
                        if c["name"] in wanted), -1)
            self._result_combo.setCurrentIndex(idx)
        self._on_selection_changed()
        # y_keys land in the drop-down (populated just now by the selection)
        # or in the free-text field when the names are unknown statically.
        if pend_ykeys:
            if self._ng_traces_combo.names():
                self._ng_traces_combo.set_checked(pend_ykeys)
            else:
                self._ng_traces.setText(", ".join(pend_ykeys))
        if pend_goal is not None:
            py_name, par_srcs = pend_goal
            for name, (py, _params) in _GOALS.items():
                if py == py_name:
                    self._goal.setCurrentText(name)   # rebuilds the fields
                    for (_lbl, edit), src in zip(self._goal_pars,
                                                 par_srcs):
                        edit.setText(src)
                    break
        # setCurrentText is a no-op when the text is not among the items, so
        # a stale kwarg cannot select something the rules table forbids.
        if entry["func"] == "plotSweep":
            self._axis.setCurrentText(pend_axis or "auto")
            if pend_ftype:
                self._ftype.setCurrentText(pend_ftype)
            elif self._ftype.count():
                self._ftype.setCurrentIndex(0)
        elif entry["func"] == "plot" and pend_axis:
            self._axis.setCurrentText(pend_axis)
