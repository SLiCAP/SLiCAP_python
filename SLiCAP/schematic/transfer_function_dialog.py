"""Instruction -> Transfer function…: an instruction that makes a Laplace
transfer function without a circuit, so that it lands in the Design data
like a doLaplace() result (Anton, 2026-11-18: "there is still no GUI way
of getting a pure Laplace expression in the Design data").

Three forms, one line each, the dialog computes nothing:

- a classic family: ``H1 = sl.filterFunc("butterworth", "bp", 2, f_c="1k", B=100)``
  (corner or centre frequency and, for bp and bs, bandwidth: one pair of
  fields for every type. f_low/f_high as fields was REPLACED, Anton,
  2026-11-18: "vaguely defined terms")
- one section by type, frequency and Q: ``H1 = sl.sectionFunc("bp", "10k", Q=5)``
- a typed expression: ``H1 = sl.transferFunc("1/(1 + s*T)")``

A frequency or a Q typed as a name instead of a number stays a symbol of
the transfer: a filter made from it gets that name as a parameter pin.
The entry sits on the Instruction menu of the SLiCAP and the system
schematic; not on the NGspice one (Anton, 2026-11-18: realising a
transfer in NGspice needs circuit synthesis, which belongs to SLiCAP).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QDialog, QDialogButtonBox,
                               QFormLayout, QGroupBox, QLabel, QLineEdit,
                               QMessageBox, QRadioButton, QSpinBox, QVBoxLayout)

from .instr_file import next_result_name, quoted
from .sizing import chars, scroll_body, fit_to_screen

FAMILIES = ["butterworth", "bessel", "chebyshev1"]
TYPES = ["lp", "hp", "bp", "bs", "ap"]


def _number_or_name(text: str) -> str:
    """The Python text of a field: a number in SLiCAP notation as it is
    written (the functions take it), a name as a quoted string, which the
    functions turn into a symbol."""
    from SLiCAP.SLiCAPlex import _scale_float
    text = text.strip()
    try:
        _scale_float(text)
        return quoted(text) if text[-1:].isalpha() else text
    except ValueError:
        return quoted(text)


def transfer_line(name, form, **f) -> str:
    """The instruction line of one form: "family", "section" or "typed"."""
    if form == "family":
        args = [quoted(f["family"]), quoted(f["type"]), str(int(f["order"]))]
        args.append("f_c=%s" % _number_or_name(f["f_c"]))
        if f["type"] in ("bp", "bs"):
            args.append("B=%s" % _number_or_name(f["B"]))
        if f["family"] == "chebyshev1":
            args.append("ripple=%s" % _number_or_name(f.get("ripple", "1")))
        return "%s = sl.filterFunc(%s)" % (name, ", ".join(args))
    if form == "section":
        args = [quoted(f["type"]), _number_or_name(f["f_0"])]
        if f.get("Q", "").strip():
            args.append("Q=%s" % _number_or_name(f["Q"]))
        return "%s = sl.sectionFunc(%s)" % (name, ", ".join(args))
    return "%s = sl.transferFunc(%s)" % (name, quoted(f["expr"].strip()))


class TransferFunctionDialog(QDialog):
    """Result name and one of the three forms; the fields of the other
    forms are greyed out."""

    def __init__(self, instr_text: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Transfer function")
        self.setMinimumWidth(chars(self, 60))
        frame, lay, self._scroll = scroll_body(self)
        top = QFormLayout()
        self._name = QLineEdit(next_result_name("H", instr_text))
        top.addRow("Result name:", self._name)
        lay.addLayout(top)

        self._family_rb = QRadioButton("Classic family (filterFunc)")
        self._family_rb.setChecked(True)
        self._section_rb = QRadioButton("One section by frequency and Q (sectionFunc)")
        self._typed_rb = QRadioButton("Typed expression in s (transferFunc)")
        # the three live in different group boxes: exclusive only through
        # an explicit button group
        self._forms = QButtonGroup(self)
        for rb in (self._family_rb, self._section_rb, self._typed_rb):
            self._forms.addButton(rb)

        box = QGroupBox()
        f = QFormLayout(box)
        f.addRow(self._family_rb)
        self._family = QComboBox()
        self._family.addItems(FAMILIES)
        f.addRow("Family:", self._family)
        self._ftype = QComboBox()
        self._ftype.addItems(TYPES)
        f.addRow("Type:", self._ftype)
        self._order = QSpinBox()
        self._order.setRange(1, 20)
        self._order.setValue(2)
        f.addRow("Order:", self._order)
        self._f_c = QLineEdit()
        self._f_c.setPlaceholderText("Hz, number or name")
        f.addRow("Corner / centre frequency f_c:", self._f_c)
        self._B = QLineEdit()
        self._B.setPlaceholderText("Hz, number or name (bp, bs)")
        f.addRow("Bandwidth B:", self._B)
        self._ripple = QLineEdit("1")
        f.addRow("Ripple [dB] (Chebyshev):", self._ripple)
        lay.addWidget(box)
        self._family_box = (self._family, self._ftype, self._order, self._f_c,
                            self._B, self._ripple)

        box = QGroupBox()
        f = QFormLayout(box)
        f.addRow(self._section_rb)
        self._stype = QComboBox()
        self._stype.addItems(TYPES)
        f.addRow("Type:", self._stype)
        self._f_0 = QLineEdit()
        self._f_0.setPlaceholderText("Hz, number or name")
        f.addRow("f_0:", self._f_0)
        self._Q = QLineEdit()
        self._Q.setPlaceholderText("empty: first order (lp, hp, ap)")
        f.addRow("Q:", self._Q)
        lay.addWidget(box)
        self._section_box = (self._stype, self._f_0, self._Q)

        box = QGroupBox()
        f = QFormLayout(box)
        f.addRow(self._typed_rb)
        self._expr = QLineEdit()
        self._expr.setPlaceholderText("e.g. 1/(1 + s*T), SLiCAP notation")
        f.addRow("H(s):", self._expr)
        lay.addWidget(box)
        self._typed_box = (self._expr,)

        hint = QLabel("A frequency or a Q given as a name stays a symbol of the "
                      "transfer: a filter made from it gets a pin for it.")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        for rb in (self._family_rb, self._section_rb, self._typed_rb):
            rb.toggled.connect(self._enable)
        self._ftype.currentTextChanged.connect(self._enable)
        self._enable()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check)
        buttons.rejected.connect(self.reject)
        frame.addWidget(buttons)
        fit_to_screen(self, self._scroll)

    # ---- state -------------------------------------------------------------

    def form(self) -> str:
        if self._section_rb.isChecked():
            return "section"
        if self._typed_rb.isChecked():
            return "typed"
        return "family"

    def _enable(self, *_):
        form = self.form()
        for w in self._family_box:
            w.setEnabled(form == "family")
        for w in self._section_box:
            w.setEnabled(form == "section")
        for w in self._typed_box:
            w.setEnabled(form == "typed")
        if form == "family":
            t = self._ftype.currentText()
            self._B.setEnabled(t in ("bp", "bs"))
            self._ripple.setEnabled(self._family.currentText() == "chebyshev1")

    def _fields(self) -> dict:
        form = self.form()
        if form == "family":
            return {"family": self._family.currentText(), "type": self._ftype.currentText(),
                    "order": self._order.value(), "f_c": self._f_c.text(),
                    "B": self._B.text(), "ripple": self._ripple.text()}
        if form == "section":
            return {"type": self._stype.currentText(), "f_0": self._f_0.text(),
                    "Q": self._Q.text()}
        return {"expr": self._expr.text()}

    def error(self) -> str:
        """Why the fields cannot make a line, or ""."""
        name = self._name.text().strip()
        if not name.isidentifier():
            return "Not a valid result name: %r" % name
        f = self._fields()
        form = self.form()
        if form == "family":
            if not f["f_c"].strip():
                return "Give f_c."
            if f["type"] in ("bp", "bs") and not f["B"].strip():
                return "A %s filter needs the bandwidth B." % f["type"]
        elif form == "section":
            if not f["f_0"].strip():
                return "Give f_0."
            if f["type"] in ("bp", "bs") and not f["Q"].strip():
                return "A %s section is second order: give Q." % f["type"]
        elif not f["expr"].strip():
            return "Type the transfer function."
        return ""

    def _check(self):
        error = self.error()
        if error:
            QMessageBox.warning(self, "Transfer function", error)
            return
        self.accept()

    def generated_snippet(self) -> str:
        return transfer_line(self._name.text().strip(), self.form(), **self._fields())
