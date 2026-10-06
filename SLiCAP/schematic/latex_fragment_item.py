from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from .config import style_of

_PLACEHOLDER_COLOR = QColor(240, 240, 180)   # light yellow
_PLACEHOLDER_TEXT  = "LaTeX\n(not rendered)"
_NUMBERED = ("equation", "align", "gather", "multline", "eqnarray", "flalign")


def unnumbered(code: str) -> str:
    """The snippet as a schematic renders it: numbered display environments
    become their starred forms. A numbered equation is typeset at the full
    line width with its "(1)" (284 units for a one-line transfer, the
    unnumbered form 86), and a schematic has no equation numbers to refer
    to (2026-10-06). The snippet FILE is never changed: in the report it
    keeps its number."""
    import re
    for env in _NUMBERED:
        code = re.sub(r"\\(begin|end)\{%s\}" % env, r"\\\1{%s*}" % env, code)
    return code
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

    *color* ("" = the document black) tints the render the way a symbol's
    LaTeX labels are tinted: the black of the stored SVG is replaced on the
    canvas and in the export (latex_label.recolor_svg), the stored bytes
    stay black. A colour written inside the LaTeX code is left alone
    (Anton, 2026-10-06). A \\color command in the preamble was considered
    and REJECTED: it re-renders on every colour change and ties the colour
    to the render cache.
    """
    SNAPS_TO_GRID = False   # an annotation: placed and dragged freely (canvas: group move, _FREE_PLACEMENT_MODES)

    def __init__(self, latex_code: str, preamble_path: str,
                 display_width: int, display_height: int,
                 pos: QPointF = QPointF(0, 0), color: str = "",
                 snippet: str = ""):
        super().__init__()
        self.latex_code:    str        = latex_code
        self.preamble_path: str        = preamble_path
        self.color:         str        = color or ""
        # A SNIPPET item links a LaTeX snippet object by its NAME in the
        # Design data (the run manifest, which records the snippet's text):
        # the code is taken from there on load and after every run; a saved
        # file is not needed. Scale and colour are the item's own (Anton,
        # 2026-10-06). Reading tex/SLiCAPdata/<name>.tex by save name was
        # tried first and REPLACED: the Variable pane is the source.
        self.snippet:       str        = snippet or ""
        self._svg_bytes:    bytes | None = None
        self.display_width:  int       = display_width
        self.display_height: int       = display_height
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None
        self._load_renderer()

    # ── loading ───────────────────────────────────────────────────────────────

    def _resolve_snippet(self) -> bool:
        """A snippet item takes its LaTeX from the Design data (the run
        manifest records the snippet's text); True when the text changed.
        Without an entry (no run yet) the stored text stays, so the item
        still renders and exports."""
        if not self.snippet:
            return False
        from . import project
        from .design_data import manifest_snippets
        code = dict(manifest_snippets(project.project_root())).get(self.snippet)
        if code is not None and code != self.latex_code:
            self.latex_code = code
            return True
        return False

    def reload_if_changed(self) -> bool:
        """Re-render a snippet item whose text in the Design data changed
        (a run rewrote it); True when it did. A typed fragment never
        changes this way."""
        if not self._resolve_snippet():
            return False
        self.prepareGeometryChange()
        self._load_renderer()
        self.update()
        return True

    def _load_renderer(self) -> None:
        self._renderer = None
        self._resolve_snippet()
        from .latex_label import LATEX_INSTALLED
        # Fresh rendering needs the tools AND the owning schematic's preference;
        # before the item is in a scene only stored bytes are used (the scene-
        # entry hook re-runs this with the real style).
        if (self.scene() is not None and LATEX_INSTALLED
                and style_of(self).LATEX_RENDERING_ENABLED and self.latex_code):
            from .latex_label import cache_dir_of, render_latex_raw
            code = unnumbered(self.latex_code) if self.snippet else self.latex_code
            svg, _err = render_latex_raw(code, self.preamble_path,
                                         cache_dir=cache_dir_of(self))
            if svg:
                self._svg_bytes = svg
        if self._svg_bytes:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QByteArray
            from .latex_label import display_svg
            r = QSvgRenderer(QByteArray(self.display_bytes()))
            if r.isValid():
                self._renderer = r

    def display_bytes(self) -> bytes:
        """The SVG as drawn on the canvas: tinted in the item's own colour
        (theme-adjusted like a shape's stroke), else the theme's rendering
        of the document black."""
        from .latex_label import display_svg, recolor_svg
        from .config import display_color
        if self.color:
            return recolor_svg(self._svg_bytes, display_color(self.color).name())
        return display_svg(self._svg_bytes, self)

    def export_bytes(self) -> bytes:
        """The SVG the export inlines: the document black, or the own colour."""
        from .latex_label import recolor_svg
        return recolor_svg(self._svg_bytes, self.color) if self.color else self._svg_bytes

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
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self.prepareGeometryChange()
            self._load_renderer()
            self.update()
        # No grid snap: an annotation (see canvas._FREE_PLACEMENT_MODES).
        return super().itemChange(change, value)
