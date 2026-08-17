import re

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem, QStyle
from PySide6.QtCore import QByteArray, Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QFont, QFontMetricsF, QTransform, QPainterPath

from . import config
from .config import snap, style_of, default_style


def _pt_key(pt: "QPointF") -> tuple[int, int]:
    """Round a scene point to the nearest integer grid key."""
    return (round(pt.x()), round(pt.y()))


def _sign(v: float) -> float:
    return 0.0 if v == 0 else (1.0 if v > 0 else -1.0)


# Pin-name labels (subcircuit blocks): the generated box has stubs of this length
# (see subcircuit._STUB), so the outline edge at a pin is the pin minus one stub.
# Names sit this far inside that edge.
_SUBCKT_STUB     = 10.0
_PIN_LABEL_MARGIN = 4.0


def _pin_name_font(style) -> QFont:
    """Smaller than the property-label font so four names fit in a compact box."""
    font = QFont(style.COMP_PARAM_FONT)
    font.setPointSize(5)
    return font


def draw_subckt_pin_names(painter, nodes, pins, rotation=0.0,
                          h_flip=False, v_flip=False, style=None) -> None:
    """Draw subcircuit pin names just inside the outline, one per pin.

    Each name is counter-transformed so it stays horizontal and unmirrored under
    any rotation/flip, and anchored to grow inward from its box edge so it never
    pokes out.  Shared by ComponentItem.paint and the Place Subcircuit preview.
    """
    style = style or default_style()
    ct = _counter_transform(rotation, h_flip, v_flip)
    font = _pin_name_font(style)
    fm = QFontMetricsF(font)
    painter.save()
    painter.setPen(style.SYMBOL_TEXT_COLOR)
    painter.setFont(font)
    for (px, py), name in zip(pins, nodes):
        if abs(px) >= abs(py):                       # left / right pin
            edge = px - _sign(px) * _SUBCKT_STUB
            ax = edge - _sign(px) * (fm.horizontalAdvance(name) / 2 + _PIN_LABEL_MARGIN)
            ay = py
        else:                                        # top / bottom pin
            edge = py - _sign(py) * _SUBCKT_STUB
            ax = px
            ay = edge - _sign(py) * (fm.height() / 2 + _PIN_LABEL_MARGIN)
        painter.save()
        painter.translate(ax, ay)
        painter.setTransform(ct, True)
        painter.drawText(QRectF(-100, -20, 200, 40), Qt.AlignCenter, name)
        painter.restore()
    painter.restore()


def _counter_transform(rotation: float, h_flip: bool, v_flip: bool) -> "QTransform":
    """
    Return the label counter-transform that exactly cancels the parent component's
    combined rotate × flip transform, keeping label text upright and unmirrored.

    The parent's effective linear transform is scale(sx,sy) × rotate(rot).
    Its inverse is rotate(-rot) × scale(sx,sy)  [since scale is self-inverse here].
    In Qt's QTransform, .rotate().scale() post-multiplies left-to-right, giving
    exactly rotate(-rot) × scale(sx,sy) as required.
    """
    sx = -1 if h_flip else 1
    sy = -1 if v_flip else 1
    return QTransform().rotate(-rotation).scale(sx, sy)


_TEXT_RE = re.compile(rb'<text\b([^>]*)>(.*?)</text>', re.S)


def _split_symbol_text(svg_bytes: bytes) -> tuple[bytes, list[dict]]:
    """Split a symbol's SVG into (artwork_without_text, embedded_texts).

    Embedded <text> labels (e.g. +/- polarity markers, noise-source labels) are
    removed from the artwork so they can be redrawn upright and unmirrored on top,
    regardless of the component's rotation/flip.  Each text is
    {x, y, size, content} in symbol-local coordinates."""
    texts: list[dict] = []

    def _num(s, default):
        try:
            return float(s)
        except (TypeError, ValueError):
            return default

    def _attr(attrs: str, name: str, default: float) -> float:
        m = re.search(rf'{name}\s*=\s*"([^"]*)"', attrs)
        return _num(m.group(1), default) if m else default

    def _repl(m):
        attrs   = m.group(1).decode("utf-8", "replace")
        content = m.group(2).decode("utf-8", "replace").strip()
        if content:
            texts.append({
                "x":    _attr(attrs, "x", 0.0),
                "y":    _attr(attrs, "y", 0.0),
                "size": _attr(attrs, "font-size", 8.0),
                "content": content,
            })
        return b""

    return _TEXT_RE.sub(_repl, svg_bytes), texts


def draw_symbol_texts(painter, texts, rotation: float,
                      h_flip: bool, v_flip: bool, style=None) -> None:
    """Draw a symbol's embedded text labels upright and unmirrored under any
    rotation/flip (companion to draw_subckt_pin_names; used by ComponentItem and
    the SVG/PDF exporter via the same text list)."""
    if not texts:
        return
    style = style or default_style()
    ct = _counter_transform(rotation, h_flip, v_flip)
    painter.save()
    painter.setPen(style.SYMBOL_TEXT_COLOR)
    for t in texts:
        content = t["content"]
        if not content:
            continue
        f = QFont(style.COMP_PARAM_FONT)
        f.setPixelSize(max(1, round(t["size"])))
        painter.setFont(f)
        painter.save()
        painter.translate(t["x"], t["y"])
        painter.setTransform(ct, True)
        # Centred horizontally AND vertically on the anchor point, so the counter
        # transform pivots on the glyph centre — the text stays put (just upright)
        # under any rotation/mirror.  The previews render through the same path
        # (paint_symbol) so the canvas and previews match exactly.
        painter.drawText(QRectF(-100.0, -100.0, 200.0, 200.0),
                         Qt.AlignCenter, content)
        painter.restore()
    painter.restore()


def paint_symbol(painter, svg_bytes: bytes, rect: QRectF, style=None) -> None:
    """Render a symbol (artwork + centred embedded text, default orientation)
    into ``rect`` of ``painter``, preserving aspect ratio.

    Shared by the palette icons and the place-symbol preview so they render the
    embedded text identically to the canvas (ComponentItem.paint)."""
    style = style or default_style()
    stripped, texts = _split_symbol_text(svg_bytes)
    renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(stripped, style)))
    vb = renderer.viewBoxF()
    if vb.width() <= 0 or vb.height() <= 0:
        return
    sc = min(rect.width() / vb.width(), rect.height() / vb.height())
    w, h = vb.width() * sc, vb.height() * sc
    ox = rect.x() + (rect.width() - w) / 2.0
    oy = rect.y() + (rect.height() - h) / 2.0
    renderer.render(painter, QRectF(ox, oy, w, h))
    painter.save()
    painter.translate(ox, oy)
    painter.scale(sc, sc)
    painter.translate(-vb.left(), -vb.top())
    draw_symbol_texts(painter, texts, 0.0, False, False, style=style)
    painter.restore()


# ── symbol metadata ───────────────────────────────────────────────────────────
# A placed component's metadata (pins, model, params, …) is a property of the
# symbol DEFINITION in its schematic's own library: every panel owns a
# SymbolLibrary (with the schematic's frozen .symbols overlay), and each
# ComponentItem holds the Symbol record it was placed from.  There is no
# process-global symbol namespace — two open schematics may define the same
# symbol name differently without affecting each other.

# Fixed params for power symbols (ground, port) — {symbol: {param: default}}.
# These carry no SLiCAP model, so their editable field is supplied here.
# Genuine constants (part of the program, not of any schematic).
_SYMBOL_FIXED_PARAMS: dict[str, dict[str, str]] = {
    "0":    {"name": "0"},
    "port": {"name": ""},
}


def fixed_params_for_symbol(symbol_name: str) -> dict[str, str]:
    """Return a default params dict for power symbols (ground, port)."""
    return dict(_SYMBOL_FIXED_PARAMS.get(symbol_name, {}))


def strip_braces(value: str) -> str:
    """Remove a single pair of surrounding {…} braces, if present.

    Parameter values/expressions are stored and edited *without* braces — the
    braces are a netlist-syntax detail the program adds, never something the
    user types (see wrap_braces)."""
    s = value.strip()
    if s.startswith("{") and s.endswith("}"):
        return s[1:-1].strip()
    return s


def wrap_braces(value: str) -> str:
    """Wrap a parameter value in {…} unless already wrapped; empty stays empty.

    In a SLiCAP netlist every parameter value/expression is enclosed in curly
    braces. The user enters the bare expression; the netlist writer and LaTeX
    renderer add the braces via this helper."""
    s = value.strip()
    # A bare "?" is an unset-value reminder, not an expression — never brace it
    # (and netlist generation rejects it before output anyway).
    if not s or s == "?" or (s.startswith("{") and s.endswith("}")):
        return s
    return "{" + s + "}"

def _vi_stimuli_display(key: str, params: dict) -> "tuple[str, list[tuple[str,str]]]":
    """Return (prefix, pairs) for render_stimuli_label from canonical V/I source params.

    Called from update_labels() when displaying dc/ac/tran for a V or I source."""
    if key == "dc":
        val = params.get("dc", "").strip()
        return "dc:", [("DC", val)] if val else []
    if key == "ac":
        ac    = params.get("ac", "").strip()
        parts = ac.split()
        pairs = [("MAG", parts[0])] if parts else []
        if len(parts) > 1:
            pairs.append(("PHASE", parts[1]))
        return "ac:", pairs
    if key == "tran":
        from .source_stimuli_dialog import _WAVEFORMS
        wf_type = params.get("_tran_type", "PULSE")
        if wf_type == "PWL":
            path  = params.get("_pwl_file", "")
            pairs = [("file", path)] if path else []
            r  = params.get("_pwl_r",  "")
            td = params.get("_pwl_td", "")
            if r:  pairs.append(("r",  r))
            if td: pairs.append(("td", td))
        else:
            wf_dict = {n: f for n, f in _WAVEFORMS}
            fields  = wf_dict.get(wf_type, [])
            pairs   = []
            for f in fields:
                v = params.get(f"_{wf_type.lower()}_{f.lower()}", "").strip()
                if v:
                    pairs.append((f, v))
        return wf_type.lower() + ":", pairs
    return "", []


_DEFAULT_LABEL_X    = 32   # fallback when no tight rect is available
_DEFAULT_LABEL_Y0   = -10
_DEFAULT_LABEL_STEP = 10   # line spacing (scene units) between attribute labels
_LABEL_MARGIN       = 5    # gap between symbol right edge and first label column


def _discard_label(lbl) -> None:
    """Delete a property label for good.

    ``setParentItem(None)`` does NOT remove an item from the scene - it
    re-parents it to the TOP LEVEL, where the scene keeps owning it and it
    keeps painting.  Rebuilding the labels therefore left a GHOST behind: an
    old label lingering at its old position.  It stayed invisible while the
    re-rendered label was identical, and became visible the moment the
    rendering changed - which is why a value with a syntax error showed up
    twice (Anton, 2026-08-16).  The scene must remove it explicitly.
    """
    scene = lbl.scene()
    lbl.setParentItem(None)
    if scene is not None:
        scene.removeItem(lbl)


class _PropertyLabel(QGraphicsItem):
    """
    Movable label for one component property — supports plain text and SVG modes.

    In SVG mode (a rendered LaTeX expression) the SVG is scaled to the style's
    COMP_LABEL_SVG_HEIGHT scene units tall; an optional prefix string is drawn
    as plain text immediately to the left.

    Freely draggable (no snap) as a child of ComponentItem.
    Counter-rotated by the parent so characters always stay upright.
    """

    def __init__(self, prop_key: str, parent: "ComponentItem"):
        super().__init__(parent)
        self.prop_key = prop_key
        self._text: str = ""
        self._svg_renderer: QSvgRenderer | None = None
        self._svg_bytes: bytes = b""        # kept for SVG export
        self._svg_rect: QRectF = QRectF()   # scaled draw rect, centered at (0,0)
        self._prefix: str = ""              # plain text before the SVG
        self._prefix_w: float = 0.0         # cached width of prefix string
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptedMouseButtons(Qt.LeftButton)

    def itemChange(self, change, value):
        p = self.parentItem()
        if p is not None:
            if change in (QGraphicsItem.ItemPositionChange,
                          QGraphicsItem.ItemPositionHasChanged):
                p.update()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        p = self.parentItem()
        if p is not None:
            p._active_label_key = self.prop_key
            p._show_leaders = True     # draw leaders without selecting the parent
            p.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        p = self.parentItem()
        if p is not None:
            p._show_leaders = False
            p.update()
        super().mouseReleaseEvent(event)

    # ── public setters ────────────────────────────────────────────────────────

    def set_text(self, text: str) -> None:
        self._text = text
        self._svg_renderer = None
        self._svg_bytes = b""
        self._svg_rect = QRectF()
        self._prefix = ""
        self._prefix_w = 0.0
        self.prepareGeometryChange()

    def set_svg(self, svg_bytes: bytes, prefix: str = "") -> None:
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if not renderer.isValid():
            self._svg_renderer = None
            self._svg_bytes = b""
            return
        vb = renderer.viewBoxF()
        from .latex_label import svg_line_height
        ref_h = svg_line_height()
        style = style_of(self)
        target_h = (style.COMP_LABEL_SVG_HEIGHT if self.prop_key == "refdes"
                    else style.COMP_PARAM_SVG_HEIGHT)
        if ref_h and ref_h > 0:
            scale = target_h / ref_h * 0.75
        elif vb.height() > 0:
            scale = target_h / vb.height() * 0.75
        else:
            scale = 1.0
        svg_w = vb.width() * scale
        svg_h = vb.height() * scale
        font, _ = self._font_and_color()
        fm = QFontMetricsF(font)
        prefix_w = (fm.horizontalAdvance(prefix) + fm.horizontalAdvance(" ") * 0.25) if prefix else 0.0
        # Bottom-aligned: y=0 is the bottom edge (matches text-mode baseline).
        self._svg_renderer = renderer
        self._svg_bytes = svg_bytes
        self._svg_rect = QRectF(prefix_w, -svg_h, svg_w, svg_h)
        self._prefix = prefix
        self._prefix_w = prefix_w
        self._text = ""
        self.prepareGeometryChange()

    # ── QGraphicsItem interface ───────────────────────────────────────────────

    def _h_flipped(self) -> bool:
        p = self.parentItem()
        return p is not None and getattr(p, 'h_flip', False)

    def _font_and_color(self):
        """Return (font, color) appropriate for this label's property key."""
        style = style_of(self)
        if self.prop_key == "refdes":
            return style.COMP_LABEL_FONT, style.COMP_LABEL_COLOR
        if self.prop_key == "dc_current":
            from PySide6.QtGui import QFont as _QFont
            parent = self.parentItem()
            scene = self.scene()
            value = (scene.dc_current(parent.instance_id)
                     if parent is not None and hasattr(scene, "dc_current")
                     else None)
            dimmed = value is None or getattr(scene, "op_stale", False)
            font = _QFont(style.BIAS_FONT)
            font.setItalic(dimmed)
            return font, (QColor("#909090") if dimmed else style.BIAS_COLOR)
        return style.COMP_PARAM_FONT, style.COMP_PARAM_COLOR

    def boundingRect(self) -> QRectF:
        hf = self._h_flipped()
        if self._svg_renderer is not None:
            total_w = self._prefix_w + self._svg_rect.width()
            r = self._svg_rect
            x0 = -total_w if hf else 0.0
            return QRectF(x0, r.top(), total_w, r.height())
        if not self._text:
            return QRectF()
        font, _ = self._font_and_color()
        fm = QFontMetricsF(font)
        w = fm.horizontalAdvance(self._text)
        x0 = -w if hf else 0.0
        return QRectF(x0, -fm.ascent(), w, fm.ascent() + fm.descent())

    def paint(self, painter: QPainter, option, widget=None):
        hf = self._h_flipped()
        font, color = self._font_and_color()
        painter.setFont(font)
        painter.setPen(QPen(color))
        if self._svg_renderer is not None:
            # LaTeX SVG rendering — font settings don't apply to the SVG itself,
            # only to any plain-text prefix drawn alongside it.
            total_w = self._prefix_w + self._svg_rect.width()
            x0 = -total_w if hf else 0.0
            if self._prefix:
                fm = QFontMetricsF(font)
                svg_center_y = self._svg_rect.top() + self._svg_rect.height() / 2
                baseline_y = svg_center_y + (fm.ascent() - fm.descent()) / 2
                painter.drawText(QPointF(x0, baseline_y), self._prefix)
            svg_x = x0 + self._prefix_w
            r = self._svg_rect
            self._svg_renderer.render(
                painter,
                QRectF(svg_x, r.top(), r.width(), r.height()),
            )
        elif self._text:
            fm = QFontMetricsF(font)
            w = fm.horizontalAdvance(self._text)
            x0 = -w if hf else 0.0
            painter.drawText(QPointF(x0, 0), self._text)


def _apply_symbol_colors(svg_bytes: bytes, style=None) -> bytes:
    """
    Substitute configurable symbol colours into raw SVG bytes.

    Explicit stroke="black" and fill="black" (arrowheads, dots) are replaced
    with the style's SYMBOL_STROKE_COLOR.  <text> elements that have no
    explicit fill get one added so they render in SYMBOL_TEXT_COLOR.
    """
    style = style or default_style()
    stroke = style.SYMBOL_STROKE_COLOR.name()
    text_c = style.SYMBOL_TEXT_COLOR.name()
    svg = svg_bytes.decode("utf-8", errors="replace")
    svg = svg.replace('stroke="black"', f'stroke="{stroke}"')
    svg = svg.replace('fill="black"',   f'fill="{stroke}"')
    # Add fill to <text> elements (they carry no explicit fill in the symbols).
    svg = svg.replace("<text ", f'<text fill="{text_c}" ')
    return svg.encode("utf-8")


class _ViewBoxSvgItem(QGraphicsSvgItem):
    """
    QGraphicsSvgItem whose local origin matches SVG coordinate (0,0).

    boundingRect() returns viewBoxF() so the origin equals the SVG's (0,0).
    paint() calls renderer.render() directly because the C++ vtable does not
    dispatch to the Python override of boundingRect().
    """

    def __init__(self, svg_bytes: bytes, style=None):
        super().__init__()
        self._renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(svg_bytes, style)))
        self.setSharedRenderer(self._renderer)

    def boundingRect(self):
        return self._renderer.viewBoxF()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        self._renderer.render(painter, self._renderer.viewBoxF())


def make_ghost(svg_bytes: bytes, style=None) -> _ViewBoxSvgItem:
    """Semi-transparent drag preview used during placement mode."""
    item = _ViewBoxSvgItem(svg_bytes, style)
    item.setOpacity(0.4)
    item.setAcceptedMouseButtons(Qt.NoButton)
    return item


class ComponentItem(_ViewBoxSvgItem):
    """
    A single placed component on the schematic canvas.

    symbol_name  : key into the symbol library (e.g. "resistor")
    instance_id  : unique label on this schematic (e.g. "R1")

    prop_display maps each property key to (show_value, show_name):
      show_value=False          → no label for this property
      show_value=True, show_name=False  → displays the value only  (e.g. "1k")
      show_value=True, show_name=True   → displays "name: value"   (e.g. "value: 1k")
    """

    def __init__(self, symbol, instance_id: str, svg_bytes: bytes | None = None):
        # ``symbol`` is the Symbol record from the SCHEMATIC'S OWN library —
        # the component keeps it, so its metadata never depends on any other
        # open schematic's symbol definitions.
        if svg_bytes is None:
            svg_bytes = symbol.svg
        stripped, texts = _split_symbol_text(svg_bytes)
        super().__init__(stripped)
        self.symbol       = symbol
        self.symbol_name  = symbol.name
        self.instance_id  = instance_id
        self._svg_bytes   = stripped
        # Embedded symbol text, drawn upright in paint()/export (not in the artwork).
        self.symbol_texts = texts
        self.model: str   = symbol.model
        self.params: dict[str, str] = (dict(symbol.param_defaults)
                                       or fixed_params_for_symbol(symbol.name))
        _is_sub = symbol.prefix == "X"
        self.refs: list[str] = [] if _is_sub else ["?"] * len(symbol.refs)
        # Ground and port are power symbols — show net name, never refdes
        _show_refdes = symbol.name not in ("0", "port")
        self.prop_display: dict[str, tuple[bool, bool]] = {"refdes": (_show_refdes, False)}
        # Parameter default visibility comes from the symbol's data-params.
        for pname in self.params:
            if not pname.startswith("_"):
                self.prop_display[pname] = symbol.param_display.get(pname, (False, False))
        # References are shown by default.
        for i in range(len(symbol.refs)):
            self.prop_display[f"ref {i + 1}"] = (True, False)
        # The model is shown per the symbol's data-model flag (subcircuit blocks
        # and "?" reminders set it, e.g. data-model="?|1").
        if self.model:
            self.prop_display["model"] = (symbol.model_show, False)
        # Ground/port net-name visibility now comes from the symbol's
        # data-params (name|default|show_name|show_value), like every other
        # field — no hardcoded override here.
        self.prop_offsets: dict[str, tuple[float, float]] = {}
        self.h_flip: bool = False
        self.v_flip: bool = False
        self._labels: dict[str, _PropertyLabel] = {}
        # Key of the label the user last clicked, or None.  Drives the dashed
        # leader line: a clicked attribute shows only its own line; selecting the
        # component body (no active label) shows lines to all attributes.
        self._active_label_key: "str | None" = None
        self._show_leaders: bool = False   # True while a child label is being dragged
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(config.Z_COMPONENT)   # above wires so labels stay selectable
        self._prev_pos: "QPointF | None" = None
        # Wires captured at the start of a drag (as [(wire, point_index), …]) so
        # they follow this component's pins. None until the first move of a drag;
        # reset to None by the scene at every mouse press. See _rubber_band_wires.
        self._drag_wires: "list | None" = None
        # Indices of pins with nothing connected to them — drawn as grey markers.
        # Starts with all pins unconnected; the scene refreshes this on every
        # topology change (via _sync_junctions → _refresh_pin_markers).
        self._unconnected_pins: set[int] = set(range(len(symbol.pins)))
        self.update_labels()

    # ── symbol metadata (from this schematic's own library) ────────────────────

    @property
    def prefix(self) -> str:
        """Refdes prefix of this component's symbol (e.g. 'R', 'X')."""
        return self.symbol.prefix

    def pin_positions(self) -> list:
        """Pin coordinates in node order, in symbol-local units."""
        return list(self.symbol.pins)

    def node_names(self) -> list:
        """SLiCAP node names in pin order."""
        return list(self.symbol.nodes)

    def tight_rect(self) -> tuple:
        """The symbol's selection box (x, y, w, h)."""
        return self.symbol.select_box

    def ref_count(self) -> int:
        """Number of element references this symbol requires."""
        return len(self.symbol.refs)

    def available_models(self) -> list:
        """The SLiCAP model(s) for this symbol — at most one (data-model)."""
        return [self.symbol.model] if self.symbol.model else []

    def default_params(self) -> dict:
        """Params dict with the symbol's default values (order preserved)."""
        return dict(self.symbol.param_defaults)

    # ── flip / rotation ───────────────────────────────────────────────────────

    def _flip_transform(self) -> QTransform:
        """Scale transform that represents the current flip state."""
        return QTransform().scale(
            -1.0 if self.h_flip else 1.0,
            -1.0 if self.v_flip else 1.0,
        )

    def apply_transform(self) -> None:
        """Apply h_flip / v_flip to the item and counter-transform all labels."""
        self.setTransform(self._flip_transform())
        ct = _counter_transform(self.rotation(), self.h_flip, self.v_flip)
        for lbl in self._labels.values():
            lbl.setTransform(ct)

    # ── property helpers ──────────────────────────────────────────────────────

    def _label_x(self) -> float:
        """X offset for the first label column, just right of the symbol outline."""
        x0, _y0, w, _h = self.symbol.select_box
        right = x0 + w
        if right > 0:
            return right + _LABEL_MARGIN
        return _DEFAULT_LABEL_X

    def _all_prop_keys(self) -> list[str]:
        """Ordered list of every key that can be displayed as a label, in the
        on-canvas stacking order: refdes, references, model, then parameters.
        Internal params (starting with '_') are excluded — they are never shown."""
        keys = ["refdes"]
        keys += [f"ref {i + 1}" for i in range(self.ref_count())]
        if self.model:
            keys.append("model")
        keys += [k for k in self.params if not k.startswith("_")]
        # DC operating-point current annotation (NGspice back-annotation):
        # i(<refdes>) exists in an op run for independent V-sources and
        # inductors (both MNA unknowns). Shown only when the Properties
        # dialog enabled it (prop_display); never offered elsewhere.
        if self.symbol.prefix in ("V", "L"):
            keys.append("dc_current")
        return keys

    def _prop_value(self, key: str) -> str:
        """Raw value string for a property key."""
        if key == "refdes":
            return self.instance_id
        if key == "model":
            return self.model
        if key.startswith("ref "):
            try:
                idx = int(key.split()[1]) - 1
                return self.refs[idx] if idx < len(self.refs) else ""
            except (ValueError, IndexError):
                return ""
        return self.params.get(key, "")

    def _prop_text(self, key: str) -> str:
        """
        Fallback plain text for a property, honouring prop_display settings.
        For {…} expressions the braces are stripped so the raw expression is
        shown when LaTeX rendering is unavailable.
        Returns "" when nothing should be shown.
        """
        show_val, show_name = self.prop_display.get(key, (False, False))
        if not show_val:
            return ""
        val = self._prop_value(key)
        if not val:
            return ""
        # strip braces for plain-text display of expressions
        display_val = val.strip()
        if display_val.startswith("{") and display_val.endswith("}"):
            display_val = display_val[1:-1].strip()
        return f"{key} = {display_val}" if show_name else display_val

    # ── label management ──────────────────────────────────────────────────────

    def _save_label_offsets(self) -> None:
        """Persist current label positions into prop_offsets."""
        for key, lbl in self._labels.items():
            self.prop_offsets[key] = (lbl.pos().x(), lbl.pos().y())

    def update_labels(self) -> None:
        """Rebuild visible property labels from prop_display."""
        from .latex_label import (
            LATEX_INSTALLED, cache_dir_of, is_expression,
            render_expression, render_name_eq_value,
        )

        style = style_of(self)
        # LaTeX labels need the system tools AND this schematic's preference;
        # renders land in this schematic's own cache sidecar. BEFORE the
        # item is in a scene the labels stay plain text: a pre-scene render
        # would go to the SESSION temp (cache misses — one pdflatex per
        # label, ~10 s per schematic load, Anton 2026-07-12); the
        # scene-entry hook re-runs this with the schematic's own cache.
        use_latex = (LATEX_INSTALLED and style.LATEX_RENDERING_ENABLED
                     and self.scene() is not None)
        cache = cache_dir_of(self)

        self._save_label_offsets()

        for lbl in list(self._labels.values()):
            _discard_label(lbl)
        self._labels.clear()

        # Ensure a default offset exists for every known property.
        # Always use +label_x; the rendering side adapts for h_flip.
        label_x = self._label_x()
        for i, key in enumerate(self._all_prop_keys()):
            if key not in self.prop_offsets:
                self.prop_offsets[key] = (
                    label_x,
                    _DEFAULT_LABEL_Y0 + i * _DEFAULT_LABEL_STEP,
                )

        for key in self._all_prop_keys():
            show_val, show_name = self.prop_display.get(key, (False, False))
            if not show_val:
                continue

            if key == "dc_current":
                lbl = _PropertyLabel(key, self)
                lbl.set_text(self._dc_current_text())
                lbl.setToolTip(
                    "DC operating-point current i(%s) — NGspice convention: "
                    "measured INTO the + terminal (a source driving a load "
                    "reads negative)" % self.instance_id)
                lbl.setPos(QPointF(*self.prop_offsets[key]))
                lbl.setTransform(_counter_transform(self.rotation(),
                                                    self.h_flip, self.v_flip))
                self._labels[key] = lbl
                continue

            raw_val = self._prop_value(key)
            if not raw_val:
                continue

            lbl = _PropertyLabel(key, self)

            # V/I source stimuli labels: dc, ac, tran displayed as formatted labels
            # generated on-the-fly from the canonical param values.
            if self.symbol.prefix in ("V", "I") and key in ("dc", "ac", "tran"):
                from .latex_label import render_stimuli_label
                pfx, pairs = _vi_stimuli_display(key, self.params)
                svg = (render_stimuli_label(pfx, pairs, cache_dir=cache)
                       if use_latex else None)
                if svg is not None:
                    lbl.set_svg(svg)
                else:
                    text = pfx + "|".join(f"{pn}={pv}" for pn, pv in pairs)
                    lbl.set_text(text or raw_val)
                lbl.setPos(QPointF(*self.prop_offsets[key]))
                lbl.setTransform(_counter_transform(self.rotation(), self.h_flip, self.v_flip))
                self._labels[key] = lbl
                continue

            # Parameter values are LaTeX expressions by default: the user enters
            # the bare expression and the braces that mark it as an expression
            # are added here for rendering (refdes/model/refs are left as-is).
            # Power symbols' "name" param is a net name, not an expression.
            is_param = key in self.params and self.symbol_name not in ("0", "port")
            render_val = wrap_braces(raw_val) if is_param else raw_val

            if is_expression(render_val):
                if not use_latex:
                    svg = None
                elif show_name:
                    svg = render_name_eq_value(key, render_val, cache_dir=cache)
                else:
                    svg = render_expression(render_val, cache_dir=cache)
                if svg is not None:
                    lbl.set_svg(svg)
                else:
                    lbl.set_text(self._prop_text(key))
            elif key == "refdes" and style.COMP_LABEL_LATEX and use_latex:
                # IEEE-style element identifiers: refdes through the SLiCAP
                # LaTeX chokepoint, optionally upright bold, tinted with the
                # refdes colour preference (all from this schematic's style).
                from .latex_label import recolor_svg, render_refdes
                svg = render_refdes(raw_val, style.COMP_LABEL_LATEX_BOLD,
                                    cache_dir=cache)
                if svg is not None:
                    lbl.set_svg(recolor_svg(
                        svg, style.COMP_LABEL_COLOR.name()))
                else:
                    lbl.set_text(self._prop_text(key))
            else:
                lbl.set_text(self._prop_text(key))

            lbl.setPos(QPointF(*self.prop_offsets[key]))
            lbl.setTransform(_counter_transform(self.rotation(), self.h_flip, self.v_flip))
            self._labels[key] = lbl

    def _dc_current_text(self) -> str:
        """The "I: <value>" bias annotation from the scene's op store —
        placeholder "I: —" until an unstepped op run made values available."""
        scene = self.scene()
        value = (scene.dc_current(self.instance_id)
                 if hasattr(scene, "dc_current") else None)
        if value is None:
            return "I: —"
        from SLiCAP.SLiCAPlex import _eng_notation
        return f"I: {_eng_notation(value, style_of(self).BIAS_DIGITS)}"

    def refresh_svg_labels(self) -> None:
        """Re-scale all SVG-mode labels using the style's LABEL/PARAM SVG heights.

        Re-uses cached SVG bytes so no LaTeX recompilation happens.
        """
        for lbl in self._labels.values():
            if lbl._svg_bytes:
                lbl.set_svg(lbl._svg_bytes, lbl._prefix)
        self.update()

    # ── geometry ──────────────────────────────────────────────────────────────

    def boundingRect(self):
        br = super().boundingRect()
        for lbl in self._labels.values():
            br = br.united(lbl.mapRectToParent(lbl.boundingRect()))
        # Always include the pin-marker squares so they're never clipped; kept
        # independent of connection state so toggling a marker is just an update().
        size = style_of(self).HANDLE_SIZE
        h = size / 2.0
        for lx, ly in self.symbol.pins:
            br = br.united(QRectF(lx - h, ly - h, size, size))
        return br

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(*self.symbol.select_box))
        return path

    def pin_scene_pos(self) -> list[QPointF]:
        """World positions of all pins, in node order."""
        return [
            self.mapToScene(QPointF(lx, ly))
            for lx, ly in self.symbol.pins
        ]

    def reload_symbol(self, symbol) -> None:
        """Swap this instance's symbol for a freshly loaded definition
        (artwork AND metadata — the component keeps its own Symbol record).

        Connections are deliberately NOT re-derived: pins may have moved, so the
        caller (and ultimately the user) is responsible for repairing wiring."""
        self.prepareGeometryChange()
        self.symbol = symbol
        self.symbol_name = symbol.name
        stripped, self.symbol_texts = _split_symbol_text(symbol.svg)
        self._svg_bytes = stripped
        self._renderer = QSvgRenderer(
            QByteArray(_apply_symbol_colors(stripped, style_of(self))))
        self.setSharedRenderer(self._renderer)
        # Pin count may have changed; mark every pin unconnected until the scene
        # re-runs connectivity (_sync_junctions) and corrects the markers.
        self._unconnected_pins = set(range(len(symbol.pins)))
        self.update_labels()
        self.update()

    def set_unconnected_pins(self, indices: set[int]) -> None:
        """Record which pin indices have nothing attached (scene calls this)."""
        new = set(indices)
        if new != self._unconnected_pins:
            self._unconnected_pins = new
            self.update()

    def mousePressEvent(self, event):
        # Clicking the symbol body (not a label) clears the focused attribute,
        # so all leader lines show again.
        self._active_label_key = None
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            # Style comes from the scene: recolour the artwork and rebuild the
            # labels with the owning schematic's style.
            self._renderer = QSvgRenderer(
                QByteArray(_apply_symbol_colors(self._svg_bytes, style_of(self))))
            self.setSharedRenderer(self._renderer)
            self.update_labels()
        if change == QGraphicsItem.ItemSelectedHasChanged and not value:
            self._active_label_key = None      # deselected → forget focused label
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Save old position here — self.pos() is still the old value at this point.
            self._prev_pos = self.pos()
            return snap(value)
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            if (self._prev_pos is not None
                    and not getattr(self.scene(), '_group_drag_active', False)):
                delta = self.pos() - self._prev_pos
                if delta.x() or delta.y():
                    self._rubber_band_wires(delta)
        if change == QGraphicsItem.ItemRotationHasChanged:
            ct = _counter_transform(self.rotation(), self.h_flip, self.v_flip)
            for lbl in self._labels.values():
                lbl.setTransform(ct)
        return super().itemChange(change, value)

    def _rubber_band_wires(self, delta: QPointF) -> None:
        """Stretch the wires attached to this component's pins so they follow it.

        Only wires that were attached AT THE START of the drag move — captured
        lazily on the first move and reused for the rest of the drag. A wire the
        component merely passes over mid-drag is never captured, so moving a
        component can never steal (and thereby disconnect) another element's
        wire. The captured set is reset to None by the scene on every press.
        """
        from .wire_item import WireItem
        # After ItemPositionHasChanged, self.pos() is the new position; the wires
        # are still at the previous pin positions = current pins minus this delta.
        if self._drag_wires is None:
            start_keys = {_pt_key(p - delta) for p in self.pin_scene_pos()}
            self._drag_wires = [
                (item, i)
                for item in self.scene().items()
                if isinstance(item, WireItem) and not getattr(item, "_preview", False)
                for i, pt in enumerate(item.points) if _pt_key(pt) in start_keys
            ]
        by_wire: dict = {}
        for wire, idx in self._drag_wires:
            if wire.scene() is not None:
                by_wire.setdefault(wire, set()).add(idx)
        for wire, idxs in by_wire.items():
            wire.move_points(idxs, delta)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        style = style_of(self)

        # Embedded symbol text (+/- markers, noise labels …) — drawn on top of the
        # artwork and kept upright/unmirrored under any rotation/flip.
        draw_symbol_texts(painter, self.symbol_texts,
                          self.rotation(), self.h_flip, self.v_flip, style=style)

        # Pin markers — small grey squares on UNCONNECTED pins; they disappear as
        # soon as a wire or another pin connects to the pin (the scene keeps
        # _unconnected_pins in sync). Drawn here so they sit on top of the symbol.
        if self._unconnected_pins:
            pins = self.symbol.pins
            size = style.HANDLE_SIZE
            h = size / 2.0
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(style.CONNECTION_COLOR)
            for i in self._unconnected_pins:
                if i < len(pins):
                    lx, ly = pins[i]
                    painter.drawRect(QRectF(lx - h, ly - h, size, size))
            painter.restore()

        # Pin names — only for symbols that opt in via data-show-pinnames (the
        # auto-generated subcircuit boxes, whose shape carries no pin meaning).
        # Each name is counter-transformed so it stays horizontal and unmirrored
        # under any rotation/flip of the block.
        if self.symbol.show_pinnames:
            draw_subckt_pin_names(
                painter,
                self.symbol.nodes,
                self.symbol.pins,
                self.rotation(), self.h_flip, self.v_flip,
                style=style,
            )

        # Dashed leader lines from the symbol centre to its attribute labels,
        # drawn while the component is selected.  A clicked attribute shows only
        # its own leader; selecting the body (no active label) shows them all.
        if self._labels and ((option.state & QStyle.State_Selected) or self._show_leaders):
            active = self._labels.get(self._active_label_key)
            painter.save()
            painter.setPen(QPen(style.COMP_LABEL_COLOR, 0.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            origin = QPointF(0.0, 0.0)
            targets = [active] if active is not None else list(self._labels.values())
            for lbl in targets:
                painter.drawLine(origin, lbl.pos())
            painter.restore()

        if option.state & QStyle.State_Selected:
            painter.save()
            painter.setPen(QPen(QColor(0, 120, 215), 1.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(*self.symbol.select_box))
            painter.restore()
