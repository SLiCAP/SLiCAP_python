from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QGraphicsPathItem, QGraphicsItem, QGraphicsSimpleTextItem, QStyle,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPainterPathStroker, QPainter, QColor

from .config import (
    WIRE_COLOR, WIRE_WIDTH,
    NET_LABEL_COLOR, NET_LABEL_FONT,
    HANDLE_COLOR, HANDLE_SIZE,
    Z_WIRE, Z_NET_LABEL,
)

_HIT_TOL          = 6.0   # click-to-wire tolerance in scene units
_NET_LABEL_OFFSET = 3.0   # default y-offset above the first wire point


def _seg_dist(p: QPointF, a: QPointF, b: QPointF) -> float:
    """Perpendicular (clamped) distance from p to segment a→b."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    if dx == 0 and dy == 0:
        return math.hypot(p.x() - a.x(), p.y() - a.y())
    t = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(p.x() - (a.x() + t * dx), p.y() - (a.y() + t * dy))


class _NetLabel(QGraphicsSimpleTextItem):
    """
    Draggable, selectable net-name label, child of WireItem.

    Position is stored on the parent as label_offset relative to points[0],
    so the label travels with the wire during rubber-banding.
    WireItem has no rotation transform, so the label is always horizontal.

    The label sits above wires in Z-order so it receives clicks first.
    When selected a bounding-box is drawn (like a component selection rect).
    """

    def __init__(self, parent: "WireItem"):
        super().__init__(parent)
        self.setFont(NET_LABEL_FONT)
        self.setBrush(QBrush(NET_LABEL_COLOR))
        self.setPen(QPen(Qt.NoPen))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)   # selectable independently
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(Z_NET_LABEL)

    def shape(self) -> QPainterPath:
        # Pad the clickable area beyond the tight glyph bounds so a short net
        # name is an easy target (the default shape is hard to hit).
        path = QPainterPath()
        path.addRect(self.boundingRect().adjusted(-3, -2, 3, 2))
        return path

    def mousePressEvent(self, event):
        w = self.parentItem()
        if w is not None:
            w._label_active = True
            w.update()
        # Accept the event so the wire behind is not also selected.
        event.accept()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        w = self.parentItem()
        if w is not None:
            w._label_active = False
            w.update()
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        # Draw text without Qt's default selection indicator.
        clean_option = option.__class__(option)
        clean_option.state = option.state & ~QStyle.State_Selected
        super().paint(painter, clean_option, widget)
        if option.state & QStyle.State_Selected:
            painter.save()
            painter.setPen(QPen(QColor(0, 120, 215), 0.8))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
            painter.restore()

    def itemChange(self, change, value):
        wire = self.parentItem()
        if wire is not None:
            if change == QGraphicsItem.ItemPositionChange:
                wire.prepareGeometryChange()
            elif change == QGraphicsItem.ItemPositionHasChanged:
                if wire.points:
                    ref = wire.points[0]
                    wire.label_offset = QPointF(
                        self.pos().x() - ref.x(),
                        self.pos().y() - ref.y(),
                    )
                wire.update()
        return super().itemChange(change, value)


class WireItem(QGraphicsPathItem):
    """
    A committed wire on the schematic — an ordered polyline of grid-snapped points.
    Points are in scene coordinates (item pos is always (0,0)).

    net_name     : set by the connectivity resolver or an explicit net label.
    display_name : when True, a draggable net-name label is shown.
    label_offset : label position relative to points[0] (survives rubber-banding).

    When selected, filled square handles appear at every vertex.
    Clicking a handle starts a vertex drag; clicking the wire body inserts a
    new vertex at that point and immediately starts dragging it.
    """

    def __init__(self, points: list[QPointF]):
        super().__init__()
        self.points: list[QPointF] = list(points)
        self.net_name: str | None = None
        self.display_name: bool = False
        self.label_offset: QPointF = QPointF(0.0, -_NET_LABEL_OFFSET)
        self.net_locked: bool = False          # True when name is imposed by a port
        self._user_net_name: str | None = None # name saved before port override
        self._net_label: _NetLabel | None = None
        self._label_active: bool = False
        self.setPen(QPen(WIRE_COLOR, WIRE_WIDTH))
        self.setZValue(Z_WIRE)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self._rebuild()

    # ── net label ─────────────────────────────────────────────────────────────

    def update_label(self) -> None:
        """Create, update, or hide the net-name label child item."""
        if self.display_name and self.net_name:
            if self._net_label is None:
                self._net_label = _NetLabel(self)
            self._net_label.setText(self.net_name)
            self._net_label.setVisible(True)
            self._place_label()
        elif self._net_label is not None:
            self._net_label.setVisible(False)

    def _place_label(self) -> None:
        """Position the label at points[0] + label_offset."""
        if self._net_label is None or not self.points:
            return
        ref = self.points[0]
        self._net_label.setPos(ref.x() + self.label_offset.x(),
                               ref.y() + self.label_offset.y())

    # ── bounding rect ─────────────────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        br = super().boundingRect()
        m = HANDLE_SIZE / 2.0
        br = br.adjusted(-m, -m, m, m)
        if self._net_label is not None and self._net_label.isVisible() and self.points:
            br = br.united(self._net_label.mapRectToParent(self._net_label.boundingRect()))
            anchor  = self.points[0]
            lbl_pos = self._net_label.pos()
            m = 3.0
            br = br.united(QRectF(
                min(anchor.x(), lbl_pos.x()) - m,
                min(anchor.y(), lbl_pos.y()) - m,
                abs(anchor.x() - lbl_pos.x()) + 2 * m,
                abs(anchor.y() - lbl_pos.y()) + 2 * m,
            ))
        return br

    # ── hit testing ───────────────────────────────────────────────────────────

    def shape(self) -> QPainterPath:
        s = QPainterPathStroker()
        s.setWidth(_HIT_TOL * 2)
        return s.createStroke(self.path())

    def vertex_near(self, pos: QPointF) -> int | None:
        """Return the index of the vertex within _HIT_TOL of pos, else None."""
        for i, pt in enumerate(self.points):
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) <= _HIT_TOL:
                return i
        return None

    def segment_near(self, pos: QPointF) -> int | None:
        """Return the start-index of the nearest segment within _HIT_TOL, else None."""
        best_d, best_i = _HIT_TOL, None
        for i in range(len(self.points) - 1):
            d = _seg_dist(pos, self.points[i], self.points[i + 1])
            if d < best_d:
                best_d, best_i = d, i
        return best_i

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # prepareGeometryChange() invalidates the scene's spatial index
            # and forces a repaint to be scheduled immediately, so selection
            # handles appear on the same event-loop tick as the click.
            self.prepareGeometryChange()
        return super().itemChange(change, value)

    # ── mutation ──────────────────────────────────────────────────────────────

    def insert_vertex(self, seg_idx: int, pt: QPointF) -> int:
        """Insert pt after seg_idx; returns the new vertex index."""
        self.points.insert(seg_idx + 1, pt)
        self._rebuild()
        return seg_idx + 1

    def move_vertex(self, idx: int, pt: QPointF) -> None:
        self.points[idx] = pt
        self._rebuild()

    def move_points(self, indices: set[int], delta: QPointF) -> None:
        """Shift the points at the given indices by delta (used by rubber-banding)."""
        for i in indices:
            self.points[i] = self.points[i] + delta
        self._rebuild()

    # ── visuals ───────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)

        # Anchor dot + leader line — when wire or its label is active
        if ((option.state & QStyle.State_Selected or self._label_active)
                and self.display_name and self.net_name
                and self._net_label is not None
                and self._net_label.isVisible()
                and self.points):
            painter.save()
            painter.setPen(QPen(NET_LABEL_COLOR, 0.6))
            painter.setBrush(NET_LABEL_COLOR)
            anchor = self.points[0]
            painter.drawLine(anchor, self._net_label.pos())
            painter.drawEllipse(anchor, 2.0, 2.0)
            painter.restore()

        if option.state & QStyle.State_Selected:
            painter.save()
            s = HANDLE_SIZE / 2
            painter.setPen(QPen(HANDLE_COLOR, 0.8))
            painter.setBrush(HANDLE_COLOR)
            for pt in self.points:
                painter.drawRect(QRectF(pt.x() - s, pt.y() - s, HANDLE_SIZE, HANDLE_SIZE))
            painter.restore()

    def _rebuild(self):
        if len(self.points) < 2:
            self.setPath(QPainterPath())
        else:
            path = QPainterPath(self.points[0])
            for pt in self.points[1:]:
                path.lineTo(pt)
            self.setPath(path)
        self._place_label()
