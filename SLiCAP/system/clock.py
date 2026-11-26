"""Clock tree of the system-level simulator.

SystemExtensionSpecs.md section 3. The root is the reference clock with
frequency ``f_ref``. A node multiplies or divides its parent's frequency
by integer factors ``m`` and ``d``. Any node can serve as a clock
domain. A domain has a phase, an offset in master ticks, default 0.

The master tick is the smallest clock that is an integer multiple of
every domain clock. For domain ratios ``n_k / d_k`` to ``f_ref`` (reduced
fractions) that is ``lcm(n_k) / gcd(d_k)`` times ``f_ref``. Each domain
then has an integer period in master ticks. The user never enters
periods.

A domain can be a PACING domain (Specs 10.3.6): the update clock of a
programmable filter. It counts for the master tick like any domain,
but not for the hyperperiod: a slow update clock would make the tick
program as long as its period. The engine ends its blocks at the
ticks of a pacing domain instead and runs the functions of that domain
in Python between two blocks. Its period must therefore be a multiple
of the hyperperiod of the signal domains.
"""

from fractions import Fraction
from math import gcd, lcm


class ClockTree:
    """Reference clock, divider and multiplier nodes, domains.

    :param f_ref: reference frequency [Hz]

    Usage::

        clk = ClockTree(1e9)
        clk.node("slow", parent="ref", d=5)       # 200 MHz
        clk.domain("ref")                         # the reference as a domain
        clk.domain("slow", phase=0)
    """

    ROOT = "ref"

    def __init__(self, f_ref=None):
        # None: a driven reference clock (Specs 15.1), whose frequency the
        # system takes from its signal before the run (System.drive_clock)
        self.f_ref = None if f_ref is None else float(f_ref)
        self._ratio = {self.ROOT: Fraction(1)}
        self._parent = {self.ROOT: None}
        self._phase = {}
        self._pacing = set()

    # ---- building -------------------------------------------------------

    def node(self, name, parent=ROOT, m=1, d=1):
        """Add a node: frequency of *parent* times *m* over *d*."""
        if name in self._ratio:
            raise ValueError("clock node %r exists" % name)
        if parent not in self._ratio:
            raise ValueError("clock node %r: unknown parent %r"
                             % (name, parent))
        m, d = int(m), int(d)
        if m < 1 or d < 1:
            raise ValueError("clock node %r: factors must be positive integers"
                             % name)
        self._ratio[name] = self._ratio[parent] * Fraction(m, d)
        self._parent[name] = parent
        return self

    def domain(self, name, phase=0, pacing=False):
        """Declare node *name* a clock domain with *phase* master ticks.
        With *pacing* True it is an update clock: it paces the blocks of
        the run loop and stays out of the hyperperiod (Specs 10.3.6)."""
        if name not in self._ratio:
            raise ValueError("unknown clock node %r" % name)
        self._phase[name] = int(phase)
        if pacing:
            self._pacing.add(name)
        else:
            self._pacing.discard(name)
        return self

    # ---- queries --------------------------------------------------------

    def _f_ref(self):
        if self.f_ref is None:
            raise ValueError("the frequency of the reference clock is not known "
                             "yet: a driven clock takes it from its signal "
                             "(System.drive_clock)")
        return self.f_ref

    def frequency(self, name):
        """Frequency of node *name* [Hz]."""
        return self._f_ref() * float(self._ratio[name])

    @property
    def domains(self):
        """All domains, signal and pacing, in declaration order."""
        return list(self._phase)

    @property
    def signal_domains(self):
        """The domains of the schedule: all but the pacing ones."""
        return [n for n in self._phase if n not in self._pacing]

    @property
    def pacing_domains(self):
        return [n for n in self._phase if n in self._pacing]

    def is_pacing(self, name):
        return name in self._pacing

    @property
    def master_ratio(self):
        """Master tick frequency over ``f_ref``, a ``Fraction``."""
        if not self._phase:
            raise ValueError("clock tree has no domain")
        nums = [self._ratio[n].numerator for n in self._phase]
        dens = [self._ratio[n].denominator for n in self._phase]
        return Fraction(lcm(*nums), gcd(*dens))

    @property
    def master_frequency(self):
        """Master tick frequency [Hz]."""
        return self._f_ref() * float(self.master_ratio)

    @property
    def master_tick(self):
        """Master tick step [s]."""
        return 1.0 / self.master_frequency

    def period(self, name):
        """Period of domain *name* in master ticks, an integer."""
        p = self.master_ratio / self._ratio[name]
        assert p.denominator == 1
        return p.numerator

    def phase(self, name):
        return self._phase[name]

    def periods(self):
        """``{domain: period in master ticks}``."""
        return {n: self.period(n) for n in self._phase}

    @property
    def hyperperiod(self):
        """Least common multiple of the periods of the signal domains, in
        master ticks. The pacing domains stay out of it (Specs 10.3.6)."""
        signal = self.signal_domains
        if not signal:
            raise ValueError("every domain is an update clock: a system "
                             "needs a signal domain")
        return lcm(*(self.period(n) for n in signal))

    def check_pacing(self):
        """Raise ``ValueError`` when the period of a pacing domain is not
        a multiple of the hyperperiod of the signal domains: a faster
        update clock would be a time-varying filter, another block
        (Specs 10.3.6)."""
        hp = self.hyperperiod
        for n in self.pacing_domains:
            if self.period(n) % hp:
                raise ValueError(
                    "update clock %s: its period of %d master ticks is not "
                    "a multiple of the hyperperiod of %d master ticks of "
                    "the signal domains" % (n, self.period(n), hp))

    def next_pacing_of(self, name, tick):
        """The first master tick at or after *tick* where domain *name*
        fires."""
        p, per = self._phase[name], self.period(name)
        return p + (-(-(tick - p) // per)) * per if tick > p else p

    def next_pacing(self, tick):
        """The first master tick at or after *tick* where a pacing domain
        fires, or None without pacing domains."""
        ticks = [self.next_pacing_of(n, tick) for n in self.pacing_domains]
        return min(ticks) if ticks else None

    def fires(self, name, tick):
        """True when domain *name* fires at master *tick*."""
        return (tick - self._phase[name]) % self.period(name) == 0

    def firing(self, tick):
        """The domains that fire at master *tick*, in declaration order."""
        return [n for n in self._phase if self.fires(n, tick)]

    def table(self):
        """Rows ``(node, parent, frequency, period or None, phase or None)``
        for display: the GUI shows the frequency per node and the master
        tick (Specs 3.2, 3.3)."""
        rows = []
        for name in self._ratio:
            per = self.period(name) if name in self._phase else None
            ph = self._phase.get(name)
            rows.append((name, self._parent[name], self.frequency(name),
                         per, ph))
        return rows
