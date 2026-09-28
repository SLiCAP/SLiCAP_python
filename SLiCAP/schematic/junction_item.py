from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QStyle
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, Qt

from .config import snap, style_of, default_style, Z_JUNCTION, SELECTION_COLOR

_SEL_PAD = 3.0  # extra space around the dot: an easier click target


def _pt_key(pt: QPointF) -> tuple:
    return (round(pt.x()), round(pt.y()))


class JunctionItem(QGraphicsEllipseItem):
    GRID_CRITICAL = True      # always snaps: connectivity (config.snap_pos)
    """
    Electrical junction dot — always user-managed.

    Junctions are auto-placed when a wire drawing operation creates a new
    T-intersection, but they are ordinary objects after that: selectable,
    movable, and deletable.  There is no separate 'auto' type.
    """

    def __init__(self, center: QPointF):
        super().__init__()
        self._apply_style(default_style())
        self.setPos(center)
        self.setPen(QPen(Qt.NoPen))
        self.setZValue(Z_JUNCTION)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def _apply_style(self, style) -> None:
        self._radius = style.JUNCTION_RADIUS
        r = self._radius
        self.setRect(-r, -r, 2 * r, 2 * r)
        self.setBrush(QBrush(style.JUNCTION_COLOR))

    def boundingRect(self) -> QRectF:
        r = self._radius + _SEL_PAD
        return QRectF(-r, -r, 2.0 * r, 2.0 * r)

    def paint(self, painter, option, widget=None):
        # Selected: the dot itself in the selection colour, no box around it
        # (like wires and shapes; Anton, 2026-09-27).
        clean_option = option.__class__(option)
        clean_option.state = option.state & ~QStyle.State_Selected
        if option.state & QStyle.State_Selected:
            painter.save()
            painter.setPen(QPen(Qt.NoPen))
            painter.setBrush(QBrush(SELECTION_COLOR))
            painter.drawEllipse(self.rect())
            painter.restore()
        else:
            super().paint(painter, clean_option, widget)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self._apply_style(style_of(self))
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
