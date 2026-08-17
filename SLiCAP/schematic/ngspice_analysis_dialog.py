"""Create/Edit NGspice instruction dialog — generates a Python sl.*() snippet.

Editing is append-only (SLNG.md): "Edit existing" lists THIS circuit's
instructions; the regenerated call keeps the name and is appended.

The active tab determines the analysis type.  Behavior and output-variable
selections apply to that single instruction.  The snippet is returned via
``generated_snippet()`` after the dialog is accepted.

Example output::

    AC1 = sl.ac("design", "dec", 50, 1, 10e6,
                names={"V_out": "v(out)"}, behavior="ps")
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QTabWidget, QWidget,
    QDialogButtonBox, QPushButton,
    QButtonGroup, QRadioButton, QScrollArea, QCheckBox, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from .param_table import ParamTable, PARAM_NAME_WIDTH
from .source_stimuli_table import SourceStimuliTable, _ANALYSIS_DOMAIN
from .step_widget import StepWidget
from .instr_file import next_result_name, parse_calls
from .value_fields import watch, all_valid


# ── helpers ───────────────────────────────────────────────────────────────────

def _field(label: str, placeholder: str = "", width: int = 120,
           kind: str = "number") -> tuple[QLabel, QLineEdit]:
    """A labelled field. *kind* 'number' is watched: the field is marked while
    its text is not a number in SLiCAP notation, and the dialog refuses to
    build an instruction from it (value_fields). Fields that hold a NAME - a
    source, a node - pass kind='name' and are not checked."""
    lbl  = QLabel(label)
    edit = QLineEdit()
    if placeholder:
        edit.setPlaceholderText(placeholder)
    edit.setMaximumWidth(width)
    if kind == "number":
        watch(edit, "number")
    return lbl, edit


_NGSPICE_FUNCS = {"op", "tran", "ac", "dc", "noise"}


def _q(text: str) -> str:
    """Python double-quoted string literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _lit(src, default=None):
    """Literal value of an argument's source text ('"1n"' → '1n', '50' → 50);
    unparseable source (an expression) returns *default*."""
    import ast as _ast
    if src is None:
        return default
    try:
        return _ast.literal_eval(src)
    except (ValueError, SyntaxError):
        return default


def _py_num(value: str) -> str:
    """Field text → Python literal for the generated sl.*() call.

    Plain numbers stay bare; a value with a scale factor (``1n``, ``10k``,
    ``10M``) is quoted, because unquoted it is a Python syntax error in the
    instruction file.

    The value keeps the SLiCAP notation the user typed: ONE notation for
    numbers (Anton, 2026-07-31), converted where it crosses into NGspice -
    the netlist and the control section - and nowhere earlier. The
    instruction file is SLiCAP's own, so '1n' stays '1n' there.
    """
    value = value.strip()
    try:
        float(value)
        return value
    except ValueError:
        return '"' + value.replace('"', "'") + '"'


# ── behavior selector ─────────────────────────────────────────────────────────

class _BehaviorSelector(QGroupBox):
    """Radio button row for the behavior= kwarg."""

    _MODES = ["none", "ps", "hs", "lt", "spec", "ng"]

    def __init__(self, parent=None):
        super().__init__("Behavior", parent)
        lay = QHBoxLayout(self)
        self._group = QButtonGroup(self)
        for i, mode in enumerate(self._MODES):
            rb = QRadioButton(mode.upper() if mode != "none" else "(none)")
            self._group.addButton(rb, i)
            lay.addWidget(rb)
            if mode == "none":
                rb.setChecked(True)
        lay.addStretch()

    def kwarg(self) -> str:
        idx = self._group.checkedId()
        mode = self._MODES[idx] if idx >= 0 else "none"
        return f', behavior="{mode}"' if mode != "none" else ""

    def set_mode(self, mode: str | None) -> None:
        mode = (mode or "none").lower()
        if mode not in self._MODES:
            mode = "none"
        self._group.button(self._MODES.index(mode)).setChecked(True)


# ── saved signals (save= kwarg) ──────────────────────────────────────────────

class _SaveWidget(QGroupBox):
    """The SIGNALS the simulator writes: ONE editable, comma-separated list.

    A signal is named numeric data coming out of the simulation - what NGspice
    calls a vector, and the word this GUI uses everywhere (TRACES.md section
    1). The analysis call speaks NGspice only; Python names for these signals
    are chosen afterwards, in the Traces dialog, so this widget has one column
    and no name field.

    Empty means the default set: node voltages, including subcircuit nodes,
    and voltage-source branch currents (NGspice manual 15.6.1). A non-empty
    list saves ONLY what it lists, so ``all`` must be listed alongside an
    internal parameter: ``all, @q1[gm]``.

    One line, not a stack of rows (Anton, 2026-08-01): a name is INSERTED from
    the select menu and REMOVED by deleting it from the text, and explanatory
    text sits above the field, never below the buttons.
    """

    def __init__(self, output_vars: list[str], parent=None):
        super().__init__("Signals to save", parent)
        self._output_vars = list(output_vars)

        hint = QLabel("Insert comma separated NGspice vectors.\n"
                      "Empty saves all node voltages and dependent currents.\n"
                      'For internal parameters, always add "all".')
        hint.setWordWrap(True)
        hint.setStyleSheet("color: grey; font-size: 9pt;")

        self._signals = QLineEdit()
        self._signals.setPlaceholderText(
            "e.g. v(out), i(v1), all, @q1[gm]")

        self._insert = QPushButton("Insert Signal")
        self._insert.setMenu(QMenu(self))

        self._currents = QCheckBox(
            "Device currents  (.options savecurrents; op, dc and tran only)")
        self._currents.setToolTip(
            "Terminal currents of R, C, L, M, J, Q, D, … including devices "
            "inside subcircuits. NGspice manual 15.7.3: not available for AC "
            "or noise, where the signals come back empty.")

        actions = QHBoxLayout()
        actions.addWidget(self._insert)
        actions.addWidget(self._currents)
        actions.addStretch(1)

        outer = QVBoxLayout(self)
        outer.addWidget(hint)              # text ABOVE the field it explains
        outer.addWidget(self._signals)
        outer.addLayout(actions)           # actions last

        self.set_output_vars(output_vars)

    # ── the select menu ───────────────────────────────────────────────────

    def set_output_vars(self, output_vars) -> None:
        """Offer another set of signals - a NOISE run has spectra where the
        others have node voltages."""
        self._output_vars = list(output_vars)
        menu = self._insert.menu()
        menu.clear()
        for name in self._output_vars:
            menu.addAction(name, lambda n=name: self._insert_signal(n))
        self._insert.setEnabled(bool(self._output_vars))

    def _insert_signal(self, name: str) -> None:
        """Append a signal to the list, unless it is already there."""
        current = self.signals()
        if name not in current:
            current.append(name)
        self._signals.setText(", ".join(current))

    def set_currents_enabled(self, enabled: bool) -> None:
        """AC and noise cannot deliver device currents (manual 15.7.3)."""
        self._currents.setEnabled(enabled)
        if not enabled:
            self._currents.setChecked(False)

    def set_from(self, save, savecurrents) -> None:
        """Prefill from an existing instruction."""
        self._signals.setText(", ".join(str(s) for s in (save or [])))
        self._currents.setChecked(bool(savecurrents))

    # ── emission ──────────────────────────────────────────────────────────

    def signals(self) -> list[str]:
        out = []
        for name in self._signals.text().split(","):
            name = name.strip()
            if name and name not in out:
                out.append(name)
        return out

    def kwarg(self) -> str:
        parts = ""
        signals = self.signals()
        if signals:
            parts += ", save=[" + ", ".join(_q(s) for s in signals) + "]"
        if self._currents.isChecked() and self._currents.isEnabled():
            parts += ", savecurrents=True"
        return parts


# ── base tab ──────────────────────────────────────────────────────────────────

class _AnalysisTab(QWidget):
    key   = ""
    label = ""

    def __init__(self, step_params=()):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._body = QWidget()
        outer.addWidget(self._body)
        self._step = StepWidget(step_params, key_style="ngspice")
        outer.addWidget(self._step)
        outer.addStretch()
        self._setup_fields(self._body)

    def _setup_fields(self, parent: QWidget) -> None:
        pass

    def _step_kwarg(self) -> str:
        d = self._step.dict_literal()
        return f", step={d}" if d else ""

    def snippet(self, cir_stem: str, varname: str, extra_kwargs: str = "") -> str:
        raise NotImplementedError

    def prefill(self, args: list, kwargs: dict) -> None:
        """Prefill the tab's own fields from a parsed call (append-only
        editing); the shared step/names/params/behavior widgets are filled
        by the dialog."""
        pass


# ── op ────────────────────────────────────────────────────────────────────────

class _OpTab(_AnalysisTab):
    key   = "op"
    label = "Operating Point"

    def _setup_fields(self, parent):
        lay = QVBoxLayout(parent)
        lay.addWidget(QLabel("No required parameters."))

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        step = self._step_kwarg()
        return f'{varname} = sl.op("{cir_stem}"{step}{extra_kwargs})'


# ── tran ──────────────────────────────────────────────────────────────────────

class _TranTab(_AnalysisTab):
    key   = "tran"
    label = "Transient"

    # NGspice specwindow values (fft post-processing)
    _WINDOWS = ["hanning", "rectangular", "bartlett", "blackman",
                "hamming", "gaussian", "flattop"]

    def _setup_fields(self, parent):
        grid = QGridLayout(parent)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl1, self._tstep  = _field("Time step",         "e.g. 1n")
        lbl2, self._tstop  = _field("Stop time",         "e.g. 1u")
        lbl3, self._tstart = _field("Start time (opt.)", "e.g. 0")
        for row, (lbl, edit) in enumerate(
            [(lbl1, self._tstep), (lbl2, self._tstop), (lbl3, self._tstart)]
        ):
            grid.addWidget(lbl,  row, 0, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(edit, row, 1)

        # Post-processing (build-order item 3, Anton 2026-07-12): FFT →
        # frequency-domain result (dataType 'fft'); Fourier → harmonics
        # table on instr.fourier next to the time-domain result. Both need
        # names= (enforced by sl.tran; the dialog's output-variables row
        # provides them).
        from PySide6.QtWidgets import QComboBox, QLabel, QSpinBox
        grid.addWidget(QLabel("Post-processing"), 3, 0,
                       Qt.AlignmentFlag.AlignRight)
        self._post = QComboBox()
        self._post.addItems(["None", "FFT (spectrum)", "Fourier (harmonics)"])
        self._post.currentIndexChanged.connect(self._on_post_changed)
        grid.addWidget(self._post, 3, 1)

        self._lbl_window = QLabel("FFT window")
        self._fft_window = QComboBox()
        self._fft_window.addItems(self._WINDOWS)
        self._fft_window.currentTextChanged.connect(
            lambda w: self._fft_order.setEnabled(w == "gaussian"))
        grid.addWidget(self._lbl_window, 4, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._fft_window, 4, 1)
        self._lbl_order = QLabel("Gaussian order")
        self._fft_order = QSpinBox()
        self._fft_order.setRange(2, 32)
        self._fft_order.setValue(8)
        self._fft_order.setEnabled(False)
        grid.addWidget(self._lbl_order, 5, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._fft_order, 5, 1)

        self._lbl_ffreq, self._four_freq = _field("Fundamental freq.",
                                                  "e.g. 100k")
        self._lbl_nfreq = QLabel("Harmonics")
        self._four_n = QSpinBox()
        self._four_n.setRange(2, 100)
        self._four_n.setValue(10)
        grid.addWidget(self._lbl_ffreq, 4, 2, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._four_freq, 4, 3)
        grid.addWidget(self._lbl_nfreq, 5, 2, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._four_n, 5, 3)
        self._on_post_changed()

    def _on_post_changed(self, *_):
        mode = self._post.currentIndex()          # 0 none, 1 fft, 2 fourier
        for w in (self._lbl_window, self._fft_window,
                  self._lbl_order, self._fft_order):
            w.setVisible(mode == 1)
        for w in (self._lbl_ffreq, self._four_freq,
                  self._lbl_nfreq, self._four_n):
            w.setVisible(mode == 2)

    def _post_kwarg(self) -> str:
        mode = self._post.currentIndex()
        if mode == 1:
            window = self._fft_window.currentText()
            if window == "gaussian":
                return (f', fft={{"window": "gaussian", '
                        f'"order": {self._fft_order.value()}}}')
            if window == "hanning":
                return ", fft=True"                # the default window
            return f', fft={{"window": "{window}"}}'
        if mode == 2:
            freq = self._four_freq.text().strip()
            if not freq:
                return ""
            n = self._four_n.value()
            if n != 10:
                return f', fourier={{"freq": "{freq}", "nfreqs": {n}}}'
            return f', fourier="{freq}"'
        return ""

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        tstep  = _py_num(self._tstep.text())
        tstop  = _py_num(self._tstop.text())
        tstart = self._tstart.text().strip()
        step   = self._step_kwarg()
        args   = f'"{cir_stem}", {tstep}, {tstop}'
        if tstart:
            args += f", tstart={_py_num(tstart)}"
        return (f'{varname} = sl.tran({args}{step}{extra_kwargs}'
                f'{self._post_kwarg()})')

    def prefill(self, args, kwargs):
        if len(args) > 1:
            self._tstep.setText(str(_lit(args[1], args[1])))
        if len(args) > 2:
            self._tstop.setText(str(_lit(args[2], args[2])))
        tstart = kwargs.get("tstart")
        self._tstart.setText("" if tstart is None else str(_lit(tstart, tstart)))
        fft = _lit(kwargs.get("fft"), None) if "fft" in kwargs else None
        fourier = (_lit(kwargs.get("fourier"), None)
                   if "fourier" in kwargs else None)
        if fft:
            self._post.setCurrentIndex(1)
            if isinstance(fft, dict):
                w = fft.get("window", "hanning")
                if w in self._WINDOWS:
                    self._fft_window.setCurrentText(w)
                if fft.get("order") is not None:
                    self._fft_order.setValue(int(fft["order"]))
        elif fourier is not None:
            self._post.setCurrentIndex(2)
            if isinstance(fourier, dict):
                self._four_freq.setText(str(fourier.get("freq", "")))
                self._four_n.setValue(int(fourier.get("nfreqs", 10)))
            else:
                self._four_freq.setText(str(fourier))
        else:
            self._post.setCurrentIndex(0)


# ── ac ────────────────────────────────────────────────────────────────────────

class _AcTab(_AnalysisTab):
    key   = "ac"
    label = "AC Analysis"

    def _setup_fields(self, parent):
        grid = QGridLayout(parent)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl0 = QLabel("Sweep type")
        self._sweep = QComboBox()
        self._sweep.addItems(["dec", "oct", "lin"])
        self._sweep.setMaximumWidth(80)
        lbl1, self._pts    = _field("Points/decade", "e.g. 50")
        lbl2, self._fstart = _field("F start",       "e.g. 1")
        lbl3, self._fstop  = _field("F stop",        "e.g. 10e6")
        grid.addWidget(lbl0,        0, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._sweep, 0, 1)
        for row, (lbl, edit) in enumerate(
            [(lbl1, self._pts), (lbl2, self._fstart), (lbl3, self._fstop)], start=1
        ):
            grid.addWidget(lbl,  row, 0, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(edit, row, 1)

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        step = self._step_kwarg()
        return (
            f'{varname} = sl.ac('
            f'"{cir_stem}", "{self._sweep.currentText()}", '
            f'{_py_num(self._pts.text())}, '
            f'{_py_num(self._fstart.text())}, '
            f'{_py_num(self._fstop.text())}'
            f'{step}{extra_kwargs})'
        )

    def prefill(self, args, kwargs):
        if len(args) > 1:
            self._sweep.setCurrentText(str(_lit(args[1], "dec")))
        for i, field in ((2, self._pts), (3, self._fstart), (4, self._fstop)):
            if len(args) > i:
                field.setText(str(_lit(args[i], args[i])))


# ── dc ────────────────────────────────────────────────────────────────────────

class _DcTab(_AnalysisTab):
    key   = "dc"
    label = "DC Sweep"

    def _setup_fields(self, parent):
        grid = QGridLayout(parent)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl0, self._src   = _field("Source",    "e.g. V1", kind="name")
        lbl1, self._start = _field("Start",     "e.g. 0")
        lbl2, self._stop  = _field("Stop",      "e.g. 5")
        lbl3, self._incr  = _field("Increment", "e.g. 0.1")
        for row, (lbl, edit) in enumerate(
            [(lbl0, self._src), (lbl1, self._start), (lbl2, self._stop), (lbl3, self._incr)]
        ):
            grid.addWidget(lbl,  row, 0, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(edit, row, 1)

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        step = self._step_kwarg()
        return (
            f'{varname} = sl.dc('
            f'"{cir_stem}", "{self._src.text().strip()}", '
            f'{_py_num(self._start.text())}, '
            f'{_py_num(self._stop.text())}, '
            f'{_py_num(self._incr.text())}'
            f'{step}{extra_kwargs})'
        )

    def prefill(self, args, kwargs):
        if len(args) > 1:
            self._src.setText(str(_lit(args[1], "")))
        for i, field in ((2, self._start), (3, self._stop), (4, self._incr)):
            if len(args) > i:
                field.setText(str(_lit(args[i], args[i])))


# ── dc TEMP ───────────────────────────────────────────────────────────────────

class _DcTempTab(_AnalysisTab):
    key   = "dc_temp"
    label = "Temperature Sweep"

    def _setup_fields(self, parent):
        grid = QGridLayout(parent)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl1, self._start = _field("T start (°C)", "e.g. -55")
        lbl2, self._stop  = _field("T stop (°C)",  "e.g. 125")
        lbl3, self._incr  = _field("Step (°C)",    "e.g. 5")
        for row, (lbl, edit) in enumerate(
            [(lbl1, self._start), (lbl2, self._stop), (lbl3, self._incr)]
        ):
            grid.addWidget(lbl,  row, 0, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(edit, row, 1)

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        step = self._step_kwarg()
        return (
            f'{varname} = sl.dc('
            f'"{cir_stem}", "TEMP", '
            f'{_py_num(self._start.text())}, '
            f'{_py_num(self._stop.text())}, '
            f'{_py_num(self._incr.text())}'
            f'{step}{extra_kwargs})'
        )

    def prefill(self, args, kwargs):
        for i, field in ((2, self._start), (3, self._stop), (4, self._incr)):
            if len(args) > i:
                field.setText(str(_lit(args[i], args[i])))


# ── noise ─────────────────────────────────────────────────────────────────────

class _NoiseTab(_AnalysisTab):
    key   = "noise"
    label = "Noise Analysis"

    def _setup_fields(self, parent):
        grid = QGridLayout(parent)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl0, self._out    = _field("Output node",   "e.g. v(out)", kind="name")
        lbl1, self._src    = _field("Input source",  "e.g. V1", kind="name")
        lbl2 = QLabel("Sweep type")
        self._sweep = QComboBox()
        self._sweep.addItems(["dec", "oct", "lin"])
        self._sweep.setMaximumWidth(80)
        lbl3, self._pts    = _field("Points/decade", "e.g. 50")
        lbl4, self._fstart = _field("F start",       "e.g. 1")
        lbl5, self._fstop  = _field("F stop",        "e.g. 10e6")
        grid.addWidget(lbl0,         0, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._out,    0, 1)
        grid.addWidget(lbl1,         1, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._src,    1, 1)
        grid.addWidget(lbl2,         2, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._sweep,  2, 1)
        grid.addWidget(lbl3,         3, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._pts,    3, 1)
        grid.addWidget(lbl4,         4, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._fstart, 4, 1)
        grid.addWidget(lbl5,         5, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self._fstop,  5, 1)
        # The noise BUDGET: one spectrum per noisy element, in the same
        # V^2/Hz as the total, so the dominant contributor is visible
        # (Anton, 2026-07-31). NGspice computes them only when the noise
        # command carries its summary-interval argument.
        self._contrib = QCheckBox("Noise contributions per source "
                                  "(onoise_<refdes>, …)")
        grid.addWidget(self._contrib, 6, 1)

    def snippet(self, cir_stem, varname, extra_kwargs=""):
        step = self._step_kwarg()
        contrib = ", contributions=True" if self._contrib.isChecked() else ""
        return (
            f'{varname} = sl.noise('
            f'"{cir_stem}", "{self._out.text().strip()}", '
            f'"{self._src.text().strip()}", '
            f'"{self._sweep.currentText()}", '
            f'{_py_num(self._pts.text())}, '
            f'{_py_num(self._fstart.text())}, '
            f'{_py_num(self._fstop.text())}'
            f'{contrib}{step}{extra_kwargs})'
        )

    def prefill(self, args, kwargs):
        if len(args) > 1:
            self._out.setText(str(_lit(args[1], "")))
        if len(args) > 2:
            self._src.setText(str(_lit(args[2], "")))
        if len(args) > 3:
            self._sweep.setCurrentText(str(_lit(args[3], "dec")))
        for i, field in ((4, self._pts), (5, self._fstart), (6, self._fstop)):
            if len(args) > i:
                field.setText(str(_lit(args[i], args[i])))
        self._contrib.setChecked(bool(_lit(kwargs.get("contributions"))))


# ── dialog ────────────────────────────────────────────────────────────────────

_TAB_CLASSES = [_OpTab, _TranTab, _AcTab, _DcTab, _DcTempTab, _NoiseTab]

_VARNAME_BASES = {
    "op":       "OP",
    "tran":     "TRAN",
    "ac":       "AC",
    "dc":       "DC",
    "dc_temp":  "DCTMP",
    "noise":    "NOISE",
}


class NGspiceAnalysisDialog(QDialog):
    """Add a single NGspice analysis instruction.

    The active tab picks the analysis type.  Call ``generated_snippet()``
    after ``exec()`` returns ``True``.

    :param cir_stem:    Circuit file stem (no extension), used in the snippet.
    :param output_vars: List of ``v(node)`` / ``i(Vxxx)`` strings for the
                        Select dropdown; pass ``[]`` if the netlist is not
                        available.
    """

    def __init__(self, cir_stem: str, output_vars: list[str] = (),
                 noise_vars: list[str] = (),
                 param_names: list[str] = (), existing_text: str = "",
                 sources: list[str] = (), parent=None):
        super().__init__(parent, Qt.Window)
        self._cir_stem = cir_stem
        self._existing_text = existing_text or ""
        self.setWindowTitle("Create / Edit NGspice Instruction")

        # The two-column body still lives in a QScrollArea: it keeps the
        # dialog's own layout free of heightForWidth (the word-wrapped hint
        # labels no longer feed back into the window width during an interactive
        # resize — the "jumpy width" bug), and on a short screen the content
        # scrolls instead of squishing.  With two columns the natural height is
        # roughly half the old single-column stack, so scrolling is rarely
        # needed and the source-stimulus editor is visible without hunting.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer.addWidget(scroll, 1)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        # ── load existing (append-only editing, SLNG.md) ──────────────────────
        # Only THIS schematic's instructions are editable here: the snippet
        # is regenerated with this dialog's cir_stem, so loading another
        # circuit's instruction would silently re-target it.
        self._defined = [c for c in parse_calls(self._existing_text)
                         if c["func"] in _NGSPICE_FUNCS and c["args"]
                         and _lit(c["args"][0]) == cir_stem]
        load_row = QHBoxLayout()
        load_row.addWidget(QLabel("Edit existing:"))
        self._load = QComboBox()
        self._load.addItem("(new instruction)")
        self._load.addItems([f'{c["name"]}  (sl.{c["func"]})'
                             for c in self._defined])
        self._load.currentIndexChanged.connect(self._on_load_existing)
        load_row.addWidget(self._load)
        load_row.addStretch()
        layout.addLayout(load_row)

        # ── variable name ─────────────────────────────────────────────────────
        var_row = QHBoxLayout()
        var_row.addWidget(QLabel("Variable name:"))
        self._varname = QLineEdit(next_result_name("OP", self._existing_text))
        self._varname.setMaximumWidth(120)
        self._varname.textChanged.connect(self._update)
        var_row.addWidget(self._varname)
        var_row.addStretch()
        layout.addLayout(var_row)

        # Two columns keep the dialog a normal, movable size: the analysis is
        # picked/parametrised on the LEFT (tabs), the per-instruction options
        # (behavior, outputs, params, source stimuli) sit on the RIGHT.  A
        # single column stacked these ~1350px tall, burying the stimulus editor
        # off-screen (Anton, 2026-07-16).
        columns = QHBoxLayout()
        left_panel, right_panel = QWidget(), QWidget()
        left  = QVBoxLayout(left_panel)
        right = QVBoxLayout(right_panel)
        left.setContentsMargins(0, 0, 0, 0)
        right.setContentsMargins(0, 0, 0, 0)
        columns.addWidget(left_panel, 1)
        columns.addWidget(right_panel, 1)
        layout.addLayout(columns)

        # ── analysis tabs (left) ──────────────────────────────────────────────
        self._tab_widget = QTabWidget()
        self._tabs: list[_AnalysisTab] = []
        for cls in _TAB_CLASSES:
            tab = cls(list(param_names))
            tab._step.changed.connect(self._update)
            if hasattr(tab, "_contrib"):        # noise: contributions switch
                tab._contrib.toggled.connect(self._update)
                tab._contrib.toggled.connect(self._refresh_output_vars)
            self._tabs.append(tab)
            self._tab_widget.addTab(tab, cls.label)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        left.addWidget(self._tab_widget)
        left.addStretch(1)

        # ── behavior (right) ──────────────────────────────────────────────────
        self._behavior = _BehaviorSelector()
        right.addWidget(self._behavior)

        # ── output variables (right) ──────────────────────────────────────────
        self._output_vars = list(output_vars)
        # what a NOISE run delivers instead of node voltages; the totals are
        # always there, the per-source ones only with contributions=True
        self._noise_vars = list(noise_vars)
        self._save = _SaveWidget(list(output_vars))
        right.addWidget(self._save)

        # ── per-instruction circuit parameters (params=, right) ───────────────
        self._params_table = ParamTable(
            "Circuit parameters (params=; unchecked = netlist definitions)",
            key_candidates=param_names,
            ordered=True, checkable=True,
            hint="Definitions are applied in order — each parameter must be "
                 "numerically evaluable when defined; NGspice errors on "
                 "undefined parameters. Existing netlist parameters are "
                 "overridden for this instruction only.")
        self._params_table.changed.connect(self._update)
        right.addWidget(self._params_table)

        # ── per-run source stimuli (stimuli=, right) ──────────────────────────
        # One stimulus per source, entered with the canvas SourceStimuliDialog
        # filtered to the analysis's domain (op/dc → DC, ac/noise → AC,
        # tran → TRAN).  The active tab sets the domain (Anton, 2026-07-16).
        start_key = _TAB_CLASSES[0].key if _TAB_CLASSES else "op"
        self._stimuli_table = SourceStimuliTable(
            list(sources), domain=_ANALYSIS_DOMAIN.get(start_key, "dc"))
        self._stimuli_table.changed.connect(self._update)
        right.addWidget(self._stimuli_table)
        right.addStretch(1)

        # ── buttons (fixed, outside the scroll area) ──────────────────────────
        buttons = QDialogButtonBox()
        self._add_btn = buttons.addButton(
            "Add instruction", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setContentsMargins(9, 6, 9, 9)
        outer.addWidget(buttons)

        self._refresh_output_vars()   # the tab the dialog OPENS on
        self._update()
        self._set_default_size(left_panel, right_panel)

    def _set_default_size(self, left_panel, right_panel) -> None:
        """Open wide enough to show every field in full, tabs excepted.

        A hard-coded 880 px cut into the right column: the saved-signals line,
        its hint and the parameter-table hint wrapped or clipped (Anton,
        2026-08-02). The width is therefore taken from the columns' own size
        hints, so a larger font or a longer label still fits, and is capped by
        the screen. The ANALYSIS TABS are deliberately not allowed to widen
        the window beyond that cap - a tab scrolls, a field must not.
        """
        m = self.layout().contentsMargins()
        spacing = 6 * 2 + 24            # column spacing + the scroll bar
        width = (left_panel.sizeHint().width() + right_panel.sizeHint().width()
                 + m.left() + m.right() + spacing)
        height = 700
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width  = min(width, int(available.width() * 0.95))
            height = min(height, int(available.height() * 0.9))
        self.resize(width, height)

    def _on_tab_changed(self, idx: int):
        key = _TAB_CLASSES[idx].key if idx < len(_TAB_CLASSES) else "op"
        base = _VARNAME_BASES.get(key, "RES")
        self._varname.setText(next_result_name(base, self._existing_text))
        self._stimuli_table.set_domain(_ANALYSIS_DOMAIN.get(key, "dc"))
        self._refresh_output_vars()
        self._update()

    def _refresh_output_vars(self, *_args) -> None:
        """Offer the signals the ACTIVE analysis produces: a noise run has
        ``onoise_spectrum`` / ``inoise_spectrum`` - and one spectrum per
        element when contributions are asked for - where the others have
        ``v(node)`` and ``i(Vxxx)``."""
        idx = self._tab_widget.currentIndex()
        tab = self._tabs[idx] if 0 <= idx < len(self._tabs) else None
        if tab is not None and tab.key == "noise":
            names = self._noise_vars or ["onoise_spectrum", "inoise_spectrum"]
            if not getattr(tab, "_contrib", None) or not tab._contrib.isChecked():
                names = [n for n in names if n.endswith("_spectrum")]
        else:
            names = self._output_vars
        self._save.set_output_vars(names)
        # device currents exist for op, dc and tran only (manual 15.7.3)
        self._save.set_currents_enabled(
            tab is not None and tab.key in ("op", "dc", "tran"))

    def _on_load_existing(self, idx: int):
        """Prefill from an existing instruction (append-only editing): the
        regenerated call keeps the name and is appended — the later
        definition wins at runtime; cleanup of the old line is the user's."""
        if idx <= 0:
            return
        entry = self._defined[idx - 1]
        key = entry["func"]
        if key == "dc" and len(entry["args"]) > 1 \
                and _lit(entry["args"][1]) == "TEMP":
            key = "dc_temp"
        tab_idx = next((i for i, cls in enumerate(_TAB_CLASSES)
                        if cls.key == key), 0)
        self._tab_widget.setCurrentIndex(tab_idx)   # resets varname; set below
        tab = self._tabs[tab_idx]
        tab.prefill(entry["args"], entry["kwargs"])
        kw = entry["kwargs"]
        tab._step.set_from_dict(_lit(kw.get("step")))
        self._save.set_from(_lit(kw.get("save")),
                             _lit(kw.get("savecurrents")))
        params = _lit(kw.get("params"))
        self._params_table.set_entries(params or [], active=bool(params))
        stimuli = _lit(kw.get("stimuli")) or {}
        self._stimuli_table.set_stimuli(stimuli, active=bool(stimuli))
        self._behavior.set_mode(_lit(kw.get("behavior")))
        self._varname.setText(entry["name"])
        # prefill may select the tab that was ALREADY current, so no
        # currentChanged signal fires and the drop-down would keep the
        # previous analysis's signals (Anton, 2026-08-01)
        self._refresh_output_vars()
        self._update()

    def _update(self, *_args):
        """Enable "Add instruction" only for a valid composition."""
        idx = self._tab_widget.currentIndex()
        tab = self._tabs[idx] if 0 <= idx < len(self._tabs) else None
        ok = bool(self._varname.text().strip())
        if tab is not None and not tab._step.is_valid():
            ok = False
        if tab is not None and not all_valid(tab):
            ok = False              # a marked field cannot become a netlist
        if not self._params_table.is_valid():
            ok = False
        if not self._stimuli_table.is_valid():
            ok = False
        self._add_btn.setEnabled(ok)

    def _params_kwarg(self) -> str:
        if not self._params_table.active():
            return ""
        lit = self._params_table.list_literal()
        return f", params={lit}" if lit else ""

    def _stimuli_kwarg(self) -> str:
        """Build ``, stimuli={"V1": ["SIN", "{A}", "1MEG"], …}`` from the
        stimuli table (one stimulus list per source)."""
        if not self._stimuli_table.active():
            return ""
        items = []
        for src, flat in self._stimuli_table.stimuli_dict().items():
            lst = "[" + ", ".join(_q(t) for t in flat) + "]"
            items.append(f"{_q(src)}: {lst}")
        return f", stimuli={{{', '.join(items)}}}" if items else ""

    def generated_snippet(self) -> str:
        """Return the sl.*() call for the active tab."""
        idx = self._tab_widget.currentIndex()
        if idx < 0 or idx >= len(self._tabs):
            return ""
        tab     = self._tabs[idx]
        varname = self._varname.text().strip() or "RES1"
        extra   = (self._save.kwarg() + self._params_kwarg()
                   + self._stimuli_kwarg() + self._behavior.kwarg())
        return tab.snippet(self._cir_stem, varname, extra)
