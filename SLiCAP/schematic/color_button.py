"""
The colour swatch button of the dialogs (border, shape, drawing preferences).

One class, so that a fix reaches every dialog. Two rules learned the hard
way (Anton, Win10 2026-09-25 and Linux 2026-09-30):

* The swatch colour is set with a stylesheet SCOPED to this button by
  object name. A bare ``background-color: ...`` cascades to every child
  widget, the colour picker included, which then renders in the swatch
  colour.
* The colour picker is parented to the top-level window, not to the
  button, for the same reason.
"""
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QColorDialog

from .sizing import fix_chars

_OBJECT_NAME = "slicapColorBtn"
_CHARS = 7          # swatch width in digit widths


class ColorButton(QPushButton):
    """Swatch button opening a colour picker. ``color()`` is the colour name
    ``#rrggbb``; ``changed`` carries the new name when the user picked one."""

    changed = Signal(str)

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setObjectName(_OBJECT_NAME)
        fix_chars(self, _CHARS)
        self._color = QColor(color)
        self._refresh()
        self.clicked.connect(self._pick)

    def color(self) -> str:
        return self._color.name()

    def qcolor(self) -> QColor:
        return QColor(self._color)

    def _pick(self):
        c = QColorDialog.getColor(self._color, self.window())
        if c.isValid():
            self._color = c
            self._refresh()
            self.changed.emit(self.color())

    def _refresh(self):
        self.setStyleSheet(
            "#%s { background-color: %s; border: 1px solid #888; }"
            % (_OBJECT_NAME, self._color.name()))
        self.setText("")
