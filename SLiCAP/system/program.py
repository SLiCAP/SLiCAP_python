"""Generator of the tick program (SystemExtensionSpecs.md 4.7,
SystemExtensionDesign.md 9.1).

From a ``System`` and its ``Schedule`` the generator writes the source
of a self-contained Python module: the kernels of the functions, copied
from their modules, and one function ``block(n, t0, ...)`` that runs
*n* master ticks with the hyperperiod written out as straight-line
code. Every signal is a local variable, every state vector an array
argument, every parameter an argument. There is no lookup of a wire or
a function during the run.

The program runs in plain Python as it is. When every function has
kernels and numba is installed, the same source is compiled with
``numba.njit`` before the first tick. A function without kernels is
driven by its methods inside the program, which is Python but not
compilable; the program then reports it.
"""

import inspect
import keyword
import re
import textwrap
import types

import numpy as np

_IDENT = re.compile(r"[^0-9a-zA-Z_]")


def _ident(name):
    """A valid identifier made from a function name."""
    s = _IDENT.sub("_", str(name))
    if not s or s[0].isdigit() or keyword.iskeyword(s):
        s = "_" + s
    return s


def _literal(value):
    """Python source of a plain parameter value."""
    if isinstance(value, (bool, np.bool_)):
        return "True" if value else "False"
    if isinstance(value, (int, np.integer)):
        return repr(int(value))
    if isinstance(value, (float, np.floating)):
        return repr(float(value))
    raise TypeError("not a literal: %r" % (value,))


class KernelSource:
    """Collects the source of the kernels and of the module-level
    functions and constants they use, so that the program is one
    self-contained module."""

    def __init__(self):
        self.lines = []          # source blocks in dependency order
        self.imports = set()
        self.constants = {}      # name -> literal source
        self._done = set()

    def add(self, fn):
        """Add function *fn* and what it references; returns its name
        in the program."""
        key = (fn.__module__, fn.__qualname__)
        if key in self._done:
            return fn.__name__
        self._done.add(key)
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            raise ValueError(
                "kernel %s.%s: source not available (a kernel must be a "
                "function in a module file)" % key) from None
        src = textwrap.dedent(src)
        # drop decorators: the program decides about compilation
        body = src.lstrip()
        while body.startswith("@"):
            body = body.split("\n", 1)[1]
        g = fn.__globals__
        for name in fn.__code__.co_names:
            if name not in g:
                continue              # a builtin or an attribute name
            value = g[name]
            if isinstance(value, types.FunctionType):
                if getattr(value, "python_only", False):
                    # a Python function the kernel reaches through object
                    # mode (scipy inside): imported, never compiled
                    self.imports.add("from %s import %s"
                                     % (value.__module__, name))
                elif value.__module__ == fn.__module__:
                    self.add(value)
                else:
                    self.imports.add("from %s import %s"
                                     % (value.__module__, name))
            elif isinstance(value, types.ModuleType):
                self.imports.add("import %s as %s" % (value.__name__, name))
            elif isinstance(value, (bool, int, float, np.integer,
                                    np.floating)):
                self.constants[name] = _literal(value)
            elif isinstance(value, types.BuiltinFunctionType):
                mod = getattr(value, "__module__", None) or "builtins"
                if mod != "builtins":
                    self.imports.add("from %s import %s" % (mod, name))
            elif isinstance(value, type):
                if value.__module__ != "builtins":
                    self.imports.add("from %s import %s"
                                     % (value.__module__, name))
            else:
                # any other object the kernel names (numba's objmode context,
                # 2026-11-20): the kernel's own module holds it
                self.imports.add("from %s import %s" % (fn.__module__, name))
        self.lines.append(body.rstrip() + "\n")
        return fn.__name__

    def text(self):
        out = sorted(self.imports)
        out += ["%s = %s" % kv for kv in sorted(self.constants.items())]
        out.append("")
        out += self.lines
        return "\n".join(out)


class Program:
    """The tick program of a system.

    :param system: the ``System``
    :param schedule: its ``Schedule``

    Attributes after construction: ``source`` (the module text),
    ``methods`` (names of the functions without kernels, empty when the
    program is compilable), ``signals`` (``[(fn, out), ...]`` in
    ``held`` order), ``stored`` (``[(fn, out), ...]`` in buffer order).
    """

    def __init__(self, system, schedule):
        self.system = system
        self.schedule = schedule
        self.functions = list(schedule.order)
        self.fname = {fn: "f%d_%s" % (i, _ident(fn.name))
                      for i, fn in enumerate(self.functions)}
        self.methods = [fn.name for fn in self.functions
                        if getattr(fn, "kernels", None) is None]
        self.signals = [(fn, out) for fn in self.functions
                        for out in fn.outputs]
        self.sig_index = {so: i for i, so in enumerate(self.signals)}
        # the stored signals of the program; those of the pacing
        # functions are recorded by the engine between blocks
        self.stored = [so for so in system.stored if so[0] in self.functions]
        self.stored_index = {so: j for j, so in enumerate(self.stored)}
        self.wire_in = {}        # (dst, inp) -> (src, out)
        for w in system.wires:
            self.wire_in[(w.dst, w.inp)] = (w.src, w.out)
        # the signal that gives the actual frequency of the reference
        # clock (System.drive_clock): its variable in the program
        self.clock_var = None
        if system.clock_source is not None:
            fn, out = system.clock_source
            if fn not in self.functions:
                raise ValueError("%s drives the reference clock but is not "
                                 "in the tick program" % fn.name)
            self.clock_var = self._var(fn, out)
        self.kernel_names = {}   # fn -> (k_out name, k_upd name | None)
        self.retime_names = {}   # fn -> name of its retime kernel (Specs 15.3)
        self.ksrc = KernelSource()
        for fn in self.functions:
            ks = getattr(fn, "kernels", None)
            if ks is None:
                continue
            names = [self.ksrc.add(k) for k in ks]
            self.kernel_names[fn] = (names[0], names[1] if len(names) > 1
                                     else None)
            rt = getattr(fn, "retime", None)
            if rt is not None:
                self.retime_names[fn] = self.ksrc.add(rt)
        self.patterns, self.pattern_of_tick = self._patterns()
        self.args = self._arguments()
        self.source = self._generate()

    # ---- analysis -----------------------------------------------------------

    def _patterns(self):
        """Distinct (outputs, updates) firing patterns of the hyperperiod
        and the pattern index of every tick."""
        patterns, index = [], []
        for outs, ups in self.schedule.ticks:
            key = (tuple(outs), tuple(ups))
            if key not in patterns:
                patterns.append(key)
            index.append(patterns.index(key))
        return patterns, np.array(index, dtype=np.int64)

    def _arguments(self):
        """Argument names of block() after the fixed ones, with the
        objects to pass: ``[(name, value), ...]``."""
        args = []
        for fn in self.functions:
            f = self.fname[fn]
            if fn in self.kernel_names:
                if fn.kind == "clocked":
                    args.append(("s_" + f, fn.state))
                for i, p in enumerate(getattr(fn, "params", ())):
                    args.append(("p%d_%s" % (i, f), p))
            else:
                args.append(("o_" + f, fn))
        for j, (fn, out) in enumerate(self.stored):
            args.append(("r%d_%s_%s" % (j, self.fname[fn], out), None))
        return args

    # ---- generation ---------------------------------------------------------

    def _var(self, fn, out):
        return "v_%s_%s" % (self.fname[fn], out)

    def _input_expr(self, fn, inp):
        """Source of the value of input *inp* of *fn*: the signal that
        drives it, or its present value when nothing does."""
        src = self.wire_in.get((fn, inp))
        if src is not None:
            return self._var(*src)
        return _literal(getattr(fn, inp))

    def _wrap(self, fn, out, var):
        dt = fn.dtype(out)
        if dt.kind not in "iu":
            return []
        info = np.iinfo(dt)
        lo, span = int(info.min), int(info.max) - int(info.min) + 1
        return ["%s = (int(%s) - %d) %% %d + %d" % (var, var, lo, span, lo)]

    def _fire(self, fn):
        """Lines of the output call of *fn* and its wrapping."""
        f = self.fname[fn]
        outs = [self._var(fn, o) for o in fn.outputs]
        ins = [self._input_expr(fn, i) for i in fn.inputs]
        lines = []
        if fn in self.kernel_names:
            k_out, _ = self.kernel_names[fn]
            call = (["tm"] if fn.uses_time else []) + list(ins)
            if fn.kind == "clocked":
                call.append("s_" + f)
            call += ["p%d_%s" % (i, f)
                     for i in range(len(getattr(fn, "params", ())))]
            lhs = ", ".join(outs) if outs else "_"
            lines.append("%s = %s(%s)" % (lhs, k_out, ", ".join(call)))
        else:
            o = "o_" + f
            if fn.uses_time:
                lines.append("%s.time = tm" % o)
            for inp, expr in zip(fn.inputs, ins):
                lines.append("%s.%s = %s" % (o, inp, expr))
            lines.append("%s.output()" % o)
            for out, var in zip(fn.outputs, outs):
                lines.append("%s = %s.%s" % (var, o, out))
        for out, var in zip(fn.outputs, outs):
            lines += self._wrap(fn, out, var)
        return lines

    def _update(self, fn):
        f = self.fname[fn]
        if fn in self.kernel_names:
            _, k_upd = self.kernel_names[fn]
            if k_upd is None:
                return []
            call = (["tm"] if fn.uses_time else [])
            call += [self._input_expr(fn, i) for i in fn.inputs]
            call += [self._var(fn, o) for o in fn.outputs]
            call.append("s_" + f)
            call += ["p%d_%s" % (i, f)
                     for i in range(len(getattr(fn, "params", ())))]
            return ["%s(%s)" % (k_upd, ", ".join(call))]
        # a method reads its inputs as attributes: give it the values of
        # this tick, which may have been computed after its output()
        o = "o_" + f
        lines = ["%s.%s = %s" % (o, inp, self._input_expr(fn, inp))
                 for inp in fn.inputs]
        return lines + ["%s.update()" % o]

    def _store(self, fn, out):
        j = self.stored_index[(fn, out)]
        buf = "r%d_%s_%s" % (j, self.fname[fn], out)
        return ["%s[cnt[%d]] = %s" % (buf, j, self._var(fn, out)),
                "cnt[%d] += 1" % j]

    def _generate(self):
        hp = self.schedule.hyperperiod
        L = []
        L.append('"""Tick program, generated by SLiCAP.system.program; '
                 'do not edit."""')
        L.append(self.ksrc.text())
        L.append("")
        L.append("HP = %d" % hp)
        L.append("")
        fixed = ["n", "t0", "prog", "clk", "held", "cnt", "pat", "tbuf"]
        names = fixed + [name for name, _ in self.args]
        L.append("def block(%s):" % ", ".join(names))
        L.append("    # signals held between blocks")
        for i, (fn, out) in enumerate(self.signals):
            var = self._var(fn, out)
            if fn.dtype(out).kind in "iu":
                L.append("    %s = int(held[%d])" % (var, i))
            else:
                L.append("    %s = held[%d]" % (var, i))
        # physical time (Specs 15.2): tm at the start of the tick, dt the
        # duration of the last tick, Ts the nominal master tick, t_end
        # where the run stops by time (inf for a run by ticks)
        L.append("    tm = clk[0]")
        L.append("    dt = clk[1]")
        L.append("    Ts = clk[2]")
        L.append("    t_end = clk[3]")
        L.append("    t = t0")
        L.append("    end = t0 + n")
        L.append("    while t < end:")
        L.append("        tbuf[t - t0] = tm")
        L.append("        k = pat[t % HP]")
        # the duration of this tick: 1/f from the clock's source, the value
        # computed in this tick (Specs 15.1), known once every block has
        # fired and before the states move on, so that a non-stationary
        # filter steps over the duration of THIS tick (Specs 15.3: the
        # retime, one branch per tick for all of them)
        clock = []
        if self.clock_var is not None:
            clock.append("f = %s" % self.clock_var)
            clock.append("if f <= 0.0:")
            clock.append("    raise ValueError('the frequency of the "
                         "reference clock is not positive')")
            clock.append("dt_new = 1.0 / f")
            if self.retime_names:
                clock.append("if dt_new != dt:")
                for fn, k_rt in self.retime_names.items():
                    f = self.fname[fn]
                    args = ["dt_new"] + ["p%d_%s" % (i, f)
                                         for i in range(len(fn.params))]
                    clock.append("    %s(%s)" % (k_rt, ", ".join(args)))
            clock.append("dt = dt_new")
        for p, (outs, ups) in enumerate(self.patterns):
            L.append("        %s k == %d:" % ("if" if p == 0 else "elif", p))
            body = []
            for fn in outs:
                body += self._fire(fn)
                for out in fn.outputs:
                    if (fn, out) in self.stored_index:
                        body += self._store(fn, out)
            body += clock
            for fn in ups:
                body += self._update(fn)
            if not body:
                body = ["pass"]
            L += ["            " + line for line in body]
        # the time of the next tick: accumulated with a driven clock, kept
        # exact as t * Ts with the nominal one
        if self.clock_var is not None:
            L.append("        tm += dt")
        else:
            L.append("        dt = Ts")
            L.append("        tm = (t + 1) * Ts")
        L.append("        t += 1")
        L.append("        prog[0] = t")
        # by time: the run ends when the next tick would start at or beyond
        # t_end, to half a tick, as the nominal run rounds its tick count
        L.append("        if tm + 0.5 * dt >= t_end:")
        L.append("            break")
        L.append("    clk[0] = tm")
        L.append("    clk[1] = dt")
        for i, (fn, out) in enumerate(self.signals):
            L.append("    held[%d] = %s" % (i, self._var(fn, out)))
        L.append("    return t")
        L.append("")
        return "\n".join(L)

    # ---- building -----------------------------------------------------------

    def build(self, jit):
        """Execute the source and return ``block``; with *jit* True the
        kernels and ``block`` are compiled with numba first."""
        ns = {}
        exec(compile(self.source, "<tick program>", "exec"), ns)
        if jit:
            import numba
            for name in self._function_names():
                ns[name] = numba.njit(cache=False)(ns[name])
            ns["block"] = numba.njit(cache=False)(ns["block"])
        return ns["block"]

    def _function_names(self):
        """Names of the kernel functions in the program, in order."""
        names = []
        for line in self.ksrc.lines:
            m = re.match(r"def\s+(\w+)\s*\(", line)
            if m:
                names.append(m.group(1))
        return names

    def feed(self, fn, held):
        """Set the inputs of *fn*, a function outside the program, from
        the ``held`` values of the program's signals; an input driven by
        another function outside the program is copied from that
        function's output attribute."""
        for w in self.system.wires_into(fn):
            i = self.sig_index.get((w.src, w.out))
            if i is None:
                value = getattr(w.src, w.out)
            else:
                value = held[i]
                if w.src.dtype(w.out).kind in "iu":
                    value = int(value)
            setattr(fn, w.inp, value)

    def held_values(self):
        """The present output values of all functions, as the ``held``
        array."""
        held = np.zeros(len(self.signals))
        for i, (fn, out) in enumerate(self.signals):
            held[i] = float(getattr(fn, out))
        return held

    def set_outputs(self, held):
        """Copy the ``held`` array back to the output attributes."""
        for i, (fn, out) in enumerate(self.signals):
            v = held[i]
            if fn.dtype(out).kind in "iu":
                v = int(v)
            setattr(fn, out, v)
