from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF, QByteArray
from PySide6.QtGui import QPainterPath, QFontMetricsF, QColor, QPen
from PySide6.QtSvg import QSvgRenderer

from .config import snap, style_of, default_style

_SEL_PEN = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


class AnalysisItem(QGraphicsItem):
    """
    SLiCAP analysis setup block: .source / .detector / .lgref commands.
    Stores structured data; double-click reopens the dialog for editing.

    Display: with "LaTeX rendering" enabled the block is typeset as a single
    LaTeX SVG — the keywords in ``{\\footnotesize \\textsf{}}`` (like a component
    parameter name), the source/lgref refdesses and the detector names as math
    symbols (:func:`SLiCAP.SLiCAPlatex.symbolLatex`).  Otherwise the block is
    painted as plain multi-line text.  The leading '.' is shown only in the
    netlist (:meth:`commands`), not on the canvas.

    This is a plain ``QGraphicsItem`` (not a ``QGraphicsTextItem``): it paints
    the SVG or the text itself, so re-rendering never mutates a text document
    from inside ``itemChange`` — the scene-entry hook can safely re-render on
    add (mirrors :class:`ModelItem` / :class:`ParameterItem`).
    """

    def __init__(self,
                 source:   list,   # 0-2 independent source refdes strings
                 detector: list,   # 0-2 [type, ref] pairs; type = "V" or "I"
                 lgref:    list,   # 0-2 dependent source refdes strings
                 pos: QPointF = QPointF(0, 0),
                 show: bool = True):
        super().__init__()
        self.source   = list(source)
        self.detector = [list(d) for d in detector]
        self.lgref    = list(lgref)
        # "Show on schematic" (Anton, 2026-07-11): a hidden item stays in
        # the scene and is ALWAYS netlisted; only drawing and image export
        # are suppressed.
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)
        self.setPos(pos)
        self._renderer  = None             # LaTeX-rendered block, or None (plain text)
        self._svg_rect  = QRectF()
        self._svg_bytes = b""              # kept for SVG export
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._load_renderer()

    def set_show(self, show: bool) -> None:
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)

    # ── content ────────────────────────────────────────────────────────────────
    def _blocks(self):
        """[(keyword_without_dot, [item_strings]), ...] for the three commands."""
        src = [r.strip() for r in self.source if r.strip()]
        det = [f"{t}_{r.strip()}" for t, r in self.detector if r.strip()]
        lg  = [r.strip() for r in self.lgref if r.strip()]
        return [("source", src), ("detector", det), ("lgref", lg)]

    def commands(self) -> list:
        """Netlist lines — WITH the leading dot."""
        return ["." + kw + " " + " ".join(items)
                for kw, items in self._blocks() if items]

    def _plain_display(self) -> str:
        """Canvas plain-text — WITHOUT the leading dot."""
        lines = [(kw + " " + " ".join(items)).rstrip()
                 for kw, items in self._blocks() if items]
        return "\n".join(lines) if lines else "source\ndetector\nlgref"

    def toPlainText(self) -> str:
        """Plain-text form (used by the SVG exporter's text block)."""
        return self._plain_display()

    def _latex_block(self) -> str:
        """One math array: footnotesize sans-serif keywords, then the items —
        source/lgref as component refdesses (bold, like the refdes labels),
        detector names as math symbols.  The block is scaled to the parameter
        size, so keyword (footnotesize) and detector (normalsize) already match
        component parameter name/value; the refdesses are bumped to the refdes
        size by the exact COMP_LABEL/COMP_PARAM ratio (\\scalebox)."""
        from .latex_label import symbol_to_latex, refdes_to_latex
        style = style_of(self) if self.scene() is not None else default_style()
        bold  = getattr(style, "COMP_LABEL_LATEX_BOLD", False)
        lh    = getattr(style, "COMP_LABEL_SVG_HEIGHT", 14.0)
        ph    = getattr(style, "COMP_PARAM_SVG_HEIGHT", 12.0)
        ref_scale = (lh / ph) if ph else 1.0

        def _item_tex(kw, it):
            if kw == "detector":                       # parameter-value size
                return symbol_to_latex(it)
            # refdes size: \scalebox's arg is text mode, so keep the refdes math
            # with \ensuremath.
            return rf"\scalebox{{{ref_scale:.4f}}}{{\ensuremath{{{refdes_to_latex(it, bold)}}}}}"

        blocks = [(kw, items) for kw, items in self._blocks() if items]
        if not blocks:                                   # empty → keyword template
            blocks = [(kw, []) for kw, _ in self._blocks()]
        rows = []
        for kw, items in blocks:
            row = rf"{{\footnotesize \textsf{{{kw}}}}}"
            if items:
                row += r"\;" + r"\;".join(_item_tex(kw, it) for it in items)
            rows.append(row)
        return r"\begin{array}{l}" + r" \\ ".join(rows) + r"\end{array}"

    # ── rendering ────────────────────────────────────────────────────────────────
    def _load_renderer(self) -> None:
        """(Re)build the LaTeX SVG renderer from the owning schematic's style.
        Before the item is in a scene, or with LaTeX rendering off, leaves the
        renderer None so :meth:`paint` draws plain text."""
        self._renderer  = None
        self._svg_bytes = b""
        from .latex_label import LATEX_INSTALLED
        style = style_of(self) if self.scene() is not None else default_style()
        if (self.scene() is not None and LATEX_INSTALLED
                and getattr(style, "LATEX_RENDERING_ENABLED", False)):
            from .latex_label import cache_dir_of, _render_latex_str
            svg = _render_latex_str(self._latex_block(), cache_dir=cache_dir_of(self))
            if svg:
                r = QSvgRenderer(QByteArray(svg))
                if r.isValid():
                    self._renderer  = r
                    self._svg_bytes = svg
                    self._derive_svg_rect(r)

    def _derive_svg_rect(self, renderer) -> None:
        """On-canvas size: scale the natural SVG so the block matches the
        component parameter text height (keyword/detector), the refdesses
        already bumped to the refdes height inside the LaTeX (\\scalebox)."""
        vb = renderer.viewBoxF()
        from .latex_label import svg_line_height
        style = style_of(self) if self.scene() is not None else default_style()
        ref_h    = svg_line_height()
        target_h = style.COMP_PARAM_SVG_HEIGHT
        if ref_h and ref_h > 0:
            scale = target_h / ref_h * 0.75
        elif vb.height() > 0:
            scale = target_h / vb.height() * 0.75
        else:
            scale = 1.0
        self._svg_rect = QRectF(0.0, 0.0, vb.width() * scale, vb.height() * scale)

    def update_text(self) -> None:
        """Re-render after an edit or a style change (safe outside itemChange)."""
        self.prepareGeometryChange()
        self._load_renderer()
        self.update()

    # ── geometry / paint ──────────────────────────────────────────────────────────
    def _natural_text_rect(self) -> QRectF:
        style = style_of(self) if self.scene() is not None else default_style()
        fm    = QFontMetricsF(style.COMMAND_FONT)
        lines = self._plain_display().split("\n")
        w = max((fm.horizontalAdvance(l) for l in lines), default=10.0)
        h = fm.height() * len(lines)
        return QRectF(0.0, 0.0, max(1.0, w), max(1.0, h))

    def boundingRect(self) -> QRectF:
        if self._renderer is not None:
            return self._svg_rect
        return self._natural_text_rect()

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        p.addRect(self.boundingRect())
        return p

    def _paint_text(self, painter) -> None:
        style = style_of(self) if self.scene() is not None else default_style()
        painter.setFont(style.COMMAND_FONT)
        painter.setPen(style.COMMAND_COLOR)
        fm = QFontMetricsF(style.COMMAND_FONT)
        y  = fm.ascent()
        for line in self._plain_display().split("\n"):
            painter.drawText(QPointF(0.0, y), line)
            y += fm.height()

    def paint(self, painter, option, widget=None) -> None:
        if self._renderer is not None:
            self._renderer.render(painter, self._svg_rect)
        else:
            self._paint_text(painter)
        if option.state & QStyle.State_Selected:
            painter.save()
            painter.setPen(_SEL_PEN)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
            painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            # Safe here: no text document to relayout — just reload the SVG.
            self.prepareGeometryChange()
            self._load_renderer()
            self.update()
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
