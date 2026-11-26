"""A table cell with a small button at its right edge.

The cell stays an ordinary text cell: a double click or a key edits the text
in place. The button opens a helper for the same cell, for instance the
expression creator of the Traces dialog (Anton, 2026-11-25).

The delegate PAINTS the button. The item keeps its text, its itemChanged
signal and its line editor, so the dialog code that reads and writes the
cells is unchanged. While the cell is being edited, the editor covers the
button.

A cell widget (a line edit plus a button) was considered and REJECTED
(2026-11-25): the dialogs read and write these cells as QTableWidgetItems and
listen to itemChanged, and a widget in the cell would take both over.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QEvent, QRect, QPersistentModelIndex, Signal
from PySide6.QtWidgets import (
    QApplication, QStyle, QStyledItemDelegate, QStyleOptionButton,
    QStyleOptionViewItem, QToolTip,
)


class CellButtonDelegate(QStyledItemDelegate):
    """Paints a button at the right edge of every editable cell it is set
    on, and emits ``clicked(row, column)`` when that button is clicked.

    Set it on columns with ``setItemDelegateForColumn``. A cell that is not
    editable gets no button.
    """

    clicked = Signal(int, int)

    def __init__(self, text: str = "…", tooltip: str = "", parent=None):
        super().__init__(parent)
        self._text = text
        self._tooltip = tooltip
        self._pressed = None        # the cell whose button is held down

    @staticmethod
    def _has_button(index) -> bool:
        return bool(index.flags() & Qt.ItemFlag.ItemIsEditable)

    def button_rect(self, option) -> QRect:
        """The button inside the cell *option.rect*: as wide as the cell is
        high, or wider when its text needs it."""
        rect = option.rect
        width = max(rect.height(),
                    option.fontMetrics.horizontalAdvance(self._text) + 12)
        return QRect(rect.right() - width + 1, rect.top(), width,
                     rect.height()).adjusted(2, 2, -2, -2)

    def paint(self, painter, option, index):
        if not self._has_button(index):
            super().paint(painter, option, index)
            return
        widget = option.widget
        style = widget.style() if widget else QApplication.style()
        # the background (selection) over the full cell, the text left of
        # the button
        full = QStyleOptionViewItem(option)
        self.initStyleOption(full, index)
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem,
                            full, painter, widget)
        button = self.button_rect(option)
        text = QStyleOptionViewItem(option)
        text.rect = option.rect.adjusted(0, 0, -(button.width() + 4), 0)
        super().paint(painter, text, index)
        face = QStyleOptionButton()
        face.rect = button
        face.text = self._text
        face.fontMetrics = option.fontMetrics
        face.state = QStyle.StateFlag.State_Enabled | (
            QStyle.StateFlag.State_Sunken
            if self._pressed == QPersistentModelIndex(index)
            else QStyle.StateFlag.State_Raised)
        style.drawControl(QStyle.ControlElement.CE_PushButton, face, painter,
                          widget)

    def editorEvent(self, event, model, option, index):
        """A press on the button holds it down, the release on it clicks.
        Both are consumed, so the cell does not start editing."""
        kind = event.type()
        if kind not in (QEvent.Type.MouseButtonPress,
                        QEvent.Type.MouseButtonDblClick,
                        QEvent.Type.MouseButtonRelease):
            return super().editorEvent(event, model, option, index)
        on_button = (self._has_button(index)
                     and event.button() == Qt.MouseButton.LeftButton
                     and self.button_rect(option).contains(
                         event.position().toPoint()))
        here = QPersistentModelIndex(index)
        if kind == QEvent.Type.MouseButtonRelease:
            clicked = on_button and self._pressed == here
            self._pressed = None
            if clicked:
                self.clicked.emit(index.row(), index.column())
                return True
        else:
            # every press decides anew, so a press that never got its
            # release leaves nothing behind
            self._pressed = here if on_button else None
            if on_button:
                return True
        return super().editorEvent(event, model, option, index)

    def helpEvent(self, event, view, option, index):
        if (self._tooltip and event.type() == QEvent.Type.ToolTip
                and self._has_button(index)
                and self.button_rect(option).contains(event.pos())):
            QToolTip.showText(event.globalPos(), self._tooltip, view)
            return True
        return super().helpEvent(event, view, option, index)
