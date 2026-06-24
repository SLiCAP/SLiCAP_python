from __future__ import annotations
from PySide6.QtCore import QPointF

from .component_item import PIN_POSITIONS, wrap_braces
from .connectivity import resolve_nets, _rpt

# Symbols that are net annotations only — no element line in the netlist
_ANNOTATION = {"0", "port"}


class NetlistError(Exception):
    """A netlist could not be generated because unresolved "?" placeholders
    remain — a value, model, reference or connection the user must still define.

    Symbols declare such placeholders as "?" in their SVG definition; a netlist
    must never contain "?" (it would only make the SLiCAP parser fail later), so
    generation is aborted and nothing is written.  ``errors`` lists the problems,
    one human-readable message per issue."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def _node_resolver(components: list, wires: list):
    """Return a function mapping a component pin (local x, y) to its net name."""
    net_map = resolve_nets(components, wires)

    def _node(comp, lx: float, ly: float) -> str:
        return net_map.get(_rpt(comp.mapToScene(QPointF(lx, ly))), "?")

    return _node


def _element_lines(components: list, node_fn) -> list[str]:
    """Element lines (one per non-annotation component) in netlist order.

    Raises NetlistError if any unresolved "?" placeholder remains (missing
    value, model, reference or connection), so a netlist containing "?" — which
    would only make the SLiCAP parser fail later — is never produced.  All
    problems across all components are collected and reported together."""
    lines:  list[str] = []
    errors: list[str] = []
    for comp in components:
        if comp.symbol_name in _ANNOTATION:
            continue

        pins   = PIN_POSITIONS.get(comp.symbol_name, [])
        nodes  = [node_fn(comp, px, py) for px, py in pins]
        refs   = list(comp.refs)
        model  = comp.model
        params = [(k, v) for k, v in comp.params.items() if v.strip()]

        cid = comp.instance_id
        if any("?" in n for n in nodes):
            errors.append(f"{cid}: missing connection — '?' found in a node name.")
        if any("?" in r for r in refs):
            errors.append(f"{cid}: missing reference — '?' found in a referenced element name.")
        if "?" in model:
            errors.append(f"{cid}: missing model — '?' found in the model name.")
        for k, v in params:
            if "?" in v:
                errors.append(f"{cid}: missing value — '?' found in parameter '{k}'.")

        parts = [cid]
        if nodes:
            parts.extend(nodes)
        if refs:
            parts.extend(refs)
        if model:
            parts.append(model)
        parts.extend(f"{k}={wrap_braces(v)}" for k, v in params)

        lines.append(" ".join(parts))

    if errors:
        raise NetlistError(errors)
    return lines


def build_netlist(
    components: list,        # list[ComponentItem]
    wires:      list,        # list[WireItem]
    commands:   list,        # list[CommandItem]
    title:      str = "schematic",
    libs:       list = None, # list[LibraryItem]
    params:     list = None, # list[ParameterItem]
    model_defs: list = None, # list[ModelItem]
) -> str:
    """
    Build a SLiCAP netlist string.

    Format:
        <title>            (quoted if the title contains spaces)

        .command lines...

        RefDes nodes... refs... Model param=val...

        .end
    """
    title_line = f'"{title}"' if " " in title else title

    _node = _node_resolver(components, wires)

    lines: list[str] = [title_line]

    # ── library includes ──────────────────────────────────────────────────────
    if libs:
        lines.append("")
        for lib_item in libs:
            lines.append(lib_item.netlist_line())

    # ── model definitions ─────────────────────────────────────────────────────
    if model_defs:
        for model_item in model_defs:
            model_lines = model_item.netlist_lines()
            if model_lines:
                lines.append("")
                lines.extend(model_lines)

    # ── parameter blocks ──────────────────────────────────────────────────────
    if params:
        for param_item in params:
            param_lines = param_item.param_lines()
            if param_lines:
                lines.append("")
                lines.extend(param_lines)

    # ── command blocks ────────────────────────────────────────────────────────
    cmd_lines: list[str] = []
    for cmd_item in commands:
        cmd_lines.extend(cmd_item.commands())
    if cmd_lines:
        lines.append("")
        lines.extend(cmd_lines)

    # ── element lines ─────────────────────────────────────────────────────────
    lines.append("")
    lines.extend(_element_lines(components, _node))

    lines += ["", ".end"]
    return "\n".join(lines)


def build_subcircuit(
    components: list,        # list[ComponentItem]
    wires:      list,        # list[WireItem]
    name:       str,         # subcircuit (.subckt) name
    ports:      list,        # ordered node names exposed to the parent
    params:     list = None, # list[(name, default)] overridable parameters
    params_items: list = None,  # list[ParameterItem] — internal .param definitions
) -> str:
    """
    Build a SLiCAP library (`.lib`) file holding one subcircuit definition.

    Format::

        <name>

        .subckt <name> <port1> <port2> ... par1=def1 par2=def2 ...

        .param ...              (internal parameter definitions, if any)

        <element lines>

        .ends
        .end

    Ports are emitted in the given order; they are the named nets the parent
    wires to.  A ``ground`` (node 0) inside the schematic stays global and is
    never a port — grounding is the parent's job (it wires a port to 0).
    """
    title_line = f'"{name}"' if " " in name else name

    _node = _node_resolver(components, wires)

    subckt = f".subckt {name}"
    if ports:
        subckt += " " + " ".join(ports)
    if params:
        subckt += " " + " ".join(f"{k}={v}" for k, v in params if str(k).strip())

    lines: list[str] = [title_line, "", subckt]

    # ── internal parameter definitions ─────────────────────────────────────────
    # A parameter passed in through the .subckt line must NOT be redefined
    # internally — the passed value supersedes any local definition.
    passed = {str(k).strip().strip("{}") for k, _ in (params or [])}
    if params_items:
        for param_item in params_items:
            param_lines = param_item.param_lines(exclude=passed)
            if param_lines:
                lines.append("")
                lines.extend(param_lines)

    # ── element lines ──────────────────────────────────────────────────────────
    lines.append("")
    lines.extend(_element_lines(components, _node))

    lines += ["", ".ends", ".end"]
    return "\n".join(lines)


def schematic_ports(components: list, wires: list) -> list[str]:
    """Port names contributed by ``port`` symbols, in clockwise order starting
    from the top-left.  This is only the *default* order shown to the user, who
    may reorder it; the chosen order is what defines the subcircuit node list.

    A ``ground`` (node 0) is global, never a port, so it is excluded even if a
    port symbol happens to sit on it.
    """
    import math

    ports: list[tuple[float, float, str]] = []
    for comp in components:
        if comp.symbol_name != "port":
            continue
        name = comp.params.get("name", "").strip()
        if not name or name == "0":
            continue
        p = comp.mapToScene(QPointF(0.0, 0.0))
        ports.append((p.x(), p.y(), name))

    if not ports:
        return []

    cx = sum(p[0] for p in ports) / len(ports)
    cy = sum(p[1] for p in ports) / len(ports)

    def _clock(p) -> float:
        # Angle measured clockwise from straight up (12 o'clock), y grows down.
        ang = math.atan2(p[0] - cx, -(p[1] - cy))
        return ang if ang >= 0 else ang + 2 * math.pi

    seen: set[str] = set()
    ordered: list[str] = []
    for _x, _y, n in sorted(ports, key=_clock):
        if n not in seen:        # same-name ports are one net → one port node
            seen.add(n)
            ordered.append(n)
    return ordered
