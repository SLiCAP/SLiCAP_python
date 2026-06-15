from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QFontMetricsF, QPen

from .config import snap, COMP_LABEL_FONT_SIZE, COMP_REFDES_FONT_FAMILY

_BORDER_COLOR  = QColor(60, 100, 140)
_LINE_SPACING  = 1.3                       # multiple of line height
_SELECTED      = QStyle.State_Selected
_SEL_PEN       = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


class ParameterItem(QGraphicsItem):
    """
    A circuit parameter table on the canvas.

    Stores parameter name/value pairs and the SVG rendered from them.
    The rendered SVG is cached in the schematic file so the item is visible
    even on machines without pdflatex/dvisvgm.

    Contributes .param lines to the netlist on export.
    Double-click opens the parameter dialog to edit and re-render.
    """

    def __init__(self, params: list,        # list[tuple[str, str]]
                 preamble_path: str,
                 svg_bytes: bytes | None,
                 display_width: int, display_height: int,
                 pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.params:        list        = list(params)  # [(name, value), ...]
        self.preamble_path: str         = preamble_path
        self._svg_bytes:    bytes | None = svg_bytes
        self.display_width:  int        = display_width
        self.display_height: int        = display_height
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._renderer = None
        self._load_renderer()

    def _load_renderer(self) -> None:
        self._renderer = None
        from .latex_label import LATEX_AVAILABLE
        if not LATEX_AVAILABLE:
            return
        if self._svg_bytes is None:
            from .latex_label import render_latex_raw
            svg, _err = render_latex_raw(self.build_latex(self.params),
                                         self.preamble_path)
            if svg:
                self._svg_bytes = svg
        if self._svg_bytes:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QByteArray
            r = QSvgRenderer(QByteArray(self._svg_bytes))
            if r.isValid():
                self._renderer = r

    # ── geometry ──────────────────────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        if self._renderer is not None:
            return QRectF(0, 0, self.display_width, self.display_height)
        return self._natural_text_rect()

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _natural_text_rect(self) -> QRectF:
        """Bounding rect sized to the text content (used when there is no renderer)."""
        hdr_font = QFont(COMP_REFDES_FONT_FAMILY)
        hdr_font.setBold(True)
        hdr_font.setPointSizeF(COMP_LABEL_FONT_SIZE)
        body_font = QFont(COMP_REFDES_FONT_FAMILY)
        body_font.setPointSizeF(COMP_LABEL_FONT_SIZE)

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

        hdr_font = QFont(COMP_REFDES_FONT_FAMILY)
        hdr_font.setBold(True)
        hdr_font.setPointSizeF(COMP_LABEL_FONT_SIZE)
        body_font = QFont(COMP_REFDES_FONT_FAMILY)
        body_font.setPointSizeF(COMP_LABEL_FONT_SIZE)

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
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    # ── static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def build_latex(params: list) -> str:
        from .latex_label import expression_to_latex
        if not params:
            return r"$\emptyset$"

        def _value_texify(s: str) -> str:
            """Run value through SLiCAP expression pipeline; fall back to raw LaTeX."""
            s = s.strip()
            if not s:
                return ""
            if not (s.startswith("{") and s.endswith("}")):
                s = "{" + s + "}"
            return expression_to_latex(s)

        rows = " \\\\\n".join(
            f"  {_value_texify(name)} & {_value_texify(value)}"
            for name, value in params
        )
        return (
            r"\["                                                    "\n"
            r"\begin{array}{r@{\;=\;}l}"                            "\n"
            r"\multicolumn{2}{c}{\textbf{Parameters}} \\"          "\n"
            + rows + "\n"
            r"\end{array}"                                          "\n"
            r"\]"
        )

    def param_lines(self, exclude=None) -> list:
        """Return SPICE .param lines for netlist export.

        Names in ``exclude`` (e.g. parameters passed in through a ``.subckt``
        line) are skipped: the passed value supersedes any internal definition.
        """
        exclude = exclude or set()
        rows = []
        for name, value in self.params:
            clean_name = name.strip().strip("{}")
            if clean_name in exclude:
                continue
            v = value.strip()
            if not (v.startswith("{") and v.endswith("}")):
                v = "{" + v + "}"
            rows.append(f"+ {clean_name}={v}")
        if not rows:
            return []
        return [".param"] + rows
