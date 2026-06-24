import weakref

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from .config import snap

_live_latex_items: weakref.WeakSet = weakref.WeakSet()

_PLACEHOLDER_COLOR = QColor(240, 240, 180)   # light yellow
_PLACEHOLDER_TEXT  = "LaTeX\n(not rendered)"
_SELECTED          = QStyle.State_Selected
_SEL_PEN           = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


def _draw_selection(painter: QPainter, r: QRectF) -> None:
    painter.save()
    painter.setPen(_SEL_PEN)
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(r)
    painter.restore()


def _aspect_fit(renderer, rect: QRectF) -> QRectF:
    """Return a sub-rect of *rect* that preserves the renderer's aspect ratio."""
    vb = renderer.viewBoxF()
    sw = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
    sh = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
    if sw <= 0 or sh <= 0:
        return rect
    scale = min(rect.width() / sw, rect.height() / sh)
    rw = sw * scale
    rh = sh * scale
    return QRectF(
        rect.x() + (rect.width()  - rw) / 2,
        rect.y() + (rect.height() - rh) / 2,
        rw, rh,
    )


class LatexFragmentItem(QGraphicsItem):
    """
    A rendered LaTeX fragment on the canvas.

    Stores the original LaTeX source and preamble path so the dialog can
    re-open them for editing.  The rendered SVG bytes are stored alongside
    the source and are written into the schematic file so the item remains
    visible even on machines where pdflatex / pdf2svg are unavailable.

    display_width / display_height are in scene units.
    Double-click opens the LaTeX fragment dialog to edit and re-render.
    """

    def __init__(self, latex_code: str, preamble_path: str,
                 display_width: int, display_height: int,
                 pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.latex_code:    str        = latex_code
        self.preamble_path: str        = preamble_path
        self._svg_bytes:    bytes | None = None
        self.display_width:  int       = display_width
        self.display_height: int       = display_height
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None
        _live_latex_items.add(self)
        self._load_renderer()

    def rescale(self, ratio: float) -> None:
        self.prepareGeometryChange()
        self.display_width  = max(1, round(self.display_width  * ratio))
        self.display_height = max(1, round(self.display_height * ratio))
        self.update()

    # ── loading ───────────────────────────────────────────────────────────────

    def _load_renderer(self) -> None:
        self._renderer = None
        from .latex_label import LATEX_AVAILABLE
        if LATEX_AVAILABLE and self.latex_code:
            from .latex_label import render_latex_raw
            svg, _err = render_latex_raw(self.latex_code, self.preamble_path)
            if svg:
                self._svg_bytes = svg
        if self._svg_bytes:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QByteArray
            r = QSvgRenderer(QByteArray(self._svg_bytes))
            if r.isValid():
                self._renderer = r

    # ── QGraphicsItem interface ───────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.display_width, self.display_height)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter: QPainter, option, widget=None) -> None:
        r = self.boundingRect()
        if self._renderer is not None:
            self._renderer.render(painter, _aspect_fit(self._renderer, r))
        else:
            painter.fillRect(r, _PLACEHOLDER_COLOR)
            painter.setPen(QColor(100, 100, 60))
            painter.drawText(r, Qt.AlignCenter, _PLACEHOLDER_TEXT)
        if option.state & _SELECTED:
            sel_r = _aspect_fit(self._renderer, r) if self._renderer is not None else r
            _draw_selection(painter, sel_r)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
