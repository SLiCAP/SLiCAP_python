"""Input validation for value fields (Anton, 2026-07-31).

ONE notation for numbers: the user writes SLiCAP notation, where a scale
factor is exactly ONE case-sensitive character ('M' = mega, 'm' = milli).
NGspice spellings - ``1MEG``, ``10K``, ``1kohm``, ``1uF``, ``1mil`` - are NOT
converted, because ``1M``, ``1K`` and ``1F`` mean different numbers in the two
notations and a tolerant reader would have to guess.

Such a value is refused **before it is accepted**, not reported afterwards:
the field is marked while its text is unusable and the dialog's accept button
stays disabled, so it cannot reach a netlist at all. A message box would say
the same thing one step too late, and a line in the log panel would not be
seen.

The CHECK is the core's, not a copy of it:

- :func:`SLiCAP.SLiCAPmath.str2number` for a field that must hold a plain
  number (analysis arguments, step values) - returns None when it does not;
- :func:`SLiCAP.SLiCAPmath._checkExpression` for a field where an expression
  is legitimate (component values, ``.param``, stimuli) - keeps the symbols,
  which then go into the netlist in braces for NGspice to resolve.

The script path is guarded separately, at the boundary functions in
:mod:`SLiCAP.SLiCAPngspice`, which raise ``ValueError``: a script never passes
through a dialog.
"""
from __future__ import annotations

import contextlib
import io

from SLiCAP.SLiCAPmath import str2number, _checkExpression
from SLiCAP.SLiCAPlex import _SCALEFACTORS

#: marks a field whose text is not usable; the attribute set by :func:`watch`
KIND_ATTRIBUTE = "_slicap_value_kind"

_MARK = "QLineEdit { background-color: #ffe0e0; }"

_HINT = ("Not SLiCAP notation. A scale factor is ONE case-sensitive "
         "character: " + " ".join(sorted(_SCALEFACTORS)) + ". "
         "NGspice spellings (1MEG, 10K, 1kohm, 1uF, 1mil) are not accepted; "
         "write 1M, 10k, 1k, 1u.")


def _reads_as_number(text) -> bool:
    """True when str2number can read *text*.

    str2number RAISES for anything that is not a plain number in SLiCAP
    notation - that is its contract. A field validator asks a question, so
    it catches here rather than changing that contract.
    """
    try:
        return str2number(text) is not None
    except BaseException:
        return False


def is_number(text) -> bool:
    """True when *text* is a plain number in SLiCAP notation (or empty, so a
    field is not marked before anything is typed)."""
    text = str(text).strip()
    return not text or _reads_as_number(text)


def is_value(text) -> bool:
    """True when *text* is a number OR an expression SLiCAP can read.

    Braces are netlist syntax rather than mathematics, so ``{A}`` is checked
    as ``A``.
    """
    text = str(text).strip()
    if not text:
        return True
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    # _checkExpression PRINTS its complaint; here it is asked a question, and
    # a half-typed expression would otherwise print on every keystroke.
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return _checkExpression(text) is not None
        except BaseException:
            return False


def is_number_list(text) -> bool:
    """True when *text* is a list of plain numbers - the step value list,
    written space- or comma-separated."""
    text = str(text).strip()
    if not text:
        return True
    return all(_reads_as_number(item)
               for item in text.replace(",", " ").split())


#: a name whose LaTeX would not say what it looks like
LATEX_HINT = ("This name renders oddly in LaTeX: sympy reads '__' as a "
              "SUPERSCRIPT (I__q1_ic prints as I^{q1}_{ic}) and a trailing "
              "'_' as an empty subscript. It is accepted - the name is "
              "yours - but 'I_q1_ic' prints as intended.")


def is_latex_safe(name) -> bool:
    """True when a Python NAME renders in LaTeX as it reads.

    SLiCAP turns a name into LaTeX through sympy, where the underscore is
    subscript syntax: ``I__q1_ic`` becomes ``I^{q1}_{ic}`` - a power, not a
    current - and ``I_`` becomes an empty subscript. Flagged, never refused
    (Anton, 2026-08-03): the name is the user's, and this is presentation,
    not correctness.
    """
    text = str(name).strip()
    if not text:
        return True
    return not ("__" in text or text.startswith("_") or text.endswith("_"))


def mark_item(item, ok: bool, hint: str = "") -> None:
    """Flag a TABLE CELL the way :func:`watch` flags a field: a table holds
    items, which have no style sheet of their own."""
    from PySide6.QtGui import QBrush, QColor
    item.setBackground(QBrush(QColor("#ffe0e0")) if not ok else QBrush())
    item.setToolTip("" if ok else hint)


def check(text, kind: str = "number") -> bool:
    """Validity of *text* for a field of *kind*: 'number' (a plain number),
    'numbers' (a list of them) or 'value' (a number or an expression)."""
    if kind == "number":
        return is_number(text)
    if kind == "numbers":
        return is_number_list(text)
    return is_value(text)


def watch(edit, kind: str = "number", changed=None):
    """Mark *edit* whenever its text is not usable, and tag it with *kind*.

    *changed* is called after every check, so a dialog can re-evaluate its
    accept button. Returns the refresh function (call it after a programmatic
    ``setText``).
    """
    setattr(edit, KIND_ATTRIBUTE, kind)

    def _refresh(*_args):
        ok = check(edit.text(), kind)
        edit.setStyleSheet("" if ok else _MARK)
        edit.setToolTip("" if ok else _HINT)
        if changed is not None:
            changed()

    edit.textChanged.connect(_refresh)
    _refresh()
    return _refresh


def all_valid(widget) -> bool:
    """True when every watched field in *widget* holds usable text.

    *widget* itself counts when it is a watched field, so a single field and
    a whole tab are asked the same way.
    """
    from PySide6.QtWidgets import QLineEdit
    fields = list(widget.findChildren(QLineEdit))
    if isinstance(widget, QLineEdit):
        fields.append(widget)
    for edit in fields:
        kind = getattr(edit, KIND_ATTRIBUTE, None)
        if kind is not None and not check(edit.text(), kind):
            return False
    return True
