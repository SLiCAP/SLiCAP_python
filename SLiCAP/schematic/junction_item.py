from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, Qt

from .config import JUNCTION_COLOR, JUNCTION_RADIUS, snap, Z_JUNCTION

_SEL_PAD = 3.0  # extra space around the dot so the selection box appears around it


def _pt_key(pt: QPointF) -> tuple:
    return (round(pt.x()), round(pt.y()))


class JunctionItem(QGraphicsEllipseItem):
    """
    Electrical junction dot — always user-managed.

    Junctions are auto-placed when a wire drawing operation creates a new
    T-intersection, but they are ordinary objects after that: selectable,
    movable, and deletable.  There is no separate 'auto' type.
    """

    def __init__(self, center: QPointF):
        r = JUNCTION_RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.setPos(center)
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(JUNCTION_COLOR))
        self.setZValue(Z_JUNCTION)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def boundingRect(self) -> QRectF:
        r = JUNCTION_RADIUS + _SEL_PAD
        return QRectF(-r, -r, 2.0 * r, 2.0 * r)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            snapped = snap(value)
            if self.scene() and not getattr(self.scene(), '_group_drag_active', False):
                delta = snapped - self.pos()
                if delta.x() or delta.y():
                    self._rubber_band_wires(delta)
            return snapped
        return super().itemChange(change, value)

    def _rubber_band_wires(self, delta: QPointF) -> None:
        """Move wire endpoints that currently touch this junction."""
        from .wire_item import WireItem
        pos_key = _pt_key(self.pos())
        for item in self.scene().items():
            if not isinstance(item, WireItem):
                continue
            hits = {i for i, pt in enumerate(item.points) if _pt_key(pt) == pos_key}
            if hits:
                item.move_points(hits, delta)
