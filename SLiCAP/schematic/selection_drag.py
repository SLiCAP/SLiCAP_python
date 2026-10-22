"""
One drag of the selection, owned by the scene (Anton, 2026-10-21/22).

Before 6.4.1 four engines moved things. Qt's ``ItemIsMovable`` machinery
dragged a single item, and the component's and the junction's
``itemChange`` rubber-banded their wires on EVERY position change, also
on a ``setPos`` from code (undo, paste, a group transform), which a scene
flag then had to silence. The scene dragged a group, a wire by its body
and a net label, each with its own bookkeeping. Every rule (the junction
dots that follow, the bridge preview of a point pulled off a pin, the
labels in a group) had to be added to each engine, and they disagreed:
a wire moved by its body left a T-connection on its interior behind, a
net-label move had no undo step, only a wire-body drag reselected the
wires that a merge had replaced. Anton (2026-10-22) chose the general
rule for all of them.

The scene takes every plain press on a draggable item (``draggable``)
and builds ONE ``SelectionDrag`` over the selection. The press is
accepted and never delivered to Qt, so Qt's movable machinery never
runs and the view starts no rubber band; ``ItemIsMovable`` stays as the
declaration "the scene drags this item" (``canvas._undo_tracked``). A
press that is an item's own gesture - a border edge, a handle of a
selected shape, a text being edited - goes to Qt as before
(``takes_own_press``).

What moves, from the selection at press:

- members: the top-level movable items that are not wires, from their
  original positions;
- labels: selected labels (of a component or of a wire) whose parent is
  NOT selected, by the same delta in the parent's frame; a label of a
  selected parent rides with it;
- wires: the selected wires, every point.

Captured ONCE at press from the originals, never re-detected during the
drag (re-detection against the current pin positions was tried and
REVERTED on 2026-09-25: a pin passing over a foreign wire end stole it):

- anchors: the pins of the moving components, the positions of the
  moving junctions, every point of a selected wire;
- followers: the points of unselected wires on an anchor, and the
  unselected junction dots there, which follow the drag;
- bridges: a moving point (a pin of a moving component, a point of a
  selected wire, a moving junction) that sits on a pin of a NON-moving
  component. A dashed preview shows the bridge during the drag. At
  release one bridge wire per pin/point pair connects the pin to where
  the point ended, so a drag never silently disconnects a pin. "A group
  move needs no bridges" was the earlier assumption and was WRONG
  (2026-10-08).

The delta is ONE grid-aware step from the originals (Anton, 2026-09-27):
"grid" when a member is grid-critical or a wire moves, or a gridded
member moves without Shift; "fine" for gridded members under Shift;
"free" when only annotations and labels move. Start and pointer are
snapped in that mode, so grid items stay on grid and annotations keep
their fractional positions. Snapping each item's new position instead
made every annotation in a group jump onto the grid at the first step.

The pressed item is told ``drag_started()`` / ``drag_ended()`` when it
has them: a label shows its leader line meanwhile, a component clears
its focused label. Those are the item's own feedback; the engine only
says when.
"""
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem

from .config import Z_WIRE, Z_WIRE_DRAG, shift_held, snap, snap_fine


def _label_classes() -> tuple:
    from .component_item import _PropertyLabel
    from .wire_item import _DCLabel, _NetLabel
    return (_PropertyLabel, _NetLabel, _DCLabel)


def draggable(item) -> bool:
    """The scene drags *item* on a plain press: a wire, a label (a child
    of a component or of a wire) or a top-level movable item. A preview
    (a paste ghost, a dashed bridge) never."""
    from .wire_item import WireItem
    if item is None or getattr(item, "_preview", False):
        return False
    if isinstance(item, (WireItem,) + _label_classes()):
        return True
    return (item.parentItem() is None
            and bool(item.flags() & QGraphicsItem.ItemIsMovable))


def takes_own_press(item, scene_pos: QPointF) -> bool:
    """The press at *scene_pos* is the item's own gesture, not a move: the
    item says so through ``owns_press`` (BorderItem: an edge to resize,
    ShapeItem: a handle of a selected shape), or it is a text being
    edited, which is Qt's own state. Such a press is delivered to Qt."""
    owns = getattr(item, "owns_press", None)
    if owns is not None and owns(scene_pos):
        return True
    return (isinstance(item, QGraphicsTextItem)
            and item.textInteractionFlags() != Qt.NoTextInteraction)


def _dashed(points: list):
    """A dashed preview wire: never serialised, undone or dragged."""
    from .wire_item import WireItem
    pw = WireItem([QPointF(p) for p in points])
    pen = pw.pen()
    pen.setStyle(Qt.DashLine)
    pw.setPen(pen)
    pw._preview = True
    return pw


class SelectionDrag:
    """One drag of the scene's selection: built on press, driven by
    ``move`` on every mouse move, ended by ``finish`` on release (or
    ``cancel`` when the scene is reset meanwhile). See the module."""

    def __init__(self, scene, press_pos: QPointF, pressed=None):
        from .canvas import _pt_key, _undo_tracked
        from .component_item import ComponentItem
        from .junction_item import JunctionItem
        from .wire_item import WireItem
        self.scene = scene
        self.pressed = pressed
        self.delta = QPointF(0, 0)
        self.snapshot = scene.to_data()          # the undo step, pushed at release

        labels = _label_classes()
        selected = scene.selectedItems()
        self.members = [(i, QPointF(i.pos())) for i in selected
                        if _undo_tracked(i) and not isinstance(i, labels)]
        self.labels = [(lbl, lbl.parentItem().mapToScene(lbl.pos()))
                       for lbl in selected
                       if isinstance(lbl, labels) and lbl.parentItem() is not None
                       and not lbl.parentItem().isSelected()]
        self.wires = [(w, [QPointF(p) for p in w.points]) for w in selected
                      if isinstance(w, WireItem) and not getattr(w, "_preview", False)]

        critical = (any(getattr(i, "GRID_CRITICAL", False) for i, _ in self.members)
                    or bool(self.wires))
        gridded = any(getattr(i, "SNAPS_TO_GRID", True) for i, _ in self.members)
        self.mode = ("grid" if critical or (gridded and not shift_held())
                     else "fine" if gridded else "free")
        self.start = self._snapped(press_pos)

        moving = {id(i) for i, _ in self.members}
        moving_wires = {id(w) for w, _ in self.wires}
        # every component pin in the scene, by position
        pins: dict = {}
        for comp in scene.items():
            if isinstance(comp, ComponentItem):
                for lx, ly in comp.pin_positions():
                    k = _pt_key(comp.mapToScene(QPointF(lx, ly)))
                    pins.setdefault(k, []).append((comp, (lx, ly)))
        # the moving points: (source, position), see _moving_point
        sources: list = []
        for i, _ in self.members:
            if isinstance(i, ComponentItem):
                sources += [(("pin", i, (lx, ly)), i.mapToScene(QPointF(lx, ly)))
                            for lx, ly in i.pin_positions()]
            elif isinstance(i, JunctionItem):
                sources.append((("item", i, None), i.pos()))
        for w, pts in self.wires:
            sources += [(("wire", w, idx), pts[idx]) for idx in {0, len(pts) - 1}]
        anchors = {_pt_key(p) for _, p in sources}
        for w, pts in self.wires:
            anchors.update(_pt_key(p) for p in pts)

        self.followers = [(w, idx, QPointF(p)) for w in scene.items()
                          if isinstance(w, WireItem) and id(w) not in moving_wires
                          and not getattr(w, "_preview", False)
                          for idx, p in enumerate(w.points) if _pt_key(p) in anchors]
        self.dots = [(j, QPointF(j.pos())) for j in scene.items()
                     if isinstance(j, JunctionItem) and id(j) not in moving
                     and _pt_key(j.pos()) in anchors]
        self.bridges = [(comp, local, src) for src, p in sources
                        for comp, local in pins.get(_pt_key(p), [])
                        if id(comp) not in moving]
        self.previews = []
        for _, _, src in self.bridges:
            pt = self._moving_point(src)
            pw = _dashed([pt, pt])
            scene.addItem(pw)
            self.previews.append(pw)

        # the moved wires above their followers, so their handles stay visible
        for w, _ in self.wires:
            w.setZValue(Z_WIRE_DRAG)
        started = getattr(pressed, "drag_started", None)
        if started is not None:
            started()

    # ── helpers ───────────────────────────────────────────────────────────

    def _snapped(self, raw: QPointF) -> QPointF:
        if self.mode == "grid":
            return snap(raw)
        if self.mode == "fine":
            return snap_fine(raw)
        return QPointF(raw)

    @staticmethod
    def _moving_point(src) -> "QPointF | None":
        """Current scene position of a moving point: ("wire", wire, idx) a
        point of a selected wire, ("pin", comp, local) a pin of a moving
        component, ("item", junction, None) a moving junction. None once
        the item is gone."""
        kind, item, ref = src
        if item.scene() is None:
            return None
        if kind == "wire":
            return QPointF(item.points[ref]) if ref < len(item.points) else None
        if kind == "pin":
            return item.mapToScene(QPointF(*ref))
        return QPointF(item.pos())

    # ── the gesture ───────────────────────────────────────────────────────

    def move(self, raw: QPointF) -> None:
        """Everything by ONE delta from its original."""
        from .canvas import _elbow
        delta = self._snapped(raw) - self.start
        self.delta = delta
        for item, orig in self.members:
            if item.scene() is not None:
                item.setPos(orig + delta)
        for lbl, orig_scene in self.labels:
            parent = lbl.parentItem()
            if parent is not None and parent.scene() is not None:
                lbl.setPos(parent.mapFromScene(orig_scene + delta))
        for w, pts in self.wires:
            if w.scene() is not None:
                w.points = [p + delta for p in pts]
                w._rebuild()
        touched = set()
        for w, idx, orig in self.followers:
            if w.scene() is not None and idx < len(w.points):
                w.points[idx] = orig + delta
                touched.add(w)
        for w in touched:
            w._rebuild()
        for j, orig in self.dots:
            if j.scene() is not None:
                j.setPos(orig + delta)
        for (comp, local, src), pw in zip(self.bridges, self.previews):
            if pw.scene() is None or comp.scene() is None:
                continue
            pt = self._moving_point(src)
            if pt is not None:
                pw.points = _elbow(comp.mapToScene(QPointF(*local)), pt, True)
                pw._rebuild()

    def _drop_previews(self) -> None:
        for pw in self.previews:
            if pw.scene() is not None:
                self.scene.removeItem(pw)
        self.previews = []
        for w, _ in self.wires:
            if w.scene() is not None:
                w.setZValue(Z_WIRE)
        ended = getattr(self.pressed, "drag_ended", None)
        if ended is not None and (self.pressed.scene() is not None):
            ended()

    def finish(self) -> bool:
        """The release. Returns True when something moved: then the
        pre-drag snapshot is the undo step, the bridges are added, the
        wires are normalised and the moved wires reselected."""
        from .canvas import _elbow, _pt_key
        from .wire_item import WireItem
        scene = self.scene
        self._drop_previews()
        moved = bool(self.delta.x() or self.delta.y())
        if not moved:
            return False
        scene._push_snapshot(self.snapshot)
        bridged: set = set()
        for comp, local, src in self.bridges:
            if comp.scene() is None:
                continue
            pin = comp.mapToScene(QPointF(*local))
            pt = self._moving_point(src)
            if pt is None or _pt_key(pt) == _pt_key(pin):
                continue
            key = (_pt_key(pin), _pt_key(pt))
            if key not in bridged:
                bridged.add(key)
                scene.addItem(WireItem(_elbow(QPointF(pin), QPointF(pt), True)))
        # the footprint of the moved wires, before the sync replaces them
        moved_segs = [(QPointF(w.points[i]), QPointF(w.points[i + 1]))
                      for w, _ in self.wires if w.scene() is not None
                      for i in range(len(w.points) - 1)]
        scene._sync_junctions()
        scene._remove_short_circuit_wires()
        scene._sync_junctions()
        scene._reselect_on_footprint(moved_segs)
        scene.update()
        return True

    def cancel(self) -> None:
        """The scene is reset during the gesture: drop what the drag added."""
        self._drop_previews()
