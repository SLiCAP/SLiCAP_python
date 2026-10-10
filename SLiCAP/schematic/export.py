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
from .fonts import svg_family, register_pdf_fonts

def _units_per_mm() -> float:
    """Scene units per millimeter — the project setting ini.sch_scale
    ([gui] sch_scale in the project SLiCAP.ini, default 2). Read
    dynamically so switching projects picks up each project's scale
    (Anton, 2026-07-15: book projects with narrow LaTeX figure widths
    use 4-5)."""
    import SLiCAP.SLiCAPconfigure as ini
    return float(getattr(ini, "sch_scale", 2.0))
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
    # Without a border the frame is the drawing, EXACTLY: a poster of
    # bordered schematics then has their size and sits on the book's
    # margins (Anton, 2026-10-09). The guard against clipped text stays
    # where the uncertainty is: an item drawn from Qt text metrics (a
    # label, a free text, a command or library block) gets 1.5 mm around
    # its own rectangle, since a renderer whose font is a fraction wider,
    # or the overhang of the last glyph, was clipped at the edge ('inc
    # BC847.lib' lost part of its b - Anton, 2026-09-21). A margin around
    # the whole frame was the previous form and was REPLACED: it widened
    # every export, also one whose edge is an image or a shape.
    from .image_item import ImageItem
    from .shape_item import ShapeItem
    from .wire_item import WireItem
    from .junction_item import JunctionItem
    from .latex_fragment_item import LatexFragmentItem
    from .component_item import _ViewBoxSvgItem
    exact = (ImageItem, ShapeItem, WireItem, JunctionItem, LatexFragmentItem,
             _ViewBoxSvgItem)
    m = 1.5 * _units_per_mm()
    b = QRectF()
    for item in scene.items():
        r = item.sceneBoundingRect()
        if not isinstance(item, exact):
            r = r.adjusted(-m, -m, m, m)
        b = b.united(r)
    if b.isEmpty():
        b = QRectF(0, 0, 200, 200)
    return b


def _centred_baseline_y(y: float, size_px: float, style) -> float:
    """The SVG baseline of a symbol text whose line box is CENTRED on the
    anchor y, as the canvas draws it (component_item.draw_symbol_texts,
    Qt.AlignCenter): the metrics of the canvas font at that pixel size.
    dominant-baseline="central" was used and REPLACED: svglib, the PDF
    path, does not know the attribute and put the BASELINE on the anchor,
    so the +/- of a source sat higher in the PDF than in the SVG and on
    the canvas (Anton, 2026-10-10). An explicit baseline reads the same
    in a browser, in Qt and in svglib."""
    from PySide6.QtGui import QFont, QFontMetricsF
    f = QFont(style.SYMBOL_TEXT_FONT)
    f.setPixelSize(max(1, round(size_px)))
    fm = QFontMetricsF(f)
    return y + (fm.ascent() - fm.descent()) / 2


def _touches(r: QRectF, frame: QRectF) -> bool:
    """r overlaps or borders *frame* (QRectF.intersects is False for a rect
    of zero area, which a straight line may have)."""
    return (r.right() >= frame.left() and r.left() <= frame.right() and
            r.bottom() >= frame.top() and r.top() <= frame.bottom())


def _qhex(c) -> str:
    return f"#{c.red():02x}{c.green():02x}{c.blue():02x}"


def _build_svg(scene, title: str = "", source: str = "") -> bytes:
    """Render all scene items to a vector SVG document, returning UTF-8 bytes.
    *source* is the schematic file name, written as a provenance comment
    (see :mod:`SLiCAP.schematic.provenance`)."""
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
    from .model_item import ModelItem
    from .library_item import LibraryItem
    from .config import default_style

    # The scene carries the schematic's own style; a bare scene (tests,
    # headless callers that did not set one) falls back to the defaults.
    # NOTE: QGraphicsScene has a BUILT-IN .style() method, so the presence
    # test must be for the SLiCAP style object, not mere truthiness.
    style = getattr(scene, "style", None)
    if not hasattr(style, "WIRE_COLOR"):
        style = default_style()

    bounds = export_bounds(scene)
    vx, vy = bounds.x(), bounds.y()
    vw, vh = bounds.width(), bounds.height()

    root = ET.Element(f"{{{_SVG_NS}}}svg")
    root.set("version", "1.1")
    root.set("viewBox", f"{vx:.3f} {vy:.3f} {vw:.3f} {vh:.3f}")
    # Physical size from the project's units-per-mm (ini.sch_scale): a
    # border designed in mm exports/prints/includes at that size instead
    # of the implicit 96-px-per-inch interpretation of unitless pixels.
    upm = _units_per_mm()
    root.set("width",  f"{vw / upm:.3f}mm")
    root.set("height", f"{vh / upm:.3f}mm")
    if source:
        from .provenance import svg_marker
        root.append(ET.Comment(svg_marker(source)))
    if title:
        ET.SubElement(root, f"{{{_SVG_NS}}}title").text = title

    # Collects glyph <defs> extracted from inlined LaTeX SVGs.
    defs = ET.SubElement(root, f"{{{_SVG_NS}}}defs")

    bg = ET.SubElement(root, f"{{{_SVG_NS}}}rect")
    bg.set("x", f"{vx:.3f}"); bg.set("y", f"{vy:.3f}")
    bg.set("width", f"{vw:.3f}"); bg.set("height", f"{vh:.3f}")
    bg.set("fill", "white")

    # A border CLIPS (Anton, 2026-10-09): the export holds what lies
    # inside it. An item wholly outside is left out, one that crosses the
    # border is cut by a clip path on the group that holds the drawing.
    # The viewBox alone hid such items but kept them in the file, where an
    # editor showed them beyond the page. Without a border nothing clips.
    from .border_item import BorderItem
    border = next((i for i in scene.items() if isinstance(i, BorderItem)), None)
    frame = None
    out = root
    if border is not None:
        frame = QRectF(border.pos().x(), border.pos().y(),
                       border.rect().width(), border.rect().height())
        cp = ET.SubElement(defs, f"{{{_SVG_NS}}}clipPath")
        cp.set("id", "frame")
        cr = ET.SubElement(cp, f"{{{_SVG_NS}}}rect")
        cr.set("x", f"{frame.x():.3f}"); cr.set("y", f"{frame.y():.3f}")
        cr.set("width", f"{frame.width():.3f}"); cr.set("height", f"{frame.height():.3f}")
        out = ET.SubElement(root, f"{{{_SVG_NS}}}g")
        out.set("clip-path", "url(#frame)")

    wire_color = _qhex(style.WIRE_COLOR)
    junc_color = _qhex(style.JUNCTION_COLOR)
    lbl_color  = _qhex(style.COMP_LABEL_COLOR)
    net_color  = _qhex(style.NET_LABEL_COLOR)
    cmd_color  = _qhex(style.COMMAND_COLOR)
    lnk_color  = _qhex(style.HYPERLINK_COLOR)

    for item in reversed(scene.items()):
        if item.parentItem() is not None:
            continue   # child items (labels, net labels) handled by their parents
        if frame is not None and not _touches(item.sceneBoundingRect(), frame):
            continue   # wholly outside the border: not exported

        if isinstance(item, BorderItem):
            _border_rect(out, item)    # bg (alpha>0) + line (show_in_export)
            continue
        if isinstance(item, WireItem):
            _wire(out, item, wire_color, style.WIRE_WIDTH, net_color,
                  style.NET_LABEL_FONT_SIZE)
        elif isinstance(item, JunctionItem):
            _junction(out, item, junc_color, style.JUNCTION_RADIUS)
        elif isinstance(item, ComponentItem):
            _component(out, defs, item, lbl_color, style.COMP_LABEL_FONT_SIZE, style)
        elif isinstance(item, ImageItem):
            _image_svg(out, defs, item)
        elif isinstance(item, (LatexFragmentItem, ParameterItem, ModelItem)):
            if not item.isVisible():
                continue        # "Show on schematic" off: netlisted, not drawn
            if item._svg_bytes:
                pos = item.pos()
                svg_bytes = (item.export_bytes() if isinstance(item, LatexFragmentItem)
                             else item._svg_bytes)
                _inline_image_svg(out, defs, svg_bytes,
                                  pos.x(), pos.y(),
                                  item.display_width, item.display_height,
                                  aspect_fit=True)
        elif isinstance(item, (FreeTextItem, CommandItem, AnalysisItem, LibraryItem)):
            if (isinstance(item, (AnalysisItem, LibraryItem))
                    and not item.isVisible()):
                continue        # "Show on schematic" off: netlisted, not drawn
            if isinstance(item, (AnalysisItem, LibraryItem)) and item._svg_bytes:
                pos = item.pos()          # LaTeX-rendered block → embed the vector SVG
                _inline_image_svg(out, defs, item._svg_bytes,
                                  pos.x(), pos.y(),
                                  item._svg_rect.width(), item._svg_rect.height(),
                                  aspect_fit=True)
                continue
            if isinstance(item, FreeTextItem):
                # the item's own font and colour, or the style's (the scene's
                # style holds the document colours)
                font = item.effective_font(style)
                _text_block(out, item, _qhex(item.effective_color(style)),
                            font.pointSize(), font.family(), font)
            else:
                _text_block(
                    root, item, cmd_color, style.COMMAND_FONT_SIZE,
                    "monospace", style.COMMAND_FONT,
                )
        elif type(item).__name__ in ("SymbolPinItem", "SymbolTextItem", "OpaqueSvgItem"):
            _symbol_item(out, item, style)
        elif isinstance(item, HyperlinkItem):
            _hyperlink_block(out, item, lnk_color,
                             style.HYPERLINK_FONT_SIZE, style.HYPERLINK_FONT_FAMILY,
                             style.HYPERLINK_UNDERLINE)
        elif isinstance(item, ShapeItem):
            _shape(out, item)

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

    if (item.display_name
            and item._net_label is not None and item._net_label.isVisible()):
        from PySide6.QtGui import QFontMetricsF
        lpos = item._net_label.pos()
        # QGraphicsSimpleTextItem.pos() is the top-left of the bounding rect.
        # SVG <text y> anchors the baseline; add the font ascent to align correctly.
        fm = QFontMetricsF(item._net_label.font())
        t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        t.set("x", f"{lpos.x():.2f}")
        t.set("y", f"{lpos.y() + fm.ascent():.2f}")
        t.set("font-family", svg_family("sans-serif"))
        t.set("font-size", f"{net_fs}pt")
        t.set("fill", net_color)
        t.text = item._net_label.text()   # effective name (may be derived)

    # DC operating-point annotation: exported as displayed — the current
    # value when available, otherwise the "V: —" placeholder.
    if (item.show_dc_voltage
            and item._dc_label is not None and item._dc_label.isVisible()):
        from PySide6.QtGui import QFontMetricsF
        from .config import default_style
        scene = item.scene()
        style = getattr(scene, "style", None)
        if not hasattr(style, "BIAS_COLOR"):
            style = default_style()
        lbl  = item._dc_label
        fm   = QFontMetricsF(lbl.font())
        t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        t.set("x", f"{lbl.pos().x():.2f}")
        t.set("y", f"{lbl.pos().y() + fm.ascent():.2f}")
        t.set("font-family", svg_family(style.BIAS_FONT_FAMILY))
        t.set("font-size", f"{style.BIAS_FONT_SIZE}pt")
        t.set("fill", _qhex(lbl.brush().color()))
        if lbl.font().italic():
            t.set("font-style", "italic")
        t.text = lbl.text()


def _junction(parent, item, fill, radius):
    el = ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
    el.set("cx", f"{item.pos().x():.2f}")
    el.set("cy", f"{item.pos().y():.2f}")
    el.set("r",  f"{radius:.2f}")
    el.set("fill", fill)


def _border_rect(parent, item):
    """Border background (bottom layer, when bg_alpha > 0) and border line
    (when show_in_export). Called first in the item loop (Z_BORDER is the
    lowest z), so the background rect lands under everything."""
    pos = item.pos()
    r   = item.rect()
    if getattr(item, "bg_alpha", 0) > 0:
        bg = ET.SubElement(parent, f"{{{_SVG_NS}}}rect")
        bg.set("x",      f"{pos.x():.2f}")
        bg.set("y",      f"{pos.y():.2f}")
        bg.set("width",  f"{r.width():.2f}")
        bg.set("height", f"{r.height():.2f}")
        bg.set("fill",   getattr(item, "bg_color", "#ffffff"))
        bg.set("fill-opacity", f"{item.bg_alpha / 100:.2f}")
        bg.set("stroke", "none")
    if item.show_in_export:
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}rect")
        el.set("x",              f"{pos.x():.2f}")
        el.set("y",              f"{pos.y():.2f}")
        el.set("width",          f"{r.width():.2f}")
        el.set("height",         f"{r.height():.2f}")
        el.set("fill",           "none")
        el.set("stroke",         getattr(item, "line_color", "#5050b4"))
        el.set("stroke-width",   f'{getattr(item, "line_width", 0.8):g}')
        da = _DASH_ARRAY.get(getattr(item, "line_style", "dashed"), "8,4")
        if da:
            el.set("stroke-dasharray", da)


def _image_svg(parent, defs, item) -> None:
    """Dispatch to vector-inline (SVG source) or base64 PNG (everything else)."""
    from pathlib import Path as _Path
    file = _Path(item.path)                 # the link, resolved from the project root
    from . import project
    from .provenance import own_exports
    cur = project.current()
    if cur is not None and file.resolve() in own_exports(cur):
        return                              # the schematic's own export: never nested
    if getattr(item, "link_kind", "") in ("schematic", "poster"):
        # a drawing shown on a poster: in a browser a click opens the
        # drawing's own export, next to the poster's in img/ (relative link)
        a = ET.SubElement(parent, f"{{{_SVG_NS}}}a")
        a.set("href", item.link_stem + ".svg")
        a.set(f"{{{_XLINK_NS}}}href", item.link_stem + ".svg")
        parent = a
    ext = file.suffix.lower()
    pos = item.pos()
    x, y = pos.x(), pos.y()
    w, h = item.display_width, item.display_height

    if ext == ".svg":
        try:
            svg_bytes = file.read_bytes()
        except OSError:
            return
        _inline_image_svg(parent, defs, svg_bytes, x, y, w, h)
        return

    # Raster path: a PNG or JPEG file is embedded as it is, anything else
    # (a PDF page) as the item's bitmap; both at the picture's own
    # resolution, placed in the rect the picture fills on the canvas.
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext)
    if mime and file.is_file():
        raw = file.read_bytes()
    else:
        px = item._pixmap
        if px is None or px.isNull():
            return
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        px.save(buf, "PNG")
        raw, mime = bytes(buf.data()), "image/png"
        buf.close()
    data = base64.b64encode(raw).decode("ascii")
    r = item.picture_rect()
    el = ET.SubElement(parent, f"{{{_SVG_NS}}}image")
    el.set("x",      f"{x + r.x():.2f}")
    el.set("y",      f"{y + r.y():.2f}")
    el.set("width",  f"{r.width():.2f}")
    el.set("height", f"{r.height():.2f}")
    el.set("href",   f"data:{mime};base64,{data}")


def _inline_image_svg(parent, defs, svg_bytes: bytes,
                      x: float, y: float, w: float, h: float,
                      aspect_fit: bool = False) -> None:
    """
    Inline an SVG file as scaled vector content at scene position (x, y).

    Top-left corner is anchored at (x, y); content is scaled to fit w × h
    scene units.  IDs are prefixed to avoid collisions with other inlined SVGs.
    Any <defs> inside the embedded SVG are hoisted to the output document's
    top-level <defs>.

    When *aspect_fit* is True, content is scaled uniformly to the largest size
    that fits within (w, h) and centred — matching the canvas _aspect_fit
    behaviour used for LatexFragmentItem, ParameterItem, and ModelItem.
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

    if aspect_fit:
        scale  = min(w / vb_w, h / vb_h)
        fit_w  = vb_w * scale
        fit_h  = vb_h * scale
        x_off  = x + (w - fit_w) / 2
        y_off  = y + (h - fit_h) / 2
        transform = f"translate({x_off:.3f},{y_off:.3f}) scale({scale:.6f},{scale:.6f})"
    else:
        sx = w / vb_w
        sy = h / vb_h
        transform = f"translate({x:.3f},{y:.3f}) scale({sx:.6f},{sy:.6f})"
    if vb_x or vb_y:
        transform += f" translate({-vb_x:.3f},{-vb_y:.3f})"

    g = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
    g.set("transform", transform)
    # A dvisvgm render has no colour attributes: its paths inherit from the
    # root <svg>, which is where recolor_svg puts a tint. The root is dropped
    # here, so the wrapper group takes its fill and stroke over, or the tint
    # of a LaTeX fragment would be lost in the export (2026-10-06).
    for attr in ("fill", "stroke"):
        if sym.get(attr):
            g.set(attr, sym.get(attr))
    for child in content:
        g.append(child)


def _component(parent, defs, item, lbl_color, lbl_fs, style=None):
    """*style* is the DOCUMENT style of the scene (never the display style:
    an export from a dark canvas keeps the document colours)."""
    from .config import default_style
    style = style or default_style()
    px, py = item.pos().x(), item.pos().y()
    rot    = item.rotation()
    sx     = -1 if item.h_flip else 1
    sy     = -1 if item.v_flip else 1

    # Order matters when rotation AND flip are combined (mirrored ports,
    # Anton live finding 2026-07-11): the canvas applies rotate FIRST, then
    # flip (Qt: setTransform(scale) composes on top of setRotation). SVG
    # transform lists apply right-to-left to the point, so the flip must be
    # emitted BEFORE the rotation to match: translate · scale · rotate.
    parts = [f"translate({px:.2f},{py:.2f})"]
    if sx != 1 or sy != 1:
        parts.append(f"scale({sx},{sy})")
    if rot:
        parts.append(f"rotate({rot:.3f})")

    try:
        sym = ET.fromstring(item._svg_bytes.decode("utf-8", errors="replace"))
    except ET.ParseError:
        return

    g = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
    g.set("transform", " ".join(parts))
    g.set("font-size", f"{lbl_fs}pt")  # baseline for text within symbol (e.g. +/-)
    for child in sym:
        g.append(child)

    # Embedded symbol text and baked LaTeX labels were stripped from the
    # artwork (item._svg_bytes); emit each at its transformed position under the
    # readable-orientation rule of the canvas (component_item.readable_transform):
    # unmirrored, upright for a symbol at 0/180 degrees, reading bottom-to-top
    # for one at +/-90 degrees.
    vertical = round(rot) % 180 == 90
    symbol_text_color = style.SYMBOL_TEXT_COLOR
    for t in getattr(item, "symbol_texts", ()):
        content = t.get("content")
        if not content:
            continue
        sp = item.mapToScene(QPointF(t["x"], t["y"]))
        te = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        te.set("x", f"{sp.x():.2f}")
        # centred horizontally (text-anchor) and vertically (the baseline
        # below the anchor by the font's half line box) on the anchor point
        te.set("y", f"{_centred_baseline_y(sp.y(), t['size'], style):.2f}")
        te.set("font-family", svg_family(style.SYMBOL_TEXT_FONT_FAMILY))
        te.set("font-size", f"{t['size']:.1f}")
        te.set("text-anchor", "middle")
        te.set("fill", _qhex(symbol_text_color))
        if vertical:
            # about the anchor, where the glyph centre is: the text turns
            # in place, as readable_transform does on the canvas
            te.set("transform", f"rotate(-90 {sp.x():.2f} {sp.y():.2f})")
        te.text = content
    stroke_hex = _qhex(style.SYMBOL_STROKE_COLOR)
    for f in getattr(item, "symbol_latex", ()):
        try:
            frag = ET.fromstring(f["svg"].decode("utf-8", errors="replace"))
        except ET.ParseError:
            continue
        cx, cy = f["x"] + f["w"] / 2.0, f["y"] + f["h"] / 2.0
        sp = item.mapToScene(QPointF(cx, cy))
        tr = f"translate({sp.x():.3f},{sp.y():.3f})"
        if vertical:
            tr += " rotate(-90)"
        tr += f" translate({-cx:.3f},{-cy:.3f})"
        wrap = ET.SubElement(parent, f"{{{_SVG_NS}}}g")
        wrap.set("transform", tr)
        for child in list(frag):
            if child.get("fill") == "black":
                child.set("fill", stroke_hex)
            wrap.append(child)

    for lbl in item._labels.values():
        sp = lbl.mapToScene(QPointF(0.0, 0.0))
        font, color = lbl._font_and_color(style)
        clr = _qhex(color)
        fs  = font.pointSizeF()
        if lbl._text:
            t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
            t.set("x", f"{sp.x():.2f}")
            t.set("y", f"{sp.y():.2f}")
            t.set("font-family", svg_family(font.family()))
            t.set("font-size", f"{fs:.1f}pt")
            t.set("fill", clr)
            # For h_flipped components the label's local origin is baseline-right;
            # use text-anchor="end" so SVG anchors the text on the same side.
            if item.h_flip:
                t.set("text-anchor", "end")
            t.text = lbl._text
        elif lbl._svg_renderer is not None:
            _latex_label(parent, defs, item, lbl, sp, clr, fs)


def _latex_label(parent, defs, item, lbl, sp, lbl_color, lbl_fs):
    """Inline a LaTeX property label as scaled vector SVG content."""
    svg_bytes = lbl._svg_bytes or None

    if svg_bytes is None:
        text = item._prop_text(lbl.prop_key)
        if text:
            t = ET.SubElement(parent, f"{{{_SVG_NS}}}text")
            t.set("x", f"{sp.x():.2f}")
            t.set("y", f"{sp.y():.2f}")
            t.set("font-family", svg_family("sans-serif"))
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
        t.set("font-family", svg_family("sans-serif"))
        t.set("font-size", f"{lbl_fs}pt")
        t.set("fill", lbl_color)
        t.text = lbl._prefix

    # The label's bytes are the render in document black; the document
    # colour of its kind (refdes, parameter) is applied here, the export's
    # own decision, as the canvas applies the display colour in set_svg.
    from .latex_label import recolor_svg
    _inline_latex_svg(parent, defs, recolor_svg(svg_bytes, lbl_color), svg_x, sp.y(), svg_w, svg_h)


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
    # The root of the render is dropped; its presentation attributes (the
    # fill that recolor_svg sets, which the paths inherit) move to the group.
    for attr in ("fill", "stroke"):
        if sym.get(attr):
            g.set(attr, sym.get(attr))
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
        t.set("font-family", svg_family(family))
        t.set("font-size", f"{fs}pt")
        if font is not None and font.bold():
            t.set("font-weight", "bold")
        if font is not None and font.italic():
            t.set("font-style", "italic")
        t.set("fill", color)
        t.text = line


_DASH_ARRAY = {
    "solid":    None,
    "dashed":   "8,4",
    "dotted":   "2,4",
    "dash-dot": "8,4,2,4",
}


def _shape(parent, item) -> None:
    """Render a ShapeItem to SVG: line (polyline with filled heads), rect,
    ellipse, polygon; stroke style "none" gives a fill without contour;
    the rotation goes out as an SVG rotate about the shape's centre."""
    from .shape_item import shaft_points, head_base, KINDS_SAMPLED
    from PySide6.QtCore import QPointF
    ox, oy = item.pos().x(), item.pos().y()
    # arc, curve and func are exported as the polyline they are drawn with
    source = item.stroke_points() if item.kind in KINDS_SAMPLED else item.rel_points
    pts    = [(ox + p.x(), oy + p.y()) for p in source]
    lw     = item.line_width
    fill   = item.fill_color if item.is_filled() else "none"

    if item.line_style == "none":
        stroke_attrs = {"stroke": "none", "fill": fill}
    else:
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
    if item.rotation:
        c = item.centre()
        stroke_attrs["transform"] = f"rotate({item.rotation:.2f} {ox + c.x():.2f} {oy + c.y():.2f})"

    def _pts(seq):
        return " ".join(f"{x:.2f},{y:.2f}" for x, y in seq)

    if item.kind == "curve" and item.closed and len(pts) >= 3:
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polygon")
        el.set("points", _pts(pts))
        for k, v in stroke_attrs.items():
            el.set(k, v)

    elif item.kind in ("line",) + KINDS_SAMPLED and len(pts) >= 2:
        qpts = [QPointF(x, y) for x, y in pts]
        shaft = shaft_points(qpts, item.line_end_start, item.line_end_end, item.head_length)
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polyline")
        el.set("points", _pts((p.x(), p.y()) for p in shaft))
        for k, v in stroke_attrs.items():
            el.set(k, v)
        el.set("fill", "none")
        _svg_line_end(parent, head_base(qpts, item.head_length, False), qpts[0],
                      item.line_end_start, item)
        _svg_line_end(parent, head_base(qpts, item.head_length, True), qpts[-1],
                      item.line_end_end, item)

    elif item.kind == "rect" and len(pts) == 2:
        x0 = min(pts[0][0], pts[1][0]); y0 = min(pts[0][1], pts[1][1])
        w  = abs(pts[1][0] - pts[0][0]); h  = abs(pts[1][1] - pts[0][1])
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}rect")
        el.set("x", f"{x0:.2f}"); el.set("y", f"{y0:.2f}")
        el.set("width", f"{w:.2f}"); el.set("height", f"{h:.2f}")
        for k, v in stroke_attrs.items():
            el.set(k, v)

    elif item.kind == "ellipse" and len(pts) == 2:
        cx = (pts[0][0] + pts[1][0]) / 2; cy = (pts[0][1] + pts[1][1]) / 2
        rx = abs(pts[1][0] - pts[0][0]) / 2; ry = abs(pts[1][1] - pts[0][1]) / 2
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}ellipse")
        el.set("cx", f"{cx:.2f}"); el.set("cy", f"{cy:.2f}")
        el.set("rx", f"{rx:.2f}"); el.set("ry", f"{ry:.2f}")
        for k, v in stroke_attrs.items():
            el.set(k, v)

    elif item.kind == "polygon" and len(pts) >= 3:
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polygon")
        el.set("points", _pts(pts))
        for k, v in stroke_attrs.items():
            el.set(k, v)


def _svg_line_end(parent, p_from, p_to, style: str, item) -> None:
    """Filled line-end head without contour, as in the canvas: arrow and
    diamond as a polygon of the item's head width and length, dot as a
    circle of the head width."""
    from .shape_item import head_polygon
    if style == "none":
        return
    color = item.stroke_color
    if style == "dot":
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
        el.set("cx", f"{p_to.x():.2f}"); el.set("cy", f"{p_to.y():.2f}")
        el.set("r",  f"{item.head_width / 2:.2f}")
    else:
        poly = head_polygon(p_from, p_to, style, item.head_width, item.head_length)
        if not poly:
            return
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}polygon")
        el.set("points", " ".join(f"{p.x():.2f},{p.y():.2f}" for p in poly))
    el.set("fill", color); el.set("stroke", "none")


def _symbol_item(parent, item, style) -> None:
    """Symbol editor items in an SVG export of the symbol canvas: a pin as
    a small marker, symbol text as text, an opaque element verbatim."""
    from .symbol_editor import SymbolPinItem, SymbolTextItem
    import xml.etree.ElementTree as _ET
    x, y = item.pos().x(), item.pos().y()
    if isinstance(item, SymbolPinItem):
        el = _ET.SubElement(parent, f"{{{_SVG_NS}}}circle")
        el.set("cx", f"{x:.2f}"); el.set("cy", f"{y:.2f}"); el.set("r", "2")
        el.set("fill", _qhex(style.NET_LABEL_COLOR)); el.set("stroke", "none")
    elif isinstance(item, SymbolTextItem):
        el = _ET.SubElement(parent, f"{{{_SVG_NS}}}text")
        el.set("x", f"{x:.2f}")
        el.set("y", f"{_centred_baseline_y(y, item.size, style):.2f}")   # see _centred_baseline_y
        el.set("font-size", f"{item.size:g}"); el.set("text-anchor", "middle")
        el.set("fill", _qhex(style.SYMBOL_TEXT_COLOR))
        el.text = item.content
    else:
        try:
            el = _ET.fromstring(item.xml)
        except _ET.ParseError:
            return
        wrap = _ET.SubElement(parent, f"{{{_SVG_NS}}}g")
        wrap.set("transform", f"translate({x:.2f} {y:.2f})")
        wrap.append(el)


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
    t.set("font-family", svg_family(family))
    t.set("font-size", f"{fs}pt")
    t.set("fill", color)
    if underline:
        t.set("text-decoration", "underline")
    t.text = label


def export_svg(scene, output_path: Path, title: str = "",
               source: str = "") -> None:
    output_path.write_bytes(_build_svg(scene, title, source))


def export_pdf(scene, output_path: Path, source: str = "",
               title: str = "") -> None:
    """Render the schematic SVG to PDF with svglib + reportlab — the same
    pure-Python path used in SLiCAPkicad. No Cairo (dropped for its Windows
    trouble), and no Qt application required, so it works from the headless
    ``cli export`` subprocess or any non-GUI caller. The PDF inherits the SVG's
    physical (mm) page size set in ``_build_svg``. The creator and subject
    fields name the export and *source* (provenance, 2026-09-13)."""
    import os
    import tempfile
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    from reportlab.pdfgen import canvas as rl_canvas
    from .provenance import CREATOR
    register_pdf_fonts()      # the shipped families, embedded (see fonts.py)
    with tempfile.NamedTemporaryFile("wb", suffix=".svg", delete=False) as tf:
        tf.write(_build_svg(scene))
        tmp = tf.name
    try:
        drawing = svg2rlg(tmp)
        if drawing is None:
            raise RuntimeError("Could not parse the schematic SVG for PDF export.")
        drawing = renderPDF.renderScaledDrawing(drawing)
        c = rl_canvas.Canvas(str(output_path),
                             pagesize=(drawing.width, drawing.height))
        c.setCreator(CREATOR)
        c.setSubject(source)
        c.setTitle(title or source)
        renderPDF.draw(drawing, c, 0, 0)
        c.showPage()
        c.save()
    finally:
        os.unlink(tmp)


def print_scene(scene, parent=None) -> None:
    from PySide6.QtPrintSupport import QPrinter, QPrintDialog
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPainter
    from PySide6.QtCore import QByteArray
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
    nat_w     = svg_w / _units_per_mm() * dpmm
    nat_h     = svg_h / _units_per_mm() * dpmm

    fit_pct = 0.0
    if nat_w > 0 and nat_h > 0:
        fit_pct = min(page_rect.width() / nat_w,
                      page_rect.height() / nat_h) * 100.0

    from PySide6.QtCore import Qt
    scale_dlg = QDialog(parent, Qt.Window)
    scale_dlg.setWindowTitle("Print Scale")
    vlay = QVBoxLayout(scale_dlg)

    # Default is TRUE SIZE (100 %, per ini.sch_scale) — fit-to-page is the
    # opt-in (Anton, 2026-07-15).
    fit_cb = QCheckBox("Fit to page")
    fit_cb.setChecked(False)
    vlay.addWidget(fit_cb)

    hlay = QHBoxLayout()
    hlay.addWidget(QLabel("Scale:"))
    scale_sb = QDoubleSpinBox()
    scale_sb.setRange(10.0, 500.0)
    scale_sb.setSingleStep(5.0)
    scale_sb.setDecimals(1)
    scale_sb.setSuffix(" %")
    scale_sb.setValue(100.0)
    scale_sb.setEnabled(True)
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

    # ── step 4: render the SVG VECTOR onto the printer ────────────────────────
    # QSvgRenderer paints vectors straight onto the printer (no cairosvg, no
    # temp PDF, no rasterisation) — crisp at any scale, same renderer as canvas.
    renderer = QSvgRenderer(QByteArray(_build_svg(scene)))
    painter  = QPainter(printer)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, render_rect)
    painter.end()
