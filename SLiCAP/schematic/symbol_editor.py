"""
Symbol editor: create or edit a symbol of a ``.slicap_sym`` / ``.spice_sym``
file with the schematic editor itself (Anton, 2026-09-27).

Design (agreed 2026-09-27, see the GUI manual page "The symbol editor"):

* A symbol is one ``<g id=NAME data-...>`` in a symbol file, drawn with the
  SVG primitives the drawing shapes already produce (line/polyline, rect,
  circle/ellipse, polygon), plus ``<text>`` for symbol text and one
  ``<circle class="node" data-node=NAME>`` per pin. The file is the input
  AND the output: Open reads a symbol out of a file, Save writes it back
  as one group, replacing the group of the same name and leaving the other
  symbols of the file untouched.
* "Create / edit symbol" on the main window opens a CanvasPanel in
  SYMBOL MODE: the same canvas, undo, selection and drawing, with reduced
  menus. Nothing of the schematic editor is changed for it.
* Two item kinds are specific to symbols: a PIN (grid-snapping marker with
  a node name and an order number; the node names are free, only the
  order matters because the netlister writes the pins in list order) and
  SYMBOL TEXT (decoration such as "+", "-", drawn upright like the library's
  embedded text). There is no third text kind: pin names are drawn by the
  canvas from the pin list when the symbol says so.
* The origin (the component's anchor) is set by the user: "Set origin at
  selection" shifts the drawing so the selected item sits at 0,0.
* Colours: the canvas restyles symbols by replacing the literal colours
  ``black`` (strokes, filled heads) and adding a fill to ``<text>``; ``white``
  fills mask wires. A shape with another colour is written as is and
  reported on save, since it will not follow the schematic style.
* A primitive the editor cannot edit (``<path>``, nested ``<g>``, anything
  with a transform) is kept as an OPAQUE item: shown, movable, deletable,
  re-emitted verbatim (with a translate when moved).

Placed elements go to the view centre and are dragged into place; the
placement modes of the canvas are not extended for them (considered and
REJECTED as needless canvas surface, 2026-09-27).
"""
from __future__ import annotations

import copy
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtWidgets import (
    QGraphicsItem, QStyle, QDialog, QVBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QDialogButtonBox, QLabel,
)
from PySide6.QtCore import Qt, QPointF, QRectF, QByteArray
from PySide6.QtGui import (QColor, QPainter, QPen, QBrush, QFont, QFontMetricsF,
                           QPolygonF, QPainterPath)
from PySide6.QtSvg import QSvgRenderer

from .config import snap, style_of, default_style

XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("xlink", XLINK_NS)
from .sizing import fix_chars, fit_contents

SVG_NS  = "http://www.w3.org/2000/svg"
NODE_R  = 0.5                       # radius of the pin marker in the file
_SEL    = QColor(0, 120, 215)
_ATTR_KEYS = ("prefix", "nodes", "model", "params", "refs", "description",
              "info", "show-pinnames")


def _local(tag) -> str:
    return tag.split("}", 1)[1] if isinstance(tag, str) and "}" in tag else str(tag)


# ── metadata ─────────────────────────────────────────────────────────────────

@dataclass
class SymbolMeta:
    """The attributes of the symbol's <g> (everything but the drawing)."""
    name:          str = "NEW"
    prefix:        str = "X"
    model:         str = ""
    model_show:    bool = False
    params:        list = field(default_factory=list)   # [name, default, show_name, show_value]
    refs:          list = field(default_factory=list)   # reference designators, e.g. ["V1"]
    description:   str = ""
    info:          str = ""
    show_pinnames: bool = False

    @classmethod
    def from_g(cls, g) -> "SymbolMeta":
        model_raw = g.get("data-model", "") or ""
        model, show = model_raw, False
        if "|" in model_raw:
            model, flag = model_raw.split("|", 1)
            show = flag.strip() == "1"
        params = []
        for entry in (g.get("data-params", "") or "").split(";"):
            f = [p.strip() for p in entry.split("|")]
            if len(f) == 4 and f[0]:
                params.append([f[0], f[1], f[2] == "1", f[3] == "1"])
        return cls(name=g.get("id", "NEW"),
                   prefix=g.get("data-prefix", "X") or "X",
                   model=model.strip(), model_show=show, params=params,
                   refs=(g.get("data-refs", "") or "").split(),
                   description=g.get("data-description", "") or "",
                   info=g.get("data-info", "") or "",
                   show_pinnames=(g.get("data-show-pinnames", "").strip().lower()
                                  in ("true", "1", "yes")))

    def attributes(self, node_names: list[str]) -> dict:
        a = {"id": self.name, "data-prefix": self.prefix,
             "data-nodes": " ".join(node_names)}
        if self.model:
            a["data-model"] = f"{self.model}|{1 if self.model_show else 0}"
        a["data-params"] = "; ".join(
            f"{n}|{d}|{1 if sn else 0}|{1 if sv else 0}" for n, d, sn, sv in self.params)
        if self.refs:
            a["data-refs"] = " ".join(self.refs)
        a["data-description"] = self.description
        if self.info:
            a["data-info"] = self.info
        if self.show_pinnames:
            a["data-show-pinnames"] = "true"
        return a


# ── items ────────────────────────────────────────────────────────────────────

class SymbolPinItem(QGraphicsItem):
    """A pin: grid-snapping marker with a node name and an order number.

    Shown as a BADGE on the pin point with the order number inside: the
    file holds no placement for labels, and a label beside the marker
    overlapped neighbouring pins and the outline (Anton, 2026-09-27). The
    badge sits exactly on the pin, where only the pin's own line ends. The
    name is the tooltip; name and number are edited by double-click."""
    BADGE_R = 2.6
    GRID_CRITICAL = True      # a pin always snaps (config.snap_pos)

    def __init__(self, name: str, number: int, pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.name   = name
        self.number = number
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(5)
        self.refresh()

    def refresh(self) -> None:
        self.setToolTip(f"pin {self.number}: {self.name}")
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        r = self.BADGE_R + 1
        return QRectF(-r, -r, 2 * r, 2 * r)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.BADGE_R, self.BADGE_R)
        return path

    def _font(self) -> QFont:
        f = QFont(style_of(self).COMP_PARAM_FONT)
        f.setPixelSize(4)
        f.setBold(True)
        return f

    def paint(self, painter: QPainter, option, widget=None) -> None:
        st = style_of(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(st.NET_LABEL_COLOR, 0.4))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(0, 0), self.BADGE_R, self.BADGE_R)
        painter.setFont(self._font())
        painter.setPen(st.NET_LABEL_COLOR)
        painter.drawText(QRectF(-self.BADGE_R, -self.BADGE_R, 2 * self.BADGE_R, 2 * self.BADGE_R),
                         Qt.AlignCenter, str(self.number))
        if option.state & QStyle.State_Selected:
            pen = QPen(_SEL, 1.0, Qt.DashLine); pen.setCosmetic(True)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())


class SymbolTextItem(QGraphicsItem):
    """Symbol text (decoration such as "+", "-"): drawn centred on its anchor
    with the symbol text colour, like the library's embedded <text>."""
    SNAPS_TO_GRID = False

    def __init__(self, content: str, size: float = 8.0, pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.content = content
        self.size    = float(size)
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def _font(self) -> QFont:
        f = QFont(style_of(self).COMP_PARAM_FONT)
        f.setPixelSize(max(1, round(self.size)))
        return f

    def boundingRect(self) -> QRectF:
        fm = QFontMetricsF(self._font())
        w = max(4.0, fm.horizontalAdvance(self.content)); h = fm.height()
        return QRectF(-w / 2 - 2, -h / 2 - 2, w + 4, h + 4)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        st = style_of(self)
        painter.setFont(self._font())
        painter.setPen(st.SYMBOL_TEXT_COLOR)
        painter.drawText(QRectF(-100, -100, 200, 200), Qt.AlignCenter, self.content)
        if option.state & QStyle.State_Selected:
            pen = QPen(_SEL, 1.0, Qt.DashLine); pen.setCosmetic(True)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())


class OpaqueSvgItem(QGraphicsItem):
    """A primitive the editor does not edit (<path>, nested <g>, transformed
    elements): rendered as is, movable, re-emitted verbatim on save."""

    def __init__(self, xml: str, pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.xml = xml
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._bbox = QRectF(-5, -5, 10, 10)
        self._renderer = None
        self._build()

    def _build(self) -> None:
        from .symbol_library import _element_bbox
        from .component_item import _apply_symbol_colors
        try:
            el = ET.fromstring(self.xml)
            box = _element_bbox(el)
        except ET.ParseError:
            box = None
        if box:
            x0, y0, x1, y1 = box
            self._bbox = QRectF(x0 - 1, y0 - 1, (x1 - x0) + 2, (y1 - y0) + 2)
        vb = self._bbox
        svg = (f'<svg xmlns="{SVG_NS}" viewBox="{vb.x()} {vb.y()} {vb.width()} {vb.height()}">'
               f"{self.xml}</svg>").encode()
        self._renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(svg, style_of(self))))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self._build()
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        return self._bbox.adjusted(-2, -2, 2, 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        if self._renderer is not None and self._renderer.isValid():
            self._renderer.render(painter, self._bbox)
        if option.state & QStyle.State_Selected:
            pen = QPen(_SEL, 1.0, Qt.DashLine); pen.setCosmetic(True)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(self._bbox)


class OriginItem(QGraphicsItem):
    """The symbol's origin (the anchor of the placed component): a circle
    with a cross. WHERE THE MARKER IS, IS THE ORIGIN: saving writes every
    coordinate relative to it, so dragging the marker, alone or as part of
    a selected group, sets the origin without moving the drawing (Anton,
    2026-09-27; shifting the drawing on release was tried and REJECTED the
    same day because a group move must carry the origin along). Always
    snaps, is never written to the file, survives undo through the data.
    """
    GRID_CRITICAL = True
    R = 4.0

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(50)
        self.setToolTip("origin: drag to set (the drawing is saved relative to it)")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        r = self.R * 1.6 + 1
        return QRectF(-r, -r, 2 * r, 2 * r)

    def shape(self) -> QPainterPath:
        """Hit area: the ring and the cross only, not the square around them
        (a press on a shape inside that square went to the marker, Anton,
        2026-09-27)."""
        from PySide6.QtGui import QPainterPathStroker
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.R, self.R)
        c = self.R * 1.6
        path.moveTo(-c, 0); path.lineTo(c, 0)
        path.moveTo(0, -c); path.lineTo(0, c)
        stroker = QPainterPathStroker(); stroker.setWidth(2.0)
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(_SEL if (option.state & QStyle.State_Selected) else QColor(120, 120, 120), 0.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), self.R, self.R)
        c = self.R * 1.6
        painter.drawLine(QPointF(-c, 0), QPointF(c, 0))
        painter.drawLine(QPointF(0, -c), QPointF(0, c))


# ── file <-> items ───────────────────────────────────────────────────────────

def _color_out(c: str) -> str:
    """Conventional colour names for the symbol file: 'black' and 'white'
    are what the canvas restyles; anything else is written as given."""
    c = (c or "").strip().lower()
    if c in ("#000000", "black"):
        return "black"
    if c in ("#ffffff", "white"):
        return "white"
    return c


def _color_in(c: str, default: str) -> str:
    c = (c or "").strip().lower()
    if c in ("", "none"):
        return default
    if c == "black":
        return "#000000"
    if c == "white":
        return "#ffffff"
    return c


def _rotated(points, angle_deg: float, centre: QPointF):
    a = math.radians(angle_deg); ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in points:
        dx, dy = p.x() - centre.x(), p.y() - centre.y()
        out.append(QPointF(centre.x() + dx * ca - dy * sa, centre.y() + dx * sa + dy * ca))
    return out


def _fmt(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


_IMAGE_SIZE_NOTE = 200_000     # bytes; above this the save reports the size


def _resolved_latex_children(svg_bytes: bytes) -> tuple[list, tuple]:
    """The drawable content of a dvisvgm SVG with every ``<use>`` of a glyph
    path replaced by the path itself (translated into place), so the result
    is self-contained: no ids, no <defs>, nothing that can collide when the
    symbol is placed several times or several symbols carry LaTeX.
    Returns (children, viewBox) with viewBox = (x, y, w, h)."""
    root = ET.fromstring(svg_bytes)
    ns = f"{{{SVG_NS}}}"
    vb = [float(v) for v in (root.get("viewBox") or "0 0 0 0").split()]
    if len(vb) != 4:
        vb = [0.0, 0.0, 0.0, 0.0]
    defs: dict[str, ET.Element] = {}
    for d in root.iter(f"{ns}defs"):
        for el in d.iter():
            if el.get("id"):
                defs[el.get("id")] = el
    href_keys = (f"{{{XLINK_NS}}}href", "href")

    def resolve(el) -> list:
        tag = _local(el.tag)
        if tag == "defs" or not isinstance(el.tag, str):
            return []
        if tag == "use":
            ref = next((el.get(k) for k in href_keys if el.get(k)), "")
            target = defs.get(ref[1:]) if ref.startswith("#") else None
            if target is None:
                return []
            copies = resolve(target) if _local(target.tag) == "g" else [copy.deepcopy(target)]
            x, y = el.get("x", "0"), el.get("y", "0")
            tr = " ".join(t for t in (el.get("transform", ""), f"translate({x} {y})") if t)
            out = []
            for c in copies:
                c.attrib.pop("id", None)
                own = c.get("transform")
                c.set("transform", f"{tr} {own}" if own else tr)
                out.append(c)
            return out
        if tag == "g":
            g = ET.Element(f"{ns}g", {k: v for k, v in el.attrib.items() if k != "id"})
            for c in el:
                g.extend(resolve(c))
            return [g]
        c = copy.deepcopy(el)
        c.attrib.pop("id", None)
        return [c]

    children: list = []
    for el in root:
        children.extend(resolve(el))
    return children, tuple(vb)


def bake_latex_group(latex_code: str, preamble_path: str, svg_bytes: bytes,
                     x: float, y: float, w: float, h: float) -> ET.Element:
    """The ``<g class="latex">`` of a LaTeX label in a symbol file.

    The group draws the label at rotation 0 in symbol coordinates: the
    dvisvgm output, resolved to plain paths (see _resolved_latex_children),
    fitted with its aspect ratio kept into the box (x, y, w, h).  The source
    (``data-latex``, ``data-preamble``) and the box (``data-x/-y/-w/-h``) are
    kept so the editor can reopen the label and so the component can turn it
    under the readable-orientation rule.  ``fill="black"`` on the group is
    what the schematic style recolours."""
    g = ET.Element(f"{{{SVG_NS}}}g")
    g.set("class", "latex")
    g.set("data-latex", latex_code)
    g.set("data-preamble", preamble_path or "")
    for k, v in (("data-x", x), ("data-y", y), ("data-w", w), ("data-h", h)):
        g.set(k, _fmt(v))
    g.set("fill", "black")
    if not svg_bytes:
        return g
    try:
        children, (vx, vy, vw, vh) = _resolved_latex_children(svg_bytes)
    except ET.ParseError:
        return g
    if vw <= 0 or vh <= 0:
        return g
    sc = min(w / vw, h / vh)
    fx = x + (w - vw * sc) / 2.0
    fy = y + (h - vh * sc) / 2.0
    g.set("transform", f"translate({fx:.4f} {fy:.4f}) scale({sc:.6f}) translate({-vx:.4f} {-vy:.4f})")
    g.extend(children)
    return g


def _image_element(item, x: float, y: float) -> tuple[ET.Element | None, int]:
    """An ``<image>`` with the picture of an ImageItem embedded as a data URI
    (PNG/JPEG files as they are, everything else rasterised at four times the
    display size).  Returns (element, byte size) or (None, 0)."""
    import base64
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QPainter as _QP, QPixmap as _QPixmap, QImage as _QImage
    path = Path(item.file_path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower())
    data = b""
    if mime and path.is_file():
        data = path.read_bytes()
    else:
        mime = "image/png"
        w, h = max(1, item.display_width), max(1, item.display_height)
        img = _QImage(w * 4, h * 4, _QImage.Format_ARGB32)
        img.fill(0)
        p = _QP(img)
        p.setRenderHint(_QP.Antialiasing)
        p.setRenderHint(_QP.SmoothPixmapTransform)
        p.scale(4, 4)
        item.paint_picture(p, QRectF(0, 0, w, h))
        p.end()
        buf = QBuffer(); buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG"); data = bytes(buf.data()); buf.close()
    if not data:
        return None, 0
    el = ET.Element(f"{{{SVG_NS}}}image")
    el.set("x", _fmt(x)); el.set("y", _fmt(y))
    el.set("width", _fmt(item.display_width)); el.set("height", _fmt(item.display_height))
    el.set("preserveAspectRatio", "xMidYMid meet")
    el.set(f"{{{XLINK_NS}}}href", f"data:{mime};base64," + base64.b64encode(data).decode("ascii"))
    return el, len(data)


def items_to_g(meta: SymbolMeta, items, origin: QPointF = QPointF(0, 0)) -> tuple[ET.Element, list[str]]:
    """Serialize the symbol items into the <g> of the symbol file, with every
    coordinate relative to *origin* (the origin marker's position).
    Returns (g, warnings); warnings name shapes with non-conventional colours
    and other things the author should know."""
    ox0, oy0 = origin.x(), origin.y()
    from .shape_item import ShapeItem, head_polygon, shaft_points, KINDS_WITH_FILL
    from .latex_fragment_item import LatexFragmentItem
    from .image_item import ImageItem
    pins  = sorted((i for i in items if isinstance(i, SymbolPinItem)), key=lambda p: p.number)
    names = [p.name for p in pins]
    g = ET.Element(f"{{{SVG_NS}}}g")
    for k, v in meta.attributes(names).items():
        g.set(k, v)
    warnings: list[str] = []

    def sub(tag, **attrs):
        el = ET.SubElement(g, f"{{{SVG_NS}}}{tag}")
        for k, v in attrs.items():
            if v is not None:
                el.set(k.replace("_", "-"), v)
        return el

    for it in items:
        if isinstance(it, ShapeItem):
            ox, oy = it.pos().x() - ox0, it.pos().y() - oy0
            pts = [QPointF(ox + p.x(), oy + p.y()) for p in it.rel_points]
            stroke = "none" if it.line_style == "none" else _color_out(it.stroke_color)
            fill = _color_out(it.fill_color) if (it.fill_style == "solid" and it.kind in KINDS_WITH_FILL) else "none"
            for c in (stroke, fill):
                if c not in ("none", "black", "white"):
                    warnings.append(f"{it.kind}: colour {c} will not follow the schematic style")
            base = dict(stroke=stroke, stroke_width=_fmt(it.line_width) if stroke != "none" else None, fill=fill)
            if it.line_style in ("dashed", "dotted", "dash-dot") and stroke != "none":
                base["stroke_dasharray"] = {"dashed": "4 2", "dotted": "1 2", "dash-dot": "4 2 1 2"}[it.line_style]
            centre = QPointF(ox + it.centre().x(), oy + it.centre().y())
            rot = float(it.rotation or 0.0)
            if it.kind == "line" and len(pts) >= 2:
                shaft = shaft_points(pts, it.line_end_start, it.line_end_end, it.head_length)
                sub("polyline", points=" ".join(f"{_fmt(p.x())},{_fmt(p.y())}" for p in shaft), **{**base, "fill": "none"})
                for a, b, style in ((pts[1], pts[0], it.line_end_start), (pts[-2], pts[-1], it.line_end_end)):
                    if style == "dot":
                        sub("circle", cx=_fmt(b.x()), cy=_fmt(b.y()), r=_fmt(it.head_width / 2), fill=_color_out(it.stroke_color), stroke="none")
                    else:
                        poly = head_polygon(a, b, style, it.head_width, it.head_length)
                        if poly:
                            sub("polygon", points=" ".join(f"{_fmt(p.x())},{_fmt(p.y())}" for p in poly), fill=_color_out(it.stroke_color), stroke="none")
            elif it.kind == "rect" and len(pts) == 2:
                x0, y0 = min(pts[0].x(), pts[1].x()), min(pts[0].y(), pts[1].y())
                x1, y1 = max(pts[0].x(), pts[1].x()), max(pts[0].y(), pts[1].y())
                if rot:
                    corners = _rotated([QPointF(x0, y0), QPointF(x1, y0), QPointF(x1, y1), QPointF(x0, y1)], rot, centre)
                    sub("polygon", points=" ".join(f"{_fmt(p.x())},{_fmt(p.y())}" for p in corners), **base)
                else:
                    sub("rect", x=_fmt(x0), y=_fmt(y0), width=_fmt(x1 - x0), height=_fmt(y1 - y0), **base)
            elif it.kind == "ellipse" and len(pts) == 2:
                rx, ry = abs(pts[1].x() - pts[0].x()) / 2, abs(pts[1].y() - pts[0].y()) / 2
                cx, cy = (pts[0].x() + pts[1].x()) / 2, (pts[0].y() + pts[1].y()) / 2
                extra = {"transform": f"rotate({_fmt(rot)} {_fmt(cx)} {_fmt(cy)})"} if (rot and abs(rx - ry) > 1e-6) else {}
                if extra:
                    warnings.append("rotated ellipse: its extent is measured unrotated by the symbol loader")
                if abs(rx - ry) < 1e-6:
                    sub("circle", cx=_fmt(cx), cy=_fmt(cy), r=_fmt(rx), **base)
                else:
                    sub("ellipse", cx=_fmt(cx), cy=_fmt(cy), rx=_fmt(rx), ry=_fmt(ry), **base, **extra)
            elif it.kind == "polygon" and len(pts) >= 3:
                if rot:
                    pts = _rotated(pts, rot, centre)
                sub("polygon", points=" ".join(f"{_fmt(p.x())},{_fmt(p.y())}" for p in pts), **base)
        elif isinstance(it, SymbolTextItem):
            el = sub("text", x=_fmt(it.pos().x() - ox0), y=_fmt(it.pos().y() - oy0),
                     dominant_baseline="middle", text_anchor="middle", font_size=_fmt(it.size))
            el.text = it.content
        elif isinstance(it, LatexFragmentItem):
            if not it._svg_bytes:
                warnings.append("LaTeX label not rendered (pdflatex/dvisvgm missing?): "
                                "its source is saved, its drawing is not")
            g.append(bake_latex_group(it.latex_code, it.preamble_path, it._svg_bytes,
                                      it.pos().x() - ox0, it.pos().y() - oy0,
                                      it.display_width, it.display_height))
        elif isinstance(it, ImageItem):
            el, size = _image_element(it, it.pos().x() - ox0, it.pos().y() - oy0)
            if el is None:
                warnings.append(f"image {it.file_path}: nothing to embed")
                continue
            if size > _IMAGE_SIZE_NOTE:
                warnings.append(f"image {Path(it.file_path).name}: {size // 1000} kB embedded "
                                "in the symbol (and in every schematic that uses it)")
            g.append(el)
        elif isinstance(it, OpaqueSvgItem):
            try:
                el = ET.fromstring(it.xml)
            except ET.ParseError:
                continue
            dx, dy = it.pos().x() - ox0, it.pos().y() - oy0
            if dx or dy:
                wrap = ET.SubElement(g, f"{{{SVG_NS}}}g")
                wrap.set("transform", f"translate({_fmt(dx)} {_fmt(dy)})")
                wrap.append(el)
            else:
                g.append(el)
    for p in pins:
        sub("circle", cx=_fmt(p.pos().x() - ox0), cy=_fmt(p.pos().y() - oy0), r=_fmt(NODE_R),
            **{"class": "node", "data-node": p.name})
    if not pins:
        warnings.append("the symbol has no pins")
    return g, warnings


def g_to_items(g) -> tuple[SymbolMeta, list]:
    """The inverse of items_to_g: the items of a symbol's <g>."""
    from .shape_item import ShapeItem
    meta = SymbolMeta.from_g(g)
    nodes = (g.get("data-nodes") or "").split()
    items: list = []

    def style_kwargs(el, default_stroke="black"):
        stroke = el.get("stroke", default_stroke)
        fill   = el.get("fill", "none")
        kw = dict(stroke_color=_color_in(stroke, "#000000"),
                  line_style="none" if (stroke or "").strip().lower() == "none" else "solid",
                  line_width=float(el.get("stroke-width", "1") or 1),
                  fill_style="none" if (fill or "").strip().lower() in ("", "none") else "solid",
                  fill_color=_color_in(fill, "#ffffff"))
        da = (el.get("stroke-dasharray") or "").strip()
        if da:
            kw["line_style"] = "dotted" if da.startswith("1 ") else "dashed"
        return kw

    from .latex_fragment_item import LatexFragmentItem
    for el in list(g):
        if callable(el.tag):
            continue
        tag = _local(el.tag)
        xml = ET.tostring(el, encoding="unicode")
        if tag == "g" and el.get("class") == "latex":
            try:
                items.append(LatexFragmentItem(
                    el.get("data-latex", ""), el.get("data-preamble", ""),
                    int(round(float(el.get("data-w", 40)))), int(round(float(el.get("data-h", 20)))),
                    QPointF(float(el.get("data-x", 0)), float(el.get("data-y", 0)))))
            except ValueError:
                items.append(OpaqueSvgItem(xml))
            continue
        if el.get("transform") and tag != "g":
            items.append(OpaqueSvgItem(xml)); continue
        try:
            if tag == "circle" and el.get("class") == "node":
                name = el.get("data-node", "")
                number = nodes.index(name) + 1 if name in nodes else len(nodes) + 1
                items.append(SymbolPinItem(name, number, QPointF(float(el.get("cx", 0)), float(el.get("cy", 0)))))
            elif tag == "circle":
                cx, cy, r = float(el.get("cx", 0)), float(el.get("cy", 0)), float(el.get("r", 0))
                items.append(ShapeItem("ellipse", [QPointF(0, 0), QPointF(2 * r, 2 * r)], pos=QPointF(cx - r, cy - r), **style_kwargs(el)))
            elif tag == "ellipse":
                cx, cy = float(el.get("cx", 0)), float(el.get("cy", 0))
                rx, ry = float(el.get("rx", 0)), float(el.get("ry", 0))
                items.append(ShapeItem("ellipse", [QPointF(0, 0), QPointF(2 * rx, 2 * ry)], pos=QPointF(cx - rx, cy - ry), **style_kwargs(el)))
            elif tag == "rect":
                x, y = float(el.get("x", 0)), float(el.get("y", 0))
                w, h = float(el.get("width", 0)), float(el.get("height", 0))
                items.append(ShapeItem("rect", [QPointF(0, 0), QPointF(w, h)], pos=QPointF(x, y), **style_kwargs(el)))
            elif tag == "line":
                x1, y1 = float(el.get("x1", 0)), float(el.get("y1", 0))
                x2, y2 = float(el.get("x2", 0)), float(el.get("y2", 0))
                items.append(ShapeItem("line", [QPointF(0, 0), QPointF(x2 - x1, y2 - y1)], pos=QPointF(x1, y1), **style_kwargs(el)))
            elif tag in ("polyline", "polygon"):
                nums = [float(v) for v in re.split(r"[\s,]+", (el.get("points") or "").strip()) if v]
                pts = [QPointF(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
                if len(pts) < 2:
                    items.append(OpaqueSvgItem(xml)); continue
                kind = "polygon"
                kw = style_kwargs(el)
                if tag == "polyline":
                    closed = len(pts) >= 4 and abs(pts[0].x() - pts[-1].x()) < 1e-6 and abs(pts[0].y() - pts[-1].y()) < 1e-6
                    if closed:
                        pts = pts[:-1]
                    elif kw["fill_style"] == "solid" and len(pts) >= 3:
                        # SVG fills a polyline as if closed: a filled arrow
                        # head written as an open polyline (Martijn's XQN2E,
                        # 2026-09-27) is a polygon for the editor.
                        pass
                    else:
                        kind = "line"
                if float(el.get("stroke-width", "1") or 1) == 0:
                    kw["line_style"] = "none"       # a zero stroke is no stroke
                anchor = pts[0]
                items.append(ShapeItem(kind, [QPointF(p.x() - anchor.x(), p.y() - anchor.y()) for p in pts], pos=anchor, **kw))
            elif tag == "text":
                items.append(SymbolTextItem((el.text or "").strip(), float(el.get("font-size", "8") or 8),
                                            QPointF(float(el.get("x", 0)), float(el.get("y", 0)))))
            else:
                items.append(OpaqueSvgItem(xml))
        except (TypeError, ValueError):
            items.append(OpaqueSvgItem(xml))
    return meta, items


def loadable_groups(groups: dict) -> dict:
    """The symbols of a file that the library can load (they have a
    drawing). The editor opens every group, also an empty one saved as a
    named start (Anton, 2026-09-27: saving first is what users do)."""
    from .symbol_library import _geometry_bbox
    return {n: g for n, g in groups.items() if _geometry_bbox(g) is not None}


def read_symbol_file(path) -> tuple[ET.ElementTree, dict]:
    """Parse a symbol file; returns (tree, {name: <g>}) for every symbol group."""
    ET.register_namespace("", SVG_NS)
    tree = ET.parse(path)
    groups = {}
    for g in tree.getroot().iter(f"{{{SVG_NS}}}g"):
        if g.get("id") and g.get("data-prefix") is not None:
            groups[g.get("id")] = g
    return tree, groups


def write_symbol(path, g: ET.Element, replace_id: str | None = None) -> None:
    """Write *g* into the symbol file: replace the group of the same id in
    place, or append it to the file's <defs> (created for a new file).
    *replace_id* names the group the symbol was loaded from: a symbol
    renamed in the editor replaces that group instead of being added next
    to it (Anton, 2026-09-27: a rename left the old symbol in the file)."""
    ET.register_namespace("", SVG_NS)
    path = Path(path)
    if path.is_file():
        tree = ET.parse(path)
        root = tree.getroot()
    else:
        root = ET.Element(f"{{{SVG_NS}}}svg")
        tree = ET.ElementTree(root)
    parent_map = {c: p for p in root.iter() for c in p}

    def find(sym_id):
        return next((e for e in root.iter(f"{{{SVG_NS}}}g")
                     if e.get("id") == sym_id and e.get("data-prefix") is not None), None)
    old = find(replace_id) if replace_id else None
    if old is None:
        old = find(g.get("id"))
    if old is not None:
        parent = parent_map[old]
        idx = list(parent).index(old)
        parent.remove(old)
        parent.insert(idx, g)
    else:
        defs = root.find(f"{{{SVG_NS}}}defs")
        if defs is None:
            defs = ET.SubElement(root, f"{{{SVG_NS}}}defs")
        defs.append(g)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=False)


def validate(meta: SymbolMeta, items) -> list[str]:
    """Errors that make a symbol unusable (empty list = fine)."""
    errors: list[str] = []
    if not re.match(r"^[A-Za-z0-9_\-]+$", meta.name or ""):
        errors.append("the symbol name must be letters, digits, '_' or '-' (it is the id in the file)")
    pins = [i for i in items if isinstance(i, SymbolPinItem)]
    names = [p.name for p in pins]
    if len(set(names)) != len(names):
        errors.append("pin names must be unique")
    if any(not n or " " in n for n in names):
        errors.append("every pin needs a name without spaces")
    numbers = sorted(p.number for p in pins)
    if numbers and numbers != list(range(1, len(pins) + 1)):
        errors.append("pin numbers must run 1, 2, ... without gaps")
    try:
        from SLiCAP.SLiCAPprotos import _DEVICES
        dev = _DEVICES.get(meta.prefix)
    except Exception:
        dev = None
    if dev is not None and getattr(dev, "nNodes", -1) >= 0 and len(pins) != dev.nNodes:
        errors.append(f"a '{meta.prefix}' element has {dev.nNodes} pins, the drawing has {len(pins)}")
    return errors


# ── dialogs ──────────────────────────────────────────────────────────────────

class PinDialog(QDialog):
    def __init__(self, name: str = "", number: int = 1, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Pin")
        lay = QFormLayout(self)
        self._name = QLineEdit(name); fix_chars(self._name, 16)
        self._number = QSpinBox(); self._number.setRange(1, 99); self._number.setValue(number)
        fit_contents(self._number)
        lay.addRow("Node name:", self._name)
        lay.addRow("Order:", self._number)
        lay.addRow(QLabel("Names are free; the ORDER is the netlist order of the element."))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def name(self) -> str: return self._name.text().strip()
    def number(self) -> int: return self._number.value()


class SymbolTextDialog(QDialog):
    def __init__(self, content: str = "+", size: float = 8.0, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Symbol text")
        lay = QFormLayout(self)
        self._text = QLineEdit(content); fix_chars(self._text, 20)
        self._size = QDoubleSpinBox(); self._size.setRange(1, 100); self._size.setDecimals(1); self._size.setValue(size)
        fit_contents(self._size)
        lay.addRow("Text:", self._text)
        lay.addRow("Size:", self._size)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def content(self) -> str: return self._text.text()
    def size(self) -> float: return self._size.value()


class SymbolPropertiesDialog(QDialog):
    """The symbol's metadata: name, prefix, model, parameters, references,
    description, info link, pin-name display."""

    def __init__(self, meta: SymbolMeta, sch_type: str = "slicap", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Symbol properties")
        lay = QVBoxLayout(self)
        box = QGroupBox("Identity"); f = QFormLayout(box)
        self._name = QLineEdit(meta.name); fix_chars(self._name, 20)
        f.addRow("Name (id):", self._name)
        self._prefix = QComboBox(); self._prefix.setEditable(True)
        try:
            from SLiCAP.SLiCAPprotos import _DEVICES
            self._prefix.addItems(sorted(_DEVICES.keys()))
        except Exception:
            self._prefix.addItems(["R", "C", "L", "V", "I", "E", "F", "G", "H", "X"])
        self._prefix.setCurrentText(meta.prefix)
        f.addRow("Prefix (element type):", self._prefix)
        self._model = QLineEdit(meta.model); fix_chars(self._model, 16)
        f.addRow("Model:", self._model)
        self._model_show = QCheckBox("show the model on the schematic"); self._model_show.setChecked(meta.model_show)
        f.addRow("", self._model_show)
        self._refs = QLineEdit(" ".join(meta.refs)); fix_chars(self._refs, 16)
        f.addRow("References (space separated):", self._refs)
        self._descr = QLineEdit(meta.description); fix_chars(self._descr, 40)
        f.addRow("Description:", self._descr)
        self._info = QLineEdit(meta.info); fix_chars(self._info, 40)
        f.addRow("Info link:", self._info)
        self._pinnames = QCheckBox("draw the pin names on the schematic"); self._pinnames.setChecked(meta.show_pinnames)
        f.addRow("", self._pinnames)
        lay.addWidget(box)

        pbox = QGroupBox("Parameters (name, default, show name, show value)"); pl = QVBoxLayout(pbox)
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Name", "Default", "Show name", "Show value"])
        for row in meta.params:
            self._add_row(*row)
        pl.addWidget(self._table)
        btns = QHBoxLayout()
        add = QPushButton("Add"); add.clicked.connect(lambda: self._add_row("", "", False, True))
        rem = QPushButton("Remove"); rem.clicked.connect(self._remove_row)
        btns.addWidget(add); btns.addWidget(rem); btns.addStretch(1)
        pl.addLayout(btns)
        lay.addWidget(pbox)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _add_row(self, name="", default="", show_name=False, show_value=True):
        r = self._table.rowCount(); self._table.insertRow(r)
        self._table.setItem(r, 0, QTableWidgetItem(str(name)))
        self._table.setItem(r, 1, QTableWidgetItem(str(default)))
        for col, flag in ((2, show_name), (3, show_value)):
            it = QTableWidgetItem(); it.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            it.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self._table.setItem(r, col, it)

    def _remove_row(self):
        r = self._table.currentRow()
        if r >= 0:
            self._table.removeRow(r)

    def meta(self) -> SymbolMeta:
        params = []
        for r in range(self._table.rowCount()):
            name = (self._table.item(r, 0).text() if self._table.item(r, 0) else "").strip()
            if not name:
                continue
            default = (self._table.item(r, 1).text() if self._table.item(r, 1) else "").strip()
            sn = self._table.item(r, 2).checkState() == Qt.Checked
            sv = self._table.item(r, 3).checkState() == Qt.Checked
            params.append([name, default, sn, sv])
        return SymbolMeta(name=self._name.text().strip(), prefix=self._prefix.currentText().strip() or "X",
                          model=self._model.text().strip(), model_show=self._model_show.isChecked(),
                          params=params, refs=self._refs.text().split(),
                          description=self._descr.text().strip(), info=self._info.text().strip(),
                          show_pinnames=self._pinnames.isChecked())
