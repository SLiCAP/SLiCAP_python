"""NGspice SPICE netlist builder.

Produces a standard SPICE netlist from an NGspice schematic
(``.spice_sch``).  The format is:

    * Title
    .include "lib/..."
    .param ...

    R1 N+ N- 1k
    ...

    .end

Parameter formatting follows NGspice conventions:
  - R, C, L, E, G, F, H, K: the ``value`` param is written positionally;
    any remaining params use ``key=value`` notation.
  - V, I sources: written as ``dc val [ac val] [tran val]``.
  - B (behavioral): written as ``V=expr`` / ``I=expr``.
  - All other elements (Q, M, J, Z, D, S, W, T, X, O ...):
    use ``key=value`` for all params.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF

from SLiCAP.SLiCAPlex import _to_ngspice

from .connectivity import resolve_nets, _rpt
from .netlist import NetlistError


_ANNOTATION = {"0", "port"}

# Prefixes whose first param ("value") is written positionally in SPICE.
_POSITIONAL_VALUE = {"R", "C", "L", "E", "G", "F", "H", "K"}

# Param names whose values must NOT be wrapped in {} (boolean/integer flags).
_NO_BRACES = {"noisy", "off"}

# Param names handled outside _format_params (e.g. converted to ON/OFF in
# _element_lines) and therefore excluded from all param output here.
_SKIP_PARAMS = {"onoff"}


def _wrap(value: str, key: str = "") -> str:
    """Wrap a bare value in {} for NGspice parameter substitution.

    Values use SLiCAP notation ('M' = mega) and are translated to NGspice
    notation here ('1M' → '1Meg'); NGspice reads scale factors
    case-insensitively, so untranslated '1M' would mean 1 milli. Hand-written
    {expressions} are passed through untouched — numeric literals inside them
    must use NGspice notation or plain exponents.

    Skips wrapping when the value is already wrapped or the key is a known
    boolean / integer flag (listed in _NO_BRACES)."""
    v = value.strip()
    if not v or key in _NO_BRACES:
        return _to_ngspice(v)
    if v.startswith("{") and v.endswith("}"):
        return v
    return f"{{{_to_ngspice(v)}}}"


def _node_resolver(components: list, wires: list):
    net_map = resolve_nets(components, wires)

    def _node(comp, lx: float, ly: float) -> str:
        return net_map.get(_rpt(comp.mapToScene(QPointF(lx, ly))), "?")

    return _node


def _expand_pwl(params: dict) -> str:
    """Read a PWL data file and return a PWL(...) string for the netlist."""
    path = params.get("_pwl_file", "").strip()
    if not path:
        raise NetlistError(["PWL source has no file selected."])
    try:
        tokens = open(path).read().split()
    except OSError as exc:
        raise NetlistError([f"Cannot read PWL file '{path}': {exc}"]) from exc
    if len(tokens) % 2 != 0:
        raise NetlistError([f"PWL file '{path}' has an odd number of tokens (need T V pairs)."])
    inner = " ".join(f"{{{_to_ngspice(tokens[i])}}} {{{_to_ngspice(tokens[i+1])}}}"
                     for i in range(0, len(tokens), 2))
    r  = params.get("_pwl_r",  "").strip()
    td = params.get("_pwl_td", "").strip()
    suffix = (f" r={r}" if r else "") + (f" td={td}" if td else "")
    return f"PWL({inner}){suffix}"


def _format_params(prefix: str, params: dict) -> list[str]:
    """Return param tokens for an NGspice element line."""
    parts: list[str] = []

    if prefix in _POSITIONAL_VALUE:
        val = params.get("value", "").strip()
        if val:
            parts.append(_wrap(val))
        for k, v in params.items():
            if k == "value" or k.startswith("_") or k in _SKIP_PARAMS:
                continue
            v = v.strip()
            if v:
                parts.append(f"{k}={_wrap(v, k)}")

    elif prefix in ("V", "I"):
        dc = params.get("dc", "").strip()
        if dc:
            parts.append(f"dc {_wrap(dc)}")
        ac = params.get("ac", "").strip()
        if ac:
            parts.append("ac " + " ".join(_wrap(t) for t in ac.split()))
        tran = params.get("tran", "")
        if tran.strip() == "_PWL_":
            parts.append(_expand_pwl(params))
        elif tran.strip():
            parts.append(tran)   # PULSE(...) / SIN(...) etc. already wrapped by dialog

    elif prefix == "B":
        for k, v in params.items():
            if k.startswith("_") or k in _SKIP_PARAMS:
                continue
            v = v.strip()
            if v:
                parts.append(f"{k}={_wrap(v, k)}")

    else:
        # Q, M, J, Z, D, S, W, T, X and everything else
        for k, v in params.items():
            if k.startswith("_") or k in _SKIP_PARAMS:
                continue
            v = v.strip()
            if v:
                parts.append(f"{k}={_wrap(v, k)}")

    return parts


def _element_lines(components: list, node_fn) -> list[str]:
    lines:  list[str] = []
    errors: list[str] = []

    for comp in components:
        if comp.symbol_name in _ANNOTATION:
            continue

        prefix = comp.prefix or "X"
        pins   = comp.pin_positions()
        nodes  = [node_fn(comp, px, py) for px, py in pins]
        refs   = list(comp.refs)
        model  = comp.model
        params = dict(comp.params)  # preserve insertion order

        cid = comp.instance_id

        if any("?" in n for n in nodes):
            errors.append(f"{cid}: missing connection - '?' in a node name.")
        if any("?" in r for r in refs):
            errors.append(f"{cid}: missing reference - '?' in a referenced element name.")
        if model and "?" in model:
            errors.append(f"{cid}: missing model - '?' in model name.")
        for k, v in params.items():
            if v.strip() and "?" in v:
                errors.append(f"{cid}: missing value - '?' in parameter '{k}'.")

        parts = [cid] + nodes + refs
        if model:
            parts.append(model)
        parts.extend(_format_params(prefix, params))

        # Voltage- and current-controlled switches end with ON or OFF
        if prefix in ("S", "W"):
            onoff = params.get("onoff", "0").strip()
            parts.append("ON" if onoff == "1" else "OFF")

        lines.append(" ".join(parts))

    if errors:
        raise NetlistError(errors)
    return lines


def build_ngspice_netlist(
    components:      list,       # list[ComponentItem]
    wires:           list,       # list[WireItem]
    title:           str  = "schematic",
    libs:            list = None, # list[LibraryItem]  (.include lines)
    params:          list = None, # list[ParameterItem] (.param lines)
    control_section: str  = "",   # body of .control…endc (without the wrapper)
    raw_path:        str  = "",   # path for explicit `write` at end of .control
    program_netlist: bool = False, # True → plain netlist, no .control block
) -> str:
    """Build a NGspice SPICE netlist string.

    When *program_netlist* is ``False`` (default) a ``.control save all … .endc``
    block is emitted for interactive use.  When ``True`` the control block is
    omitted, producing a plain program netlist (``.cir``) suitable for use with
    the SLiCAP simulation API (``sl.op``, ``sl.ac``, etc.), which appends its
    own control block at run time.

    When *raw_path* is provided (interactive mode only), a ``write`` command is
    appended inside ``.control`` so the raw file is written unconditionally.
    """
    _node = _node_resolver(components, wires)

    title_line = f'"{title}"' if " " in title else title
    lines: list[str] = [title_line]

    if libs:
        from . import project
        try:
            root = project.project_root()
        except Exception:
            root = None
        lines.append("")
        for lib_item in libs:
            # NGspice netlists go straight to ngspice (no SLiCAPyacc parse, so no
            # "cannot find library" backstop) — resolve to an absolute path for
            # THIS machine and warn here if it is missing.
            for _d, path, _c, exists in lib_item.resolved_entries(root):
                if not exists:
                    print(f"WARNING: library file not found: {path}")
                lines.append(f'.include "{path}"')

    if params:
        for param_item in params:
            param_lines = param_item.param_lines(value_fn=_to_ngspice)
            if param_lines:
                lines.append("")
                lines.extend(param_lines)

    lines.append("")
    lines.extend(_element_lines(components, _node))

    if not program_netlist:
        lines.append("")
        lines.append(".control")
        lines.append("save all")
        if control_section.strip():
            lines.extend(control_section.splitlines())
        if raw_path:
            lines.append(f"write {raw_path}")
        lines.append(".endc")

    lines += ["", ".end"]
    return "\n".join(lines)
