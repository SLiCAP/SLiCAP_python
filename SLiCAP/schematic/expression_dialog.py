"""Expression creator - the sub-dialog that composes ONE expression.

Shared by the Traces and the Measurements tab of the Traces dialog (Anton,
2026-08-02): both compose the same kind of expression, over the same signals,
circuit parameters, functions and goal functions, so there is ONE
implementation of the four insert menus. The caller passes what differs -
the caption, the sources, whether a goal function applies and what it MEANS
here - the same way :class:`SnippetDialog` takes a target.

Opening it is not the only way to write an expression: the table cell stays
directly editable, so a quick ``V_out`` needs no window. This dialog is for
composing with the menus, and it is where the explanations live, because
that is where they are read.

The names offered come from the CORE - the goal functions from
:func:`SLiCAP.SLiCAPtraces.goal_names`, the trace functions from
:func:`SLiCAP.SLiCAPtraces.function_names` - so the dialog cannot disagree
with what ``make_traces`` and ``measure`` accept.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMenu, QDialogButtonBox,
)

from SLiCAP.SLiCAPtraces import goal_names, function_names

# {expression name: [(parameter label, default), …]}
_GOALS = goal_names()
# {name: what it does} - dB_20, phase, real, … (SLiCAPtraces._TRACE_FUNCTIONS)
_FUNCTIONS = function_names()


class ExpressionDialog(QDialog):
    """Compose one expression with the insert menus.

    :param caption: what is being written, e.g. "Y expression of trace 1".
    :type caption: str

    :param text: the expression as it stands.
    :type text: str

    :param signals: signals of the result, as the simulator names them.
    :type signals: list

    :param assigned: ``{simulated signal: Python variable}`` already assigned.
    :type assigned: dict

    :param on_signal: called with a signal the user picks; returns the Python
                      name to insert. The caller owns the assignment table,
                      so it is the caller that creates a missing row.
    :type on_signal: callable

    :param params: circuit parameters usable in the expression.
    :type params: list

    :param goal_enabled: False when the result has no runs to reduce.
    :type goal_enabled: bool

    :param hint: what applies HERE - a goal function makes a trace into a
                 measurement, complex data shows its magnitude, …
    :type hint: str
    """

    def __init__(self, caption, text="", signals=(), assigned=None,
                 on_signal=None, params=(), goal_enabled=True, hint="",
                 parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit Expression")
        self.setMinimumWidth(560)
        self._on_signal = on_signal

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(caption))

        self._expr = QLineEdit(str(text or ""))
        self._expr.setPlaceholderText("numpy syntax, e.g. RMS(I_V1**2*R_a)")
        outer.addWidget(self._expr)

        inserts = QHBoxLayout()
        self._insert_signal = QPushButton("Insert Signal")
        self._insert_param = QPushButton("Insert Circuit Parameter")
        self._insert_function = QPushButton("Insert Function")
        self._insert_goal = QPushButton("Insert Goal Function")
        for button in (self._insert_signal, self._insert_param,
                       self._insert_function, self._insert_goal):
            button.setMenu(QMenu(self))
            inserts.addWidget(button)
        inserts.addStretch(1)
        outer.addLayout(inserts)

        if hint:
            label = QLabel(hint)
            label.setWordWrap(True)
            label.setStyleSheet("color: grey; font-size: 9pt;")
            outer.addWidget(label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok
                                   | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._fill_menus(signals, assigned or {}, params, goal_enabled)
        self._expr.setFocus()
        self._expr.end(False)

    # ── the menus ─────────────────────────────────────────────────────────

    def _fill_menus(self, signals, assigned, params, goal_enabled):
        menu = self._insert_signal.menu()
        # EVERY signal of the result is offerable: picking one that has no
        # Python name yet creates its assignment row, so `v(out)` and
        # `@q1[gm]` are not second-class (TRACES.md phase 6d).
        for signal in signals:
            label = ("{0}   [{1}]".format(signal, assigned[signal])
                     if signal in assigned else signal)
            menu.addAction(label, lambda s=signal: self._insert_signal_name(s))
        self._insert_signal.setEnabled(bool(signals))

        menu = self._insert_param.menu()
        for name in params:
            menu.addAction(name, lambda n=name: self._insert(n))
        self._insert_param.setEnabled(bool(params))

        menu = self._insert_function.menu()
        for name, description in _FUNCTIONS.items():
            menu.addAction("{0}(y)   {1}".format(name, description),
                           lambda n=name: self._insert_call(n))

        menu = self._insert_goal.menu()
        for name, goal_params in _GOALS.items():
            text = name + ("(y, " + ", ".join(label
                                              for label, _d in goal_params)
                           + ")" if goal_params else "(y)")
            menu.addAction(text, lambda n=name, p=goal_params:
                           self._insert_call(n, p))
        # A goal reduces ONE RUN to one number, so it needs runs to reduce.
        self._insert_goal.setEnabled(bool(goal_enabled))

    # ── inserting ─────────────────────────────────────────────────────────

    def _insert(self, text: str, caret_back: int = 0):
        """Insert *text* at the cursor (replacing a selection) and put the
        cursor *caret_back* characters back into it."""
        self._expr.insert(text)
        if caret_back:
            self._expr.setCursorPosition(
                max(0, self._expr.cursorPosition() - caret_back))
        self._expr.setFocus()

    def _insert_signal_name(self, signal: str):
        """Insert a signal by its PYTHON name; the caller assigns one when
        the signal has none yet."""
        name = self._on_signal(signal) if self._on_signal else signal
        self._insert(str(name))

    def _insert_call(self, name: str, params: list = ()):
        """Wrap the selected part of the expression in *name*, or insert the
        call with its parameter defaults filled in.

        Used for both menus: a function (``dB_20``) takes the signal only, a
        goal function may take parameters after it (``Y_AT_X(V_out, 1e3)``).
        """
        selection = self._expr.selectedText()
        arguments = [selection] + [str(default) for _label, default in params]
        text = "{0}({1})".format(name, ", ".join(arguments))
        self._insert(text, 0 if selection else len(text) - len(name) - 1)

    # ── result ────────────────────────────────────────────────────────────

    def expression(self) -> str:
        return self._expr.text().strip()
