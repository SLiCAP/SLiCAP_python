from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainterPathStroker

from .config import snap, Z_BORDER

_PEN_COLOR = QColor(80, 80, 180)
_PEN_WIDTH = 0.8


class BorderItem(QGraphicsRectItem):
    """
    Export boundary rectangle.

    When present, SVG/PDF export uses this rect as the viewport instead of
    the items bounding box.  show_in_export controls whether the dashed
    rectangle itself appears in the exported output.
    """

    def __init__(self, x: float, y: float, width: float, height: float,
                 show_in_export: bool = True):
        super().__init__(0.0, 0.0, width, height)
        self.show_in_export: bool = show_in_export
        self.setPos(x, y)
        self.setPen(QPen(_PEN_COLOR, _PEN_WIDTH, Qt.DashLine))
        self.setBrush(QBrush(Qt.NoBrush))
        self.setZValue(Z_BORDER)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def shape(self) -> QPainterPath:
        """Hit-test only within 5 scene units of the border line (not the interior)."""
        r = self.rect()
        outline = QPainterPath()
        outline.addRect(r)
        stroker = QPainterPathStroker()
        stroker.setWidth(10.0)   # 5 units inside + 5 units outside the line
        return stroker.createStroke(outline)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
