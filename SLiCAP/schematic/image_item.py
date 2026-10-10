from pathlib import Path

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QSize, QRectF
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QPen


_PLACEHOLDER_COLOR = QColor(200, 200, 200)

# Physical SVG units in scene units: 90 per inch, the convention of Qt's
# QSvgRenderer.defaultSize() and of the schematic scale 90/25.4 per mm.
_SVG_UNITS = {"": 1.0, "px": 1.0, "pt": 90.0 / 72.0, "pc": 15.0,
              "mm": 90.0 / 25.4, "cm": 900.0 / 25.4, "in": 90.0}


def _svg_length(text):
    import re
    m = re.fullmatch(r"\s*([0-9.eE+-]+)\s*([a-z%]*)\s*", text or "")
    if not m or m.group(2) not in _SVG_UNITS:
        return None
    try:
        return float(m.group(1)) * _SVG_UNITS[m.group(2)]
    except ValueError:
        return None


def natural_size(path):
    """The size of a picture at 100 %, in scene units, as real numbers:
    an SVG by its width and height attributes (its viewBox when they are
    missing), a PDF by its page size in points, a raster image by its
    pixels. None when the file cannot be read. The one authority for the
    image dialog and the image item: Qt's defaultSize() is a whole number,
    and the cut-off fraction made a 25.4 mm high drawing 89 units high
    instead of 90, so it was drawn 1 % too narrow (Anton, 2026-10-10)."""
    path = str(path)
    ext = Path(path).suffix.lower()
    if ext == ".svg":
        try:
            import xml.etree.ElementTree as ET
            root = ET.parse(path).getroot()
        except Exception:
            return None
        w, h = _svg_length(root.get("width")), _svg_length(root.get("height"))
        if w and h and w > 0 and h > 0:
            return w, h
        vb = (root.get("viewBox") or "").replace(",", " ").split()
        if len(vb) == 4:
            try:
                w, h = float(vb[2]), float(vb[3])
            except ValueError:
                return None
            if w > 0 and h > 0:
                return w, h
        return None
    if ext == ".pdf":
        try:
            from PySide6.QtPdf import QPdfDocument
            doc = QPdfDocument(None)
            doc.load(path)
            pt = doc.pagePointSize(0) if doc.pageCount() > 0 else None
            doc.close()
            if pt is not None and pt.width() > 0 and pt.height() > 0:
                return float(pt.width()), float(pt.height())
        except Exception:
            pass
        return None
    from PySide6.QtGui import QImageReader
    size = QImageReader(path).size()
    if size.isValid() and size.width() > 0 and size.height() > 0:
        return float(size.width()), float(size.height())
    return None
_SELECTED          = QStyle.State_Selected
_SEL_PEN           = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


class ImageItem(QGraphicsItem):
    """
    An image on the canvas, loaded from a file path.

    SVG files are rendered via QSvgRenderer at full vector quality.
    PDF files are rasterised via QPdfDocument.
    All other formats are loaded directly as a QPixmap.

    The size of the picture is its natural size (``natural_size``) times
    ``size_scale`` (1.0 = 100 %), computed from the CURRENT file on every
    load: a linked drawing that changes size keeps its scale and its
    proportions, and no fraction is lost to whole units (Anton, 2026-10-10:
    an absolute box of 425 x 89 units made a 425.2 x 90 drawing 1 %
    narrower). display_width / display_height are in scene units: the box
    the picture is fitted into (aspect ratio kept). Without a scale (an
    image whose file cannot be read, or an old box that is not a whole
    percentage of the file) the stored box is used as it is.  The picture itself is kept at its
    own resolution and scaled at paint time, so it is sharp at every zoom
    (Anton, 2026-09-27: a picture shown at 5 % was reduced to that many
    pixels and blurred when zoomed in).  The image is reloaded from disk each
    time from_data() restores the scene and after every run of the
    instruction file (SchematicScene.reload_links), so the canvas stays in
    sync with the source file: a plot written by a simulation is a link.

    file_path is the stored link: relative to the project root when the
    file lies inside the project (project.relative_to_root), absolute
    otherwise; ``path`` resolves it.

    Double-click opens a dialog to change the file or resize.
    """

    def __init__(self, file_path: str, display_width: float, display_height: float,
                 pos: QPointF = QPointF(0, 0), link: str = "",
                 size_scale: float | None = None):
        super().__init__()
        self.file_path: str      = file_path
        # A LINK item shows something of the project by NAME and follows it:
        # "figure:<name>", a figure object of the Design data (the run
        # manifest), whose image is re-derived from the manifest on every
        # load and reload (Anton, 2026-10-06: the Variable pane is the
        # source, not the instruction file - that was tried first and
        # REPLACED); "schematic:<source path>" (sch/x.slicap_sch,
        # lib/y.spice_sch; a bare name in older files) and "poster:<name>",
        # a drawing of the project, shown as its export img/<stem>.svg,
        # which the export of a poster brings up to date first. A plain
        # image has no link.
        self.link: str           = link or ""
        self._box                = (float(display_width), float(display_height))
        self.size_scale: float | None = size_scale
        self._natural: tuple | None   = None
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None          # QSvgRenderer for SVG files
        self._pixmap: QPixmap | None = None  # QPixmap for raster / PDF
        self._loaded_mtime: float | None = None
        self._load()
        if self.size_scale is None:
            self.size_scale = self._scale_of_box()

    # ── size ─────────────────────────────────────────────────────────────────

    def _scale_of_box(self):
        """The scale of an old absolute box: the whole percentage that the
        image dialog rounded to, when the box is that percentage of the
        file's natural size within one unit (the dialog's rounding); None
        for a box that is not (kept as it is)."""
        if not self._natural:
            return None
        nw, nh = self._natural
        w, h = self._box
        pct = round(w / nw * 100)
        if pct >= 1 and abs(nw * pct / 100 - w) <= 1.0 and abs(nh * pct / 100 - h) <= 1.0:
            return pct / 100
        return None

    def _size(self):
        if self.size_scale is not None and self._natural:
            return self._natural[0] * self.size_scale, self._natural[1] * self.size_scale
        return self._box

    @property
    def display_width(self) -> float:
        return self._size()[0]

    @display_width.setter
    def display_width(self, value) -> None:
        self.prepareGeometryChange()
        self._box = (float(value), self._size()[1])
        self.size_scale = None

    @property
    def display_height(self) -> float:
        return self._size()[1]

    @display_height.setter
    def display_height(self, value) -> None:
        self.prepareGeometryChange()
        self._box = (self._size()[0], float(value))
        self.size_scale = None

    def set_size_scale(self, scale: float) -> None:
        """Set the scale (1.0 = 100 %); the size follows the file."""
        self.prepareGeometryChange()
        self._box = self._size()
        self.size_scale = float(scale)

    # ── loading ───────────────────────────────────────────────────────────────

    @property
    def path(self) -> Path:
        """The linked file, resolved from the project root."""
        from . import project
        return project.resolve_from_root(self.file_path)

    def _file_mtime(self):
        try:
            return self.path.stat().st_mtime
        except OSError:
            return None

    @property
    def link_kind(self) -> str:
        return self.link.split(":", 1)[0] if ":" in self.link else ""

    @property
    def link_name(self) -> str:
        return self.link.split(":", 1)[1] if ":" in self.link else ""

    @property
    def link_stem(self) -> str:
        """The stem of the linked drawing: the name of its export."""
        from pathlib import PurePosixPath
        return PurePosixPath(self.link_name).stem if self.link_name else ""

    def _resolve_figure(self) -> bool:
        """A link item takes its image from what it links: a figure from the
        Design data, a schematic or poster from the export of that drawing;
        True when the link's file changed. Without a manifest entry (no run
        yet, or a figure renamed away) the stored link stays."""
        kind, name = self.link_kind, self.link_name
        if not kind:
            return False
        new = None
        if kind == "figure":
            from . import project
            from .design_data import manifest_figures
            new = dict(manifest_figures(project.project_root())).get(name)
        elif kind in ("schematic", "poster"):
            from . import project
            new = project.folder_rel("img") + "/" + self.link_stem + ".svg"
        if new and new != self.file_path:
            self.file_path = new
            return True
        return False

    def reload_if_changed(self) -> bool:
        """Reload the picture when the linked file changed on disk since it
        was loaded (a simulation rewrote a plot), or when a Figure's image
        in the Design data is another file; True when it did."""
        if not self._resolve_figure() and self._file_mtime() == self._loaded_mtime:
            return False
        self.prepareGeometryChange()       # the size follows the file
        self._load()
        self.update()
        return True

    def _load(self) -> None:
        self._resolve_figure()
        path = str(self.path)
        ext = Path(path).suffix.lower()
        self._natural = natural_size(path)
        bw, bh = self._size()
        w, h = max(1, round(bw)), max(1, round(bh))
        self._loaded_mtime = self._file_mtime()

        if ext == ".svg":
            from PySide6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(path)
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
            px = QPixmap(path)
            if px.isNull():
                px = self._placeholder(w, h)
            self._renderer = None
            self._pixmap   = px            # full resolution; scaled when drawn

    def _load_pdf(self, w: int, h: int) -> QPixmap:
        try:
            from PySide6.QtPdf import QPdfDocument
            doc = QPdfDocument(None)
            doc.load(str(self.path))
            if doc.pageCount() < 1:
                doc.close()
                return self._placeholder(w, h)
            pt = doc.pagePointSize(0)
            if pt.width() <= 0:
                doc.close()
                return self._placeholder(w, h)
            # Rasterise the page once at a fixed resolution (4 px per point,
            # about 290 dpi, at most 4000 px wide); it is scaled when drawn.
            px_per_pt = min(4.0, 4000.0 / pt.width())
            img_w = max(1, round(pt.width()  * px_per_pt))
            img_h = max(1, round(pt.height() * px_per_pt))
            qimg  = doc.render(0, QSize(img_w, img_h))
            doc.close()
            return QPixmap.fromImage(qimg)
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

    def picture_rect(self, box: QRectF | None = None) -> QRectF:
        """The rect the picture fills inside *box* (the display box by
        default): the largest rect of the picture's aspect ratio, centred."""
        r = self.boundingRect() if box is None else box
        if self._renderer is not None:
            vb = self._renderer.viewBoxF()
            sw, sh = (vb.width(), vb.height()) if vb.width() > 0 and vb.height() > 0 \
                else (self._renderer.defaultSize().width(), self._renderer.defaultSize().height())
        elif self._pixmap is not None and not self._pixmap.isNull():
            sw, sh = self._pixmap.width(), self._pixmap.height()
        else:
            return r
        if sw <= 0 or sh <= 0:
            return r
        sc = min(r.width() / sw, r.height() / sh)
        w, h = sw * sc, sh * sc
        return QRectF(r.x() + (r.width() - w) / 2, r.y() + (r.height() - h) / 2, w, h)

    def paint_picture(self, painter: QPainter, box: QRectF | None = None) -> None:
        """Draw the picture fitted into *box* (the display box by default),
        scaled from its own resolution; shared by paint() and the embedding
        of an image into a symbol."""
        target = self.picture_rect(box)
        if self._renderer is not None:
            self._renderer.render(painter, target)
        elif self._pixmap is not None and not self._pixmap.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
        else:
            painter.fillRect(target, _PLACEHOLDER_COLOR)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        r = self.boundingRect()
        self.paint_picture(painter, r)
        if option.state & _SELECTED:
            painter.save()
            painter.setPen(_SEL_PEN)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(r)
            painter.restore()

    @property
    def SNAPS_TO_GRID(self) -> bool:
        """An image or a figure is an annotation and moves freely (see
        canvas._FREE_PLACEMENT_MODES). A linked DRAWING snaps like a shape:
        the grid, or the fine grid under Shift (config.snap_pos), since it
        shares the grid of the poster it is placed on (Anton, 2026-10-09).
        The group drag reads the same flag."""
        return self.link_kind in ("schematic", "poster")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            from .config import snap_pos
            return snap_pos(self, value)     # the one snapping rule
        return super().itemChange(change, value)
