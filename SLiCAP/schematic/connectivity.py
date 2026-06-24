from __future__ import annotations
from PySide6.QtCore import QPointF


_TOL = 0.5   # half a scene unit; pins land on multiples of 5


def _rpt(p: QPointF) -> tuple[int, int]:
    """Round a scene point to the nearest integer grid key."""
    return (round(p.x()), round(p.y()))


def _on_segment(p1: QPointF, p2: QPointF, q: QPointF) -> bool:
    """True if q lies on the axis-aligned segment p1→p2 (inclusive endpoints)."""
    if abs(p1.x() - p2.x()) < _TOL:          # vertical
        if abs(q.x() - p1.x()) > _TOL:
            return False
        lo, hi = min(p1.y(), p2.y()), max(p1.y(), p2.y())
        return lo - _TOL <= q.y() <= hi + _TOL
    if abs(p1.y() - p2.y()) < _TOL:          # horizontal
        if abs(q.y() - p1.y()) > _TOL:
            return False
        lo, hi = min(p1.x(), p2.x()), max(p1.x(), p2.x())
        return lo - _TOL <= q.x() <= hi + _TOL
    return False


class _UF:
    def __init__(self):
        self._p: dict[tuple, tuple] = {}

    def _ensure(self, x):
        if x not in self._p:
            self._p[x] = x

    def find(self, x) -> tuple:
        self._ensure(x)
        if self._p[x] != x:
            self._p[x] = self.find(self._p[x])
        return self._p[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._p[rb] = ra


def resolve_nets(
    components: list,   # list[ComponentItem]
    wires: list,        # list[WireItem]
) -> dict[tuple[int, int], str]:
    """
    Build nets by union-find over all wire points and component pins.

    Returns a mapping: rounded scene position → net name.

    Priority for net naming:
      1. ground symbol → "0"
      2. WireItem.net_name (explicit user label)
      3. port symbol → port params["name"] if set
      4. auto-generated "n1", "n2", ...
    """
    from .component_item import PIN_POSITIONS

    uf = _UF()

    # ── union consecutive points along each wire ──────────────────────────────
    for wire in wires:
        pts = [_rpt(p) for p in wire.points]
        for i in range(len(pts) - 1):
            uf.union(pts[i], pts[i + 1])

    # ── collect all candidate junction points ─────────────────────────────────
    junctions: list[QPointF] = []
    for wire in wires:
        junctions.extend(wire.points)
    for comp in components:
        for lx, ly in PIN_POSITIONS.get(comp.symbol_name, []):
            junctions.append(comp.mapToScene(QPointF(lx, ly)))

    # ── ensure every junction key exists in the UF ────────────────────────────
    for q in junctions:
        uf.find(_rpt(q))

    # ── T-junction detection ──────────────────────────────────────────────────
    # A junction point that falls on the interior of a wire segment joins that net.
    for wire in wires:
        for i in range(len(wire.points) - 1):
            p1, p2 = wire.points[i], wire.points[i + 1]
            seg_key = _rpt(p1)
            for q in junctions:
                if _on_segment(p1, p2, q):
                    uf.union(_rpt(q), seg_key)

    # ── same-name ports form one net regardless of physical connection ────────
    _port_roots: dict[str, tuple] = {}
    for comp in components:
        if comp.symbol_name == "port":
            name = comp.params.get("name", "").strip()
            if name:
                root = uf.find(_rpt(comp.mapToScene(QPointF(0.0, 0.0))))
                if name in _port_roots:
                    uf.union(root, _port_roots[name])
                else:
                    _port_roots[name] = root

    # ── assign net names ──────────────────────────────────────────────────────
    root_name: dict[tuple, str] = {}
    counter = [1]

    def _auto(root):
        if root not in root_name:
            root_name[root] = str(counter[0])
            counter[0] += 1

    # Priority 1 — ground (net name from params, defaults to "0")
    for comp in components:
        if comp.symbol_name == "0":
            name = comp.params.get("name", "0").strip() or "0"
            root = uf.find(_rpt(comp.mapToScene(QPointF(0.0, 0.0))))
            root_name[root] = name

    # Priority 2 — explicit wire labels
    for wire in wires:
        if wire.net_name:
            root = uf.find(_rpt(wire.points[0]))
            if root not in root_name:
                root_name[root] = wire.net_name

    # Priority 3 — port name
    for comp in components:
        if comp.symbol_name == "port":
            name = comp.params.get("name", "").strip()
            if name:
                root = uf.find(_rpt(comp.mapToScene(QPointF(0.0, 0.0))))
                if root not in root_name:
                    root_name[root] = name

    # Priority 4 — auto-name everything that touches a wire or pin
    for k in list(uf._p):
        _auto(uf.find(k))

    return {k: root_name[uf.find(k)] for k in uf._p}
