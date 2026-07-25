"""Formatter-agnostic "Create snippet" dialog (SLNG.md, 2026-07-16).

One dialog, one emission engine, parameterised by a :class:`SnippetTarget`
descriptor per output format. A target names only its formatter object
(``ltx``/``rst``), its constructor, and — for the formatter-method kinds
(from-a-file, from-an-object) — **nothing about the arguments**: the fields to
show and the call to emit are derived from the real formatter method
signatures via :mod:`inspect`.

Because RST, LaTeX and future MyST/HTML/plain-text formatters expose different
functionality, an argument one accepts may be absent in another (LaTeX
``file(language=)`` vs RST ``file(firstNumber=)``; RST ``expr(name=)`` vs LaTeX
``expr()``). Reading the signatures means those differences need no per-format
tables here — adding a formatter is adding a target, nothing else.

Two workflows that are more than a single formatter call stay bespoke: text
output (a TXT-formatter line + an include line) and a specification table
(``csv2specs`` load + ``specs`` call).

The dialog only EMITS readable formatter calls (two-translators rule); editing
is append-only, so the snippet self-carries idempotent ``<var> = sl.<Fmt>()`` /
``txt = sl.TXTformatter()`` init lines when the file lacks them. Result
variables come from the instruction-file inventory (``instr_file.parse_calls``).
"""
import inspect

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QCheckBox, QDialogButtonBox, QPlainTextEdit, QPushButton, QFileDialog,
    QHBoxLayout, QWidget,
)

from . import instr_file

# ── result-variable classification by producing function ────────────────────
_PZ_FUNCS      = {"doPoles", "doZeros", "doPZ"}
_LAPLACE_FUNCS = {"doLaplace", "doNumer", "doDenom", "doDC"}
_NOISE_FUNCS   = {"doNoise"}
_DCVAR_FUNCS   = {"doDCvar"}
_MATRIX_FUNCS  = {"doMatrix"}

KIND_TEXT, KIND_FILE, KIND_OBJECT, KIND_SPECS = range(4)

# text-output sources (kind 1): (label, TXT-formatter method, result filter).
# Always emitted as txt.<method>() — the TXT formatter is format-independent.
_TEXT_SOURCES = [
    ("Pole-zero listing (listPZ)", "pz",             _PZ_FUNCS),
    ("Servo bandwidth",            "servoBandwidth", _LAPLACE_FUNCS),
    ("Phase margin",               "phaseMargin",    _LAPLACE_FUNCS),
    ("Free text",                  "text",           None),
]

# Formatter methods offered, per UI kind: (method, label, result filter).
# WHICH methods appear and how their result variable is filtered is domain
# knowledge (not in the signature); the ARGUMENTS of each are read from the
# signature. A method absent on a given formatter is dropped automatically.
_FILE_METHODS = [
    ("file",    "file — include any text file", None),
    ("netlist", "netlist — include a netlist",  None),
]
_OBJECT_METHODS = [
    ("eqn",           "eqn — displayed equation",              None),
    ("eqnInline",     "eqnInline — inline equation",           None),
    ("expr",          "expr — inline expression",              None),
    ("pz",            "pz — pole-zero table",                  _PZ_FUNCS),
    ("coeffsTransfer", "coeffsTransfer — coefficient table",   _LAPLACE_FUNCS),
    ("matrixEqn",     "matrixEqn — matrix equation",           _MATRIX_FUNCS),
    ("elementData",   "elementData — expanded netlist table",  None),
    ("parDefs",       "parDefs — parameter definitions table", None),
    ("params",        "params — undefined parameters table",   None),
    ("noiseContribs", "noiseContribs — noise contributions",   _NOISE_FUNCS),
    ("dcvarContribs", "dcvarContribs — dcvar contributions",   _DCVAR_FUNCS),
]

# Signature parameter → the input widget that supplies it. Parameters not
# listed either need no widget (``circuitObject`` → ``cir``; ``name`` → the
# always-present snippet-name field) or are left to their default (LaTeX
# ``color``/``style``). A REQUIRED parameter must be renderable (see
# _param_fragment); every method above satisfies that for both formatters.
_PARAM_WIDGET = {
    "resultObject": "result", "transferCoeffs": "result",
    "Iv": "result", "M": "result", "Dv": "result",
    "LHS": "lhs", "RHS": "expr", "expr": "expr",
    "fileName": "path", "netlistFile": "path",
    "units": "units", "label": "label", "caption": "caption",
    "lineRange": "linerange", "firstNumber": "firstnumber",
    "language": "language", "multiline": "multiline",
}


class SnippetTarget:
    """One output format: its formatter object, constructor, and formatter
    class (introspected for method arguments).

    :param name:        human name in the title ("LaTeX", "RST (Sphinx)").
    :param var:         formatter variable emitted in the snippet ("ltx"/"rst").
    :param ctor:        formatter constructor call ("sl.LaTeXformatter()").
    :param ctor_marker: substring proving the init line already exists.
    :param formatter:   ``(module, class_name)`` imported lazily for signatures.
    :param append_file: save stem for methods with a ``name=`` substitution
                        parameter (RST expr/eqnInline append to one file).
    """

    def __init__(self, *, name, var, ctor, ctor_marker, formatter,
                 append_file="substitutions"):
        self.name = name
        self.var = var
        self.ctor = ctor
        self.ctor_marker = ctor_marker
        self.formatter = formatter
        self.append_file = append_file

    def formatter_class(self):
        import importlib
        module, cls = self.formatter
        return getattr(importlib.import_module(module), cls)


LATEX_TARGET = SnippetTarget(
    name="LaTeX", var="ltx", ctor="sl.LaTeXformatter()",
    ctor_marker="LaTeXformatter()",
    formatter=("SLiCAP.SLiCAPlatex", "LaTeXformatter"))

RST_TARGET = SnippetTarget(
    name="RST (Sphinx)", var="rst", ctor="sl.RSTformatter()",
    ctor_marker="RSTformatter()",
    formatter=("SLiCAP.SLiCAPrst", "RSTformatter"))


def _q(text: str) -> str:
    """Python double-quoted string literal."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _ident(text: str, fallback: str = "specs") -> str:
    """A valid Python identifier from arbitrary text (spec-file stem →
    variable-name fragment)."""
    import re
    stem = re.sub(r"\W", "_", text.strip()).strip("_") or fallback
    if stem[0].isdigit():
        stem = "_" + stem
    return stem


# Snippets are ASSIGNED so they appear as named objects in the Design data
# panel via the run manifest. The variable name IS the user's snippet name;
# the name field therefore requires a valid Python identifier.


class SnippetDialog(QDialog):
    """Input hierarchy: kind → method/source → fields → name. All output-format
    and argument specifics come from *target* and the formatter signatures."""

    def __init__(self, target: SnippetTarget, instr_text: str = "",
                 csv_dir: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self._target = target
        # Lazy: importing the formatter class pulls the (heavier) core module,
        # paid once when the snippet dialog is first opened.
        self._fmt_cls = target.formatter_class()
        self._sig_cache: dict = {}
        self.setWindowTitle(f"Create {target.name} snippet")
        self._instr_text = instr_text
        self._csv_dir = csv_dir
        self._calls = [c for c in instr_file.parse_calls(instr_text)
                       if c["assigned"]]

        # Methods this formatter actually implements (a format missing one just
        # doesn't offer it).
        self._file_methods = [m for m in _FILE_METHODS
                              if hasattr(self._fmt_cls, m[0])]
        self._object_methods = [m for m in _OBJECT_METHODS
                                if hasattr(self._fmt_cls, m[0])]

        outer = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)
        row = 0

        grid.addWidget(QLabel("Create"), row, 0)
        self.kind = QComboBox()
        self.kind.addItems([
            "Text output (txt file + include)",
            "Snippet from a file",
            "Snippet from an object",
            "Specification table (from a CSV)",
        ])
        self.kind.currentIndexChanged.connect(self._update_form)
        grid.addWidget(self.kind, row, 1); row += 1

        # kind 1: text source; kind 2/3: formatter method
        self._lbl_source = QLabel("Source")
        self.source = QComboBox()
        grid.addWidget(self._lbl_source, row, 0)
        grid.addWidget(self.source, row, 1); row += 1
        self.source.currentIndexChanged.connect(self._update_fields)

        # result variable (editable: free typing stays possible)
        self._lbl_result = QLabel("Result")
        self.result = QComboBox()
        self.result.setEditable(True)
        grid.addWidget(self._lbl_result, row, 0)
        grid.addWidget(self.result, row, 1); row += 1

        # kind 4 (specs): spec CSV file + specType
        self._lbl_spec_file = QLabel("Spec file")
        self.spec_file = QComboBox()
        self.spec_file.setEditable(True)
        self.spec_file.currentTextChanged.connect(self._reload_spec_types)
        grid.addWidget(self._lbl_spec_file, row, 0)
        grid.addWidget(self.spec_file, row, 1); row += 1

        self._lbl_spec_type = QLabel("Spec type")
        self.spec_type = QComboBox()
        self.spec_type.setEditable(True)
        grid.addWidget(self._lbl_spec_type, row, 0)
        grid.addWidget(self.spec_type, row, 1); row += 1

        # expression (editable combo prefilled with <VAR>.laplace candidates)
        self._lbl_expr = QLabel("Expression")
        self.expr = QComboBox()
        self.expr.setEditable(True)
        grid.addWidget(self._lbl_expr, row, 0)
        grid.addWidget(self.expr, row, 1); row += 1

        self._lbl_lhs = QLabel("Left-hand side")
        self.lhs = QLineEdit()
        self.lhs.setPlaceholderText('e.g. V_out/V_in')
        grid.addWidget(self._lbl_lhs, row, 0)
        grid.addWidget(self.lhs, row, 1); row += 1

        self._lbl_units = QLabel("Units")
        self.units = QLineEdit()
        grid.addWidget(self._lbl_units, row, 0)
        grid.addWidget(self.units, row, 1); row += 1

        self._lbl_label = QLabel("Label")
        self.label = QLineEdit()
        grid.addWidget(self._lbl_label, row, 0)
        grid.addWidget(self.label, row, 1); row += 1

        self._lbl_caption = QLabel("Caption")
        self.caption = QLineEdit()
        grid.addWidget(self._lbl_caption, row, 0)
        grid.addWidget(self.caption, row, 1); row += 1

        self.multiline = QCheckBox("Multiline equation")
        grid.addWidget(self.multiline, row, 1); row += 1

        # kind 1 free text
        self._lbl_text = QLabel("Text")
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Text content of the snippet …")
        grid.addWidget(self._lbl_text, row, 0)
        grid.addWidget(self.text_edit, row, 1); row += 1

        # kind 2 file fields
        self._lbl_path = QLabel("File")
        self.path = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        pw = QWidget(); ph = QHBoxLayout(pw); ph.setContentsMargins(0, 0, 0, 0)
        ph.addWidget(self.path); ph.addWidget(browse)
        grid.addWidget(self._lbl_path, row, 0)
        grid.addWidget(pw, row, 1); row += 1

        self._lbl_language = QLabel("Language")
        self.language = QComboBox()
        self.language.addItems(["", "ltspice"])
        self.language.setEditable(True)
        grid.addWidget(self._lbl_language, row, 0)
        grid.addWidget(self.language, row, 1); row += 1

        self._lbl_linerange = QLabel("Line range")
        self.linerange = QLineEdit()
        self.linerange.setPlaceholderText("e.g. 2-10 (optional)")
        grid.addWidget(self._lbl_linerange, row, 0)
        grid.addWidget(self.linerange, row, 1); row += 1

        self._lbl_firstnumber = QLabel("First line no.")
        self.firstnumber = QLineEdit()
        self.firstnumber.setPlaceholderText("start line number (optional)")
        grid.addWidget(self._lbl_firstnumber, row, 0)
        grid.addWidget(self.firstnumber, row, 1); row += 1

        # snippet name (output file stem / substitution reference) — required
        self._lbl_name = QLabel("Snippet name")
        self.name = QLineEdit()
        self.name.setPlaceholderText(
            "snippet variable + file stem, e.g. H1 (valid Python name)")
        grid.addWidget(self._lbl_name, row, 0)
        grid.addWidget(self.name, row, 1); row += 1

        hint = QLabel("The instruction is appended to the instruction file; "
                      "running it (re)writes the snippet files. Existing "
                      "snippets with the same name are overwritten.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(hint)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok
                                         | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        outer.addWidget(self._buttons)

        self.name.textChanged.connect(self._validate)
        self.result.editTextChanged.connect(self._validate)
        self.expr.editTextChanged.connect(self._validate)
        self.path.textChanged.connect(self._validate)
        self.spec_file.currentTextChanged.connect(self._validate)
        self.spec_type.currentTextChanged.connect(self._validate)
        self._populate_spec_files()
        self._update_form()

    # ── signature introspection ──────────────────────────────────────────

    def _params(self, method: str) -> list:
        """Ordered parameter names of a formatter method (minus ``self``)."""
        if method not in self._sig_cache:
            sig = inspect.signature(getattr(self._fmt_cls, method))
            self._sig_cache[method] = list(sig.parameters.values())[1:]
        return self._sig_cache[method]

    def _fields_for(self, method: str) -> set:
        """Input widgets a method needs, from its signature."""
        return {_PARAM_WIDGET[p.name] for p in self._params(method)
                if p.name in _PARAM_WIDGET}

    # ── inventory helpers ────────────────────────────────────────────────

    def _vars_for(self, funcs) -> list:
        if funcs is None:
            return []
        return [c["name"] for c in self._calls if c["func"] in funcs]

    def _populate_spec_files(self):
        import os
        from .design_data_panel import find_spec_csvs
        from pathlib import Path
        self.spec_file.clear()
        if self._csv_dir and os.path.isdir(self._csv_dir):
            for p in find_spec_csvs(Path(self._csv_dir)):
                self.spec_file.addItem(p.name)
        self._reload_spec_types()

    def _reload_spec_types(self, *_):
        import os
        from .specifications_viewer import read_spec_types
        cur = self.spec_type.currentText()
        self.spec_type.clear()
        name = self.spec_file.currentText().strip()
        path = os.path.join(self._csv_dir, name) if self._csv_dir else name
        if name and os.path.isfile(path):
            try:
                import SLiCAP as sl
                specs = sl.csv2specs(name) if self._csv_dir else []
                self.spec_type.addItems(read_spec_types(specs))
            except Exception:
                pass
        if cur:
            self.spec_type.setEditText(cur)

    def _expr_candidates(self) -> list:
        return [f"{c['name']}.laplace" for c in self._calls
                if c["func"] in _LAPLACE_FUNCS]

    def _methods_for_kind(self, kind):
        return self._file_methods if kind == KIND_FILE else self._object_methods

    def _current_entry(self):
        """The selected (method, label, result_funcs) for kind 2/3."""
        kind = self.kind.currentIndex()
        methods = self._methods_for_kind(kind)
        idx = min(max(self.source.currentIndex(), 0), len(methods) - 1)
        return methods[idx]

    # ── form cascading ───────────────────────────────────────────────────

    def _update_form(self):
        kind = self.kind.currentIndex()
        self.source.blockSignals(True)
        self.source.clear()
        if kind == KIND_TEXT:
            self._lbl_source.setText("Source")
            self.source.addItems([s[0] for s in _TEXT_SOURCES])
        elif kind in (KIND_FILE, KIND_OBJECT):
            self._lbl_source.setText("Method")
            self.source.addItems([m[1] for m in self._methods_for_kind(kind)])
        # KIND_SPECS: no method — the source combo is hidden
        self.source.blockSignals(False)
        self._update_fields()

    def _update_fields(self):
        kind = self.kind.currentIndex()
        show = set()
        result_funcs = None
        if kind == KIND_TEXT:
            idx = max(self.source.currentIndex(), 0)
            _, method, result_funcs = _TEXT_SOURCES[idx]
            show = {"text"} if method == "text" else {"result"}
        elif kind in (KIND_FILE, KIND_OBJECT):
            _, _, result_funcs = self._current_entry()
            show = self._fields_for(self._current_entry()[0])
        else:  # KIND_SPECS
            show = {"spec_file", "spec_type", "label", "caption"}

        # the source (method) combo is meaningless for specs
        self._lbl_source.setVisible(kind != KIND_SPECS)
        self.source.setVisible(kind != KIND_SPECS)

        vis = {
            "result":   (self._lbl_result, self.result),
            "expr":     (self._lbl_expr, self.expr),
            "lhs":      (self._lbl_lhs, self.lhs),
            "units":    (self._lbl_units, self.units),
            "label":    (self._lbl_label, self.label),
            "caption":  (self._lbl_caption, self.caption),
            "multiline": (self.multiline,),
            "text":     (self._lbl_text, self.text_edit),
            "path":     (self._lbl_path, self.path.parentWidget()),
            "language": (self._lbl_language, self.language),
            "linerange": (self._lbl_linerange, self.linerange),
            "firstnumber": (self._lbl_firstnumber, self.firstnumber),
            "spec_file": (self._lbl_spec_file, self.spec_file),
            "spec_type": (self._lbl_spec_type, self.spec_type),
        }
        for key, widgets in vis.items():
            for w in widgets:
                w.setVisible(key in show)

        # refill pickers; keep the user's text only while it is still a
        # valid candidate for the new selection (otherwise the first
        # candidate wins — stale variables must not leak across filters)
        if "result" in show:
            cur = self.result.currentText()
            items = self._vars_for(result_funcs)
            self.result.clear()
            self.result.addItems(items)
            if cur in items:
                self.result.setEditText(cur)
        if "expr" in show:
            cur = self.expr.currentText()
            items = self._expr_candidates()
            self.expr.clear()
            self.expr.addItems(items)
            if cur in items:
                self.expr.setEditText(cur)
        self._validate()

    def _browse(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select file")
        if fn:
            self.path.setText(fn)

    def _validate(self):
        kind = self.kind.currentIndex()
        ok = self.name.text().strip().isidentifier()
        if kind == KIND_TEXT:
            idx = max(self.source.currentIndex(), 0)
            method = _TEXT_SOURCES[idx][1]
            if method != "text":
                ok = ok and bool(self.result.currentText().strip())
        elif kind == KIND_FILE:
            ok = ok and bool(self.path.text().strip())
        elif kind == KIND_OBJECT:
            fields = self._fields_for(self._current_entry()[0])
            if "result" in fields:
                ok = ok and bool(self.result.currentText().strip())
            if "expr" in fields:
                ok = ok and bool(self.expr.currentText().strip())
        else:  # KIND_SPECS
            ok = ok and bool(self.spec_file.currentText().strip()) \
                and bool(self.spec_type.currentText().strip())
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(ok)

    # ── emission ─────────────────────────────────────────────────────────

    def _init_lines(self, need_txt: bool) -> list:
        """Idempotent formatter-init lines: added only when the instruction
        file does not define them yet."""
        lines = []
        if self._target.ctor_marker not in self._instr_text:
            lines.append(f"{self._target.var} = {self._target.ctor}")
        if need_txt and "TXTformatter()" not in self._instr_text:
            lines.append("txt = sl.TXTformatter()")
        return lines

    def _param_fragment(self, pname: str, name: str):
        """Emit one signature parameter: ``("pos", text)`` for a positional
        argument, ``("kw", "name=value")`` for a keyword, or ``None`` to omit
        it (empty optional, or a parameter left to its default)."""
        res = self.result.currentText().strip()
        if pname == "circuitObject":
            return ("pos", "cir")
        if pname == "resultObject":
            return ("pos", res)
        if pname == "transferCoeffs":
            return ("pos", f"sl.coeffsTransfer({res}.laplace)")
        if pname in ("Iv", "M", "Dv"):
            return ("pos", f"{res}.{pname}")
        if pname == "LHS":
            return ("pos", _q(self.lhs.text().strip()))
        if pname in ("RHS", "expr"):
            return ("pos", self.expr.currentText().strip())
        if pname in ("fileName", "netlistFile"):
            return ("pos", _q(self.path.text().strip()))
        if pname == "name":                        # RST expr/eqnInline
            return ("kw", f"name={_q(name)}")
        if pname == "multiline":
            return ("kw", "multiline=True") if self.multiline.isChecked() else None
        text_fields = {
            "units": self.units, "label": self.label, "caption": self.caption,
            "lineRange": self.linerange, "firstNumber": self.firstnumber,
        }
        if pname in text_fields:
            val = text_fields[pname].text().strip()
            return ("kw", f"{pname}={_q(val)}") if val else None
        if pname == "language":
            val = self.language.currentText().strip()
            return ("kw", f"language={_q(val)}") if val else None
        return None            # circuitObject handled above; color/style default

    def _emit_call(self, method: str, name: str) -> str:
        """A ``<name> = <var>.<method>(…).save(…)`` line, arguments and the
        required/optional split taken from the method signature. A method with
        a ``name=`` substitution parameter appends to the shared file."""
        params = self._params(method)
        pos, kwargs = [], []
        for p in params:
            frag = self._param_fragment(p.name, name)
            if frag is None:
                continue
            (pos if frag[0] == "pos" else kwargs).append(frag[1])
        pnames = {p.name for p in params}
        save_target = self._target.append_file if "name" in pnames else name
        return (f"{name} = {self._target.var}.{method}"
                f"({', '.join(pos + kwargs)}).save({_q(save_target)})")

    def generated_snippet(self) -> str:
        var  = self._target.var
        kind = self.kind.currentIndex()
        name = self.name.text().strip()

        def kw(field, value):
            return f", {field}={_q(value.strip())}" if value.strip() else ""

        if kind == KIND_TEXT:
            idx = max(self.source.currentIndex(), 0)
            _, method, _ = _TEXT_SOURCES[idx]
            lines = self._init_lines(need_txt=True)
            if method == "text":
                content = self.text_edit.toPlainText()
                lines.append(f"{name}_txt = "
                             f"txt.text({_q(content)}).save({_q(name)})")
            else:
                res = self.result.currentText().strip()
                lines.append(f"{name}_txt = "
                             f"txt.{method}({res}).save({_q(name)})")
            lines.append(f"{name} = "
                         f"{var}.file(sl.ini.txt_path + {_q(name + '.txt')})"
                         f".save({_q(name)})")
        elif kind in (KIND_FILE, KIND_OBJECT):
            lines = self._init_lines(need_txt=False)
            lines.append(self._emit_call(self._current_entry()[0], name))
        else:  # KIND_SPECS
            lines = self._init_lines(need_txt=False)
            fname = self.spec_file.currentText().strip()
            specs_var = f"SPECS_{_ident(fname.rsplit('.', 1)[0])}"
            load = f'{specs_var} = sl.csv2specs({_q(fname)})'
            if load not in self._instr_text:
                lines.append(load)
            spectype = self.spec_type.currentText().strip()
            opts = kw("label", self.label.text()) + kw("caption",
                                                       self.caption.text())
            lines.append(f"{name} = {var}.specs({specs_var}, "
                         f"{_q(spectype)}{opts}).save({_q(name)})")
        return "\n".join(lines) + "\n"


class LatexSnippetDialog(SnippetDialog):
    """LaTeX instantiation of the generic snippet dialog."""

    def __init__(self, instr_text: str = "", csv_dir: str = "", parent=None):
        super().__init__(LATEX_TARGET, instr_text=instr_text,
                         csv_dir=csv_dir, parent=parent)


class RstSnippetDialog(SnippetDialog):
    """RST (Sphinx) instantiation of the generic snippet dialog."""

    def __init__(self, instr_text: str = "", csv_dir: str = "", parent=None):
        super().__init__(RST_TARGET, instr_text=instr_text,
                         csv_dir=csv_dir, parent=parent)
