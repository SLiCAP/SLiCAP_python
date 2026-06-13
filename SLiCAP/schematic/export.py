"""
Schematic export utilities — shared by the GUI (window.py) and CLI (cli.py).

SVG export builds the file manually by iterating scene items and embedding
symbol SVG content inline, producing fully vector output.  PDF and Print
load the generated SVG through QSvgRenderer and render it to QPainter on
QPrinter, which also produces vector PDF/print output.
"""
from __future__ import annotations
import base64
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from PySide6.QtCore import QRectF, QPointF, QBuffer, QIODevice

_MARGIN             = 20    # scene-unit padding around bounding box
_SCENE_UNITS_PER_MM = 2.0   # 1 mm = 2 scene units
_SVG_NS             = "http://www.w3.org/2000/svg"
_XLINK_NS           = "http://www.w3.org/1999/xlink"

ET.register_namespace("",      _SVG_NS)
ET.register_namespace("xlink", _XLINK_NS)

_latex_uid = 0   # incremented per inlined LaTeX SVG to keep IDs unique
_image_uid = 0   # incremented per inlined image SVG to keep IDs unique

_SVG_LENGTH_RE = re.compile(
    r"^\s*([\d.+\-eE]+)\s*(px|pt|mm|cm|in|em|ex|pc|%)?\s*$", re.IGNORECASE)
_URL_REF_RE    = re.compile(r'url\(#([^)]+)\)')

_UNIT_TO_PX = {
    'px': 1.0, 'pt': 96.0 / 72.0, 'pc': 96.0 / 6.0,
    'mm': 96.0 / 25.4, 'cm': 96.0 / 2.54, 'in': 96.0,
}


def _parse_svg_length(s, fallback: float) -> float:
    """Parse an SVG length string, stripping any unit suffix (mm, pt, px …)."""
    m = _SVG_LENGTH_RE.match(str(s)) if s else None
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return fallback


def _svg_length_to_px(s, fallback: float) -> float:
    """Parse SVG length and convert to CSS pixels (96 dpi).

    SVGs with physical units (mm, cm, in, pt) but no viewBox use pixel
    coordinates internally; the width/height attributes only specify the
    physical rendered size.  Converting to px gives the correct viewport
    size to use as the scale denominator when inlining the SVG.
    """
    m = _SVG_LENGTH_RE.match(str(s)) if s else None
    if m:
        try:
            val  = float(m.group(1))
            unit = (m.group(2) or 'px').lower()
            return val * _UNIT_TO_PX.get(unit, 1.0)
        except ValueError:
            pass
    return fallback


def export_bounds(scene) -> QRectF:
    from .border_item import BorderItem
    for item in scene.items():
        if isinstance(item, BorderItem):
            pos = item.pos()
            r   = item.rect()
            return QRectF(pos.x(), pos.y(), r.width(), r.height())
    b = scene.itemsBoundingRect()
    if b.isEmpty():
        b = QRectF(0, 0, 200, 200)
    return b.adjusted(-_MARGIN, -_MARGIN, _MARGIN, _MARGIN)


def _qhex(c) -> str:
    return f"#{c.red():02x}{c.green():02x}{c.blue():02x}"


def _build_svg(scene, title: str = "") -> bytes:
    """Render all scene items to a vector SVG document, returning UTF-8 bytes."""
    from .component_item import ComponentItem
    from .wire_item import WireItem
    from .junction_item import JunctionItem
    from .free_text_item import FreeTextItem
    from .command_item import CommandItem
    from .analysis_item import AnalysisItem
    from .hyperlink_item import HyperlinkItem
    from .shape_item import ShapeItem
    from .image_item import ImageItem
    from .latex_fragment_item import LatexFragmentItem
    from .parameter_item import ParameterItem
    from .config import (
        WIRE_COLOR, WIRE_WIDTH,
        JUNCTION_COLOR, JUNCTION_RADIUS,
        COMP_LABEL_COLOR, COMP_LABEL_FONT_SIZE,
        NET_LABEL_COLOR, NET_LABEL_FONT_SIZE,
        TEXT_COLOR, TEXT_FONT_SIZE, TEXT_FONT_FAMILY, TEXT_FONT,
        HYPERLINK_COLOR, HYPERLINK_FONT_SIZE, HYPERLINK_FONT_FAMILY, HYPERLINK_UNDERLINE,
        COMMAND_COLOR, COMMAND_FONT_SIZE, COMMAND_FONT,
    )

    bounds = export_bounds(scene)
    vx, vy = bounds.x(), bounds.y()
    vw, vh = bounds.width(), bounds.height()

    root = ET.Element(f"{{{_SVG_NS}}}svg")
    root.set("version", "1.1")
    root.set("viewBox", f"{vx:.3f} {vy:.3f} {vw:.3f} {vh:.3f}")
    root.set("width",  f"{int(vw)}")
    root.set("height", f"{int(vh)}")
    if title:
        ET.SubElement(root, f"{{{_SVG_NS}}}title").text = title

    # Collects glyph <defs> extracted from inlined LaTeX SVGs.
    defs = ET.SubElement(root, f"{{{_SVG_NS}}}defs")

    bg = ET.SubElement(root, f"{{{_SVG_NS}}}rect")
    bg.set("x", f"{vx:.3f}"); bg.set("y", f"{vy:.3f}")
    bg.set("width", f"{vw:.3f}"); bg.set("height", f"{vh:.3f}")
    bg.set("fill", "white")

    wire_color = _qhex(WIRE_COLOR)
    junc_color = _qhex(JUNCTION_COLOR)
    lbl_color  = _qhex(COMP_LABEL_COLOR)
    net_color  = _qhex(NET_LABEL_COLOR)
    txt_color  = _qhex(TEXT_COLOR)
    cmd_color  = _qhex(COMMAND_COLOR)
    lnk_color  = _qhex(HYPERLINK_COLOR)

    for item in reversed(scene.items()):
        if item.parentItem() is not None:
            continue   # child items (labels, net labels) handled by their parents

        from .border_item import BorderItem
        if isinstance(item, BorderItem):
            if item.show_in_export:
                _border_rect(root, item)
            continue
        if isinstance(item, WireItem):
            _wire(root, item, wire_color, WIRE_WIDTH, net_color, NET_LABEL_FONT_SIZE)
        elif isinstance(item, JunctionItem):
            _junction(root, item, junc_color, JUNCTION_RADIUS)
        elif isinstance(item, ComponentItem):
            _component(root, defs, item, lbl_color, COMP_LABEL_FONT_SIZE)
        elif isinstance(item, ImageItem):
            _image_svg(root, defs, item)
        elif isinstance(item, (LatexFragmentItem, ParameterItem)):
            if item._svg_bytes:
                pos = item.pos()
                _inline_image_svg(root, defs, item._svg_bytes,
                                  pos.x(), pos.y(),
                                  item.display_width, item.display_height)
        elif isinstance(item, (FreeTextItem, CommandItem, AnalysisItem)):
            is_cmd = isinstance(item, (CommandItem, AnalysisItem))
            _text_block(
                root, item,
                cmd_color if is_cmd else txt_color,
                COMMAND_FONT_SIZE if is_cmd else TEXT_FONT_SIZE,
                "monospace" if is_cmd else TEXT_FONT_FAMILY,
                COMMAND_FONT if is_cmd else TEXT_FONT,
            )
        elif isinstance(item, HyperlinkItem):
            _hyperlink_block(root, item, lnk_color,
                             HYPERLINK_FONT_SIZE, HYPERLINK_FONT_FAMILY,
                             HYPERLINK_UNDERLINE)
        elif isinstance(item, ShapeItem):
            _shape(root, item)

    try:
        ET.indent(root, space="  ")
    except AttributeError:
        pass  # Python < 3.9
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def _wire(parent, item, stroke, width, net_color, net_fs):
    if len(item.points) < 2:
        return
    el = ET.SubElement(parent, f"{{{_SVG_NS}}}polyline")
    el.set("points", " ".join(f"{p.x():.2f},{p.y():.2f}" for p in item.points))
    el.set("fill", "none")
    el.set("stroke", stroke)
    el.set("stroke-width", f"{width:.2f}")
    el.set("stroke-linecap", "round")
    el.set("stroke-linejoin", "round")

    if (item.display_name and item.net_name
            and item._net_label is not None and item._net_label.isVisible()):
        from PySide6.QtGui import QFontMetricsF
        lpos = item._net_label.pos()
        # QGraphicsSimpleTextItem.pos() is the top-left of the bounding rect.
        # SVG <text y> anchors the baseline; add the font ascent to align correctly.
        fm = QFontMetricsF(item._net_label.font())
        t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        t.set("x", f"{lpos.x():.2f}")
        t.set("y", f"{lpos.y() + fm.ascent():.2f}")
        t.set("font-family", "sans-serif")
        t.set("font-size", f"{net_fs}pt")
        t.set("fill", net_color)
        t.text = item.net_name


def _junction(parent, item, fill, radius):
    el = ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
    el.set("cx", f"{item.pos().x():.2f}")
    el.set("cy", f"{item.pos().y():.2f}")
    el.set("r",  f"{radius:.2f}")
    el.set("fill", fill)


def _border_rect(parent, item):
    pos = item.pos()
    r   = item.rect()
    el  = ET.SubElement(parent, f"{{{_SVG_NS}}}rect")
    el.set("x",              f"{pos.x():.2f}")
    el.set("y",              f"{pos.y():.2f}")
    el.set("width",          f"{r.width():.2f}")
    el.set("height",         f"{r.height():.2f}")
    el.set("fill",           "none")
    el.set("stroke",         "#5050b4")
    el.set("stroke-width",   "0.8")
    el.set("stroke-dasharray", "4 2")


def _image_svg(parent, defs, item) -> None:
    """Dispatch to vector-inline (SVG source) or base64 PNG (everything else)."""
    from pathlib import Path as _Path
    ext = _Path(item.file_path).suffix.lower()
    pos = item.pos()
    x, y = pos.x(), pos.y()
    w, h = item.display_width, item.display_height

    if ext == ".svg":
        try:
            svg_bytes = _Path(item.file_path).read_bytes()
        except OSError:
            return
        _inline_image_svg(parent, defs, svg_bytes, x, y, w, h)
        return

    # Raster path (PNG, JPG, PDF rendered to pixmap, etc.)
    px = item._pixmap
    if px is None or px.isNull():
        return
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    px.save(buf, "PNG")
    data = base64.b64encode(bytes(buf.data())).decode("ascii")
    buf.close()
    el = ET.SubElement(parent, f"{{{_SVG_NS}}}image")
    el.set("x",      f"{x:.2f}")
    el.set("y",      f"{y:.2f}")
    el.set("width",  f"{px.width()}")
    el.set("height", f"{px.height()}")
    el.set("href",   f"data:image/png;base64,{data}")


def _inline_image_svg(parent, defs, svg_bytes: bytes,
                      x: float, y: float, w: float, h: float) -> None:
    """
    Inline an SVG file as scaled vector content at scene position (x, y).

    Top-left corner is anchored at (x, y); content is scaled to fit w × h
    scene units.  IDs are prefixed to avoid collisions with other inlined SVGs.
    Any <defs> inside the embedded SVG are hoisted to the output document's
    top-level <defs>.
    """
    global _image_uid
    try:
        sym = ET.fromstring(svg_bytes.decode("utf-8", errors="replace"))
    except ET.ParseError:
        return

    # Determine natural size from viewBox, then width/height attributes
    vb_str = sym.get("viewBox", "")
    parts  = vb_str.split() if vb_str else []
    if len(parts) == 4:
        try:
            vb_x, vb_y, vb_w, vb_h = (float(p) for p in parts)
        except ValueError:
            vb_x, vb_y, vb_w, vb_h = 0.0, 0.0, 0.0, 0.0
    else:
        # Convert to CSS px so content coordinates (always in px) match.
        vb_w = _svg_length_to_px(sym.get("width"),  w)
        vb_h = _svg_length_to_px(sym.get("height"), h)
        vb_x, vb_y = 0.0, 0.0

    if vb_w <= 0 or vb_h <= 0:
        return

    pfx = f"img{_image_uid}-"
    _image_uid += 1
    _rename_svg_ids(sym, pfx)

    defs_tag = f"{{{_SVG_NS}}}defs"
    content  = []
    for child in list(sym):
        if child.tag == defs_tag:
            for grandchild in list(child):
                defs.append(grandchild)
        else:
            content.append(child)

    sx = w / vb_w
    sy = h / vb_h
    transform = f"translate({x:.3f},{y:.3f}) scale({sx:.6f},{sy:.6f})"
    if vb_x or vb_y:
        transform += f" translate({-vb_x:.3f},{-vb_y:.3f})"

    g = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
    g.set("transform", transform)
    for child in content:
        g.append(child)


def _component(parent, defs, item, lbl_color, lbl_fs):
    px, py = item.pos().x(), item.pos().y()
    rot    = item.rotation()
    sx     = -1 if item.h_flip else 1
    sy     = -1 if item.v_flip else 1

    parts = [f"translate({px:.2f},{py:.2f})"]
    if rot:
        parts.append(f"rotate({rot:.3f})")
    if sx != 1 or sy != 1:
        parts.append(f"scale({sx},{sy})")

    try:
        sym = ET.fromstring(item._svg_bytes.decode("utf-8", errors="replace"))
    except ET.ParseError:
        return

    g = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
    g.set("transform", " ".join(parts))
    g.set("font-size", f"{lbl_fs}pt")  # baseline for text within symbol (e.g. +/-)
    for child in sym:
        g.append(child)

    for lbl in item._labels.values():
        sp = lbl.mapToScene(QPointF(0.0, 0.0))
        if lbl._text:
            t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
            t.set("x", f"{sp.x():.2f}")
            t.set("y", f"{sp.y():.2f}")
            t.set("font-family", "sans-serif")
            t.set("font-size", f"{lbl_fs}pt")
            t.set("fill", lbl_color)
            # For h_flipped components the label's local origin is baseline-right;
            # use text-anchor="end" so SVG anchors the text on the same side.
            if item.h_flip:
                t.set("text-anchor", "end")
            t.text = lbl._text
        elif lbl._svg_renderer is not None:
            _latex_label(parent, defs, item, lbl, sp, lbl_color, lbl_fs)


def _latex_label(parent, defs, item, lbl, sp, lbl_color, lbl_fs):
    """Inline a LaTeX property label as scaled vector SVG content."""
    from .latex_label import render_expression

    raw_val   = item._prop_value(lbl.prop_key)
    svg_bytes = render_expression(raw_val)

    if svg_bytes is None:
        text = item._prop_text(lbl.prop_key)
        if text:
            t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
            t.set("x", f"{sp.x():.2f}")
            t.set("y", f"{sp.y():.2f}")
            t.set("font-family", "sans-serif")
            t.set("font-size", f"{lbl_fs}pt")
            t.set("fill", lbl_color)
            if item.h_flip:
                t.set("text-anchor", "end")
            t.text = text
        return

    rect     = lbl._svg_rect   # QRectF(prefix_w, -h, svg_w, h) in label-local coords
    svg_h    = rect.height()
    svg_w    = rect.width()
    prefix_w = lbl._prefix_w   # 0 when no prefix

    # sp = scene position of label local (0,0).
    # local (0,0) is the bottom of the SVG (bottom-aligned, matching text baseline).
    # For h_flip=False: local (0,0) is bottom-left  → prefix starts at sp.x()
    # For h_flip=True:  local (0,0) is bottom-right → content ends at sp.x()
    if item.h_flip:
        svg_x    = sp.x() - svg_w
        prefix_x = sp.x() - svg_w - prefix_w
    else:
        prefix_x = sp.x()
        svg_x    = sp.x() + prefix_w

    if lbl._prefix:
        t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        t.set("x", f"{prefix_x:.2f}")
        # Prefix text centred on SVG: baseline at SVG centre (sp.y() - svg_h/2)
        t.set("y", f"{sp.y() - svg_h / 2:.2f}")
        t.set("font-family", "sans-serif")
        t.set("font-size", str(lbl_fs))
        t.set("fill", lbl_color)
        t.text = lbl._prefix

    _inline_latex_svg(parent, defs, svg_bytes, svg_x, sp.y(), svg_w, svg_h)


def _inline_latex_svg(parent, defs, svg_bytes, x, y, w, h):
    """
    Inline LaTeX SVG content as a positioned, scaled <g> element.

    Glyph <defs> are hoisted to the output SVG's top-level <defs> so that
    QSvgRenderer renders them as vector paths rather than rasterising them.
    IDs are prefixed with a unique token to avoid collisions when multiple
    expressions are inlined into the same document.
    """
    global _latex_uid
    try:
        sym = ET.fromstring(svg_bytes.decode("utf-8", errors="replace"))
    except ET.ParseError:
        return

    vb_str = sym.get("viewBox", "")
    parts  = vb_str.split() if vb_str else []
    if len(parts) == 4:
        vb_x, vb_y, vb_w, vb_h = (float(p) for p in parts)
    else:
        vb_x, vb_y, vb_w, vb_h = 0.0, 0.0, w, h
    if vb_w <= 0 or vb_h <= 0:
        return

    pfx = f"lt{_latex_uid}-"
    _latex_uid += 1
    _rename_svg_ids(sym, pfx)

    defs_tag = f"{{{_SVG_NS}}}defs"
    content  = []
    for child in list(sym):
        if child.tag == defs_tag:
            for grandchild in list(child):
                defs.append(grandchild)
        else:
            content.append(child)

    sx = w / vb_w
    sy = h / vb_h
    # y is the SVG bottom (bottom-aligned at label origin, matching text baseline).
    # QSvgRenderer renders _svg_rect from y-h to y in canvas space.
    transform = f"translate({x:.3f},{y - h:.3f}) scale({sx:.6f},{sy:.6f})"
    if vb_x or vb_y:
        transform += f" translate({-vb_x:.3f},{-vb_y:.3f})"

    g = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
    g.set("transform", transform)
    for child in content:
        g.append(child)


def _rename_svg_ids(element, prefix: str) -> None:
    """Prefix all id attributes and internal #-references throughout an ET tree.

    Handles both href/xlink:href fragment references and url(#...) references
    that appear in presentation attributes such as marker-start, marker-end,
    fill, stroke, clip-path, filter, mask, and inline style strings.
    """
    xhref = f"{{{_XLINK_NS}}}href"

    def _rewrite_url(val: str) -> str:
        return _URL_REF_RE.sub(lambda m: f"url(#{prefix}{m.group(1)})", val)

    for el in element.iter():
        id_val = el.get("id")
        if id_val:
            el.set("id", prefix + id_val)
        for attr, val in list(el.attrib.items()):
            if not val:
                continue
            if attr in (xhref, "href"):
                if val.startswith("#"):
                    el.set(attr, "#" + prefix + val[1:])
            elif "url(#" in val:
                el.set(attr, _rewrite_url(val))


def _text_block(parent, item, color, fs, family, font=None):
    from PySide6.QtGui import QFontMetricsF
    pos = item.pos()
    # QGraphicsTextItem.pos() is the top-left of the document frame.
    # SVG <text y="…"> anchors the baseline; offset by the document margin and
    # the font ascent so the first baseline lands in the right place.
    doc_margin = item.document().documentMargin() if hasattr(item, 'document') else 0.0
    if font is not None:
        fm      = QFontMetricsF(font)
        ascent  = fm.ascent()
        line_h  = fm.lineSpacing()
    else:
        ascent = fs * 0.8
        line_h = fs * 1.5
    x0         = pos.x() + doc_margin
    baseline_y = pos.y() + doc_margin + ascent
    lines = item.toPlainText().splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        t.set("x", f"{x0:.2f}")
        t.set("y", f"{baseline_y + i * line_h:.2f}")
        t.set("font-family", family)
        t.set("font-size", f"{fs}pt")
        t.set("fill", color)
        t.text = line


_DASH_ARRAY = {
    "solid":    None,
    "dashed":   "8,4",
    "dotted":   "2,4",
    "dash-dot": "8,4,2,4",
}


def _shape(parent, item) -> None:
    """Render a ShapeItem to SVG with full style support."""
    import math
    ox, oy = item.pos().x(), item.pos().y()
    pts    = [(ox + p.x(), oy + p.y()) for p in item.rel_points]
    lw     = item.line_width
    fill   = item.fill_color if item.fill_style == "solid" else "none"

    stroke_attrs = {
        "stroke":           item.stroke_color,
        "stroke-width":     f"{lw:.2f}",
        "fill":             fill,
        "stroke-linecap":   "round",
        "stroke-linejoin":  "round",
    }
    da = _DASH_ARRAY.get(item.line_style)
    if da:
        stroke_attrs["stroke-dasharray"] = da

    if item.kind == "line" and len(pts) >= 2:
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polyline")
        el.set("points", " ".join(f"{x:.2f},{y:.2f}" for x, y in pts))
        for k, v in stroke_attrs.items():
            el.set(k, v)
        # line ends drawn as separate open geometry (no SVG markers needed)
        _svg_line_end(parent, pts[1],  pts[0],  item.line_end_start, lw, item.stroke_color)
        _svg_line_end(parent, pts[-2], pts[-1],  item.line_end_end,   lw, item.stroke_color)

    elif item.kind == "rect" and len(pts) == 2:
        x0 = min(pts[0][0], pts[1][0]); y0 = min(pts[0][1], pts[1][1])
        w  = abs(pts[1][0] - pts[0][0]); h  = abs(pts[1][1] - pts[0][1])
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}rect")
        el.set("x", f"{x0:.2f}"); el.set("y", f"{y0:.2f}")
        el.set("width", f"{w:.2f}"); el.set("height", f"{h:.2f}")
        for k, v in stroke_attrs.items():
            el.set(k, v)

    elif item.kind == "circle" and len(pts) == 2:
        cx, cy = pts[0]
        r = math.hypot(pts[1][0] - cx, pts[1][1] - cy)
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
        el.set("cx", f"{cx:.2f}"); el.set("cy", f"{cy:.2f}")
        el.set("r",  f"{r:.2f}")
        for k, v in stroke_attrs.items():
            el.set(k, v)


def _svg_line_end(parent, p_from, p_to, style: str, lw: float, color: str) -> None:
    """Draw a line-end marker (arrow / dot / diamond) as plain SVG elements."""
    import math
    if style == "none":
        return
    dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    size = max(16.0, lw * 6)
    ux, uy = dx / length, dy / length
    base = {"stroke": color, "stroke-width": f"{lw:.2f}",
            "stroke-linecap": "round"}

    if style == "arrow":
        px_, py_ = -uy, ux
        for side in (1, -1):
            ax = p_to[0] - size * ux + side * size * 0.4 * px_
            ay = p_to[1] - size * uy + side * size * 0.4 * py_
            al = ET.SubElement(parent, f"{{{_SVG_NS}}}line")
            al.set("x1", f"{p_to[0]:.2f}"); al.set("y1", f"{p_to[1]:.2f}")
            al.set("x2", f"{ax:.2f}");       al.set("y2", f"{ay:.2f}")
            al.set("fill", "none")
            for k, v in base.items(): al.set(k, v)

    elif style == "dot":
        r = size * 0.35
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
        el.set("cx", f"{p_to[0]:.2f}"); el.set("cy", f"{p_to[1]:.2f}")
        el.set("r",  f"{r:.2f}")
        el.set("fill", color); el.set("stroke", "none")

    elif style == "diamond":
        h, w = size * 0.9, size * 0.4
        px_, py_ = -uy, ux
        tip  = p_to
        back = (p_to[0] - h*ux,          p_to[1] - h*uy)
        left = (p_to[0] - h/2*ux + w*px_, p_to[1] - h/2*uy + w*py_)
        rght = (p_to[0] - h/2*ux - w*px_, p_to[1] - h/2*uy - w*py_)
        pts_str = " ".join(f"{x:.2f},{y:.2f}"
                           for x, y in [tip, left, back, rght])
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polygon")
        el.set("points", pts_str)
        el.set("fill", color); el.set("stroke", "none")


def _hyperlink_block(parent, item, color, fs, family, underline: bool):
    """Render a HyperlinkItem as an SVG <a href> element."""
    from PySide6.QtGui import QFontMetricsF
    pos   = item.pos()
    label = item.label or item.url
    url   = item.url
    # QGraphicsSimpleTextItem.pos() is the top-left; add ascent for SVG baseline.
    fm = QFontMetricsF(item.font())
    a = ET.SubElement(parent, f"{{{_SVG_NS}}}a")
    a.set("href", url)
    a.set(f"{{{_XLINK_NS}}}href", url)   # SVG 1.1 compatibility
    t = ET.SubElement(a, f"{{{_SVG_NS}}}text")
    t.set("x", f"{pos.x():.2f}")
    t.set("y", f"{pos.y() + fm.ascent():.2f}")
    t.set("font-family", family)
    t.set("font-size", f"{fs}pt")
    t.set("fill", color)
    if underline:
        t.set("text-decoration", "underline")
    t.text = label


def export_svg(scene, output_path: Path, title: str = "") -> None:
    output_path.write_bytes(_build_svg(scene, title))


def export_pdf(scene, output_path: Path) -> None:
    import cairosvg
    cairosvg.svg2pdf(bytestring=_build_svg(scene), write_to=str(output_path))


def print_scene(scene, parent=None) -> None:
    import os, tempfile
    import cairosvg
    from PySide6.QtPrintSupport import QPrinter, QPrintDialog
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtGui import QPainter
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QDoubleSpinBox, QCheckBox, QDialogButtonBox,
    )

    # ── step 1: printer / paper ───────────────────────────────────────────────
    printer = QPrinter(QPrinter.HighResolution)
    if QPrintDialog(printer, parent).exec() != QPrintDialog.Accepted:
        return

    # ── step 2: scale options ─────────────────────────────────────────────────
    bounds = export_bounds(scene)
    svg_w, svg_h = bounds.width(), bounds.height()

    page_rect = QRectF(printer.pageRect(QPrinter.DevicePixel))
    dpmm      = printer.resolution() / 25.4
    nat_w     = svg_w / _SCENE_UNITS_PER_MM * dpmm
    nat_h     = svg_h / _SCENE_UNITS_PER_MM * dpmm

    fit_pct = 0.0
    if nat_w > 0 and nat_h > 0:
        fit_pct = min(page_rect.width() / nat_w,
                      page_rect.height() / nat_h) * 100.0

    from PySide6.QtCore import Qt
    scale_dlg = QDialog(parent, Qt.Window)
    scale_dlg.setWindowTitle("Print Scale")
    vlay = QVBoxLayout(scale_dlg)

    fit_cb = QCheckBox("Fit to page")
    fit_cb.setChecked(True)
    vlay.addWidget(fit_cb)

    hlay = QHBoxLayout()
    hlay.addWidget(QLabel("Scale:"))
    scale_sb = QDoubleSpinBox()
    scale_sb.setRange(10.0, 500.0)
    scale_sb.setSingleStep(5.0)
    scale_sb.setDecimals(1)
    scale_sb.setSuffix(" %")
    scale_sb.setValue(round(fit_pct, 1) if fit_pct > 0 else 100.0)
    scale_sb.setEnabled(False)
    hlay.addWidget(scale_sb)
    if fit_pct > 0:
        hlay.addWidget(QLabel(f"(fit = {fit_pct:.1f} %)"))
    vlay.addLayout(hlay)

    fit_cb.toggled.connect(lambda checked: scale_sb.setEnabled(not checked))

    btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    btns.accepted.connect(scale_dlg.accept)
    btns.rejected.connect(scale_dlg.reject)
    vlay.addWidget(btns)

    if scale_dlg.exec() != QDialog.Accepted:
        return

    # ── step 3: compute render rect ───────────────────────────────────────────
    if fit_cb.isChecked():
        s = min(page_rect.width() / nat_w, page_rect.height() / nat_h) if nat_w > 0 and nat_h > 0 else 1.0
    else:
        s = scale_sb.value() / 100.0
    rw = nat_w * s
    rh = nat_h * s
    if rw > page_rect.width() or rh > page_rect.height():
        clamp = min(page_rect.width() / rw, page_rect.height() / rh)
        rw *= clamp
        rh *= clamp

    render_rect = QRectF(
        page_rect.x() + (page_rect.width()  - rw) / 2,
        page_rect.y() + (page_rect.height() - rh) / 2,
        rw, rh,
    )

    # ── step 4: cairosvg → PDF → raster → paint ──────────────────────────────
    pdf_bytes = cairosvg.svg2pdf(bytestring=_build_svg(scene))
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        tmp.write(pdf_bytes)
        tmp.close()
        doc = QPdfDocument(None)
        doc.load(tmp.name)
        pt      = doc.pagePointSize(0)
        img_dpi = max(printer.resolution(), 300)
        img_w   = max(1, round(pt.width()  / 72.0 * img_dpi))
        img_h   = max(1, round(pt.height() / 72.0 * img_dpi))
        qimg    = doc.render(0, QSize(img_w, img_h))
        doc.close()
    finally:
        os.unlink(tmp.name)

    painter = QPainter(printer)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.drawImage(render_rect, qimg)
    painter.end()
