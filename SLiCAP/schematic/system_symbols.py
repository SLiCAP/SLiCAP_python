"""Symbols of function blocks, generated from the class (Specs 9.5).

A lowest-level block of a system diagram is a function class. Its symbol
is not drawn by hand: it is a box with the inputs on the left, the
outputs on the right and, for a clocked function, the signal clock
``cp`` on the left above the bottom edge, generated from the class data
``inputs``, ``outputs``, ``types`` and the base class (the layout of
Specs 9.5, ``block_svg``; a clock pin at the bottom centre was the first
layout and was REPLACED, Anton, 2026-11-17, decision A). Every signal pin carries an arrowhead at the box
edge, pointing in or out (Anton, 2026-11-16). The constructor parameters
become the block's parameters, read from the signature of ``__init__``.
Every pin carries its data type and its direction as symbol metadata
(``data-types``, ``data-dirs``); the wire rules of Specs 5.1 and 9.3
(``check_net``) read them from the symbols, so a wire is checked
without importing the classes.

The symbol is written into the project's ``lib/`` as
``<Name>.system_sym`` when the block is first placed, like a subcircuit
block symbol, and regenerated from the class when the declaration
changed (``is_current()``). No Qt in this module: it is the data side of
the system dialect, testable without a display.
"""

import inspect
import re
import importlib.util
from pathlib import Path

import numpy as np

from .subcircuit import symbol_file_svg, _arrowhead

CLOCK_PIN = "cp"          # the signal clock of a clocked block ("clk" until 2026-11-18)
CLOCK_TYPE = "clock"
PREFIX = "F"              # reference designator prefix of a function block
SOURCE_PREFIX = "S"       # ... of a signal source (Anton, 2026-11-17)
CONSTANT_PREFIX = "K"     # ... of a constant (Anton, 2026-11-17: on the
                          # Symbol menu with the clock and the signal)
BLOCK_PREFIXES = (PREFIX, SOURCE_PREFIX, CONSTANT_PREFIX)
FLOAT = "float64"         # the type of a pin without a declaration
# Classes with a hand-drawn symbol in the fixed library (Symbols.system_sym),
# placed from Circuit -> Symbol like the clock, not from Place function:
# class name -> symbol id. Their symbol metadata must match the class
# (is_current), which the tests check.
FIXED_SYMBOLS = {"Signal": "SIGNAL", "Constant": "CONST"}

# The programmable filter block (Specs 10.3.3): its symbol is generated
# from a DESIGN (a createIIR()/createFIR() result), not from a class. The
# model is the class ``Filter``; the design's name is the symbol's name,
# the block's label and its one parameter, ``design``. Pins: the signal
# clock cp, the update clock cu and one input per parameter of the
# design (Anton, 2026-11-17, decisions A and B).
SIGNAL_CLOCK = CLOCK_PIN
UPDATE_CLOCK = "cu"
FILTER_CLASS = "Filter"
FILTER_PINS = ("x", "y", SIGNAL_CLOCK, UPDATE_CLOCK)


def _default_text(value) -> str:
    """The parameter default as the block shows it."""
    if value is inspect.Parameter.empty or value is None:
        return ""
    if isinstance(value, float):
        return "%g" % value
    if isinstance(value, str):
        return value
    return repr(value)


def declaration(cls) -> dict:
    """The declaration of function class *cls* as plain data: name,
    kind ("algebraic" or "clocked"), inputs, outputs, params
    ``[(name, default), ...]`` and types ``{pin: dtype name}`` for EVERY
    signal pin, float64 included: a symbol pin without a type entry is
    untyped (a port, a probe), a function pin never is."""
    from SLiCAP.system.function import Function
    if not (inspect.isclass(cls) and issubclass(cls, Function)) or cls.kind is None:
        raise TypeError("%r is not a function class" % (cls,))
    params = []
    for p in list(inspect.signature(cls.__init__).parameters.values())[1:]:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue                        # the waveform parameters of Signal
        params.append((p.name, _default_text(p.default)))
    types = {pin: np.dtype(cls.types.get(pin, np.float64)).name
             for pin in tuple(cls.inputs) + tuple(cls.outputs)}
    return {"name": cls.__name__, "kind": cls.kind,
            "inputs": list(cls.inputs), "outputs": list(cls.outputs),
            "params": params, "types": types,
            "doc": (inspect.getdoc(cls) or "").split("\n")[0]}


# ---- the drawing of a block (Specs 9.5) --------------------------------------

G = 10                    # the grid step of the layout (two fine grid units)
STUB = 10                 # pin stub, box edge to node
_CHARW = 3.2              # approximate width of a pin-name character
_MARK = 4                 # depth of the dynamic-input mark


def block_svg(name, inputs, outputs, clocked, controls=(), prefix=PREFIX,
              model=None, params_field="", description="", types=None,
              names=(), extra=None) -> str:
    """The symbol file text of a block with the layout of Specs 9.5
    (Anton, 2026-11-17, decisions A and B): signal inputs on the left and
    outputs on the right, one row of 2 G per signal; for a clocked block
    the signal clock ``cp`` on the left one grid step above the bottom
    of the signal part, with the dynamic-input mark; a block with
    *controls* (the parameter pins of a programmable filter) has a
    horizontal line under the signal part and a parameter part of 2 G
    below it, with the update clock ``cu`` leftmost on the bottom edge,
    marked, and the controls 3 G from it and 2 G apart. Pin names are
    drawn inside the box by the editor (data-show-pinnames). *types* maps
    every signal pin to its data type; the clock pins get ``clock``."""
    inputs, outputs, controls = list(inputs), list(outputs), list(controls)
    ports = inputs + outputs + ([CLOCK_PIN] if clocked else [])
    if controls:
        ports += [UPDATE_CLOCK] + controls
    m = max(len(inputs), len(outputs), 1)
    hs = 2 * G * m + (2 * G if clocked else 0)          # the signal part
    total = hs + (2 * G if controls else 0)
    hh = total / 2
    name_w = (max([len(p) for p in inputs], default=0)
              + max([len(p) for p in outputs], default=0)) * _CHARW + 3 * 6.0
    hw = max(2 * G, G * -(-name_w // (2 * G)),
             G * (len(controls) + 2) if controls else 0)
    top, bottom = -hh, hh
    line = top + hs

    def f(v):
        return "%g" % v

    pos = {}
    for i, pin in enumerate(inputs):
        pos[pin] = (-hw, top + G + 2 * G * i, -hw - STUB, top + G + 2 * G * i)
    for i, pin in enumerate(outputs):
        pos[pin] = (hw, top + G + 2 * G * i, hw + STUB, top + G + 2 * G * i)
    if clocked:
        pos[CLOCK_PIN] = (-hw, line - G, -hw - STUB, line - G)
    if controls:
        pos[UPDATE_CLOCK] = (-hw + G, bottom, -hw + G, bottom + STUB)
        for i, pin in enumerate(controls):
            x = -hw + G + 3 * G + 2 * G * i
            pos[pin] = (x, bottom, x, bottom + STUB)
    lines = [f'<rect x="{f(-hw)}" y="{f(top)}" width="{f(2 * hw)}" '
             f'height="{f(total)}" fill="none" stroke="black" stroke-width="1"/>']
    if controls:
        lines.append(f'<line x1="{f(-hw)}" y1="{f(line)}" x2="{f(hw)}" y2="{f(line)}" '
                     f'stroke="black" stroke-width="1"/>')
    lines.append("")
    lines.append("<!-- Pins -->")
    dirs = {p: "in" for p in inputs + controls}       # controls are inputs too
    dirs.update({p: "out" for p in outputs})
    for port in ports:
        ex, ey, nx, ny = pos[port]
        lines.append(f'<line x1="{f(ex)}" y1="{f(ey)}" x2="{f(nx)}" y2="{f(ny)}" '
                     f'stroke="black" stroke-width="1"/>')
        if port in dirs:
            lines.append(_arrowhead(ex, ey, nx, ny, dirs[port] == "in", f))
        elif port == CLOCK_PIN:          # the dynamic-input mark, on the left edge
            lines.append(f'<polyline points="{f(ex)} {f(ey - 3)}  {f(ex + _MARK)} {f(ey)}  '
                         f'{f(ex)} {f(ey + 3)}" fill="none" stroke="black" stroke-width="1"/>')
        else:                            # the update clock, on the bottom edge
            lines.append(f'<polyline points="{f(ex - 3)} {f(ey)}  {f(ex)} {f(ey - _MARK)}  '
                         f'{f(ex + 3)} {f(ey)}" fill="none" stroke="black" stroke-width="1"/>')
        dirs.setdefault(port, "in")
    lines.append("")
    for port in ports:
        _ex, _ey, nx, ny = pos[port]
        lines.append(f'<circle cx="{f(nx)}" cy="{f(ny)}" r="0.5" class="node" '
                     f'data-node="{port}"/>')
    all_types = dict(types or {})
    for port in ports:
        if port in (CLOCK_PIN, UPDATE_CLOCK):
            all_types[port] = CLOCK_TYPE
        elif port not in all_types:
            all_types[port] = FLOAT
    return symbol_file_svg(name, prefix, ports, model or "%s|1" % name,
                           params_field, all_types, dirs,
                           description.replace('"', "'"), "\n      ".join(lines),
                           names=names, extra=extra)


def symbol_svg(cls) -> str:
    """The symbol file text of function class *cls*."""
    d = declaration(cls)
    description = "%s function: %s" % (d["kind"].capitalize(), d["doc"] or d["name"])
    return block_svg(d["name"], d["inputs"], d["outputs"], d["kind"] == "clocked",
                     params_field=";".join("%s|%s|1|1" % kv for kv in d["params"]),
                     description=description, types=d["types"])


def design_declaration(design) -> dict:
    """The declaration of the filter block of *design* (a
    ``FilterResult`` with a name): name, inputs ``["x"]``, outputs
    ``["y"]``, ``controls`` (the parameter pins, the design's parameters
    in alphabetical order), ``types`` for every pin and ``doc``. A
    design without parameters has no update clock and no controls."""
    name = getattr(design, "name", None)
    if not name:
        raise ValueError("the filter design needs a name (createIIR(..., "
                         "name=...)): it names the block's symbol")
    controls = list(getattr(design, "params", []))
    clash = [p for p in controls if p in FILTER_PINS]
    if clash:
        raise ValueError("%s: the parameter%s %s of the design clash%s with "
                         "the pins of a filter block; rename %s in the circuit"
                         % (name, "s" if len(clash) > 1 else "", ", ".join(clash),
                            "" if len(clash) > 1 else "es",
                            "them" if len(clash) > 1 else "it"))
    types = {"x": FLOAT, "y": FLOAT, SIGNAL_CLOCK: CLOCK_TYPE}
    if controls:
        types[UPDATE_CLOCK] = CLOCK_TYPE
        types.update({p: FLOAT for p in controls})
    kind = getattr(design, "dataType", "iir").upper()
    method = getattr(design, "method", None) or getattr(design, "window", "")
    return {"name": name, "inputs": ["x"], "outputs": ["y"],
            "controls": controls, "types": types,
            "doc": "%s filter %s (%s)%s" % (
                kind, name, method,
                ", parameters " + ", ".join(controls) if controls else "")}


def design_ports(controls) -> list:
    """The pins of a filter block with the parameter pins *controls*, in
    symbol order: x, y, cp, then cu and the controls when there are any."""
    ports = ["x", "y", SIGNAL_CLOCK]
    if controls:
        ports += [UPDATE_CLOCK] + list(controls)
    return ports


# The design of a filter block is a library file of the sheet (Specs
# 10.3.1, Anton, 2026-11-19: "the equivalent of a SLiCAP, NGspice library
# definition would be a Python import"): the file assigns the design to
# the block's name. The symbol holds the pins and, for the descent, the
# circuit schematic the design was made from (10.3.8); the block holds
# nothing but its name. The design properties as hidden parameters of
# the block with the lines in the symbol (2026-11-18) were REPLACED: the
# name and the properties sat in two places and the copies disagreed.


def design_symbol_svg(design, schematic="") -> str:
    """The symbol file text of the filter block of *design* (a named
    ``FilterResult``), with the *schematic* of its design script for the
    descent (``system_script.design_schematic``)."""
    d = design_declaration(design)
    return filter_symbol_svg(d["name"], d["controls"], d["doc"], schematic)


def filter_symbol_svg(name, controls, doc="", schematic="") -> str:
    """The symbol file text of a filter block named *name* (the design's
    name, shown as the block's label) with the parameter pins
    *controls*: the layout of ``block_svg``, ``data-design="1"`` and the
    circuit *schematic* of the design for the descent."""
    return block_svg(name, ["x"], ["y"], True, controls,
                     description=doc or "Filter %s" % name,
                     extra={"design": "1", "schematic": schematic})


def design_controls(symbol) -> list:
    """The parameter pins of a filter block's *symbol*: its pins beyond
    x, y, cp and cu."""
    return [p for p in symbol.nodes if p not in FILTER_PINS]


def is_current_design(symbol, controls) -> bool:
    """Whether library *symbol*, a filter block, has the parameter pins
    *controls* (the design's parameters) with the right types."""
    ports = design_ports(controls)
    types = {"x": FLOAT, "y": FLOAT, SIGNAL_CLOCK: CLOCK_TYPE}
    if controls:
        types[UPDATE_CLOCK] = CLOCK_TYPE
        types.update({p: FLOAT for p in controls})
    return (list(symbol.nodes) == ports and dict(symbol.pin_types) == types
            and symbol.is_design)


def is_design_block(symbol) -> bool:
    """True for the symbol of a filter block generated from a design."""
    return bool(getattr(symbol, "is_design", False))


def is_old_design_block(symbol) -> bool:
    """True for a filter symbol of the 2026-11-18 form (model ``Filter``,
    the design name a parameter, the lines in the symbol): migrated to
    a library file on load (system_dialect.after_load)."""
    return symbol.model == FILTER_CLASS and "design" in symbol.params


def old_design_record(symbol, params=None) -> dict:
    """The design of an old filter symbol (``is_old_design_block``) as
    the migration needs it: ``name`` (the block's design parameter, or
    the symbol's name), ``lines``, ``source``, ``kind``, ``method``,
    ``length``, ``window``, ``schematic``."""
    import xml.etree.ElementTree as ET
    values = dict(symbol.param_defaults)
    values.update(params or {})
    out = {"name": str(values.get("design", "")).strip() or symbol.name,
           "lines": ET.fromstring(symbol.g_xml).get("data-lines", "")}
    for key in ("source", "kind", "method", "length", "window", "schematic"):
        out[key] = str(values.get(key, "")).strip()
    return out


def is_current(symbol, cls) -> bool:
    """Whether library *symbol* still matches the declaration of *cls*:
    the same pins in the same order, the same types and parameter names."""
    d = declaration(cls)
    ports = d["inputs"] + d["outputs"] + ([CLOCK_PIN] if d["kind"] == "clocked" else [])
    types = dict(d["types"])
    if d["kind"] == "clocked":
        types[CLOCK_PIN] = CLOCK_TYPE
    if list(symbol.nodes) != ports or dict(symbol.pin_types) != types:
        return False
    if cls.__name__ in FIXED_SYMBOLS and not symbol.params:
        return True          # its parameters belong to the dialect's editor
    return list(symbol.params) == [k for k, _ in d["params"]]


# ---- the wires: types and directions (Specs 5.1, 9.3) ------------------------

def cast_ok(src, dst, implicit=True) -> bool:
    """Whether an output of type *src* may drive an input of type *dst*:
    equal types always; with *implicit*, also a conversion that loses no
    value in numpy's safe sense (integer to wider integer, integer to
    float, float to wider float)."""
    if src == dst:
        return True
    if not implicit:
        return False
    try:
        return bool(np.can_cast(np.dtype(src), np.dtype(dst), "safe"))
    except TypeError:
        return False


def check_net(pins, implicit=True) -> list:
    """The rules for the pins on one wire. *pins* is
    ``[(label, type, direction), ...]`` with the type None for an untyped
    pin (a port, a probe) and the direction "in", "out" or None. Returns
    the rules the wire breaks, as messages, [] when none: every one of
    them, so that a pin added to a wire that already breaks a rule is a
    new message (the scene compares the messages before and after a
    gesture; 2026-11-19, was the first reason only).

    A clock wire carries clock pins only, with at most one source. A
    signal wire has at most one output; every typed input must accept
    the output's type (``cast_ok``). A wire without a typed output is
    not checked: its type comes from outside (a port)."""
    out = []
    clocks = [p for p in pins if p[1] == CLOCK_TYPE]
    if clocks:
        for sig in (p for p in pins if p[1] not in (None, CLOCK_TYPE)):
            out.append("A clock wire cannot connect to a signal pin: %s and %s."
                       % (clocks[0][0], sig[0]))
        sources = [p for p in clocks if p[2] == "out"]
        if len(sources) > 1:
            out.append("Two clock sources on one wire: %s."
                       % ", ".join(p[0] for p in sources))
        return out
    outs = [p for p in pins if p[2] == "out"]
    if len(outs) > 1:
        out.append("Two outputs on one wire: %s." % ", ".join(p[0] for p in outs))
    if not outs or outs[0][1] is None:
        return out
    label, src, _ = outs[0]
    for lbl, typ, direction in pins:
        if direction == "in" and typ is not None and not cast_ok(src, typ, implicit):
            why = ("the conversion may lose value" if implicit
                   else "implicit casts are off in the schematic properties")
            out.append("%s (%s) cannot drive %s (%s): %s. Insert a cast block."
                       % (label, src, lbl, typ, why))
    return out


# ---- where the classes come from --------------------------------------------

def builtin_classes(fixed=False, designs=False) -> list:
    """The function classes of ``SLiCAP.SLiCAPsystem``, in its order,
    without the classes that have a fixed library symbol unless *fixed*
    is True, and without the classes whose symbol comes from a design
    (the filter block) unless *designs* is True: they are not placed
    from the class."""
    import SLiCAP.SLiCAPsystem as mod
    from SLiCAP.system.function import Function
    out = []
    for name in mod.__all__:
        obj = getattr(mod, name, None)
        if (inspect.isclass(obj) and issubclass(obj, Function)
                and obj.kind is not None and obj.__module__ == mod.__name__
                and (designs or not getattr(obj, "from_design", False))
                and (fixed or name not in FIXED_SYMBOLS)):
            out.append(obj)
    return out


def project_classes(root) -> tuple:
    """The function classes of the project's ``lib/<Name>.py`` modules,
    one class per file named after it: ``(classes, problems)`` with
    *problems* a list of "file: reason" strings."""
    from SLiCAP.system.function import Function
    libdir = Path(root) / "lib"
    classes, problems = [], []
    for path in sorted(libdir.glob("*.py")) if libdir.is_dir() else []:
        if not is_class_file(path):
            continue        # a design file (Specs 10.3.1): an instruction file, not imported
        try:
            spec = importlib.util.spec_from_file_location("lib." + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:        # a user file: report, do not stop
            problems.append("%s: %s" % (path.name, exc))
            continue
        cls = getattr(module, path.stem, None)
        if inspect.isclass(cls) and issubclass(cls, Function) and cls.kind:
            classes.append(cls)
        else:
            problems.append("%s: no function class named %s" % (path.name, path.stem))
    return classes, problems


def is_class_file(path) -> bool:
    """Whether ``lib/<stem>.py`` declares a function class ``<stem>``, read
    from its text: a design file of a filter (``lib/<name>.py`` assigning
    a design, an instruction file with makeCircuit and doLaplace) lives
    in lib/ too and must not be imported to find out (the load of a
    diagram ran every design's circuit analysis four times, 2026-11-19)."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return re.search(r"^class\s+%s\b" % re.escape(path.stem), text, re.M) is not None


def class_named(name, root=None):
    """The function class *name*: a project class first, then a built-in."""
    if root is not None:
        for cls in project_classes(root)[0]:
            if cls.__name__ == name:
                return cls
    for cls in builtin_classes(fixed=True, designs=True):
        if cls.__name__ == name:
            return cls
    return None


# ---- the scaffold of a new function -----------------------------------------

def scaffold(name, kind, inputs, outputs, order=0, params=()) -> str:
    """The text of ``lib/<name>.py`` for a new function class: the kernels
    with the right signatures, the class with its declaration and the
    parameter tuple, and no methods (SystemExtensionSpecs.md 2.8). The
    user fills in the arithmetic in an editor."""
    inputs, outputs, params = list(inputs), list(outputs), list(params)
    clocked = kind == "clocked"
    base = "Clocked" if clocked else "Algebraic"
    k_out, k_upd = name.lower() + "_out", name.lower() + "_upd"
    ins = ", ".join(inputs)
    state = ", state" if clocked else ""
    par = "".join(", " + p for p in params)
    returns = ", ".join("0.0" for _ in outputs) or "None"
    article = "an" if kind[:1] in "aeiou" else "a"
    # The file is the user's: it names no spec section, which the user does
    # not have (Anton, 2026-11-21: "Specs 2.8" in every generated file).
    L = ['"""%s: %s %s function of the system diagram.' % (name, article, kind),
         "",
         "Generated by the schematic editor; fill in the kernels. The class",
         "declares the pins and the parameters, the base class runs the kernels.",
         '"""', "",
         "import numpy as np", "",
         "from SLiCAP.system import %s" % base, "", "",
         "def %s(%s%s%s):" % (k_out, ins, state, par),
         "    # the outputs%s from the inputs%s" % (
             " " + ", ".join(outputs) if outputs else "",
             " and the state" if clocked else ""),
         "    return %s" % returns, ""]
    if clocked:
        outs = "".join(", " + o for o in outputs)
        if order == 0:
            cells = "it has no state (order 0)"
        elif order == 1:
            cells = "it is state[0]"
        else:
            cells = "it is state[0] .. state[%d]" % (order - 1)
        L += ["", "def %s(%s%s, state%s):" % (k_upd, ins, outs, par),
              "    # move the state to the next cycle; %s" % cells,
              "    pass", ""]
    L += ["", "class %s(%s):" % (name, base),
          '    """%s."""' % name,
          "    inputs = %r" % (tuple(inputs),),
          "    outputs = %r" % (tuple(outputs),),
          "    kernels = (%s,)" % (k_out + (", " + k_upd if clocked else "")),
          ""]
    L.append("    def __init__(self%s):" % ("".join(", " + p for p in params)))
    L.append("        super().__init__(%s)" % ("order=%d" % order if clocked else ""))
    for p in params:
        L.append("        self.%s = %s" % (p, p))
    L.append("        self.params = (%s)" % "".join("self.%s, " % p for p in params))
    if clocked:
        L.append("        self.direct = set()        # outputs that read the inputs of the same tick")
    return "\n".join(L) + "\n"
