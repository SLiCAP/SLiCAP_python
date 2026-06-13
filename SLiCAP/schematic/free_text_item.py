from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import TEXT_FONT, TEXT_COLOR, snap


class FreeTextItem(QGraphicsTextItem):
    """
    Text annotation on the schematic.

    Font, size, and colour are read from Preferences (config.TEXT_*).
    Placement and editing go through TextDialog; there is no inline editing.
    Double-click is intercepted by the canvas and opens the dialog.
    """

    def __init__(self, text: str = "Text", pos: QPointF = QPointF(0, 0)):
        super().__init__(text)
        self.setPos(pos)
        self.setFont(TEXT_FONT)
        self.setDefaultTextColor(TEXT_COLOR)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
