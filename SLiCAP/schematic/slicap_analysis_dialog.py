"""Create/Edit SLiCAP instruction dialog — a cascading form that emits a sl.do*() call.

Editing is append-only (SLNG.md): "Edit existing" lists the defined sl.do*()
instructions; the regenerated call keeps its result name and is appended.

Rebuilt from scratch per SLNG.md, "SLiCAP instruction dialog — rework spec
(v2)".  The ``_RULES`` table below is the single source of truth for which
fields apply to which analysis function; it mirrors ``SLiCAPshell.py``
(authoritative behaviour) and the manual's analysis chapter (authoritative
intent).  ``doParams`` is deliberately absent — it is a ``plotSweep`` helper,
not an analysis.

The dialog only composes and emits the readable shell call (kwargs equal to
the function's defaults are omitted); the shell remains the only place that
turns the call into an instruction.  Call ``generated_snippet()`` after
``exec()`` returns True.
"""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QCheckBox, QDialogButtonBox, QRadioButton,
    QButtonGroup,
)

from .param_table import ParamTable
from .step_widget import StepWidget
from .instr_file import next_result_name, parse_calls


# ─────────────────────────────────────────────────────────────────────────────
# Rules — the single source of truth (SLiCAPshell.py + manual, see SLNG.md)
# ─────────────────────────────────────────────────────────────────────────────

_TRANSFERS   = ["gain", "asymptotic", "direct", "loopgain", "servo"]
_T_WITH_NONE = _TRANSFERS + ["None"]

# Refs shown per transfer, for functions with refs policy "per-transfer".
_TRANSFER_REFS = {
    "None":       ("detector",),
    "gain":       ("source", "detector"),
    "asymptotic": ("source", "detector", "lgref"),
    "direct":     ("source", "detector", "lgref"),
    "loopgain":   ("lgref",),
    "servo":      ("lgref",),
}

# Function groups (adjusted 2026-07-09): doDC/doDCsolve are the s=0
# companions of doLaplace/doSolve, and doDCvar pairs with doNoise (same
# form: no transfer, detector required, source optional).
_GROUPS = [
    ("Network equations",   ["doMatrix"]),
    ("Laplace / DC",        ["doLaplace", "doDC", "doNumer", "doDenom",
                             "doSolve", "doDCsolve"]),
    ("Poles / zeros",       ["doPoles", "doZeros", "doPZ"]),
    ("Noise / DC variance", ["doNoise", "doDCvar"]),
    ("Time",                ["doTime", "doImpulse", "doStep", "doTimeSolve"]),
]

# transfers: offered options, first entry = shell default; None = no transfer
#            step ("None" in the list is the literal transfer=None choice).
# refs:      "per-transfer"  — from _TRANSFER_REFS
#            "lgref-only"    — per-transfer minus source/detector (doDenom,
#                              doPoles: denominator-only; the shell drops the
#                              refs for doPoles)
#            "detector-only" — doTime (shell forces transfer=None, source=None)
#            "noise"         — detector required + source optional (doNoise /
#                              doDCvar; lgref is forced None by the shell)
#            "none"          — no refs at all
# convtype:  "full" (doMatrix only, manual) or "dm-cm" (None/dd/cc)
# base:      result-variable prefix (auto-incremented per instruction file)
_RULES = {
    "doMatrix":    dict(transfers=None,         refs="none",          convtype="full",  base="MATRIX"),
    "doLaplace":   dict(transfers=_T_WITH_NONE, refs="per-transfer",  convtype="dm-cm", base="LAPLACE"),
    "doNumer":     dict(transfers=_T_WITH_NONE, refs="per-transfer",  convtype="dm-cm", base="NUMER"),
    "doDenom":     dict(transfers=_T_WITH_NONE, refs="lgref-only",    convtype="dm-cm", base="DENOM"),
    "doSolve":     dict(transfers=None,         refs="none",          convtype="dm-cm", base="SOLVE"),
    "doPoles":     dict(transfers=_TRANSFERS,   refs="lgref-only",    convtype="dm-cm", base="POLES"),
    "doZeros":     dict(transfers=_TRANSFERS,   refs="per-transfer",  convtype="dm-cm", base="ZEROS"),
    "doPZ":        dict(transfers=_TRANSFERS,   refs="per-transfer",  convtype="dm-cm", base="PZ"),
    "doNoise":     dict(transfers=None,         refs="noise",         convtype="dm-cm", base="NOISE"),
    "doTime":      dict(transfers=None,         refs="detector-only", convtype="dm-cm", base="TIME"),
    "doImpulse":   dict(transfers=_TRANSFERS,   refs="per-transfer",  convtype="dm-cm", base="IMPULSE"),
    "doStep":      dict(transfers=_TRANSFERS,   refs="per-transfer",  convtype="dm-cm", base="STEP"),
    "doTimeSolve": dict(transfers=None,         refs="none",          convtype="dm-cm", base="TIMESOLVE"),
    "doDC":        dict(transfers=_T_WITH_NONE, refs="per-transfer",  convtype="dm-cm", base="DC"),
    "doDCsolve":   dict(transfers=None,         refs="none",          convtype="dm-cm", base="DCSOLVE"),
    "doDCvar":     dict(transfers=None,         refs="noise",         convtype="dm-cm", base="DCVAR"),
}

_CONVTYPES = {
    "full":  ["None", "all", "dd", "cc", "dc", "cd"],
    "dm-cm": ["None", "dd", "cc"],
}


def _shown_refs(func: str, transfer: str | None) -> tuple[str, ...]:
    """Refs (source/detector/lgref) shown for *func* at *transfer*."""
    policy = _RULES[func]["refs"]
    if policy == "none":
        return ()
    if policy == "detector-only":
        return ("detector",)
    if policy == "noise":
        return ("source", "detector")
    per = _TRANSFER_REFS.get(transfer or "None", ())
    if policy == "lgref-only":
        return tuple(r for r in per if r == "lgref")
    return per


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class SLiCAPAnalysisDialog(QDialog):
    """Compose a single SLiCAP analysis instruction (cascading form).

    :param cir_var:          Python variable holding the circuit object.
    :param sources:          Independent source refdes strings (``cir.indepVars``).
    :param detectors:        Valid detector names (``cir.depVars()``).
    :param lgrefs:           Controlled-source refdes strings (``cir.controlled``).
    :param par_defs:         ``{name: value}`` strings of the circuit's defined
                             parameters (``cir.parDefs``) — pre-fills the
                             pardefs table's "Load circuit definitions".
    :param undefined_params: Names of undefined parameters (``cir.params``).
    :param existing_text:    Instruction-file content, used to auto-increment
                             the result-variable name.
    """

    def __init__(self, cir_var: str = "cir", sources=(), detectors=(),
                 lgrefs=(), par_defs: dict | None = None,
                 undefined_params=(), existing_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create / Edit SLiCAP Instruction")
        self.setMinimumWidth(560)

        self._existing = existing_text or ""
        par_defs = {str(k): str(v) for k, v in (par_defs or {}).items()}
        param_names = list(par_defs.keys()) + [
            str(p) for p in undefined_params if str(p) not in par_defs]

        layout = QVBoxLayout(self)

        # ── help link ─────────────────────────────────────────────────────────
        help_lbl = QLabel(
            'Composes a <code>sl.do…()</code> analysis call — '
            '<a href="https://www.slicap.org/userguide/analysis'
            '#general-instruction-format">help: general instruction format</a>')
        help_lbl.setOpenExternalLinks(True)
        layout.addWidget(help_lbl)

        # ── load existing (append-only editing, SLNG.md) ──────────────────────
        self._defined = [c for c in parse_calls(self._existing)
                         if c["func"] in _RULES]
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

        # ── 1. instruction type + variables (aligned grid) ────────────────────
        top = QGridLayout()
        top.addWidget(QLabel("Analysis group:"), 0, 0,
                      Qt.AlignmentFlag.AlignRight)
        self._group = QComboBox()
        self._group.addItems([g for g, _ in _GROUPS])
        top.addWidget(self._group, 0, 1)
        top.addWidget(QLabel("Instruction:"), 0, 2,
                      Qt.AlignmentFlag.AlignRight)
        self._func = QComboBox()
        self._func.setMinimumWidth(130)
        top.addWidget(self._func, 0, 3)

        cir_lbl = QLabel("Circuit variable:")
        cir_lbl.setToolTip(
            "Python variable that holds the circuit object — the instruction "
            'file contains  cir = sl.makeCircuit("<schematic>").')
        top.addWidget(cir_lbl, 1, 0, Qt.AlignmentFlag.AlignRight)
        self._cir_var = QLineEdit(cir_var)
        self._cir_var.setMaximumWidth(120)
        self._cir_var.setToolTip(cir_lbl.toolTip())
        top.addWidget(self._cir_var, 1, 1)
        top.addWidget(QLabel("Result variable:"), 1, 2,
                      Qt.AlignmentFlag.AlignRight)
        self._result_var = QLineEdit()
        self._result_var.setMaximumWidth(130)
        self._result_var.textChanged.connect(self._update)
        top.addWidget(self._result_var, 1, 3)
        self._name_warn = QLabel("")
        self._name_warn.setStyleSheet("color: #b36b00; font-size: 9pt;")
        top.addWidget(self._name_warn, 1, 4)

        # ── 2. transfer ───────────────────────────────────────────────────────
        self._transfer_lbl = QLabel("Transfer:")
        top.addWidget(self._transfer_lbl, 2, 0, Qt.AlignmentFlag.AlignRight)
        self._transfer = QComboBox()
        self._transfer.currentTextChanged.connect(self._on_transfer_changed)
        top.addWidget(self._transfer, 2, 1)
        top.setColumnStretch(4, 1)
        layout.addLayout(top)

        # ── 3. signal references ──────────────────────────────────────────────
        self._refs_box = QGroupBox("Signal references")
        grid = QGridLayout(self._refs_box)
        self._refs = {}
        for r, (key, items) in enumerate((("source", list(sources)),
                                          ("detector", list(detectors)),
                                          ("lgref", list(lgrefs)))):
            lbl = QLabel(key)
            c1 = QComboBox()
            c1.setEditable(True)
            c1.setMinimumWidth(140)
            c1.currentTextChanged.connect(self._update)
            pair_lbl = QLabel("2nd (differential):")
            c2 = QComboBox()
            c2.setEditable(True)
            c2.setMinimumWidth(140)
            c2.currentTextChanged.connect(self._update)
            grid.addWidget(lbl, r, 0, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(c1, r, 1)
            grid.addWidget(pair_lbl, r, 2, Qt.AlignmentFlag.AlignRight)
            grid.addWidget(c2, r, 3)
            self._refs[key] = dict(lbl=lbl, c1=c1, c2=c2, pair=pair_lbl,
                                   items=[str(i) for i in items])
        layout.addWidget(self._refs_box)

        # ── 4. pardefs ────────────────────────────────────────────────────────
        pd_box = QGroupBox("Parameter substitution (pardefs)")
        pv = QVBoxLayout(pd_box)
        prow = QHBoxLayout()
        self._pd_group = QButtonGroup(self)
        for i, text in enumerate(("None", "'circuit'", "Custom dict")):
            rb = QRadioButton(text)
            self._pd_group.addButton(rb, i)
            prow.addWidget(rb)
            if i == 0:
                rb.setChecked(True)
        prow.addStretch(1)
        pv.addLayout(prow)
        self._pd_table = ParamTable(
            "Custom definitions", key_candidates=param_names,
            load_values=par_defs,
            hint="These definitions replace the circuit definitions — "
                 "parameters not listed stay symbolic.")
        self._pd_table.setVisible(False)
        self._pd_table.changed.connect(self._update)
        pv.addWidget(self._pd_table)
        self._pd_group.idClicked.connect(self._on_pardefs_mode)
        layout.addWidget(pd_box)

        # ── 5./6. numeric + convtype ──────────────────────────────────────────
        orow = QHBoxLayout()
        self._numeric = QCheckBox("numeric")
        self._numeric.setToolTip(
            "Numeric evaluation (floats). Forced on while stepping — "
            "symbolic stepping is not implemented.")
        orow.addWidget(self._numeric)
        orow.addSpacing(20)
        orow.addWidget(QLabel("convtype:"))
        self._convtype = QComboBox()
        orow.addWidget(self._convtype)
        orow.addStretch(1)
        layout.addLayout(orow)

        # ── 7. stepping ───────────────────────────────────────────────────────
        self._step = StepWidget(param_names, key_style="slicap")
        self._step.changed.connect(self._update)
        layout.addWidget(self._step)

        # extra vertical space goes here, not into the group boxes
        layout.addStretch(1)

        # ── buttons ───────────────────────────────────────────────────────────
        buttons = QDialogButtonBox()
        self._add_btn = buttons.addButton(
            "Add instruction", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # ── wiring ────────────────────────────────────────────────────────────
        self._group.currentIndexChanged.connect(self._on_group_changed)
        self._func.currentTextChanged.connect(self._on_func_changed)
        self._group.setCurrentIndex(1)      # default: Laplace / DC → doLaplace
        self._on_group_changed(self._group.currentIndex())

    # ── cascade handlers ──────────────────────────────────────────────────────

    def _on_group_changed(self, idx: int) -> None:
        funcs = _GROUPS[idx][1]
        self._func.blockSignals(True)
        self._func.clear()
        self._func.addItems(funcs)
        self._func.blockSignals(False)
        self._on_func_changed(self._func.currentText())

    def _on_func_changed(self, func: str) -> None:
        if func not in _RULES:
            return
        rules = _RULES[func]

        # transfer options
        self._transfer.blockSignals(True)
        self._transfer.clear()
        if rules["transfers"]:
            self._transfer.addItems(rules["transfers"])
        self._transfer.blockSignals(False)

        # ref candidate lists ('(none)' only where source is optional)
        for key, w in self._refs.items():
            optional = key == "source" and rules["refs"] == "noise"
            first = ["circuit"] + (["(none)"] if optional else [])
            w["c1"].blockSignals(True)
            w["c1"].clear()
            w["c1"].addItems(first + w["items"])
            w["c1"].setCurrentText("circuit")
            w["c1"].blockSignals(False)
            w["c2"].blockSignals(True)
            w["c2"].clear()
            w["c2"].addItems(["(none)"] + w["items"])
            w["c2"].setCurrentText("(none)")
            w["c2"].blockSignals(False)

        # convtype options
        self._convtype.blockSignals(True)
        self._convtype.clear()
        self._convtype.addItems(_CONVTYPES[rules["convtype"]])
        self._convtype.blockSignals(False)

        # result-variable default
        self._result_var.setText(next_result_name(rules["base"], self._existing))

        self._refresh_visibility()

    def _on_transfer_changed(self, _text: str) -> None:
        self._refresh_visibility()

    def _on_load_existing(self, idx: int) -> None:
        """Prefill from an existing instruction (append-only editing): the
        regenerated call keeps its result name and is appended — the later
        definition wins at runtime; cleanup of the old line is the user's."""
        if idx <= 0:
            return
        import ast as _ast

        def lit(src, default=None):
            try:
                return _ast.literal_eval(src) if src is not None else default
            except (ValueError, SyntaxError):
                return default

        entry = self._defined[idx - 1]
        func = entry["func"]
        for g_idx, (_label, funcs) in enumerate(_GROUPS):
            if func in funcs:
                self._group.setCurrentIndex(g_idx)
                break
        self._func.setCurrentText(func)
        if entry["args"]:
            self._cir_var.setText(entry["args"][0])
        kw = entry["kwargs"]
        transfer = lit(kw.get("transfer"), "__absent__")
        if transfer is None:
            self._transfer.setCurrentText("None")
        elif isinstance(transfer, str) and transfer != "__absent__":
            self._transfer.setCurrentText(transfer)
        for key in ("source", "detector", "lgref"):
            val = lit(kw.get(key))
            if val is None:
                continue
            pair = val if isinstance(val, list) else [val]
            self._refs[key]["c1"].setCurrentText(str(pair[0]))
            if len(pair) > 1:
                self._refs[key]["c2"].setCurrentText(str(pair[1]))
        convtype = lit(kw.get("convtype"))
        if convtype is not None:
            self._convtype.setCurrentText(str(convtype))
        pardefs = lit(kw.get("pardefs"), "__absent__")
        if pardefs == "circuit":
            mode = 1
        elif isinstance(pardefs, dict):
            mode = 2
            self._pd_table.set_entries(pardefs)
        else:
            mode = 0
        self._pd_group.button(mode).setChecked(True)
        self._on_pardefs_mode(mode)
        self._numeric.setChecked(bool(lit(kw.get("numeric"), False)))
        self._step.set_from_dict(lit(kw.get("stepdict")))
        self._result_var.setText(entry["name"])
        self._update()

    def _on_pardefs_mode(self, idx: int) -> None:
        self._pd_table.setVisible(idx == 2)
        self._update()

    def _current_transfer(self) -> str | None:
        rules = _RULES[self._func.currentText()]
        return self._transfer.currentText() if rules["transfers"] else None

    def _refresh_visibility(self) -> None:
        func = self._func.currentText()
        if func not in _RULES:
            return
        rules = _RULES[func]
        has_transfer = bool(rules["transfers"])
        self._transfer_lbl.setVisible(has_transfer)
        self._transfer.setVisible(has_transfer)

        shown = _shown_refs(func, self._current_transfer())
        for key, w in self._refs.items():
            vis = key in shown
            for part in ("lbl", "c1", "pair", "c2"):
                w[part].setVisible(vis)
        self._refs_box.setVisible(bool(shown))
        self._update()

    # ── validation ────────────────────────────────────────────────────────────

    def _update(self, *_args) -> None:
        # differential partner only meaningful for an explicit first reference
        for w in self._refs.values():
            v1 = w["c1"].currentText().strip()
            w["c2"].setEnabled(v1 not in ("circuit", "(none)", ""))

        # stepping requires numeric results (symbolic stepping is not
        # implemented — SLiCAPinstruction._checkStep)
        stepping = self._step.isChecked()
        if stepping and not self._numeric.isChecked():
            self._numeric.setChecked(True)
        self._numeric.setEnabled(not stepping)

        ok = True
        name = self._result_var.text().strip()
        if not name:
            ok = False
        warn = ""
        if name and re.search(r"\b" + re.escape(name) + r"\s*=", self._existing):
            warn = "name already used — it will shadow the earlier result"
        self._name_warn.setText(warn)

        if self._pd_group.checkedId() == 2 and not self._pd_table.is_valid():
            ok = False
        if not self._step.is_valid():
            ok = False
        self._add_btn.setEnabled(ok)

    # ── emission ──────────────────────────────────────────────────────────────

    def _ref_kwarg(self, key: str) -> str | None:
        w = self._refs[key]
        v1 = w["c1"].currentText().strip()
        v2 = w["c2"].currentText().strip() if w["c2"].isEnabled() else ""
        if not v1 or v1 == "circuit":
            return None                          # shell default — omit
        if v1 == "(none)":
            return f"{key}=None"
        if v2 and v2 != "(none)":
            return f"{key}=['{v1}', '{v2}']"
        return f"{key}='{v1}'"

    def generated_snippet(self) -> str:
        """The composed ``<RESULT> = sl.<func>(<cir>, …)`` line."""
        func = self._func.currentText()
        rules = _RULES[func]
        cirv = self._cir_var.text().strip() or "cir"
        res = (self._result_var.text().strip()
               or next_result_name(rules["base"], self._existing))

        parts: list[str] = []
        shown = _shown_refs(func, self._current_transfer())
        for key in ("source", "detector", "lgref"):     # signature order
            if key in shown:
                kw = self._ref_kwarg(key)
                if kw:
                    parts.append(kw)
        if rules["transfers"]:
            t = self._transfer.currentText()
            if t != rules["transfers"][0]:              # first = shell default
                parts.append("transfer=None" if t == "None"
                             else f"transfer='{t}'")
        ct = self._convtype.currentText()
        if ct and ct != "None":
            parts.append(f"convtype='{ct}'")
        pd_mode = self._pd_group.checkedId()
        if pd_mode == 1:
            parts.append("pardefs='circuit'")
        elif pd_mode == 2:
            lit = self._pd_table.dict_literal()
            if lit:
                parts.append(f"pardefs={lit}")
        if self._numeric.isChecked():
            parts.append("numeric=True")
        step_lit = self._step.dict_literal()
        if step_lit:
            parts.append(f"stepdict={step_lit}")

        return f"{res} = sl.{func}({', '.join([cirv] + parts)})"
