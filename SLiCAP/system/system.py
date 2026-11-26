"""The ``System``: functions, wires, clock tree and stored signals.

This is the description the run script builds (SystemExtensionSpecs.md
8.2): instances, their clock domains, the wiring and the stored
signals. It holds no schedule. The engine derives the schedule from it
at the start of the run (Specs 4.2).

Wires carry a data type check (Specs 5.1): an output may feed an input
of another type when the conversion loses no value, numpy's "safe"
casting. The setting ``implicit_casts=False`` refuses every type
change, so that a fixed-point design shows all its casts.
"""

import numpy as np

from .clock import ClockTree
from .function import check_function


class Wire:
    __slots__ = ("src", "out", "dst", "inp")

    def __init__(self, src, out, dst, inp):
        self.src, self.out, self.dst, self.inp = src, out, dst, inp

    def __repr__(self):
        return "%s.%s -> %s.%s" % (self.src.name, self.out,
                                   self.dst.name, self.inp)


class System:
    """A system to run.

    :param clocks: the ``ClockTree``
    :param implicit_casts: allow safe casts on wires (default True)

    Usage::

        sys = System(ClockTree(1e9).domain("ref"))
        nco = sys.add(NCO(...), "NCO", domain="ref")
        xt  = sys.add(Biquad(...), "XT", domain="ref")
        sys.connect(nco, "sin", xt, "x")
        sys.store(xt, "y")
    """

    def __init__(self, clocks, implicit_casts=True):
        if not isinstance(clocks, ClockTree):
            raise TypeError("clocks must be a ClockTree")
        self.clocks = clocks
        self.implicit_casts = bool(implicit_casts)
        self.functions = []           # in order of adding
        self.wires = []
        self.stored = []              # (function, output) pairs
        self._names = {}
        # (function, output) whose value is the actual frequency of the
        # reference clock, or None for the nominal clock (Specs 15.1)
        self.clock_source = None
        self.start_time = 0.0         # physical time at the start of a run

    # ---- building -------------------------------------------------------

    def add(self, fn, name, domain=None):
        """Add a function instance under *name*.

        A clocked function needs its *domain*, a domain of the clock
        tree. An algebraic function has none.
        """
        check_function(fn)
        if name in self._names:
            raise ValueError("function name %r is used twice" % name)
        if fn.kind == "clocked" and domain is None and getattr(fn, "pacing", False):
            # an update function without an update clock: it fires in the
            # pass before the first block only, "once" (Specs 10.3.4; Anton,
            # 2026-11-18: constants on the parameter pins need no clock)
            pass
        elif fn.kind == "clocked":
            if domain is None:
                raise ValueError("%s %r needs a clock domain"
                                 % (type(fn).__name__, name))
            if domain not in self.clocks.domains:
                raise ValueError("%r: unknown clock domain %r"
                                 % (name, domain))
            if getattr(fn, "pacing", False) and not self.clocks.is_pacing(domain):
                raise ValueError(
                    "%r fires with an update clock and must be added to a "
                    "pacing domain, not to %r (Specs 10.3.6)" % (name, domain))
            fn.domain = domain
            # the sample period; None until a driven clock has its frequency
            fn.Ts = (None if self.clocks.f_ref is None
                     else 1.0 / self.clocks.frequency(domain))
            fn.period = self.clocks.period(domain)      # in master ticks
        elif domain is not None:
            raise ValueError("%r is algebraic and has no clock domain" % name)
        fn.name = name
        self._names[name] = fn
        self.functions.append(fn)
        return fn

    def __getitem__(self, name):
        return self._names[name]

    def connect(self, src, out, dst, inp):
        """Wire output *out* of *src* to input *inp* of *dst*.

        *src* and *dst* are instances or names. One wire per input.
        """
        src, dst = self._fn(src), self._fn(dst)
        if out not in src.outputs:
            raise ValueError("%s has no output %r" % (src, out))
        if inp not in dst.inputs:
            raise ValueError("%s has no input %r" % (dst, inp))
        for w in self.wires:
            if w.dst is dst and w.inp == inp:
                raise ValueError("input %s.%s is already driven by %s.%s"
                                 % (dst.name, inp, w.src.name, w.out))
        self._check_types(src, out, dst, inp)
        if self._pacing(src) and not self._pacing(dst):
            raise ValueError(
                "wire %s.%s -> %s.%s: %s fires with the update clock %s "
                "between the blocks of the run and feeds parameters, not "
                "signals; it cannot drive a function of the tick program "
                "(Specs 10.3.6)" % (src.name, out, dst.name, inp, src.name,
                                    src.domain))
        w = Wire(src, out, dst, inp)
        self.wires.append(w)
        return w

    def drive_clock(self, fn, out):
        """Let output *out* of *fn* give the frequency of the reference
        clock in Hz (Specs 15.1): the duration of master tick k is
        1/f(k), f(k) the value computed in tick k. A tree made with
        ``ClockTree(None)``, the driven clock symbol, takes its nominal
        frequency from the value of the signal now, its initial output,
        and the sample periods of the clocked functions follow: call it
        after adding the functions. A tree made with a number keeps that
        number as the nominal. One source; a function of the tick
        program, not a pacing one."""
        fn = self._fn(fn)
        if out not in fn.outputs:
            raise ValueError("%s has no output %r" % (fn, out))
        if self._pacing(fn):
            raise ValueError("%s fires with an update clock between the "
                             "blocks and cannot drive the reference clock"
                             % fn.name)
        if fn.dtype(out).kind not in "fiu":
            raise TypeError("%s.%s (%s) is not a number: it cannot be a "
                            "frequency" % (fn.name, out, fn.dtype(out)))
        self.clock_source = (fn, out)
        if self.clocks.f_ref is None:
            fn.prepare(1)                 # a source that draws its samples
            fn.output()
            value = float(getattr(fn, out))
            if not value > 0.0:
                raise ValueError("%s.%s gives %g at the start: the frequency of "
                                 "the reference clock must be positive"
                                 % (fn.name, out, value))
            self.clocks.f_ref = value
            for f in self.functions:
                if f.kind == "clocked" and f.domain is not None:
                    f.Ts = 1.0 / self.clocks.frequency(f.domain)
        return self

    def store(self, fn, out):
        """Record output *out* of *fn* during the run (Specs 6.3)."""
        fn = self._fn(fn)
        if out not in fn.outputs:
            raise ValueError("%s has no output %r" % (fn, out))
        if (fn, out) not in self.stored:
            self.stored.append((fn, out))

    # ---- helpers --------------------------------------------------------

    def _pacing(self, fn):
        return fn.kind == "clocked" and (
            (fn.domain is None and getattr(fn, "pacing", False))
            or (fn.domain is not None and self.clocks.is_pacing(fn.domain)))

    def _fn(self, ref):
        if isinstance(ref, str):
            try:
                return self._names[ref]
            except KeyError:
                raise ValueError("unknown function %r" % ref) from None
        if ref not in self.functions:
            raise ValueError("%r was not added to the system" % (ref,))
        return ref

    def _check_types(self, src, out, dst, inp):
        t_out, t_in = src.dtype(out), dst.dtype(inp)
        if t_out == t_in:
            return
        if not self.implicit_casts:
            raise TypeError(
                "wire %s.%s (%s) -> %s.%s (%s): implicit casts are off; "
                "insert a cast block"
                % (src.name, out, t_out, dst.name, inp, t_in))
        if not np.can_cast(t_out, t_in, casting="safe"):
            raise TypeError(
                "wire %s.%s (%s) -> %s.%s (%s) may lose values; "
                "insert a cast block"
                % (src.name, out, t_out, dst.name, inp, t_in))

    def wires_from(self, fn):
        return [w for w in self.wires if w.src is fn]

    def wires_into(self, fn):
        return [w for w in self.wires if w.dst is fn]

    def sources_of(self, fn):
        """Functions whose outputs feed *fn*."""
        seen, out = set(), []
        for w in self.wires_into(fn):
            if id(w.src) not in seen:
                seen.add(id(w.src))
                out.append(w.src)
        return out
