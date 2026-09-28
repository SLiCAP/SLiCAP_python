"""
Annotation drawing shapes: line (polyline), rectangle, ellipse, polygon.

One model for all four kinds (Anton, 2026-09-27): a points list, a stroke
(with style "none": a filled shape without contour), a fill, a rotation angle
about the shape's centre, and for lines two line ends whose arrow head is a
filled polygon without contour of a given width and length (defaults as the
current-source arrow of the symbol library: 4 wide, 6 long).

Legacy kinds are migrated in __init__: "arrow" (a line with an arrow end) and
"circle" (centre + radius vector) which becomes an ellipse defined by the two
corners of its bounding rectangle. Scaling is NOT a separate attribute: the
points define the size, dragging them scales; rotation is the one attribute
that the points cannot express (considered and REJECTED as scale_x/scale_y,
2026-09-27: it would encode the geometry twice).

All coordinates are in item-local space (relative to pos()).
pos() is the anchor: first point for line and polygon, first corner for rect
and ellipse.
"""
import math

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QBrush, QPolygonF

from .config import snap, snap_pos, snap_fine, shift_held, display_color

_SEL_COLOR = QColor(0, 120, 215)

_LINE_STYLES = {
    "solid":    Qt.SolidLine,
    "dashed":   Qt.DashLine,
    "dotted":   Qt.DotLine,
    "dash-dot": Qt.DashDotLine,
}

KINDS_WITH_FILL = ("rect", "ellipse", "polygon")
DEFAULT_HEAD_WIDTH  = 4.0
DEFAULT_HEAD_LENGTH = 6.0


class ShapeItem(QGraphicsItem):

    def __init__(self, kind: str,
                 rel_points: list,
                 stroke_color:   str   = "#000000",
                 fill_color:     str   = "#ffffff",
                 fill_style:     str   = "none",    # "none" | "solid"
                 line_style:     str   = "solid",   # "none"|"solid"|"dashed"|"dotted"|"dash-dot"
                 line_end_start: str   = "none",    # "none"|"arrow"|"dot"|"diamond"
                 line_end_end:   str   = "none",
                 line_width:     float = 1.5,
                 pos: QPointF = QPointF(0, 0),
                 rotation:    float = 0.0,          # degrees about the centre
                 head_width:  float = DEFAULT_HEAD_WIDTH,
                 head_length: float = DEFAULT_HEAD_LENGTH):
        super().__init__()
        rel_points = [QPointF(p) for p in rel_points]

        # Migrate legacy kinds
        if kind == "arrow":
            kind = "line"
            line_end_end = "arrow"
        if kind == "circle" and len(rel_points) >= 2:
            r = math.hypot(rel_points[1].x(), rel_points[1].y())
            rel_points = [QPointF(-r, -r), QPointF(r, r)]
            kind = "ellipse"

        self.kind            = kind
        self.rel_points      = rel_points
        self.stroke_color    = stroke_color
        self.fill_color      = fill_color
        self.fill_style      = fill_style
        self.line_style      = line_style
        self.line_end_start  = line_end_start
        self.line_end_end    = line_end_end
        self.line_width      = line_width
        self.head_width      = head_width
        self.head_length     = head_length
        self.rotation        = rotation
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.apply_rotation()

    # ── geometry ──────────────────────────────────────────────────────────────

    def _content_rect(self) -> QRectF:
        pts = self.rel_points
        if not pts:
            return QRectF()
        if self.kind in ("line", "polygon"):
            xs = [p.x() for p in pts]; ys = [p.y() for p in pts]
            return QRectF(min(xs), min(ys),
                          max(xs) - min(xs), max(ys) - min(ys))
        if self.kind in ("rect", "ellipse") and len(pts) >= 2:
            x0, y0 = pts[0].x(), pts[0].y()
            x1, y1 = pts[1].x(), pts[1].y()
            return QRectF(min(x0, x1), min(y0, y1),
                          abs(x1 - x0), abs(y1 - y0))
        return QRectF()

    def centre(self) -> QPointF:
        return self._content_rect().center()

    def apply_rotation(self) -> None:
        """Rotate the item about the centre of its content (call after the
        rotation or the points changed)."""
        self.prepareGeometryChange()
        self.setTransformOriginPoint(self.centre())
        self.setRotation(self.rotation)

    def select_rect(self) -> QRectF:
        """The extent the rubber band tests (canvas._rb_keep_item): the
        geometry plus the stroke and, for a line with heads, the head. A
        generous padding made a small head impossible to enclose (Anton,
        2026-09-27)."""
        m = (self.line_width / 2 if self.line_style != "none" else 0.0) + 0.5
        if self.kind == "line" and (self.line_end_start != "none" or self.line_end_end != "none"):
            m += max(self.head_length, self.head_width) / 2
        return self._content_rect().adjusted(-m, -m, m, m)

    def boundingRect(self) -> QRectF:
        m = self.HANDLE + 1.0          # room for the selection dots and cross
        return self.select_rect().adjusted(-m, -m, m, m)

    def _outline(self) -> QPainterPath:
        """The drawn geometry as a path (open polyline for a line)."""
        pts, path = self.rel_points, QPainterPath()
        if self.kind == "line" and len(pts) >= 2:
            path.moveTo(pts[0])
            for q in pts[1:]:
                path.lineTo(q)
        elif self.kind == "polygon" and len(pts) >= 3:
            path.addPolygon(QPolygonF(pts)); path.closeSubpath()
        elif self.kind == "rect" and len(pts) == 2:
            path.addRect(self._content_rect())
        elif self.kind == "ellipse" and len(pts) == 2:
            path.addEllipse(self._content_rect())
        return path

    def shape(self) -> QPainterPath:
        """Hit area = the geometry: a band along the stroke, plus the area of
        a filled shape, plus the handles when selected. The padded bounding
        box used before made a polyline win clicks on its neighbours
        (Anton, 2026-09-27)."""
        from PySide6.QtGui import QPainterPathStroker
        outline = self._outline()
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.line_width, 1.0) + 4.0)
        hit = stroker.createStroke(outline)
        if self.fill_style == "solid" and self.kind in KINDS_WITH_FILL:
            hit = hit.united(outline)
        if self.isSelected():
            h = self.HANDLE_HIT
            for q in self._handles():
                hit.addRect(QRectF(q.x() - h, q.y() - h, 2 * h, 2 * h))
        # winding, not even-odd: a handle square overlapping the stroke band
        # must not cancel it (the vertex itself was then outside, 2026-09-27)
        hit.setFillRule(Qt.WindingFill)
        return hit

    def hit_exact(self, local: QPointF) -> bool:
        """True when the point lies on the drawn geometry itself: on the
        stroke (its real width, at least 1 unit) or inside a filled shape.
        The tolerance band of shape() is for convenience only."""
        from PySide6.QtGui import QPainterPathStroker
        outline = self._outline()
        if self.fill_style == "solid" and self.kind in KINDS_WITH_FILL and outline.contains(local):
            return True
        if self.line_style == "none":
            return False
        stroker = QPainterPathStroker(); stroker.setWidth(max(self.line_width, 1.0) + 0.6)
        return stroker.createStroke(outline).contains(local)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            ref = getattr(self, "_snap_ref", None)
            if ref is not None:
                # snap the vertex nearest to the grab point, not the anchor
                fn = snap_fine if shift_held() else snap
                return fn(QPointF(value.x() + ref.x(), value.y() + ref.y())) - ref
            return snap_pos(self, value)
        return super().itemChange(change, value)

    # ── vertex editing (handles on the selected shape) ──────────────────────

    HANDLE = 2.5          # painting margin for the selection marks
    HANDLE_HIT = 1.8      # a press within this distance of a vertex dot is a
                          # vertex press; larger, and a press inside a small
                          # polygon reshaped it instead of moving it (2026-09-27)

    def _handles(self) -> list:
        """Editable points in local coordinates: the points of a line or
        polygon, the two corners of a rect or ellipse."""
        return list(self.rel_points)

    def _handle_at(self, local: QPointF):
        tol = self.HANDLE_HIT
        for i, p in enumerate(self._handles()):
            if abs(p.x() - local.x()) <= tol and abs(p.y() - local.y()) <= tol:
                return i
        return None

    def mousePressEvent(self, event):
        self._vertex = None
        self._snap_ref = None
        if self.isSelected() and event.button() == Qt.LeftButton:
            i = self._handle_at(event.pos())
            if i is not None:
                sc = self.scene()
                if sc is not None and hasattr(sc, "_push_undo"):
                    sc._push_undo()
                self._vertex = i
                event.accept()
                return
        if event.button() == Qt.LeftButton:
            sc = self.scene()
            others = [o for o in (sc.items(event.scenePos()) if sc is not None else [])
                      if o is not self and isinstance(o, ShapeItem)]
            # A vertex handle of a SELECTED shape wins every press: a handle
            # of the arrow head under the band of the emitter line must
            # reshape the head, not grab the line (Anton, 2026-09-27).
            if any(o.isSelected() and o._handle_at(o.mapFromScene(event.scenePos())) is not None for o in others):
                event.ignore()
                return
            if not self.hit_exact(event.pos()):
                # Only the tolerance band was hit: if another shape under the
                # cursor is hit on its real geometry, let the press pass on to
                # it (Qt hands an ignored press to the next item below).
                if any(o.hit_exact(o.mapFromScene(event.scenePos())) for o in others):
                    event.ignore()
                    return
        if event.button() == Qt.LeftButton and self.rel_points:
            # the vertex nearest to the grab point is the snap reference of the move
            p = event.pos()
            self._snap_ref = QPointF(min(self.rel_points, key=lambda q: (q.x() - p.x()) ** 2 + (q.y() - p.y()) ** 2))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_vertex", None) is not None:
            p = event.pos()
            fn = snap_fine if shift_held() else snap
            p = self.mapFromScene(fn(self.mapToScene(p)))
            self.prepareGeometryChange()
            self.rel_points[self._vertex] = QPointF(p)
            self.apply_rotation()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._snap_ref = None
        if getattr(self, "_vertex", None) is not None:
            self._vertex = None
            sc = self.scene()
            if sc is not None and hasattr(sc, "data_changed"):
                sc.data_changed.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── paint ─────────────────────────────────────────────────────────────────

    def _pen(self) -> QPen:
        if self.line_style == "none":
            return QPen(Qt.NoPen)
        pen = QPen(display_color(self.stroke_color), self.line_width)
        pen.setStyle(_LINE_STYLES.get(self.line_style, Qt.SolidLine))
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        return pen

    def paint(self, painter: QPainter, option, widget=None) -> None:
        selected = bool(option.state & QStyle.State_Selected)
        pen = self._pen()
        if selected:
            # a selected shape shows itself in the selection colour; no box
            # around it, small dots at the vertices, a cross on the active
            # point (Anton, 2026-09-27: squares covered the line ends)
            pen = QPen(pen); pen.setColor(_SEL_COLOR)
            if pen.style() == Qt.NoPen:
                pen = QPen(_SEL_COLOR, 0.6)
        painter.setPen(pen)
        if self.fill_style == "solid" and self.kind in KINDS_WITH_FILL:
            painter.setBrush(QBrush(display_color(self.fill_color)))
        else:
            painter.setBrush(Qt.NoBrush)

        pts = self.rel_points
        kind = self.kind

        if kind == "line" and len(pts) >= 2:
            shaft = shaft_points(pts, self.line_end_start, self.line_end_end,
                                 self.head_length)
            for i in range(len(shaft) - 1):
                painter.drawLine(shaft[i], shaft[i + 1])
            color = display_color(self.stroke_color)   # heads and dots as the stroke
            _draw_end(painter, pts[1],  pts[0],  self.line_end_start,
                      self.head_width, self.head_length, color)
            _draw_end(painter, pts[-2], pts[-1],  self.line_end_end,
                      self.head_width, self.head_length, color)

        elif kind == "rect" and len(pts) == 2:
            painter.drawRect(self._content_rect())

        elif kind == "ellipse" and len(pts) == 2:
            painter.drawEllipse(self._content_rect())

        elif kind == "polygon" and len(pts) >= 3:
            painter.drawPolygon(QPolygonF(pts))

        if selected:
            painter.setRenderHint(QPainter.Antialiasing)
            active = None
            if getattr(self, "_vertex", None) is not None:
                active = self._handles()[self._vertex]
            elif getattr(self, "_snap_ref", None) is not None:
                active = self._snap_ref
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(_SEL_COLOR))
            for p in self._handles():          # vertex dots: drag one to reshape
                painter.drawEllipse(p, 1.0, 1.0)
            if active is not None:             # the active point: a dark cross
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.drawLine(QPointF(active.x() - 2.5, active.y()), QPointF(active.x() + 2.5, active.y()))
                painter.drawLine(QPointF(active.x(), active.y() - 2.5), QPointF(active.x(), active.y() + 2.5))


# ── line-end helpers (shared with the SVG export) ───────────────────────────

def _unit(p_from, p_to):
    dx, dy = p_to.x() - p_from.x(), p_to.y() - p_from.y()
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    return dx / length, dy / length


def head_polygon(p_from: QPointF, p_to: QPointF, style: str,
                 head_width: float, head_length: float):
    """Points of the filled head at p_to (pointing away from p_from), or None:
    "arrow" a triangle of the given width and length, "diamond" a rhombus of
    the given width and length. "dot" is a circle, see head_dot."""
    u = _unit(p_from, p_to)
    if u is None or style not in ("arrow", "diamond"):
        return None
    ux, uy = u
    px_, py_ = -uy, ux
    w = head_width / 2
    if style == "arrow":
        base = QPointF(p_to.x() - head_length * ux, p_to.y() - head_length * uy)
        return [p_to,
                QPointF(base.x() + w * px_, base.y() + w * py_),
                QPointF(base.x() - w * px_, base.y() - w * py_)]
    back = QPointF(p_to.x() - head_length * ux, p_to.y() - head_length * uy)
    mid  = QPointF(p_to.x() - head_length / 2 * ux, p_to.y() - head_length / 2 * uy)
    return [p_to,
            QPointF(mid.x() + w * px_, mid.y() + w * py_),
            back,
            QPointF(mid.x() - w * px_, mid.y() - w * py_)]


def shaft_points(pts, end_start: str, end_end: str, head_length: float):
    """The polyline to stroke: shortened by the head length at an arrow or
    diamond end, so that the round line cap does not show beyond the tip."""
    shaft = [QPointF(p) for p in pts]
    if end_start in ("arrow", "diamond"):
        u = _unit(pts[1], pts[0])
        if u is not None:
            shaft[0] = QPointF(pts[0].x() - head_length * u[0], pts[0].y() - head_length * u[1])
    if end_end in ("arrow", "diamond"):
        u = _unit(pts[-2], pts[-1])
        if u is not None:
            shaft[-1] = QPointF(pts[-1].x() - head_length * u[0], pts[-1].y() - head_length * u[1])
    return shaft


def _draw_end(painter: QPainter, p_from: QPointF, p_to: QPointF, style: str,
              head_width: float, head_length: float, color: QColor) -> None:
    """Filled head without contour: arrow and diamond as polygons, dot as a
    circle of the head width."""
    if style == "none":
        return
    saved_pen, saved_brush = painter.pen(), painter.brush()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color))
    if style == "dot":
        r = head_width / 2
        painter.drawEllipse(p_to, r, r)
    else:
        poly = head_polygon(p_from, p_to, style, head_width, head_length)
        if poly:
            painter.drawPolygon(QPolygonF(poly))
    painter.setPen(saved_pen)
    painter.setBrush(saved_brush)
