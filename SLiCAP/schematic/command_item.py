from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import COMMAND_COLOR, COMMAND_FONT, snap


class CommandItem(QGraphicsTextItem):
    """
    SLiCAP command block — one or more lines beginning with '.'.
    Each non-empty line is inserted verbatim into the netlist.
    Double-click to edit; Enter adds a new command line.
    """

    def __init__(self, text: str = ".", pos: QPointF = QPointF(0, 0)):
        super().__init__(text)
        self.setPos(pos)
        self.setFont(COMMAND_FONT)
        self.setDefaultTextColor(COMMAND_COLOR)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        super().focusOutEvent(event)

    def commands(self) -> list[str]:
        """Return each non-empty line as a netlist command string."""
        return [ln for ln in self.toPlainText().splitlines() if ln.strip()]
