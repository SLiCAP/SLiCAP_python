"""Schedule of one hyperperiod (SystemExtensionSpecs.md section 4).

Built by the engine at the start of the run, before the first tick.

Firing
    A clocked function fires at the ticks of its domain. An algebraic
    function fires at every tick where a function feeding it fires.

Order
    Within a tick the ``output()`` calls run in dependency order. A
    wire from P to C constrains the order (P before C) when C has at
    least one direct output: C's ``output()`` then needs its inputs of
    this tick. A wire into a function without direct outputs puts no
    constraint: its ``output()`` reads the state only, and its
    ``update()`` runs after all outputs anyway. The sort runs over all
    functions regardless of domain (a sort per domain was REJECTED,
    Specs 4.2).

Algebraic loop
    A cycle of such constraints is an algebraic loop. It is refused
    with a message that names the blocks (Specs 4.3). The dependency is
    taken per function, not per output: a function whose ``output()``
    computes a direct output from one input and a state output read by
    the same loop is refused, with the advice to split the block. That
    keeps the structure visible in the drawing. Per-output dependency
    declarations were considered and REJECTED (2026-11-16): ``output()``
    computes all outputs in one call, so a function cannot be placed
    both before and after another one.

Pacing functions
    A function of a pacing domain (an update clock, Specs 10.3.6) is
    not in the schedule: the engine runs it in Python between two
    blocks, at the ticks of its domain. ``order`` holds the functions
    of the tick program, ``pacing`` the others, both in dependency
    order. A wire from a pacing function into the program is refused
    by the ``System``. A wire into a pacing function always orders the
    producer before it: between blocks the function fires by
    ``output()`` with the inputs of that moment (found 2026-11-17: an
    updater fed by a source of the same update clock read the source's
    initial value).
"""

from graphlib import TopologicalSorter, CycleError


class AlgebraicLoop(ValueError):
    """A loop of direct dependencies without a state output."""


class Schedule:
    """Firing functions per tick of one hyperperiod, in dependency order.

    :param system: the ``System``
    """

    def __init__(self, system):
        self.system = system
        self.clocks = system.clocks
        self.hyperperiod = self.clocks.hyperperiod
        self.clocks.check_pacing()
        order = self._global_order()
        self.pacing = [fn for fn in order if self.is_pacing(fn)]
        self.order = [fn for fn in order if not self.is_pacing(fn)]
        self.ticks = [self._tick(t) for t in range(self.hyperperiod)]

    def is_pacing(self, fn):
        """True for a function of a pacing domain, and for an update
        function without a domain, which fires once, before the first
        block (Specs 10.3.4)."""
        return fn.kind == "clocked" and (
            (fn.domain is None and getattr(fn, "pacing", False))
            or (fn.domain is not None and self.clocks.is_pacing(fn.domain)))

    # ---- dependency order -------------------------------------------------

    def _constraints(self):
        """``{function: set of functions that must run before it}``."""
        before = {fn: set() for fn in self.system.functions}
        for w in self.system.wires:
            # a pacing function reads its inputs in output(): between two
            # blocks there is no later update() pass to read them in
            if w.dst.direct or self.is_pacing(w.dst):
                before[w.dst].add(w.src)
        return before

    def _global_order(self):
        """All functions in dependency order; raises ``AlgebraicLoop``."""
        before = self._constraints()
        ts = TopologicalSorter(before)
        try:
            order = list(ts.static_order())
        except CycleError as e:
            cycle = e.args[1]
            names = [fn.name for fn in cycle[:-1]]
            raise AlgebraicLoop(
                "algebraic loop through %s: every function in the loop "
                "reads its inputs in the same tick. Give one of them a "
                "state output, or split a block so that the feedthrough "
                "path and the state path are separate blocks."
                % " -> ".join(names)) from None
        # static_order() is deterministic for a given insertion order;
        # keep the system's order of adding among independent functions.
        pos = {fn: i for i, fn in enumerate(self.system.functions)}
        return self._stable(order, before, pos)

    @staticmethod
    def _stable(order, before, pos):
        """Topological order that prefers the order of adding."""
        done, result = set(), []
        pending = sorted(order, key=pos.get)
        while pending:
            for fn in pending:
                if before[fn] <= done:
                    result.append(fn)
                    done.add(fn)
                    pending.remove(fn)
                    break
            else:  # pragma: no cover - cycle was caught above
                raise AlgebraicLoop("unexpected cycle")
        return result

    # ---- firing sets --------------------------------------------------------

    def _tick(self, t):
        """``(outputs, updates)`` for master tick *t*.

        *outputs*: functions whose ``output()`` runs, in order.
        *updates*: clocked functions whose ``update()`` runs.
        """
        firing = set()
        for fn in self.order:
            if fn.kind == "clocked" and self.clocks.fires(fn.domain, t):
                firing.add(fn)
        # algebraic functions fire when a source fires; propagate in
        # dependency order, so a chain of algebraic functions is covered
        for fn in self.order:
            if fn.kind == "algebraic" and fn not in firing:
                if any(src in firing for src in self.system.sources_of(fn)):
                    firing.add(fn)
        outputs = [fn for fn in self.order if fn in firing]
        updates = [fn for fn in outputs if fn.kind == "clocked"]
        return outputs, updates

    def at(self, tick):
        """``(outputs, updates)`` for any master *tick*."""
        return self.ticks[tick % self.hyperperiod]

    def firings(self, fn, ticks):
        """Number of times *fn* fires in *ticks* master ticks."""
        if self.is_pacing(fn):
            if fn.domain is None:
                return 0                              # once, before the first block
            p, per = self.clocks.phase(fn.domain), self.clocks.period(fn.domain)
            return max(0, (ticks - 1 - p) // per + 1) if ticks > p else 0
        per_hp = sum(1 for outs, _ in self.ticks if fn in outs)
        full, rest = divmod(ticks, self.hyperperiod)
        extra = sum(1 for outs, _ in self.ticks[:rest] if fn in outs)
        return full * per_hp + extra

    def ticks_until(self, fn, firings, start=0):
        """Number of master ticks from *start* up to and including the
        tick of the *firings*-th firing of *fn*. None when *fn* never
        fires; 0 when *firings* is 0."""
        if self.is_pacing(fn):
            if fn.domain is None:
                return None                           # never fires in the run
            if firings <= 0:
                return 0
            p, per = self.clocks.phase(fn.domain), self.clocks.period(fn.domain)
            first = self.clocks.next_pacing_of(fn.domain, start)
            return first + (firings - 1) * per - start + 1
        hp = self.hyperperiod
        fires = sorted((t - start) % hp
                       for t, (outs, _) in enumerate(self.ticks)
                       if fn in outs)
        if not fires:
            return None
        if firings <= 0:
            return 0
        full, r = divmod(firings - 1, len(fires))
        return full * hp + fires[r] + 1

    def describe(self):
        """Readable listing, one line per tick of the hyperperiod."""
        lines = ["hyperperiod %d master ticks" % self.hyperperiod]
        for t, (outs, _) in enumerate(self.ticks):
            lines.append("tick %d: %s" % (t, ", ".join(fn.name for fn in outs)
                                           or "-"))
        for fn in self.pacing:
            if fn.domain is None:
                lines.append("before the first block only: %s" % fn.name)
                continue
            lines.append("between blocks, every %d ticks from tick %d: %s"
                         % (self.clocks.period(fn.domain),
                            self.clocks.phase(fn.domain), fn.name))
        return "\n".join(lines)
