from pathlib import Path

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF, QByteArray
from PySide6.QtGui import QPainterPath, QFontMetricsF, QColor, QPen
from PySide6.QtSvg import QSvgRenderer

from .config import snap, style_of, default_style

_SEL_PEN = QPen(QColor(0, 120, 215), 1.5, Qt.DashLine)
_SEL_PEN.setCosmetic(True)


def _tex_escape(s: str) -> str:
    """Escape a filename/corner for LaTeX \\texttt{}."""
    for a, b in (("\\", r"\textbackslash{}"), ("{", r"\{"), ("}", r"\}"),
                 ("_", r"\_"), ("#", r"\#"), ("%", r"\%"), ("&", r"\&"),
                 ("$", r"\$"), ("^", r"\^{}"), ("~", r"\~{}")):
        s = s.replace(a, b)
    return s


class LibraryItem(QGraphicsItem):
    """
    A block of ``.lib`` / ``.inc`` library references on the canvas.

    Holds a LIST of entries, each a dict ``{"directive", "file", "corner"}``;
    double-click opens the "Add / Edit libraries" editor.  Displayed as one
    block (footnotesize LaTeX when rendering is on, else plain text) with the
    leading '.' shown only in the netlist, not on the canvas — same model as the
    analysis block.  A hidden block stays in the scene and is ALWAYS netlisted;
    only drawing and image export are suppressed.

    The netlist format follows the schematic *type*, not the item: SLiCAP
    schematics use :meth:`netlist_lines` (``.lib``/``.inc`` + corner); NGspice
    schematics read :attr:`entries` and emit ``.include``.
    """

    def __init__(self, entries=None, pos: QPointF = QPointF(0, 0),
                 show: bool = True):
        super().__init__()
        self.entries: list = [dict(e) for e in (entries or [])]
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)
        self.setPos(pos)
        self._renderer  = None
        self._svg_rect  = QRectF()
        self._svg_bytes = b""
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._load_renderer()

    def set_show(self, show: bool) -> None:
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)

    # ── content ────────────────────────────────────────────────────────────────
    def _display_entries(self):
        """Cleaned entries with a non-empty file."""
        out = []
        for e in self.entries:
            f = (e.get("file") or "").strip()
            if not f:
                continue
            out.append({
                "directive": (e.get("directive") or "lib").strip() or "lib",
                "file": f,
                "corner": (e.get("corner") or "").strip(),
            })
        return out

    def netlist_lines(self) -> list:
        """SLiCAP netlist lines: ``.{directive} {path} {corner}`` per entry
        (WITH the leading dot; the path is quoted when it contains a space)."""
        lines = []
        for e in self._display_entries():
            path = e["file"]
            if " " in path:
                path = f'"{path}"'
            parts = ["." + e["directive"], path]
            if e["corner"]:
                parts.append(e["corner"])
            lines.append(" ".join(parts))
        return lines

    def _plain_lines(self) -> list:
        """Canvas lines — WITHOUT the leading dot, filename only."""
        out = []
        for e in self._display_entries():
            name = Path(e["file"]).name
            parts = [e["directive"], name] + ([e["corner"]] if e["corner"] else [])
            out.append(" ".join(p for p in parts if p))
        return out or ["lib"]

    def _plain_display(self) -> str:
        return "\n".join(self._plain_lines())

    def toPlainText(self) -> str:
        """Plain-text form (used by the SVG exporter's text block)."""
        return self._plain_display()

    def _latex_block(self) -> str:
        """One math array: each line footnotesize \\texttt (dot dropped)."""
        rows = [rf"{{\footnotesize \texttt{{{_tex_escape(line)}}}}}"
                for line in self._plain_lines()]
        return r"\begin{array}{l}" + r" \\ ".join(rows) + r"\end{array}"

    # ── rendering ────────────────────────────────────────────────────────────────
    def _load_renderer(self) -> None:
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
        self.prepareGeometryChange()
        self._load_renderer()
        self.update()

    # ── geometry / paint ──────────────────────────────────────────────────────────
    def _natural_text_rect(self) -> QRectF:
        style = style_of(self) if self.scene() is not None else default_style()
        fm    = QFontMetricsF(style.COMMAND_FONT)
        lines = self._plain_lines()
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
        for line in self._plain_lines():
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
            self.prepareGeometryChange()
            self._load_renderer()
            self.update()
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
