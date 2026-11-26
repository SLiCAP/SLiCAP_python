"""The sources of a trace set: the results of an instruction file that a
trace may use, and the ``sl.makeDataset()`` call that combines them
(TRACES.md phase 9, Anton, 2026-11-25).

A trace set is no longer built from ONE chosen result. Its expressions name
what they use with the dotted names of the Design data - ``AC1.V_out``,
``FLT1.H_fs``, ``LAPLACE1.laplace``, ``R1.Ix``, ``HS`` - and the sources
follow from those names. DATA (an NGspice run, a system run) lies on its own
points; a FUNCTION (a filter, a SLiCAP result, an expression in s, f or t)
is evaluated where needed. The rules are the core's (``makeDataset``); this
module only knows enough to write the call and to say beforehand what will
not combine.

Pure functions over the parsed instruction file (``instr_file.parse_calls``)
and its manifest section, so they can be tested without a window.
"""
from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field

from .instr_file import quoted, literal as _lit

# ── the results of an instruction file ────────────────────────────────────

# Results that carry numeric arrays straight away.
_NG_FUNCS = {"op", "dc", "ac", "tran", "noise"}
# the system-level run (sl.runSystem): numeric, swept over time
_SYSTEM_FUNCS = {"runSystem"}
# SLiCAP results are SYMBOLIC: they hold a formula (TRACES.md phase 6f);
# the value is the abscissa of their function
_SLICAP_FUNCS = {"doLaplace": "frequency", "doNumer": "frequency",
                 "doDenom": "frequency", "doNoise": "frequency",
                 "doTime": "t", "doImpulse": "t", "doStep": "t"}
# the functions of a SLiCAP result, per instruction: its own attributes,
# already Python identifiers (makeDataset columns NAME.<attribute>)
_SLICAP_SIGNALS = {"doLaplace": ["laplace"], "doNumer": ["numer"],
                   "doDenom": ["denom"], "doNoise": ["onoise", "inoise"],
                   "doTime": ["time"], "doImpulse": ["impulse"],
                   "doStep": ["stepResp"]}
# a filter made with sl.makeFilter(): its functions in frequency and its
# sample responses in time; not H_s and H_z (Anton, 2026-11-25: the same
# curve under a second name, and no sample period)
_FILTER_FUNCS = {"makeFilter"}
FILTER_SIGNALS = {"H_fs": "frequency", "H_fz": "frequency",
                  "impulse": "time", "stepResp": "time"}
# Abscissa of an NGspice analysis that does NOT reduce: what it swept.
_SWEEP_NAME = {"ac": "frequency", "noise": "frequency", "tran": "time",
               "fft": "frequency", "runSystem": "time"}
# the x axes of a system run's dataset (SystemResult.X_AXES)
SYSTEM_X = {"time": "time [s]", "tick": "master tick (integer)",
            "sample": "sample index of the domain (integer)"}

NGSPICE, SYSTEM, SLICAP, FILTER, EXPRESSION = (
    "ngspice", "system", "slicap", "filter", "expression")
#: sources that are DATA: they lie on their own points
DATA_KINDS = (NGSPICE, SYSTEM)


def result_entries(calls: list[dict]) -> list[dict]:
    """The result variables a trace can be built from: NGspice runs, SLiCAP
    (symbolic) analyses, system runs and filters (makeFilter)."""
    return [c for c in calls
            if (c["func"] in _NG_FUNCS or c["func"] in _SLICAP_FUNCS
                or c["func"] in _SYSTEM_FUNCS or c["func"] in _FILTER_FUNCS)
            and c["assigned"]]


def is_symbolic(entry: dict) -> bool:
    """True for a SLiCAP result: a formula, so it needs a sweep."""
    return entry.get("func") in _SLICAP_FUNCS


def is_filter(entry: dict) -> bool:
    """True for a filter (makeFilter)."""
    return entry.get("func") in _FILTER_FUNCS


def is_system(entry: dict) -> bool:
    """True for a system run (sl.runSystem): its signals lie in clock
    domains."""
    return entry.get("func") in _SYSTEM_FUNCS


def _result_kind(entry: dict) -> str:
    """Analysis kind, with 'fft' for a transient carrying fft=."""
    if entry["func"] == "tran" and entry.get("kwargs", {}).get("fft"):
        return "fft"
    return entry["func"]


def _abscissa(entry: dict) -> str:
    """The sweep variable this result provides."""
    if is_symbolic(entry):
        return _SLICAP_FUNCS[entry["func"]]
    return _SWEEP_NAME.get(_result_kind(entry), "")


def _is_stepped(entry: dict) -> bool:
    """True when the analysis steps, so its signals are 2-D and a goal
    function has more than one run to reduce: ``step=`` of an NGspice
    analysis, ``stepdict=`` of a SLiCAP instruction."""
    kwargs = entry.get("kwargs", {}) or {}
    return bool(kwargs.get("step") or kwargs.get("stepdict"))


def _step_name(entry: dict):
    """The stepped parameter of a result, or None (array stepping, none)."""
    kwargs = entry.get("kwargs", {}) or {}
    step = _lit(kwargs.get("step")) or _lit(kwargs.get("stepdict")) or {}
    if not isinstance(step, dict):
        return None
    name = step.get("param") or step.get("params")
    if isinstance(name, (list, tuple)):
        name = name[0] if len(name) == 1 else None
    return str(name) if name else None


def gain_type_of(entry) -> str:
    """The gain type a result statement asks for, '' for data that has none.

    A SLiCAP analysis carries one - ``transfer='asymptotic'``, defaulting to
    'gain' - and it decides the automatic COLOUR (ini.gaincolors). An NGspice
    run has none.
    """
    if not entry or not is_symbolic(entry):
        return ""
    transfer = _lit((entry.get("kwargs") or {}).get("transfer"))
    return str(transfer) if transfer else "gain"


def signal_names(entry: dict, section: dict) -> list[str]:
    """Signals of an NGspice or system result: what the RUN recorded, and
    nothing else.

    The manifest holds the keys the result actually produced. Two other
    sources were tried and REVERTED (Anton, 2026-08-01): deriving them from
    the netlist, and falling back to the analysis's ``save=`` list. A signal
    "can only exist after a run" - before that the dialog offers nothing, and
    says so.
    """
    if is_system(entry):
        return [s for signals in system_domains(entry, section).values()
                for s in signals]
    names = []
    for variable in section.get("variables", []):
        if variable.get("name") == entry["name"]:
            names += [a.get("name", "") for a in
                      variable.get("attributes", [])]
    return [n for n in names if n]


def system_domains(entry: dict, section: dict) -> dict:
    """``{clock domain: [signal, ...]}`` of a system run, from the result's
    ``domains`` record in the file's manifest *section*
    (SystemExtensionSpecs.md 6.9.3)."""
    out = {}
    for variable in section.get("variables", []):
        if variable.get("name") != entry["name"]:
            continue
        for attr in variable.get("attributes", []):
            if attr.get("name") != "domains":
                continue
            for domain in attr.get("attributes", []):
                fields = {f.get("name"): f.get("value", "")
                          for f in domain.get("attributes", [])}
                names = str(fields.get("signals", "")).split(",")
                out[domain.get("name", "")] = [n.strip() for n in names
                                               if n.strip()]
    return out


def param_names(entry: dict) -> list[str]:
    """Circuit parameters of an NGspice result, as simulated: read from the
    CORE netlist reader with the call's own ``params=`` overrides."""
    from SLiCAP.SLiCAPngspice import _netlist_par_defs
    args = entry.get("args") or []
    circuit = _lit(args[0]) if args else None
    if not isinstance(circuit, str):
        return []
    overrides = []
    for pair in _lit(entry["kwargs"].get("params")) or []:
        if isinstance(pair, (tuple, list)) and len(pair) == 2:
            overrides.append((str(pair[0]), str(pair[1])))
    try:
        par_defs = _netlist_par_defs(circuit, overrides)
    except Exception:
        return []
    return sorted(str(key) for key in par_defs)


# ── the sources ────────────────────────────────────────────────────────────

@dataclass
class Source:
    """One result a trace may use.

    *signals*: what the signal list offers - the simulator's names of an
    NGspice run, the attributes of a SLiCAP result or a filter. *axis*: the
    abscissa, "frequency", "time" or the x name of data ("" for a filter,
    whose axis follows the signal). *domains*: the clock domains of a
    system run with their signals.
    """
    name: str
    kind: str
    entry: dict | None = None
    signals: list = field(default_factory=list)
    domains: dict = field(default_factory=dict)
    axis: str = ""
    stepped: bool = False
    step_name: str | None = None
    gain: str = ""
    params: list = field(default_factory=list)


def _ngspice_axis(entry: dict) -> str:
    kind = _result_kind(entry)
    if kind == "dc":
        # the swept source is the second argument of sl.dc(...)
        args = entry.get("args") or []
        source = _lit(args[1]) if len(args) > 1 else None
        return "v-sweep" if not isinstance(source, str) else source
    if kind == "op":
        return ""
    return _SWEEP_NAME.get(kind, "")


def _expression_axis(symbols) -> str:
    """The axis of an expression variable from its free symbols, or ""
    when it is not a function of s, f or t alone."""
    import SLiCAP.SLiCAPconfigure as ini
    symbols = set(symbols)
    if symbols in ({str(ini.laplace)}, {str(ini.frequency)}):
        return "frequency"
    if symbols == {"t"}:
        return "time"
    return ""


def file_sources(calls: list[dict], section: dict) -> dict:
    """``{name: Source}`` of every result of the file, in file order, and
    of the expression variables in s, f or t the last run recorded."""
    out = {}
    for entry in result_entries(calls):
        name, func = entry["name"], entry["func"]
        if func in _NG_FUNCS:
            # the axis of the run is not one of its signals: the dataset
            # keeps it as its x, unprefixed (frequency, time)
            axis = _ngspice_axis(entry)
            signals = [s for s in signal_names(entry, section)
                       if s not in (axis, "frequency", "time")]
            out[name] = Source(name, NGSPICE, entry, signals, axis=axis,
                               stepped=_is_stepped(entry),
                               step_name=_step_name(entry),
                               params=param_names(entry))
        elif func in _SYSTEM_FUNCS:
            domains = system_domains(entry, section)
            out[name] = Source(name, SYSTEM, entry,
                               [s for d in domains.values() for s in d],
                               domains=domains, axis="time",
                               stepped=_is_stepped(entry),
                               step_name=_step_name(entry))
        elif func in _SLICAP_FUNCS:
            axis = "time" if _SLICAP_FUNCS[func] == "t" else "frequency"
            out[name] = Source(name, SLICAP, entry, list(_SLICAP_SIGNALS[func]),
                               axis=axis, stepped=_is_stepped(entry),
                               step_name=_step_name(entry),
                               gain=gain_type_of(entry))
        else:
            out[name] = Source(name, FILTER, entry, list(FILTER_SIGNALS))
    for variable in section.get("variables", []):
        name = variable.get("name", "")
        if variable.get("kind") != "expression" or not name or name in out:
            continue
        axis = _expression_axis(variable.get("symbols") or [])
        if axis:
            out[name] = Source(name, EXPRESSION, axis=axis)
    return out


# ── the names an expression uses ──────────────────────────────────────────

def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return ".".join([node.id] + parts[::-1])


def names_in(text: str) -> list[str]:
    """The names an expression uses for data, dotted where dotted
    (``AC1.V_out``), in order; called functions are not names of data."""
    try:
        tree = ast.parse(str(text or ""), mode="eval")
    except SyntaxError:
        return []
    out = []

    class _Visitor(ast.NodeVisitor):
        def visit_Attribute(self, node):
            name = _dotted(node)
            if name is not None:
                out.append(name)
            else:
                self.generic_visit(node)

        def visit_Name(self, node):
            out.append(node.id)

        def visit_Call(self, node):
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                self.visit(node.func)
            for arg in node.args:
                self.visit(arg)
            for keyword in node.keywords:
                self.visit(keyword.value)

    _Visitor().visit(tree)
    return out


def used_sources(texts, sources: dict, extra_names=()) -> list[str]:
    """The sources the *texts* (and the *extra_names*, such as the Python
    names of the assignment table) use, in file order."""
    heads = set()
    for name in [n for text in texts for n in names_in(text)] + list(extra_names):
        head, _, tail = str(name).partition(".")
        source = sources.get(head)
        if source is None:
            continue
        if source.kind == EXPRESSION or tail:
            heads.add(head)
    return [name for name in sources if name in heads]


def used_signals(texts, source: str) -> list[str]:
    """The attributes of *source* the *texts* use: ``R1.Ix`` -> ``Ix``."""
    out = []
    for name in [n for text in texts for n in names_in(text)]:
        head, _, tail = str(name).partition(".")
        if head == source and tail and tail not in out:
            out.append(tail)
    return out


@dataclass
class Statement:
    """What one statement (a trace set or a measurement) reads: its sources,
    its axis, what the range row must give, and why it cannot be built
    (*reason*, "" when it can)."""
    used: list
    axis: str = ""
    range: str = ""          # "full", "limits" (start, stop) or ""
    domains: dict = field(default_factory=dict)    # system source -> domain
    reason: str = ""


def statement(texts, sources: dict, extra_names=(), x_axis: str = "time") -> Statement:
    """Read the *texts* of one statement: which sources, which axis, and
    whether they combine (TRACES.md phase 9, 9.1 item 5). The points of two
    data sources are only known after a run; makeDataset() checks them."""
    used = used_sources(texts, sources, extra_names)
    out = Statement(used)
    axes = {}
    for name in used:
        source = sources[name]
        if source.kind == FILTER:
            kinds = {FILTER_SIGNALS.get(s) for s in used_signals(texts, name)}
            kinds.discard(None)
            if len(kinds) > 1:
                out.reason = ("{0}: its frequency functions and its time responses "
                              "cannot be combined".format(name))
                return out
            if kinds:
                axes[name] = kinds.pop()
        elif source.kind == SYSTEM:
            signals = used_signals(texts, name)
            domains = {d for d, members in source.domains.items()
                       for s in signals if s in members}
            if len(domains) > 1:
                out.reason = ("{0}: the signals {1} lie in different clock domains"
                              .format(name, ", ".join(signals)))
                return out
            if domains:
                out.domains[name] = domains.pop()
            elif source.domains:
                out.domains[name] = next(iter(source.domains))
            axes[name] = "time" if x_axis == "time" else x_axis
        elif source.axis:
            axes[name] = source.axis
    if len(set(axes.values())) > 1:
        out.reason = "the sources lie on different axes: " + ", ".join(
            "{0} {1}".format(n, a) for n, a in axes.items())
        return out
    out.axis = next(iter(axes.values()), "")
    has_data = any(sources[n].kind in DATA_KINDS for n in used)
    filters_in_time = any(sources[n].kind == FILTER and axes.get(n) == "time"
                          for n in used)
    if out.axis and out.axis not in ("frequency", "time") and any(
            sources[n].kind not in DATA_KINDS for n in used):
        out.reason = ("functions need a frequency or a time axis, not {0}"
                      .format(out.axis))
        return out
    if filters_in_time:
        out.range = "limits"
    elif not has_data and used:
        out.range = "full"
    return out


def dataset_call(st: Statement, sources: dict, x_axis="time", start="",
                 stop="", num="", method="", params="") -> str:
    """``sl.makeDataset({...}, ...)`` for the statement *st*: the sources
    by name, a system run as the dataset of its clock domain, and the range
    when no data fixes the points."""
    entries = []
    for name in st.used:
        source = sources[name]
        if source.kind == SYSTEM:
            entries.append("{0}: {1}.dataset({2}{3})".format(
                quoted(name), name, quoted(st.domains.get(name, "")),
                "" if x_axis == "time" else ", x=" + quoted(x_axis)))
        else:
            entries.append("{0}: {1}".format(quoted(name), name))
    parts = ["{" + ", ".join(entries) + "}"]
    if st.range == "full":
        parts.append("x=" + quoted(st.axis))
    elif st.range == "limits" and not any(
            sources[n].kind in DATA_KINDS for n in st.used):
        parts.append('x="time"')
    if st.range:
        parts += ["start=" + quoted(start), "stop=" + quoted(stop)]
    if st.range == "full":
        parts.append("num=" + str(num))
        default = "log" if st.axis == "frequency" else "lin"
        if method and method != default:
            parts.append("method=" + quoted(method))
    if params:
        parts.append("params=" + params)
    return "sl.makeDataset(" + ", ".join(parts) + ")"


# ── reading a statement written before phase 9 ────────────────────────────

# what the sweep of one SLiCAP result called its signals (SWEEP_SIGNAL_NAMES
# and before), and what a filter's sweep called them
_OLD_SLICAP = {"H_s": "laplace", "N_s": "numer", "D_s": "denom",
               "laplace": "laplace", "numer": "numer", "denom": "denom",
               "time": "time", "impulse": "impulse", "stepResp": "stepResp",
               "onoise": "onoise", "inoise": "inoise"}
_OLD_FILTER = {"H_z": "H_fz", "H_s": "H_fs", "impulse": "impulse",
               "step": "stepResp"}


def rename(text: str, mapping: dict, prefixes=None) -> str:
    """*text* with every NAME token of *mapping* replaced, except an
    attribute (after a dot) and a called function (before a parenthesis).
    *prefixes* ``{"onoise_": "NOISE1"}`` puts ``NOISE1.`` before every name
    that starts with a key. Token-based, so the rest of the text keeps its
    spelling."""
    text = str(text or "")
    prefixes = dict(prefixes or {})
    if not mapping and not prefixes:
        return text
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError):
        return text
    lines = text.split("\n")
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line) + 1)
    edits = []
    significant = [t for t in tokens if t.type not in (
        tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER, tokenize.COMMENT)]
    for i, tok in enumerate(significant):
        if tok.type != tokenize.NAME:
            continue
        new = mapping.get(tok.string)
        if new is None:
            head = next((h for h in prefixes if tok.string.startswith(h)), None)
            if head is None:
                continue
            new = "{0}.{1}".format(prefixes[head], tok.string)
        before = significant[i - 1].string if i else ""
        after = significant[i + 1].string if i + 1 < len(significant) else ""
        if before == "." or after == "(":
            continue
        start = offsets[tok.start[0] - 1] + tok.start[1]
        end = offsets[tok.end[0] - 1] + tok.end[1]
        edits.append((start, end, new))
    for start, end, new in reversed(edits):
        text = text[:start] + new + text[end:]
    return text


@dataclass
class Data:
    """The data argument of an existing statement, read back: the
    *mapping* that turns its names into dotted ones, its *variables* in
    the new form, and the range and x axis it gave."""
    mapping: dict = field(default_factory=dict)
    prefixes: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)
    start: str = ""
    stop: str = ""
    num: str = ""
    method: str = ""
    x_axis: str = "time"
    params: str = ""

    def rename(self, text: str) -> str:
        """*text* with its names in the dotted form."""
        return rename(text, self.mapping, self.prefixes)


def read_data(text: str, sources: dict, variables=None) -> Data:
    """Read the data argument *text* of an existing make_traces or measure
    statement. The new form, ``sl.makeDataset({...}, ...)``, gives its range
    and system x axis. An old form of ONE result - ``AC1``,
    ``sl.sweepData(LAPLACE1, ...)``, ``sl.sweepData(FLT1, ...)``,
    ``R1.dataset("ref", x="tick")`` - is rewritten in the new form (Anton,
    2026-11-25): *mapping* gives every name its dotted form, and
    *variables* ``{"V_out": "v(out)"}`` become ``{"AC1.V_out": "AC1.v(out)"}``."""
    out = Data()
    variables = dict(variables or {})
    text = str(text or "").strip()
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return out

    def segment(n):
        return ast.get_source_segment(text, n) or ""

    def kw(call, key):
        return next((segment(k.value) for k in call.keywords if k.arg == key), None)

    def sweep_args(call, offset):
        pos = [segment(a) for a in call.args]

        def arg(i, key):
            value = kw(call, key)
            if value is None and len(pos) > i:
                value = pos[i]
            literal = _lit(value) if value is not None else None
            return "" if literal is None else str(literal)
        return arg

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        attr = node.func.attr
        if attr == "makeDataset":
            for key in ("start", "stop", "num", "method"):
                value = _lit(kw(node, key))
                setattr(out, key, "" if value is None else str(value))
            out.params = kw(node, "params") or ""
            first = node.args[0] if node.args else None
            if isinstance(first, ast.Dict):
                for value in first.values:
                    if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                            and value.func.attr == "dataset"):
                        x = _lit(kw(value, "x"))
                        if x:
                            out.x_axis = str(x)
            out.variables = {str(k): str(v) for k, v in variables.items()}
            return out
        if attr == "sweepData" and node.args:
            result = segment(node.args[0])
            arg = sweep_args(node, 0)
            out.start, out.stop, out.num = arg(1, "sweepStart"), arg(2, "sweepStop"), arg(3, "sweepNum")
            method = arg(4, "sweepMethod")
            out.method = method if method in ("lin", "log") else ""
            out.params = kw(node, "params") or ""
            source = sources.get(result)
            old = _OLD_FILTER if source is not None and source.kind == FILTER else _OLD_SLICAP
            out.mapping = {k: "{0}.{1}".format(result, v) for k, v in old.items()}
            if source is not None and source.kind == SLICAP:
                # the noise terms per source, onoise_<source>
                out.prefixes = {"onoise_": result, "inoise_": result}
            return out
        if attr == "dataset" and isinstance(node.func.value, ast.Name):
            result = node.func.value.id
            x = _lit(kw(node, "x"))
            out.x_axis = str(x) if x else "time"
            source = sources.get(result)
            names = source.signals if source is not None else []
            out.mapping = {s: "{0}.{1}".format(result, s) for s in names
                           if str(s).isidentifier()}
            return out
    if isinstance(node, ast.Name):
        result = node.id
        source = sources.get(result)
        names = [s for s in (source.signals if source else []) if str(s).isidentifier()]
        names += list(variables) + list(source.params if source else [])
        out.mapping = {n: "{0}.{1}".format(result, n) for n in names}
        out.variables = {"{0}.{1}".format(result, k): "{0}.{1}".format(result, v)
                         for k, v in variables.items()}
    return out
