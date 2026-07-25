from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainterPathStroker

from .config import snap, Z_BORDER

DEFAULT_LINE_COLOR = "#5050b4"
DEFAULT_LINE_WIDTH = 0.8
DEFAULT_BG_COLOR   = "#ffffff"

_EDGE_TOL = 5.0    # scene units; matches the shape() hit band
_MIN_SIZE = 10.0


class BorderItem(QGraphicsRectItem):
    """
    Export boundary rectangle.

    When present, SVG/PDF export uses this rect as the viewport instead of
    the items bounding box.  show_in_export controls whether the dashed
    rectangle itself appears in the exported output.

    Sides can be dragged to resize unless the corresponding axis is fixed
    (fixed_w locks the left/right sides, fixed_h the top/bottom sides —
    LaTeX auto-sizing spec, SLNG.md 2026-07-15). The optional background
    fill (bg_alpha > 0) is the bottom layer of the schematic (Z_BORDER is
    below everything).
    """

    def __init__(self, x: float, y: float, width: float, height: float,
                 show_in_export: bool = True,
                 fixed_w: bool = False, fixed_h: bool = False,
                 line_color: str = DEFAULT_LINE_COLOR,
                 line_width: float = DEFAULT_LINE_WIDTH,
                 bg_color: str = DEFAULT_BG_COLOR,
                 bg_alpha: int = 0):
        super().__init__(0.0, 0.0, width, height)
        self.show_in_export: bool = show_in_export
        self.fixed_w: bool = fixed_w
        self.fixed_h: bool = fixed_h
        self.line_color: str = line_color
        self.line_width: float = line_width
        self.bg_color: str = bg_color
        self.bg_alpha: int = bg_alpha          # 0 (transparent) … 100 (opaque)
        self._resize: tuple | None = None      # (ex, ey) during an edge drag
        self.setPos(x, y)
        self.setZValue(Z_BORDER)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.apply_style()

    def apply_style(self):
        self.setPen(QPen(QColor(self.line_color), self.line_width, Qt.DashLine))
        if self.bg_alpha > 0:
            c = QColor(self.bg_color)
            c.setAlpha(round(self.bg_alpha * 255 / 100))
            self.setBrush(QBrush(c))
        else:
            self.setBrush(QBrush(Qt.NoBrush))

    def shape(self) -> QPainterPath:
        """Hit-test only within 5 scene units of the border line — unless a
        background fill is shown, which should not swallow clicks either
        (items inside the border must stay selectable)."""
        r = self.rect()
        outline = QPainterPath()
        outline.addRect(r)
        stroker = QPainterPathStroker()
        stroker.setWidth(2 * _EDGE_TOL)
        return stroker.createStroke(outline)

    # ── edge-drag resize ─────────────────────────────────────────────────

    def _edge_at(self, pos: QPointF) -> tuple:
        """(ex, ey) with ex ∈ {-1,0,1} = left/none/right, ey likewise for
        top/bottom, within the hit band; fixed axes report 0."""
        r = self.rect()
        ex = -1 if abs(pos.x() - r.left()) <= _EDGE_TOL else \
              1 if abs(pos.x() - r.right()) <= _EDGE_TOL else 0
        ey = -1 if abs(pos.y() - r.top()) <= _EDGE_TOL else \
              1 if abs(pos.y() - r.bottom()) <= _EDGE_TOL else 0
        if self.fixed_w:
            ex = 0
        if self.fixed_h:
            ey = 0
        return ex, ey

    def hoverMoveEvent(self, event):
        ex, ey = self._edge_at(event.pos())
        if ex and ey:
            self.setCursor(Qt.SizeFDiagCursor if ex == ey else Qt.SizeBDiagCursor)
        elif ex:
            self.setCursor(Qt.SizeHorCursor)
        elif ey:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)   # drag = move (fixed axes too)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            ex, ey = self._edge_at(event.pos())
            if ex or ey:
                self._resize = (ex, ey)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize is None:
            super().mouseMoveEvent(event)
            return
        ex, ey = self._resize
        # current geometry in scene coordinates
        left   = self.pos().x()
        top    = self.pos().y()
        right  = left + self.rect().width()
        bottom = top + self.rect().height()
        p = snap(event.scenePos())
        if ex == -1:
            left = min(p.x(), right - _MIN_SIZE)
        elif ex == 1:
            right = max(p.x(), left + _MIN_SIZE)
        if ey == -1:
            top = min(p.y(), bottom - _MIN_SIZE)
        elif ey == 1:
            bottom = max(p.y(), top + _MIN_SIZE)
        self.setPos(left, top)
        self.setRect(0.0, 0.0, right - left, bottom - top)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._resize is not None:
            self._resize = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self._resize is None:
            return snap(value)
        return super().itemChange(change, value)
