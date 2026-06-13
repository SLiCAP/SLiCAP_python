"""
Annotation drawing shapes: line (polyline), rectangle, circle.

Arrow is no longer a separate kind — it is a Line with line_end_end="arrow".
Old files saved with kind="arrow" are auto-migrated in __init__.

All coordinates are in item-local space (relative to pos()).
pos() is the anchor: first point for line, top-left for rect, centre for circle.
"""
import math

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QBrush

from .config import snap

_SEL_COLOR = QColor(0, 120, 215)

_LINE_STYLES = {
    "solid":    Qt.SolidLine,
    "dashed":   Qt.DashLine,
    "dotted":   Qt.DotLine,
    "dash-dot": Qt.DashDotLine,
}


class ShapeItem(QGraphicsItem):

    def __init__(self, kind: str,
                 rel_points: list,
                 stroke_color:   str   = "#000000",
                 fill_color:     str   = "#ffffff",
                 fill_style:     str   = "none",    # "none" | "solid"
                 line_style:     str   = "solid",   # "solid"|"dashed"|"dotted"|"dash-dot"
                 line_end_start: str   = "none",    # "none"|"arrow"|"dot"|"diamond"
                 line_end_end:   str   = "none",
                 line_width:     float = 1.5,
                 pos: QPointF = QPointF(0, 0)):
        super().__init__()

        # Migrate legacy "arrow" kind
        if kind == "arrow":
            kind = "line"
            line_end_end = "arrow"

        self.kind            = kind
        self.rel_points      = [QPointF(p) for p in rel_points]
        self.stroke_color    = stroke_color
        self.fill_color      = fill_color
        self.fill_style      = fill_style
        self.line_style      = line_style
        self.line_end_start  = line_end_start
        self.line_end_end    = line_end_end
        self.line_width      = line_width
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    # ── geometry ──────────────────────────────────────────────────────────────

    def _content_rect(self) -> QRectF:
        pts = self.rel_points
        if not pts:
            return QRectF()
        if self.kind == "line":
            xs = [p.x() for p in pts]; ys = [p.y() for p in pts]
            return QRectF(min(xs), min(ys),
                          max(xs) - min(xs), max(ys) - min(ys))
        if self.kind == "rect" and len(pts) >= 2:
            x0, y0 = pts[0].x(), pts[0].y()
            x1, y1 = pts[1].x(), pts[1].y()
            return QRectF(min(x0, x1), min(y0, y1),
                          abs(x1 - x0), abs(y1 - y0))
        if self.kind == "circle" and len(pts) >= 2:
            r = math.hypot(pts[1].x(), pts[1].y())
            return QRectF(-r, -r, 2 * r, 2 * r)
        return QRectF()

    def boundingRect(self) -> QRectF:
        m = self.line_width / 2 + 18
        return self._content_rect().adjusted(-m, -m, m, m)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        m = max(6.0, self.line_width + 4)
        path.addRect(self._content_rect().adjusted(-m, -m, m, m))
        return path

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    # ── paint ─────────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, widget=None) -> None:
        pen = QPen(QColor(self.stroke_color), self.line_width)
        pen.setStyle(_LINE_STYLES.get(self.line_style, Qt.SolidLine))
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.fill_style == "solid" and self.kind in ("rect", "circle"):
            painter.setBrush(QBrush(QColor(self.fill_color)))
        else:
            painter.setBrush(Qt.NoBrush)

        pts = self.rel_points
        kind = self.kind

        if kind == "line" and len(pts) >= 2:
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])
            _draw_end(painter, pts[1],  pts[0],  self.line_end_start, self.line_width)
            _draw_end(painter, pts[-2], pts[-1],  self.line_end_end,   self.line_width)

        elif kind == "rect" and len(pts) == 2:
            painter.drawRect(self._content_rect())

        elif kind == "circle" and len(pts) == 2:
            painter.drawEllipse(self._content_rect())

        if option.state & QStyle.State_Selected:
            sel = QPen(_SEL_COLOR, 1.0, Qt.DashLine)
            sel.setCosmetic(True)
            painter.setPen(sel)
            painter.setBrush(Qt.NoBrush)
            r = self._content_rect()
            m = max(3.0, self.line_width)
            painter.drawRect(r.adjusted(-m, -m, m, m))


# ── line-end helpers ──────────────────────────────────────────────────────────

def _draw_end(painter: QPainter, p_from: QPointF, p_to: QPointF,
              style: str, lw: float) -> None:
    if style == "none":
        return
    dx, dy = p_to.x() - p_from.x(), p_to.y() - p_from.y()
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    size = max(16.0, lw * 6)
    ux, uy = dx / length, dy / length

    pen = painter.pen()
    solid_pen = QPen(pen.color(), pen.widthF())
    solid_pen.setJoinStyle(Qt.RoundJoin)
    solid_pen.setCapStyle(Qt.RoundCap)
    painter.setPen(solid_pen)

    if style == "arrow":
        px_, py_ = -uy, ux
        a = QPointF(p_to.x() - size * ux + size * 0.4 * px_,
                    p_to.y() - size * uy + size * 0.4 * py_)
        b = QPointF(p_to.x() - size * ux - size * 0.4 * px_,
                    p_to.y() - size * uy - size * 0.4 * py_)
        painter.drawLine(p_to, a)
        painter.drawLine(p_to, b)

    elif style == "dot":
        r = size * 0.35
        painter.setBrush(QBrush(pen.color()))
        painter.drawEllipse(p_to, r, r)
        painter.setBrush(Qt.NoBrush)

    elif style == "diamond":
        px_, py_ = -uy, ux
        h = size * 0.9
        w = size * 0.4
        tip  = p_to
        back = QPointF(p_to.x() - h * ux, p_to.y() - h * uy)
        left = QPointF(p_to.x() - h/2*ux + w*px_, p_to.y() - h/2*uy + w*py_)
        rght = QPointF(p_to.x() - h/2*ux - w*px_, p_to.y() - h/2*uy - w*py_)
        from PySide6.QtGui import QPolygonF
        poly = QPolygonF([tip, left, back, rght])
        painter.setBrush(QBrush(pen.color()))
        painter.drawPolygon(poly)
        painter.setBrush(Qt.NoBrush)

    painter.setPen(pen)   # restore original pen
