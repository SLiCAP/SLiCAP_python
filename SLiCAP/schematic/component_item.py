import weakref

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem, QStyle
from PySide6.QtCore import QByteArray, Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QFont, QFontMetricsF, QTransform, QPainterPath

from . import config
from .config import (
    snap,
    COMP_LABEL_FONT, COMP_LABEL_COLOR, COMP_LABEL_SVG_HEIGHT,
    COMP_PARAM_SVG_HEIGHT,
    COMP_PARAM_FONT, COMP_PARAM_COLOR,
)

# Unconnected-pin markers reuse the wire-handle size and a dedicated connection
# colour, both configured in Preferences ("Wire handles / connections"). Read
# live from config so a Preferences change takes effect on the next repaint.


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
# Smaller than the property-label font so four names fit inside a compact box.
_PIN_NAME_FONT = QFont(COMP_PARAM_FONT)
_PIN_NAME_FONT.setPointSize(5)


def draw_subckt_pin_names(painter, nodes, pins, rotation=0.0,
                          h_flip=False, v_flip=False) -> None:
    """Draw subcircuit pin names just inside the outline, one per pin.

    Each name is counter-transformed so it stays horizontal and unmirrored under
    any rotation/flip, and anchored to grow inward from its box edge so it never
    pokes out.  Shared by ComponentItem.paint and the Place Subcircuit preview.
    """
    ct = _counter_transform(rotation, h_flip, v_flip)
    fm = QFontMetricsF(_PIN_NAME_FONT)
    painter.save()
    painter.setPen(config.SYMBOL_TEXT_COLOR)
    painter.setFont(_PIN_NAME_FONT)
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


# ── symbol metadata ───────────────────────────────────────────────────────────
# These dicts are the single source of truth for placed components.  They start
# empty and are filled by SymbolLibrary.inject_into_component_item() at startup,
# straight from the symbols' own data-* attributes — nothing comes from the
# SLiCAP Python package's model tables.  Other modules import these dicts by
# reference, so they are mutated in place (never reassigned).

SYMBOL_PREFIX:      dict[str, str]                       = {}  # name → refdes prefix
PIN_POSITIONS:      dict[str, list[tuple[float, float]]] = {}  # name → pin coords (node order)
SYMBOL_TIGHT_RECT:  dict[str, tuple[float, float, float, float]] = {}  # name → select box
SYMBOL_NODES:       dict[str, list[str]]                 = {}  # name → node names
SYMBOL_MODEL:       dict[str, str]                       = {}  # name → SLiCAP model
SYMBOL_PARAMS:      dict[str, list[str]]                 = {}  # name → param names
SYMBOL_REFS:        dict[str, int]                       = {}  # name → # of references
SYMBOL_DESCRIPTION: dict[str, str]                       = {}  # name → description
SYMBOL_INFO:        dict[str, str]                       = {}  # name → help/info URL
SYMBOL_SHOW_PINNAMES: dict[str, bool]                    = {}  # name → draw node names?

# Fixed params for power symbols (ground, port) — {symbol: {param: default}}.
# These carry no SLiCAP model, so their editable field is supplied here.
_SYMBOL_FIXED_PARAMS: dict[str, dict[str, str]] = {
    "ground": {"name": "0"},
    "port":   {"name": ""},
}


def available_models(symbol_name: str) -> list[str]:
    """Return the SLiCAP model(s) for this symbol — at most one (data-model)."""
    model = SYMBOL_MODEL.get(symbol_name, "")
    return [model] if model else []


def params_for_symbol(symbol_name: str) -> dict[str, str]:
    """Return a params dict for the symbol (preserving param order).
    For non-subcircuit symbols the 'value' parameter gets '?' as a reminder;
    all other parameters default to '' and are omitted from the netlist when unset.
    Subcircuit/hierarchical blocks (prefix 'X') always use '' so the user is not
    prompted for parameters that may be optional or auto-filled."""
    is_sub = SYMBOL_PREFIX.get(symbol_name) == "X"
    return {k: ("?" if k == "value" and not is_sub else "") for k in SYMBOL_PARAMS.get(symbol_name, [])}


def fixed_params_for_symbol(symbol_name: str) -> dict[str, str]:
    """Return a default params dict for power symbols (ground, port)."""
    return dict(_SYMBOL_FIXED_PARAMS.get(symbol_name, {}))


def refs_for_symbol(symbol_name: str) -> int:
    """Return the number of element references this symbol requires."""
    return SYMBOL_REFS.get(symbol_name, 0)


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

_LABEL_FONT       = COMP_LABEL_FONT      # refdes font (also used for LaTeX-mode prefix text)
_LABEL_SVG_HEIGHT = COMP_LABEL_SVG_HEIGHT
_PARAM_FONT       = COMP_PARAM_FONT      # parameter plain-text font
_PARAM_SVG_HEIGHT = COMP_PARAM_SVG_HEIGHT

# All live ComponentItem instances — used by config.apply() to re-render SVG
# labels when the latex scale preference changes.
_live_components: weakref.WeakSet = weakref.WeakSet()

_DEFAULT_LABEL_X    = 32   # fallback when no tight rect is available
_DEFAULT_LABEL_Y0   = -10
_DEFAULT_LABEL_STEP = 12
_LABEL_MARGIN       = 5    # gap between symbol right edge and first label column


class _PropertyLabel(QGraphicsItem):
    """
    Movable label for one component property — supports plain text and SVG modes.

    In SVG mode (a rendered LaTeX expression) the SVG is scaled to
    _LABEL_SVG_HEIGHT scene units tall; an optional prefix string is drawn
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
            if change == QGraphicsItem.ItemPositionChange:
                p.prepareGeometryChange()
            elif change == QGraphicsItem.ItemPositionHasChanged:
                p.update()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        p = self.parentItem()
        if p is not None:
            p._label_active = True
            p.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        p = self.parentItem()
        if p is not None:
            p._label_active = False
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
        target_h = _LABEL_SVG_HEIGHT if self.prop_key == "refdes" else _PARAM_SVG_HEIGHT
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
        if self.prop_key == "refdes":
            return _LABEL_FONT, COMP_LABEL_COLOR
        return _PARAM_FONT, COMP_PARAM_COLOR

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


def _apply_symbol_colors(svg_bytes: bytes) -> bytes:
    """
    Substitute configurable symbol colours into raw SVG bytes.

    Explicit stroke="black" and fill="black" (arrowheads, dots) are replaced
    with SYMBOL_STROKE_COLOR.  <text> elements that have no explicit fill get
    one added so they render in SYMBOL_TEXT_COLOR.
    """
    from .config import SYMBOL_STROKE_COLOR, SYMBOL_TEXT_COLOR
    stroke = SYMBOL_STROKE_COLOR.name()
    text_c = SYMBOL_TEXT_COLOR.name()
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

    def __init__(self, svg_bytes: bytes):
        super().__init__()
        self._renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(svg_bytes)))
        self.setSharedRenderer(self._renderer)

    def boundingRect(self):
        return self._renderer.viewBoxF()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        self._renderer.render(painter, self._renderer.viewBoxF())


def make_ghost(svg_bytes: bytes) -> _ViewBoxSvgItem:
    """Semi-transparent drag preview used during placement mode."""
    item = _ViewBoxSvgItem(svg_bytes)
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

    def __init__(self, symbol_name: str, instance_id: str, svg_bytes: bytes):
        super().__init__(svg_bytes)
        self.symbol_name  = symbol_name
        self.instance_id  = instance_id
        self._svg_bytes   = svg_bytes
        self.model: str   = SYMBOL_MODEL.get(symbol_name, "")
        self.params: dict[str, str]  = params_for_symbol(symbol_name) or fixed_params_for_symbol(symbol_name)
        _n_refs = refs_for_symbol(symbol_name)
        _is_sub = SYMBOL_PREFIX.get(symbol_name) == "X"
        self.refs: list[str] = [] if _is_sub else ["?"] * _n_refs
        # Ground and port are power symbols — show net name, never refdes
        _show_refdes = symbol_name not in ("ground", "port")
        self.prop_display: dict[str, tuple[bool, bool]] = {"refdes": (_show_refdes, False)}
        if symbol_name in ("ground", "port"):
            self.prop_display["name"] = (True, False)
        # Show "value" and ref fields by default for new placements
        if "value" in self.params:
            self.prop_display["value"] = (True, False)
        for i in range(refs_for_symbol(symbol_name)):
            self.prop_display[f"ref {i + 1}"] = (True, False)
        # Subcircuit (X) blocks show their name (the .subckt / model) outside the
        # outline by default; the pin names are drawn inside (see paint()).
        if SYMBOL_PREFIX.get(symbol_name) == "X" and self.model:
            self.prop_display["model"] = (True, False)
        # A "?" placeholder model (the symbol's data-model SVG meta field) means a
        # .model definition is still required — show it on the canvas as a reminder.
        elif self.model == "?":
            self.prop_display["model"] = (True, False)
        self.prop_offsets: dict[str, tuple[float, float]] = {}
        self.h_flip: bool = False
        self.v_flip: bool = False
        self._labels: dict[str, _PropertyLabel] = {}
        self._label_active: bool = False
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(1)   # above wires (Z=0) so labels are always selectable
        self._prev_pos: "QPointF | None" = None
        # Wires captured at the start of a drag (as [(wire, point_index), …]) so
        # they follow this component's pins. None until the first move of a drag;
        # reset to None by the scene at every mouse press. See _rubber_band_wires.
        self._drag_wires: "list | None" = None
        # Indices of pins with nothing connected to them — drawn as grey markers.
        # Starts with all pins unconnected; the scene refreshes this on every
        # topology change (via _sync_junctions → _refresh_pin_markers).
        self._unconnected_pins: set[int] = set(
            range(len(PIN_POSITIONS.get(symbol_name, [])))
        )
        self.update_labels()
        _live_components.add(self)

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
        ct = self._flip_transform()
        for lbl in self._labels.values():
            lbl.setTransform(ct)

    # ── property helpers ──────────────────────────────────────────────────────

    def _label_x(self) -> float:
        """X offset for the first label column, just right of the symbol outline."""
        tight = SYMBOL_TIGHT_RECT.get(self.symbol_name)
        if tight:
            x0, _y0, w, _h = tight
            right = x0 + w
            if right > 0:
                return right + _LABEL_MARGIN
        return _DEFAULT_LABEL_X

    def _all_prop_keys(self) -> list[str]:
        """Ordered list of every key that can be displayed as a label."""
        keys = ["refdes"] + list(self.params.keys())
        n_refs = refs_for_symbol(self.symbol_name)
        keys += [f"ref {i + 1}" for i in range(n_refs)]
        if self.model:
            keys.append("model")
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
        from .latex_label import is_expression, render_expression, render_name_eq_value

        self._save_label_offsets()

        for lbl in list(self._labels.values()):
            lbl.setParentItem(None)
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
            raw_val = self._prop_value(key)
            if not raw_val:
                continue

            lbl = _PropertyLabel(key, self)

            # Parameter values are LaTeX expressions by default: the user enters
            # the bare expression and the braces that mark it as an expression
            # are added here for rendering (refdes/model/refs are left as-is).
            # Power symbols' "name" param is a net name, not an expression.
            is_param = key in self.params and self.symbol_name not in ("ground", "port")
            render_val = wrap_braces(raw_val) if is_param else raw_val

            if is_expression(render_val):
                if show_name:
                    svg = render_name_eq_value(key, render_val)
                else:
                    svg = render_expression(render_val)
                if svg is not None:
                    lbl.set_svg(svg)
                else:
                    lbl.set_text(self._prop_text(key))
            else:
                lbl.set_text(self._prop_text(key))

            lbl.setPos(QPointF(*self.prop_offsets[key]))
            lbl.setTransform(_counter_transform(self.rotation(), self.h_flip, self.v_flip))
            self._labels[key] = lbl

    def refresh_svg_labels(self) -> None:
        """Re-scale all SVG-mode labels using the current _LABEL/_PARAM_SVG_HEIGHT.

        Called by config.apply() when the latex_scale preference changes.
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
        size = config.HANDLE_SIZE
        h = size / 2.0
        for lx, ly in PIN_POSITIONS.get(self.symbol_name, []):
            br = br.united(QRectF(lx - h, ly - h, size, size))
        return br

    def shape(self) -> QPainterPath:
        tight = SYMBOL_TIGHT_RECT.get(self.symbol_name)
        r = QRectF(*tight) if tight is not None else self.renderer().viewBoxF()
        path = QPainterPath()
        path.addRect(r)
        return path

    def pin_scene_pos(self) -> list[QPointF]:
        """World positions of all pins, in PIN_POSITIONS order."""
        return [
            self.mapToScene(QPointF(lx, ly))
            for lx, ly in PIN_POSITIONS.get(self.symbol_name, [])
        ]

    def reload_svg(self, svg_bytes: bytes) -> None:
        """Swap this instance's artwork for a freshly loaded symbol definition.

        Rebuilds the SVG renderer, re-derives geometry-dependent state (bounding
        rect, label anchor, pin markers) and the labels.  Symbol *metadata*
        (pins, params, model …) must already have been republished into the
        component_item globals via SymbolLibrary.inject_into_component_item().

        Connections are deliberately NOT re-derived: pins may have moved, so the
        caller (and ultimately the user) is responsible for repairing wiring."""
        self.prepareGeometryChange()
        self._svg_bytes = svg_bytes
        self._renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(svg_bytes)))
        self.setSharedRenderer(self._renderer)
        # Pin count may have changed; mark every pin unconnected until the scene
        # re-runs connectivity (_sync_junctions) and corrects the markers.
        self._unconnected_pins = set(range(len(PIN_POSITIONS.get(self.symbol_name, []))))
        self.update_labels()
        self.update()

    def set_unconnected_pins(self, indices: set[int]) -> None:
        """Record which pin indices have nothing attached (scene calls this)."""
        new = set(indices)
        if new != self._unconnected_pins:
            self._unconnected_pins = new
            self.update()

    def itemChange(self, change, value):
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
                for item in self.scene().items() if isinstance(item, WireItem)
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

        # Pin markers — small grey squares on UNCONNECTED pins; they disappear as
        # soon as a wire or another pin connects to the pin (the scene keeps
        # _unconnected_pins in sync). Drawn here so they sit on top of the symbol.
        if self._unconnected_pins:
            pins = PIN_POSITIONS.get(self.symbol_name, [])
            size = config.HANDLE_SIZE
            h = size / 2.0
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(config.CONNECTION_COLOR)
            for i in self._unconnected_pins:
                if i < len(pins):
                    lx, ly = pins[i]
                    painter.drawRect(QRectF(lx - h, ly - h, size, size))
            painter.restore()

        # Pin names — only for symbols that opt in via data-show-pinnames (the
        # auto-generated subcircuit boxes, whose shape carries no pin meaning).
        # Each name is counter-transformed so it stays horizontal and unmirrored
        # under any rotation/flip of the block.
        if SYMBOL_SHOW_PINNAMES.get(self.symbol_name, False):
            draw_subckt_pin_names(
                painter,
                SYMBOL_NODES.get(self.symbol_name, []),
                PIN_POSITIONS.get(self.symbol_name, []),
                self.rotation(), self.h_flip, self.v_flip,
            )

        # Dashed leader lines — when component or any of its labels is active
        if self._labels and ((option.state & QStyle.State_Selected) or self._label_active):
            painter.save()
            painter.setPen(QPen(COMP_LABEL_COLOR, 0.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            origin = QPointF(0.0, 0.0)
            for lbl in self._labels.values():
                painter.drawLine(origin, lbl.pos())
            painter.restore()

        if option.state & QStyle.State_Selected:
            painter.save()
            painter.setPen(QPen(QColor(0, 120, 215), 1.0))
            painter.setBrush(Qt.NoBrush)
            tight = SYMBOL_TIGHT_RECT.get(self.symbol_name)
            rect = QRectF(*tight) if tight else super().boundingRect()
            painter.drawRect(rect)
            painter.restore()
