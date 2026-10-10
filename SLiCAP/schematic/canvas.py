import base64
import re
from enum import Enum, auto

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsSimpleTextItem,
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform, QTextCursor, QPixmap, QPolygonF

from . import config as _config
from .config import (
    GRID_SIZE, GRID_MAJOR, DEFAULT_ZOOM, snap, snap_pos,
    Z_WIRE, Z_WIRE_DRAG,
)
from .component_item import ComponentItem, make_ghost, _discard_label, _PropertyLabel
from .wire_item import WireItem
from .junction_item import JunctionItem
from .free_text_item import FreeTextItem
from .command_item import CommandItem
from .border_item import BorderItem
from .library_item import LibraryItem
from .image_item import ImageItem
from .latex_fragment_item import LatexFragmentItem
from .parameter_item import ParameterItem
from .analysis_item import AnalysisItem
from .hyperlink_item import HyperlinkItem
from .shape_item import ShapeItem
from .model_item import ModelItem


class _Mode(Enum):
    NORMAL              = auto()
    PLACING             = auto()
    WIRING              = auto()
    PLACING_JUNCTION    = auto()
    PLACING_TEXT        = auto()
    PLACING_COMMAND     = auto()
    PLACING_BORDER      = auto()
    PLACING_LIBRARY     = auto()
    PLACING_IMAGE       = auto()
    PLACING_LATEX       = auto()
    PLACING_PARAMETER   = auto()
    PLACING_ANALYSIS    = auto()
    PLACING_HYPERLINK   = auto()
    PLACING_MODEL       = auto()
    PLACING_ITEM        = auto()   # a prepared item follows the cursor (symbol pins, texts)
    PASTING             = auto()
    DRAWING_LINE        = auto()
    DRAWING_RECT        = auto()
    DRAWING_ELLIPSE     = auto()
    DRAWING_POLYGON     = auto()

_FREE_PLACEMENT_MODES = (_Mode.PLACING_TEXT, _Mode.PLACING_HYPERLINK,
                         _Mode.PLACING_IMAGE, _Mode.PLACING_LATEX)


# ── helpers ──────────────────────────────────────────────────────────────────

def _shape_record(item):
    """The data record of a shape (file, undo and clipboard share it)."""
    from .schematic_data import ShapeData
    return ShapeData(
        kind=item.kind,
        x=item.pos().x(), y=item.pos().y(),
        rel_points=[(p.x(), p.y()) for p in item.rel_points],
        stroke_color=item.stroke_color,
        fill_color=item.fill_color,
        fill_style=item.fill_style,
        line_style=item.line_style,
        line_end_start=item.line_end_start,
        line_end_end=item.line_end_end,
        line_width=item.line_width,
        rotation=item.rotation,
        head_width=item.head_width,
        head_length=item.head_length,
        arc_start=item.arc_start, arc_sweep=item.arc_sweep,
        closed=item.closed,
        expression=item.expression, var=item.var,
        x_range=list(item.x_range), y_range=list(item.y_range),
        x_log=item.x_log, num=item.num,
        trace_var=item.trace_var, trace_label=item.trace_label,
        data=[list(p) for p in item.data], flip_x=item.flip_x,
        z=item.zValue(),
    )


def _shape_from_record(sd, delta: QPointF = QPointF(0, 0)):
    """A shape item from its record, shifted by *delta* (paste)."""
    item = ShapeItem(
        kind=sd.kind,
        rel_points=[QPointF(px, py) for px, py in sd.rel_points],
        stroke_color=sd.stroke_color,
        fill_color=sd.fill_color,
        fill_style=sd.fill_style,
        line_style=sd.line_style,
        line_end_start=sd.line_end_start,
        line_end_end=sd.line_end_end,
        line_width=sd.line_width,
        rotation=sd.rotation,
        head_width=sd.head_width,
        head_length=sd.head_length,
        pos=QPointF(sd.x + delta.x(), sd.y + delta.y()),
        arc_start=sd.arc_start, arc_sweep=sd.arc_sweep, closed=sd.closed,
        expression=sd.expression, var=sd.var, x_range=sd.x_range,
        y_range=sd.y_range, x_log=sd.x_log, num=sd.num,
        trace_var=sd.trace_var, trace_label=sd.trace_label, data=sd.data,
        flip_x=sd.flip_x,
    )
    item.setZValue(sd.z)
    return item


def _make_preview_pen() -> QPen:
    pen = QPen(Qt.black, 1.2)
    pen.setStyle(Qt.DashLine)
    return pen


def _build_path(points: list[QPointF]) -> QPainterPath:
    if len(points) < 2:
        return QPainterPath()
    path = QPainterPath(points[0])
    for pt in points[1:]:
        path.lineTo(pt)
    return path


def _elbow(p1: QPointF, p2: QPointF, h_first: bool) -> list[QPointF]:
    """Return the two or three points needed to route from p1 to p2."""
    dx = abs(p1.x() - p2.x())
    dy = abs(p1.y() - p2.y())
    if dx < 0.1 or dy < 0.1:           # already aligned
        return [p1, p2]
    mid = QPointF(p2.x(), p1.y()) if h_first else QPointF(p1.x(), p2.y())
    return [p1, mid, p2]


# ── junction detection ────────────────────────────────────────────────────────

def _pt_key(pt: QPointF) -> tuple[int, int]:
    return (round(pt.x()), round(pt.y()))


def _pt_on_segment(x: int, y: int, p1: QPointF, p2: QPointF) -> bool:
    """True if integer point (x, y) lies strictly between p1 and p2 on an axis-aligned segment."""
    x1, y1 = round(p1.x()), round(p1.y())
    x2, y2 = round(p2.x()), round(p2.y())
    if x1 == x2:
        return x == x1 and min(y1, y2) < y < max(y1, y2)
    if y1 == y2:
        return y == y1 and min(x1, x2) < x < max(x1, x2)
    return False


def _on_wire_interior(pt_key: tuple[int, int], wire) -> bool:
    """True if pt_key lies on wire but is not one of its two endpoint vertices."""
    if len(wire.points) < 2:
        return False
    end_keys = {_pt_key(wire.points[0]), _pt_key(wire.points[-1])}
    if pt_key in end_keys:
        return False
    for pt in wire.points[1:-1]:          # intermediate elbow vertices
        if _pt_key(pt) == pt_key:
            return True
    x, y = pt_key
    for i in range(len(wire.points) - 1):
        if _pt_on_segment(x, y, wire.points[i], wire.points[i + 1]):
            return True
    return False


def _find_junction_points(wires, components) -> set[tuple[int, int]]:
    """
    Return the set of snapped grid points where a junction dot is needed.
    Assumes through-wires have already been split at T-positions.

    Unified rule: a junction is required when the total number of connections
    at a grid point is >= 3, where each wire endpoint and each component pin
    counts as one connection.

    Examples (from the schematic wiring rules picture):
      - R1+R2 series (2 pins, 0 wire endpoints) → 2 connections → no junction
      - Wire+GND     (1 wire endpoint, 1 pin)   → 2 connections → no junction
      - R4+R5+R6     (3 pins, 0 wire endpoints) → 3 connections → junction ✓
      - R11+R12+wire (2 pins, 1 wire endpoint)  → 3 connections → junction ✓
      - T-connection (1 endpoint + wire through) → safety net rule → junction ✓
    """
    # Count wire endpoints per grid point
    endpoints: dict[tuple, int] = {}
    for wire in wires:
        if len(wire.points) < 2:
            continue
        for pt in (wire.points[0], wire.points[-1]):
            k = _pt_key(pt)
            endpoints[k] = endpoints.get(k, 0) + 1

    # Count component pins per grid point
    pin_counts: dict[tuple, int] = {}
    for comp in components:
        for pin_pt in comp.pin_scene_pos():
            k = _pt_key(pin_pt)
            pin_counts[k] = pin_counts.get(k, 0) + 1

    junctions: set[tuple[int, int]] = set()

    # Safety net: wire endpoint landing on the interior of another wire
    for wire in wires:
        if len(wire.points) < 2:
            continue
        for pt in (wire.points[0], wire.points[-1]):
            k = _pt_key(pt)
            for other in wires:
                if other is not wire and _on_wire_interior(k, other):
                    junctions.add(k)
                    break

    # Unified rule: junction when wire_endpoints + component_pins >= 3
    all_points = set(endpoints.keys()) | set(pin_counts.keys())
    for k in all_points:
        if endpoints.get(k, 0) + pin_counts.get(k, 0) >= 3:
            junctions.add(k)

    return junctions


# ── scene ─────────────────────────────────────────────────────────────────────

# Annotations are placed and dragged FREELY; everything that connects or
# aligns with wires (components, wires, junctions, border, shapes, the
# parameter / analysis / model / library / command blocks) snaps to the
# grid. Free text and LaTeX fragments used to snap while component labels
# did not, which made captions such as "+", "-" and a voltage name
# impossible to align with a symbol (Anton, 2026-09-26). The item classes
# of these kinds do not snap in itemChange either. The set itself,
# _FREE_PLACEMENT_MODES, is defined right after _Mode. One exception: an
# image that LINKS a drawing (a schematic or a poster on a poster) snaps,
# in placement and in itemChange: it is a drawing on the same grid, and
# at 100 % its grid is the poster's (Anton, 2026-10-09). Plain images and
# figures stay free.


# ONE clipboard for every scene of the process, so a selection copied on one
# schematic or symbol pastes on another (Anton, 2026-09-27: a symbol drawing
# had to be redrawn for the other dialect). What a scene can take from it is
# decided at paste time (SchematicScene._pasteable).
_SHARED_CLIPBOARD: list = []

_SYMBOL_ONLY_KINDS = ("pin", "symbol_text", "opaque")
_SCHEMATIC_ONLY_KINDS = ("component", "wire", "command", "free_text", "analysis",
                         "hyperlink", "model", "parameters")


class SchematicScene(QGraphicsScene):

    # Placement signals, one meaning each (2026-09-26; before, placing_cancelled
    # fired for EVERY way a placement ended, and the window read it as "the user
    # cancelled": starting a new placement then reopened the symbol dialog).
    placing_started   = Signal()      # a placing / drawing / paste mode became
                                      # active (view: NoDrag, cross cursor)
    placing_ended     = Signal()      # the scene left that mode, for any reason:
                                      # placed, superseded, cancelled (view: normal)
    placing_cancelled = Signal(str)   # the USER ended it (Escape): the symbol
                                      # name of a component placement, '' otherwise
                                      # (window: offer that symbol again)
    wire_mode_started = Signal()
    wire_mode_ended   = Signal()
    data_changed      = Signal()   # emitted on every new undo snapshot
    group_move_started = Signal()
    group_move_ended   = Signal()

    def __init__(self):
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.show_origin = False          # symbol editor: an OriginItem
        # stroke width of a NEW shape: 1.5 for annotations on a schematic,
        # 1.0 in the symbol editor, the width of the library's symbols
        # (Anton, 2026-09-27: an added emitter line was thicker than the rest)
        self.default_line_width = 1.5
        self.apply_theme()

        # Strong references to every top-level item (see addItem): shiboken
        # keeps a Python-created QGraphicsItem alive only through its Python
        # wrapper — once the creating wrapper is gone, the transient
        # wrappers scene.items() returns can DELETE the C++ item when they
        # are garbage-collected (the exported schematic lost its wires,
        # Anton 2026-07-12). Pinning makes item lifetime explicit: an item
        # lives until removeItem()/clear().
        self._pinned: set = set()
        # Items removed during the current event, released when the event
        # loop has turned (see removeItem). Qt may still hold a removed
        # item for the rest of the event delivery that caused the removal:
        # a label discarded by the rebuild after its own double-click, a
        # component replaced by Change symbol from its dialog. Freeing it
        # at once left Qt a dangling pointer, the pattern behind a
        # segmentation fault on the click after a dialog (Anton,
        # 2026-10-10; a user's report on 6.1.0). This is deleteLater for
        # graphics items.
        self._retired: list = []

        # The schematic's own drawing style.  The owning panel replaces this
        # with the Style loaded from the file's sidecar; items resolve their
        # style through the scene (config.style_of), so several open
        # schematics never share style state.
        self.style = _config.default_style()
        # The document properties of the drawing shown (from_data; the panel
        # keeps them in step): what the properties block renders.
        self.document_properties = None
        # The schematic's own LaTeX render-cache directory (the ``<name>.cache``
        # sidecar), set by the owning panel; None → the session temp.  Items
        # resolve it via latex_label.cache_dir_of.
        self.cache_dir = None

        # DC operating-point results for bias back-annotation (NGspice):
        # lower-case vector name → float, from the circuit's most recent
        # UNSTEPPED op run in this session (<cir>_op.raw, loaded by the
        # panel after every instruction run). op_netlist is the .cir the
        # raw was produced from — the NAMING AUTHORITY for the nets (the
        # sims run on that file as last exported). Values are never
        # persisted; a NETLIST-RELEVANT edit marks them stale (greyed) —
        # cosmetic edits (annotation toggles, label drags) do not.
        self.op_results: "dict | None" = None
        self.op_netlist: "str | None" = None
        self.op_stale: bool = False
        self._op_fingerprint: "str | None" = None
        # Borrowed op context for a SUBCIRCUIT schematic opened via descend:
        # the values shown are the PARENT run's, for ONE instance (the one
        # descended from — the definition/instance rule, Anton 2026-08-05).
        # op_prefix is the dotted instance path ("x1", "x1.x2"); op_port_nets
        # maps this schematic's port net names to the raw's names for the
        # parent nets they connect to (inside a subckt the port nets ARE the
        # parent nets — NGspice only dot-prefixes the internal ones).
        self.op_prefix: "str | None" = None
        self.op_port_nets: dict = {}
        self.data_changed.connect(self._mark_op_stale)

        self._mode            = _Mode.NORMAL
        self._ghost           = None
        self._placing_name    = None
        self._placing_svg     = None
        self._counters: dict[str, int] = {}

        self._wire_points: list[QPointF] = []
        self._wire_preview: QGraphicsPathItem | None = None
        self._wire_h_first  = True
        self._last_cursor: QPointF | None = None

        self._vdrag_wire:        WireItem | None = None
        self._vdrag_idx:         int | None = None
        self._vdrag_rb:          list = []        # [(wire, endpoint_index, original_QPointF)]
        self._vdrag_pin_anchor:  tuple | None = None  # (comp, (lx, ly)) if vertex was on a pin
        self._vdrag_pin_preview: WireItem | None = None

        self._wire_move_wires:     list = []
        self._wire_move_origins:   list = []
        self._wire_move_others:    list = []
        self._wire_move_start:     QPointF | None = None
        # Scene-driven label drag (net-name / bias labels): Qt's movable
        # machinery cannot be used — a covering top-level item receives the
        # press, and an explicit grab misses the button-down bookkeeping
        # (the label "jumped off the pointer", Anton 2026-07-12).
        self._label_drag: "tuple | None" = None   # (label, orig_pos, press_scene_pos)
        self._label_group_move_items: list = []   # [(label, orig scene pos)] in a group move
        self._wire_move_moved:     bool = False
        self._wire_move_rb:        list = []   # [(wire, {idx: orig_QPointF})]
        self._wire_move_junctions: list = []   # [(JunctionItem, orig_QPointF)]
        self._pin_anchors:         list = []   # [(anchor_QPointF, comp, (lx,ly))]
        self._pin_preview_wires:   list = []   # dashed bridge previews during a component drag
        self._wire_pin_anchors:  list = []   # [(comp, (lx,ly), wire, idx)] — wire ends on a pin
        self._wire_pin_preview_wires: list = []  # preview WireItems for bridge wires during drag

        self._border_pending:   tuple | None = None   # (width, height, show_in_export)
        self._library_pending:  tuple | None = None   # (file_path, directive, simulator, corner)
        self._image_pending:    tuple | None = None   # (file_path, width, height)
        self._latex_pending:    tuple | None = None   # (code, preamble, w, h)
        self._param_pending:    tuple | None = None   # (params, preamble)
        self._analysis_pending: tuple | None = None   # (source, detector, lgref)
        self._placing_text:     str | None   = None   # text for PLACING_TEXT mode
        self._placing_text_props: dict       = {}     # its own font and colour
        self._hyperlink_pending: tuple | None = None  # (url, label)
        self._model_pending:    tuple | None = None   # (name, type, sim, params, preamble)

        # shape drawing state
        self._draw_kind:   str | None       = None   # "line"|"rect"|"circle"
        self._draw_anchor: QPointF | None   = None   # first click (scene coords)
        self._draw_pts:    list             = []     # accumulated scene pts (polyline)
        self._draw_ghost:  object | None    = None   # preview ShapeItem

        self._paste_ghost_items: list = []   # [(kind, item, base)]
        self._paste_ref: QPointF | None = None
        self._exporting: bool = False

        self._undo_stack: list = []
        self._redo_stack: list = []
        self._library    = None   # set by from_data; used by _restore

        self._pre_drag_data      = None   # snapshot before vertex/component drag
        self._pre_drag_pos: dict = {}     # item positions at drag start
        # wire points at drag start, by wire id: the release pass maps OLD
        # anchor positions to new ones, and must read where a point WAS, not
        # where live rubber-banding has already put it (see
        # _reconnect_after_move).
        self._pre_drag_wire_pts: dict = {}
        self._vdrag_moved        = False  # True once a vertex was actually moved

        self._group_drag_active      = False   # suppresses itemChange rubber-banding
        self._comp_group_move_start: QPointF | None = None
        self._comp_group_move_snaps  = True    # False: a group of annotations only
        self._comp_group_move_items: list = []   # [(item, orig_QPointF)]
        self._wire_group_move_data:  list = []   # [(wire, [orig_QPointF, ...])]
        # Unselected wire points attached to the group at drag START, moved
        # from their originals on every step: [(wire, idx, orig_QPointF)].
        self._group_rb: list = []
        # Moving points of the group that sit on a component pin at press:
        # [(comp, local_xy, source)], source = ("wire", wire, idx) or
        # ("pin", comp, local_xy). A point that leaves its pin is bridged at
        # release; a dashed preview shows the bridge during the drag.
        self._group_pin_anchors: list = []
        self._group_pin_previews: list = []
        self._comp_group_move_moved  = False

    # ── copy / paste ──────────────────────────────────────────────────────────

    def hide_label(self, label) -> None:
        """Delete on a visible attribute label means HIDE (Anton, 2026-08-04):
        clear the component's display flags for that attribute and rebuild
        its labels. The attribute itself is untouched; the refdes label is
        hidden the same way (Show refdes off). Never removes the item."""
        comp = label.parentItem()
        if not isinstance(comp, ComponentItem) or label.scene() is None:
            return
        key = label.prop_key
        if key in comp.prop_display:
            comp.prop_display[key] = (False, False)
        label.setSelected(False)
        comp.update_labels()
        comp.update()

    def _copy_selection(self) -> None:
        from .component_item import ComponentItem
        # selectedItems() comes in hash order, which differs between runs;
        # the paste reference is the FIRST clipboard entry, so the order is
        # fixed here: top to bottom, left to right (wires by their first
        # point).  Without it the item that lands under the cursor on paste
        # was random (2026-09-25).
        def _key(item):
            pts = getattr(item, "points", None)
            pos = pts[0] if pts else item.pos()
            return (pos.y(), pos.x(), type(item).__name__)
        sel = sorted(self.selectedItems(), key=_key)
        if not sel:
            return
        from .symbol_editor import SymbolPinItem, SymbolTextItem, OpaqueSvgItem
        self._clipboard.clear()
        self._paste_count = 0
        for item in sel:
            if isinstance(item, ComponentItem):
                item._save_label_offsets()
                self._clipboard.append({
                    'kind':        'component',
                    'symbol_name': item.symbol_name,
                    'svg_bytes':   item._svg_bytes,
                    'x':           item.pos().x(),
                    'y':           item.pos().y(),
                    'rotation':    item.rotation(),
                    'h_flip':      item.h_flip,
                    'v_flip':      item.v_flip,
                    'params':      dict(item.params),
                    'model':       item.model,
                    'refs':        list(item.refs),
                    'prop_display': {k: tuple(v) for k, v in item.prop_display.items()},
                    'prop_offsets': {k: list(v) for k, v in item.prop_offsets.items()},
                })
            elif isinstance(item, WireItem):
                self._clipboard.append({
                    'kind':         'wire',
                    'points':       [(p.x(), p.y()) for p in item.points],
                    'net_name':     item.net_name,
                    'display_name': item.display_name,
                    'label_offset': (item.label_offset.x(), item.label_offset.y()),
                })
            elif isinstance(item, CommandItem):
                self._clipboard.append({
                    'kind': 'command',
                    'x':    item.pos().x(),
                    'y':    item.pos().y(),
                    'text': item.toPlainText(),
                })
            elif isinstance(item, FreeTextItem):
                self._clipboard.append({
                    'kind': 'free_text',
                    'x':    item.pos().x(),
                    'y':    item.pos().y(),
                    'text': item.toPlainText(),
                    'props': dict(font_family=item.font_family, font_size=item.font_size,
                                  bold=item.bold, italic=item.italic, color=item.color),
                    'z': item.zValue(),
                })
            elif isinstance(item, AnalysisItem):
                self._clipboard.append({
                    'kind':     'analysis',
                    'x':        item.pos().x(),
                    'y':        item.pos().y(),
                    'source':   list(item.source),
                    'detector': [list(d) for d in item.detector],
                    'lgref':    list(item.lgref),
                })
            elif isinstance(item, HyperlinkItem):
                self._clipboard.append({
                    'kind':  'hyperlink',
                    'x':     item.pos().x(),
                    'y':     item.pos().y(),
                    'url':   item.url,
                    'label': item.label,
                    'z':     item.zValue(),
                })
            # Model definitions and parameter tables copy as they are, the
            # model under the SAME name (Anton, 2026-09-20: renaming is the
            # first edit after pasting; a duplicate .model line exists only
            # until then).
            elif isinstance(item, ModelItem):
                self._clipboard.append({
                    'kind':       'model',
                    'x':          item.pos().x(),
                    'y':          item.pos().y(),
                    'model_name': item.model_name,
                    'model_type': item.model_type,
                    'simulator':  item.simulator,
                    'params':     [tuple(p) for p in item.params],
                    'preamble':   item.preamble_path,
                    'show':       item.show_on_schematic,
                })
            elif isinstance(item, ParameterItem):
                self._clipboard.append({
                    'kind':     'parameters',
                    'x':        item.pos().x(),
                    'y':        item.pos().y(),
                    'params':   [tuple(p) for p in item.params],
                    'preamble': item.preamble_path,
                    'show':     item.show_on_schematic,
                })
            # Shapes, LaTeX labels, images and the symbol editor's items copy
            # through their data records (Anton, 2026-09-27: Ctrl+C/V did
            # nothing on a pin).
            elif isinstance(item, ShapeItem):
                self._clipboard.append({'kind': 'shape', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'record': _shape_record(item)})
            elif isinstance(item, LatexFragmentItem):
                self._clipboard.append({'kind': 'latex', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'latex_code': item.latex_code, 'preamble': item.preamble_path,
                                        'w': item.display_width, 'h': item.display_height,
                                        'color': item.color, 'snippet': item.snippet,
                                        'z': item.zValue()})
            elif isinstance(item, ImageItem):
                self._clipboard.append({'kind': 'image', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'file_path': item.file_path, 'link': item.link,
                                        'z': item.zValue(), 'scale': item.size_scale,
                                        'w': item.display_width, 'h': item.display_height})
            elif isinstance(item, SymbolPinItem):
                self._clipboard.append({'kind': 'pin', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'name': item.name})
            elif isinstance(item, SymbolTextItem):
                self._clipboard.append({'kind': 'symbol_text', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'content': item.content, 'size': item.size})
            elif isinstance(item, OpaqueSvgItem):
                self._clipboard.append({'kind': 'opaque', 'x': item.pos().x(), 'y': item.pos().y(),
                                        'xml': item.xml})

    @property
    def _clipboard(self) -> list:
        return _SHARED_CLIPBOARD

    def _pasteable(self) -> list:
        """The clipboard entries this scene can take: a symbol drawing takes
        no components or wires, a schematic takes no pins or symbol texts;
        shapes, texts, LaTeX labels and images go anywhere."""
        symbol_mode = bool(self.show_origin)
        banned = _SCHEMATIC_ONLY_KINDS if symbol_mode else _SYMBOL_ONLY_KINDS
        return [d for d in self._clipboard if d['kind'] not in banned]

    def _paste_clipboard(self) -> None:
        if not self._pasteable():
            return
        self._start_paste_ghost()

    def _start_paste_ghost(self) -> None:
        """Enter paste-ghost mode: clipboard items follow the cursor, click to place."""
        from PySide6.QtWidgets import QGraphicsSimpleTextItem as _ST
        entries = self._pasteable()
        if not entries:
            return
        self._end_wire(commit=False)
        self._cancel_placement()   # clears any prior ghost / mode
        # The copied originals stay selected after Copy. R and M act on
        # the selection when no single ghost is being placed, so R during
        # a paste rotated the ORIGINALS (a user's report on 6.1.0,
        # 2026-10-09). The paste is the new selection: the pasted items
        # are selected when placed, and R then turns those.
        self.clearSelection()

        # Reference point: first component's position (always on-grid).
        # Using a component origin guarantees delta = snapped_cursor - ref
        # is a multiple of GRID_SIZE, so all pasted components land on-grid.
        ref = None
        for data in entries:
            if data['kind'] == 'component':
                ref = QPointF(data['x'], data['y'])
                break
        if ref is None:
            # Clipboard has no components; fall back to first item position.
            for data in entries:
                if 'x' in data and 'y' in data:
                    ref = QPointF(data['x'], data['y'])
                    break
                if data['kind'] == 'wire' and data['points']:
                    x, y = data['points'][0]
                    ref = QPointF(x, y)
                    break
        if ref is None:
            return
        self._paste_ref = ref

        for data in entries:
            kind = data['kind']
            if kind == 'component':
                ghost = make_ghost(data['svg_bytes'], _config.display_style(self.style))
                ghost.setTransform(QTransform().scale(
                    -1 if data['h_flip'] else 1,
                    -1 if data['v_flip'] else 1,
                ))
                ghost.setRotation(data['rotation'])
                ghost.setPos(QPointF(data['x'], data['y']))
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, QPointF(data['x'], data['y'])))
            elif kind == 'wire':
                pts = [QPointF(x, y) for x, y in data['points']]
                ghost = QGraphicsPathItem(_build_path(pts))
                ghost.setPen(QPen(Qt.black, 1.2))
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                self.addItem(ghost)
                self._paste_ghost_items.append(('wire', ghost, pts))
            elif kind in ('command', 'free_text'):
                ghost = _ST(data['text'][:30])
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                ghost.setPos(QPointF(data['x'], data['y']))
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, QPointF(data['x'], data['y'])))
            elif kind == 'analysis':
                ghost = _ST(".source / .detector / .lgref")
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                ghost.setPos(QPointF(data['x'], data['y']))
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, QPointF(data['x'], data['y'])))
            elif kind == 'hyperlink':
                ghost = _ST((data['label'] or data['url'])[:30])
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                ghost.setPos(QPointF(data['x'], data['y']))
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, QPointF(data['x'], data['y'])))
            elif kind in ('model', 'parameters'):
                ghost = _ST(("%s %s" % (data['model_name'], data['model_type']))
                            if kind == 'model' else "parameters")
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                ghost.setPos(QPointF(data['x'], data['y']))
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, QPointF(data['x'], data['y'])))
            elif kind in ('shape', 'latex', 'image', 'pin', 'symbol_text', 'opaque'):
                from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem
                from .symbol_editor import OpaqueSvgItem
                base = QPointF(data['x'], data['y'])
                if kind == 'shape':
                    ghost = _shape_from_record(data['record'])
                elif kind in ('latex', 'image'):
                    ghost = QGraphicsRectItem(0, 0, data['w'], data['h'])
                    ghost.setPen(QPen(Qt.gray, 0.5, Qt.DashLine))
                elif kind == 'pin':
                    ghost = QGraphicsEllipseItem(-2, -2, 4, 4)
                    ghost.setBrush(QBrush(Qt.red)); ghost.setPen(QPen(Qt.NoPen))
                elif kind == 'symbol_text':
                    ghost = _ST(data['content'])
                else:
                    ghost = OpaqueSvgItem(data['xml'])
                ghost.setFlag(QGraphicsItem.ItemIsSelectable, False)
                ghost.setFlag(QGraphicsItem.ItemIsMovable, False)
                ghost.setOpacity(0.4)
                ghost.setAcceptedMouseButtons(Qt.NoButton)
                ghost.setPos(base)
                self.addItem(ghost)
                self._paste_ghost_items.append(('point', ghost, base))

        self._mode = _Mode.PASTING
        self.placing_started.emit()

    def _commit_paste(self, pos: QPointF) -> None:
        """Place clipboard items at pos and exit paste-ghost mode."""
        for _, item, _ in self._paste_ghost_items:
            if item.scene():
                self.removeItem(item)
        self._paste_ghost_items.clear()

        self._mode = _Mode.NORMAL
        self.placing_ended.emit()

        entries = self._pasteable()
        if not entries or self._paste_ref is None:
            self._paste_ref = None
            return

        delta = pos - self._paste_ref
        self._paste_ref = None

        self._push_undo()
        self.clearSelection()

        for data in entries:
            kind = data['kind']
            if kind == 'component':
                # Re-fetch the full symbol SVG from the library so embedded text
                # (stripped from item._svg_bytes) is restored on the copy, just as
                # file loading does.  Fall back to the stored artwork if absent.
                lib = getattr(self, '_library', None)
                sym = lib.symbol(data['symbol_name']) if lib is not None else None
                if sym is None:
                    continue   # symbol unknown to this schematic's library
                item = ComponentItem(sym, self._next_id(data['symbol_name']))
                item.setPos(QPointF(data['x'], data['y']) + delta)
                item.setRotation(data['rotation'])
                item.h_flip       = data['h_flip']
                item.v_flip       = data['v_flip']
                item.apply_transform()
                item.params       = dict(data['params'])
                item.model        = data['model']
                item.refs         = list(data['refs'])
                item.prop_display = {k: tuple(v) for k, v in data['prop_display'].items()}
                item.set_prop_offsets(data['prop_offsets'])   # moved labels stay moved
                item.update_labels()
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'wire':
                pts = [QPointF(x + delta.x(), y + delta.y()) for x, y in data['points']]
                wire = WireItem(pts)
                wire.net_name     = data['net_name']
                wire.display_name = data['display_name']
                wire.label_offset = QPointF(*data['label_offset'])
                self.addItem(wire)
                wire.update_label()
                wire.setSelected(True)
            elif kind == 'command':
                item = CommandItem(data['text'],
                                   QPointF(data['x'] + delta.x(), data['y'] + delta.y()))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'free_text':
                item = FreeTextItem(data['text'],
                                    QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                                    **data.get('props', {}))
                item.setZValue(data.get('z', 0.0))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'analysis':
                item = AnalysisItem(
                    data['source'], data['detector'], data['lgref'],
                    QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                )
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'hyperlink':
                item = HyperlinkItem(
                    data['url'], data['label'],
                    QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                )
                item.setZValue(data.get('z', 0.0))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'model':
                item = ModelItem(data['model_name'], data['model_type'],
                                 data['simulator'], list(data['params']),
                                 data['preamble'],
                                 QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                                 show=data['show'])
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'parameters':
                item = ParameterItem(list(data['params']), data['preamble'],
                                     QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                                     show=data['show'])
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'shape':
                item = _shape_from_record(data['record'], delta)
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'latex':
                item = LatexFragmentItem(data['latex_code'], data['preamble'], data['w'], data['h'],
                                         QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                                         color=data.get('color', ''),
                                         snippet=data.get('snippet', ''))
                item.setZValue(data.get('z', 0.0))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'image':
                item = ImageItem(data['file_path'], data['w'], data['h'],
                                 QPointF(data['x'] + delta.x(), data['y'] + delta.y()),
                                 link=data.get('link', ''), size_scale=data.get('scale'))
                item.setZValue(data.get('z', 0.0))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'pin':
                # A pin copy gets the next pin number; its name is kept when
                # free, otherwise the number is appended (b -> b3).
                from .symbol_editor import SymbolPinItem
                pins = [i for i in self.items() if isinstance(i, SymbolPinItem)]
                number = max((p.number for p in pins), default=0) + 1
                names = {p.name for p in pins}
                name = data['name'] if data['name'] not in names else f"{data['name']}{number}"
                item = SymbolPinItem(name, number, QPointF(data['x'] + delta.x(), data['y'] + delta.y()))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'symbol_text':
                from .symbol_editor import SymbolTextItem
                item = SymbolTextItem(data['content'], data['size'],
                                      QPointF(data['x'] + delta.x(), data['y'] + delta.y()))
                self.addItem(item)
                item.setSelected(True)
            elif kind == 'opaque':
                from .symbol_editor import OpaqueSvgItem
                item = OpaqueSvgItem(data['xml'], QPointF(data['x'] + delta.x(), data['y'] + delta.y()))
                self.addItem(item)
                item.setSelected(True)

        self._sync_junctions()
        self._remove_short_circuit_wires()
        self._sync_junctions()

    # ── placement ─────────────────────────────────────────────────────────────

    def start_item_placement(self, item) -> None:
        """A prepared item (a symbol pin, a symbol text) follows the cursor
        with its own snapping rule (config.snap_pos) and is placed with a
        click; Escape removes it (Anton, 2026-09-27: pins appeared at a
        fixed spot and had to be dragged from there)."""
        self._end_wire(commit=False)
        self._cancel_placement()
        item.setOpacity(0.5)
        item.setAcceptedMouseButtons(Qt.NoButton)
        item.setPos(QPointF(-9999, -9999))
        self._ghost = item
        self.addItem(item)
        self._mode = _Mode.PLACING_ITEM
        self.placing_started.emit()

    def rotate_ghost(self) -> bool:
        """R while a component is being placed: the ghost turns, and the
        component is placed as shown (a user found rotation possible only
        after placement, 2026-09-25). Returns False outside a placement."""
        if self._mode != _Mode.PLACING or self._ghost is None:
            return False
        self._ghost.setRotation(self._ghost.rotation() + 90)
        return True

    def mirror_ghost(self) -> bool:
        """M while a component is being placed: the ghost mirrors."""
        if self._mode != _Mode.PLACING or self._ghost is None:
            return False
        self._placing_hflip = not self._placing_hflip
        self._ghost.setTransform(QTransform().scale(-1 if self._placing_hflip else 1, 1))
        return True

    def start_placement(self, name: str, svg_bytes: bytes):
        self._end_wire(commit=False)
        self._cancel_placement()
        self._mode         = _Mode.PLACING
        self._placing_name = name
        self._placing_svg  = svg_bytes
        self._placing_hflip = False
        self._ghost        = make_ghost(svg_bytes, _config.display_style(self.style))
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self.placing_started.emit()

    def cancel_placement(self):
        """The user ends the current placement (Escape). Leaves the mode
        first, then reports the cancel with the symbol name of a component
        placement, so that a listener can offer that symbol again in a
        scene that is already back in normal mode."""
        name = self._placing_name if self._mode == _Mode.PLACING else None
        self._cancel_placement()
        self.placing_cancelled.emit(name or "")

    def _cancel_placement(self):
        if self._ghost is not None:
            self.removeItem(self._ghost)
            self._ghost = None
        for _, item, _ in self._paste_ghost_items:
            if item.scene():
                self.removeItem(item)
        self._paste_ghost_items.clear()
        self._paste_ref = None
        self._mode            = _Mode.NORMAL
        self._placing_name    = None
        self._placing_svg     = None
        self._border_pending    = None
        self._library_pending   = None
        self._image_pending     = None
        self._latex_pending     = None
        self._param_pending     = None
        self._analysis_pending  = None
        self._placing_text      = None
        self._placing_text_props = {}
        self._hyperlink_pending = None
        self._model_pending     = None
        # also cancel any in-progress shape draw
        if self._draw_ghost is not None and self._draw_ghost.scene():
            self.removeItem(self._draw_ghost)
        self._draw_ghost  = None
        self._draw_anchor = None
        self._draw_pts    = []
        self._draw_kind   = None
        self.placing_ended.emit()

    def _next_id(self, symbol_name: str) -> str:
        # Number per-PREFIX (not per-symbol): symbols that share a refdes prefix
        # — every subcircuit block uses 'X', and e.g. nmos/pmos both use 'M' —
        # must draw from one counter so their refdes never collide.  from_data
        # seeds these counters with the same key (keep them in sync).
        sym = self._library.symbol(symbol_name) if getattr(self, '_library', None) else None
        prefix = (sym.prefix if sym and sym.prefix else "X")
        n = self._counters.get(prefix, 1)
        self._counters[prefix] = n + 1
        return f"{prefix}{n}"

    def _render_ghost_latex(self, latex_code: str, preamble_path: str) -> "bytes | None":
        """Render LaTeX for a placement ghost, honouring this schematic's
        latex_rendering preference (None → pixmap placeholder)."""
        from .latex_label import LATEX_INSTALLED
        if not (LATEX_INSTALLED and self.style.LATEX_RENDERING_ENABLED):
            return None
        from .latex_label import render_latex_raw
        svg_bytes, _ = render_latex_raw(latex_code, preamble_path,
                                        cache_dir=self.cache_dir)
        return svg_bytes

    def _ghost_pixmap(self, svg_bytes) -> QPixmap:
        """Placement-ghost pixmap at the DERIVED display size (natural SVG
        size × the schematic's table-scale preference) — the size the placed
        item will actually get."""
        from PySide6.QtGui import QPainter as _QPainter
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        from .parameter_item import svg_scene_size
        from .latex_label import display_svg
        renderer = QSvgRenderer(QByteArray(display_svg(svg_bytes))) if svg_bytes else None
        if renderer and renderer.isValid():
            natural = svg_scene_size(renderer, self.style)
            pct = self.style.SCALE_PARAMETER_TABLE / 100.0
            if natural is not None:
                w = max(1, round(natural[0] * pct))
                h = max(1, round(natural[1] * pct))
            else:
                w, h = 200, 80
            px = QPixmap(w, h)
            px.fill(Qt.transparent)
            p = _QPainter(px)
            renderer.render(p)
            p.end()
        else:
            px = QPixmap(200, 80)
            px.fill(QColor(200, 225, 255))
        return px

    # ── DC operating-point store (bias back-annotation) ───────────────────

    def load_op_raw(self, sch_path) -> bool:
        """Load the circuit's most recent UNSTEPPED operating-point results
        (cir/<stem>_op.raw, written by sl.op()) into the op store and
        refresh the bias annotations. Shared by the window (after a run)
        and the headless export (2026-09-21: the exported SVG carries the
        annotations). Stepped op runs write *_op_sN.raw and are excluded.
        Returns True when results were installed."""
        from pathlib import Path
        from . import project
        sch_path = Path(sch_path)
        raw = project.subdir_for(sch_path, "cir") / f"{sch_path.stem}_op.raw"
        if not raw.is_file():
            return False
        from .raw_file import RawFile
        try:
            analyses = RawFile.load(raw)
        except Exception:
            return False
        for a in analyses:
            if "operating point" not in a.name.lower():
                continue
            results = {}
            if getattr(a, "x_data", None) is not None and a.x_data.size == 1:
                results[a.x_name.lower()] = float(a.x_data[0].real)
            for k, v in a.signals.items():
                if v.size == 1:
                    results[k.lower()] = float(v[0].real)
            if not results:
                return False
            # The .cir the raw was produced from names the nets.
            cir = raw.with_name(f"{sch_path.stem}.cir")
            try:
                netlist_text = cir.read_text(encoding="utf-8", errors="replace")
            except OSError:
                netlist_text = None
            self.set_op_results(results, netlist_text)
            return True
        return False

    def set_op_results(self, results: "dict | None",
                       netlist_text: "str | None" = None) -> None:
        """Install fresh op results (panel calls this after a run).
        *netlist_text* is the .cir the raw was produced from.
        An OWN run supersedes any context borrowed via descend."""
        self.op_results = results
        self.op_netlist = netlist_text
        self.op_prefix = None
        self.op_port_nets = {}
        self.op_stale = False
        self._op_fingerprint = self._netlist_fingerprint()
        self.refresh_bias_annotations()

    def adopt_op_context(self, results: "dict | None", lib_netlist: "str | None",
                         prefix: "str | None", port_nets: "dict | None") -> None:
        """Borrow a PARENT run's op results for one instance of this
        subcircuit (set on descend; see the attribute comment in __init__).

        *lib_netlist* is this subcircuit's own ``.lib`` text — the naming
        authority for the internal nets, exactly as ``op_netlist`` is for a
        top-level schematic (its element lines carry the node names the raw
        dot-prefixes).  A COPY of *results* is stored, so the borrowed values
        survive the parent panel being closed."""
        self.op_results = dict(results) if results else None
        self.op_netlist = lib_netlist
        self.op_prefix = (prefix or None) if results else None
        self.op_port_nets = dict(port_nets or {}) if results else {}
        self.op_stale = False
        self._op_fingerprint = self._netlist_fingerprint()
        self.refresh_bias_annotations()

    def _netlist_fingerprint(self) -> str:
        """Hash of the NETLIST-RELEVANT scene state.  Cosmetic changes
        (annotation check-boxes, label positions, text/graphic items) do
        not change it — only edits that would change the generated netlist
        mark the op values stale (and undoing them un-marks)."""
        import hashlib
        import json
        d = self.to_data()
        core = {
            "components": sorted(
                (c.symbol_name, c.instance_id, c.model,
                 sorted(c.params.items()), list(c.refs),
                 c.x, c.y, c.rotation, c.h_flip, c.v_flip)
                for c in d.components),
            "wires": sorted(
                (tuple(map(tuple, w.points)), w.net_name or "")
                for w in d.wires),
            "commands": sorted(c.text for c in d.commands),
            "analysis": sorted(
                (tuple(a.source), tuple(map(tuple, a.detector)),
                 tuple(a.lgref)) for a in d.analysis_items),
            "libs": sorted(tuple((e.get("directive", ""), e.get("file", ""),
                                  e.get("corner", "")) for e in l.entries)
                           for l in d.libs),
            "params": sorted(tuple(map(tuple, p.params))
                             for p in d.parameters),
            "models": sorted(
                (m.model_name, m.model_type, tuple(map(tuple, m.params)))
                for m in d.model_defs),
        }
        return hashlib.sha1(
            json.dumps(core, default=str, sort_keys=True).encode()
        ).hexdigest()

    def _mark_op_stale(self) -> None:
        if self.op_results is not None:
            self.op_stale = (self._netlist_fingerprint()
                             != self._op_fingerprint)
        # Refresh unconditionally: derived net names (and thus the labels
        # of unnamed nets) can shift with any topology edit.
        self.refresh_bias_annotations()

    def refresh_bias_annotations(self) -> None:
        # Effective nets come FROM THE NETLIST the op raw was produced
        # with (scene.op_netlist — round 3, Anton 2026-07-12: the sims run
        # cir/<stem>.cir exactly as last exported, so no live resolver can
        # be trusted to reproduce its numbers; the file is the naming
        # authority). Fallback when no netlist is known yet: the builder's
        # own resolver. The map also feeds the NET-NAME labels of unnamed
        # nets ("Display net name" without a user label shows the derived
        # name — Anton, 2026-07-12).
        from .connectivity import nets_from_netlist, resolve_nets, _rpt
        comps = [i for i in self.items() if isinstance(i, ComponentItem)]
        wires = [i for i in self.items() if isinstance(i, WireItem)]
        if any(w.show_dc_voltage or (w.display_name and not w.net_name)
               for w in wires):
            net_map = (nets_from_netlist(comps, wires, self.op_netlist)
                       if self.op_netlist else resolve_nets(comps, wires))
        else:
            net_map = {}
        for wire in wires:
            wire.update_dc_label(net_map.get(_rpt(wire.points[0]))
                                 if wire.points else None)
            wire.update_label()
        for comp in comps:
            if comp.prop_display.get("dc_current", (False, False))[0]:
                comp.update_labels()

    def dc_voltage(self, net_name) -> "float | None":
        """v(<net>) from the op results, or None when unavailable.

        With a borrowed subcircuit context (op_prefix), an internal net is
        dot-prefixed the way the raw names it (``v(x1.<net>)``); a PORT net
        maps to the parent net it connects to (op_port_nets)."""
        if not self.op_results or not net_name:
            return None
        net = str(net_name).lower()
        r = self.op_results
        if self.op_prefix:
            mapped = self.op_port_nets.get(net)
            net = mapped if mapped is not None else f"{self.op_prefix}.{net}"
        return r.get(f"v({net})", r.get(net))

    def dc_current(self, refdes) -> "float | None":
        """i(<refdes>) from the op results (NGspice sign convention:
        measured INTO the + terminal), or None when unavailable.

        With a borrowed subcircuit context, NGspice names the branch vector
        of a device inside an instance ``<type>.<path>.<refdes>#branch``
        (e.g. ``v.x1.v1#branch``) — the type letter is repeated in front of
        the dotted path."""
        if not self.op_results or not refdes:
            return None
        ref = str(refdes).lower()
        r = self.op_results
        if self.op_prefix:
            path = f"{ref[:1]}.{self.op_prefix}.{ref}"
            return r.get(f"i({path})", r.get(f"{path}#branch"))
        return r.get(f"i({ref})", r.get(f"{ref}#branch"))

    def start_junction_placement(self):
        self._end_wire(commit=False)
        self._cancel_placement()
        r = self.style.JUNCTION_RADIUS
        ghost = QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
        ghost.setPen(QPen(Qt.NoPen))
        ghost.setBrush(QBrush(self.style.JUNCTION_COLOR))
        ghost.setOpacity(0.4)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_JUNCTION
        self.placing_started.emit()

    def link_choices(self, kind: str) -> list:
        """What a link of *kind* can show, as (key, "img/<stem>.svg"): the
        figures of the Design data by name; the schematics of the project
        (sch/ and lib/) by source path; the posters of the project by name,
        except this one and any poster that already shows this one,
        directly or through a chain (a poster may not contain itself)."""
        from . import project
        root = project.project_root()
        if kind == "figure":
            from .design_data import manifest_figures
            return manifest_figures(root)
        out = []
        img = project.folder_rel("img", root)
        if kind == "schematic":
            for p in project.project_schematics(root):
                out.append((project.schematic_ref(p, root), img + "/" + p.stem + ".svg"))
        elif kind == "poster":
            from .provenance import poster_contains
            me = getattr(self, "file_path", None)
            folder = project.folder("posters", root)
            for p in sorted(folder.glob("*" + project.POSTER_SUFFIX)) if folder.is_dir() else []:
                if me is not None and poster_contains(p, me):
                    continue                     # itself, or one that shows it
                out.append((p.stem, img + "/" + p.stem + ".svg"))
        return out

    def properties_block(self):
        """THE document-properties block of the drawing, or None."""
        return next((i for i in self.items()
                     if isinstance(i, FreeTextItem) and i.is_properties), None)

    def refresh_properties_text(self, props) -> None:
        """Re-render the properties block from *props* (after the
        properties dialog, at save)."""
        self.document_properties = props
        block = self.properties_block()
        if block is not None:
            block.render(props)

    def link_source(self, link: str):
        """The source file of a schematic or poster link, or None."""
        from . import project
        return project.link_source(link)

    # ── stacking order of annotations ───────────────────────────────────────
    # Shapes, images, LaTeX fragments, text and hyperlinks keep a z value of
    # their own, saved with them; the circuit layers (border -10, wires 0,
    # components 10, junctions 20, net labels 30) are fixed. An annotation
    # may go above the circuit: a figure over a component, overlapping
    # schematics on a poster (Anton, 2026-10-06). Keeping annotations
    # below the components was considered and REJECTED for that reason.

    ANNOTATION_TYPES = ("ShapeItem", "ImageItem", "LatexFragmentItem",
                        "FreeTextItem", "HyperlinkItem")

    def _is_annotation(self, item) -> bool:
        return type(item).__name__ in self.ANNOTATION_TYPES

    def settle_stacking(self) -> None:
        """Make the stacking order of the annotations explicit: annotations
        with EQUAL z values are drawn in the order they were added, which
        no file records (a reload adds texts before images), so a reopened
        drawing and its export showed another order than the canvas they
        were saved from (Anton, 2026-10-10: "What You See Is What You
        Get"). Each run of equal values gets small steps in the order it is
        drawn now, below the next distinct value, so that the saved z alone
        reproduces the canvas. The circuit layers are fixed and untouched."""
        from .border_item import BorderItem
        top = [i for i in self.items() if i.parentItem() is None
               and not isinstance(i, BorderItem)]
        drawn = list(reversed(top))                       # bottom to top
        values = sorted({i.zValue() for i in drawn})
        anns = [i for i in drawn if self._is_annotation(i)]
        k = 0
        while k < len(anns):
            z = anns[k].zValue()
            run = [anns[k]]
            while k + len(run) < len(anns) and anns[k + len(run)].zValue() == z:
                run.append(anns[k + len(run)])
            if len(run) > 1:
                higher = [v for v in values if v > z]
                gap = (higher[0] - z) if higher else 1.0
                step = min(1e-3, gap / (len(run) + 1))
                for n, item in enumerate(run):
                    item.setZValue(z + n * step)
            k += len(run)

    def restack(self, how: str) -> int:
        """Move the selected annotations in the stacking order: 'front'
        above everything, 'back' just above the border, 'forward' past the
        next item above, 'backward' past the next item below. Returns the
        count moved."""
        from .border_item import BorderItem
        from .config import Z_BORDER
        sel = [i for i in self.selectedItems() if self._is_annotation(i)]
        if not sel:
            return 0
        others = [i for i in self.items()
                  if i not in sel and not isinstance(i, BorderItem)
                  and i.parentItem() is None]
        zs = sorted({i.zValue() for i in others})
        self._push_undo()
        for item in sel:
            z = item.zValue()
            if how == "front":
                new = (max(zs) if zs else z) + 1.0
            elif how == "back":
                new = (min(zs) if zs else z) - 1.0
            elif how == "forward":
                above = [v for v in zs if v > z]
                new = (above[0] + 0.5) if above else z + 1.0
            elif how == "backward":
                below = [v for v in zs if v < z]
                new = (below[-1] - 0.5) if below else z - 1.0
            else:
                raise ValueError(how)
            item.setZValue(max(new, Z_BORDER + 1.0))     # never under the border
        self.data_changed.emit()
        return len(sel)

    def reload_links(self) -> int:
        """Reload every link that changed after a run of the instruction
        file: images whose file changed on disk, Figure items whose image in
        the Design data is another file, and LaTeX snippet items whose text
        in the Design data changed; the count reloaded."""
        n = 0
        for item in self.items():
            if isinstance(item, (ImageItem, LatexFragmentItem)) and item.reload_if_changed():
                n += 1
            elif isinstance(item, ShapeItem) and item.kind == "func" and item.trace_var:
                before = item.data
                item.resample()
                if item.data != before:
                    n += 1
        return n

    def start_text_placement(self, text: str = "Text", props: dict | None = None,
                             template: str = ""):
        """*props*: the item's own font and colour (TextDialog.properties()).
        *template*: the text is the rendered document-properties block."""
        from PySide6.QtGui import QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        self._placing_text = text
        self._placing_text_props = dict(props or {})
        self._placing_text_template = template or ""
        first_line = (text.split('\n')[0] or "Text")[:50]
        ghost = QGraphicsSimpleTextItem(first_line)
        probe = FreeTextItem(first_line, **self._placing_text_props)
        ghost.setFont(probe.effective_font(self.style))
        ghost.setBrush(QBrush(probe.defaultTextColor()))
        ghost.setOpacity(0.4)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_TEXT
        self.placing_started.emit()

    def start_hyperlink_placement(self, url: str, label: str):
        from PySide6.QtGui import QFont, QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        self._hyperlink_pending = (url, label)
        display = label or url or "hyperlink"
        ghost = QGraphicsSimpleTextItem(display[:50])
        font = QFont(_config.resolve_family(self.style.HYPERLINK_FONT_FAMILY), self.style.HYPERLINK_FONT_SIZE)
        font.setUnderline(self.style.HYPERLINK_UNDERLINE)
        ghost.setFont(font)
        ghost.setBrush(QBrush(self.style.HYPERLINK_COLOR))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_HYPERLINK
        self.placing_started.emit()

    def start_command_placement(self):
        self._end_wire(commit=False)
        self._cancel_placement()
        ghost = QGraphicsSimpleTextItem(".command")
        ghost.setOpacity(0.4)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_COMMAND
        self.placing_started.emit()

    def start_border_placement(self, props: dict):
        """props = BorderItem kwargs minus x/y (border_properties() of the
        dialog): width, height, show_in_export, fixed_w/h, line/bg style."""
        self._end_wire(commit=False)
        self._cancel_placement()
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QPen, QBrush, QColor
        ghost = QGraphicsRectItem(0, 0, props["width"], props["height"])
        ghost.setPen(QPen(QColor(props.get("line_color", "#5050b4")),
                          props.get("line_width", 0.8), Qt.DashLine))
        ghost.setBrush(QBrush(Qt.NoBrush))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._border_pending = dict(props)
        self._mode = _Mode.PLACING_BORDER
        self.placing_started.emit()

    def library_block(self):
        """The single library block on this schematic, or None."""
        for it in self.items():
            if isinstance(it, LibraryItem):
                return it
        return None

    def apply_library_block(self, entries, show: bool = True, pos=None) -> None:
        """Create/update THE library block from a list of entry dicts (the
        caller pushes undo).  Empty entries remove the block."""
        block = self.library_block()
        if not entries:
            if block is not None:
                self.removeItem(block)
            return
        entries = [dict(e) for e in entries]
        if block is None:
            self.addItem(LibraryItem(entries, pos or QPointF(0, 0), show=show))
        else:
            block.entries = entries
            block.set_show(show)
            block.update_text()

    def start_image_placement(self, file_path: str, width: float, height: float,
                              link: str = "", size_scale: float | None = None):
        from pathlib import Path as _Path
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPainter as _QPainter
        self._end_wire(commit=False)
        self._cancel_placement()
        w, h = max(1, round(width)), max(1, round(height))   # ghost pixmap only
        ext = _Path(file_path).suffix.lower()
        if ext == ".svg":
            from PySide6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(file_path)
            if renderer.isValid():
                px = QPixmap(w, h)
                px.fill(Qt.transparent)
                p = _QPainter(px)
                renderer.render(p)
                p.end()
            else:
                px = QPixmap(w, h)
                px.fill(Qt.lightGray)
        else:
            px = QPixmap(file_path)
            if not px.isNull():
                px = px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                px = QPixmap(w, h)
                px.fill(Qt.lightGray)
        ghost = QGraphicsPixmapItem(px)
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._image_pending = (file_path, width, height, link, size_scale)
        self._mode = _Mode.PLACING_IMAGE
        self.placing_started.emit()

    def start_latex_placement(self, latex_code: str, preamble_path: str,
                              width: int, height: int, color: str = "",
                              snippet: str = ""):
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPainter as _QPainter
        self._end_wire(commit=False)
        self._cancel_placement()
        svg_bytes = self._render_ghost_latex(latex_code, preamble_path)
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        from .latex_label import display_svg, recolor_svg
        from .config import display_color
        if svg_bytes and color:
            svg_bytes = recolor_svg(svg_bytes, display_color(color).name())
        renderer = QSvgRenderer(QByteArray(display_svg(svg_bytes))) if svg_bytes else None
        w, h = max(1, width), max(1, height)
        if renderer and renderer.isValid():
            px = QPixmap(w, h)
            px.fill(Qt.transparent)
            p = _QPainter(px)
            renderer.render(p)
            p.end()
        else:
            px = QPixmap(w, h)
            px.fill(QColor(240, 240, 180))
        ghost = QGraphicsPixmapItem(px)
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._latex_pending = (latex_code, preamble_path, width, height, color, snippet)
        self._mode = _Mode.PLACING_LATEX
        self.placing_started.emit()

    def start_parameter_placement(self, params: list, preamble_path: str):
        from PySide6.QtWidgets import QGraphicsPixmapItem
        self._end_wire(commit=False)
        self._cancel_placement()
        from .parameter_item import ParameterItem as _PI
        svg_bytes = self._render_ghost_latex(_PI.build_latex(params), preamble_path)
        ghost = QGraphicsPixmapItem(self._ghost_pixmap(svg_bytes))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._param_pending = (params, preamble_path)
        self._mode = _Mode.PLACING_PARAMETER
        self.placing_started.emit()

    def start_analysis_placement(self, source: list, detector: list, lgref: list):
        from PySide6.QtWidgets import QGraphicsSimpleTextItem
        from PySide6.QtGui import QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        ghost = QGraphicsSimpleTextItem(".source / .detector / .lgref")
        ghost.setFont(self.style.COMMAND_FONT)
        ghost.setBrush(QBrush(self.style.COMMAND_COLOR))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._analysis_pending = (source, detector, lgref)
        self._mode = _Mode.PLACING_ANALYSIS
        self.placing_started.emit()

    def start_model_placement(self, model_name: str, model_type: str,
                               simulator: str, params: list,
                               preamble_path: str = ""):
        self._end_wire(commit=False)
        self._cancel_placement()
        from .model_item import ModelItem as _MI
        svg_bytes = self._render_ghost_latex(
            _MI.build_latex(model_name, model_type, params), preamble_path)
        if svg_bytes:
            from PySide6.QtWidgets import QGraphicsPixmapItem
            ghost = QGraphicsPixmapItem(self._ghost_pixmap(svg_bytes))
        else:
            from PySide6.QtWidgets import QGraphicsSimpleTextItem
            from PySide6.QtGui import QBrush
            ghost = QGraphicsSimpleTextItem(f".model {model_name} {model_type}")
            ghost.setFont(self.style.COMMAND_FONT)
            ghost.setBrush(QBrush(self.style.COMMAND_COLOR))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._model_pending = (model_name, model_type, simulator, params,
                               preamble_path)
        self._mode = _Mode.PLACING_MODEL
        self.placing_started.emit()

    # ── shape drawing ─────────────────────────────────────────────────────────

    def start_drawing(self, kind: str, template=None) -> None:
        """Enter drawing mode for the given shape kind. *template*: a shape
        item (not in the scene) whose properties the drawn shape takes; a
        function curve is defined in its dialog FIRST and then given its
        box with two clicks (Anton, 2026-10-06)."""
        self._end_wire(commit=False)
        self._cancel_placement()
        self._cancel_draw()
        self._draw_kind = kind
        self._draw_template = template
        mode_map = {
            "line":    _Mode.DRAWING_LINE,
            "rect":    _Mode.DRAWING_RECT,
            "ellipse": _Mode.DRAWING_ELLIPSE,
            "circle":  _Mode.DRAWING_ELLIPSE,    # legacy name
            "polygon": _Mode.DRAWING_POLYGON,
            "arc":     _Mode.DRAWING_ELLIPSE,    # two corners, as an ellipse
            "func":    _Mode.DRAWING_RECT,       # two corners: the box
            "curve":   _Mode.DRAWING_POLYGON,    # clicked points
        }
        self._mode = mode_map[kind]
        self.placing_started.emit()   # reuse signal: switches view to NoDrag

    def _cancel_draw(self) -> None:
        if self._draw_ghost is not None and self._draw_ghost.scene():
            self.removeItem(self._draw_ghost)
        self._draw_ghost  = None
        self._draw_anchor = None
        self._draw_pts    = []
        self._draw_kind   = None
        self._draw_template = None
        if self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_RECT,
                           _Mode.DRAWING_ELLIPSE, _Mode.DRAWING_POLYGON):
            self._mode = _Mode.NORMAL
            self.placing_ended.emit()

    def _update_draw_ghost(self, scene_pos: QPointF) -> None:
        from .shape_item import ShapeItem
        from . import config as cfg
        color = "#000000"
        lw    = self.default_line_width

        if self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_POLYGON):
            pts = self._draw_pts + [scene_pos]
            if len(pts) < 2:
                if self._draw_ghost and self._draw_ghost.scene():
                    self.removeItem(self._draw_ghost)
                    self._draw_ghost = None
                return
            anchor = pts[0]
            rel    = [QPointF(p.x() - anchor.x(), p.y() - anchor.y()) for p in pts]
            # a polygon preview with fewer than 3 points is its outline so far
            if self._draw_kind == "curve":
                kind_g = "curve"
            else:
                kind_g = "polygon" if (self._mode == _Mode.DRAWING_POLYGON and len(pts) >= 3) else "line"

        elif self._mode == _Mode.DRAWING_RECT:
            if self._draw_anchor is None:
                return
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
            kind_g = "rect"                      # a func box previews as its rect

        elif self._mode == _Mode.DRAWING_ELLIPSE:
            if self._draw_anchor is None:
                return
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
            kind_g = "arc" if self._draw_kind == "arc" else "ellipse"
        else:
            return

        if self._draw_ghost and self._draw_ghost.scene():
            self.removeItem(self._draw_ghost)
        ghost = ShapeItem(kind_g, rel, stroke_color=color, line_width=lw,
                          pos=anchor)
        ghost.setOpacity(0.45)
        ghost.setFlag(QGraphicsItem.ItemIsSelectable, False)
        ghost.setFlag(QGraphicsItem.ItemIsMovable, False)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._draw_ghost = ghost
        self.addItem(ghost)

    def _commit_shape(self, scene_pos: QPointF) -> None:
        """Finalise the current shape and add it to the scene."""
        kind = self._draw_kind

        if kind in ("line", "polygon", "curve"):
            pts    = self._draw_pts
            if kind == "polygon" and len(pts) < 3:
                self._cancel_draw()
                return
            if kind == "curve" and len(pts) < 2:
                self._cancel_draw()
                return
            anchor = pts[0]
            rel    = [QPointF(p.x() - anchor.x(), p.y() - anchor.y()) for p in pts]
        elif kind in ("rect", "ellipse", "circle", "arc", "func"):
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
        else:
            return

        self._push_undo()
        template = getattr(self, "_draw_template", None)
        if template is not None:
            # the properties were set in the dialog before the box was clicked
            item = _shape_from_record(_shape_record(template))
            item.rel_points = rel
            item.setPos(anchor)
            item.line_width = self.default_line_width if template.line_width is None else template.line_width
            item.apply_rotation()
            item.anchor_to_first_point()
            self.addItem(item)
            item.resample()
            self._cancel_draw()
            return                       # one box per command
        item = ShapeItem(kind, rel, pos=anchor, line_width=self.default_line_width)
        self.addItem(item)
        self._cancel_draw()
        if kind == "func":
            # a function curve is nothing without its source: the dialog
            # opens at once; cancelled, the box goes again
            if not self.edit_shape(item):
                self.removeItem(item)
                self._pop_undo_if_possible()
            return                       # one box per command
        self.start_drawing(kind)

    def edit_shape(self, item) -> bool:
        """The properties dialog of a shape; True when accepted and applied."""
        from .shape_dialog import ShapeDialog
        dlg = ShapeDialog(item, trace_choices=self._trace_choices())
        if not dlg.exec():
            return False
        self._apply_shape_dialog(item, dlg)
        return True

    def _pop_undo_if_possible(self) -> None:
        try:
            self._undo_stack.pop()
        except (AttributeError, IndexError):
            pass

    def _trace_choices(self) -> list:
        """The traces of the Design data for a function curve, as
        (trace_var, label) pairs."""
        from . import project
        from .design_data import manifest_traces
        try:
            return [(v, l) for v, l, _d in manifest_traces(project.project_root())]
        except Exception:
            return []

    def _apply_shape_dialog(self, item, dlg) -> None:
        item.stroke_color   = dlg.get_stroke_color()
        item.line_width     = dlg.get_line_width()
        item.line_style     = dlg.get_line_style()
        item.line_end_start = dlg.get_line_end_start()
        item.line_end_end   = dlg.get_line_end_end()
        item.fill_style     = dlg.get_fill_style()
        item.fill_color     = dlg.get_fill_color()
        item.head_width     = dlg.get_head_width()
        item.head_length    = dlg.get_head_length()
        item.rotation       = dlg.get_rotation()
        if item.kind == "arc":
            item.arc_start, item.arc_sweep = dlg.get_arc()
        if item.kind == "curve":
            item.closed = dlg.get_closed()
        if item.kind == "func":
            src = dlg.get_func()
            item.expression  = src["expression"]
            item.var         = src["var"]
            item.x_range     = src["x_range"]
            item.y_range     = src["y_range"]
            item.x_log       = src["x_log"]
            item.num         = src["num"]
            item.trace_var   = src["trace_var"]
            item.trace_label = src["trace_label"]
            item.resample()
        item.apply_rotation()
        item.update()

    # ── wiring ────────────────────────────────────────────────────────────────

    def start_wire_mode(self):
        self._cancel_placement()
        self._mode = _Mode.WIRING
        self._wire_points = []
        self.wire_mode_started.emit()

    def finish_wire(self):
        self._end_wire(commit=True)

    def cancel_wire(self):
        self._end_wire(commit=False)

    def toggle_elbow(self):
        self._wire_h_first = not self._wire_h_first
        self._refresh_preview(self._last_cursor)

    def _end_wire(self, *, commit: bool):
        if self._wire_preview is not None:
            self.removeItem(self._wire_preview)
            self._wire_preview = None
        committed = commit and len(self._wire_points) >= 2
        if committed:
            self._push_undo()
            self.addItem(WireItem(self._wire_points))
        self._wire_points = []
        if self._mode == _Mode.WIRING:
            self._mode = _Mode.NORMAL
            self.wire_mode_ended.emit()
        if committed:
            self._sync_junctions()
            self._remove_short_circuit_wires()
            self._sync_junctions()

    def _refresh_preview(self, cursor: QPointF | None):
        self._last_cursor = cursor
        if not self._wire_points or cursor is None:
            return
        pts = self._wire_points + _elbow(self._wire_points[-1], cursor, self._wire_h_first)[1:]
        path = _build_path(pts)
        if self._wire_preview is None:
            self._wire_preview = QGraphicsPathItem()
            self._wire_preview.setPen(_make_preview_pen())
            self.addItem(self._wire_preview)
        self._wire_preview.setPath(path)

    # ── data model ────────────────────────────────────────────────────────────

    def addItem(self, item) -> None:
        super().addItem(item)
        self._pinned.add(item)

    def removeItem(self, item) -> None:
        """Remove *item* from the scene now, free it on the next turn of the
        event loop (see _retired): it stops painting and receiving events
        at once, but Qt's event delivery in progress keeps a valid object."""
        super().removeItem(item)
        self._pinned.discard(item)
        if not self._retired:
            QTimer.singleShot(0, self._release_retired)
        self._retired.append(item)

    def _release_retired(self) -> None:
        self._retired.clear()

    def clear(self) -> None:
        super().clear()
        self._pinned.clear()

    def reset(self):
        """Clear scene and reset all state (for New / before Load)."""
        self._end_wire(commit=False)
        self._cancel_placement()
        self._vdrag_wire        = None
        self._vdrag_idx         = None
        self._vdrag_rb          = []
        self._vdrag_pin_anchor  = None
        self._vdrag_pin_preview = None
        self._wire_move_wires     = []
        self._wire_move_origins   = []
        self._wire_move_others    = []
        self._wire_move_start     = None
        self._wire_move_moved     = False
        self._wire_move_rb        = []
        self._wire_move_junctions = []
        self._pin_anchors         = []
        self._pin_preview_wires   = []
        self._wire_pin_preview_wires = []
        self._group_pin_anchors   = []
        self._group_pin_previews  = []
        self._border_pending    = None
        self._library_pending   = None
        self._image_pending     = None
        self._latex_pending     = None
        self._param_pending     = None
        self._analysis_pending  = None
        self.clear()
        self._counters = {}

    # ── undo / redo ───────────────────────────────────────────────────────────

    def _push_undo(self) -> None:
        """Snapshot current state as a new undo point."""
        self._push_snapshot(self.to_data())

    def _push_snapshot(self, data) -> None:
        """Push a pre-captured snapshot onto the undo stack."""
        if data is None:
            return
        self._undo_stack.append(data)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self.data_changed.emit()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self.to_data())
        self._restore(self._undo_stack.pop())

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self.to_data())
        self._restore(self._redo_stack.pop())

    def _restore(self, data) -> None:
        undo_save = self._undo_stack
        redo_save = self._redo_stack
        self.from_data(data, self._library)  # calls reset() which clears new empty lists
        self._undo_stack = undo_save
        self._redo_stack = redo_save

    def clear_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    # ── wire splitting ────────────────────────────────────────────────────────

    def _connect_wires_at(self, pos: QPointF) -> None:
        """Place > Junction: CONNECT the wires that pass through *pos*.

        Junction dots are derived from the wire topology (_sync_junctions),
        so a dot placed by hand at a crossing used to vanish at the next sync
        and connected nothing; a placement that changes nothing is useless
        (Anton, 2026-09-27). A placed junction therefore changes the
        topology: every wire whose interior passes through the point is
        split there, the wire ends meet, the connectivity joins them, and
        the dot follows from the ordinary rule and stays. On a single wire
        the two halves are collinear and merge again: no connection, no dot.
        In empty space nothing happens."""
        pk = _pt_key(pos)
        for wire in [i for i in self.items() if isinstance(i, WireItem)]:
            if _on_wire_interior(pk, wire):
                self._split_wire_at(wire, pk)
        self._sync_junctions()

    def _split_through_wires(self) -> None:
        """Split any wire that is crossed by a wire endpoint or component pin."""
        changed = True
        while changed:
            changed = False
            wires = [i for i in self.items() if isinstance(i, WireItem)]
            comps = [i for i in self.items() if isinstance(i, ComponentItem)]
            for wire in wires:
                pt = self._interior_tap(wire, wires, comps)
                if pt is not None:
                    self._split_wire_at(wire, pt)
                    changed = True
                    break  # restart after topology change

    def _interior_tap(self, wire, wires, comps):
        """Return the first interior tap position on wire, or None."""
        for other in wires:
            if other is wire:
                continue
            for ep in (other.points[0], other.points[-1]):
                pk = _pt_key(ep)
                if _on_wire_interior(pk, wire):
                    return pk
        for comp in comps:
            for pin_pt in comp.pin_scene_pos():
                pk = _pt_key(pin_pt)
                if _on_wire_interior(pk, wire):
                    return pk
        return None

    def _split_wire_at(self, wire, pt_key: tuple) -> None:
        """Split wire at an interior position, creating two sub-segments."""
        pt = QPointF(pt_key[0], pt_key[1])
        pts = wire.points
        # Check intermediate elbow vertices first
        for idx in range(1, len(pts) - 1):
            if _pt_key(pts[idx]) == pt_key:
                self._do_wire_split(wire, list(pts[:idx + 1]), list(pts[idx:]))
                return
        # Split a segment interior
        for i in range(len(pts) - 1):
            if _pt_on_segment(pt_key[0], pt_key[1], pts[i], pts[i + 1]):
                self._do_wire_split(wire,
                                    list(pts[:i + 1]) + [pt],
                                    [pt] + list(pts[i + 1:]))
                return

    def _do_wire_split(self, wire, pts1: list, pts2: list) -> None:
        net_name      = wire.net_name
        display_name  = wire.display_name
        net_locked    = wire.net_locked
        user_net_name = wire._user_net_name
        self.removeItem(wire)
        for i, pts in enumerate([pts1, pts2]):
            if len(pts) >= 2:
                w = WireItem(pts)
                w.net_name      = net_name
                w.display_name  = display_name if i == 0 else False
                w.net_locked    = net_locked
                w._user_net_name = user_net_name
                self.addItem(w)
                w.update_label()

    # ── post-drag reconnection ────────────────────────────────────────────────

    def _reconnect_after_move(self) -> None:
        """
        Rubber-band unselected wires after any drag completes (called on release).

        Builds a map of old anchor positions → new positions from:
          - Components that moved (via _pre_drag_pos)
          - Non-wire items moved inside a wire-body drag (_wire_move_others)
          - Selected wire endpoints that moved (_wire_group_move_data, _wire_move_wires)

        Any unselected wire point that sat on an old anchor position AT DRAG
        START (_pre_drag_wire_pts) is moved to the new position.  Reading the
        point's CURRENT position instead was tried and REVERTED (2026-09-25):
        live rubber-banding had already moved it to the new pin, and when that
        new position equalled another pin's OLD position it was moved a second
        time, e.g. a wire on the top pin of a resistor dragged down by its own
        length ended on the bottom pin.  Must be called before state variables
        are cleared.
        """
        from .component_item import ComponentItem
        from .wire_item import WireItem

        anchor_map: dict[tuple, QPointF] = {}

        # 1. Components moved via Qt default drag or group drag (_pre_drag_pos)
        for item in self.items():
            if not isinstance(item, ComponentItem):
                continue
            old_xy = self._pre_drag_pos.get(id(item))
            if old_xy is None:
                continue
            comp_delta = item.pos() - QPointF(*old_xy)
            if not (comp_delta.x() or comp_delta.y()):
                continue
            for lx, ly in item.pin_positions():
                new_pin = item.mapToScene(QPointF(lx, ly))
                old_pin = new_pin - comp_delta
                anchor_map[_pt_key(old_pin)] = new_pin

        # 2. Non-wire items moved as part of a wire-body drag (_wire_move_others)
        for other_item, ox, oy in self._wire_move_others:
            if not isinstance(other_item, ComponentItem) or other_item.scene() is None:
                continue
            comp_delta = other_item.pos() - QPointF(ox, oy)
            if not (comp_delta.x() or comp_delta.y()):
                continue
            for lx, ly in other_item.pin_positions():
                new_pin = other_item.mapToScene(QPointF(lx, ly))
                old_pin = new_pin - comp_delta
                anchor_map[_pt_key(old_pin)] = new_pin

        # 3. Selected wire endpoints that moved (group drag)
        moved_wire_ids: set[int] = {id(w) for w, _ in self._wire_group_move_data}
        for wire, orig_pts in self._wire_group_move_data:
            if wire.scene() is None:
                continue
            for j in (0, len(orig_pts) - 1):
                op = orig_pts[j]
                np_ = wire.points[j]
                k = _pt_key(op)
                if k not in anchor_map and _pt_key(op) != _pt_key(np_):
                    anchor_map[k] = QPointF(np_)

        # 4. Selected wire endpoints that moved (wire body drag)
        for wire, orig_pts in zip(self._wire_move_wires, self._wire_move_origins):
            if wire.scene() is None:
                continue
            moved_wire_ids.add(id(wire))
            for j in (0, len(orig_pts) - 1):
                op = orig_pts[j]
                np_ = wire.points[j]
                k = _pt_key(op)
                if k not in anchor_map and _pt_key(op) != _pt_key(np_):
                    anchor_map[k] = QPointF(np_)

        if not anchor_map:
            return

        # Stretch unselected wire points that SAT on an old anchor position.
        for wire in self.items():
            if not isinstance(wire, WireItem) or id(wire) in moved_wire_ids:
                continue
            orig = self._pre_drag_wire_pts.get(id(wire))
            if orig is None or len(orig) != len(wire.points):
                orig = wire.points          # created during the drag: as it is
            changed = False
            for i, pt in enumerate(wire.points):
                new_pt = anchor_map.get(_pt_key(orig[i]))
                if new_pt is not None and _pt_key(pt) != _pt_key(new_pt):
                    wire.points[i] = QPointF(new_pt)
                    changed = True
            if changed:
                wire._rebuild()

    def _group_moving_point(self, src) -> QPointF | None:
        """Current scene position of a moving point of the group drag:
        ("wire", wire, idx) a point of a selected wire, ("pin", comp,
        local_xy) a pin of a moving component. None once the item is gone."""
        kind, item, ref = src
        if item.scene() is None:
            return None
        if kind == "wire":
            return QPointF(item.points[ref]) if ref < len(item.points) else None
        return item.mapToScene(QPointF(*ref))

    def _record_pre_drag_wire_pts(self) -> None:
        """Remember every wire's points at drag start (for _reconnect_after_move)."""
        self._pre_drag_wire_pts = {
            id(w): [QPointF(p) for p in w.points]
            for w in self.items() if isinstance(w, WireItem)
        }

    # ── junction sync ─────────────────────────────────────────────────────────

    def _remove_short_circuit_wires(self) -> None:
        """Remove single wire segments that directly short two pins of the same component.

        Only a segment whose *both* endpoints land exactly on pins of the same
        component is removed.  This is the segment created when a component is
        placed or moved so that an existing wire passes directly between two of
        its pins; _split_through_wires() isolates that piece and this method
        cleans it up.

        Multi-hop paths (intentional connections such as a bulk–source tie
        routed with an elbow or through an intermediate node) are left intact.
        """
        changed = True
        while changed:
            changed = False
            comps = [i for i in self.items() if isinstance(i, ComponentItem)]
            pin_to_comp: dict[tuple, ComponentItem] = {}
            for comp in comps:
                for p in comp.pin_scene_pos():
                    pin_to_comp[_pt_key(p)] = comp

            for w in list(self.items()):
                if not isinstance(w, WireItem):
                    continue
                k0 = _pt_key(w.points[0])
                kn = _pt_key(w.points[-1])
                if k0 == kn:
                    continue        # zero-length wire, handled elsewhere
                c0 = pin_to_comp.get(k0)
                cn = pin_to_comp.get(kn)
                if c0 is not None and c0 is cn:
                    self.removeItem(w)
                    changed = True
                    break           # restart with a fresh scene snapshot

    def _merge_collinear_wires(self) -> None:
        """Remove duplicate wire segments and fuse collinear adjacent pairs.

        Phase 1 – duplicate removal: if two straight wire items share both
        endpoints, discard one.

        Phase 2 – collinear fusion: if exactly two wire-endpoints meet at a
        point with no component pin, and the two segments are collinear there
        (same axis, continuing in the same direction), merge them into one wire.
        Repeated until no more fusions are possible.
        """
        changed = True
        while changed:
            changed = False
            wires = [i for i in self.items() if isinstance(i, WireItem)]
            comps = [i for i in self.items() if isinstance(i, ComponentItem)]
            comp_pins: set[tuple] = {
                _pt_key(p) for c in comps for p in c.pin_scene_pos()
            }

            # ── Phase 1: remove exact duplicates (straight segments only) ─────
            canonical: dict[tuple, object] = {}
            for w in wires:
                if len(w.points) != 2:
                    continue
                k0 = _pt_key(w.points[0])
                kn = _pt_key(w.points[-1])
                key = (min(k0, kn), max(k0, kn))
                if key in canonical:
                    self.removeItem(w)
                    changed = True
                    break
                canonical[key] = w
            if changed:
                continue

            # ── Phase 2: fuse collinear adjacent pairs ────────────────────────
            ep_wires: dict[tuple, list] = {}
            for w in wires:
                for pt in (w.points[0], w.points[-1]):
                    k = _pt_key(pt)
                    ep_wires.setdefault(k, []).append(w)

            for k, ws in ep_wires.items():
                if len(ws) != 2:
                    continue
                if k in comp_pins:
                    continue

                w1, w2 = ws

                # Orient: w1 ends at k, w2 starts at k
                pts1 = (list(w1.points) if _pt_key(w1.points[-1]) == k
                        else list(reversed(w1.points)))
                pts2 = (list(w2.points) if _pt_key(w2.points[0]) == k
                        else list(reversed(w2.points)))

                if len(pts1) < 2 or len(pts2) < 2:
                    continue

                prev_pt = pts1[-2]
                next_pt = pts2[1]

                dx1 = k[0] - round(prev_pt.x())
                dy1 = k[1] - round(prev_pt.y())
                dx2 = round(next_pt.x()) - k[0]
                dy2 = round(next_pt.y()) - k[1]

                # Same axis, same direction of travel through k
                on_x = dx1 != 0 and dy1 == 0 and dx2 != 0 and dy2 == 0
                on_y = dx1 == 0 and dy1 != 0 and dx2 == 0 and dy2 != 0
                if not (on_x or on_y):
                    continue
                if on_x and (dx1 > 0) != (dx2 > 0):
                    continue
                if on_y and (dy1 > 0) != (dy2 > 0):
                    continue

                # k is a collinear midpoint — drop it
                merged_pts = pts1[:-1] + pts2[1:]
                if len(merged_pts) < 2:
                    continue

                src = (w1 if (w1.net_locked or (w1.net_name and not w2.net_name))
                       else w2)
                self.removeItem(w1)
                self.removeItem(w2)
                nw = WireItem(merged_pts)
                nw.net_name       = src.net_name
                nw._user_net_name = src._user_net_name
                nw.net_locked     = src.net_locked
                nw.display_name   = src.display_name
                nw.label_offset   = QPointF(src.label_offset)
                self.addItem(nw)
                nw.update_label()
                changed = True
                break

    def _split_wire_elbows(self) -> None:
        """Normalize multi-segment wires into individual straight 2-point segments.

        An elbowed wire with N vertices becomes N-1 separate WireItems.
        This ensures that a single click selects only one straight segment.
        Net annotation (user name, display flag, label offset) is inherited
        by the first segment; subsequent segments start with no annotation
        so the connectivity resolver can assign net names cleanly.
        """
        for wire in list(self.items()):
            if not isinstance(wire, WireItem):
                continue
            pts = wire.points
            if len(pts) <= 2:
                continue
            pts_copy       = [QPointF(p) for p in pts]
            net_name       = wire.net_name
            user_net       = wire._user_net_name
            net_locked     = wire.net_locked
            display_name   = wire.display_name
            label_offset   = QPointF(wire.label_offset)
            self.removeItem(wire)
            for i, (a, b) in enumerate(zip(pts_copy, pts_copy[1:])):
                nw = WireItem([a, b])
                if i == 0:
                    nw.net_name       = net_name
                    nw._user_net_name = user_net
                    nw.net_locked     = net_locked
                    nw.display_name   = display_name
                    nw.label_offset   = label_offset
                self.addItem(nw)
                nw.update_label()

    def _sync_junctions(self) -> None:
        """Split through-wires, normalize to segments, merge collinear pairs, add/remove junctions."""
        # Remove degenerate zero-length wires (created when two pins are brought together)
        for item in list(self.items()):
            if isinstance(item, WireItem):
                pts = item.points
                if len(pts) >= 2 and _pt_key(pts[0]) == _pt_key(pts[-1]):
                    self.removeItem(item)
        self._split_through_wires()
        self._split_wire_elbows()
        self._merge_collinear_wires()
        wires    = [i for i in self.items() if isinstance(i, WireItem)]
        comps    = [i for i in self.items() if isinstance(i, ComponentItem)]
        required = _find_junction_points(wires, comps)
        kept: set[tuple] = set()
        for item in list(self.items()):
            if not isinstance(item, JunctionItem):
                continue
            k = _pt_key(item.pos())
            if k in required:
                kept.add(k)
            else:
                self.removeItem(item)
        for k in required:
            if k not in kept:
                self.addItem(JunctionItem(QPointF(k[0], k[1])))
        self._sync_port_net_names()
        self._refresh_pin_markers(wires, comps)

    def _refresh_pin_markers(self, wires=None, comps=None) -> None:
        """Tell each component which of its pins are unconnected, so it can draw
        a marker there. A pin is connected when a wire touches it (endpoint or
        passing through) or another component pin sits on it."""
        if comps is None:
            comps = [i for i in self.items() if isinstance(i, ComponentItem)]
        if wires is None:
            wires = [i for i in self.items() if isinstance(i, WireItem)]

        pin_counts: dict[tuple, int] = {}
        for c in comps:
            for p in c.pin_scene_pos():
                k = _pt_key(p)
                pin_counts[k] = pin_counts.get(k, 0) + 1

        def on_any_wire(k: tuple) -> bool:
            for w in wires:
                pts = w.points
                for i in range(len(pts) - 1):
                    p1, p2 = pts[i], pts[i + 1]
                    if _pt_key(p1) == k or _pt_key(p2) == k:
                        return True
                    if _pt_on_segment(k[0], k[1], p1, p2):
                        return True
            return False

        for c in comps:
            unconnected = set()
            for idx, p in enumerate(c.pin_scene_pos()):
                k = _pt_key(p)
                connected = pin_counts.get(k, 0) >= 2 or on_any_wire(k)
                if not connected:
                    unconnected.add(idx)
            c.set_unconnected_pins(unconnected)

    def _sync_port_net_names(self) -> None:
        """Lock net names on wires that belong to a net containing a port symbol.

        Uses a union-find over the wire/pin graph (same logic as connectivity.py)
        to find which nets contain port symbols.  Wires on those nets have their
        net_name overridden with the port name; the original user-set name is
        preserved in _user_net_name so it can be restored if the port is removed.
        """
        from .connectivity import _UF, _rpt, _on_segment

        comps = [i for i in self.items() if isinstance(i, ComponentItem)]
        wires = [i for i in self.items() if isinstance(i, WireItem)]

        uf = _UF()

        # Union consecutive points on each wire
        for wire in wires:
            pts = [_rpt(p) for p in wire.points]
            for i in range(len(pts) - 1):
                uf.union(pts[i], pts[i + 1])

        # Collect all candidate points and ensure they exist in the UF
        all_pts: list[tuple] = []
        for wire in wires:
            all_pts.extend(_rpt(p) for p in wire.points)
        for comp in comps:
            for lx, ly in comp.pin_positions():
                all_pts.append(_rpt(comp.mapToScene(QPointF(lx, ly))))
        for pt in all_pts:
            uf.find(pt)

        # T-junction detection: wire endpoint on segment interior → same net
        for wire in wires:
            for i in range(len(wire.points) - 1):
                p1, p2 = wire.points[i], wire.points[i + 1]
                seg_key = _rpt(p1)
                for pt in all_pts:
                    if _on_segment(p1, p2, QPointF(pt[0], pt[1])):
                        uf.union(pt, seg_key)

        # Pin-to-pin contacts: two components with pins at the same position
        seen: dict[tuple, tuple] = {}
        for comp in comps:
            for lx, ly in comp.pin_positions():
                pk = _rpt(comp.mapToScene(QPointF(lx, ly)))
                if pk in seen:
                    uf.union(pk, seen[pk])
                else:
                    seen[pk] = pk

        # Same-named ports are on the same net regardless of physical position
        port_first: dict[str, tuple] = {}
        for comp in comps:
            if comp.symbol_name == "port":
                name = comp.params.get("name", "").strip()
                if name:
                    root = uf.find(_rpt(comp.mapToScene(QPointF(0.0, 0.0))))
                    if name in port_first:
                        uf.union(root, port_first[name])
                    else:
                        port_first[name] = root

        # Build root → port_name (last port on net wins — conflict is a schematic error)
        root_to_port: dict[tuple, str] = {}
        for comp in comps:
            if comp.symbol_name == "port":
                name = comp.params.get("name", "").strip()
                if name:
                    root = uf.find(_rpt(comp.mapToScene(QPointF(0.0, 0.0))))
                    root_to_port[root] = name

        # Lock or unlock each wire
        for wire in wires:
            if not wire.points:
                continue
            root = uf.find(_rpt(wire.points[0]))
            if root in root_to_port:
                port_name = root_to_port[root]
                if not wire.net_locked:
                    wire._user_net_name = wire.net_name
                wire.net_name   = port_name
                wire.net_locked = True
            else:
                if wire.net_locked:
                    wire.net_name       = wire._user_net_name
                    wire._user_net_name = None
                wire.net_locked = False
            wire.update_label()

    def to_data(self):
        """Serialize the current scene to a SchematicData object."""
        self.settle_stacking()         # the saved z reproduces the canvas
        from .schematic_data import SchematicData, ComponentData, WireData, JunctionData, FreeTextData, CommandData, BorderData, LibraryData, ImageData, LatexFragmentData, ParameterData, AnalysisData, HyperlinkData, ModelData, PinData, SymbolTextData, OpaqueData
        from .symbol_editor import SymbolPinItem, SymbolTextItem, OpaqueSvgItem
        comps, wires, junctions, free_texts, commands, libs, images, latex_frags, param_items, analysis_items, hyperlinks, shapes, model_defs = [], [], [], [], [], [], [], [], [], [], [], [], []
        pins, symbol_texts, opaques = [], [], []
        border_data = None
        # bottom-to-top, so that from_data (which adds in list order) restores
        # the stacking; top-first flipped the order on every undo (2026-09-27)
        for item in reversed(self.items()):
            if isinstance(item, SymbolPinItem):
                pins.append(PinData(x=item.pos().x(), y=item.pos().y(), name=item.name, number=item.number)); continue
            if isinstance(item, SymbolTextItem):
                symbol_texts.append(SymbolTextData(x=item.pos().x(), y=item.pos().y(), content=item.content, size=item.size)); continue
            if isinstance(item, OpaqueSvgItem):
                opaques.append(OpaqueData(x=item.pos().x(), y=item.pos().y(), xml=item.xml)); continue
            if isinstance(item, ComponentItem):
                item._save_label_offsets()
                comps.append(ComponentData(
                    symbol_name=item.symbol_name,
                    instance_id=item.instance_id,
                    x=item.pos().x(),
                    y=item.pos().y(),
                    rotation=item.rotation(),
                    h_flip=item.h_flip,
                    v_flip=item.v_flip,
                    params=dict(item.params),
                    model=item.model,
                    refs=list(item.refs),
                    prop_display={k: list(v) for k, v in item.prop_display.items()},
                    prop_offsets={k: list(v) for k, v in item.prop_offsets.items()},
                ))
            elif isinstance(item, WireItem):
                wires.append(WireData(
                    points=[(p.x(), p.y()) for p in item.points],
                    net_name=item.net_name,
                    display_name=item.display_name,
                    label_offset=(item.label_offset.x(), item.label_offset.y()),
                    net_locked=item.net_locked,
                    user_net_name=item._user_net_name,
                    show_dc_voltage=item.show_dc_voltage,
                    dc_label_offset=(item.dc_label_offset.x(),
                                     item.dc_label_offset.y()),
                ))
            elif isinstance(item, JunctionItem):
                junctions.append(JunctionData(x=item.pos().x(), y=item.pos().y()))
            elif isinstance(item, FreeTextItem):
                free_texts.append(FreeTextData(
                    x=item.pos().x(), y=item.pos().y(),
                    text=item.toPlainText(),
                    font_family=item.font_family, font_size=item.font_size,
                    bold=item.bold, italic=item.italic, color=item.color,
                    z=item.zValue(), template=item.template,
                ))
            elif isinstance(item, CommandItem):
                commands.append(CommandData(
                    x=item.pos().x(), y=item.pos().y(),
                    text=item.toPlainText(),
                ))
            elif isinstance(item, BorderItem):
                r = item.rect()
                border_data = BorderData(
                    x=item.pos().x(), y=item.pos().y(),
                    width=r.width(), height=r.height(),
                    show_in_export=item.show_in_export,
                    fixed_w=item.fixed_w, fixed_h=item.fixed_h,
                    line_color=item.line_color, line_width=item.line_width,
                    bg_color=item.bg_color, bg_alpha=item.bg_alpha,
                    line_style=item.line_style,
                )
            elif isinstance(item, LibraryItem):
                libs.append(LibraryData(
                    x=item.pos().x(), y=item.pos().y(),
                    entries=[dict(e) for e in item.entries],
                    show=item.show_on_schematic,
                ))
            elif isinstance(item, ImageItem):
                images.append(ImageData(
                    x=item.pos().x(), y=item.pos().y(),
                    file_path=item.file_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                    link=item.link, z=item.zValue(),
                    scale=item.size_scale,
                ))
            elif isinstance(item, LatexFragmentItem):
                latex_frags.append(LatexFragmentData(
                    x=item.pos().x(), y=item.pos().y(),
                    latex_code=item.latex_code,
                    preamble_path=item.preamble_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                    color=item.color,
                    snippet=item.snippet,
                    z=item.zValue(),
                ))
            elif isinstance(item, ParameterItem):
                param_items.append(ParameterData(
                    x=item.pos().x(), y=item.pos().y(),
                    params=[list(p) for p in item.params],
                    preamble_path=item.preamble_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                    show=item.show_on_schematic,
                ))
            elif isinstance(item, AnalysisItem):
                analysis_items.append(AnalysisData(
                    x=item.pos().x(), y=item.pos().y(),
                    source=list(item.source),
                    detector=[list(d) for d in item.detector],
                    lgref=list(item.lgref),
                    show=item.show_on_schematic,
                ))
            elif isinstance(item, HyperlinkItem):
                hyperlinks.append(HyperlinkData(
                    x=item.pos().x(), y=item.pos().y(),
                    url=item.url, label=item.label, z=item.zValue(),
                ))
            elif isinstance(item, ModelItem):
                model_defs.append(ModelData(
                    x=item.pos().x(), y=item.pos().y(),
                    model_name=item.model_name,
                    model_type=item.model_type,
                    simulator=item.simulator,
                    params=[list(p) for p in item.params],
                    preamble_path=item.preamble_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                    show=item.show_on_schematic,
                ))
            elif isinstance(item, ShapeItem):
                from .schematic_data import ShapeData
                shapes.append(_shape_record(item))
        return SchematicData(components=comps, wires=wires,
                             junctions=junctions, free_texts=free_texts,
                             commands=commands, libs=libs, images=images,
                             border=border_data, latex_fragments=latex_frags,
                             parameters=param_items, analysis_items=analysis_items,
                             hyperlinks=hyperlinks, shapes=shapes,
                             model_defs=model_defs, pins=pins,
                             symbol_texts=symbol_texts, opaques=opaques,
                             origin=([self.origin_pos().x(), self.origin_pos().y()]
                                     if self.show_origin else None))

    def from_data(self, data, library) -> list:
        """Populate the scene from a SchematicData object.

        Returns the symbol names that could NOT be found, so a caller that
        must be correct - the netlister - can refuse instead of writing a
        netlist with a device missing (Anton, 2026-08-03).
        """
        self._library = library
        self.reset()
        missing: list[str] = []
        for cd in data.components:
            sym = library.symbol(cd.symbol_name)
            if sym is None:
                # Reported, not swallowed: a dropped component means a netlist
                # without that device (Anton, 2026-08-03).
                missing.append(cd.symbol_name)
                continue
            item = ComponentItem(sym, cd.instance_id)
            item.set_prop_offsets(cd.prop_offsets)   # discards the constructor's labels
            item.setPos(QPointF(cd.x, cd.y))
            item.setRotation(cd.rotation)
            item.h_flip       = cd.h_flip
            item.v_flip       = cd.v_flip
            item.apply_transform()
            item.params       = dict(cd.params)
            item.model        = cd.model
            item.refs         = list(cd.refs)
            item.prop_display = {k: tuple(v) for k, v in cd.prop_display.items()}
            # Backfill defaults for power symbols saved without net name (old files)
            if cd.symbol_name in ("0", "port"):
                item.params.setdefault("name", "0" if cd.symbol_name == "0" else "")
                item.prop_display.setdefault("name", (True, False))
            item.update_labels()
            self.addItem(item)
            # Keep counters above highest loaded number — keyed by PREFIX, to
            # match _next_id (otherwise X / M counters reset and refdes collide).
            prefix = sym.prefix or "X"
            m = re.match(rf"^{re.escape(prefix)}(\d+)$", cd.instance_id)
            if m:
                n = int(m.group(1))
                self._counters[prefix] = max(self._counters.get(prefix, 1), n + 1)

        for wd in data.wires:
            wire = WireItem([QPointF(x, y) for x, y in wd.points])
            wire.net_name        = wd.net_name
            wire.display_name    = wd.display_name
            wire.label_offset    = QPointF(*wd.label_offset)
            wire.net_locked      = wd.net_locked
            wire._user_net_name  = wd.user_net_name
            wire.show_dc_voltage = getattr(wd, "show_dc_voltage", False)
            wire.dc_label_offset = QPointF(*getattr(wd, "dc_label_offset",
                                                    (0.0, 6.0)))
            self.addItem(wire)
            wire.update_label()
            wire.update_dc_label()

        for jd in data.junctions:
            self.addItem(JunctionItem(QPointF(jd.x, jd.y)))

        self.document_properties = getattr(data, "properties", None)
        for td in data.free_texts:
            t = FreeTextItem(td.text, QPointF(td.x, td.y),
                             font_family=td.font_family, font_size=td.font_size,
                             bold=td.bold, italic=td.italic, color=td.color,
                             template=td.template)
            t.setZValue(td.z)
            t.render(self.document_properties)      # the properties block follows the file
            self.addItem(t)

        for cd in data.commands:
            self.addItem(CommandItem(cd.text, QPointF(cd.x, cd.y)))

        # One library BLOCK per schematic: merge every stored LibraryData
        # (new single block, or legacy one-file-per-item schematics) into it.
        lib_entries, lib_pos, lib_show = [], None, True
        for ld in data.libs:
            if lib_pos is None:
                lib_pos  = QPointF(ld.x, ld.y)
                lib_show = getattr(ld, "show", True)
            lib_entries.extend(dict(e) for e in ld.entries)
        if lib_entries:
            self.addItem(LibraryItem(lib_entries, lib_pos, show=lib_show))

        for img in data.images:
            im = ImageItem(img.file_path, img.display_width,
                           img.display_height, QPointF(img.x, img.y), link=img.link,
                           size_scale=img.scale)
            im.setZValue(img.z)
            self.addItem(im)

        for frag in data.latex_fragments:
            lf = LatexFragmentItem(
                frag.latex_code, frag.preamble_path,
                frag.display_width, frag.display_height,
                QPointF(frag.x, frag.y), color=frag.color,
                snippet=frag.snippet,
            )
            lf.setZValue(frag.z)
            self.addItem(lf)

        for pd in data.parameters:
            self.addItem(ParameterItem(
                [tuple(p) for p in pd.params], pd.preamble_path,
                QPointF(pd.x, pd.y),
                show=getattr(pd, "show", True),
            ))

        for ad in data.analysis_items:
            self.addItem(AnalysisItem(ad.source, ad.detector, ad.lgref,
                                      QPointF(ad.x, ad.y),
                                      show=getattr(ad, "show", True)))

        for hd in data.hyperlinks:
            h = HyperlinkItem(hd.url, hd.label, QPointF(hd.x, hd.y))
            h.setZValue(hd.z)
            self.addItem(h)

        for sd in data.shapes:
            self.addItem(_shape_from_record(sd))

        for md in data.model_defs:
            self.addItem(ModelItem(
                md.model_name, md.model_type, md.simulator,
                [list(p) for p in md.params],
                md.preamble_path,
                QPointF(md.x, md.y),
                show=getattr(md, "show", True),
            ))

        if data.border is not None:
            bd = data.border
            self.addItem(BorderItem(
                bd.x, bd.y, bd.width, bd.height, bd.show_in_export,
                fixed_w=bd.fixed_w, fixed_h=bd.fixed_h,
                line_color=bd.line_color, line_width=bd.line_width,
                bg_color=bd.bg_color, bg_alpha=bd.bg_alpha,
                line_style=bd.line_style))

        from .symbol_editor import SymbolPinItem, SymbolTextItem, OpaqueSvgItem
        for pd in getattr(data, "pins", []):
            self.addItem(SymbolPinItem(pd.name, pd.number, QPointF(pd.x, pd.y)))
        for td in getattr(data, "symbol_texts", []):
            self.addItem(SymbolTextItem(td.content, td.size, QPointF(td.x, td.y)))
        for od in getattr(data, "opaques", []):
            self.addItem(OpaqueSvgItem(od.xml, QPointF(od.x, od.y)))
        o = getattr(data, "origin", None)
        self.ensure_origin(QPointF(o[0], o[1]) if o else None)
        self._sync_junctions()
        # Derived net names for 'Display net name' wires without a
        # user label (transient; netlist authority arrives after a run).
        self.refresh_bias_annotations()
        return missing

    # ── scene events ─────────────────────────────────────────────────────────

    def _place_pos(self, event) -> QPointF:
        """Where a placed item goes: the raw pointer position for an
        annotation, the grid point for everything else (see
        _FREE_PLACEMENT_MODES)."""
        if self._mode == _Mode.PLACING_IMAGE and self._image_pending and \
           self._image_pending[3].split(":", 1)[0] in ("schematic", "poster"):
            from .config import shift_held, snap_fine
            # a placed DRAWING aligns with the grid, or the fine grid under Shift
            return snap_fine(event.scenePos()) if shift_held() else snap(event.scenePos())
        if self._mode in _FREE_PLACEMENT_MODES:
            return event.scenePos()
        if self._mode == _Mode.PLACING_ITEM and self._ghost is not None:
            return snap_pos(self._ghost, event.scenePos())
        return snap(event.scenePos())

    # ── hit resolution ────────────────────────────────────────────────────────

    def item_at(self, pos: QPointF):
        """The item the user points at, for a press, a right-click and a
        double-click alike.

        Precision beats stacking order. Qt's itemAt() takes the topmost item
        whose shape contains *pos*, but the shapes differ in precision: a
        component's shape is its select box, a deliberately coarse target
        that includes the pin leads, while a wire's shape is its own stroke,
        a net label's its text box and a drawn shape's its real geometry. A
        click on a visible wire where it enters a component's box must pick
        the wire, otherwise the wire cannot be selected or named near a pin
        (Anton, 2026-10-10). Raising the Z of the SELECTED item instead was
        considered and REJECTED: it works only once the wire is selected,
        and Z is part of the document (serialized and in the undo
        snapshots) and of the paint order.

        Order of preference, each level in stacking order:
        1. a handle of a selected drawn shape,
        2. a net label or DC bias label (a wire child whose Z only orders it
           among siblings; Anton, 2026-07-12: the bias placeholder was
           unreachable on top of a component),
        3. the topmost item that is not a coarse hit. Coarse hits are a
           component (hit through its select box) and a drawn shape hit on
           its band rather than on its real geometry. Everything else, a
           wire, a junction, a component label (a child with its own text
           box), a text, counts as exact and keeps its stacking order,
        4. the topmost item."""
        from .wire_item import _DCLabel, _NetLabel
        stack = self.items(pos)                      # topmost first
        if not stack:
            return None
        for i in stack:
            if (isinstance(i, ShapeItem) and i.isSelected()
                    and i._handle_at(i.mapFromScene(pos)) is not None):
                return i
        for i in stack:
            if isinstance(i, (_NetLabel, _DCLabel)):
                return i
        for i in stack:
            if isinstance(i, ComponentItem):
                continue
            if isinstance(i, ShapeItem) and not i.hit_exact(i.mapFromScene(pos)):
                continue
            return i
        return stack[0]

    def mousePressEvent(self, event):
        pos = self._place_pos(event)

        if self._mode == _Mode.PLACING and event.button() == Qt.LeftButton:
            self._push_undo()
            item = ComponentItem(
                self._library.symbol(self._placing_name),
                self._next_id(self._placing_name),
                self._placing_svg,
            )
            item.setPos(pos)
            if self._ghost is not None:           # as the ghost shows it
                item.setRotation(self._ghost.rotation())
                item.h_flip = bool(getattr(self, "_placing_hflip", False))
                item.apply_transform()
            self.addItem(item)
            self._sync_junctions()
            self._remove_short_circuit_wires()
            self._sync_junctions()

        elif self._mode == _Mode.PLACING_JUNCTION and event.button() == Qt.LeftButton:
            self._push_undo()
            self._connect_wires_at(pos)

        elif self._mode == _Mode.PLACING_TEXT and event.button() == Qt.LeftButton:
            self._push_undo()
            item = FreeTextItem(self._placing_text or "Text", pos,
                                template=getattr(self, "_placing_text_template", ""),
                                **getattr(self, "_placing_text_props", {}))
            self.addItem(item)
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_ITEM and event.button() == Qt.LeftButton:
            item, self._ghost = self._ghost, None
            self.removeItem(item)            # the snapshot is the scene without it
            self._push_undo()
            item.setOpacity(1.0)
            item.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
            item.setPos(pos)
            self.addItem(item)
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_HYPERLINK and event.button() == Qt.LeftButton:
            self._push_undo()
            url, label = self._hyperlink_pending or ("", "")
            self.addItem(HyperlinkItem(url, label, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_COMMAND and event.button() == Qt.LeftButton:
            self._push_undo()
            item = CommandItem(".", pos)
            self.addItem(item)
            self._cancel_placement()
            item.setTextInteractionFlags(Qt.TextEditorInteraction)
            item.setFocus()
            c = item.textCursor()
            c.movePosition(QTextCursor.End)
            item.setTextCursor(c)

        elif self._mode == _Mode.PLACING_BORDER and event.button() == Qt.LeftButton:
            self._push_undo()
            for existing in [i for i in self.items() if isinstance(i, BorderItem)]:
                self.removeItem(existing)
            self.addItem(BorderItem(pos.x(), pos.y(), **self._border_pending))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_IMAGE and event.button() == Qt.LeftButton:
            self._push_undo()
            fp, w, h, link, scale = self._image_pending
            self.addItem(ImageItem(fp, w, h, pos, link=link, size_scale=scale))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_LATEX and event.button() == Qt.LeftButton:
            self._push_undo()
            lc, pp, w, h, color, snippet = self._latex_pending
            self.addItem(LatexFragmentItem(lc, pp, w, h, pos, color=color, snippet=snippet))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_PARAMETER and event.button() == Qt.LeftButton:
            self._push_undo()
            prms, pp = self._param_pending
            self.addItem(ParameterItem(prms, pp, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_ANALYSIS and event.button() == Qt.LeftButton:
            self._push_undo()
            src, det, lgr = self._analysis_pending
            self.addItem(AnalysisItem(src, det, lgr, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_MODEL and event.button() == Qt.LeftButton:
            self._push_undo()
            mn, mt, sim, prms, pp = self._model_pending
            self.addItem(ModelItem(mn, mt, sim, prms, pp, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PASTING and event.button() == Qt.LeftButton:
            self._commit_paste(pos)

        elif self._mode in (_Mode.DRAWING_RECT, _Mode.DRAWING_ELLIPSE) and event.button() == Qt.LeftButton:
            if self._draw_anchor is None:
                self._draw_anchor = snap(pos)
            else:
                self._commit_shape(snap(pos))

        elif self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_POLYGON) and event.button() == Qt.LeftButton:
            sp = snap(pos)
            if not self._draw_pts:
                self._draw_pts = [sp]
                self._draw_anchor = sp
            else:
                self._draw_pts.append(sp)

        elif self._mode == _Mode.WIRING:
            if event.button() == Qt.LeftButton:
                if self._wire_points:
                    new_pts = _elbow(self._wire_points[-1], pos, self._wire_h_first)
                    self._wire_points.extend(new_pts[1:])
                else:
                    self._wire_points = [pos]
                self._refresh_preview(pos)
            elif event.button() == Qt.RightButton:
                self._end_wire(commit=True)

        else:
            raw = event.scenePos()
            if event.button() == Qt.LeftButton:
                # Start of a possible drag: reset every component's captured
                # rubber-band wire set so each component follows only the wires
                # attached to it at THIS drag's start (never a wire it passes
                # over mid-drag — that would steal another element's connection).
                for it in self.items():
                    if isinstance(it, ComponentItem):
                        it._drag_wires = None
                item = self.item_at(raw)
                from .wire_item import _DCLabel, _NetLabel
                if isinstance(item, (_NetLabel, _DCLabel)):
                    _lbl = item
                    # The scene drags the label itself (like wires/groups).
                    event.accept()          # no rubber band
                    if not (event.modifiers() & Qt.ControlModifier):
                        self.clearSelection()
                    _lbl.setSelected(True)
                    wire = _lbl.parentItem()
                    if wire is not None:
                        if isinstance(_lbl, _DCLabel):
                            wire._dc_label_active = True
                        else:
                            wire._label_active = True
                        wire.update()
                    self._label_drag = (_lbl, QPointF(_lbl.pos()),
                                        event.scenePos())
                    return
                if isinstance(item, WireItem):
                    # Accept the event so the view's RubberBandDrag mode does not
                    # start a rubber-band (which would clear our selection on release).
                    event.accept()
                    # Select on first contact so click+drag works in one gesture.
                    if not item.isSelected():
                        if not (event.modifiers() & Qt.ControlModifier):
                            self.clearSelection()
                        item.setSelected(True)
                    v = item.vertex_near(raw)
                    if v is not None:
                        self._pre_drag_data = self.to_data()
                        self._vdrag_moved   = False
                        self._vdrag_wire = item
                        self._vdrag_idx  = v
                        item.active_vertex = v
                        item.update()
                        # Find wires sharing the dragged endpoint so they
                        # stretch with it (rubber-band partners).
                        dragged_key = _pt_key(item.points[v])
                        self._vdrag_rb = []
                        for candidate in self.items():
                            if not isinstance(candidate, WireItem):
                                continue
                            if candidate is item:
                                continue
                            for ep_idx, ep_pt in ((0, candidate.points[0]),
                                                   (len(candidate.points) - 1,
                                                    candidate.points[-1])):
                                if _pt_key(ep_pt) == dragged_key:
                                    self._vdrag_rb.append(
                                        (candidate, ep_idx, QPointF(ep_pt)))
                                    break
                        # Check if the dragged vertex sits on a component pin.
                        self._vdrag_pin_anchor  = None
                        self._vdrag_pin_preview = None
                        for comp in self.items():
                            if not isinstance(comp, ComponentItem):
                                continue
                            for lx, ly in comp.pin_positions():
                                if _pt_key(comp.mapToScene(QPointF(lx, ly))) == dragged_key:
                                    self._vdrag_pin_anchor = (comp, (lx, ly))
                                    pw = WireItem([QPointF(item.points[v]),
                                                   QPointF(item.points[v])])
                                    pen = pw.pen()
                                    pen.setStyle(Qt.DashLine)
                                    pw.setPen(pen)
                                    self.addItem(pw)
                                    self._vdrag_pin_preview = pw
                                    break
                            if self._vdrag_pin_anchor is not None:
                                break
                        return
                    # Body click on a selected wire → move all selected items together
                    self._pre_drag_data = self.to_data()
                    self._record_pre_drag_wire_pts()
                    sel = self.selectedItems()
                    self._wire_move_wires   = [i for i in sel if isinstance(i, WireItem)]
                    self._wire_move_origins = [
                        [QPointF(p) for p in w.points]
                        for w in self._wire_move_wires
                    ]
                    self._wire_move_others  = [
                        (i, i.pos().x(), i.pos().y())
                        for i in sel if not isinstance(i, WireItem)
                    ]
                    self._wire_move_start   = snap(raw)
                    self._wire_move_moved   = False
                    # Lift moved wires above rubber-band partners (Z=0) so their
                    # selection handles are never overdrawn during drag.
                    for wire in self._wire_move_wires:
                        wire.setZValue(Z_WIRE_DRAG)
                    # Collect adjacent non-selected wires sharing an endpoint
                    # with a wire being moved (rubber-band partners).
                    moved_ids = {id(w) for w in self._wire_move_wires}
                    ep_keys: set[tuple] = set()
                    for origins in self._wire_move_origins:
                        if len(origins) >= 2:
                            ep_keys.add(_pt_key(origins[0]))
                            ep_keys.add(_pt_key(origins[-1]))
                    self._wire_move_rb = []
                    for candidate in self.items():
                        if not isinstance(candidate, WireItem):
                            continue
                        if id(candidate) in moved_ids:
                            continue
                        hits: dict = {}
                        last = len(candidate.points) - 1
                        if _pt_key(candidate.points[0]) in ep_keys:
                            hits[0] = QPointF(candidate.points[0])
                        if _pt_key(candidate.points[last]) in ep_keys:
                            hits[last] = QPointF(candidate.points[last])
                        if hits:
                            self._wire_move_rb.append((candidate, hits))
                    # Junctions at moving endpoints follow the drag visually.
                    self._wire_move_junctions = [
                        (item, QPointF(item.pos()))
                        for item in self.items()
                        if isinstance(item, JunctionItem)
                        and _pt_key(item.pos()) in ep_keys
                    ]
                    # Rule 1: remember which moved-wire endpoints sit on a
                    # component pin, so the connection is bridged (not dropped)
                    # if the wire is dragged off the pin. The component (if it
                    # isn't moving too) stays put, so its pin is the bridge anchor.
                    comp_pins: dict[tuple, tuple] = {}
                    for comp in self.items():
                        if isinstance(comp, ComponentItem):
                            for lx, ly in comp.pin_positions():
                                k = _pt_key(comp.mapToScene(QPointF(lx, ly)))
                                comp_pins[k] = (comp, (lx, ly))
                    self._wire_pin_anchors = []
                    for wire, origins in zip(self._wire_move_wires,
                                             self._wire_move_origins):
                        for idx in {0, len(origins) - 1}:
                            info = comp_pins.get(_pt_key(origins[idx]))
                            if info is not None:
                                comp, local = info
                                self._wire_pin_anchors.append((comp, local, wire, idx))
                    # Create dashed preview wires so the bridge is visible during drag.
                    self._wire_pin_preview_wires = []
                    for comp, local, wire, idx in self._wire_pin_anchors:
                        pw = WireItem([QPointF(wire.points[idx]),
                                       QPointF(wire.points[idx])])
                        pen = pw.pen()
                        pen.setStyle(Qt.DashLine)
                        pw.setPen(pen)
                        self.addItem(pw)
                        self._wire_pin_preview_wires.append(pw)
                    return
                # Detect pin-to-pin connections on the component under the cursor
                # so a connecting wire can be created if it is dragged away.
                self._pin_anchors = []
                if isinstance(item, ComponentItem):
                    others = {
                        _pt_key(p): QPointF(p)
                        for comp in self.items()
                        if isinstance(comp, ComponentItem) and comp is not item
                        for p in comp.pin_scene_pos()
                    }
                    for lx, ly in item.pin_positions():
                        p = item.mapToScene(QPointF(lx, ly))
                        pk = _pt_key(p)
                        if pk in others:
                            self._pin_anchors.append((others[pk], item, (lx, ly)))
                # snapshot before potential component/text/junction/border move
                self._pre_drag_data = self.to_data()
                self._record_pre_drag_wire_pts()
                self._pre_drag_pos  = {
                    id(i): (i.pos().x(), i.pos().y())
                    for i in self.items() if _undo_tracked(i)
                }
                # Custom group drag: intercept multi-item non-wire selections so
                # rubber-banding runs after all items have moved (not per-item in itemChange).
                if (item is not None and item.isSelected()
                        and not isinstance(item, WireItem)):
                    non_wire_sel = [
                        i for i in self.selectedItems()
                        if _undo_tracked(i) and not isinstance(i, _PropertyLabel)
                    ]
                    # Selected attribute labels of components that are NOT
                    # selected move with the group by the same scene delta;
                    # a label of a selected component rides with its parent.
                    loose_labels = [
                        i for i in self.selectedItems()
                        if isinstance(i, _PropertyLabel)
                        and i.parentItem() is not None
                        and not i.parentItem().isSelected()
                    ]
                    # A selection is a GROUP as soon as it holds more than
                    # the pressed item: other components, loose labels OR
                    # wires. One component with its wires selected is a
                    # block too; counting the non-wire items only sent it
                    # down the single-component path, which moved the
                    # component alone and stretched its selected wires from
                    # the pins (Anton, 2026-10-08).
                    sel_wires = [w for w in self.selectedItems() if isinstance(w, WireItem)]
                    if len(non_wire_sel) + len(loose_labels) + len(sel_wires) > 1 and non_wire_sel:
                        self._comp_group_move_items = [
                            (i, QPointF(i.pos())) for i in non_wire_sel
                        ]
                        # A group of annotations only (free text, LaTeX,
                        # hyperlinks, images: SNAPS_TO_GRID = False) moves
                        # freely; as soon as the group holds a grid item or
                        # a wire, the delta is a grid multiple so that those
                        # stay on grid while the annotations keep their
                        # offsets (Anton, 2026-09-27).
                        from .config import shift_held, snap_fine
                        critical = (any(getattr(i, "GRID_CRITICAL", False) for i in non_wire_sel)
                                    or any(isinstance(w, WireItem) for w in self.selectedItems()))
                        gridded = any(getattr(i, "SNAPS_TO_GRID", True) for i in non_wire_sel)
                        # grid: a critical item, or gridded items without Shift;
                        # fine: gridded items under Shift; free: annotations only
                        self._comp_group_move_mode = ("grid" if critical or (gridded and not shift_held())
                                                      else "fine" if gridded else "free")
                        self._comp_group_move_snaps = self._comp_group_move_mode == "grid"
                        self._comp_group_move_start = {"grid": snap(raw), "fine": snap_fine(raw)}.get(
                            self._comp_group_move_mode, QPointF(raw))
                        self._label_group_move_items = [
                            (lbl, lbl.parentItem().mapToScene(lbl.pos()))
                            for lbl in loose_labels
                        ]
                        # Store original positions of every point of every selected wire
                        self._wire_group_move_data = [
                            (w, [QPointF(p) for p in w.points])
                            for w in self.selectedItems()
                            if isinstance(w, WireItem)
                        ]
                        self._comp_group_move_moved = False
                        self._pin_anchors = []   # group move: no bridge wires needed
                        # Capture the unselected wire points that sit on the
                        # group's pins, junctions and selected-wire points NOW.
                        # They are moved from these originals on every step.
                        # Re-detecting them per step against the CURRENT pin
                        # positions was tried and REVERTED (2026-09-25): a pin
                        # passing over any foreign wire end mid-drag stole that
                        # wire, so a long drag connected the group to "almost
                        # all nodes" and broke the nets it crossed.
                        anchors: set[tuple] = set()
                        for itm, _ in self._comp_group_move_items:
                            if isinstance(itm, ComponentItem):
                                anchors.update(_pt_key(p) for p in itm.pin_scene_pos())
                            elif isinstance(itm, JunctionItem):
                                anchors.add(_pt_key(itm.pos()))
                        sel_wire_ids = {id(w) for w, _ in self._wire_group_move_data}
                        for w, orig_pts in self._wire_group_move_data:
                            anchors.update(_pt_key(p) for p in orig_pts)
                        self._group_rb = [
                            (w, i, QPointF(p))
                            for w in self.items()
                            if isinstance(w, WireItem) and id(w) not in sel_wire_ids
                            and not getattr(w, "_preview", False)
                            for i, p in enumerate(w.points) if _pt_key(p) in anchors
                        ]
                        # Rule 1 for the group (Anton, 2026-10-08): a moving
                        # point - a pin of a moving component or a point of a
                        # selected wire - that sits on a component pin at
                        # press stays connected. If it leaves the pin, the pin
                        # is bridged to its new position at release (dashed
                        # preview during the drag). A pin that moves with the
                        # group ends where the point ends, so nothing is added
                        # then. "Group move: no bridge wires needed" was the
                        # earlier assumption and was WRONG: a selected wire
                        # dragged off an unselected pin disconnected the net.
                        comp_pins: dict[tuple, list] = {}
                        for comp in self.items():
                            if isinstance(comp, ComponentItem):
                                for lx, ly in comp.pin_positions():
                                    k = _pt_key(comp.mapToScene(QPointF(lx, ly)))
                                    comp_pins.setdefault(k, []).append((comp, (lx, ly)))
                        self._group_pin_anchors = []
                        for w, orig_pts in self._wire_group_move_data:
                            for idx in {0, len(orig_pts) - 1}:
                                for comp, local in comp_pins.get(_pt_key(orig_pts[idx]), []):
                                    self._group_pin_anchors.append(
                                        (comp, local, ("wire", w, idx)))
                        for itm, _ in self._comp_group_move_items:
                            if not isinstance(itm, ComponentItem):
                                continue
                            for lx, ly in itm.pin_positions():
                                k = _pt_key(itm.mapToScene(QPointF(lx, ly)))
                                for comp, local in comp_pins.get(k, []):
                                    if comp is not itm:
                                        self._group_pin_anchors.append(
                                            (comp, local, ("pin", itm, (lx, ly))))
                        self._group_pin_previews = []
                        for comp, local, src in self._group_pin_anchors:
                            pt = self._group_moving_point(src)
                            pw = WireItem([QPointF(pt), QPointF(pt)])
                            pen = pw.pen()
                            pen.setStyle(Qt.DashLine)
                            pw.setPen(pen)
                            pw._preview = True
                            self.addItem(pw)
                            self._group_pin_previews.append(pw)
                        self.group_move_started.emit()
                        return
                # Single-component drag off a pin-to-pin contact: show the
                # bridge wire(s) as a dashed preview DURING the drag — like the
                # wire-move preview above — so pulling a connection apart is
                # visible immediately, not only after release. Created after the
                # pre-drag snapshot, and marked _preview, so they are never
                # serialised, undone, or grabbed by the component's own wire
                # rubber-banding.
                self._pin_preview_wires = []
                for anchor, comp, local in self._pin_anchors:
                    pw = WireItem([QPointF(anchor), QPointF(anchor)])
                    pen = pw.pen()
                    pen.setStyle(Qt.DashLine)
                    pw.setPen(pen)
                    pw._preview = True
                    self.addItem(pw)
                    self._pin_preview_wires.append(pw)
            elif event.button() == Qt.RightButton:
                item = self.item_at(raw)
                if isinstance(item, HyperlinkItem):
                    self._hyperlink_context_menu(item, event.screenPos())
                    return
            super().mousePressEvent(event)

    def _hyperlink_context_menu(self, item: HyperlinkItem, screen_pos) -> None:
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl, QPoint
        menu = QMenu()
        url_display = item.url if len(item.url) <= 60 else item.url[:57] + "…"
        open_act = menu.addAction(f"Open  {url_display}")
        open_act.setEnabled(bool(item.url))
        menu.addSeparator()
        edit_act = menu.addAction("Edit Hyperlink…")
        chosen = menu.exec(QPoint(int(screen_pos.x()), int(screen_pos.y())))
        if chosen is open_act and item.url:
            QDesktopServices.openUrl(QUrl(item.url))
        elif chosen is edit_act:
            from .hyperlink_dialog import HyperlinkDialog
            dlg = HyperlinkDialog(item.url, item.label, style=self.style)
            if dlg.exec():
                self._push_undo()
                item.url   = dlg.url()
                item.label = dlg.label()
                item.setText(item.label or item.url)

    def _wires_on_same_net(self, wire: WireItem) -> list:
        """Return all WireItems connected to wire on the same electrical net."""
        from .connectivity import _UF, _rpt, _on_segment
        wires = [w for w in self.items() if isinstance(w, WireItem)]
        uf = _UF()
        for w in wires:
            pts = [_rpt(p) for p in w.points]
            for i in range(len(pts) - 1):
                uf.union(pts[i], pts[i + 1])
        all_pts = [_rpt(p) for w in wires for p in w.points]
        for w in wires:
            for i in range(len(w.points) - 1):
                p1, p2 = w.points[i], w.points[i + 1]
                seg_root = uf.find(_rpt(p1))
                for pt in all_pts:
                    if _on_segment(p1, p2, QPointF(pt[0], pt[1])):
                        uf.union(seg_root, pt)
        if not wire.points:
            return [wire]
        target_root = uf.find(_rpt(wire.points[0]))
        return [w for w in wires if w.points and uf.find(_rpt(w.points[0])) == target_root]

    def _open_net_label(self, wire: WireItem) -> None:
        from .net_label_dialog import NetLabelDialog
        net_wires = self._wires_on_same_net(wire)
        # Use the canonical name from any segment on the net that already has one.
        canon_name    = wire.net_name or ""
        canon_display = wire.display_name
        for w in net_wires:
            if w.net_name and not w.net_locked:
                canon_name    = w.net_name
                canon_display = w.display_name
                break
        view     = self.views()[0] if self.views() else None
        panel    = view.parent() if view else None
        ngspice  = getattr(panel, '_sch_type', None) == 'ngspice'
        dlg = NetLabelDialog(canon_name, canon_display, locked=wire.net_locked,
                             offer_dc=ngspice, show_dc=wire.show_dc_voltage)
        if dlg.exec():
            self._push_undo()
            new_name = dlg.net_name() if not wire.net_locked else wire.net_name
            # Propagate the name to every segment on the same net.
            for w in net_wires:
                if not w.net_locked:
                    w.net_name       = new_name
                    w._user_net_name = new_name
            # Display flag: only show the label on the right-clicked segment.
            wire.display_name = dlg.display()
            if ngspice:
                # DC annotation belongs to the clicked segment only (one
                # "V: <value>" per net is the user's choice of placement).
                wire.show_dc_voltage = dlg.show_dc()
            for w in net_wires:
                w.update_label()
            self.refresh_bias_annotations()

    def mouseMoveEvent(self, event):
        pos = snap(event.scenePos())

        if (self._mode in (_Mode.PLACING, _Mode.PLACING_JUNCTION,
                           _Mode.PLACING_TEXT, _Mode.PLACING_COMMAND,
                           _Mode.PLACING_BORDER, _Mode.PLACING_LIBRARY,
                           _Mode.PLACING_IMAGE, _Mode.PLACING_LATEX,
                           _Mode.PLACING_PARAMETER, _Mode.PLACING_ANALYSIS,
                           _Mode.PLACING_HYPERLINK, _Mode.PLACING_MODEL,
                           _Mode.PLACING_ITEM)
                and self._ghost is not None):
            self._ghost.setPos(self._place_pos(event))

        elif self._mode == _Mode.WIRING:
            self._refresh_preview(pos)

        elif self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_RECT,
                             _Mode.DRAWING_ELLIPSE, _Mode.DRAWING_POLYGON):
            self._update_draw_ghost(snap(event.scenePos()))

        elif self._mode == _Mode.PASTING:
            if self._paste_ghost_items and self._paste_ref is not None:
                delta = pos - self._paste_ref
                for kind, item, base in self._paste_ghost_items:
                    if kind == 'point':
                        item.setPos(base + delta)
                    else:
                        item.setPath(_build_path([p + delta for p in base]))

        elif self._label_drag is not None:
            lbl, orig, start = self._label_drag
            lbl.setPos(orig + (event.scenePos() - start))

        elif self._wire_move_start is not None:
            delta = pos - self._wire_move_start
            if delta.x() != 0 or delta.y() != 0:
                self._wire_move_moved = True
            for wire, origins in zip(self._wire_move_wires, self._wire_move_origins):
                wire.points = [p + delta for p in origins]
                wire._rebuild()
            for rb_wire, rb_ep_origins in self._wire_move_rb:
                for idx, orig_pt in rb_ep_origins.items():
                    rb_wire.points[idx] = orig_pt + delta
                rb_wire._rebuild()
            for junc, orig_pos in self._wire_move_junctions:
                if junc.scene() is not None:
                    junc.setPos(orig_pos + delta)
            for other_item, ox, oy in self._wire_move_others:
                other_item.setPos(QPointF(ox + delta.x(), oy + delta.y()))   # delta is a grid multiple
            for (comp, local, wire, idx), pw in zip(self._wire_pin_anchors,
                                                     self._wire_pin_preview_wires):
                if pw.scene() is None:
                    continue
                cur_pin = comp.mapToScene(QPointF(*local))
                new_pt  = wire.points[idx]
                pw.points = _elbow(QPointF(cur_pin), QPointF(new_pt), True)
                pw._rebuild()

        elif self._vdrag_wire is not None:
            self._vdrag_moved = True
            self._vdrag_wire.move_vertex(self._vdrag_idx, pos)
            for rb_wire, rb_ep_idx, _ in self._vdrag_rb:
                rb_wire.points[rb_ep_idx] = QPointF(pos)
                rb_wire._rebuild()
            if self._vdrag_pin_preview is not None and self._vdrag_pin_anchor is not None:
                comp, local = self._vdrag_pin_anchor
                cur_pin = comp.mapToScene(QPointF(*local))
                self._vdrag_pin_preview.points = _elbow(QPointF(cur_pin), pos, True)
                self._vdrag_pin_preview._rebuild()

        elif self._comp_group_move_start is not None:
            from .config import snap_fine
            mode = getattr(self, "_comp_group_move_mode", "grid" if self._comp_group_move_snaps else "free")
            cur = pos if mode == "grid" else (snap_fine(event.scenePos()) if mode == "fine" else event.scenePos())
            total_delta = cur - self._comp_group_move_start
            if total_delta.x() != 0 or total_delta.y() != 0:
                self._comp_group_move_moved = True
            # The group moves by ONE delta, applied as it is: start and
            # pointer are both snapped, so the delta is a grid multiple and
            # grid items stay on grid, while annotations (free text, LaTeX,
            # hyperlinks, images) keep their fractional positions. Snapping
            # each item's new position instead made every annotation in the
            # group jump onto the grid at the first drag step (Anton,
            # 2026-09-27; see _FREE_PLACEMENT_MODES).
            self._group_drag_active = True
            for itm, orig_pos in self._comp_group_move_items:
                itm.setPos(orig_pos + total_delta)
            self._group_drag_active = False
            # Loose labels: same delta, in their parent's frame.
            if self._comp_group_move_items:
                label_delta = total_delta
                for lbl, orig_scene in self._label_group_move_items:
                    parent = lbl.parentItem()
                    if parent is not None and parent.scene() is not None:
                        lbl.setPos(parent.mapFromScene(orig_scene + label_delta))

            # Selected wires: recompute ALL points from their stored originals.
            snap_delta = total_delta if self._comp_group_move_items else QPointF(0, 0)

            for w, orig_pts in self._wire_group_move_data:
                if w.scene() is None:
                    continue
                for i, op in enumerate(orig_pts):
                    w.points[i] = op + snap_delta
                w._rebuild()

            # Unselected wires attached at drag start: their captured points
            # follow the group from the ORIGINALS (see the press branch).
            touched = set()
            for w, i, op in self._group_rb:
                if w.scene() is None or i >= len(w.points):
                    continue
                w.points[i] = op + snap_delta
                touched.add(w)
            for w in touched:
                w._rebuild()
            # Dashed bridge previews: from the pin to the moving point.
            for (comp, local, src), pw in zip(self._group_pin_anchors,
                                              self._group_pin_previews):
                if pw.scene() is None or comp.scene() is None:
                    continue
                pw.points = _elbow(QPointF(comp.mapToScene(QPointF(*local))),
                                   QPointF(self._group_moving_point(src)), True)
                pw._rebuild()

        else:
            super().mouseMoveEvent(event)
            # Stretch the dashed bridge previews to follow the dragged pins.
            if self._pin_preview_wires:
                for (anchor, comp, local), pw in zip(self._pin_anchors,
                                                     self._pin_preview_wires):
                    if pw.scene() is None or comp.scene() is None:
                        continue
                    new_pin = comp.mapToScene(QPointF(*local))
                    pw.points = _elbow(QPointF(anchor), QPointF(new_pin), True)
                    pw._rebuild()

    def _reselect_on_footprint(self, moved_segs: list) -> None:
        """Re-select wire items that lie on (or contain) the given footprint.

        After _sync_junctions() the original wire items may have been replaced
        by split pieces or a merged larger segment.  Both cases are handled:

        • split  – all points of the new piece lie within the footprint
                   (checked with _on_footprint for every vertex).
        • merge  – _merge_collinear_wires fused the moved wire with an
                   adjacent collinear wire; the footprint is a *sub-segment*
                   of the larger result.  Detected by verifying that every
                   endpoint of the moved segment lies on the candidate wire
                   (inclusive of that wire's own endpoints).
        """
        if not moved_segs:
            return

        def _on_footprint(pt):
            k = _pt_key(pt)
            for p1, p2 in moved_segs:
                if _pt_key(p1) == k or _pt_key(p2) == k:
                    return True
                if _pt_on_segment(k[0], k[1], p1, p2):
                    return True
            return False

        def _pt_on_wire_incl(k, wpts):
            return (_pt_key(wpts[0]) == k or _pt_key(wpts[-1]) == k
                    or _pt_on_segment(k[0], k[1], wpts[0], wpts[-1]))

        def _seg_in_wire(p1, p2, wpts):
            return (_pt_on_wire_incl(_pt_key(p1), wpts)
                    and _pt_on_wire_incl(_pt_key(p2), wpts))

        for w in self.items():
            if not (isinstance(w, WireItem) and len(w.points) >= 2):
                continue
            if (all(_on_footprint(p) for p in w.points)
                    or any(_seg_in_wire(p1, p2, w.points) for p1, p2 in moved_segs)):
                w.setSelected(True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._label_drag is not None:
                wire = self._label_drag[0].parentItem()
                if wire is not None:
                    wire._label_active = False
                    wire._dc_label_active = False
                    wire.update()
                self._label_drag = None
                event.accept()
                return
            if self._wire_move_start is not None:
                # Remove bridge-wire previews before any geometry operations.
                for pw in self._wire_pin_preview_wires:
                    if pw.scene() is not None:
                        self.removeItem(pw)
                self._wire_pin_preview_wires = []
                # Restore Z-values that were raised at drag-start.
                for wire in self._wire_move_wires:
                    if wire.scene() is not None:
                        wire.setZValue(Z_WIRE)
                if self._wire_move_moved:
                    self._push_snapshot(self._pre_drag_data)
                    self._reconnect_after_move()
                    # Footprint of the moved wire(s) at their new position.
                    moved_segs = [
                        (QPointF(w.points[i]), QPointF(w.points[i + 1]))
                        for w in self._wire_move_wires
                        for i in range(len(w.points) - 1)
                    ]
                    # Rule 1: bridge any moved-wire endpoint back to the component
                    # pin it left, so moving a wire never silently disconnects it.
                    for comp, local, wire, idx in self._wire_pin_anchors:
                        if wire.scene() is None or comp.scene() is None:
                            continue
                        new_pt  = wire.points[idx]
                        cur_pin = comp.mapToScene(QPointF(*local))
                        if _pt_key(new_pt) != _pt_key(cur_pin):
                            self.addItem(WireItem(_elbow(QPointF(cur_pin),
                                                         QPointF(new_pt), True)))
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                    self._reselect_on_footprint(moved_segs)
                    self.update()
                self._pre_drag_data          = None
                self._wire_move_start        = None
                self._wire_move_wires        = []
                self._wire_move_origins      = []
                self._wire_move_others       = []
                self._wire_move_moved        = False
                self._wire_move_rb           = []
                self._wire_move_junctions    = []
                self._wire_pin_anchors       = []
                self._wire_pin_preview_wires = []
                return
            if self._vdrag_wire is not None:
                # Remove pin preview regardless of movement.
                if self._vdrag_pin_preview is not None:
                    if self._vdrag_pin_preview.scene() is not None:
                        self.removeItem(self._vdrag_pin_preview)
                    self._vdrag_pin_preview = None
                if self._vdrag_moved:
                    self._push_snapshot(self._pre_drag_data)
                    # Bridge wire: if the dragged vertex left its component pin,
                    # add a wire from the pin to the new vertex position.
                    if self._vdrag_pin_anchor is not None:
                        comp, local = self._vdrag_pin_anchor
                        if comp.scene() is not None:
                            cur_pin = comp.mapToScene(QPointF(*local))
                            new_pt  = self._vdrag_wire.points[self._vdrag_idx]
                            if _pt_key(new_pt) != _pt_key(cur_pin):
                                self.addItem(WireItem(_elbow(QPointF(cur_pin),
                                                             QPointF(new_pt), True)))
                    # Capture footprint before _sync_junctions may replace the wire.
                    moved_segs = [(QPointF(self._vdrag_wire.points[0]),
                                   QPointF(self._vdrag_wire.points[-1]))]
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                    self._reselect_on_footprint(moved_segs)
                    self.update()
                self._pre_drag_data     = None
                self._vdrag_moved       = False
                if self._vdrag_wire is not None and self._vdrag_wire.scene() is self:
                    self._vdrag_wire.active_vertex = None
                    self._vdrag_wire.update()
                self._vdrag_wire        = None
                self._vdrag_idx         = None
                self._vdrag_rb          = []
                self._vdrag_pin_anchor  = None
                self._vdrag_pin_preview = None
                return
            if self._comp_group_move_start is not None:
                for pw in self._group_pin_previews:
                    if pw.scene() is not None:
                        self.removeItem(pw)
                self._group_pin_previews = []
                if self._comp_group_move_moved:
                    self._push_snapshot(self._pre_drag_data)
                    self._reconnect_after_move()
                    # Bridge every moving point that left its pin (one wire
                    # per pin/point pair: a wire end and a group pin on the
                    # same fixed pin would otherwise add the bridge twice).
                    bridged: set[tuple] = set()
                    for comp, local, src in self._group_pin_anchors:
                        if comp.scene() is None:
                            continue
                        pin = comp.mapToScene(QPointF(*local))
                        pt  = self._group_moving_point(src)
                        if pt is None or _pt_key(pt) == _pt_key(pin):
                            continue
                        key = (_pt_key(pin), _pt_key(pt))
                        if key not in bridged:
                            bridged.add(key)
                            self.addItem(WireItem(_elbow(QPointF(pin), QPointF(pt), True)))
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                self._group_pin_anchors = []
                self._comp_group_move_start = None
                self._comp_group_move_items = []
                self._label_group_move_items = []
                self._wire_group_move_data  = []
                self._group_rb              = []
                self._comp_group_move_moved = False
                self._pre_drag_data = None
                self._pre_drag_pos  = {}
                self._pre_drag_wire_pts = {}
                self._pin_anchors   = []
                self.group_move_ended.emit()
                return
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            if self._pre_drag_data is not None:
                # Drop the dashed bridge previews; the real bridge WireItems are
                # created below from _pin_anchors (only if the pin actually moved).
                for pw in self._pin_preview_wires:
                    if pw.scene() is not None:
                        self.removeItem(pw)
                self._pin_preview_wires = []
                moved = any(
                    (i.pos().x(), i.pos().y()) != self._pre_drag_pos.get(id(i))
                    for i in self.items()
                    if _undo_tracked(i) and id(i) in self._pre_drag_pos
                )
                if moved:
                    self._push_snapshot(self._pre_drag_data)
                    self._reconnect_after_move()
                    for anchor, comp, local_xy in self._pin_anchors:
                        if comp.scene() is not None:
                            new_pin = comp.mapToScene(QPointF(*local_xy))
                            if _pt_key(new_pin) != _pt_key(anchor):
                                self.addItem(WireItem(_elbow(anchor, new_pin, True)))
                    # A junction dragged off a component pin takes its attached
                    # wires with it (JunctionItem._rubber_band_wires) but leaves the
                    # pin behind — bridge the pin to the junction's new position so
                    # the connection is not silently dropped (only deleting a wire
                    # or component should disconnect a pin).
                    comp_pins = {
                        _pt_key(comp.mapToScene(QPointF(lx, ly)))
                        for comp in self.items() if isinstance(comp, ComponentItem)
                        for lx, ly in comp.pin_positions()
                    }
                    for j in self.items():
                        if not isinstance(j, JunctionItem):
                            continue
                        old_xy = self._pre_drag_pos.get(id(j))
                        if old_xy is None:
                            continue
                        old_pin = QPointF(*old_xy)
                        new_pos = j.pos()
                        if (_pt_key(old_pin) in comp_pins
                                and _pt_key(old_pin) != _pt_key(new_pos)):
                            self.addItem(WireItem(_elbow(old_pin, QPointF(new_pos), True)))
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                self._pin_anchors = []
            self._pre_drag_data = None
            self._pre_drag_pos  = {}
            self._pre_drag_wire_pts = {}

    def mouseDoubleClickEvent(self, event):
        if self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_POLYGON) and event.button() == Qt.LeftButton:
            # The first click of the double-click already added the final point
            # via mousePressEvent; commit if we have enough points.
            if len(self._draw_pts) >= 2:
                self._commit_shape(self._draw_pts[-1])
            return
        if self._mode != _Mode.NORMAL:
            super().mouseDoubleClickEvent(event)
            return
        if event.button() != Qt.LeftButton:
            return
        item = self.item_at(event.scenePos())
        # BorderItem.shape() covers only the edge; item_at() misses interior
        # clicks on an otherwise empty area.  Only fall back to a bounding-rect
        # check when nothing else was found at the click position.
        if item is None:
            sp = event.scenePos()
            for candidate in self.items():
                if isinstance(candidate, BorderItem):
                    if candidate.rect().contains(candidate.mapFromScene(sp)):
                        item = candidate
                        break
        if isinstance(item, BorderItem):
            from .border_dialog import BorderDialog
            from .document_properties_dialog import border_formats
            r = item.rect()
            dlg = BorderDialog(
                width=r.width(),
                height=r.height(),
                show_in_export=item.show_in_export,
                fixed_w=item.fixed_w, fixed_h=item.fixed_h,
                line_color=item.line_color, line_width=item.line_width,
                bg_color=item.bg_color, bg_alpha=item.bg_alpha,
                line_style=item.line_style,
                formats=border_formats(self.style.BORDER_PRESETS),
            )
            if dlg.exec():
                self._push_undo()
                props = dlg.border_properties()
                item.line_style = props["line_style"]
                item.setRect(0, 0, props["width"], props["height"])
                item.show_in_export = props["show_in_export"]
                item.fixed_w = props["fixed_w"]
                item.fixed_h = props["fixed_h"]
                item.line_color = props["line_color"]
                item.line_width = props["line_width"]
                item.bg_color = props["bg_color"]
                item.bg_alpha = props["bg_alpha"]
                item.apply_style()
            return
        if isinstance(item, LibraryItem):
            from .library_dialog import LibraryDialog
            dlg = LibraryDialog(entries=item.entries,
                                sch_type=getattr(self, "sch_type", "slicap"),
                                show=item.show_on_schematic)
            if dlg.exec():
                self._push_undo()
                entries = dlg.entries()
                if entries:
                    item.entries = entries
                    item.set_show(dlg.show_on_schematic())
                    item.update_text()
                else:                      # all lines removed → drop the block
                    self.removeItem(item)
            return
        if isinstance(item, ImageItem):
            from .image_dialog import ImageDialog
            dlg = ImageDialog(
                file_path=item.file_path,
                display_width=item.display_width,
                display_height=item.display_height,
                size_scale=item.size_scale,
                style=self.style,
                link_kind=item.link_kind,
                choices=self.link_choices(item.link_kind) if item.link_kind else None,
                link_name=item.link_name,
            )
            if dlg.exec() and dlg.image_path():
                self._push_undo()
                item.link           = dlg.link()
                item.file_path      = dlg.image_path()
                item.prepareGeometryChange()
                item._load()
                item.set_size_scale(dlg.image_scale())
            return
        if isinstance(item, LatexFragmentItem):
            from .latex_fragment_dialog import LatexFragmentDialog
            from .design_data import manifest_snippets
            from . import project
            dlg = LatexFragmentDialog(
                latex_code=item.latex_code,
                preamble_path=item.preamble_path,
                svg_bytes=item._svg_bytes,
                display_width=item.display_width,
                display_height=item.display_height,
                color=item.color,
                style=self.style,
                snippets=manifest_snippets(project.project_root()) if item.snippet else None,
                snippet=item.snippet,
            )
            if dlg.exec() and (dlg.svg_bytes() or dlg.snippet()):
                self._push_undo()
                item.snippet       = dlg.snippet()
                item.latex_code    = dlg.latex_code()
                item.preamble_path = dlg.preamble_path()
                item.display_width  = dlg.display_width()
                item.display_height = dlg.display_height()
                item.color          = dlg.color()
                item._load_renderer()
                item.prepareGeometryChange()
                item.update()
            return
        if isinstance(item, ParameterItem):
            from .parameter_dialog import ParameterDialog
            dlg = ParameterDialog(
                params=item.params,
                preamble_path=item.preamble_path,
                show=item.show_on_schematic,
                edit_mode=True,
                style=self.style,
            )
            if dlg.exec():
                self._push_undo()
                item.prepareGeometryChange()
                item.params        = dlg.get_params()
                item.preamble_path = dlg.preamble_path()
                item.set_show(dlg.show_on_schematic())
                item._load_renderer()
                item.update()
            return
        if isinstance(item, AnalysisItem):
            from .analysis_dialog import AnalysisDialog
            provider = getattr(self, "analysis_candidates", None)
            dlg = AnalysisDialog(
                source=item.source,
                detector=item.detector,
                lgref=item.lgref,
                show=item.show_on_schematic,
                **(provider() if provider else {}),
            )
            if dlg.exec():
                self._push_undo()
                item.source   = dlg.get_source()
                item.detector = dlg.get_detector()
                item.lgref    = dlg.get_lgref()
                item.set_show(dlg.show_on_schematic())
                item.update_text()
            return
        if isinstance(item, ModelItem):
            from .model_dialog import ModelDialog
            dlg = ModelDialog(
                model_name=item.model_name,
                model_type=item.model_type,
                simulator=item.simulator,
                params=item.params,
                preamble_path=item.preamble_path,
                show=item.show_on_schematic,
                edit_mode=True,
                style=self.style,
                sch_type=getattr(self, "sch_type", "slicap"),
            )
            if dlg.exec():
                self._push_undo()
                item.prepareGeometryChange()
                item.model_name    = dlg.model_name()
                item.model_type    = dlg.model_type()
                item.simulator     = dlg.simulator()
                item.params        = dlg.get_params()
                item.preamble_path = dlg.preamble_path()
                item.set_show(dlg.show_on_schematic())
                item._load_renderer()
                item.update()
            return
        if isinstance(item, FreeTextItem):
            from .text_dialog import TextDialog
            dlg = TextDialog(item.template or item.toPlainText(), style=self.style,
                             template=item.is_properties, **item.own_properties())
            if dlg.exec():
                self._push_undo()
                if item.is_properties:
                    item.template = dlg.text() or item.template
                    item.render(self.document_properties)
                else:
                    item.setPlainText(dlg.text())
                item.set_properties(**dlg.properties())
            return
        if isinstance(item, HyperlinkItem):
            from .hyperlink_dialog import HyperlinkDialog
            dlg = HyperlinkDialog(item.url, item.label, style=self.style)
            if dlg.exec():
                self._push_undo()
                item.url   = dlg.url()
                item.label = dlg.label()
                item.setText(item.label or item.url)
            return
        from .symbol_editor import SymbolPinItem, SymbolTextItem, PinDialog, SymbolTextDialog
        if isinstance(item, SymbolPinItem):
            dlg = PinDialog(item.name, item.number)
            if dlg.exec():
                self._push_undo()
                item.name, item.number = dlg.name(), dlg.number()
                item.refresh()
            return
        if isinstance(item, SymbolTextItem):
            dlg = SymbolTextDialog(item.content, item.size)
            if dlg.exec():
                self._push_undo()
                item.prepareGeometryChange()
                item.content, item.size = dlg.content(), dlg.size()
                item.update()
            return
        if isinstance(item, ShapeItem):
            from .shape_dialog import ShapeDialog
            dlg = ShapeDialog(item, trace_choices=self._trace_choices())
            if dlg.exec():
                self._push_undo()
                self._apply_shape_dialog(item, dlg)
                item.update()
            return
        if isinstance(item, WireItem):
            self._open_net_label(item)
            return
        from .component_item import _PropertyLabel
        if isinstance(item, _PropertyLabel) and isinstance(item.parentItem(), ComponentItem):
            comp = item.parentItem()
            from .attribute_dialog import AttributeDialog
            dlg = AttributeDialog(comp, item.prop_key)
            if dlg.exec():
                self._push_undo()
                dlg.apply()
                if comp.symbol_name == "port":
                    self._sync_port_net_names()
            return
        if isinstance(item, ComponentItem):
            if item.symbol_name in ("0", "port"):
                from .power_symbol_dialog import PowerSymbolDialog
                dlg = PowerSymbolDialog(item)
                if dlg.exec():
                    self._push_undo()
                    dlg.apply()
                    if item.symbol_name == "port":
                        self._sync_port_net_names()
            else:
                prefix   = item.prefix or "X"
                view     = self.views()[0] if self.views() else None
                panel    = view.parent() if view else None
                sch_type = getattr(panel, '_sch_type', None)
                show_stimuli = (sch_type == 'ngspice' and prefix in ("V", "I"))
                offer_dc = (sch_type == 'ngspice' and prefix in ("V", "L"))
                from .properties_dialog import PropertiesDialog
                dlg = PropertiesDialog(item,
                                       show_stimuli=show_stimuli,
                                       is_current=(prefix == "I"),
                                       offer_dc_current=offer_dc,
                                       sch_ext=(".spice_sch"
                                                if sch_type == 'ngspice'
                                                else ".slicap_sch"),
                                       library=getattr(self, "_library", None))
                result = dlg.exec()
                if dlg.descend_path() is not None:
                    # Open the subcircuit's schematic so deeper hierarchies
                    # stay navigable. open_subschematic lives on the
                    # CanvasPanel (= view.parent(), computed above);
                    # view.window() is the MAIN window, which never had it -
                    # the old hasattr guard therefore ate the click
                    # SILENTLY, and descending was dead from the day the
                    # panels were docked (Anton, 2026-08-04).
                    if panel is not None and hasattr(panel,
                                                     "open_subschematic"):
                        # from_item: the descended-from instance selects
                        # WHICH instance's operating point the subcircuit
                        # shows (last descent wins).
                        panel.open_subschematic(dlg.descend_path(),
                                                from_item=item)
                    else:
                        print("Error: cannot descend: no canvas panel "
                              "owns this scene.")
                elif result:
                    self._push_undo()
                    dlg.apply()
                    change = dlg.symbol_change()
                    if change is not None:
                        sym, svg_text = change
                        if svg_text is not None and panel is not None \
                                and hasattr(panel, "adopt_symbol"):
                            sym = panel.adopt_symbol(sym.name, svg_text) or sym
                        self.change_symbol(item, sym)
        else:
            super().mouseDoubleClickEvent(event)

    def change_symbol(self, item, symbol) -> None:
        """Give a placed component another symbol (Properties → Change
        symbol…). The wires attached to its pins follow the pins to their
        new places, so the net stays intact: the node order is the same
        (same element type, or the port mapping is written into the
        re-skinned subcircuit symbol), so pin i stays pin i."""
        old = item.pin_scene_pos()
        item.reload_symbol(symbol)
        new = item.pin_scene_pos()
        wires = [w for w in self.items()
                 if isinstance(w, WireItem) and not getattr(w, "_preview", False)]
        moves = []            # collected first: a pin swap must not chain
        for o, n in zip(old, new):
            if _pt_key(o) == _pt_key(n):
                continue
            for w in wires:
                for idx in {0, len(w.points) - 1}:
                    if _pt_key(w.points[idx]) == _pt_key(o):
                        moves.append((w, idx, n - w.points[idx]))
        for w, idx, delta in moves:
            w.move_points({idx}, delta)
        self._sync_junctions()
        self._remove_short_circuit_wires()
        self._sync_junctions()
        self.data_changed.emit()

    # ── grid background ───────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        """Canvas background for the display theme (config.dark_theme_active):
        the document colours are untouched, items resolve their display
        colours through config.style_of (2026-09-27)."""
        from . import config as _config
        self.setBackgroundBrush(_config.canvas_background())
        self.update()

    def ensure_origin(self, pos=None) -> None:
        """Symbol editor: keep exactly one origin marker (after reset / undo)."""
        from .symbol_editor import OriginItem
        if not self.show_origin:
            return
        marker = next((i for i in self.items() if isinstance(i, OriginItem)), None)
        if marker is None:
            marker = OriginItem()
            self.addItem(marker)
        if pos is not None:
            marker.setPos(pos)

    def origin_pos(self) -> QPointF:
        """Symbol editor: where the origin marker is (0,0 when absent)."""
        from .symbol_editor import OriginItem
        marker = next((i for i in self.items() if isinstance(i, OriginItem)), None)
        return QPointF(marker.pos()) if marker is not None else QPointF(0, 0)

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        if self._exporting:
            return
        from . import config as _config
        style = _config.display_style(self.style)

        left   = int(rect.left())   - (int(rect.left())   % GRID_SIZE)
        top    = int(rect.top())    - (int(rect.top())    % GRID_SIZE)
        right  = int(rect.right())
        bottom = int(rect.bottom())

        minor_pen = QPen(style.GRID_MINOR_COLOR, 0)
        major_pen = QPen(style.GRID_MAJOR_COLOR, 0)

        x = left
        while x <= right:
            painter.setPen(major_pen if (x // GRID_SIZE) % GRID_MAJOR == 0 else minor_pen)
            painter.drawLine(x, top, x, bottom)
            x += GRID_SIZE

        y = top
        while y <= bottom:
            painter.setPen(major_pen if (y // GRID_SIZE) % GRID_MAJOR == 0 else minor_pen)
            painter.drawLine(left, y, right, y)
            y += GRID_SIZE

        # Subgrid (preference "View subgrid"): a dot on every fine-grid point
        # (config.FINE_STEP, the Shift snap), drawn only when the zoom keeps
        # the dots apart (>= 3 px) - closer they would be a grey wash.
        if getattr(style, "GRID_SUBGRID", False):
            from .config import FINE_STEP
            scale = painter.worldTransform().m11()
            if scale * FINE_STEP >= 3.0:
                step = FINE_STEP
                # dot size in device pixels grows with the zoom (1 px was
                # invisible at high zoom, 2026-09-27); cosmetic pen = px
                # Drawn in DEVICE pixels, rounded, so that the dots land on
                # the same pixel columns as the pixel-snapped grid lines; at a
                # fractional zoom antialiased scene-coordinate dots drifted
                # off the lines (Anton, 2026-09-27).
                size = max(1.0, min(3.0, scale * FINE_STEP / 4.0))
                dot = QPen(style.GRID_SUBGRID_COLOR, size); dot.setCapStyle(Qt.RoundCap)
                world = painter.worldTransform()
                pts = []
                sx = int(rect.left() // step) * step
                sy = int(rect.top() // step) * step
                x = sx
                while x <= right:
                    y = sy
                    on_line_x = abs(x / GRID_SIZE - round(x / GRID_SIZE)) < 1e-6
                    while y <= bottom:
                        if not (on_line_x or abs(y / GRID_SIZE - round(y / GRID_SIZE)) < 1e-6):
                            d = world.map(QPointF(x, y))
                            pts.append(QPointF(round(d.x()) + 0.5, round(d.y()) + 0.5))
                        y += step
                    x += step
                if pts:
                    painter.save()
                    painter.resetTransform()
                    painter.setRenderHint(QPainter.Antialiasing, False)
                    painter.setPen(dot)
                    painter.drawPoints(QPolygonF(pts))
                    painter.restore()


def _undo_tracked(item) -> bool:
    """A move of this item is an undo step: every top-level movable item
    except wires (which have their own drag bookkeeping), plus the loose
    property labels. Replaces three copies of an explicit kind list that
    had to be extended for every new item kind and was not (shapes,
    hyperlinks, the symbol editor's items had no undo for moves; Anton,
    2026-09-27)."""
    from .component_item import _PropertyLabel
    from .wire_item import WireItem
    if isinstance(item, _PropertyLabel):
        return True
    return (item.parentItem() is None and not isinstance(item, WireItem)
            and bool(item.flags() & QGraphicsItem.ItemIsMovable))


def _rb_keep_item(item, scene_rect: QRectF, contains: bool) -> bool:
    """
    Return True if item should stay selected given scene_rect and mode.

    contains=True  → right-to-left drag: item must be fully inside scene_rect.
    contains=False → left-to-right drag: item must intersect scene_rect.

    Uses tight per-type rects so that label bounding boxes on components and
    wires don't trigger selection when the rubber-band is far from the body.
    """
    from .component_item import ComponentItem
    from .wire_item import WireItem
    if isinstance(item, WireItem):
        if contains:
            return all(scene_rect.contains(pt) for pt in item.points)
        # intersects: build a tight rect from the wire points, ignoring the label
        pts = item.points
        if not pts:
            return False
        xs = [p.x() for p in pts]
        ys = [p.y() for p in pts]
        tol = 3.0
        path_rect = QRectF(min(xs) - tol, min(ys) - tol,
                           max(xs) - min(xs) + 2 * tol,
                           max(ys) - min(ys) + 2 * tol)
        return scene_rect.intersects(path_rect)
    if isinstance(item, ComponentItem):
        local_rect = QRectF(*item.symbol.select_box)
        item_rect = item.mapRectToScene(local_rect)
        return scene_rect.contains(item_rect) if contains else scene_rect.intersects(item_rect)
    # Shapes: their geometry (select_rect), not the painting margin
    if hasattr(item, "select_rect"):
        item_rect = item.mapRectToScene(item.select_rect())
        return scene_rect.contains(item_rect) if contains else scene_rect.intersects(item_rect)
    # JunctionItem, FreeTextItem, CommandItem, etc. — use actual bounding rect (no labels)
    item_rect = item.mapRectToScene(item.boundingRect())
    return scene_rect.contains(item_rect) if contains else scene_rect.intersects(item_rect)


# ── view ─────────────────────────────────────────────────────────────────────

class SchematicView(QGraphicsView):
    def __init__(self, scene: SchematicScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)

        scene.placing_started.connect(self._on_active_mode)
        scene.placing_ended.connect(self._on_normal_mode)
        scene.wire_mode_started.connect(self._on_active_mode)
        scene.wire_mode_ended.connect(self._on_normal_mode)
        scene.group_move_started.connect(self._on_active_mode)
        scene.group_move_ended.connect(self._on_normal_mode)

        self._panning   = False
        self._pan_start = None
        self._rb_start  = None   # viewport pos where left-drag started

        QTimer.singleShot(0, self._init_view)

    def _init_view(self):
        self.scale(DEFAULT_ZOOM, DEFAULT_ZOOM)
        self.centerOn(0, 0)

    def _on_active_mode(self):
        """A placing or drawing mode: no rubber band, and the cross ("+")
        cursor on the view AND its viewport. The viewport is the widget
        under the pointer; QGraphicsView resets the viewport's cursor on
        its own when an item with a cursor of its own (a border edge) is
        left, and after a modal dialog the viewport's cursor is what the
        window system re-reads (Anton, 2026-10-06: the "+" must show after
        a Draw command and after OK of the function dialog)."""
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)
        self.viewport().setCursor(Qt.CrossCursor)

    def _on_normal_mode(self):
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.viewport().unsetCursor()
        self.unsetCursor()

    # ── zoom ─────────────────────────────────────────────────────────────────

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(1 / 1.25, 1 / 1.25)

    def _visible_items_rect(self) -> QRectF:
        """Union of the bounding rects of VISIBLE items only.

        Items whose display is switched off (e.g. a parameter table with
        "show on schematic" disabled) deliberately stay in the scene so
        they keep netlisting — but scene().itemsBoundingRect() counts them
        regardless of visibility, which made View → Fit frame invisible
        content. isVisible() is effective visibility, so children of
        hidden items are excluded as well."""
        r = QRectF()
        for it in self.scene().items():
            if it.isVisible():
                r = r.united(it.sceneBoundingRect())
        return r

    def zoom_reset(self):
        self.resetTransform()
        self.scale(DEFAULT_ZOOM, DEFAULT_ZOOM)
        r = self._visible_items_rect()
        self.centerOn(r.center() if not r.isNull() else QPointF(0, 0))

    def zoom_fit(self):
        """Fit all visible scene items in the viewport with a small margin."""
        r = self._visible_items_rect()
        if r.isNull():
            self.zoom_reset()
            return
        margin = max(r.width(), r.height()) * 0.05
        r = r.adjusted(-margin, -margin, margin, margin)
        self.fitInView(r, Qt.KeepAspectRatio)

    # ── pan (middle mouse) ───────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning   = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            if event.button() == Qt.LeftButton:
                self._rb_start = event.position().toPoint()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta           = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)
            # Keep visual selection in sync with what the final post-filter will keep.
            # Only while Qt is really drawing a rubber band: a press that an
            # item accepted (a label, a component) is an item DRAG, and
            # filtering the selection against the drag rectangle deselected
            # every other selected label after 4 px, so only the label under
            # the cursor kept moving (Anton, 2026-09-13).
            if (event.buttons() & Qt.LeftButton and self._rb_start is not None
                    and not self.rubberBandRect().isNull()):
                dx = event.position().x() - self._rb_start.x()
                dy = event.position().y() - self._rb_start.y()
                if abs(dx) > 4 or abs(dy) > 4:
                    press_scene   = self.mapToScene(self._rb_start)
                    release_scene = self.mapToScene(event.position().toPoint())
                    rb_rect   = QRectF(press_scene, release_scene).normalized()
                    is_contain = dx < 0
                    for item in list(self.scene().selectedItems()):
                        if not _rb_keep_item(item, rb_rect, contains=is_contain):
                            item.setSelected(False)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.unsetCursor()
        else:
            rb_start = self._rb_start
            if event.button() == Qt.LeftButton:
                self._rb_start = None
            # Qt clears its rubber band inside the release: read it first.
            if self.rubberBandRect().isNull():
                rb_start = None          # an item drag, not a rubber band
            super().mouseReleaseEvent(event)
            # Post-filter for both drag directions: use tight per-type rects so that
            # label bounding boxes don't cause early/wrong selection.
            # Skip for plain clicks (drag distance < 4 vp-px): a zero-size QRectF
            # returns False from intersects(), which would deselect any clicked item.
            if event.button() == Qt.LeftButton and rb_start is not None:
                dx = event.position().x() - rb_start.x()
                dy = event.position().y() - rb_start.y()
                if abs(dx) > 4 or abs(dy) > 4:
                    press_scene   = self.mapToScene(rb_start)
                    release_scene = self.mapToScene(event.position().toPoint())
                    rb_rect   = QRectF(press_scene, release_scene).normalized()
                    is_contain = dx < 0
                    for item in list(self.scene().selectedItems()):
                        if not _rb_keep_item(item, rb_rect, contains=is_contain):
                            item.setSelected(False)

    # ── keyboard ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        scene = self.scene()

        # While a text item is actively being edited, let Qt dispatch
        # the event normally — don't intercept Backspace, R, Ctrl+C/V, etc.
        focused = scene.focusItem()
        from PySide6.QtWidgets import QGraphicsTextItem
        if (isinstance(focused, QGraphicsTextItem)
                and focused.textInteractionFlags() != Qt.NoTextInteraction):
            super().keyPressEvent(event)
            return

        key  = event.key()
        mods = event.modifiers()

        if key == Qt.Key_Escape:
            if scene._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_POLYGON):
                # Commit if we have a valid shape; otherwise just cancel
                if len(scene._draw_pts) >= 2:
                    scene._commit_shape(scene._draw_pts[-1])
                else:
                    scene._cancel_draw()
            elif scene._mode in (_Mode.DRAWING_RECT, _Mode.DRAWING_ELLIPSE):
                scene._cancel_draw()
            elif scene._mode == _Mode.WIRING:
                scene.finish_wire()
            else:
                scene.cancel_placement()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if scene._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_POLYGON) and len(scene._draw_pts) >= 2:
                scene._commit_shape(scene._draw_pts[-1])
            else:
                scene.finish_wire()
        elif key == Qt.Key_Slash:
            scene.toggle_elbow()
        elif key == Qt.Key_Z and mods & Qt.ControlModifier:
            if mods & Qt.ShiftModifier:
                scene.redo()
            else:
                scene.undo()
        elif key == Qt.Key_Y and mods & Qt.ControlModifier:
            scene.redo()
        elif key == Qt.Key_R:
            if scene.rotate_ghost():
                return                    # a component being placed turns
            rotatable = [i for i in scene.selectedItems()
                         if not isinstance(i, _PropertyLabel)]
            if rotatable:
                scene._push_undo()
            for item in rotatable:
                if isinstance(item, ShapeItem):
                    item.rotate_quarter()      # on the points, see ShapeItem
                else:
                    item.setRotation(item.rotation() + 90)
        elif key == Qt.Key_M:
            if scene.mirror_ghost():
                return
            sel = [i for i in scene.selectedItems()
                   if isinstance(i, (ComponentItem, ShapeItem))]
            if sel:
                scene._push_undo()
                for item in sel:
                    if isinstance(item, ShapeItem):
                        item.mirror()
                    else:
                        item.h_flip = not item.h_flip
                        item.apply_transform()
                scene._sync_junctions()
        elif key in (Qt.Key_Delete, Qt.Key_Backspace):
            if scene.selectedItems():
                scene._push_undo()
                for item in scene.selectedItems():
                    from .wire_item import WireItem as _WI
                    parent = item.parentItem()
                    if isinstance(parent, _WI):
                        # Selected item is a net label child — clear the label.
                        parent.net_name       = ""
                        parent._user_net_name = ""
                        parent.display_name   = False
                        parent.update_label()
                    elif isinstance(item, _PropertyLabel):
                        scene.hide_label(item)
                    else:
                        scene.removeItem(item)
                scene._sync_junctions()
        elif key == Qt.Key_C and mods & Qt.ControlModifier:
            scene._copy_selection()
        elif key == Qt.Key_X and mods & Qt.ControlModifier:
            sel = scene.selectedItems()
            if sel:
                scene._copy_selection()
                scene._push_undo()
                for item in sel:
                    if isinstance(item, _PropertyLabel):
                        scene.hide_label(item)
                    else:
                        scene.removeItem(item)
                scene._sync_junctions()
        elif key == Qt.Key_V and mods & Qt.ControlModifier:
            scene._paste_clipboard()
        else:
            super().keyPressEvent(event)
