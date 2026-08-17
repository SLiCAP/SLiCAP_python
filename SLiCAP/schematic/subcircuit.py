"""
Hierarchical blocks — reading a subcircuit ``.lib`` and turning it into a
placeable block symbol.

A subcircuit library file holds one ``.subckt <name> <nodes…> <par=def…>``
definition (see :mod:`app.netlist`).  :func:`parse_subckt` is the single source
of truth for a block's interface (name, ordered ports, overridable parameters);
:func:`box_symbol_svg` generates a default rectangle-with-pins symbol from that
interface so the block can be placed like any other component.

The generated symbol carries the SLiCAP symbol contract used everywhere else
(``data-prefix="X"``, ``data-model="<name>"``, ``data-nodes``, ``data-params``,
``data-show-pinnames="true"`` plus ``<circle class="node">`` markers), so a placed block reuses the existing
netlist machinery verbatim and emits ``X1 <nodes…> <name> par=val …``.
"""
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .config import GRID_SIZE


@dataclass
class SubcktDef:
    """A subcircuit's interface, parsed from its ``.subckt`` header line."""
    name:   str
    ports:  list[str]                       = field(default_factory=list)  # node order
    params: list[tuple[str, str]]           = field(default_factory=list)  # (name, default)


def parse_subckt(path, dialect=None) -> SubcktDef:
    """Parse the (first) ``.subckt`` definition in a ``.lib`` file.

    Tokens after the subcircuit name are split into **ports** (bare node names)
    and **parameters** (``name=default`` tokens), preserving order.  Continuation
    lines (``+ …``) are joined first.

    *dialect* ('slicap' | 'ngspice', default inferred from the extension)
    decides what a lone ``params:`` token means (Anton, 2026-08-04). The
    authority differs per file type: ngspice itself ACCEPTS the PSpice
    keyword (manual 2.11.5), and vendor macromodels carry it, so a
    ``.spice_lib`` skips it; SLiCAP syntax has no such keyword, so a
    ``.slicap_lib`` REFUSES it - the 1MEG rule: no tolerant reading of a
    foreign dialect in our own files. Before this, the token became a
    phantom PORT and the symbol got a pin too many.
    """
    if dialect is None:
        suffix = Path(path).suffix.lower()
        dialect = "ngspice" if suffix == ".spice_lib" else "slicap"
    text = Path(path).read_text(encoding="utf-8")

    # Join continuation lines: a line whose first non-blank char is '+' extends
    # the previous logical line.
    logical: list[str] = []
    for raw in text.splitlines():
        if raw.lstrip().startswith("+"):
            if logical:
                logical[-1] += " " + raw.lstrip()[1:].strip()
        else:
            logical.append(raw)

    for line in logical:
        if line.strip().lower().startswith(".subckt"):
            tokens = line.split()[1:]          # drop ".subckt"
            if not tokens:
                break
            name   = tokens[0]
            ports:  list[str]             = []
            params: list[tuple[str, str]] = []
            for tok in tokens[1:]:
                if tok.lower() in ("params:", "params"):
                    if dialect == "ngspice":
                        continue          # PSpice separator: legal, ignored
                    raise ValueError(
                        "'params:' is NGspice/PSpice syntax; a SLiCAP "
                        "library takes bare name=default pairs on the "
                        ".subckt line.")
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    params.append((k.strip(), v.strip()))
                else:
                    ports.append(tok)
            return SubcktDef(name=name, ports=ports, params=params)

    raise ValueError(f"No .subckt definition found in {Path(path).name}")


# ── default box-symbol geometry (all on the GRID so pins are connectable) ──────
# Pin names are drawn inside the outline by ComponentItem (small font); the box
# is sized to hold them without overlap.  Names form up to three columns
# (left edge · top/bottom centred · right edge) and three rows (top · left/right
# centred · bottom).  Pins are spread evenly along each side, ≥ _CORNER from a
# corner, symmetric about the centre; everything rounds to the grid so every pin
# lands on a grid point.  Horizontal sides use wider pin spacing than vertical
# ones, since names are wider than tall.
_STUB    = 10    # pin stub length (box edge → node marker)
_CORNER  = 10    # minimum corner → pin distance
_STEP    = 2 * GRID_SIZE   # pin-spacing granularity (keeps pins symmetric on grid)
_MINH    = 20    # auto-fit minimum half-dimension (the size +/- starts from)
_FLOOR   = 10    # absolute floor the user may shrink to (overlap is then theirs)
_CHARW   = 3.2   # approx pin-name char width (scene units)
_NAMEH   = 10.0  # approx pin-name height (scene units)
_NGAP    = 6.0   # gap between adjacent names
_NMARGIN = 4.0   # name → outline margin


def _grid_up(v: float) -> float:
    """Round ``v`` up to the next grid step, so the box edges and the pins
    derived from them (edge ± stub) all land on the grid and stay connectable."""
    return math.ceil(v / GRID_SIZE) * GRID_SIZE


def _round_up(v: float, m: float) -> float:
    return math.ceil(v / m) * m


def _side_counts(n: int) -> list[int]:
    """Split ``n`` ports across the four sides (top, right, bottom, left) as
    evenly as possible, with any remainder filling sides in clockwise order."""
    base, rem = divmod(n, 4)
    return [base + (1 if i < rem else 0) for i in range(4)]


def _normalize_placement(placement) -> tuple[list, tuple]:
    """Reduce either placement form to ``(flat clockwise list, side counts)``.

    A flat list gets its side counts from ``_side_counts`` (the historic
    behaviour); a per-side dict ``{"top": [...], "right": [...], "bottom":
    [...], "left": [...]}`` states the counts itself.  Dict sides are given in
    natural reading order (top/bottom L→R, left/right T→B); the clockwise slot
    walk runs bottom R→L and left B→T, hence the reversals."""
    if isinstance(placement, dict):
        top    = list(placement.get("top", []))
        right  = list(placement.get("right", []))
        bottom = list(placement.get("bottom", []))
        left   = list(placement.get("left", []))
        flat = top + right + list(reversed(bottom)) + list(reversed(left))
        return flat, (len(top), len(right), len(bottom), len(left))
    flat = list(placement)
    return flat, tuple(_side_counts(len(flat)))


def _min_half(placement, counts=None) -> tuple[float, float]:
    """Auto-fit minimum (half_w, half_h) so the pin names fit without overlap:
    pins spaced ≥ side-spacing with corner margins, plus the name column/row
    stack.  Horizontal-side spacing is wider than vertical (names are wider than
    tall).  Rounded up to the grid."""
    if counts is None:
        placement, counts = _normalize_placement(placement)
    n_top, n_right, n_bottom, n_left = counts
    name_w  = max((len(p) for p in placement), default=1) * _CHARW
    space_h = _round_up(name_w + _NGAP, _STEP)    # horizontal-side pin spacing (wide)
    space_v = _round_up(_NAMEH + _NGAP, _STEP)    # vertical-side pin spacing (narrow)
    cols = bool(n_left) + bool(n_top or n_bottom) + bool(n_right)
    rows = bool(n_top) + bool(n_left or n_right) + bool(n_bottom)
    stack_w = cols * name_w + max(cols - 1, 0) * _NGAP
    stack_h = rows * _NAMEH + max(rows - 1, 0) * _NGAP
    half_w = _grid_up(max((max(n_top, n_bottom) - 1) * space_h / 2 + _CORNER,
                          stack_w / 2 + _NMARGIN, _MINH))
    half_h = _grid_up(max((max(n_left, n_right) - 1) * space_v / 2 + _CORNER,
                          stack_h / 2 + _NMARGIN, _MINH))
    return half_w, half_h


def min_half(defn: SubcktDef, placement=None) -> tuple[float, float]:
    """Public auto-fit minimum half-size for ``defn`` / placement (Place dialog)."""
    return _min_half(placement if placement else list(defn.ports))


def _port_side(rotation: float, h_flip: bool, v_flip: bool) -> str | None:
    """The box side a port symbol assigns its pin to, from its orientation.

    The pentagon's pin sits at the apex; the body is its tail.  A port whose
    tail points up sits above the circuit (apex pointing down into it), so the
    pin surfaces on TOP of the block symbol — the side is the tail direction.
    The table matches Qt's transform composition for ComponentItem
    (setTransform(flip scale) + setRotation, verified empirically 2026-08-05);
    the pentagon is symmetric about its axis, so only ONE flip matters per
    rotation.  Returns None for a non-orthogonal rotation."""
    r = round(rotation) % 360
    if r == 0:
        return "top" if v_flip else "bottom"
    if r == 180:
        return "bottom" if v_flip else "top"
    if r == 90:
        return "right" if h_flip else "left"
    if r == 270:
        return "left" if h_flip else "right"
    return None


def schematic_placement(defn: SubcktDef, sch_path) -> dict | None:
    """Per-side pin placement read from the subcircuit's own schematic.

    Each ``.subckt`` port takes the side its port symbol suggests (Anton,
    2026-08-05: a label pointing top→bottom belongs on top of the symbol,
    left→right on the left, and so on — see :func:`_port_side`).  Within a
    side, pins keep the schematic's geometric order (top/bottom by x,
    left/right by y), so the symbol mirrors the drawing.

    Returns ``{"top": [...], "right": [...], "bottom": [...], "left": [...]}``,
    or None when the schematic cannot supply a full, unambiguous answer
    (unreadable file, port names not matching ``defn.ports``, duplicates) —
    the caller then falls back to the count-based clockwise layout."""
    import json
    try:
        data = json.loads(Path(sch_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    found: dict[str, tuple[str, float, float]] = {}
    for c in data.get("components", []):
        if c.get("symbol_name") != "port":
            continue
        name = (c.get("params") or {}).get("name") or ""
        side = _port_side(c.get("rotation", 0.0),
                          c.get("h_flip", False), c.get("v_flip", False))
        if not name or name in found or side is None:
            return None
        found[name] = (side, float(c.get("x", 0.0)), float(c.get("y", 0.0)))
    if set(found) != set(defn.ports):
        return None
    sides: dict[str, list] = {"top": [], "right": [], "bottom": [], "left": []}
    for name, (side, x, y) in found.items():
        sides[side].append((x, y, name))
    return {
        "top":    [n for x, y, n in sorted(sides["top"])],
        "bottom": [n for x, y, n in sorted(sides["bottom"])],
        "left":   [n for x, y, n in sorted(sides["left"],
                                           key=lambda t: (t[1], t[0]))],
        "right":  [n for x, y, n in sorted(sides["right"],
                                           key=lambda t: (t[1], t[0]))],
    }


def _spread(k: int, half: float) -> list[float]:
    """``k`` pin offsets evenly spread along a side of half-length ``half``,
    symmetric about the centre, ≥ ``_CORNER`` from each corner, on the grid.

    Spacing is a multiple of ``_STEP`` (so offsets stay on the grid for any pin
    count) and as wide as fits the side; it never drops below ``_STEP``."""
    if k <= 0:
        return []
    if k == 1:
        return [0.0]
    avail = max(0.0, 2 * (half - _CORNER))
    step = max(_STEP, math.floor(avail / (k - 1) / _STEP) * _STEP)
    return [(i - (k - 1) / 2) * step for i in range(k)]


def box_symbol_svg(defn: SubcktDef, placement=None,
                   extra_w: float = 0.0, extra_h: float = 0.0) -> str:
    """Return a standalone SVG holding a default block symbol for ``defn``.

    ``placement`` is the **visual** pin arrangement (default: the ``.subckt``
    node order): either a flat clockwise-from-top-left list (sides filled by
    count) or a per-side dict ``{"top": [...], "right": [...], "bottom":
    [...], "left": [...]}`` as produced by :func:`schematic_placement`.  It
    only moves where each named pin is drawn — ``data-nodes`` stays in the
    fixed ``.subckt`` order, since a SLiCAP ``X`` instance lists its nodes
    positionally against the ``.subckt`` header.  So rearranging pins never
    changes the netlist, only the look.

    ``extra_w`` / ``extra_h`` grow (or, when negative, shrink) each half-dimension
    relative to the auto-fit minimum — the Place dialog's width/height +/- buttons.
    Shrinking is allowed down to an absolute floor; below the auto-fit size names
    may overlap, which is then the user's call.  The box stays on the grid.
    """
    ports = list(defn.ports)                           # data-nodes / netlist order
    placement, counts = _normalize_placement(placement if placement else ports)
    n_top, n_right, n_bottom, n_left = counts

    hw_min, hh_min = _min_half(placement, counts)
    half_w = max(_FLOOR, hw_min + extra_w)
    half_h = max(_FLOOR, hh_min + extra_h)

    # Clockwise slots (top L→R, right T→B, bottom R→L, left B→T): each is
    # (edge_x, edge_y, node_x, node_y).  placement[i] occupies slot i.
    slots: list[tuple[float, float, float, float]] = []
    for x in _spread(n_top, half_w):
        slots.append((x, -half_h, x, -half_h - _STUB))
    for y in _spread(n_right, half_h):
        slots.append((half_w, y, half_w + _STUB, y))
    for x in reversed(_spread(n_bottom, half_w)):
        slots.append((x, half_h, x, half_h + _STUB))
    for y in reversed(_spread(n_left, half_h)):
        slots.append((-half_w, y, -half_w - _STUB, y))
    pos = {placement[i]: slots[i] for i in range(len(placement))}

    def _f(v: float) -> str:                       # tidy number formatting
        return f"{v:g}"

    # The box + pin stubs + node markers only.  The block name (model label) and
    # the pin names are drawn by ComponentItem so they stay upright under any
    # rotation/flip — never baked into the (rotating) symbol art.
    lines = [
        f'<rect x="{_f(-half_w)}" y="{_f(-half_h)}" '
        f'width="{_f(2 * half_w)}" height="{_f(2 * half_h)}" '
        f'fill="none" stroke="black" stroke-width="1"/>',
        "",
        "<!-- Pins -->",
    ]
    for port in ports:
        ex, ey, nx, ny = pos[port]
        lines.append(
            f'<line x1="{_f(ex)}" y1="{_f(ey)}" x2="{_f(nx)}" y2="{_f(ny)}" '
            f'stroke="black" stroke-width="1"/>'
        )
    lines.append("")
    for port in ports:
        _ex, _ey, nx, ny = pos[port]
        lines.append(
            f'<circle cx="{_f(nx)}" cy="{_f(ny)}" r="0.5" '
            f'class="node" data-node="{port}"/>'
        )

    body = "\n      ".join(lines)
    # METADATA FORMAT, not bare names: the symbol parser requires
    # 'name|show' for data-model and 'name|default|show_name|show_value'
    # for data-params since the metadata migration - this generator was
    # forgotten in that migration, so every generated block symbol failed
    # to parse: the preview stayed blank and previously generated symbol
    # files were skipped on library load (Anton, 2026-08-04, "we had
    # auto-creation long time ago"). The model shows (the block name is
    # drawn through the model label, kept upright by ComponentItem).
    param_field = ";".join(f"{k}|{v}|1|1" for k, v in defn.params)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg">\n'
        f'  <g id="{defn.name}"\n'
        f'     data-prefix="X"\n'
        f'     data-nodes="{" ".join(ports)}"\n'
        f'     data-model="{defn.name}|1"\n'
        f'     data-params="{param_field}"\n'
        f'     data-show-pinnames="true"\n'
        f'     data-description="Subcircuit {defn.name}">\n'
        f'      {body}\n'
        f'  </g>\n'
        f'</svg>\n'
    )


def _lib_companions(lib_path) -> list:
    """The sidecar files that travel with a subcircuit ``.lib``: the block
    symbol SVG and the subcircuit's own schematic, per the type-tagged naming
    convention (names are the CONVENTION, never stored paths)."""
    lib_path = Path(lib_path)
    is_ng = lib_path.suffix == ".spice_lib"
    stem  = lib_path.stem
    return [
        lib_path.with_name(f"{stem}_{'spice' if is_ng else 'slicap'}_symbol.svg"),
        lib_path.with_name(f"{stem}{'.spice_sch' if is_ng else '.slicap_sch'}"),
    ]


def ensure_in_project_lib(lib_path, libdir):
    """The project-local path of *lib_path*, copying it into ``libdir`` when
    it was browsed from elsewhere.

    A placed subcircuit is referenced RELATIVELY (``lib/<name>.slicap_lib``
    in the netlist include, ``lib/<name>_<type>_symbol.svg`` for the block
    symbol), so the project must physically hold both - a project is
    self-contained and survives being moved or handed over (Anton,
    2026-08-04). Storing the foreign path instead was considered and
    REJECTED: an absolute path in a schematic file breaks on relocation.

    The subcircuit's companions travel along when they sit beside the chosen
    ``.lib``: the block symbol SVG and the subcircuit SCHEMATIC — the
    schematic is part of the package in ``lib/`` and is loaded from there
    (Anton, 2026-08-05), so descending into the hierarchy works in the
    receiving project too.

    :param lib_path: the ``.lib`` file the user chose.
    :param libdir: the project's ``lib`` directory.
    :return: the path inside *libdir*.
    :rtype: pathlib.Path
    """
    import shutil
    lib_path = Path(lib_path)
    libdir = Path(libdir)
    target = libdir / lib_path.name
    if lib_path.resolve() == target.resolve():
        return target
    libdir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(lib_path, target)
    copied = [lib_path.name]
    for comp in _lib_companions(lib_path):
        if comp.is_file():
            shutil.copyfile(comp, libdir / comp.name)
            copied.append(comp.name)
    print("Copied {0} into the project library (a project is "
          "self-contained).".format(", ".join(copied)))
    return target


def instance_port_map(parent_netlist, parent_prefix, parent_port_nets,
                      instance_id, ports) -> "dict | None":
    """Raw-vector net names for *ports* of one placed instance.

    Inside an NGspice subcircuit the port nets ARE the parent nets: the raw
    only dot-prefixes the internal nodes.  So each port maps to the node the
    parent's naming netlist wires to that ``X`` instance — composed through
    the parent's OWN borrowed context when descending deeper (a parent-port
    node maps on through *parent_port_nets*; a parent-internal node gets the
    parent's *parent_prefix*).  Ground (node 0) is global at every level.

    :param parent_netlist: the parent's naming-authority netlist text.
    :param parent_prefix: the parent's own instance path, or None at top level.
    :param parent_port_nets: the parent's own port→raw map ({} at top level).
    :param instance_id: the descended-from instance (e.g. ``X1``).
    :param ports: the subcircuit's ``.subckt`` port order.
    :return: ``{port name (lower): raw net name}``, or None when the
             instance line cannot be found or is too short (stale netlist).
    """
    inst = str(instance_id).lower()
    for line in (parent_netlist or "").splitlines():
        t = line.split()
        if t and t[0].lower() == inst:
            if len(t) < 1 + len(ports):
                return None
            nodes = t[1:1 + len(ports)]
            out = {}
            for p, n in zip(ports, nodes):
                nl = n.lower()
                if nl == "0":
                    raw = "0"
                elif parent_prefix:
                    raw = parent_port_nets.get(nl, f"{parent_prefix}.{nl}")
                else:
                    raw = nl
                out[str(p).lower()] = raw
            return out
    return None


def find_subckt_schematic(name, sch_ext, lib_path=None):
    """The subcircuit's editable schematic, or None.

    The schematic is part of the subcircuit package in the project ``lib/``
    folder and is loaded from there (Anton, 2026-08-05).  Search order:
    beside the ``.lib`` file itself (covers a freshly browsed foreign
    library), the project ``lib/``, then the project ``sch/`` — the legacy
    location, kept so older projects keep descending until re-saved.

    :param name: the subcircuit (``.subckt``) name.
    :param sch_ext: ``.slicap_sch`` or ``.spice_sch``.
    :param lib_path: the ``.lib`` file, when known.
    :return: the first existing candidate path, or None.
    :rtype: pathlib.Path, NoneType
    """
    from . import project
    candidates = []
    if lib_path is not None:
        candidates.append(Path(lib_path).parent / f"{name}{sch_ext}")
    candidates.append(project.subdir("lib") / f"{name}{sch_ext}")
    candidates.append(project.subdir("sch") / f"{name}{sch_ext}")   # legacy
    for c in candidates:
        if c.is_file():
            return c
    return None


def reskin_symbol_svg(source_g_xml, defn, port_for_pin):
    """An EXISTING symbol's artwork as *defn*'s block symbol.

    Piece 3 of the subcircuit round (Anton, 2026-08-04): any loaded symbol
    whose pin COUNT matches the subcircuit's ports can be assigned as its
    symbol - an opamp macromodel gets the opamp artwork, a transistor-level
    model the transistor symbol. There is no symbol editor yet, so this is
    how a new model gets a decent symbol.

    The artwork is kept; the METADATA is rewritten: the id and model become
    the subcircuit's name, the prefix becomes X, ``data-nodes`` becomes the
    ``.subckt`` port order (which is what the netlister emits), and every
    pin marker is renamed to the port mapped onto it. ``data-refs`` is
    dropped - a controlled-source reference means nothing on a subcircuit.

    :param source_g_xml: the source symbol's raw ``<g>`` XML (Symbol.g_xml).
    :param defn: the subcircuit interface.
    :type defn: SubcktDef
    :param port_for_pin: ``{symbol pin name: subcircuit port}`` - a bijection
                         onto the ports.
    :type port_for_pin: dict
    :return: a standalone SVG document.
    :rtype: str
    """
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    g = ET.fromstring(source_g_xml)
    g.set("id", defn.name)
    g.set("data-prefix", "X")
    g.set("data-nodes", " ".join(defn.ports))
    g.set("data-model", f"{defn.name}|1")
    g.set("data-params", ";".join(f"{k}|{v}|1|1" for k, v in defn.params))
    g.set("data-description", f"Subcircuit {defn.name}")
    g.attrib.pop("data-refs", None)
    svg_ns = "{http://www.w3.org/2000/svg}"
    for el in g.iter():
        if el.tag == f"{svg_ns}circle" and el.get("class") == "node":
            old = el.get("data-node")
            if old in port_for_pin:
                el.set("data-node", port_for_pin[old])
    return ('<svg xmlns="http://www.w3.org/2000/svg">\n  '
            + ET.tostring(g, encoding="unicode") + "\n</svg>\n")
