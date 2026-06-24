import base64
import re
from enum import Enum, auto

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsSimpleTextItem,
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform, QTextCursor

from .config import (
    GRID_SIZE, GRID_MAJOR, DEFAULT_ZOOM, snap,
    GRID_MINOR_COLOR, GRID_MAJOR_COLOR,
    JUNCTION_COLOR, JUNCTION_RADIUS,
    COMMAND_COLOR, COMMAND_FONT,
)
from .component_item import ComponentItem, SYMBOL_PREFIX, PIN_POSITIONS, make_ghost
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
    PASTING             = auto()
    DRAWING_LINE        = auto()
    DRAWING_RECT        = auto()
    DRAWING_CIRCLE      = auto()


# ── helpers ──────────────────────────────────────────────────────────────────

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

class SchematicScene(QGraphicsScene):

    placing_started   = Signal()
    placing_cancelled = Signal()
    wire_mode_started = Signal()
    wire_mode_ended   = Signal()
    data_changed      = Signal()   # emitted on every new undo snapshot
    group_move_started = Signal()
    group_move_ended   = Signal()

    def __init__(self):
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.setBackgroundBrush(QColor(255, 255, 255))

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
        self._wire_move_moved:     bool = False
        self._wire_move_rb:        list = []   # [(wire, {idx: orig_QPointF})]
        self._wire_move_junctions: list = []   # [(JunctionItem, orig_QPointF)]
        self._pin_anchors:         list = []   # [(anchor_QPointF, comp, (lx,ly))]
        self._wire_pin_anchors:  list = []   # [(comp, (lx,ly), wire, idx)] — wire ends on a pin
        self._wire_pin_preview_wires: list = []  # preview WireItems for bridge wires during drag

        self._border_pending:   tuple | None = None   # (width, height, show_in_export)
        self._library_pending:  tuple | None = None   # (file_path, directive, simulator, corner)
        self._image_pending:    tuple | None = None   # (file_path, width, height)
        self._latex_pending:    tuple | None = None   # (code, preamble, w, h)
        self._param_pending:    tuple | None = None   # (params, preamble, w, h)
        self._analysis_pending: tuple | None = None   # (source, detector, lgref)
        self._placing_text:     str | None   = None   # text for PLACING_TEXT mode
        self._hyperlink_pending: tuple | None = None  # (url, label)
        self._model_pending:    tuple | None = None   # (name, type, sim, params, preamble, w, h)

        # shape drawing state
        self._draw_kind:   str | None       = None   # "line"|"rect"|"circle"
        self._draw_anchor: QPointF | None   = None   # first click (scene coords)
        self._draw_pts:    list             = []     # accumulated scene pts (polyline)
        self._draw_ghost:  object | None    = None   # preview ShapeItem

        self._clipboard: list[dict] = []
        self._paste_ghost_items: list = []   # [(kind, item, base)]
        self._paste_ref: QPointF | None = None
        self._exporting: bool = False

        self._undo_stack: list = []
        self._redo_stack: list = []
        self._library    = None   # set by from_data; used by _restore

        self._pre_drag_data      = None   # snapshot before vertex/component drag
        self._pre_drag_pos: dict = {}     # item positions at drag start
        self._vdrag_moved        = False  # True once a vertex was actually moved

        self._group_drag_active      = False   # suppresses itemChange rubber-banding
        self._comp_group_move_start: QPointF | None = None
        self._comp_group_move_items: list = []   # [(item, orig_QPointF)]
        self._wire_group_move_data:  list = []   # [(wire, [orig_QPointF, ...])]
        self._comp_group_move_moved  = False

    # ── copy / paste ──────────────────────────────────────────────────────────

    def _copy_selection(self) -> None:
        from .component_item import ComponentItem
        sel = self.selectedItems()
        if not sel:
            return
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
                })

    def _paste_clipboard(self) -> None:
        if not self._clipboard:
            return
        self._start_paste_ghost()

    def _start_paste_ghost(self) -> None:
        """Enter paste-ghost mode: clipboard items follow the cursor, click to place."""
        from PySide6.QtWidgets import QGraphicsSimpleTextItem as _ST
        if not self._clipboard:
            return
        self._end_wire(commit=False)
        self._cancel_placement()   # clears any prior ghost / mode

        # Reference point: first component's position (always on-grid).
        # Using a component origin guarantees delta = snapped_cursor - ref
        # is a multiple of GRID_SIZE, so all pasted components land on-grid.
        ref = None
        for data in self._clipboard:
            if data['kind'] == 'component':
                ref = QPointF(data['x'], data['y'])
                break
        if ref is None:
            # Clipboard has no components; fall back to first item position.
            for data in self._clipboard:
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

        for data in self._clipboard:
            kind = data['kind']
            if kind == 'component':
                ghost = make_ghost(data['svg_bytes'])
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

        self._mode = _Mode.PASTING
        self.placing_started.emit()

    def _commit_paste(self, pos: QPointF) -> None:
        """Place clipboard items at pos and exit paste-ghost mode."""
        for _, item, _ in self._paste_ghost_items:
            if item.scene():
                self.removeItem(item)
        self._paste_ghost_items.clear()

        self._mode = _Mode.NORMAL
        self.placing_cancelled.emit()

        if not self._clipboard or self._paste_ref is None:
            self._paste_ref = None
            return

        delta = pos - self._paste_ref
        self._paste_ref = None

        self._push_undo()
        self.clearSelection()

        for data in self._clipboard:
            kind = data['kind']
            if kind == 'component':
                item = ComponentItem(
                    data['symbol_name'],
                    self._next_id(data['symbol_name']),
                    data['svg_bytes'],
                )
                item.setPos(QPointF(data['x'], data['y']) + delta)
                item.setRotation(data['rotation'])
                item.h_flip       = data['h_flip']
                item.v_flip       = data['v_flip']
                item.apply_transform()
                item.params       = dict(data['params'])
                item.model        = data['model']
                item.refs         = list(data['refs'])
                item.prop_display = {k: tuple(v) for k, v in data['prop_display'].items()}
                item.prop_offsets = {k: list(v) for k, v in data['prop_offsets'].items()}
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
                                    QPointF(data['x'] + delta.x(), data['y'] + delta.y()))
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
                self.addItem(item)
                item.setSelected(True)

        self._sync_junctions()
        self._remove_short_circuit_wires()
        self._sync_junctions()

    # ── placement ─────────────────────────────────────────────────────────────

    def start_placement(self, name: str, svg_bytes: bytes):
        self._end_wire(commit=False)
        self._cancel_placement()
        self._mode         = _Mode.PLACING
        self._placing_name = name
        self._placing_svg  = svg_bytes
        self._ghost        = make_ghost(svg_bytes)
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self.placing_started.emit()

    def cancel_placement(self):
        self._cancel_placement()

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
        self._hyperlink_pending = None
        self._model_pending     = None
        # also cancel any in-progress shape draw
        if self._draw_ghost is not None and self._draw_ghost.scene():
            self.removeItem(self._draw_ghost)
        self._draw_ghost  = None
        self._draw_anchor = None
        self._draw_pts    = []
        self._draw_kind   = None
        self.placing_cancelled.emit()

    def _next_id(self, symbol_name: str) -> str:
        # Number per-PREFIX (not per-symbol): symbols that share a refdes prefix
        # — every subcircuit block uses 'X', and e.g. nmos/pmos both use 'M' —
        # must draw from one counter so their refdes never collide.  from_data
        # seeds these counters with the same key (keep them in sync).
        prefix = SYMBOL_PREFIX.get(symbol_name, "X")
        n = self._counters.get(prefix, 1)
        self._counters[prefix] = n + 1
        return f"{prefix}{n}"

    def start_junction_placement(self):
        self._end_wire(commit=False)
        self._cancel_placement()
        r = JUNCTION_RADIUS
        ghost = QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
        ghost.setPen(QPen(Qt.NoPen))
        ghost.setBrush(QBrush(JUNCTION_COLOR))
        ghost.setOpacity(0.4)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_JUNCTION
        self.placing_started.emit()

    def start_text_placement(self, text: str = "Text"):
        from .config import TEXT_FONT, TEXT_COLOR
        from PySide6.QtGui import QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        self._placing_text = text
        first_line = (text.split('\n')[0] or "Text")[:50]
        ghost = QGraphicsSimpleTextItem(first_line)
        ghost.setFont(TEXT_FONT)
        ghost.setBrush(QBrush(TEXT_COLOR))
        ghost.setOpacity(0.4)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._mode = _Mode.PLACING_TEXT
        self.placing_started.emit()

    def start_hyperlink_placement(self, url: str, label: str):
        from .config import (
            HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE,
            HYPERLINK_COLOR, HYPERLINK_UNDERLINE,
        )
        from PySide6.QtGui import QFont, QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        self._hyperlink_pending = (url, label)
        display = label or url or "hyperlink"
        ghost = QGraphicsSimpleTextItem(display[:50])
        font = QFont(HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE)
        font.setUnderline(HYPERLINK_UNDERLINE)
        ghost.setFont(font)
        ghost.setBrush(QBrush(HYPERLINK_COLOR))
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

    def start_border_placement(self, width: int, height: int, show_in_export: bool):
        self._end_wire(commit=False)
        self._cancel_placement()
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QPen, QBrush, QColor
        ghost = QGraphicsRectItem(0, 0, width, height)
        ghost.setPen(QPen(QColor(80, 80, 180), 0.8, Qt.DashLine))
        ghost.setBrush(QBrush(Qt.NoBrush))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._border_pending = (width, height, show_in_export)
        self._mode = _Mode.PLACING_BORDER
        self.placing_started.emit()

    def start_library_placement(self, file_path: str, directive: str = "lib",
                                simulator: str = "SLiCAP", corner: str = ""):
        from pathlib import Path
        from PySide6.QtWidgets import QGraphicsSimpleTextItem
        from PySide6.QtGui import QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        name = Path(file_path).name if file_path else ""
        ghost_text = f".{directive} {name}"
        if corner:
            ghost_text += f" {corner}"
        ghost = QGraphicsSimpleTextItem(ghost_text)
        ghost.setFont(COMMAND_FONT)
        ghost.setBrush(QBrush(COMMAND_COLOR))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._library_pending = (file_path, directive, simulator, corner)
        self._mode = _Mode.PLACING_LIBRARY
        self.placing_started.emit()

    def start_image_placement(self, file_path: str, width: int, height: int):
        from pathlib import Path as _Path
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPixmap, QPainter as _QPainter
        self._end_wire(commit=False)
        self._cancel_placement()
        w, h = max(1, width), max(1, height)
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
        self._image_pending = (file_path, width, height)
        self._mode = _Mode.PLACING_IMAGE
        self.placing_started.emit()

    def start_latex_placement(self, latex_code: str, preamble_path: str,
                              width: int, height: int):
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPixmap, QPainter as _QPainter
        self._end_wire(commit=False)
        self._cancel_placement()
        from .latex_label import render_latex_raw
        svg_bytes, _ = render_latex_raw(latex_code, preamble_path)
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        renderer = QSvgRenderer(QByteArray(svg_bytes)) if svg_bytes else None
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
        self._latex_pending = (latex_code, preamble_path, width, height)
        self._mode = _Mode.PLACING_LATEX
        self.placing_started.emit()

    def start_parameter_placement(self, params: list, preamble_path: str,
                                   width: int, height: int):
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPixmap, QPainter as _QPainter
        self._end_wire(commit=False)
        self._cancel_placement()
        from .latex_label import render_latex_raw
        from .parameter_item import ParameterItem as _PI
        svg_bytes, _ = render_latex_raw(_PI.build_latex(params), preamble_path)
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        renderer = QSvgRenderer(QByteArray(svg_bytes)) if svg_bytes else None
        w, h = max(1, width), max(1, height)
        if renderer and renderer.isValid():
            px = QPixmap(w, h)
            px.fill(Qt.transparent)
            p = _QPainter(px)
            renderer.render(p)
            p.end()
        else:
            px = QPixmap(w, h)
            px.fill(QColor(200, 225, 255))
        ghost = QGraphicsPixmapItem(px)
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._param_pending = (params, preamble_path, width, height)
        self._mode = _Mode.PLACING_PARAMETER
        self.placing_started.emit()

    def start_analysis_placement(self, source: list, detector: list, lgref: list):
        from PySide6.QtWidgets import QGraphicsSimpleTextItem
        from PySide6.QtGui import QBrush
        self._end_wire(commit=False)
        self._cancel_placement()
        ghost = QGraphicsSimpleTextItem(".source / .detector / .lgref")
        ghost.setFont(COMMAND_FONT)
        ghost.setBrush(QBrush(COMMAND_COLOR))
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
                               preamble_path: str = "",
                               display_width: int = 200, display_height: int = 80):
        self._end_wire(commit=False)
        self._cancel_placement()
        from .latex_label import render_latex_raw
        from .model_item import ModelItem as _MI
        svg_bytes, _ = render_latex_raw(
            _MI.build_latex(model_name, model_type, params), preamble_path)
        if svg_bytes:
            from PySide6.QtWidgets import QGraphicsPixmapItem
            from PySide6.QtGui import QPixmap, QPainter as _QPainter
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QByteArray
            renderer = QSvgRenderer(QByteArray(svg_bytes))
            w, h = max(1, display_width), max(1, display_height)
            if renderer.isValid():
                px = QPixmap(w, h)
                px.fill(Qt.transparent)
                p = _QPainter(px)
                renderer.render(p)
                p.end()
            else:
                px = QPixmap(w, h)
                px.fill(QColor(200, 225, 255))
            ghost = QGraphicsPixmapItem(px)
        else:
            from PySide6.QtWidgets import QGraphicsSimpleTextItem
            from PySide6.QtGui import QBrush
            ghost = QGraphicsSimpleTextItem(f".model {model_name} {model_type}")
            ghost.setFont(COMMAND_FONT)
            ghost.setBrush(QBrush(COMMAND_COLOR))
        ghost.setOpacity(0.5)
        ghost.setAcceptedMouseButtons(Qt.NoButton)
        self._ghost = ghost
        self._ghost.setPos(QPointF(-9999, -9999))
        self.addItem(self._ghost)
        self._model_pending = (model_name, model_type, simulator, params,
                               preamble_path, display_width, display_height)
        self._mode = _Mode.PLACING_MODEL
        self.placing_started.emit()

    # ── shape drawing ─────────────────────────────────────────────────────────

    def start_drawing(self, kind: str) -> None:
        """Enter drawing mode for the given shape kind."""
        self._end_wire(commit=False)
        self._cancel_placement()
        self._cancel_draw()
        self._draw_kind = kind
        mode_map = {
            "line":   _Mode.DRAWING_LINE,
            "rect":   _Mode.DRAWING_RECT,
            "circle": _Mode.DRAWING_CIRCLE,
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
        if self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_RECT,
                           _Mode.DRAWING_CIRCLE):
            self._mode = _Mode.NORMAL
            self.placing_cancelled.emit()

    def _update_draw_ghost(self, scene_pos: QPointF) -> None:
        from .shape_item import ShapeItem
        from . import config as cfg
        color = "#000000"
        lw    = 1.5

        if self._mode == _Mode.DRAWING_LINE:
            pts = self._draw_pts + [scene_pos]
            if len(pts) < 2:
                if self._draw_ghost and self._draw_ghost.scene():
                    self.removeItem(self._draw_ghost)
                    self._draw_ghost = None
                return
            anchor = pts[0]
            rel    = [QPointF(p.x() - anchor.x(), p.y() - anchor.y()) for p in pts]
            kind_g = "line"

        elif self._mode == _Mode.DRAWING_RECT:
            if self._draw_anchor is None:
                return
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
            kind_g = "rect"

        elif self._mode == _Mode.DRAWING_CIRCLE:
            if self._draw_anchor is None:
                return
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
            kind_g = "circle"
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

        if kind == "line":
            pts    = self._draw_pts
            anchor = pts[0]
            rel    = [QPointF(p.x() - anchor.x(), p.y() - anchor.y()) for p in pts]
        elif kind in ("rect", "circle"):
            anchor = self._draw_anchor
            rel    = [QPointF(0, 0),
                      QPointF(scene_pos.x() - anchor.x(),
                              scene_pos.y() - anchor.y())]
        else:
            return

        self._push_undo()
        item = ShapeItem(kind, rel, pos=anchor)   # all style fields use defaults
        self.addItem(item)
        self._cancel_draw()
        self.start_drawing(kind)

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
        self._wire_pin_preview_wires = []
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

        Any unselected wire endpoint coinciding with an old anchor position is
        moved to the new position.  Must be called before state variables are cleared.
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
            for lx, ly in PIN_POSITIONS.get(item.symbol_name, []):
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
            for lx, ly in PIN_POSITIONS.get(other_item.symbol_name, []):
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

        # Stretch unselected wire endpoints that sit on an old anchor position.
        for wire in self.items():
            if not isinstance(wire, WireItem) or id(wire) in moved_wire_ids:
                continue
            changed = False
            for i, pt in enumerate(wire.points):
                new_pt = anchor_map.get(_pt_key(pt))
                if new_pt is not None:
                    wire.points[i] = QPointF(new_pt)
                    changed = True
            if changed:
                wire._rebuild()

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
        from .component_item import PIN_POSITIONS

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
            for lx, ly in PIN_POSITIONS.get(comp.symbol_name, []):
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
            for lx, ly in PIN_POSITIONS.get(comp.symbol_name, []):
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
        from .schematic_data import SchematicData, ComponentData, WireData, JunctionData, FreeTextData, CommandData, BorderData, LibraryData, ImageData, LatexFragmentData, ParameterData, AnalysisData, HyperlinkData, ModelData
        comps, wires, junctions, free_texts, commands, libs, images, latex_frags, param_items, analysis_items, hyperlinks, shapes, model_defs = [], [], [], [], [], [], [], [], [], [], [], [], []
        border_data = None
        for item in self.items():
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
                ))
            elif isinstance(item, JunctionItem):
                junctions.append(JunctionData(x=item.pos().x(), y=item.pos().y()))
            elif isinstance(item, FreeTextItem):
                free_texts.append(FreeTextData(
                    x=item.pos().x(), y=item.pos().y(),
                    text=item.toPlainText(),
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
                )
            elif isinstance(item, LibraryItem):
                libs.append(LibraryData(
                    x=item.pos().x(), y=item.pos().y(),
                    file_path=item.file_path,
                    directive=item.directive,
                    simulator=item.simulator,
                    corner=item.corner,
                ))
            elif isinstance(item, ImageItem):
                images.append(ImageData(
                    x=item.pos().x(), y=item.pos().y(),
                    file_path=item.file_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                ))
            elif isinstance(item, LatexFragmentItem):
                latex_frags.append(LatexFragmentData(
                    x=item.pos().x(), y=item.pos().y(),
                    latex_code=item.latex_code,
                    preamble_path=item.preamble_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                ))
            elif isinstance(item, ParameterItem):
                param_items.append(ParameterData(
                    x=item.pos().x(), y=item.pos().y(),
                    params=[list(p) for p in item.params],
                    preamble_path=item.preamble_path,
                    display_width=item.display_width,
                    display_height=item.display_height,
                ))
            elif isinstance(item, AnalysisItem):
                analysis_items.append(AnalysisData(
                    x=item.pos().x(), y=item.pos().y(),
                    source=list(item.source),
                    detector=[list(d) for d in item.detector],
                    lgref=list(item.lgref),
                ))
            elif isinstance(item, HyperlinkItem):
                hyperlinks.append(HyperlinkData(
                    x=item.pos().x(), y=item.pos().y(),
                    url=item.url, label=item.label,
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
                ))
            elif isinstance(item, ShapeItem):
                from .schematic_data import ShapeData
                shapes.append(ShapeData(
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
                ))
        return SchematicData(components=comps, wires=wires,
                             junctions=junctions, free_texts=free_texts,
                             commands=commands, libs=libs, images=images,
                             border=border_data, latex_fragments=latex_frags,
                             parameters=param_items, analysis_items=analysis_items,
                             hyperlinks=hyperlinks, shapes=shapes,
                             model_defs=model_defs)

    def from_data(self, data, library) -> None:
        """Populate the scene from a SchematicData object."""
        self._library = library
        self.reset()
        for cd in data.components:
            svg = library.svg_bytes(cd.symbol_name)
            if svg is None:
                continue
            item = ComponentItem(cd.symbol_name, cd.instance_id, svg)
            # __init__ creates a "refdes" label at the default position.
            # Clear it now so _save_label_offsets() inside update_labels()
            # below does not overwrite the prop_offsets we are about to restore.
            for _lbl in list(item._labels.values()):
                _lbl.setParentItem(None)
            item._labels.clear()
            item.setPos(QPointF(cd.x, cd.y))
            item.setRotation(cd.rotation)
            item.h_flip       = cd.h_flip
            item.v_flip       = cd.v_flip
            item.apply_transform()
            item.params       = dict(cd.params)
            item.model        = cd.model
            item.refs         = list(cd.refs)
            item.prop_display = {k: tuple(v) for k, v in cd.prop_display.items()}
            item.prop_offsets = {k: tuple(v) for k, v in cd.prop_offsets.items()}
            # Backfill defaults for power symbols saved without net name (old files)
            if cd.symbol_name in ("0", "port"):
                item.params.setdefault("name", "0" if cd.symbol_name == "0" else "")
                item.prop_display.setdefault("name", (True, False))
            item.update_labels()
            self.addItem(item)
            # Keep counters above highest loaded number — keyed by PREFIX, to
            # match _next_id (otherwise X / M counters reset and refdes collide).
            prefix = SYMBOL_PREFIX.get(cd.symbol_name, "X")
            m = re.match(rf"^{re.escape(prefix)}(\d+)$", cd.instance_id)
            if m:
                n = int(m.group(1))
                self._counters[prefix] = max(self._counters.get(prefix, 1), n + 1)

        for wd in data.wires:
            wire = WireItem([QPointF(x, y) for x, y in wd.points])
            wire.net_name       = wd.net_name
            wire.display_name   = wd.display_name
            wire.label_offset   = QPointF(*wd.label_offset)
            wire.net_locked     = wd.net_locked
            wire._user_net_name = wd.user_net_name
            self.addItem(wire)
            wire.update_label()

        for jd in data.junctions:
            self.addItem(JunctionItem(QPointF(jd.x, jd.y)))

        for td in data.free_texts:
            self.addItem(FreeTextItem(td.text, QPointF(td.x, td.y)))

        for cd in data.commands:
            self.addItem(CommandItem(cd.text, QPointF(cd.x, cd.y)))

        for ld in data.libs:
            self.addItem(LibraryItem(ld.file_path, QPointF(ld.x, ld.y),
                                     ld.directive, ld.simulator, ld.corner))

        for img in data.images:
            self.addItem(ImageItem(img.file_path, img.display_width,
                                   img.display_height, QPointF(img.x, img.y)))

        for frag in data.latex_fragments:
            self.addItem(LatexFragmentItem(
                frag.latex_code, frag.preamble_path,
                frag.display_width, frag.display_height,
                QPointF(frag.x, frag.y),
            ))

        for pd in data.parameters:
            self.addItem(ParameterItem(
                [tuple(p) for p in pd.params], pd.preamble_path,
                pd.display_width, pd.display_height,
                QPointF(pd.x, pd.y),
            ))

        for ad in data.analysis_items:
            self.addItem(AnalysisItem(ad.source, ad.detector, ad.lgref,
                                      QPointF(ad.x, ad.y)))

        for hd in data.hyperlinks:
            self.addItem(HyperlinkItem(hd.url, hd.label, QPointF(hd.x, hd.y)))

        for sd in data.shapes:
            self.addItem(ShapeItem(
                kind=sd.kind,
                rel_points=[QPointF(px, py) for px, py in sd.rel_points],
                stroke_color=sd.stroke_color,
                fill_color=sd.fill_color,
                fill_style=sd.fill_style,
                line_style=sd.line_style,
                line_end_start=sd.line_end_start,
                line_end_end=sd.line_end_end,
                line_width=sd.line_width,
                pos=QPointF(sd.x, sd.y),
            ))

        for md in data.model_defs:
            self.addItem(ModelItem(
                md.model_name, md.model_type, md.simulator,
                [list(p) for p in md.params],
                md.preamble_path,
                md.display_width, md.display_height,
                QPointF(md.x, md.y),
            ))

        if data.border is not None:
            bd = data.border
            self.addItem(BorderItem(bd.x, bd.y, bd.width, bd.height, bd.show_in_export))

        self._sync_junctions()

    # ── scene events ─────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        pos = snap(event.scenePos())

        if self._mode == _Mode.PLACING and event.button() == Qt.LeftButton:
            self._push_undo()
            item = ComponentItem(
                self._placing_name,
                self._next_id(self._placing_name),
                self._placing_svg,
            )
            item.setPos(pos)
            self.addItem(item)
            self._sync_junctions()
            self._remove_short_circuit_wires()
            self._sync_junctions()

        elif self._mode == _Mode.PLACING_JUNCTION and event.button() == Qt.LeftButton:
            self._push_undo()
            self.addItem(JunctionItem(pos))
            self._sync_junctions()

        elif self._mode == _Mode.PLACING_TEXT and event.button() == Qt.LeftButton:
            self._push_undo()
            item = FreeTextItem(self._placing_text or "Text", pos)
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
            w, h, show = self._border_pending
            self.addItem(BorderItem(pos.x(), pos.y(), w, h, show))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_LIBRARY and event.button() == Qt.LeftButton:
            self._push_undo()
            fp, directive, simulator, corner = self._library_pending
            self.addItem(LibraryItem(fp, pos, directive, simulator, corner))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_IMAGE and event.button() == Qt.LeftButton:
            self._push_undo()
            fp, w, h = self._image_pending
            self.addItem(ImageItem(fp, w, h, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_LATEX and event.button() == Qt.LeftButton:
            self._push_undo()
            lc, pp, w, h = self._latex_pending
            self.addItem(LatexFragmentItem(lc, pp, w, h, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_PARAMETER and event.button() == Qt.LeftButton:
            self._push_undo()
            prms, pp, w, h = self._param_pending
            self.addItem(ParameterItem(prms, pp, w, h, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_ANALYSIS and event.button() == Qt.LeftButton:
            self._push_undo()
            src, det, lgr = self._analysis_pending
            self.addItem(AnalysisItem(src, det, lgr, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PLACING_MODEL and event.button() == Qt.LeftButton:
            self._push_undo()
            mn, mt, sim, prms, pp, w, h = self._model_pending
            self.addItem(ModelItem(mn, mt, sim, prms, pp, w, h, pos))
            self._cancel_placement()

        elif self._mode == _Mode.PASTING and event.button() == Qt.LeftButton:
            self._commit_paste(pos)

        elif self._mode in (_Mode.DRAWING_RECT, _Mode.DRAWING_CIRCLE) and event.button() == Qt.LeftButton:
            if self._draw_anchor is None:
                self._draw_anchor = snap(pos)
            else:
                self._commit_shape(snap(pos))

        elif self._mode == _Mode.DRAWING_LINE and event.button() == Qt.LeftButton:
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
                item = self.itemAt(raw, QTransform())
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
                            for lx, ly in PIN_POSITIONS.get(comp.symbol_name, []):
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
                        wire.setZValue(1)
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
                            for lx, ly in PIN_POSITIONS.get(comp.symbol_name, []):
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
                    for lx, ly in PIN_POSITIONS.get(item.symbol_name, []):
                        p = item.mapToScene(QPointF(lx, ly))
                        pk = _pt_key(p)
                        if pk in others:
                            self._pin_anchors.append((others[pk], item, (lx, ly)))
                # snapshot before potential component/text/junction/border move
                self._pre_drag_data = self.to_data()
                self._pre_drag_pos  = {
                    id(i): (i.pos().x(), i.pos().y())
                    for i in self.items()
                    if isinstance(i, (ComponentItem, FreeTextItem, CommandItem,
                                      JunctionItem, BorderItem,
                                      LibraryItem, ImageItem, LatexFragmentItem, ParameterItem,
                                      AnalysisItem, HyperlinkItem, ModelItem))
                }
                # Custom group drag: intercept multi-item non-wire selections so
                # rubber-banding runs after all items have moved (not per-item in itemChange).
                if (item is not None and item.isSelected()
                        and not isinstance(item, WireItem)):
                    non_wire_sel = [
                        i for i in self.selectedItems()
                        if isinstance(i, (ComponentItem, FreeTextItem, CommandItem,
                                          JunctionItem, BorderItem, LibraryItem,
                                          ImageItem, LatexFragmentItem, ParameterItem,
                                          AnalysisItem, HyperlinkItem, ShapeItem, ModelItem))
                    ]
                    if len(non_wire_sel) > 1:
                        self._comp_group_move_start = snap(raw)
                        self._comp_group_move_items = [
                            (i, QPointF(i.pos())) for i in non_wire_sel
                        ]
                        # Store original positions of every point of every selected wire
                        self._wire_group_move_data = [
                            (w, [QPointF(p) for p in w.points])
                            for w in self.selectedItems()
                            if isinstance(w, WireItem)
                        ]
                        self._comp_group_move_moved = False
                        self._pin_anchors = []   # group move: no bridge wires needed
                        self.group_move_started.emit()
                        return
            elif event.button() == Qt.RightButton:
                item = self.itemAt(raw, QTransform())
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
            dlg = HyperlinkDialog(item.url, item.label)
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
        dlg = NetLabelDialog(canon_name, canon_display, locked=wire.net_locked)
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
            for w in net_wires:
                w.update_label()

    def mouseMoveEvent(self, event):
        pos = snap(event.scenePos())

        if (self._mode in (_Mode.PLACING, _Mode.PLACING_JUNCTION,
                           _Mode.PLACING_TEXT, _Mode.PLACING_COMMAND,
                           _Mode.PLACING_BORDER, _Mode.PLACING_LIBRARY,
                           _Mode.PLACING_IMAGE, _Mode.PLACING_LATEX,
                           _Mode.PLACING_PARAMETER, _Mode.PLACING_ANALYSIS,
                           _Mode.PLACING_HYPERLINK, _Mode.PLACING_MODEL)
                and self._ghost is not None):
            self._ghost.setPos(pos)

        elif self._mode == _Mode.WIRING:
            self._refresh_preview(pos)

        elif self._mode in (_Mode.DRAWING_LINE, _Mode.DRAWING_RECT,
                             _Mode.DRAWING_CIRCLE):
            self._update_draw_ghost(snap(event.scenePos()))

        elif self._mode == _Mode.PASTING:
            if self._paste_ghost_items and self._paste_ref is not None:
                delta = pos - self._paste_ref
                for kind, item, base in self._paste_ghost_items:
                    if kind == 'point':
                        item.setPos(base + delta)
                    else:
                        item.setPath(_build_path([p + delta for p in base]))

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
                other_item.setPos(snap(QPointF(ox + delta.x(), oy + delta.y())))
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
            total_delta = pos - self._comp_group_move_start
            if total_delta.x() != 0 or total_delta.y() != 0:
                self._comp_group_move_moved = True
            # Capture old anchor positions BEFORE moving (item.pos() is still old)
            old_anchor_to_delta: dict = {}
            for itm, orig_pos in self._comp_group_move_items:
                new_pos = snap(orig_pos + total_delta)
                step_delta = new_pos - itm.pos()
                if not (step_delta.x() or step_delta.y()):
                    continue
                if isinstance(itm, ComponentItem):
                    for pin_pt in itm.pin_scene_pos():
                        old_anchor_to_delta[_pt_key(pin_pt)] = step_delta
                elif isinstance(itm, JunctionItem):
                    old_anchor_to_delta[_pt_key(itm.pos())] = step_delta
            # Move all items with rubber-banding suppressed in ItemPositionHasChanged
            self._group_drag_active = True
            for itm, orig_pos in self._comp_group_move_items:
                itm.setPos(snap(orig_pos + total_delta))
            self._group_drag_active = False

            # Selected wires: recompute ALL points from their stored originals.
            if self._comp_group_move_items:
                ref_itm, ref_orig = self._comp_group_move_items[0]
                snap_delta = snap(ref_orig + total_delta) - ref_orig
            else:
                snap_delta = QPointF(0, 0)

            for w, orig_pts in self._wire_group_move_data:
                if w.scene() is None:
                    continue
                for i, op in enumerate(orig_pts):
                    w.points[i] = op + snap_delta
                w._rebuild()

            # Unselected wires: rubber-band endpoints at moving anchors.
            sel_wire_ids = {id(w) for w, _ in self._wire_group_move_data}
            for w in self.items():
                if not isinstance(w, WireItem) or id(w) in sel_wire_ids:
                    continue
                changed = False
                for i, pt in enumerate(w.points):
                    delta = old_anchor_to_delta.get(_pt_key(pt))
                    if delta is not None:
                        w.points[i] = pt + delta
                        changed = True
                if changed:
                    w._rebuild()

        else:
            super().mouseMoveEvent(event)

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
            if self._wire_move_start is not None:
                # Remove bridge-wire previews before any geometry operations.
                for pw in self._wire_pin_preview_wires:
                    if pw.scene() is not None:
                        self.removeItem(pw)
                self._wire_pin_preview_wires = []
                # Restore Z-values that were raised at drag-start.
                for wire in self._wire_move_wires:
                    if wire.scene() is not None:
                        wire.setZValue(0)
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
                self._vdrag_wire        = None
                self._vdrag_idx         = None
                self._vdrag_rb          = []
                self._vdrag_pin_anchor  = None
                self._vdrag_pin_preview = None
                return
            if self._comp_group_move_start is not None:
                if self._comp_group_move_moved:
                    self._push_snapshot(self._pre_drag_data)
                    self._reconnect_after_move()
                    for anchor, comp, local_xy in self._pin_anchors:
                        if comp.scene() is not None:
                            new_pin = comp.mapToScene(QPointF(*local_xy))
                            if _pt_key(new_pin) != _pt_key(anchor):
                                self.addItem(WireItem(_elbow(anchor, new_pin, True)))
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                self._comp_group_move_start = None
                self._comp_group_move_items = []
                self._wire_group_move_data  = []
                self._comp_group_move_moved = False
                self._pre_drag_data = None
                self._pre_drag_pos  = {}
                self._pin_anchors   = []
                self.group_move_ended.emit()
                return
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            if self._pre_drag_data is not None:
                moved = any(
                    (i.pos().x(), i.pos().y()) != self._pre_drag_pos.get(id(i))
                    for i in self.items()
                    if isinstance(i, (ComponentItem, FreeTextItem, CommandItem,
                                      JunctionItem, BorderItem,
                                      LibraryItem, ImageItem, LatexFragmentItem, ParameterItem,
                                      AnalysisItem, ModelItem))
                    and id(i) in self._pre_drag_pos
                )
                if moved:
                    self._push_snapshot(self._pre_drag_data)
                    self._reconnect_after_move()
                    for anchor, comp, local_xy in self._pin_anchors:
                        if comp.scene() is not None:
                            new_pin = comp.mapToScene(QPointF(*local_xy))
                            if _pt_key(new_pin) != _pt_key(anchor):
                                self.addItem(WireItem(_elbow(anchor, new_pin, True)))
                    self._sync_junctions()
                    self._remove_short_circuit_wires()
                    self._sync_junctions()
                self._pin_anchors = []
            self._pre_drag_data = None
            self._pre_drag_pos  = {}

    def mouseDoubleClickEvent(self, event):
        if self._mode == _Mode.DRAWING_LINE and event.button() == Qt.LeftButton:
            # The first click of the double-click already added the final point
            # via mousePressEvent; commit if we have at least 2 points.
            if len(self._draw_pts) >= 2:
                self._commit_shape(self._draw_pts[-1])
            return
        if self._mode != _Mode.NORMAL:
            super().mouseDoubleClickEvent(event)
            return
        if event.button() != Qt.LeftButton:
            return
        item = self.itemAt(event.scenePos(), QTransform())
        # BorderItem.shape() covers only the edge; itemAt() misses interior
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
            r = item.rect()
            dlg = BorderDialog(
                width=int(r.width()),
                height=int(r.height()),
                show_in_export=item.show_in_export,
            )
            if dlg.exec():
                self._push_undo()
                item.setRect(0, 0, dlg.border_width(), dlg.border_height())
                item.show_in_export = dlg.show_in_export()
            return
        if isinstance(item, LibraryItem):
            from .library_link_dialog import LibraryLinkDialog
            dlg = LibraryLinkDialog(
                directive=item.directive,
                simulator=item.simulator,
                file_path=item.file_path,
                corner=item.corner,
            )
            if dlg.exec() and dlg.file_path():
                self._push_undo()
                item.file_path  = dlg.file_path()
                item.directive  = dlg.directive()
                item.simulator  = dlg.simulator()
                item.corner     = dlg.corner()
                item._update_text()
            return
        if isinstance(item, ImageItem):
            from .image_dialog import ImageDialog
            dlg = ImageDialog(
                file_path=item.file_path,
                display_width=item.display_width,
                display_height=item.display_height,
            )
            if dlg.exec() and dlg.image_path():
                self._push_undo()
                item.file_path      = dlg.image_path()
                item.display_width  = dlg.image_width()
                item.display_height = dlg.image_height()
                item.prepareGeometryChange()
                item._load()
            return
        if isinstance(item, LatexFragmentItem):
            from .latex_fragment_dialog import LatexFragmentDialog
            dlg = LatexFragmentDialog(
                latex_code=item.latex_code,
                preamble_path=item.preamble_path,
                svg_bytes=item._svg_bytes,
                display_width=item.display_width,
                display_height=item.display_height,
            )
            if dlg.exec() and dlg.svg_bytes():
                self._push_undo()
                item.latex_code    = dlg.latex_code()
                item.preamble_path = dlg.preamble_path()
                item.display_width  = dlg.display_width()
                item.display_height = dlg.display_height()
                item._load_renderer()
                item.prepareGeometryChange()
                item.update()
            return
        if isinstance(item, ParameterItem):
            from .parameter_dialog import ParameterDialog
            dlg = ParameterDialog(
                params=item.params,
                preamble_path=item.preamble_path,
                svg_bytes=item._svg_bytes,
                display_width=item.display_width,
                display_height=item.display_height,
            )
            if dlg.exec():
                self._push_undo()
                item.prepareGeometryChange()
                item.params        = dlg.get_params()
                item.preamble_path = dlg.preamble_path()
                item.display_width  = dlg.display_width()
                item.display_height = dlg.display_height()
                item._load_renderer()
                item.update()
            return
        if isinstance(item, AnalysisItem):
            from .analysis_dialog import AnalysisDialog
            dlg = AnalysisDialog(
                source=item.source,
                detector=item.detector,
                lgref=item.lgref,
            )
            if dlg.exec():
                self._push_undo()
                item.source   = dlg.get_source()
                item.detector = dlg.get_detector()
                item.lgref    = dlg.get_lgref()
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
                svg_bytes=item._svg_bytes,
                display_width=item.display_width,
                display_height=item.display_height,
            )
            if dlg.exec():
                self._push_undo()
                item.model_name    = dlg.model_name()
                item.model_type    = dlg.model_type()
                item.simulator     = dlg.simulator()
                item.params        = dlg.get_params()
                item.preamble_path = dlg.preamble_path()
                item.display_width  = dlg.display_width()
                item.display_height = dlg.display_height()
                item._load_renderer()
                item.prepareGeometryChange()
                item.update()
            return
        if isinstance(item, FreeTextItem):
            from .text_dialog import TextDialog
            dlg = TextDialog(item.toPlainText())
            if dlg.exec():
                self._push_undo()
                item.setPlainText(dlg.text())
            return
        if isinstance(item, HyperlinkItem):
            from .hyperlink_dialog import HyperlinkDialog
            dlg = HyperlinkDialog(item.url, item.label)
            if dlg.exec():
                self._push_undo()
                item.url   = dlg.url()
                item.label = dlg.label()
                item.setText(item.label or item.url)
            return
        if isinstance(item, ShapeItem):
            from .shape_dialog import ShapeDialog
            dlg = ShapeDialog(item)
            if dlg.exec():
                self._push_undo()
                item.stroke_color   = dlg.get_stroke_color()
                item.line_width     = dlg.get_line_width()
                item.line_style     = dlg.get_line_style()
                item.line_end_start = dlg.get_line_end_start()
                item.line_end_end   = dlg.get_line_end_end()
                item.fill_style     = dlg.get_fill_style()
                item.fill_color     = dlg.get_fill_color()
                item.update()
            return
        if isinstance(item, WireItem):
            self._open_net_label(item)
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
                from .properties_dialog import PropertiesDialog
                dlg = PropertiesDialog(item)
                result = dlg.exec()
                if dlg.descend_path() is not None:
                    # Open the subcircuit's schematic in a new editable window so
                    # deeper hierarchies stay navigable.
                    win = self.views()[0].window() if self.views() else None
                    if win is not None and hasattr(win, "open_subschematic"):
                        win.open_subschematic(dlg.descend_path())
                elif result:
                    self._push_undo()
                    dlg.apply()
        else:
            super().mouseDoubleClickEvent(event)

    # ── grid background ───────────────────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        if self._exporting:
            return

        left   = int(rect.left())   - (int(rect.left())   % GRID_SIZE)
        top    = int(rect.top())    - (int(rect.top())    % GRID_SIZE)
        right  = int(rect.right())
        bottom = int(rect.bottom())

        minor_pen = QPen(GRID_MINOR_COLOR, 0)
        major_pen = QPen(GRID_MAJOR_COLOR, 0)

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


def _rb_keep_item(item, scene_rect: QRectF, contains: bool) -> bool:
    """
    Return True if item should stay selected given scene_rect and mode.

    contains=True  → right-to-left drag: item must be fully inside scene_rect.
    contains=False → left-to-right drag: item must intersect scene_rect.

    Uses tight per-type rects so that label bounding boxes on components and
    wires don't trigger selection when the rubber-band is far from the body.
    """
    from .component_item import ComponentItem, SYMBOL_TIGHT_RECT
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
        tight = SYMBOL_TIGHT_RECT.get(item.symbol_name)
        local_rect = QRectF(*tight) if tight else QRectF(-30, -30, 60, 60)
        item_rect = item.mapRectToScene(local_rect)
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
        scene.placing_cancelled.connect(self._on_normal_mode)
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
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)

    def _on_normal_mode(self):
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.unsetCursor()

    # ── zoom ─────────────────────────────────────────────────────────────────

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(1 / 1.25, 1 / 1.25)

    def zoom_reset(self):
        self.resetTransform()
        self.scale(DEFAULT_ZOOM, DEFAULT_ZOOM)
        r = self.scene().itemsBoundingRect()
        self.centerOn(r.center() if not r.isNull() else QPointF(0, 0))

    def zoom_fit(self):
        """Fit all scene items in the viewport with a small margin."""
        r = self.scene().itemsBoundingRect()
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
            if (event.buttons() & Qt.LeftButton and self._rb_start is not None):
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
            if scene._mode == _Mode.DRAWING_LINE:
                # Commit if we have a valid line; otherwise just cancel
                if len(scene._draw_pts) >= 2:
                    scene._commit_shape(scene._draw_pts[-1])
                else:
                    scene._cancel_draw()
            elif scene._mode in (_Mode.DRAWING_RECT, _Mode.DRAWING_CIRCLE):
                scene._cancel_draw()
            elif scene._mode == _Mode.WIRING:
                scene.finish_wire()
            else:
                scene.cancel_placement()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if scene._mode == _Mode.DRAWING_LINE and len(scene._draw_pts) >= 2:
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
            if scene.selectedItems():
                scene._push_undo()
            for item in scene.selectedItems():
                item.setRotation(item.rotation() + 90)
        elif key == Qt.Key_M:
            sel = [i for i in scene.selectedItems() if isinstance(i, ComponentItem)]
            if sel:
                scene._push_undo()
                for item in sel:
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
                    scene.removeItem(item)
                scene._sync_junctions()
        elif key == Qt.Key_V and mods & Qt.ControlModifier:
            scene._paste_clipboard()
        else:
            super().keyPressEvent(event)
