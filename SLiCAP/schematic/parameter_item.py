from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QFontMetricsF, QPen

from .config import snap, style_of

_BORDER_COLOR  = QColor(60, 100, 140)
_LINE_SPACING  = 1.3                       # multiple of line height
_SELECTED      = QStyle.State_Selected
_SEL_PEN       = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


def svg_scene_size(renderer, style) -> "tuple[float, float] | None":
    """Natural (100 %) size of a rendered-LaTeX SVG in scene units.

    Calibrated against the height of one line of math (svg_line_height) so
    that at 100 % the table's text matches the component-label font size."""
    from .latex_label import svg_line_height
    vb = renderer.viewBoxF()
    sw = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
    sh = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
    if sw <= 0 or sh <= 0:
        return None
    ref_h = svg_line_height()
    base = (style.COMP_LABEL_FONT_SIZE / ref_h) if (ref_h and ref_h > 0) else 0.5
    return sw * base, sh * base


class ParameterItem(QGraphicsItem):
    """
    A circuit parameter table on the canvas.

    Stores parameter name/value pairs and the SVG rendered from them.
    Contributes .param lines to the netlist on export — ALWAYS, also when
    "Show on schematic" is off (hidden: in the scene, not drawn/exported).

    The on-canvas size is DERIVED: natural SVG size × the schematic's
    SCALE_PARAMETER_TABLE preference (the single source for table scaling —
    there is no per-item scale).

    Double-click opens the parameter dialog to edit and re-render.
    """

    def __init__(self, params: list,        # list[tuple[str, str]]
                 preamble_path: str,
                 pos: QPointF = QPointF(0, 0),
                 show: bool = True):
        super().__init__()
        self.params:        list        = list(params)  # [(name, value), ...]
        self.preamble_path: str         = preamble_path
        self._svg_bytes:    bytes | None = None
        self.display_width:  int        = 200   # derived in _load_renderer
        self.display_height: int        = 80
        # "Show on schematic": a hidden table stays in the scene and keeps
        # netlisting its .param lines; only drawing and image export are
        # suppressed (same semantics as the analysis block / library link).
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None
        self._load_renderer()

    def set_show(self, show: bool) -> None:
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)

    def _load_renderer(self) -> None:
        self._renderer = None
        from .latex_label import LATEX_INSTALLED
        # Fresh rendering needs the tools AND the owning schematic's preference;
        # before the item is in a scene only stored bytes are used (the scene-
        # entry hook re-runs this with the real style).
        if (self.scene() is not None and LATEX_INSTALLED
                and style_of(self).LATEX_RENDERING_ENABLED):
            from .latex_label import cache_dir_of, render_latex_raw
            latex = self.build_latex(self.params)
            if latex is None:
                # An entry is not a valid SLiCAP expression: no render at all.
                self._render_error = (
                    "A parameter name or value is not a valid SLiCAP "
                    "expression (see the log for which one).")
                self._svg_bytes = b""
                svg = None
            else:
                svg, err = render_latex_raw(latex, self.preamble_path,
                                            cache_dir=cache_dir_of(self))
                self._render_error = err or ""
            if svg:
                self._svg_bytes = svg  # keep stored bytes up to date
        if self._svg_bytes:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QByteArray
            r = QSvgRenderer(QByteArray(self._svg_bytes))
            if r.isValid():
                self._renderer = r
                self._derive_size(r)
        # Text fallback caused by a LaTeX error: say WHY in the tooltip
        # (there is no preview step to surface it, Anton 2026-07-12).
        if self._renderer is None and getattr(self, "_render_error", ""):
            self.setToolTip("LaTeX rendering failed:\n" + self._render_error)
        else:
            self.setToolTip("")

    def _derive_size(self, renderer) -> None:
        """Display size = natural size × the schematic's table-scale preference."""
        style = style_of(self)
        natural = svg_scene_size(renderer, style)
        if natural is not None:
            pct = style.SCALE_PARAMETER_TABLE / 100.0
            self.display_width  = max(1, round(natural[0] * pct))
            self.display_height = max(1, round(natural[1] * pct))

    # ── geometry ──────────────────────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        if self._renderer is not None:
            return QRectF(0, 0, self.display_width, self.display_height)
        return self._natural_text_rect()

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _fonts(self) -> tuple[QFont, QFont]:
        """(header, body) fonts from the owning schematic's style."""
        style = style_of(self)
        hdr_font = QFont(style.COMP_REFDES_FONT_FAMILY)
        hdr_font.setBold(True)
        hdr_font.setPointSizeF(style.COMP_LABEL_FONT_SIZE)
        body_font = QFont(style.COMP_REFDES_FONT_FAMILY)
        body_font.setPointSizeF(style.COMP_LABEL_FONT_SIZE)
        return hdr_font, body_font

    def _natural_text_rect(self) -> QRectF:
        """Bounding rect sized to the text content (used when there is no renderer)."""
        hdr_font, body_font = self._fonts()

        fm_h = QFontMetricsF(hdr_font)
        fm_b = QFontMetricsF(body_font)

        lines = self._text_display_lines()
        pad   = fm_b.height() * 0.3
        line_h = fm_b.height() * _LINE_SPACING

        widths = [fm_h.horizontalAdvance(lines[0])] + [
            fm_b.horizontalAdvance(l) for l in lines[1:]
        ]
        max_w = max(widths) if widths else 10.0

        total_w = max_w + 2 * pad
        total_h = pad + fm_h.height() + len(lines[1:]) * line_h + pad

        return QRectF(0, 0, max(1.0, total_w), max(1.0, total_h))

    # ── paint ─────────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, widget=None) -> None:
        from .latex_fragment_item import _aspect_fit
        r = self.boundingRect()
        if self._renderer is not None:
            self._renderer.render(painter, _aspect_fit(self._renderer, r))
        else:
            self._paint_text_fallback(painter, r)
        if option.state & _SELECTED:
            sel_r = _aspect_fit(self._renderer, r) if self._renderer is not None else r
            painter.save()
            painter.setPen(_SEL_PEN)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(sel_r)
            painter.restore()

    def _text_display_lines(self) -> list:
        """Display lines for text fallback: no curly braces, 'name = value' format."""
        lines = ["Parameters"]
        for name, value in self.params:
            n = name.strip().strip("{}")
            v = value.strip().strip("{}")
            lines.append(f"{n} = {v}")
        return lines

    def _paint_text_fallback(self, painter: QPainter, r: QRectF) -> None:
        lines = self._text_display_lines()

        if not self.params:
            painter.drawText(r, Qt.AlignCenter, "Parameters\n(empty)")
            return

        hdr_font, body_font = self._fonts()

        fm_h = QFontMetricsF(hdr_font)
        fm_b = QFontMetricsF(body_font)
        pad    = fm_b.height() * 0.3
        line_h = fm_b.height() * _LINE_SPACING
        y = r.top() + pad + fm_h.ascent()

        painter.setPen(_BORDER_COLOR)
        painter.setFont(hdr_font)
        painter.drawText(QPointF(r.left() + pad, y), lines[0])
        y += line_h

        painter.setFont(body_font)
        for line in lines[1:]:
            painter.drawText(QPointF(r.left() + pad, y), line)
            y += line_h

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self.prepareGeometryChange()
            self._load_renderer()
            self.update()
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    # ── static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def build_latex(params: list) -> "str | None":
        """LaTeX for the parameter table, or None when a name or value is not
        a valid SLiCAP expression — an unparsable entry is never rendered
        (Anton, 2026-08-16); the item then shows plain text and says why.

        The table is built by SLiCAP's own LaTeX formatter (latex_label.
        slicap_table → LaTeXformatter.nestedLists): this passes SYMPY OBJECTS
        and lets the formatter decide maths-vs-text and do the escaping,
        instead of concatenating LaTeX here — a component property is not a
        LaTeX fragment and must never be treated as one (Anton, 2026-08-16).
        """
        from .latex_label import expression_sympy, slicap_table
        if not params:
            return r"$\emptyset$"

        def _cell(s: str):
            """Sympy object for an entry; None = does not parse (no render)."""
            s = (s or "").strip()
            if not s:
                return ""                       # empty cell: plain text
            if not (s.startswith("{") and s.endswith("}")):
                s = "{" + s + "}"
            return expression_sympy(s)

        rows = [[_cell(name), _cell(value)] for name, value in params]
        if any(cell is None for row in rows for cell in row):
            return None
        return slicap_table(["", ""], rows, title="Parameters")

    def param_lines(self, exclude=None, value_fn=None) -> list:
        """Return SPICE .param lines for netlist export.

        Names in ``exclude`` (e.g. parameters passed in through a ``.subckt``
        line) are skipped: the passed value supersedes any internal definition.

        *value_fn* transforms each bare value before it is wrapped — the
        NGspice netlist builder passes the SLiCAP→NGspice notation translator
        ('1M' → '1Meg'); SLiCAP netlists need no transform.
        """
        exclude = exclude or set()
        rows = []
        for name, value in self.params:
            clean_name = name.strip().strip("{}")
            if clean_name in exclude:
                continue
            v = value.strip()
            if not (v.startswith("{") and v.endswith("}")):
                if value_fn is not None:
                    v = value_fn(v)
                v = "{" + v + "}"
            rows.append(f"+ {clean_name}={v}")
        if not rows:
            return []
        return [".param"] + rows
