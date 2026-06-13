from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsItem
from PySide6.QtCore import QPointF
from PySide6.QtGui import QFont, QBrush

from .config import (
    HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE,
    HYPERLINK_COLOR, HYPERLINK_UNDERLINE, snap,
)


class HyperlinkItem(QGraphicsSimpleTextItem):
    """
    A clickable hyperlink on the schematic canvas.

    Displayed as styled text (colour + optional underline) read from
    Preferences.  In SVG/PDF export the label is wrapped in an <a href>
    element so it is clickable in browsers and PDF viewers.
    """

    def __init__(self, url: str, label: str, pos: QPointF = QPointF(0, 0)):
        super().__init__(label or url)
        self.url   = url
        self.label = label
        self._apply_style()
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def _apply_style(self) -> None:
        font = QFont(HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE)
        font.setUnderline(HYPERLINK_UNDERLINE)
        self.setFont(font)
        self.setBrush(QBrush(HYPERLINK_COLOR))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
