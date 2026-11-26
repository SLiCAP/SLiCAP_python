"""The run script of a system diagram: the netlist of the system dialect
(SystemExtensionSpecs.md 8.2, SystemExtensionDesign.md 9).

``build_run_script`` reads the blocks and wires of a ``.system_sch``
scene, flattens the hierarchical blocks over their own diagrams in
``lib/``, resolves the clock tree, checks the wires and writes a
readable Python file: imports, one ``build()`` that creates the clock
tree, the function instances with their parameters and the wires, and
a ``__main__`` that runs it from the command line. The file goes to the
project root as ``<stem>.py`` (Anton, 2026-11-16: "Export script
creates the run script in the project root"), where
``sl.runSystem("<stem>", ...)`` of an instruction file imports it.

ONE script per diagram, many instructions: the script describes the
system, the instruction selects what is stored and how long the run is
(Specs 6.3, 8.3), as one netlist serves many analyses. A script per
instruction, carrying the selection and the engine call, was the first
reading of Design 9 and was REPLACED by this split (2026-11-17).

The generator checks what the editor checks (the wire rules of
system_symbols.check_net, an input without a driver, a clock pin
without a clock) and nothing the engine checks (algebraic loops,
Specs 4.3). The clock tree of the flattened diagram is also what the
editor shows on the clock symbols (system_dialect.clock_annotations).

Local only (.git/info/exclude) until the simulator is released.
"""

import inspect
import re
from datetime import datetime
from pathlib import Path

from . import project
from . import system_symbols as symbols
from .connectivity import net_name_conflicts, resolve_nets, _rpt
from .instr_file import quoted
from .netlist import NetlistError

CLOCK = "CLK"                                # the reference clock, f_ref
DRIVEN_CLOCK = "CLKF"                        # ... whose frequency is a signal (Specs 15.1)
CLOCKS = (CLOCK, DRIVEN_CLOCK)
CLOCK_NODE = "CLKNODE"
NOT_A_FUNCTION = ("port", "PROBE", "0")      # on the diagram, not in the system
BLOCK_PREFIX = "X"                           # a hierarchical block


class Block:
    """One placed block of the flattened diagram: its name in the
    system (the instance path, ``X1.F2``), the component, the net of
    every pin and the scope its values are evaluated in: the instance
    path of the diagram it is drawn in, "" for the top diagram
    (``Flat.instances``, Specs 10.4.6)."""

    __slots__ = ("name", "comp", "symbol", "params", "nets", "scope")

    def __init__(self, name, comp, nets, scope=""):
        self.name = name
        self.comp = comp
        self.symbol = comp.symbol
        self.params = dict(comp.params)
        self.nets = nets                       # {pin: net name}
        self.scope = scope

    @property
    def model(self):
        return self.comp.model or self.symbol.name


class Flat:
    """The flattened diagram."""

    def __init__(self):
        self.functions = []      # Block, the function blocks
        self.clocks = []         # Block, the reference clocks
        self.nodes = []          # Block, the clock nodes
        self.probes = []         # Block, the probes (live view, later)
        self.classes = {}        # class name -> class
        self.designs = {}        # block name -> (design name, parameter pins)
        self.labels = {}         # net -> the label the user gave the wire
        self.clock_exprs = {}    # clock node -> {f_ref | m | d | phase: expression text}
        self.libraries = []      # the library files of the child diagrams, in order
        # instance path -> (parent instance path, the values given on the
        # block, the child diagram's own table), parents first: the scopes
        # the run script makes with Scope.child (Specs 10.4.6)
        self.instances = {}
        self.errors = []

    def updater_name(self, block_name):
        """The engine name of the update half of filter block
        *block_name* (Specs 10.3.6: one block, two functions)."""
        return block_name + ".update"

    def signals(self):
        """The storable signals: ``{name: "block.output"}`` for every
        output of a function block, in block order. The name is the
        label of the wire, the signal name of the diagram (Specs 9.2;
        Anton, 2026-11-17), or the output itself when the wire has no
        label. A clock is no signal. A block with outputs only, a
        constant, is a held value that never fires (Specs 6.1.3): there
        is nothing to record, so it is not offered (Anton, 2026-11-17:
        "K1 output CAN be stored according to the dialog")."""
        out = {}
        for b in self.functions:
            if all(b.symbol.pin_dirs.get(p) == "out" for p in b.symbol.nodes):
                continue
            for p in b.symbol.nodes:
                if (b.symbol.pin_dirs.get(p) == "out"
                        and b.symbol.pin_types.get(p) != symbols.CLOCK_TYPE):
                    ref = "%s.%s" % (b.name, p)
                    out[self.labels.get(b.nets[p], ref)] = ref
        return out


# ---- flattening --------------------------------------------------------------

def _natural(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def _net_map(components, wires):
    conflicts = net_name_conflicts(components, wires)
    if conflicts:
        raise NetlistError(["net with several names: " + ", ".join(c)
                            for c in conflicts])
    return resolve_nets(components, wires)


def _load_child(path):
    """The scene of a hierarchical block's own diagram, loaded as the
    netlist export loads a schematic, without touching the app-wide
    current schematic."""
    from .schematic_data import SchematicData
    from .symbol_library import build_library
    from .canvas import SchematicScene
    from .config import Style
    from .component_item import ComponentItem
    from .wire_item import WireItem
    data = SchematicData.load(path)
    library = build_library(path, sch_type="system")
    scene = SchematicScene()
    scene.sch_type = "system"
    scene.style = Style(project.ini_path_for(path))
    scene.cache_dir = project.cache_path_for(path)
    missing = scene.load_file_data(data, library)
    if missing:
        raise NetlistError(["%s: no symbol definition for %s"
                            % (path.name, ", ".join(sorted(set(missing))))])
    items = scene.items()
    return ([i for i in items if isinstance(i, ComponentItem)],
            [i for i in items if isinstance(i, WireItem)], scene)


def flatten(components, wires, root, flat=None, prefix="", port_nets=None,
            seen=(), descend=True):
    """Collect the blocks of a diagram and of the diagrams of its
    hierarchical blocks into one ``Flat``. Nets of a child diagram are
    prefixed with the instance path; a child net a port symbol sits on
    is the parent net the block's pin is wired to. With *descend* False
    the hierarchical blocks are left out and the classes are not
    looked up: the view of one diagram, for the clock labels."""
    from PySide6.QtCore import QPointF
    flat = flat if flat is not None else Flat()
    root = Path(root)
    net_map = _net_map(components, wires)

    def local_net(point):
        return net_map.get(_rpt(point), "?")

    def net_of(comp, idx):
        local = local_net(comp.pin_scene_pos()[idx])
        if port_nets is not None and local in port_nets:
            return port_nets[local]
        return prefix + local

    for w in wires:
        if w.net_name and w.points:
            local = local_net(w.points[0])
            net = (port_nets[local] if port_nets is not None and local in port_nets
                   else prefix + local)
            flat.labels.setdefault(net, prefix + w.net_name)

    scope = prefix[:-1] if prefix else ""        # the instance this diagram is
    for comp in sorted(components, key=lambda c: _natural(c.instance_id)):
        kind = comp.symbol_name
        name = prefix + comp.instance_id
        pins = list(comp.node_names())
        nets = {p: net_of(comp, i) for i, p in enumerate(pins)}
        if kind in NOT_A_FUNCTION:
            if kind == "PROBE":
                flat.probes.append(Block(name, comp, nets))
            continue
        if kind in CLOCKS:
            flat.clocks.append(Block(name, comp, nets, scope))
            continue
        if kind == CLOCK_NODE:
            flat.nodes.append(Block(name, comp, nets, scope))
            continue
        if comp.prefix == BLOCK_PREFIX:
            if not descend:
                continue
            child = root / "lib" / (comp.model + ".system_sch")
            if not child.is_file():
                flat.errors.append("%s: the diagram of block %s, lib/%s, is "
                                   "missing" % (name, comp.model, child.name))
                continue
            if comp.model in seen:
                flat.errors.append("%s: block %s contains itself"
                                   % (name, comp.model))
                continue
            try:
                c_comps, c_wires, scene = _load_child(child)
            except NetlistError as exc:
                flat.errors += exc.errors
                continue
            # the library block of a child diagram counts as the parent's:
            # the designs its blocks use come from its own entries, at any
            # depth (Anton, 2026-11-19: "like SLiCAP and NGspice, hierarchy
            # can be unlimited"); the run script lists them all
            from .library_item import LibraryItem
            from .parameter_item import ParameterItem
            for file in library_files([i for i in scene.items()
                                       if isinstance(i, LibraryItem)]):
                if file not in flat.libraries:
                    flat.libraries.append(file)
            # the scope of the child: what the block passes, in the
            # parent's scope, over the child's own table (Specs 10.4.6)
            given = {k: str(v).strip() for k, v in comp.params.items()
                     if not k.startswith("_") and str(v).strip()}
            table = sheet_params([i for i in scene.items()
                                  if isinstance(i, ParameterItem)])
            flat.instances[name] = (scope, given, table)
            c_map = _net_map(c_comps, c_wires)
            c_ports = {}
            for pc in c_comps:
                if pc.symbol_name == "port":
                    pname = pc.params.get("name", "").strip()
                    if pname:
                        c_ports[pname] = c_map.get(
                            _rpt(pc.mapToScene(QPointF(0.0, 0.0))), "?")
            child_port_nets = {}
            for p in pins:
                if p not in c_ports:
                    flat.errors.append("%s: lib/%s has no port %s"
                                       % (name, child.name, p))
                    continue
                child_port_nets[c_ports[p]] = nets[p]
            flatten(c_comps, c_wires, root, flat, name + ".", child_port_nets,
                    seen + (comp.model,))
            continue
        if comp.prefix not in symbols.BLOCK_PREFIXES:
            flat.errors.append("%s: %s is not a block of a system diagram"
                               % (name, kind))
            continue
        block = Block(name, comp, nets, scope)
        if symbols.is_design_block(block.symbol):
            # a filter block (Specs 10.3.3): the design names the symbol,
            # the parameter pins are the pins beyond x, y, cp and cu; its
            # class is Filter, the design comes from a library file of the
            # sheet at run time (10.3.1). Known in the one-diagram view
            # too: its cu net is a pacing domain, which the clock labels
            # must leave out of the hyperperiod
            flat.designs[name] = (block.symbol.name, symbols.design_controls(block.symbol))
            if descend and block.model not in flat.classes:
                import SLiCAP.SLiCAPsystem as sls
                flat.classes[block.model] = sls.Filter
            flat.functions.append(block)
            continue
        if symbols.is_old_design_block(block.symbol):
            flat.errors.append("%s: the filter symbol %s is of the 2026-11-18 form; "
                               "open the diagram in the editor, which moves its "
                               "design to a library file" % (name, block.symbol.name))
            continue
        if not descend:
            flat.functions.append(block)
            continue
        if block.model not in flat.classes:
            cls = symbols.class_named(block.model, root)
            if cls is None:
                flat.errors.append("%s: no function class %s in SLiCAP or "
                                   "lib/%s.py" % (name, block.model, block.model))
                continue
            if (not getattr(cls, "from_design", False)
                    and not symbols.is_current(block.symbol, cls)):
                flat.errors.append("%s: the symbol of %s does not match the "
                                   "class; reopen the diagram to regenerate it"
                                   % (name, block.model))
                continue
            flat.classes[block.model] = cls
        flat.functions.append(block)
    return flat


# ---- the clock tree ----------------------------------------------------------

def _number(text):
    """A parameter value in SLiCAP notation as a float, None for an
    expression or an empty field."""
    from SLiCAP.SLiCAPlex import _scale_float
    try:
        return _scale_float(str(text or "").strip())
    except ValueError:
        return None


def _is_expression(text) -> bool:
    """A non-empty value that is not a plain number and holds no "?": an
    expression in parameters, resolved at build time (Specs 10.4)."""
    text = str(text or "").strip()
    return bool(text) and "?" not in text and _number(text) is None


def clock_tree(flat, provisional=False, symbolic=False):
    """The ``ClockTree`` of the flattened diagram and the clock node of
    every clocked net: ``(tree, node_of_net, problems, provisional)``.
    The reference clock is the root ``"ref"``; a node is named after its
    block; a net that clocks a function is a domain, with the node's
    phase. *tree* is None without a usable reference; a node the tree
    does not reach is absent from *node_of_net* and listed in
    *problems*.

    A value of f_ref, m, d or phase may be an expression in the sheet's
    parameters (Specs 10.4). With *symbolic* True, the generator's view,
    such a value takes a placeholder (1, or 0 for the phase) so the
    structure of the tree is known, and the text goes to
    ``flat.clock_exprs`` for the run script, which resolves it at build
    time. Without it, the editor's view, the tree has no values and the
    labels show "—" until a run (10.4.9).

    With *provisional* True and no function clocked yet, every end node,
    a node (or the reference) whose net feeds no further node, counts as
    a domain, and the last value returned is True: the master tick the
    clock scheme would need, shown while the user shapes the scheme
    (Anton, 2026-11-17). The generator never asks for it."""
    from SLiCAP.system.clock import ClockTree
    problems = []
    clocked, pacing = set(), set()
    for b in flat.functions:
        for pin, typ in b.symbol.pin_types.items():
            if typ == symbols.CLOCK_TYPE and b.symbol.pin_dirs.get(pin) == "in":
                # the update clock of a filter block paces the run (Specs
                # 10.3.6); its net is a pacing domain
                if b.name in flat.designs and pin == symbols.UPDATE_CLOCK:
                    pacing.add(b.nets[pin])
                else:
                    clocked.add(b.nets[pin])
    for net in sorted(clocked & pacing):
        problems.append("the clock on net %s is a signal clock of one block "
                        "and the update clock of another; an update clock "
                        "needs a node of its own" % net)
    clocked |= pacing
    if len(flat.clocks) != 1:
        problems.append("a system has one reference clock (CLK); found %d"
                        % len(flat.clocks))
        return None, {}, problems, False
    ref = flat.clocks[0]
    flat.clock_exprs = {}
    if ref.comp.symbol_name == DRIVEN_CLOCK:
        # the frequency is the signal on its input f: the engine takes it at the
        # start of the run; a placeholder gives the tree its structure
        flat.clock_exprs[ClockTree.ROOT] = {"f_ref": None}
        f_ref = 1.0
    else:
        f_ref = _number(ref.params.get("f_ref"))
        if f_ref is None and symbolic and _is_expression(ref.params.get("f_ref")):
            flat.clock_exprs[ClockTree.ROOT] = {"f_ref": str(ref.params["f_ref"]).strip()}
            f_ref = 1.0
    if f_ref is None or f_ref <= 0:
        problems.append("%s: f_ref = %r is not a frequency"
                        % (ref.name, ref.params.get("f_ref")))
        return None, {}, problems, False
    tree = ClockTree(f_ref)
    node_of_net = {ref.nets["clk"]: ClockTree.ROOT}
    phase_of = {ClockTree.ROOT: 0}
    pending, progress = list(flat.nodes), True
    while pending and progress:
        progress = False
        for cn in list(pending):
            parent = node_of_net.get(cn.nets["in"])
            if parent is None:
                continue
            pending.remove(cn)
            progress = True
            m, d = _number(cn.params.get("m", "1")), _number(cn.params.get("d", "1"))
            ph = _number(cn.params.get("phase", "0"))
            if symbolic:
                exprs = {}
                for key, value, fill in (("m", m, 1), ("d", d, 1), ("phase", ph, 0)):
                    text = str(cn.params.get(key, "")).strip()
                    if value is None and _is_expression(text):
                        exprs[key] = text
                if exprs:
                    flat.clock_exprs[cn.name] = exprs
                    m = 1 if "m" in exprs else m
                    d = 1 if "d" in exprs else d
                    ph = 0 if "phase" in exprs else ph
            if (None in (m, d, ph) or m < 1 or d < 1 or m != int(m)
                    or d != int(d) or ph != int(ph)):
                problems.append("%s: m, d and phase must be positive integers "
                                "(m=%s, d=%s, phase=%s)" % (
                                    cn.name, cn.params.get("m"),
                                    cn.params.get("d"), cn.params.get("phase")))
                continue
            tree.node(cn.name, parent, int(m), int(d))
            node_of_net[cn.nets["out"]] = cn.name
            phase_of[cn.name] = int(ph)
    for cn in pending:
        problems.append("%s: not reached from the reference clock" % cn.name)
    # a placed block whose clock pin the tree does not reach clocks nothing
    guessed = provisional and not (clocked & set(node_of_net))
    if guessed:
        fed = {cn.nets["in"] for cn in flat.nodes if cn.nets["in"] in node_of_net}
        clocked = set(node_of_net) - fed             # the end nodes
    for net, node in node_of_net.items():
        if net in clocked:
            tree.domain(node, phase_of[node], pacing=net in pacing)
    return tree, node_of_net, problems, guessed


# ---- the wires ---------------------------------------------------------------

def wiring(flat, implicit_casts=True):
    """``(connections, domain_of_block, errors)``: one ``(src, out, dst,
    inp)`` per driven input, the clock domain of every clocked block,
    and the wire rules (system_symbols.check_net) applied to every net,
    an input without a driver, a clock pin without a clock node (an
    unconnected clock pin is one: its net has no node). The clock tree
    is the generator's symbolic view (``clock_tree``)."""
    tree, node_of_net, errors, _ = clock_tree(flat, symbolic=True)
    pins = {}
    for b in flat.functions:
        for pin, net in b.nets.items():
            pins.setdefault(net, []).append(
                ("%s.%s" % (b.name, pin), b.symbol.pin_types.get(pin),
                 b.symbol.pin_dirs.get(pin), b, pin))
    for cn in flat.nodes:
        pins.setdefault(cn.nets["in"], []).append(
            (cn.name + ".in", symbols.CLOCK_TYPE, "in", cn, "in"))
        pins.setdefault(cn.nets["out"], []).append(
            (cn.name + ".out", symbols.CLOCK_TYPE, "out", cn, "out"))
    for ck in flat.clocks:
        pins.setdefault(ck.nets["clk"], []).append(
            (ck.name + ".clk", symbols.CLOCK_TYPE, "out", ck, "clk"))
        if "f" in ck.nets:
            # the driven clock (Specs 15.1): its frequency input f, a signal
            # pin that must be driven like any input
            pins.setdefault(ck.nets["f"], []).append(
                (ck.name + ".f", "float64", "in", ck, "f"))
    connections, domains = [], {}
    for net in sorted(pins):
        entries = pins[net]
        broken = symbols.check_net([e[:3] for e in entries], implicit_casts)
        if broken:
            errors += broken
            continue
        if any(e[1] == symbols.CLOCK_TYPE for e in entries):
            node = node_of_net.get(net)
            for label, _typ, direction, b, pin in entries:
                if direction == "in" and b in flat.functions:
                    if b.name in flat.designs and pin == symbols.UPDATE_CLOCK:
                        if node is not None:
                            domains[flat.updater_name(b.name)] = node
                        # no clock on cu: the coefficients are computed once
                    elif node is None:
                        errors.append("%s: no clock on this pin" % label)
                    else:
                        domains[b.name] = node
            continue
        outs = [e for e in entries if e[2] == "out"]
        ins = [e for e in entries if e[2] == "in"]
        if not outs:
            for label, _t, _d, _b, _p in ins:
                errors.append("%s: not driven" % label)
            continue
        src = outs[0]
        for dst in ins:
            name = dst[3].name
            if name in flat.designs and dst[4] in flat.designs[name][1]:
                name = flat.updater_name(name)     # a parameter pin: the update half
            connections.append((src[3].name, src[4], name, dst[4]))
    return connections, domains, tree, errors


# ---- the parameters ------------------------------------------------------------

def _defaults(cls, params):
    """The default of every constructor parameter of *cls*, plus the
    waveform parameters of a ``Signal``."""
    out = {}
    for p in list(inspect.signature(cls.__init__).parameters.values())[1:]:
        if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            out[p.name] = p.default
    if cls.__name__ == "Signal":
        from SLiCAP.SLiCAPsystem import WAVEFORMS
        out.update(WAVEFORMS.get(params.get("waveform", "").strip(), {}))
    return out


GLOBAL_PARAMS = ("q", "k", "c", "mu_0", "epsilon_0", "epsilon_SiO2", "T", "U_T")
# the global SLiCAP parameters of SLiCAPmodels.lib: a bare name among them
# is a parameter, not a word (Specs 10.4.4)


def _literal(text, default, params=(), what="", scope="P"):
    """The Python text of a block parameter: a number in SLiCAP notation
    as a float, a text where the class expects one, a ``{...}`` as a
    Python expression, and an expression in parameters as a call on the
    scope of the run, ``P("expr")`` or ``P.int("expr")`` by the type of
    the class's default (Specs 10.4.5); *scope* is the variable of the
    scope the block is evaluated in, ``P`` or the scope of its instance
    (10.4.6). A bare word where the class has no default is a word
    ("sine") unless it names a parameter of the diagram (*params*) or a
    global one. None for an empty field."""
    text = str(text).strip()
    if not text:
        return None
    if "?" in text:
        raise ValueError("value '?'")
    value = _number(text)
    if value is not None:
        return repr(value)
    if text.startswith("{") and text.endswith("}"):
        return text[1:-1].strip()
    if text[0] in "[(":
        return text                       # an array of values, as written (no parameters inside)
    if isinstance(default, str):
        return repr(text)
    unknown = default is None or default is inspect.Parameter.empty
    if (unknown and text.isidentifier() and text.islower()
            and text not in params and text not in GLOBAL_PARAMS):
        return repr(text)                 # a word: "sine", "gaussian"
    if isinstance(default, bool):
        return text
    if isinstance(default, int):
        return ('%s.int(%r, %r)' % (scope, text, what) if what
                else '%s.int(%r)' % (scope, text))
    return '%s(%r, %r)' % (scope, text, what) if what else '%s(%r)' % (scope, text)


def _scope_var(instance) -> str:
    """The run script's variable of the scope of *instance*: ``P`` for
    the top diagram, ``P_X1``, ``P_X1_X2`` for the diagram of a block."""
    return "P_" + instance.replace(".", "_") if instance else "P"


def _scope_names(flat, instance, params):
    """The parameter names a block drawn in *instance* can use: the
    sheet's table for the top diagram, else what the block passes and
    the child diagram's own table."""
    if not instance:
        return params
    _parent, given, table = flat.instances[instance]
    return set(given) | set(table)


def _arguments(block, cls, params=(), scope="P"):
    """The constructor call's argument text of *block*; *params* are the
    names of the parameters its diagram defines, *scope* the variable of
    its scope."""
    defaults = _defaults(cls, block.params)
    if cls.__name__ == "Signal" and not block.params.get("waveform", "").strip():
        raise ValueError("%s: the signal has no waveform yet; double-click the "
                         "symbol to define it" % block.name)
    parts = []
    for key, value in block.params.items():
        if key.startswith("_"):
            continue
        try:
            lit = _literal(value, defaults.get(key), params, "%s.%s" % (block.name, key),
                           scope)
        except ValueError as exc:
            raise ValueError("%s: parameter %s has %s" % (block.name, key, exc))
        if lit is not None:
            parts.append("%s=%s" % (key, lit))
    return ", ".join(parts)


# ---- the script ------------------------------------------------------------------

def sheet_params(prms) -> dict:
    """The parameter table of the sheet, ``{name: value text}`` in table
    order, from its parameter items (Specs 10.4.3)."""
    out = {}
    for item in prms or ():
        for name, value in getattr(item, "params", []) or []:
            name, value = str(name).strip(), str(value).strip()
            if name:
                out[name] = value
    return out


def build_run_script(components, wires, input_path, root=None,
                     implicit_casts=True, libs=(), prms=()) -> str:
    """The run script text of the diagram in *components* and *wires*,
    saved as *input_path*; *libs* are the sheet's library items, whose
    entries name the library files the designs of the filter blocks
    come from (Specs 10.3.1); *prms* its parameter items, the parameter
    table of the run script (10.4.3). Raises ``NetlistError`` with every
    problem found."""
    input_path = Path(input_path)
    root = Path(root) if root is not None else project.root_for(input_path)
    flat = flatten(components, wires, root)
    libraries = library_files(libs)
    libraries += [f for f in flat.libraries if f not in libraries]
    params = sheet_params(prms)
    connections, domains, tree, errors = wiring(flat, implicit_casts)
    if tree is None:                     # no usable reference clock: the problems
        raise NetlistError(flat.errors + errors)
    node_of_net = clock_tree(flat, symbolic=True)[1]
    if not tree.domains:
        errors.append("no function is clocked: the clock tree has no domain")
    lines_add = []
    for b in flat.functions:
        cls = flat.classes.get(b.model)
        if cls is None:
            continue
        dom = ", domain=%s" % quoted(domains[b.name]) if b.name in domains else ""
        if b.name in flat.designs:
            design, controls = flat.designs[b.name]
            lines_add.append("    blk = system.add(%s(check_design(designs, %s, %r)), %s%s)"
                             % (cls.__name__, quoted(design), controls,
                                quoted(b.name), dom))
            if controls:
                upd = flat.updater_name(b.name)
                if upd in domains:
                    lines_add.append("    system.add(blk.updater, %s, domain=%s)"
                                     % (quoted(upd), quoted(domains[upd])))
                else:
                    lines_add.append("    system.add(blk.updater, %s)   # no update "
                                     "clock: the coefficients once, at the start"
                                     % quoted(upd))
            continue
        try:
            args = _arguments(b, cls, _scope_names(flat, b.scope, params),
                              _scope_var(b.scope))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        lines_add.append("    system.add(%s(%s), %s%s)"
                         % (cls.__name__, args, quoted(b.name), dom))
    designs = sorted({d for d, _ in flat.designs.values()})
    errors += missing_designs(designs, libraries, root)
    if flat.errors or errors:
        raise NetlistError(flat.errors + errors)

    rel = Path(project.folder_rel("sch", root)) / input_path.name
    rel = rel.as_posix()
    stem = input_path.stem
    project_classes = sorted(n for n, c in flat.classes.items()
                             if c.__module__.startswith("lib."))
    signals = flat.signals()
    L = ['"""Run script of %s: the system of the diagram.' % rel,
         "",
         "Written by the SLiCAP schematic editor on %s and regenerated"
         % datetime.now().strftime("%Y-%m-%d %H:%M"),
         'by sl.makeCircuit("%s"); do not edit. An instruction file runs' % rel,
         'it with sl.runSystem("%s", ...); from the project root:' % stem,
         "",
         "    python %s.py 20000 %s" % (stem, " ".join(list(signals)[:2]) or "out"),
         "",
         "runs 20000 master ticks and stores the named signals in the",
         "results folder."]
    if designs:
        L += ["",
              "The filter blocks are made from the designs %s, which" % ", ".join(designs),
              "the library files of the diagram assign: build() runs those",
              "files as instruction files at the start of every run."]
    L += ['"""']
    L.append("from SLiCAP.SLiCAPsystem import *")
    L += ["from lib.%s import %s" % (n, n) for n in project_classes]
    L += ["",
          "SCHEMATIC = %s" % quoted(rel),
          "SIGNALS = %r" % (signals,),
          "# the storable signals: the wire's label (the signal name) or the output itself",
          "LIBRARIES = %r" % (libraries,),
          "# the library files of the diagram (its library block): the filter designs",
          "PARAMS = %r" % (params,),
          "# the parameter table of the sheet; params= of the run comes on top"]
    L += ["", "",
          "def build(implicit_casts=%r, params=None):" % bool(implicit_casts),
          '    """The clock tree, the functions and the wires of the diagram."""',
          "    P = Scope(PARAMS, params)"]
    for instance, (parent, given, table) in flat.instances.items():
        # the scope of a hierarchical block's diagram (Specs 10.4.6)
        L.append("    %s = %s.child(%r, %r, %r)"
                 % (_scope_var(instance), _scope_var(parent), given, table, instance))
    ref = flat.clocks[0]
    exprs = flat.clock_exprs
    scope_of_node = {cn.name: _scope_var(cn.scope) for cn in flat.nodes}

    def clock_value(node, key, number, what, integer=True):
        text = exprs.get(node, {}).get(key)
        if text is None:
            return "%d" % number if integer else repr(number)
        var = scope_of_node.get(node, "P")
        return ('%s.int(%r, %r)' % (var, text, what) if integer
                else '%s(%r, %r)' % (var, text, what))

    if exprs.get(tree.ROOT, {}).get("f_ref", "") is None:
        # the driven clock: the frequency is its signal (drive_clock below)
        L.append("    clocks = ClockTree(None)                # %s: the signal on f"
                 % ref.name)
    else:
        L.append("    clocks = ClockTree(%s)                  # %s"
                 % (clock_value(tree.ROOT, "f_ref", tree.f_ref, ref.name + ".f_ref",
                                integer=False), ref.name))
    for cn in flat.nodes:
        parent = node_of_net[cn.nets["in"]]
        m = clock_value(cn.name, "m", int(_number(cn.params.get("m", "1")) or 1), cn.name + ".m")
        d = clock_value(cn.name, "d", int(_number(cn.params.get("d", "1")) or 1), cn.name + ".d")
        L.append("    clocks.node(%s, %s, m=%s, d=%s)"
                 % (quoted(cn.name), quoted(parent), m, d))
    for node in tree.domains:
        L.append("    clocks.domain(%s, phase=%s%s)"
                 % (quoted(node),
                    clock_value(node, "phase", tree.phase(node), node + ".phase"),
                    ", pacing=True" if tree.is_pacing(node) else ""))
    L.append("    system = System(clocks, implicit_casts)")
    if designs:
        L.append("    designs = load_designs(LIBRARIES)")
    L += lines_add
    clock_names = {ck.name for ck in flat.clocks}
    for src, out, dst, inp in connections:
        if dst in clock_names:
            # the signal that gives the frequency of the driven reference
            # clock (Specs 15.1), after the functions: it sets the nominal
            L.append("    system.drive_clock(%s, %s)" % (quoted(src), quoted(out)))
            continue
        L.append("    system.connect(%s, %s, %s, %s)"
                 % (quoted(src), quoted(out), quoted(dst), quoted(inp)))
    L += ["    return system",
          "", "",
          'if __name__ == "__main__":',
          "    import sys",
          "    run_main(build, sys.argv[1:], stem=%s, signals=SIGNALS)" % quoted(stem),
          ""]
    return "\n".join(L)


# ---- the designs of the filter blocks (Specs 10.3.1, 10.3.2) ---------------

RUN_SCRIPT_HEAD = '"""Run script of '      # the first characters of every run script
IMPORT_DIRECTIVE = "import"                # the library entries of a system sheet


def design_runs(root, design_files) -> dict:
    """``{stem: {parameter: value text}}``: the run scripts in the project
    *root* whose ``LIBRARIES`` list one of *design_files*, with the sheet
    parameters of their diagram (``PARAMS``). These are the system diagrams
    a filter design runs in. Their parameters are the "system" values of
    the Make filter dialog, as ``sl.selectPars("<stem>", ...)`` reads them
    (Anton, 2026-11-25). The files are read, not run."""
    import ast
    wanted = {str(f) for f in design_files}
    out = {}
    for path in sorted(Path(root).glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.startswith(RUN_SCRIPT_HEAD):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        found = {}
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in ("LIBRARIES", "PARAMS")):
                try:
                    found[node.targets[0].id] = ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    pass
        if wanted & {str(f) for f in found.get("LIBRARIES") or []}:
            out[path.stem] = {str(k): str(v)
                              for k, v in dict(found.get("PARAMS") or {}).items()}
    return out


def library_files(libs) -> list:
    """The design files of a system sheet, in the order of its library
    block's entries: the "import" entries, which the run script runs for
    the designs. A "lib" entry, the declaration file of a hierarchical
    block until 2026-11-19 (REMOVED: the diagram is the block), is
    netlist text, not Python: the run script ran one and Python failed
    on its ``.subckt`` line (Anton, 2026-11-19, read as "T cannot be
    passed as a parameter"). Old sheets still list them."""
    out = []
    for lib in libs or ():
        for entry in lib.entries:
            file = (entry.get("file") or "").strip()
            if (entry.get("directive") == IMPORT_DIRECTIVE and file
                    and file not in out):
                out.append(file)
    return out


def missing_designs(designs, libraries, root) -> list:
    """One error line per design name no library file of the sheet
    assigns (``instr_file.bound_names`` on the file's text): what
    ``check_design`` would refuse at run time, found at netlist time.
    At run time every name of the file's namespace counts, however it was
    bound, so an annotated or a tuple assignment counts here too."""
    from .instr_file import bound_names
    if not designs:
        return []
    root = Path(root)
    assigned, missing_files = set(), []
    for file in libraries:
        path = root / file
        try:
            assigned |= bound_names(path.read_text(encoding="utf-8"))
        except OSError:
            missing_files.append(file)
    out = ["library file not found: %s" % f for f in missing_files]
    for design in designs:
        if design not in assigned:
            out.append("no library file of the diagram or its child diagrams "
                       "assigns the design %s (the libraries: %s); add its file "
                       "(System > Library...) or redefine the block (Design... "
                       "in its Properties)" % (design, ", ".join(libraries) or "none"))
    return out


def design_file_text(name, lines, source, kind="IIR", method="bilinear",
                     length=64, window="hamming", stationary=True, Ts=None) -> str:
    """The text of the design file ``lib/<name>.py``: the sl import, the
    instruction *lines* that assign the transfer to *source*, and the
    create line that assigns the design to *name*. *stationary* False
    writes ``stationary=False`` with the method zoh or foh (the
    coefficients follow the clock, Specs 15.3); *Ts*, a float or the
    name of a parameter pin, the stationary filter's own sample period."""
    # a number, or the name of the parameter pin that gives the period
    ts = ("" if Ts is None else ", Ts=%r" % Ts if isinstance(Ts, str)
          else ", Ts=%r" % float(Ts))
    if str(kind).upper() == "FIR":
        create = "createFIR(%s, length=%d, window=%s%s, name=%s)" % (
            source, int(length or 64), quoted(window or "hamming"), ts,
            quoted(name))
    elif not stationary:
        create = "createIIR(%s, method=%s, stationary=False, name=%s)" % (
            source, quoted(method if method in ("zoh", "foh") else "zoh"),
            quoted(name))
    else:
        create = "createIIR(%s, method=%s%s, name=%s)" % (
            source, quoted(method or "bilinear"), ts, quoted(name))
    return ("import SLiCAP as sl\n%s\n%s = sl.%s\n"
            % (lines.strip(), name, create))


def with_create_line(text, name, kind="IIR", method="bilinear", length=64,
                     window="hamming", stationary=True, Ts=None):
    """*text*, a design file, with its create line rewritten by
    ``design_file_text`` from the given choices: the lines before the
    statement that assigns *name* are kept, the create line's first
    argument is the source. None when *text* has no such line."""
    import ast
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for stmt in tree.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == name and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr in ("createIIR", "createFIR")
                and stmt.value.args):
            source = ast.get_source_segment(text, stmt.value.args[0])
            body = text.splitlines()[:stmt.lineno - 1]
            body = [l for l in body if l.strip() != "import SLiCAP as sl"]
            return design_file_text(name, "\n".join(body), source, kind, method,
                                    length, window, stationary, Ts)
    return None


_PROBE = r'''
import json, sys
file, name, out_path = sys.argv[1:4]
from SLiCAP.SLiCAPsystem import load_designs, filter_pins
d = load_designs([file])
if name not in d:
    raise NameError("%s does not assign the design %s (it assigns %s)"
                    % (file, name, ", ".join(sorted(d)) or "nothing"))
d = d[name]
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"params": filter_pins(d),
               "expr": str(d.laplace), "kind": str(d.dataType).upper(),
               "method": d.method or "", "length": d.length or "",
               "stationary": bool(getattr(d, "stationary", True)),
               "Ts": (getattr(d, "Ts", None) if getattr(d, "Ts", None) is not None
                      else getattr(d, "ts_param", None)),
               "window": d.window or ""}, f)
'''


def design_schematic(text):
    """The editor schematic a design script analyses: the file of its
    ``makeCircuit("<file>.slicap_sch")`` line, as ``circuit.schematic``
    holds it, or None. Read from the text, not run. The filter block opens
    it (Specs 10.3.8). It WAS ``FilterResult.schematic``, REMOVED
    2026-11-25 (Anton: the filter has a transfer; the schematic link
    belongs to the block)."""
    import ast
    from .instr_file import parse_calls
    try:
        calls = parse_calls(text)
    except SyntaxError:
        return None
    for call in calls:
        if call["func"] == "makeCircuit" and call["args"]:
            try:
                file = ast.literal_eval(call["args"][0])
            except (ValueError, SyntaxError):
                continue
            if isinstance(file, str) and file.endswith(".slicap_sch"):
                return file
    return None


def probe_design(root, file, name, timeout=600) -> dict:
    """Run the library *file* (relative to the project *root*) in a
    child process with the root as working directory, as the SLiCAP
    instruction dialogs build the circuit and as the run script runs it
    (``load_designs``; Specs 10.3.2: the pins are detected by running
    the file, at placement and after an edit), and report the design
    *name* it assigns: ``{"params", "expr", "kind", "method", "length",
    "stationary", "Ts", "window"}``; "params" are the parameter pins of
    the block (``SLiCAPsystem.filter_pins``). Raises ``NetlistError`` with
    the child's error when the file fails. The schematic of the design is
    read from its text, ``design_schematic()``."""
    import subprocess
    import sys
    import tempfile
    import json
    root = Path(root)
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "design.json"
        cmd = [sys.executable, "-c", _PROBE, str(file), name, str(out_path)]
        try:
            res = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                                 timeout=timeout,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            raise NetlistError(["%s did not finish in %d s" % (file, timeout)])
        if res.returncode != 0 or not out_path.exists():
            tail = [l for l in (res.stderr or res.stdout).strip().splitlines() if l.strip()]
            raise NetlistError(["%s failed:" % file] + tail[-6:])
        return json.loads(out_path.read_text(encoding="utf-8"))


def check_run_script_target(path) -> None:
    """Refuse to write the run script over a file the editor did not
    write: every run script starts with ``RUN_SCRIPT_HEAD``. In a test
    project the run script of a diagram overwrote the hand-written
    script of the same stem and then the instruction file of that name
    (Anton, 2026-11-18; Specs 10.3.9). Raises ``NetlistError``."""
    path = Path(path)
    if not path.exists():
        return
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:len(RUN_SCRIPT_HEAD)]
    except OSError:
        return
    if head != RUN_SCRIPT_HEAD:
        raise NetlistError([
            "%s exists and is not a run script written by the editor. The run "
            "script of a system diagram is <project root>/<diagram name>.py: "
            "rename that file, or rename the diagram." % path])


def signal_names(components, wires, root) -> dict:
    """The storable signals of a diagram, ``{name: "block.output"}``,
    for the run dialog. Raises ``NetlistError`` when the diagram cannot
    be flattened."""
    flat = flatten(components, wires, root)
    if flat.errors:
        raise NetlistError(flat.errors)
    return flat.signals()
