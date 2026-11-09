"""A value field that also offers the parameters of the run.

A simulation setting - the stop time of a transient run, the frequency
limits of an AC run, the limits of a sweep or a stepping - is a number, or
the name of a parameter with a numeric value: a ``.param`` of the circuit
or an item of the spec file. The instruction file then names the
parameter, and the run reads its value when it runs, so a design step
that writes a new value to the specs is picked up without an edit
(Anton, 2026-11-09).

Layout (Anton, 2026-11-09): first a source selector, *manual*, *circuit*
or *specs*; then, for a parameter source, a list of the parameters that
source offers, with the parameter's value shown next to it; for *manual*,
a value field. An editable combo box holding either a number or a picked
name was the previous form and was REPLACED by this one on Anton's
request: the source is chosen explicitly, and the value of a picked
parameter is visible.

The field keeps the API of a line edit for its users: ``text()`` is the
number or the parameter name, ``setText()`` picks the source from the
name, ``textChanged`` fires on every change.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel, QStackedWidget)

from .sizing import cap_chars, fit_contents
from .value_fields import watch, set_parameter_names, is_number

MANUAL = "manual"


class ParamField(QWidget):
    """See the module docstring. ``set_choices`` takes ``(source, name,
    value)`` triples; ``parameter()`` is the picked name or None;
    ``source_of(name)`` the source that offers a name."""

    textChanged = Signal(str)

    def __init__(self, placeholder: str = "", width: int = 16, parent=None):
        super().__init__(parent)
        self._choices: list[tuple[str, str, str]] = []
        self._any_name = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._source = QComboBox()
        self._source.addItem(MANUAL)
        fit_contents(self._source)
        lay.addWidget(self._source)
        self._stack = QStackedWidget()
        self._value = QLineEdit()
        if placeholder:
            self._value.setPlaceholderText(placeholder)
        cap_chars(self._value, width)
        watch(self._value, "number")
        self._param = QComboBox()
        self._param.setMinimumWidth(self._value.minimumWidth())
        self._stack.addWidget(self._value)
        self._stack.addWidget(self._param)
        lay.addWidget(self._stack)
        self._shown = QLabel("")
        self._shown.setStyleSheet("color: grey;")
        lay.addWidget(self._shown)
        lay.addStretch(1)
        self._source.currentTextChanged.connect(self._source_picked)
        self._param.currentIndexChanged.connect(self._param_picked)
        self._value.textChanged.connect(self.textChanged)
        self._show_source(MANUAL)

    # -- line-edit API --------------------------------------------------------

    def text(self) -> str:
        if self._source.currentText() == MANUAL:
            return self._value.text()
        return self._param.currentText().strip()

    def setText(self, text) -> None:
        """A known parameter name selects its source and the name; anything
        else is a manual value."""
        before = self.text()
        self._set_text_quietly(str(text))
        if self.text() != before:
            self.textChanged.emit(self.text())

    def _set_text_quietly(self, text: str) -> None:
        """setText without a signal: the widgets are rebuilt in silence and
        the one textChanged follows at the end (a signal from the middle
        of a rebuild made the dialog read a half-built field, 2026-11-09)."""
        src = self.source_of(text)
        if src is None and self._any_name and text.strip().isidentifier() \
                and self._source.count() > 1:
            src = self._source.itemText(1)
        self._source.blockSignals(True)
        self._param.blockSignals(True)
        self._value.blockSignals(True)
        if src is None:
            self._source.setCurrentText(MANUAL)
            self._show_source(MANUAL)
            self._value.setText(text)
        else:
            self._source.setCurrentText(src)
            self._show_source(src)
            idx = self._param.findText(text)
            if idx >= 0:
                self._param.setCurrentIndex(idx)
            elif self._param.isEditable():
                self._param.setEditText(text)
            self._show_value()
        self._value.blockSignals(False)
        self._param.blockSignals(False)
        self._source.blockSignals(False)

    # -- choices --------------------------------------------------------------

    def set_choices(self, choices, any_name: bool = False, sources=()) -> None:
        """``[(source, name, value), ...]``: the parameters with a numeric
        value the field may name, grouped by source in the selector.
        *sources* are offered even without a name. With *any_name* the list
        is editable and every identifier is accepted: the names are not
        known here, the run checks them (a SLiCAP result with
        ``pardefs='circuit'``)."""
        self._any_name = any_name
        self._choices = [(str(c[0]), str(c[1]), str(c[2]) if len(c) > 2 else "")
                         for c in choices]
        current = self.text()
        was_manual = self._source.currentText() == MANUAL
        sources = list(dict.fromkeys(
            [str(s) for s in sources] + [src for src, _, _ in self._choices]))
        self._source.blockSignals(True)
        self._source.clear()
        self._source.addItem(MANUAL)
        self._source.addItems(sources)
        fit_contents(self._source)
        self._source.blockSignals(False)
        if any_name and not self._param.isEditable():
            self._param.setEditable(True)
            edit = self._param.lineEdit()
            watch(edit, "parameter")
            set_parameter_names(edit, None)
            edit.textChanged.connect(self.textChanged)
        elif not any_name and self._param.isEditable():
            self._param.setEditable(False)
        # keep the pick where the list still has it, else back to manual
        self._set_text_quietly(current if not was_manual else self._value.text())
        if self.text() != current:
            self.textChanged.emit(self.text())

    def names(self) -> list[str]:
        return [n for _, n, _ in self._choices]

    def source_of(self, name: str) -> str | None:
        """The source of a parameter the field offers, else None."""
        return next((src for src, n, _ in self._choices if n == name), None)

    def value_of(self, name: str) -> str:
        return next((v for _, n, v in self._choices if n == name), "")

    def parameter(self) -> str | None:
        """The parameter the field names, or None for a manual value."""
        if self._source.currentText() == MANUAL:
            return None
        name = self.text()
        if name in self.names() or (self._any_name and name.isidentifier()):
            return name
        return None

    # -- internals ------------------------------------------------------------

    def _show_source(self, src: str) -> None:
        """Show the widget of *src*: the value field, or the list of that
        source's parameters. No signal."""
        if src == MANUAL:
            self._stack.setCurrentWidget(self._value)
            self._shown.setText("")
            return
        self._param.blockSignals(True)
        self._param.clear()
        self._param.addItems([n for s, n, _ in self._choices if s == src])
        self._param.blockSignals(False)
        self._stack.setCurrentWidget(self._param)
        if not is_number(self._value.text()):
            self._value.clear()        # a hidden field must not block the dialog
        self._show_value()

    def _show_value(self) -> None:
        from .par_source_table import display_value
        name = self.text() if self._source.currentText() != MANUAL else ""
        self._shown.setText(display_value(self.value_of(name)) if name else "")

    def _source_picked(self, src: str) -> None:
        self._show_source(src)
        self.textChanged.emit(self.text())

    def _param_picked(self, _index: int) -> None:
        self._show_value()
        self.textChanged.emit(self.text())
