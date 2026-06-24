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
from dataclasses import dataclass, field
from pathlib import Path

from .config import GRID_SIZE


@dataclass
class SubcktDef:
    """A subcircuit's interface, parsed from its ``.subckt`` header line."""
    name:   str
    ports:  list[str]                       = field(default_factory=list)  # node order
    params: list[tuple[str, str]]           = field(default_factory=list)  # (name, default)


def parse_subckt(path) -> SubcktDef:
    """Parse the (first) ``.subckt`` definition in a ``.lib`` file.

    Tokens after the subcircuit name are split into **ports** (bare node names)
    and **parameters** (``name=default`` tokens), preserving order.  Continuation
    lines (``+ …``) are joined first.
    """
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


def _min_half(placement: list) -> tuple[float, float]:
    """Auto-fit minimum (half_w, half_h) so the pin names fit without overlap:
    pins spaced ≥ side-spacing with corner margins, plus the name column/row
    stack.  Horizontal-side spacing is wider than vertical (names are wider than
    tall).  Rounded up to the grid."""
    n_top, n_right, n_bottom, n_left = _side_counts(len(placement))
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


def min_half(defn: SubcktDef, placement: list | None = None) -> tuple[float, float]:
    """Public auto-fit minimum half-size for ``defn`` / placement (Place dialog)."""
    return _min_half(list(placement) if placement else list(defn.ports))


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


def box_symbol_svg(defn: SubcktDef, placement: list | None = None,
                   extra_w: float = 0.0, extra_h: float = 0.0) -> str:
    """Return a standalone SVG holding a default block symbol for ``defn``.

    ``placement`` is the **visual** clockwise-from-top-left pin order (default:
    the ``.subckt`` node order).  It only moves where each named pin is drawn —
    ``data-nodes`` stays in the fixed ``.subckt`` order, since a SLiCAP ``X``
    instance lists its nodes positionally against the ``.subckt`` header.  So
    reordering pins never changes the netlist, only the look.

    ``extra_w`` / ``extra_h`` grow (or, when negative, shrink) each half-dimension
    relative to the auto-fit minimum — the Place dialog's width/height +/- buttons.
    Shrinking is allowed down to an absolute floor; below the auto-fit size names
    may overlap, which is then the user's call.  The box stays on the grid.
    """
    ports     = list(defn.ports)                       # data-nodes / netlist order
    placement = list(placement) if placement else list(ports)
    n_top, n_right, n_bottom, n_left = _side_counts(len(placement))

    hw_min, hh_min = _min_half(placement)
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
    param_names = " ".join(k for k, _ in defn.params)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg">\n'
        f'  <g id="{defn.name}"\n'
        f'     data-prefix="X"\n'
        f'     data-nodes="{" ".join(ports)}"\n'
        f'     data-model="{defn.name}"\n'
        f'     data-params="{param_names}"\n'
        f'     data-show-pinnames="true"\n'
        f'     data-description="Subcircuit {defn.name}">\n'
        f'      {body}\n'
        f'  </g>\n'
        f'</svg>\n'
    )
