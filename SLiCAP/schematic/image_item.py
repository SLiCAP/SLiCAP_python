from pathlib import Path

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QSize, QRectF
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QPen

from .config import snap

_PLACEHOLDER_COLOR = QColor(200, 200, 200)
_SELECTED          = QStyle.State_Selected
_SEL_PEN           = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


class ImageItem(QGraphicsItem):
    """
    An image on the canvas, loaded from a file path.

    SVG files are rendered via QSvgRenderer at full vector quality.
    PDF files are rasterised via QPdfDocument.
    All other formats are loaded directly as a QPixmap.

    display_width / display_height are in scene units.  The image is
    reloaded from disk each time from_data() restores the scene, so the
    canvas stays in sync with the source file.

    Double-click opens a dialog to change the file or resize.
    """

    def __init__(self, file_path: str, display_width: int, display_height: int,
                 pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.file_path: str      = file_path
        self.display_width: int  = display_width
        self.display_height: int = display_height
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None          # QSvgRenderer for SVG files
        self._pixmap: QPixmap | None = None  # QPixmap for raster / PDF
        self._load()

    # ── loading ───────────────────────────────────────────────────────────────

    def _load(self) -> None:
        ext = Path(self.file_path).suffix.lower()
        w, h = max(1, self.display_width), max(1, self.display_height)

        if ext == ".svg":
            from PySide6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(self.file_path)
            if renderer.isValid():
                self._renderer = renderer
                self._pixmap   = None
                return
            self._renderer = None
            self._pixmap   = self._placeholder(w, h)
        elif ext == ".pdf":
            self._renderer = None
            self._pixmap   = self._load_pdf(w, h)
        else:
            px = QPixmap(self.file_path)
            if px.isNull():
                px = self._placeholder(w, h)
            else:
                px = px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._renderer = None
            self._pixmap   = px

    def _load_pdf(self, w: int, h: int) -> QPixmap:
        try:
            from PySide6.QtPdf import QPdfDocument
            doc = QPdfDocument(None)
            doc.load(self.file_path)
            if doc.pageCount() < 1:
                doc.close()
                return self._placeholder(w, h)
            pt = doc.pagePointSize(0)
            if pt.width() <= 0:
                doc.close()
                return self._placeholder(w, h)
            # Render at 2× display size for crispness, then downscale
            scale = w / pt.width()
            img_w = max(1, round(pt.width()  * scale * 2))
            img_h = max(1, round(pt.height() * scale * 2))
            qimg  = doc.render(0, QSize(img_w, img_h))
            doc.close()
            return QPixmap.fromImage(qimg).scaled(
                w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        except Exception:
            return self._placeholder(w, h)

    @staticmethod
    def _placeholder(w: int, h: int) -> QPixmap:
        px = QPixmap(w, h)
        px.fill(_PLACEHOLDER_COLOR)
        return px

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
            self._renderer.render(painter, r)
        elif self._pixmap is not None:
            px = self._pixmap
            # Centre in bounding rect (pixmap may be smaller due to aspect ratio)
            x_off = (r.width()  - px.width())  / 2
            y_off = (r.height() - px.height()) / 2
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(int(x_off), int(y_off), px)
        else:
            painter.fillRect(r, _PLACEHOLDER_COLOR)
        if option.state & _SELECTED:
            painter.save()
            painter.setPen(_SEL_PEN)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(r)
            painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
