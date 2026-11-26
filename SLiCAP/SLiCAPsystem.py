"""SLiCAP system-level simulation: the script API and the built-in
functions.

Local only until released (SystemExtensionSpecs.md section 13). The
engine is ``SLiCAP.system``; this module is what a run script and a
user script import::

    from SLiCAP.SLiCAPsystem import *

    clk = ClockTree(1e9).domain("ref")
    clk.node("slow", d=5).domain("slow")
    sys = System(clk)
    nco = sys.add(NCO(24, 48e6, -2e6, -1e4, 1e4), "NCO", domain="ref")
    ...
    result = run(sys, 2_500_000)

Every built-in function is a class (SystemExtensionDesign.md 12.2).
Two kinds: ``Algebraic`` functions can never have a state and have no
clock; ``Clocked`` functions can have a state and belong to a clock
domain. A clocked function reads its sample time from ``self.Ts``,
set by the ``System`` from the clock domain; no block has the sample
time as a parameter.

A filter section (``Bilin``, ``Biquad``, ``FIR``) stores its z-domain
transfer function in the attribute ``ztransfer``, a rational in
``ini.z`` built from its own coefficients (SystemExtensionDesign.md 5).

Floating-point library. The fixed-point library comes later.
"""

from math import atan2, sqrt, pi, cos, sin, exp
from pathlib import Path

import numpy as np
import sympy as sp

import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.system import (Algebraic, Clocked, ClockTree, System, run,
                           RunResult, EndOfData, load_state, save_state,
                           request_stop, envelope, AlgebraicLoop)

__all__ = ["ClockTree", "System", "run", "RunResult", "EndOfData",
           "load_state", "save_state", "request_stop", "envelope",
           "AlgebraicLoop", "Algebraic", "Clocked",
           "Add2", "Add3", "Add4", "Gain", "Clip",
           "Constant", "Signal", "WAVEFORMS", "Delay",
           "Bilin", "Biquad", "FIR", "CordicIQ", "CordicMag", "NCO",
           "FilterResult", "Realisation", "createIIR", "createFIR",
           "Filter", "FilterUpdate", "load_designs", "makeFilter", "check_design",
           "Scope",
           "SystemResult", "runSystem", "run_main"]


# ---------------------------------------------------------------------------
# Algebraic functions
# ---------------------------------------------------------------------------
#
# Every function has its arithmetic as kernels, plain functions on plain
# values (SystemExtensionSpecs.md 2.8); the base class runs them. The
# tick program copies the kernels and calls them on local variables; with
# numba it compiles them (Specs 4.7).

def add2_out(a, b):
    return a + b


def add3_out(a, b, c):
    return a + b + c


def add4_out(a, b, c, d):
    return a + b + c + d


def gain_out(x, k):
    return k * x


def clip_out(x, lo, hi):
    if x > hi:
        return hi
    if x < lo:
        return lo
    return x


class Add2(Algebraic):
    """y = a + b."""
    inputs = ("a", "b")
    outputs = ("y",)
    kernels = (add2_out,)


class Add3(Algebraic):
    """y = a + b + c."""
    inputs = ("a", "b", "c")
    outputs = ("y",)
    kernels = (add3_out,)


class Add4(Algebraic):
    """y = a + b + c + d."""
    inputs = ("a", "b", "c", "d")
    outputs = ("y",)
    kernels = (add4_out,)


class Gain(Algebraic):
    """y = k x. With k = 0 or 1 it opens or closes a loop
    (SystemExtensionDesign.md 3: a switch block was REJECTED).

    :param k: gain
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (gain_out,)

    def __init__(self, k):
        super().__init__()
        self.k = float(k)
        self.params = (self.k,)


class Clip(Algebraic):
    """y = x limited to [lo, hi].

    :param lo: lower limit
    :param hi: upper limit
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (clip_out,)

    def __init__(self, lo, hi):
        super().__init__()
        self.lo, self.hi = float(lo), float(hi)
        if self.lo > self.hi:
            raise ValueError("Clip: lo must not exceed hi")
        self.params = (self.lo, self.hi)


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def constant_out(value):
    return value


# the waveform codes of the Signal kernel and the slots of its parameter
# array p: [offset, delay, amplitude, frequency, phase (rad), duty, slope,
# f_start, f_end, duration]
_SIGNAL_CODES = {"step": 0, "ramp": 1, "sine": 2, "square": 3, "triangle": 4,
                 "chirp": 5, "noise": 6, "pwl": 7}


def signal_out(tm, state, code, p, samples, pwl_t, pwl_y):
    """The value of the waveform *code* at the time *tm* of the tick
    (Specs 15.2: a source lives in physical time), ``offset`` before
    the delay. Noise is the sample at the index in *state*, pwl the
    interpolation of its points."""
    t = tm - p[1]
    if code == 6:
        return p[0] + samples[int(state[0])]
    if t < 0.0:
        return p[0]
    if code == 0:
        return p[0] + p[2]
    if code == 1:
        return p[0] + p[6] * t
    if code == 2:
        return p[0] + p[2] * sin(2.0 * pi * p[3] * t + p[4])
    if code == 3:
        cyc = (p[3] * t + p[4] / (2.0 * pi)) % 1.0
        return p[0] + (p[2] if cyc < p[5] else -p[2])
    if code == 4:
        cyc = (p[3] * t + p[4] / (2.0 * pi)) % 1.0
        if cyc < 0.25:
            tri = 4.0 * cyc
        elif cyc < 0.75:
            tri = 2.0 - 4.0 * cyc
        else:
            tri = 4.0 * cyc - 4.0
        return p[0] + p[2] * tri
    if code == 5:
        T = p[9]
        k = (p[8] - p[7]) / T
        ts = t if t < T else T
        phase = 2.0 * pi * (p[7] * ts + 0.5 * k * ts * ts)
        if t > T:
            phase += 2.0 * pi * p[8] * (t - T)
        return p[0] + p[2] * sin(phase + p[4])
    return p[0] + np.interp(t, pwl_t, pwl_y)


def signal_upd(tm, y, state, code, p, samples, pwl_t, pwl_y):
    state[0] += 1.0


class Constant(Algebraic):
    """y = value: a held value, not a sampled one (Specs 6.1.3).

    The one block without inputs and without a clock. Its output is
    set when the block is made, so every reader sees it from the first
    tick, and it never fires: an algebraic block fires when a source
    fires, and a constant has none. A clocked constant writing the same
    value at every tick of a domain was the first form and was REPLACED
    (Anton, 2026-11-17: "the constant has a clock input, which is not
    necessary"). A fixed set point that must change during the run is a
    ``Signal``.

    :param value: the output value
    """
    inputs = ()
    outputs = ("y",)
    kernels = (constant_out,)

    def __init__(self, value):
        self.value = float(value)
        self.y = self.value              # held from the start, resume included
        super().__init__()
        self.params = (self.value,)


# One signal source for every waveform (Anton, 2026-11-16: "we make a
# signal source and the signal can be a sine, a chirp, a square wave, a
# triangle, noise, or pwl from a file"). Separate Step, Ramp, WhiteNoise
# and Samples classes were REPLACED by this the same day. The waveform
# is evaluated in the kernel at the time of the tick (Specs 15.2, step
# 12.1, 2026-11-20): with a driven reference clock the times of the
# ticks are not known before the run. The samples made in advance, "an
# array and an index" (2026-11-16), were REPLACED by that; noise keeps
# its sample array, drawn in advance by the seed, and pwl its points.
#
# Every waveform has ``offset`` and ``delay``: before ``delay`` the
# output is ``offset``. The table gives the other parameters with their
# defaults; None marks a required one.

WAVEFORMS = {
    "step":     {"amplitude": 1.0},
    "ramp":     {"slope": None},
    "sine":     {"amplitude": 1.0, "frequency": None, "phase": 0.0},
    "square":   {"amplitude": 1.0, "frequency": None, "phase": 0.0,
                 "duty": 0.5},
    "triangle": {"amplitude": 1.0, "frequency": None, "phase": 0.0},
    "chirp":    {"amplitude": 1.0, "f_start": None, "f_end": None,
                 "duration": None, "phase": 0.0},
    "noise":    {"sigma": None, "density": None, "distribution": "gaussian",
                 "seed": 0},
    "pwl":      {"points": None, "path": None, "column": 1},
}

_DISTRIBUTIONS = ("gaussian", "uniform")


class Signal(Clocked):
    """A signal source: one sample per tick of its domain, output ``y``.

    :param waveform: one of ``WAVEFORMS``: "step", "ramp", "sine",
                     "square", "triangle", "chirp", "noise", "pwl"
    :param offset: value added to every waveform; the output before
                   *delay* (default 0)
    :param delay: time [s] at which the waveform starts (default 0)
    :param parameters: the parameters of the waveform, see below

    Time t is the physical time of the tick (Specs 15.2): the tick
    count times the master tick with a nominal clock, the accumulated
    tick durations with a driven one; t' = t - delay.

    - step: ``offset`` before, ``offset + amplitude`` from t' = 0 on.
    - ramp: ``offset + slope t'``.
    - sine: ``amplitude sin(2 pi frequency t' + phase)``, phase in
      degrees.
    - square: ``+amplitude`` for the first ``duty`` part of every period,
      ``-amplitude`` for the rest; ``phase`` in degrees shifts it.
    - triangle: between ``-amplitude`` and ``+amplitude``, starting at
      zero and rising; ``phase`` in degrees shifts it.
    - chirp: a sine whose frequency rises linearly from ``f_start`` to
      ``f_end`` in ``duration`` seconds and stays at ``f_end`` after.
    - noise: white, always; a shaped spectrum is a filter behind it
      (Specs 6.1.1). The level is ``sigma``, the RMS per sample, or
      ``density``, the one-sided spectral density in V^2/Hz, converted
      with the sample rate: sigma^2 = density f_s / 2. ``distribution``
      is "gaussian" or "uniform" (same RMS, width sigma sqrt(12)).
      ``seed``: the same seed gives the same sequence in every run; two
      sources need two seeds.
    - pwl: piecewise linear through ``points``, a sequence of (t, y)
      pairs, or through a text file ``path`` read with ``numpy.loadtxt``
      (time in column 0, value in ``column``, default 1).
      Before the first point the output is the first value, after the
      last point the last value. The run is shortened to the last point
      (``limit()``, Specs 6.2).

    The noise samples are made by ``prepare()``, called by the engine
    with the number of firings of the run. By hand: set ``Ts`` and
    call ``prepare(n)`` first. The state is the index of the next
    sample; a continuation after ``load_state()`` makes the sequence
    again from the start and goes on at the index. The other waveforms
    are formulas of the time (``signal_out``).
    """
    inputs = ()
    outputs = ("y",)
    kernels = (signal_out, signal_upd)
    uses_time = True

    def __init__(self, waveform, offset=0.0, delay=0.0, **parameters):
        super().__init__(order=1)
        if waveform not in WAVEFORMS:
            raise ValueError("Signal: waveform must be one of %s"
                             % ", ".join(WAVEFORMS))
        table = WAVEFORMS[waveform]
        unknown = sorted(set(parameters) - set(table))
        if unknown:
            raise ValueError("Signal %s: unknown parameter%s %s"
                             % (waveform, "s" if len(unknown) > 1 else "",
                                ", ".join(unknown)))
        self.waveform = waveform
        self.offset, self.delay = float(offset), float(delay)
        self.parameters = dict(table)
        self.parameters.update(parameters)
        self._check()
        self.samples = np.zeros(1)
        self._pwl = None
        if waveform == "pwl":
            self._pwl = self._pwl_points()
        self._code = _SIGNAL_CODES[waveform]
        self._p = self._parameter_array()
        self._pwl_t = (np.asarray(self._pwl[0], dtype=float) if self._pwl
                       else np.zeros(1))
        self._pwl_y = (np.asarray(self._pwl[1], dtype=float) if self._pwl
                       else np.zeros(1))

    def _parameter_array(self):
        """The parameters as the kernel reads them (see ``signal_out``)."""
        p, out = self.parameters, np.zeros(10)
        out[0], out[1] = self.offset, self.delay
        for i, key in enumerate(("amplitude", "frequency", "phase", "duty",
                                 "slope", "f_start", "f_end", "duration"), 2):
            if p.get(key) is not None:
                out[i] = float(p[key])
        out[4] = np.radians(out[4])                       # phase in degrees
        return out

    def _check(self):
        p = self.parameters
        if self.waveform == "noise":
            if (p["sigma"] is None) == (p["density"] is None):
                raise ValueError("Signal noise: give sigma or density, "
                                 "not both")
            if p["distribution"] not in _DISTRIBUTIONS:
                raise ValueError("Signal noise: distribution must be one "
                                 "of %s" % ", ".join(_DISTRIBUTIONS))
            return
        if self.waveform == "pwl":
            if (p["points"] is None) == (p["path"] is None):
                raise ValueError("Signal pwl: give points or path, not both")
            return
        missing = sorted(k for k, v in p.items() if v is None)
        if missing:
            raise ValueError("Signal %s: missing parameter%s %s"
                             % (self.waveform,
                                "s" if len(missing) > 1 else "",
                                ", ".join(missing)))
        if self.waveform == "square" and not 0.0 < p["duty"] < 1.0:
            raise ValueError("Signal square: duty must be between 0 and 1")
        if self.waveform == "chirp" and p["duration"] <= 0.0:
            raise ValueError("Signal chirp: duration must be positive")

    def _pwl_points(self):
        p = self.parameters
        if p["path"] is not None:
            data = np.loadtxt(p["path"], ndmin=2)
            tp, yp = data[:, 0], data[:, int(p["column"])]
        else:
            pts = np.array([[float(a), float(b)] for a, b in p["points"]],
                           ndmin=2)
            if pts.size == 0:
                raise ValueError("Signal pwl: at least one point")
            tp, yp = pts[:, 0], pts[:, 1]
        if np.any(np.diff(tp) < 0):
            raise ValueError("Signal pwl: times must not decrease")
        return tp, yp

    @property
    def params(self):
        return (self._code, self._p, self.samples, self._pwl_t, self._pwl_y)

    @property
    def index(self):
        """Number of samples played so far."""
        return int(self.state[0])

    def _Ts(self):
        if self.Ts is None:
            raise ValueError("%s: the sample time is not set; add the "
                             "function to a system first" % (self,))
        return float(self.Ts)

    def rms(self):
        """Noise only: the RMS value per sample, from ``sigma`` or from
        ``density`` and the sample time of the domain."""
        p = self.parameters
        if p["sigma"] is not None:
            return float(p["sigma"])
        return sqrt(float(p["density"]) / (2.0 * self._Ts()))

    def limit(self):
        """pwl: firings up to and including the last point; else None."""
        if self._pwl is None:
            return None
        t_last = self._pwl[0][-1] + self.delay
        n = int(np.floor(t_last / self._Ts() + 1e-9)) + 1
        return max(n - self.index, 0)

    def prepare(self, firings):
        """Noise: draw the samples from the first tick of the run up to
        the index plus *firings*, by the seed. The other waveforms are
        formulas of the time and need nothing."""
        if self.waveform != "noise":
            return
        n = max(1, self.index + int(firings))
        p = self.parameters
        rng = np.random.default_rng(int(p["seed"]))
        rms = self.rms()
        if p["distribution"] == "gaussian":
            self.samples = rms * rng.standard_normal(n)
        else:
            half = rms * sqrt(3.0)
            self.samples = rng.uniform(-half, half, n)


# ---------------------------------------------------------------------------
# Delay and filter sections
# ---------------------------------------------------------------------------

def _shift_in(state, start, d, value):
    """Shift register of length d at state[start:start+d]: value in."""
    for i in range(start + d - 1, start, -1):
        state[i] = state[i - 1]
    state[start] = value


def delay_out(x, state, d):
    if d == 0:
        return x
    return state[d - 1]


def delay_upd(x, y, state, d):
    if d > 0:
        _shift_in(state, 0, d, x)


def bilin_out(x, state, b, a):
    return b[0] * x + state[0]


def bilin_upd(x, y, state, b, a):
    state[0] = b[1] * x - a[1] * y


def biquad_out(x, state, b, a):
    return b[0] * x + state[0]


def biquad_upd(x, y, state, b, a):
    state[0] = state[1] + b[1] * x - a[1] * y
    state[1] = b[2] * x - a[2] * y


def fir_out(x, state, taps):
    y = taps[0] * x
    for i in range(state.shape[0]):
        y += taps[i + 1] * state[i]
    return y


def fir_upd(x, y, state, taps):
    n = state.shape[0]
    if n > 0:
        _shift_in(state, 0, n, x)


def _normalise(b, a, nb, na, name):
    b = [float(v) for v in b]
    a = [float(v) for v in a]
    if len(b) != nb or len(a) != na:
        raise ValueError("%s: expected %d numerator and %d denominator "
                         "coefficients" % (name, nb, na))
    if a[0] == 0.0:
        raise ValueError("%s: a0 must be nonzero" % name)
    return [v / a[0] for v in b], [v / a[0] for v in a]


def _ztransfer(b, a):
    """Rational in ``ini.z`` for coefficients in powers of 1/z."""
    z = ini.z
    num = sum(sp.Float(bk) * z**(-k) for k, bk in enumerate(b))
    den = sum(sp.Float(ak) * z**(-k) for k, ak in enumerate(a))
    return sp.cancel(sp.together(num / den))


class Delay(Clocked):
    """Delay of d cycles of its domain, a shift register.

    :param d: number of stages (>= 0). With d = 0 the output is the
              input of the same tick, a direct output.
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (delay_out, delay_upd)

    def __init__(self, d):
        d = int(d)
        if d < 0:
            raise ValueError("Delay: d must be >= 0")
        super().__init__(order=d)
        self.direct = {"y"} if d == 0 else set()
        self.params = (d,)


class Bilin(Clocked):
    """First-order section, transposed direct form 2 (floating point).

    H(z) = (b0 + b1 z^-1) / (1 + a1 z^-1), coefficients normalised by
    a0 at creation. ``ztransfer`` holds H(z) in ``ini.z``. The output
    is direct when b0 is nonzero.

    :param b: [b0, b1]
    :param a: [a0, a1]
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (bilin_out, bilin_upd)

    def __init__(self, b, a):
        super().__init__(order=1)
        b, a = _normalise(b, a, 2, 2, "Bilin")
        self.b, self.a = np.array(b), np.array(a)
        self.params = (self.b, self.a)
        self.direct = {"y"} if b[0] != 0.0 else set()
        self.ztransfer = _ztransfer(b, a)


class Biquad(Clocked):
    """Second-order section, transposed direct form 2 (floating point).

    H(z) = (b0 + b1 z^-1 + b2 z^-2) / (1 + a1 z^-1 + a2 z^-2),
    coefficients normalised by a0 at creation. Transposed direct form 2
    is the floating-point choice: two state values, no mantissa
    swamping. (Direct form 1 is the fixed-point choice and comes with
    the fixed-point library.) ``ztransfer`` holds H(z) in ``ini.z``.
    The output is direct when b0 is nonzero.

    :param b: [b0, b1, b2]
    :param a: [a0, a1, a2]
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (biquad_out, biquad_upd)

    def __init__(self, b, a):
        super().__init__(order=2)
        b, a = _normalise(b, a, 3, 3, "Biquad")
        self.b, self.a = np.array(b), np.array(a)
        self.params = (self.b, self.a)
        self.direct = {"y"} if b[0] != 0.0 else set()
        self.ztransfer = _ztransfer(b, a)


class FIR(Clocked):
    """Finite impulse response filter.

    y[n] = sum_k taps[k] x[n-k]. The state holds the last len(taps)-1
    inputs. The output is direct when taps[0] is nonzero. ``ztransfer``
    holds H(z), a polynomial in 1/z.

    :param taps: the impulse response, at least one tap
    """
    inputs = ("x",)
    outputs = ("y",)
    kernels = (fir_out, fir_upd)

    def __init__(self, taps):
        taps = np.array([float(v) for v in taps])
        if taps.size < 1:
            raise ValueError("FIR: at least one tap")
        super().__init__(order=taps.size - 1)
        self.taps = taps
        self.params = (self.taps,)
        self.direct = {"y"} if taps[0] != 0.0 else set()
        self.ztransfer = _ztransfer(list(taps), [1.0])


# ---------------------------------------------------------------------------
# CORDIC and NCO
# ---------------------------------------------------------------------------
#
# The CORDIC is in the product: a fixed-point one and later one built
# from shift registers and adders follow. Replacing it by cos and sin
# for speed was REJECTED (Anton, 2026-11-16).

# The pipeline is a ring of d slots: a sample stays in its slot and is
# advanced in place by the n iterations of its stage, the slot of stage j
# is (head + j) mod d, and a new sample takes the slot the finished one
# leaves. The stage loop is written out in the kernel: a helper called
# per stage cost as much as the iterations under numba (NCO + CordicIQ at
# 1 GHz, compiled: n = 1, d = 24 went from 280 to 199 ns per tick, n = 24,
# d = 1 from 129 to 110; the old batch block with 24 registers took 163;
# 2026-11-19). Moving the samples one slot per tick instead of the ring
# was the first form and was REPLACED the same day.

def cordic_iq_out(x, phi, state, theta, pow2, k, n, d):
    slot = int(state[5 * d]) + d - 1
    if slot >= d:
        slot -= d
    s = 5 * slot
    sign = state[s + 4]
    return state[s] * k * sign, state[s + 1] * k * sign


def cordic_iq_upd(x, phi, I, Q, state, theta, pow2, k, n, d):
    head = int(state[5 * d]) - 1
    if head < 0:
        head = d - 1
    state[5 * d] = head
    phi = (phi + pi) % (2.0 * pi) - pi
    sign = 1.0
    if phi > pi / 2:
        phi -= pi
        sign = -1.0
    elif phi < -pi / 2:
        phi += pi
        sign = -1.0
    s = 5 * head
    state[s + 3], state[s + 4] = phi, sign
    y = 0.0
    angle = 0.0
    # the stages inline, not through a helper: a call per stage cost as
    # much as the iterations (2026-11-19)
    for j in range(d):
        if j > 0:
            slot = head + j
            if slot >= d:
                slot -= d
            s = 5 * slot
            x, y, angle, phi = state[s], state[s + 1], state[s + 2], state[s + 3]
        i = j * n
        for m in range(n):
            p2 = pow2[i]
            if angle < phi:
                angle += theta[i]
                x, y = x - y * p2, x * p2 + y
            else:
                angle -= theta[i]
                x, y = x + y * p2, -x * p2 + y
            i += 1
        state[s], state[s + 1], state[s + 2] = x, y, angle


def cordic_mag_out(x, y, state, theta, pow2, k, n, d):
    slot = int(state[2 * d]) + d - 1
    if slot >= d:
        slot -= d
    return state[2 * slot] * k


def cordic_mag_upd(x, y, A, state, theta, pow2, k, n, d):
    head = int(state[2 * d]) - 1
    if head < 0:
        head = d - 1
    state[2 * d] = head
    s = 2 * head
    if x < 0.0:
        x = -x
    for j in range(d):
        if j > 0:
            slot = head + j
            if slot >= d:
                slot -= d
            s = 2 * slot
            x, y = state[s], state[s + 1]
        i = j * n
        for m in range(n):
            p2 = pow2[i]
            dx, dy = x * p2, y * p2
            if y >= 0.0:
                x += dy
                y -= dx
            else:
                x -= dy
                y += dx
            i += 1
        state[s], state[s + 1] = x, y


class _CordicBlock(Clocked):
    """Common part: a pipeline of d stages, each stage n iterations per
    tick, n * d iterations per sample, the output d ticks after the
    input; a ring of d slots and a head index as the state. The
    parameters are the tables of the n * d rotations, the gain, n and d. One model for different implementations, as fast as
    the iterations allow (Anton, 2026-11-19): n = 1, d = 24 is the
    pipelined hardware, n = 24, d = 1 the batch. All iterations in the
    tick of the input followed by d registers (n the total, d >= 0)
    was the first form and was REPLACED the same day."""

    _per_stage = 5

    def __init__(self, n, d):
        n, d = int(n), int(d)
        if n < 1:
            raise ValueError("%s: n, the iterations per tick, must be >= 1"
                             % type(self).__name__)
        if d < 1:
            raise ValueError("%s: d, the number of ticks, must be >= 1"
                             % type(self).__name__)
        super().__init__(order=d * self._per_stage + 1)      # the slots and the head
        self.n, self.d = n, d
        total = n * d
        self.theta = np.array([atan2(1.0, 2.0**i) for i in range(total)])
        self.pow2 = np.array([2.0**-i for i in range(total)])
        k = 1.0
        for i in range(total):
            k *= 1.0 / sqrt(1.0 + 2.0**(-2 * i))
        self.k = k
        self.params = (self.theta, self.pow2, self.k, n, d)


class CordicIQ(_CordicBlock):
    """CORDIC I/Q modulator in rotational mode, as a pipeline.

    I = x cos(phi), Q = x sin(phi), no limit on x and phi.

    :param n: iterations per tick (per stage)
    :param d: number of ticks (stages): n * d iterations per sample,
              the outputs d ticks after the inputs
    """
    inputs = ("x", "phi")
    outputs = ("I", "Q")
    kernels = (cordic_iq_out, cordic_iq_upd)
    _per_stage = 5


class CordicMag(_CordicBlock):
    """CORDIC magnitude detector in vectoring mode, as a pipeline.

    A = sqrt(x^2 + y^2).

    :param n: iterations per tick (per stage)
    :param d: number of ticks (stages), as for ``CordicIQ``
    """
    inputs = ("x", "y")
    outputs = ("A",)
    kernels = (cordic_mag_out, cordic_mag_upd)
    _per_stage = 2


def nco_out(x, state, Ts, f_c, kF, df_min, df_max):
    return state[0], state[1]


def nco_upd(x, phi, fdev, state, Ts, f_c, kF, df_min, df_max):
    f = kF * x
    if f > df_max:
        f = df_max
    elif f < df_min:
        f = df_min
    p = state[0] + 2.0 * pi * Ts * (f_c + f)
    if p >= pi:
        p -= 2.0 * pi
    elif p < -pi:
        p += 2.0 * pi
    state[0] = p
    state[1] = f


class NCO(Clocked):
    """Numerically controlled oscillator: an integrator accumulating
    phase. The sine generation is a separate ``CordicIQ`` block behind
    it, with x = amplitude and phi = this phase (the CORDIC inside the
    NCO of the reference example was taken apart, Anton, 2026-11-16).

    Input ``x``: set point. The frequency is f_c + k_F x, with the
    deviation k_F x limited to [df_min, df_max]. Outputs ``phi`` (rad,
    in [-pi, pi)) and ``fdev`` (Hz, the limited deviation), both from
    the state: the set point read at a tick changes the phase and the
    deviation of the next tick. No feedthrough, so a loop may close
    through the NCO.

    The limits were called ``fmin`` and ``fmax`` until 2026-11-17 and
    were read as the frequency range of the oscillator, which they are
    not (Anton: "fmin and fmax must be the limits, not the deviation
    limits; if the original NCO meant deviation limits, the names must
    change"). Deviation limits are kept, since with tight limiting the
    values need few digits; the names now say so.

    :param f_c: centre frequency, the frequency at x = 0 [Hz]
    :param kF: frequency sensitivity [Hz per unit of x]
    :param df_min: lower limit of the frequency deviation [Hz]
    :param df_max: upper limit of the frequency deviation [Hz]

    State: [phase, deviation].
    """
    inputs = ("x",)
    outputs = ("phi", "fdev")
    kernels = (nco_out, nco_upd)

    def __init__(self, f_c, kF, df_min, df_max):
        super().__init__(order=2)
        self.f_c, self.kF = float(f_c), float(kF)
        self.df_min, self.df_max = float(df_min), float(df_max)

    @property
    def params(self):
        Ts = 0.0 if self.Ts is None else float(self.Ts)
        return (Ts, self.f_c, self.kF, self.df_min, self.df_max)


# ---------------------------------------------------------------------------
# Filter design: createIIR() and createFIR()
# ---------------------------------------------------------------------------

_WINDOWS = {"rect": None, "hann": np.hanning, "hamming": np.hamming,
            "blackman": np.blackman, "bartlett": np.bartlett}


def _window(name, length):
    """One-sided window of *length* taps: the right half of the symmetric
    numpy window of 2*length-1 points, so w[0] = 1 and the taps taper to
    the end. A causal impulse response starts with its largest values,
    which a symmetric window would attenuate."""
    try:
        fn = _WINDOWS[name]
    except KeyError:
        raise ValueError("unknown window %r; one of %s"
                         % (name, ", ".join(sorted(_WINDOWS)))) from None
    if fn is None:
        return np.ones(length)
    return fn(2 * length - 1)[length - 1:]


def _expr_of(source, attr, what):
    """The sympy expression of *source*: the attribute *attr* of a SLiCAP
    result object, or the expression itself (sympy or str)."""
    if hasattr(source, attr):
        expr = getattr(source, attr)
        if isinstance(expr, (list, tuple)):
            raise ValueError("%s: the result is stepped; design one filter "
                             "per step" % what)
        if not isinstance(expr, sp.Basic):
            raise ValueError("%s: the result has no %s" % (what, attr))
        return expr
    if isinstance(source, str):
        # SLiCAP's parser: Q, beta, ... are parameters of the filter.
        # sp.sympify was REPLACED (2026-11-22): it read Q as sympy's
        # assumptions object, so a transfer with Q raised TypeError.
        # Scale factors are read as everywhere in SLiCAP, numbers stay
        # floats (Anton, 2026-11-23). Full SLiCAP notation, with numbers as
        # exact fractions, was considered and REJECTED (2026-11-23): texts
        # that work today would change from floats to exact numbers.
        from SLiCAP.SLiCAPlex import _sympify, _replaceScaleFactors
        return _sympify(_replaceScaleFactors(source))
    if isinstance(source, sp.Basic):
        return source
    raise TypeError("%s: expected a SLiCAP result or an expression, got %r"
                    % (what, type(source).__name__))


class Realisation:
    """The numeric realisation of a filter design (``FilterResult``) for
    one sample period and one set of parameter values: ``gain`` (overall
    gain, not folded into a section), ``sections`` (list of ``{"kind":
    "biquad"|"bilin", "b": [...], "a": [1, ...]}`` or one ``{"kind":
    "fir", "taps": [...]}``), ``structure`` (the poles and zeros per
    section, for the next update of a programmable filter; None for a
    FIR), ``Ts`` and ``values``.

    ``functions()`` gives the section instances for a run script. The
    gain is a separate ``Gain`` block in the diagram. ``ztransfer`` is
    the z-domain transfer of the realisation in ``ini.z``.
    """

    def __init__(self, dataType, Ts, values, gain, sections, structure=None):
        self.dataType = dataType
        self.Ts = float(Ts)
        self.values = dict(values)
        self.gain = float(gain)
        self.sections = sections
        self.structure = structure

    def functions(self):
        """The section instances in cascade order (``Bilin``, ``Biquad``
        or one ``FIR``)."""
        out = []
        for sec in self.sections:
            if sec["kind"] == "biquad":
                out.append(Biquad(sec["b"], sec["a"]))
            elif sec["kind"] == "bilin":
                out.append(Bilin(sec["b"], sec["a"]))
            elif sec["kind"] == "fir":
                out.append(FIR(sec["taps"]))
            else:
                raise ValueError("unknown section kind %r" % sec["kind"])
        return out

    @property
    def ztransfer(self):
        from SLiCAP.SLiCAPmath import sectionsZ
        if self.dataType == "fir":
            return _ztransfer(list(self.sections[0]["taps"]), [1.0])
        return sectionsZ(self.gain, self.sections)

    def __repr__(self):
        return "Realisation(%s, Ts=%g, %d section%s)" % (
            self.dataType, self.Ts, len(self.sections),
            "" if len(self.sections) == 1 else "s")


class FilterResult:
    """The filter that ``createIIR()`` or ``createFIR()`` makes, stored in
    the design data like any other result (SystemExtensionDesign.md 6,
    Specs 10.3.1): a transfer with the way it is computed, not its
    coefficients.

    Attributes of the design: ``name``, ``dataType`` ("iir" or "fir"),
    ``laplace`` (the Laplace transfer, sympy, its parameters as symbols),
    ``params`` (the names of the free symbols of the transfer other than
    the Laplace variable, in alphabetical order), ``method`` (IIR) or
    ``window`` and ``length`` (FIR), ``stationary``, ``Ts`` and
    ``ts_param``.

    The design holds no coefficients: they depend on the parameter values
    and on the sample period, and are computed in the run by
    ``realise()``. ``stationary`` (Specs 15.3) says what the sample period
    is: True, a digital filter with fixed coefficients, computed for
    ``Ts``, the filter's own sample period, or for the value of the
    parameter ``ts_param``; False, the discrete-time implementation of an
    analog filter, whose coefficients follow the actual sample period of
    its clock in the run (``Filter``, the modal state-space form). ``Ts``
    and ``sections`` as attributes of the result were built 2026-11-16 and
    REPLACED (Anton, 2026-11-17: "it should just take the connected
    clock"); ``Ts`` came back 2026-11-20 as the stationary filter's own
    property (Anton: "it is a property of the filter and not of the
    system").

    ``makeFilter()`` fixes ONE evaluation (Anton, 2026-11-25): it sets
    ``Ts`` (the clock period of a non-stationary filter, the value of a Ts
    parameter) and ``values``, and computes ``H_s``, the Laplace transfer,
    and ``H_z``, the z-transfer the run executes, with every value
    substituted, and their frequency responses, expressions in
    ``ini.frequency``: ``H_fs``, H_s at s = j 2 pi f, and ``H_fz``, H_z at
    z = exp(j 2 pi f Ts) (TRACES.md phase 9). ``impulse()`` and
    ``stepResp()`` give the sample responses at k Ts. ``sweepData()`` evaluates them, and they can be combined
    like the ``laplace`` attribute of a SLiCAP result. A second class for
    the evaluated filter was considered and REJECTED the same day, and so
    was a separate ``Tclk``: ``Ts`` is the sample period of ``H_z``.

    REMOVED 2026-11-25 (Anton: the filter has a transfer; pins and a
    schematic belong to the block): ``pins``, now ``filter_pins()`` of the
    block side; ``schematic``, now read by the editor from the design
    script's makeCircuit line; ``sweep_dataset()``, now ``sweepData()`` on
    the trace side; ``simType`` and ``step``, never meaningful for a filter.
    """

    design_data_attrs = ("laplace", "method", "window", "length", "params",
                         "stationary", "Ts", "ts_param", "values", "H_s",
                         "H_z", "H_fs", "H_fz")

    def __init__(self, dataType, name=None):
        self.dataType = dataType
        self.name = name
        self.laplace = None
        self.method = None
        self.window = None
        self.length = None
        self.stationary = True
        self.Ts = None            # the sample period: the filter's own, or set by makeFilter()
        self.ts_param = None      # ... or the name of the parameter that gives it
        self.params = []
        # one evaluation, set by makeFilter()
        self.values = None
        self.H_s = None
        self.H_z = None
        self.H_fs = None
        self.H_fz = None
        self._coefficient_function = None

    def __getstate__(self):
        state = dict(self.__dict__)
        state["_coefficient_function"] = None        # a lambdified function
        return state

    def coefficients(self, values=None):
        """``(b, a)``: the float coefficient lists of the Laplace transfer,
        decreasing powers of s, for the parameter *values*: a dict
        ``{name: value}`` or a sequence in the order of ``params``."""
        from SLiCAP.SLiCAPmath import _laplaceRational
        given = self._values(values)
        if self._coefficient_function is None:
            num, den = _laplaceRational(self.laplace)
            syms = sorted(self.laplace.free_symbols - {ini.laplace}, key=str)
            self._coefficient_function = sp.lambdify(
                syms, [num.all_coeffs(), den.all_coeffs()], "numpy")
        b, a = self._coefficient_function(*[given[n] for n in self.params])
        return [float(c) for c in b], [float(c) for c in a]

    def _values(self, values):
        if values is None:
            values = {}
        elif not isinstance(values, dict):
            values = dict(zip(self.params, values))
        missing = [n for n in self.params if n not in values]
        extra = [n for n in values if n not in self.params]
        if missing or extra:
            raise ValueError(
                "%s: the design has the parameters %s; got values for %s"
                % (self.name or "filter", ", ".join(self.params) or "none",
                   ", ".join(sorted(values)) or "none"))
        return {n: float(values[n]) for n in self.params}

    def realise(self, Ts, values=None, previous=None):
        """The numeric realisation for the sample period *Ts* and the
        parameter *values* (``coefficients()``): a ``Realisation``.
        *previous* is the ``structure`` of an earlier realisation; the
        new poles and zeros are then assigned to its sections by
        continuity (``coeffs2sections()``, Specs 10.3.5)."""
        from SLiCAP.SLiCAPmath import coeffs2sections, coeffs2taps
        given = self._values(values)
        b, a = self.coefficients(given)
        if self.dataType == "fir":
            taps = coeffs2taps(b, a, Ts, self.length) * _window(self.window,
                                                                self.length)
            return Realisation("fir", Ts, given, 1.0,
                               [{"kind": "fir", "taps": [float(v) for v in taps]}])
        out = coeffs2sections(b, a, Ts, self.method, previous)
        return Realisation("iir", Ts, given, out["gain"], out["sections"],
                           out["structure"])

    # The response of a filter for a sample period and parameter values,
    # as the run computes it (Anton, 2026-11-24): the filter object knows
    # how it is executed, so it gives its z-transfer. By default for the Ts
    # and the values makeFilter() gave it. A missing Ts or missing values
    # give a warning and None, not an exception: a script continues (Anton,
    # 2026-11-24). makeFilter() itself refuses them with an error.

    def _period(self, Ts, what):
        """*Ts* as a positive float (a number, or a text in SLiCAP
        notation), by default the filter's ``Ts``; None with a warning."""
        if Ts is None:
            Ts = self.Ts
        if isinstance(Ts, str):
            from SLiCAP.SLiCAPlex import _sympify, _replaceScaleFactors
            try:
                Ts = _sympify(_replaceScaleFactors(Ts))
            except sp.SympifyError:
                Ts = None
        try:
            Ts = float(Ts)
        except (TypeError, ValueError):
            Ts = None
        if Ts is None or not Ts > 0:
            print("Warning: %s: %s() needs a positive sample period Ts; make "
                  "the filter with sl.makeFilter()." % (self.name or "filter", what))
            return None
        return Ts

    def _given(self, values, what):
        """The parameter values as ``_values()`` checks them, by default
        those makeFilter() gave; None with a warning when they do not match
        the parameters of the filter."""
        if values is None and self.values is not None:
            values = {n: v for n, v in self.values.items() if n in self.params}
        try:
            return self._values(values)
        except (ValueError, TypeError) as exc:
            print("Warning: %s() of %s" % (what, exc))
            return None

    def ztransfer(self, Ts=None, values=None):
        """The z-domain transfer in ``ini.z`` that the run executes, for the
        sample period *Ts* and the parameter *values* (``coefficients()``).
        Without them: those of the evaluation ``makeFilter()`` made, or
        the filter's own Ts:

        - a stationary IIR filter: its gain times the product of its
          sections (``Realisation.ztransfer``);
        - a FIR filter: the polynomial of its taps;
        - a non-stationary IIR filter: the zoh or foh discretisation of the
          whole transfer, which the run steps in state-space form, as a
          product of first- and second-order factors computed with 50
          digits (``SLiCAPmath._holdZ``).

        A product of factors, not one polynomial: the float coefficients of
        one polynomial lose all accuracy for a filter with many poles close
        to z = 1 (2026-11-24). Use ``z2fourier()`` for the frequency
        response, or ``sweepData()`` for traces.

        :return: the z-transfer, or None with a warning when there is no
                 sample period or the values do not match the parameters.
        :rtype: sympy.Expr, NoneType
        """
        Ts = self._period(Ts, "ztransfer")
        given = None if Ts is None else self._given(values, "ztransfer")
        if given is None:
            return None
        if self.dataType == "fir" or self.stationary:
            return self.realise(Ts, given).ztransfer
        from SLiCAP.SLiCAPmath import _holdZ
        b, a = self.coefficients(given)
        return _holdZ(b, a, Ts, self.method or "zoh")

    # The sample responses, as the run computes them, for makeDataset()
    # (TRACES.md phase 9). METHODS, not attributes: unlike H_fs, a sample
    # response depends on the range (Anton, 2026-11-25). The names are
    # those of a SLiCAP result, so FLT1.stepResp and LAPLACE1.stepResp read
    # alike.

    def _sample_range(self, start, stop, what):
        """``(k0, k1, Ts)``: the sample indices from *start* to *stop*.
        Raises ValueError for a filter not made with makeFilter() or a
        range without a sample time."""
        from SLiCAP.SLiCAPmath import _checkNumber
        if self.H_z is None or not self.Ts:
            raise ValueError("%s: %s() needs the filter made with "
                             "sl.makeFilter()" % (self.name or "filter", what))
        limits = []
        for value in (start, stop):
            number = _checkNumber(value)
            if number is None:
                raise ValueError("%s: %s(): %r is not a number"
                                 % (self.name or "filter", what, value))
            limits.append(float(number))
        Ts = float(self.Ts)
        k0 = max(int(np.ceil(limits[0] / Ts - 1e-9)), 0)
        k1 = int(np.floor(limits[1] / Ts + 1e-9))
        if k1 < k0:
            raise ValueError("%s: %s(): no sample time k*Ts in [%g, %g] s"
                             % (self.name or "filter", what, limits[0], limits[1]))
        return k0, k1, Ts

    def impulse(self, start, stop):
        """``(t, y)``: the response to one sample of value 1 at k = 0,
        divided by Ts so that it lies on the impulse response of the Laplace
        transfer (Anton, 2026-11-24), at the sample times k Ts from *start*
        to *stop* (numbers or SLiCAP notation)."""
        from SLiCAP.SLiCAPmath import _zFilter
        k0, k1, Ts = self._sample_range(start, stop, "impulse")
        x = np.zeros(k1 + 1)
        x[0] = 1.0
        return np.arange(k0, k1 + 1) * Ts, _zFilter(self.H_z, x)[k0:] / Ts

    def stepResp(self, start, stop):
        """``(t, y)``: the response to a unit step at k = 0, at the sample
        times k Ts from *start* to *stop* (numbers or SLiCAP notation)."""
        from SLiCAP.SLiCAPmath import _zFilter
        k0, k1, Ts = self._sample_range(start, stop, "stepResp")
        return (np.arange(k0, k1 + 1) * Ts,
                _zFilter(self.H_z, np.ones(k1 + 1))[k0:])

    def __repr__(self):
        return "FilterResult(%s, %s)" % (
            self.dataType, ", ".join(self.params) or "no parameters")


def _design(source, what, name, dataType):
    """The common part of the create functions: the Laplace transfer of
    *source*, checked rational and proper, and its parameters."""
    from SLiCAP.SLiCAPmath import _laplaceRational
    Hs = _expr_of(source, "laplace", what)
    num, den = _laplaceRational(Hs)
    if num.degree() > den.degree():
        raise ValueError(
            "%s: improper transfer function (numerator degree %d above "
            "denominator degree %d). Make it proper (a series resistance "
            "with a capacitance, for example)." % (what, num.degree(),
                                                   den.degree()))
    res = FilterResult(dataType, name)
    res.laplace = Hs
    res.params = sorted(str(v) for v in Hs.free_symbols - {ini.laplace})
    return res


def createIIR(source, method=None, name=None, stationary=True, Ts=None):
    """Designs an IIR filter from a Laplace transfer function: a cascade of
    second-order and first-order sections, realised in the run for the
    sample period of the filter and the values of its parameters
    (``FilterResult.realise()``, Specs 10.3). A NON-STATIONARY filter
    (Specs 15.3), the implementation of an analog filter, runs instead
    in state-space form stepped exactly over the actual tick, its
    matrices recomputed when the clock changes; *method* is then
    "zoh" (default), the input held over the tick, exact for a DAC
    output, or "foh", the input linear between the samples, for a
    sampled analog signal (no half-tick lag).

    :param source: a SLiCAP result with a ``laplace`` attribute
                   (``doLaplace()``), or the transfer function itself
                   (sympy.Expr or str), rational in ``ini.laplace``; its
                   free symbols other than the Laplace variable are the
                   parameters of the filter. A str may have scale factors
                   ("1/(1+s/1k)"), its numbers stay floats.
    :param method: stationary: "bilinear" (default), "zoh", "foh", ... as
                   ``laplace2z()``; non-stationary: "zoh" (default) or
                   "foh"
    :type method: str
    :param name: name of the result (default None)
    :type name: str
    :param stationary: True (default): fixed coefficients for the sample
                       period *Ts*; False: the coefficients follow the
                       actual clock
    :type stationary: bool
    :param Ts: the sample period of a stationary filter [s], a property
               of the filter, or the name of a parameter pin of the block
               that gives it in the run (a parent block can pass it); a
               stationary design without it can be realised by hand
               (``realise(Ts)``) but not placed as a block
    :type Ts: float, str
    :return: FilterResult
    """
    res = _design(source, "createIIR", name, "iir")
    res.stationary = bool(stationary)
    if method is None:
        method = "bilinear" if res.stationary else "zoh"
    if not res.stationary and method not in ("zoh", "foh"):
        raise ValueError("createIIR: a non-stationary filter steps with "
                         "\"zoh\" or \"foh\", not %r" % (method,))
    res.method = method
    _sample_period(res, Ts, "createIIR")
    return res


def _sample_period(res, Ts, what):
    """The sample period of a design: a positive number, the name of a
    parameter pin (an identifier) that gives it in the run, or None.
    A non-stationary filter has none: it follows the clock."""
    if Ts is None:
        return
    if not res.stationary:
        raise ValueError("%s: a non-stationary filter follows the clock and "
                         "has no sample period of its own" % what)
    if isinstance(Ts, str):
        name = Ts.strip()
        if not name.isidentifier():
            raise ValueError("%s: Ts must be a number or the name of a "
                             "parameter, not %r" % (what, Ts))
        if name in res.params:
            raise ValueError("%s: %s is already a parameter of the transfer"
                             % (what, name))
        res.ts_param = name
        return
    res.Ts = float(Ts)
    if res.Ts <= 0.0:
        raise ValueError("%s: Ts must be positive" % what)


def createFIR(source, length, window="hamming", name=None, Ts=None):
    """Designs a FIR filter from a Laplace transfer function: the taps
    are the samples ``Ts * h(k Ts)``, k = 0 ... length-1, of its impulse
    response, times a one-sided window (w[0] = 1, tapering to the end),
    realised in the run for the sample period of the filter's clock
    (``FilterResult.realise()``, ``coeffs2taps()``). The factor Ts keeps
    the DC gain: the sum of the taps approximates the integral of h(t).
    The direct term of a transfer with equal degrees goes into the first
    tap. A separate ``doImpulse()`` result as the source was built
    2026-11-16 and REPLACED (Specs 10.3.1): the impulse response is
    derived from the Laplace transfer in the run.

    :param source: a SLiCAP result with a ``laplace`` attribute, or the
                   transfer function itself (sympy.Expr or str). A str may
                   have scale factors ("1/(1+s/1k)"), its numbers stay
                   floats.
    :param length: number of taps
    :type length: int
    :param window: "hamming" (default), "hann", "blackman", "bartlett"
                   or "rect"
    :type window: str
    :param name: name of the result (default None)
    :type name: str
    :param Ts: the sample period of the taps [s], a property of the
               filter, or the name of a parameter pin that gives it;
               without it the design can be realised by hand but not
               placed as a block. A FIR filter is stationary.
    :type Ts: float, str
    :return: FilterResult
    """
    length = int(length)
    if length < 1:
        raise ValueError("createFIR: length must be at least 1")
    _window(window, 1)                      # unknown window: refused now
    res = _design(source, "createFIR", name, "fir")
    res.window = window
    res.length = length
    _sample_period(res, Ts, "createFIR")
    return res


# ---------------------------------------------------------------------------
# The programmable filter (Specs 10.3.3 to 10.3.6)
# ---------------------------------------------------------------------------
#
# One block in the diagram, two functions for the engine: the Filter in the
# domain of its signal clock cp, and its FilterUpdate in the domain of the
# update clock cu, a pacing domain. The coefficients are arrays the Filter
# holds as parameters and the FilterUpdate writes; the compiled program
# sees them by reference. A filter without parameters has no update: it
# realises its design once, when the program reads its parameters.

# The state-space form of a non-stationary filter (Specs 15.3, 15.4):
# x' = A x + B u, y = C x + D u, the controllable canonical form of the
# block's transfer (scipy.signal.tf2ss), which keeps its meaning under
# any change of the coefficients, a complex pair becoming two real poles
# or a double pole included (Anton, 2026-11-20: "you cannot just change
# this"). Stepped exactly over the actual tick T by the matrix
# exponential of the augmented matrix (Van Loan), computed by scipy in
# ``_discretise``:
#   zoh, the input held:  x[k+1] = Ad x[k] + G0 u[k]
#   foh, the input linear between the samples (the triangle hold):
#                         x[k+1] = Ad x[k] + (G0 - G1) u[k] + G1 u[k+1]
# The term in u[k+1] makes the output at tick k+1 depend on the input
# of that tick, which the Filter declares (direct output), so the state
# kept between the ticks is the part known at the end of the tick,
# x~[k+1] = Ad x[k] + Bd u[k] with Bd = G0 - G1, and x[k] = x~[k] + B2
# u[k] with B2 = G1 (zero for zoh). B2 belongs to the interval that LED
# to tick k, so with a varying tick the state record is the pair (x~,
# B2): ``ss_retime`` computes Ad, Bd and B2n, the weights of the NEXT
# interval, and the update takes B2n over as B2 once that interval is
# stepped. The engine calls the retime when the tick duration changed;
# it reaches scipy through numba's object mode, about thirty ticks of
# simulation per call, nothing for a switched or drifting clock, a
# factor thirty under a jittering one (Anton, 2026-11-20: acceptable, a
# fast kernel later, Specs 14). The modal form with closed-form blocks
# per pole was built first and REPLACED: it needed distinct poles and a
# fixed block structure, which a parameter update can break. foh
# removes the half-tick lag of the staircase for a sampled analog
# input; zoh is the exact one for a held input, a DAC.

try:
    from numba import objmode
except ImportError:                        # plain Python: the block does nothing
    import contextlib

    def objmode(**types):
        """numba's objmode without numba: called as numba's is, with the
        types of the variables the block assigns, and a context that does
        nothing. An object with __enter__ and __exit__ was used until
        2026-11-20 and REPLACED: `with objmode():` calls it, so every
        non-stationary filter failed without numba ("'_NoObjMode' object
        is not callable", Anton's Windows test, where numba did not
        import). Linux never took this branch."""
        return contextlib.nullcontext()


def _discretise(T, foh, A, B, Ad, Bd, B2n):
    """Ad, Bd and B2n of the state-space step over the sample period *T*,
    in place: one matrix exponential of the augmented matrix."""
    from scipy.linalg import expm
    n = A.shape[0]
    em = np.zeros((n + 2, n + 2))
    em[:n, :n] = A * T
    em[:n, n] = B * T
    em[n, n + 1] = 1.0
    ms = expm(em)
    Ad[:, :] = ms[:n, :n]
    g0 = ms[:n, n]
    g1 = ms[:n, n + 1]
    if foh:
        Bd[:] = g0 - g1
        B2n[:] = g1
    else:
        Bd[:] = g0
        B2n[:] = 0.0


_discretise.python_only = True            # reached through object mode, not compiled


def ss_out(x, state, A, B, C, D, Ad, Bd, B2, B2n, per, dt_cur, hold, xk):
    y = D[0] * x
    for i in range(C.shape[0]):
        y += C[i] * (state[i] + B2[i] * x)
    return y


def ss_upd(x, y, state, A, B, C, D, Ad, Bd, B2, B2n, per, dt_cur, hold, xk):
    # xk is a scratch array of the block: an allocation per tick inside the
    # compiled loop cost a third of the step (Anton, 2026-11-20)
    n = C.shape[0]
    for i in range(n):
        xk[i] = state[i] + B2[i] * x
    for i in range(n):
        v = Bd[i] * x
        for j in range(n):
            v += Ad[i, j] * xk[j]
        state[i] = v
    for i in range(n):
        B2[i] = B2n[i]                     # the weight of the interval just stepped


def ss_retime(dt, A, B, C, D, Ad, Bd, B2, B2n, per, dt_cur, hold, xk):
    """Ad, Bd and B2n for the master tick *dt*, the weights of the next
    interval: the sample period is ``per[0] * dt``; ``hold[0]`` 0 for
    zoh, 1 for foh. The step is computed by scipy, reached from the
    compiled program through object mode."""
    dt_cur[0] = dt
    with objmode():
        _discretise(per[0] * dt, hold[0] > 0.5, A, B, Ad, Bd, B2n)


def filter_out(x, state, gain, b, a):
    v = x
    for i in range(b.shape[0]):
        v = b[i, 0] * v + state[2 * i]
    return gain[0] * v


def filter_upd(x, y, state, gain, b, a):
    v = x
    for i in range(b.shape[0]):
        w = b[i, 0] * v + state[2 * i]
        state[2 * i] = state[2 * i + 1] + b[i, 1] * v - a[i, 1] * w
        state[2 * i + 1] = b[i, 2] * v - a[i, 2] * w
        v = w


def filter_pins(design):
    """The parameter pins of a filter block: the parameters of the
    transfer of its filter *design* and, for a stationary filter whose
    sample period is a parameter, that parameter (Anton, 2026-11-20: "make
    it a parameter, then we can set it from a parent block"). A property
    of the BLOCK: ``FilterResult.pins`` was REMOVED 2026-11-25 (Anton: the
    filter has a transfer; pins belong to the block)."""
    return list(design.params) + ([design.ts_param] if design.ts_param else [])


class Filter(Clocked):
    """The filter block of a design (``createIIR()`` or ``createFIR()``):
    the complete filter, all its sections and its gain, with the
    parameter update (Specs 10.3.3).

    :param design: the ``FilterResult``

    Pins: ``x`` in, ``y`` out, the signal clock (the domain the block is
    added to). An IIR design runs as a cascade of second-order sections
    in transposed direct form 2, every section the same arithmetic as
    ``Biquad`` (a first-order remainder is a section with zero second
    coefficients); a FIR design runs as ``FIR``. The output is declared
    direct whatever the coefficients: they are not known when the block
    is made and may change. A loop closed through a programmable filter
    therefore needs another state output in the loop.

    A design with parameters (free symbols of the transfer) has an
    ``updater``, a ``FilterUpdate`` with one input per parameter, to be
    added to the domain of the update clock, or without a domain: the
    coefficients are then computed once, before the first block, from
    the values on the parameter pins (constants, Anton, 2026-11-18;
    in the diagram a cu pin without a clock). Without parameters
    ``updater`` is None and the coefficients are realised once, for the
    sample period of the signal clock, before the run starts (Specs
    10.3.4). ``realisation`` holds the last ``Realisation`` loaded.
    """
    inputs = ("x",)
    outputs = ("y",)
    from_design = True          # its symbol comes from a design, not from the class

    def __init__(self, design):
        if not isinstance(design, FilterResult):
            raise TypeError("Filter: expected a FilterResult, got %r"
                            % type(design).__name__)
        self.design = design
        self.realisation = None
        self.retime = None
        if design.dataType == "fir":
            super().__init__(order=design.length - 1)
            self.taps = np.zeros(design.length)
            self.kernels = (fir_out, fir_upd)
            self.params = (self.taps,)
        elif not design.stationary:
            # the state-space form (Specs 15.3), stepped exactly over the
            # actual tick, recomputed by ``ss_retime`` when the tick
            # changes; the sections of a stationary filter cannot be
            # recomputed in a kernel (the factorisation needs roots)
            from SLiCAP.SLiCAPmath import _laplaceRational
            _, den = _laplaceRational(design.laplace)
            n = den.degree()
            super().__init__(order=n)
            self.A = np.zeros((n, n))
            self.B = np.zeros(n)
            self.C = np.zeros(n)
            self.D = np.zeros(1)
            self.Ad = np.zeros((n, n))
            self.Bd = np.zeros(n)
            self.B2 = np.zeros(n)                 # the weight of the last step
            self.B2n = np.zeros(n)                # ... of the next one (retime)
            self.per = np.ones(1)
            self.dt_cur = np.zeros(1)
            self.hold = np.array([1.0 if design.method == "foh" else 0.0])
            self.xk = np.zeros(n)                 # scratch of the update kernel
            self.kernels = (ss_out, ss_upd)
            self.retime = ss_retime
            self.params = (self.A, self.B, self.C, self.D, self.Ad, self.Bd,
                           self.B2, self.B2n, self.per, self.dt_cur, self.hold,
                           self.xk)
            self._loaded = False
        else:
            from SLiCAP.SLiCAPmath import _laplaceRational
            _, den = _laplaceRational(design.laplace)
            n = (den.degree() + 1) // 2          # sections, two poles each
            super().__init__(order=2 * n)
            self.gain = np.zeros(1)
            self.b = np.zeros((n, 3))
            self.a = np.zeros((n, 3))
            self.kernels = (filter_out, filter_upd)
            self.params = (self.gain, self.b, self.a)
        self.direct = {"y"}
        self.updater = FilterUpdate(self) if filter_pins(design) else None

    @property
    def stationary(self):
        return self.design.stationary or self.design.dataType == "fir"

    def design_period(self):
        """The sample period a stationary filter is realised for: the
        design's own ``Ts``, a property of the filter and of nothing
        else (Anton, 2026-11-20: "it must be an input on this widget").
        Taking the nominal period of the clock instead was built and
        REJECTED the same day."""
        if self.design.Ts is None:
            raise ValueError(
                "%s: the design %s has no sample period; a stationary filter "
                "is designed for its own sample period: Design... in the "
                "block's Properties, \"Sample period\", or Ts= of createIIR "
                "and createFIR" % (self.name, self.design.name or "of the block"))
        return float(self.design.Ts)

    def prepare(self, firings):
        """Before the run: a filter without parameters realises its
        design, for its design period (stationary) or for the nominal
        tick of its clock (non-stationary, ``load_ss``); one with
        parameters must have its updater in the system."""
        if self.updater is None:
            if self.stationary:
                if self.realisation is None:
                    self.load(self.design.realise(self.design_period()))
            elif not self._loaded:
                self.load_ss(*self.design.coefficients({}))
        elif self.updater.name is None:              # never added to the system
            raise ValueError(
                "%s: the design has the parameters %s; add %s.updater to the "
                "system, in the domain of the update clock, or without a "
                "domain to compute the coefficients once"
                % (self.name, ", ".join(filter_pins(self.design)), self.name))

    def load_ss(self, b, a):
        """Non-stationary: the state-space form of the transfer with the
        coefficients *b*, *a* into the arrays the program holds (the
        controllable canonical form, whose state keeps its meaning across
        a parameter update), and Ad, Bd for the current master tick (the
        nominal one before the run)."""
        from scipy.signal import tf2ss
        A, B, C, D = tf2ss(np.asarray(b, dtype=float), np.asarray(a, dtype=float))
        n = self.A.shape[0]
        if A.shape[0] != n:
            raise ValueError("%s: the design has %d poles now, %d before: the "
                             "structure of the filter is fixed at the start of "
                             "the run" % (self.name, A.shape[0], n))
        self.A[:, :] = A
        self.B[:] = B.ravel()
        self.C[:] = C.ravel()
        self.D[0] = float(np.asarray(D).ravel()[0]) if np.asarray(D).size else 0.0
        self._loaded = True
        if self.Ts is not None:
            self.per[0] = float(getattr(self, "period", 1))
            first = self.dt_cur[0] <= 0.0
            dt = self.dt_cur[0] if not first else self.Ts / self.per[0]
            ss_retime(dt, *self.params)
            if first:
                self.B2[:] = self.B2n                 # no step yet: the same weights

    def load(self, realisation):
        """Load the coefficients of *realisation* into the arrays the
        program holds."""
        if realisation.dataType == "fir":
            taps = realisation.sections[0]["taps"]
            if len(taps) != self.taps.size:
                raise ValueError("%s: %d taps, expected %d"
                                 % (self.name, len(taps), self.taps.size))
            self.taps[:] = taps
        else:
            secs = realisation.sections
            if len(secs) != self.b.shape[0]:
                raise ValueError(
                    "%s: the realisation has %d sections, the block %d: "
                    "the structure of the filter is fixed at the start of "
                    "the run" % (self.name, len(secs), self.b.shape[0]))
            self.gain[0] = realisation.gain
            self.b[:] = 0.0
            self.a[:] = 0.0
            for i, sec in enumerate(secs):
                self.b[i, :len(sec["b"])] = sec["b"]
                self.a[i, :len(sec["a"])] = sec["a"]
        self.realisation = realisation


class FilterUpdate(Clocked):
    """The update half of a ``Filter`` with parameters (Specs 10.3.4,
    10.3.6): fires with the update clock, a pacing domain, between the
    blocks of the run. Its inputs are the parameters of the design, in
    alphabetical order. At each firing it realises the design for the
    present input values and the sample period of the filter's signal
    clock, tracking the poles and zeros into the sections of the
    previous realisation, and loads the coefficients into the filter.
    Its state is that structure, so a continuation keeps the tracking.
    No outputs: the coefficients are parameters of the filter, not
    signals. Made by ``Filter``, never directly.
    """
    outputs = ()
    kernels = None
    pacing = True                       # the System requires a pacing domain
    from_design = True

    def __init__(self, flt):
        self.inputs = tuple(filter_pins(flt.design))
        super().__init__(order=0)
        self.filter = flt
        self._structure = None
        self._next = None

    def output(self):
        flt = self.filter
        if flt.Ts is None:
            raise ValueError("%s: add the filter %s to its clock domain "
                             "before the run" % (self.name, flt.name))
        values = {n: float(getattr(self, n)) for n in flt.design.params}
        if not flt.stationary:
            flt.load_ss(*flt.design.coefficients(values))
            return
        ts_name = flt.design.ts_param
        if ts_name:
            Ts = float(getattr(self, ts_name))        # the sample period from its pin
            if Ts <= 0.0:
                raise ValueError("%s: the sample period on pin %s is %g, not "
                                 "positive" % (flt.name, ts_name, Ts))
        else:
            Ts = flt.design_period()
        self._next = flt.design.realise(Ts, values, previous=self._structure)
        flt.load(self._next)

    def update(self):
        if self._next is not None:
            self._structure = self._next.structure

    def read_state(self):
        """The structure as a complex array, one row per section:
        two poles and two zeros, NaN for an absent one."""
        if not self._structure:
            return np.zeros((0, 4), dtype=complex)
        out = np.full((len(self._structure), 4), np.nan, dtype=complex)
        for i, sec in enumerate(self._structure):
            for j, r in enumerate(sec["poles"][:2]):
                out[i, j] = r
            for j, r in enumerate(sec["zeros"][:2]):
                out[i, 2 + j] = r
        return out

    def load_state(self, vector):
        arr = np.asarray(vector, dtype=complex).reshape(-1, 4)
        if arr.shape[0] == 0:
            self._structure = None
            return
        self._structure = [
            {"poles": [complex(r) for r in row[:2] if not np.isnan(r.real)],
             "zeros": [complex(r) for r in row[2:] if not np.isnan(r.real)]}
            for row in arr]


# The designs loaded during ONE run instruction: build() runs the library
# files, and a stepped run calls build() once per value; the design files
# are not parameterised from the sheet (Specs 10.4.2), so the circuit
# analysis of a design is done once per instruction, not once per step
# (Anton, 2026-11-19: "LRC is checked for every run"). None outside a run.
_DESIGNS_OF_RUN = None


def load_designs(files):
    """The filter designs of the library *files* of a diagram (Specs
    10.3.1: the sheet's library block names them, the run script lists
    them as ``LIBRARIES``): every file, a path relative to the project
    root, is run as an instruction file in a namespace of its own, and
    every ``FilterResult`` it assigns is collected under the name it is
    assigned to. Returns ``{name: design}``. The project of the working
    directory is loaded first, as an instruction file's main.py does:
    a design file calls makeCircuit() and doLaplace(). A name two files
    assign is an error. Within one run instruction the files are run
    once (``_DESIGNS_OF_RUN``).

    This is the loader of the run script. An instruction file makes one
    filter with ``makeFilter()``. A *name* argument for that use, added
    2026-11-24, was REMOVED 2026-11-25 when makeFilter() took the role.

    :param files: paths of the design files, relative to the project root
    :type files: list
    :return: ``{name: design}``
    :rtype: dict
    """
    import runpy
    import SLiCAP
    key = tuple(str(f) for f in files)
    if _DESIGNS_OF_RUN is not None and key in _DESIGNS_OF_RUN:
        return dict(_DESIGNS_OF_RUN[key])
    SLiCAP.loadProject()
    designs, where = {}, {}
    for file in files:
        path = Path.cwd() / str(file)         # the project root, as loadProject() takes it
        if not path.is_file():
            raise FileNotFoundError("library file not found: %s" % file)
        ns = runpy.run_path(str(path), run_name=path.stem)
        for name, obj in ns.items():
            if isinstance(obj, FilterResult) and not name.startswith("_"):
                if name in designs and where[name] != file:
                    raise ValueError("the design %s is assigned in %s and in %s"
                                     % (name, where[name], file))
                if obj.name is None:
                    obj.name = name
                designs[name], where[name] = obj, file
    if _DESIGNS_OF_RUN is not None:
        _DESIGNS_OF_RUN[key] = dict(designs)
    return designs


def makeFilter(file, Ts=None, params=None):
    """Makes the filter of the design script *file* for one sample period
    and one set of parameter values, for its z-transfer and its traces in
    an instruction file (Anton, 2026-11-25)::

        FLT1 = sl.makeFilter("lib/filter_a.py", Ts="10u",
                             params=sl.selectPars("system1", circuit=["f_c"]))
        D1   = sl.makeDataset({"FLT1": FLT1}, x="frequency", start="10",
                              stop="50k", num=200)

    The script runs, as in a system run, so the filter is never out of
    date. The returned object is the filter itself (``FilterResult``)
    with its evaluation set: ``Ts``, ``values``, and ``H_s`` and ``H_z``,
    the Laplace transfer and the z-transfer the run executes, with every
    value substituted, and their frequency responses ``H_fs`` and
    ``H_fz``. They combine like the ``laplace`` attribute of a
    SLiCAP result, ``FLT1.H_s + FLT2.H_s``. A filter data file
    written by createIIR() and read here was considered and REJECTED
    (2026-11-25): it is out of date as soon as the circuit, its parameters
    or the specs change, and only running the script sees that.

    A stationary filter uses its own Ts: *Ts* is not used for it. A Ts
    parameter takes its value from *params*, like the other parameters, and
    that value becomes ``Ts``. A non-stationary filter gets *Ts*, the
    period of its clock.

    Errors, not warnings: the filter is used further on, and a script
    should stop at the cause (Anton, 2026-11-25). The GUI prevents them.

    :param file: the design script, relative to the project root; it must
                 make exactly one filter (createIIR() or createFIR())
    :type file: str
    :param Ts: the clock period of a non-stationary filter: a number, SLiCAP
               notation ("10u") or the name of a parameter in *params*
    :type Ts: str, float, int, NoneType
    :param params: the parameter values, ``{name: value}``, as
                   ``selectPars()`` returns them; a value may be an
                   expression in the other parameters
    :type params: dict, NoneType
    :return: the filter
    :rtype: FilterResult
    :raises FileNotFoundError: the script does not exist
    :raises ValueError: the script makes no filter or more than one, a
                        parameter has no numeric value, or a non-stationary
                        filter has no positive Ts
    """
    import copy
    from SLiCAP.SLiCAPmath import _checkNumber, _checkExpression, fullSubs
    if not (Path.cwd() / str(file)).is_file():
        raise FileNotFoundError("makeFilter: the design script %s does not "
                                "exist." % file)
    made = load_designs([file])
    if len(made) != 1:
        raise ValueError("makeFilter: %s must make one filter (createIIR() or "
                         "createFIR()); it makes %s." % (
                             file, ", ".join(sorted(made)) or "none"))
    # its own object: a filter loaded during a run is shared by the run
    flt = copy.copy(next(iter(made.values())))
    par_defs = {}
    for key, value in (params or {}).items():
        par_defs[sp.Symbol(str(key))] = (_checkExpression(value)
                                         if isinstance(value, str)
                                         else sp.sympify(value))
    values = {}
    for name in filter_pins(flt):
        symbol = sp.Symbol(name)
        number = None
        if symbol in par_defs:
            number = sp.N(fullSubs(par_defs[symbol], par_defs))
        if number is None or not (number.is_number and number.is_real):
            raise ValueError("makeFilter: the parameter %s of %s has no "
                             "numeric value in params." % (name, flt.name))
        values[name] = float(number)
    if flt.ts_param and not values[flt.ts_param] > 0:
        raise ValueError("makeFilter: the sample period %s of %s is %g, not "
                         "positive." % (flt.ts_param, flt.name,
                                        values[flt.ts_param]))
    flt.values = values
    if flt.ts_param:
        flt.Ts = values[flt.ts_param]
    elif not flt.stationary:
        period = None if Ts is None else _checkNumber(Ts, par_defs)
        if period is None or not period > 0:
            raise ValueError("makeFilter: %s is non-stationary: it needs the "
                             "clock period Ts, a positive number or a "
                             "parameter in params; got %r." % (flt.name, Ts))
        flt.Ts = float(period)
    given = {n: values[n] for n in flt.params}
    flt.H_s = flt.laplace.xreplace({sp.Symbol(n): v for n, v in given.items()})
    flt.H_z = flt.ztransfer(flt.Ts, given)
    # the frequency responses, as z2fourier() and sweepData() take f
    from SLiCAP.SLiCAPmath import z2fourier
    s_f = (2 * sp.pi * sp.I if ini.hz else sp.I) * ini.frequency
    flt.H_fs = flt.H_s.xreplace({ini.laplace: s_f})
    flt.H_fz = z2fourier(flt.H_z, flt.Ts)
    return flt


def check_design(designs, name, controls=()):
    """The design *name* of *designs* (``load_designs()``), checked
    against *controls*, the parameter pins of the block in the diagram:
    a design the library files do not assign, or whose parameters
    changed since the block was placed, is refused with the advice to
    redefine the block (Specs 10.3.2: "the only forbidden thing is to
    change the schematic of a filter without redefining the block").
    ``design_of(designs, name, controls)`` on the ``designs`` argument
    of ``runSystem()`` (2026-11-18) and ``check_design(design,
    controls)`` on a design function of the run script (step 9) were
    REPLACED by the library files (2026-11-19)."""
    design = designs.get(name)
    if design is None:
        raise ValueError(
            "no library file of the diagram assigns the design %s (they "
            "assign %s); add its file to the libraries (System > Library...)"
            % (name, ", ".join(sorted(designs)) or "nothing"))
    if filter_pins(design) != list(controls):
        raise ValueError(
            "%s: the block in the diagram has the parameter pins %s, the "
            "design has the parameters %s; redefine the block (Design... in "
            "its Properties), then wire the new pins"
            % (name, ", ".join(controls) or "none",
               ", ".join(filter_pins(design)) or "none"))
    return design


# ---------------------------------------------------------------------------
# The parameters of a run (Specs 10.4)
# ---------------------------------------------------------------------------

class Scope:
    """The parameters a run script evaluates its values in (Specs 10.4.4):
    the global SLiCAP parameters of the compiled libraries (q, k, c,
    mu_0, epsilon_0, T, U_T), the parameter table of the sheet on top,
    the values of the run (``params=`` of ``runSystem``, the step value)
    on top of that. Every value is a SLiCAP expression, resolved
    recursively (``fullSubs``). The run script makes one at the top of
    ``build()``: ``P = Scope(PARAMS, params)``, and writes every argument
    that is not a plain number as ``P("expr")`` or ``P.int("expr")``.

    A name found nowhere, or an integer argument that does not come out
    as an integer, is refused with the argument named: the engine never
    sees an expression.
    """

    def __init__(self, sheet=None, run=None):
        import SLiCAP
        from SLiCAP.SLiCAPmath import _checkExpression
        if not ini.SLiCAPPARAMS:
            SLiCAP.loadProject()           # compiles the libraries: the globals
        self.defs = {}
        for name, value in ini.SLiCAPPARAMS.items():
            self.defs[sp.Symbol(str(name))] = value
        self.sheet = dict(sheet or {})
        self.run = dict(run or {})
        for source in (self.sheet, self.run):
            for name, value in source.items():
                if isinstance(value, sp.Basic):
                    expr = value                   # a selectPars() dictionary
                else:
                    expr = _checkExpression(value if isinstance(value, str) else float(value))
                if expr is None:
                    raise ValueError("parameter %s: not an expression: %r" % (name, value))
                self.defs[sp.Symbol(str(name))] = expr

    def value(self, text, what="value"):
        """*text*, a SLiCAP expression, resolved to a sympy number."""
        from SLiCAP.SLiCAPmath import _checkExpression, fullSubs
        expr = _checkExpression(text if isinstance(text, str) else float(text))
        if expr is None:
            raise ValueError("%s: not an expression: %r" % (what, text))
        expr = fullSubs(expr, self.defs)
        free = sorted(str(s) for s in getattr(expr, "free_symbols", ()))
        if free:
            raise ValueError(
                "%s = %r names %s, defined nowhere: not in the parameter table "
                "of the sheet, not in the run (params=) and not a global "
                "SLiCAP parameter" % (what, text, ", ".join(free)))
        return sp.N(expr)

    def __call__(self, text, what="value"):
        """*text* as a float."""
        value = self.value(text, what)
        try:
            return float(value)
        except TypeError:
            raise ValueError("%s = %r is not a real number: %s" % (what, text, value))

    def int(self, text, what="value"):
        """*text* as an integer; a value that is not one is refused."""
        value = self(text, what)
        if value != int(round(value)):
            raise ValueError("%s = %r must be an integer, it is %g" % (what, text, value))
        return int(round(value))

    def child(self, given, table, instance):
        """The scope of a hierarchical block's diagram (Specs 10.4.6),
        like a subcircuit instance in SLiCAP: the global parameters, the
        child diagram's own table *table* (its defaults) and, on top, the
        values *given* on the block, expressions in THIS scope, the
        parent's, resolved here. A name of the parent's sheet is not
        seen inside the child unless the block passes it, as a subcircuit
        parameter is local. *instance* names the block in refusals."""
        return Scope(table, {name: self.value(text, "%s.%s" % (instance, name))
                             for name, text in given.items()})


def _step_values(step):
    """The step of a run (Specs 10.4.7), the step dictionary of the
    NGspice instruction: ``(name, values)`` for the methods ``lin``,
    ``log`` and ``list``; ``array`` is not built for a system run yet.
    The interpretation follows ``SLiCAPngspice._step_values``, without
    the deck resolver: the limits are numbers in SLiCAP notation."""
    from SLiCAP.SLiCAPlex import _scale_float
    method = str(step.get("method", "list")).lower()
    name = step.get("param") or step.get("params")
    if isinstance(name, (list, tuple)):
        if len(name) != 1 or method == "array":
            raise ValueError("a system run steps one parameter; array stepping "
                             "is not available")
        name = name[0]
    if not name:
        raise ValueError('step definition without "param"')
    if method in ("lin", "log"):
        missing = [k for k in ("start", "stop", "num") if step.get(k) is None]
        if missing:
            raise ValueError('step method "%s" without %s'
                             % (method, ", ".join(missing)))
        start, stop = (_scale_float(str(step[k])) for k in ("start", "stop"))
        num = int(_scale_float(str(step["num"])))
        space = np.linspace if method == "lin" else np.geomspace
        return str(name), space(start, stop, num)
    if method == "list":
        values = step.get("values")
        if not values:
            raise ValueError('step method "list" without "values"')
        return str(name), np.asarray([_scale_float(str(v)) for v in values], dtype=float)
    raise ValueError("step method must be lin, log or list; got %r" % method)


# ---------------------------------------------------------------------------
# The run of a diagram's run script (Specs 8.2, 8.3; Design 9)
# ---------------------------------------------------------------------------
#
# The schematic editor writes <project root>/<name>.py from a .system_sch
# diagram: a build() that returns the System. runSystem() imports it, stores
# the selected signals, runs the engine and returns a SystemResult, a result
# object of the design data like any SLiCAP result. run_main() is the
# command-line entry the script itself calls under __main__.

class SystemResult:
    """The result of :func:`runSystem` (SystemExtensionSpecs.md 6.9): the
    report of the run, the clock domains and the stored signals.

    Every sample was recorded at an integer master tick, and that integer
    is kept. Time is derived from it, t = k * Ts, or, with a driven
    reference clock (Specs 15), read from the recorded time of every
    tick. A signal of a clocked
    domain with period P and phase p has its sample n at k = p + n * P,
    so time, master tick and sample index are one axis under a scale and
    an offset (6.9.1).

    The report: ``script`` (the run script), ``ticks`` (master ticks
    run), ``tick`` (the tick count after the run, the start of a
    continuation), ``master_tick`` (Ts in seconds), ``hyperperiod`` (in
    master ticks), ``mode`` ("jit" or "python"), ``seconds``,
    ``compile_seconds``, ``stopped``, ``ended`` and ``state_file``.

    ``domains``: per clock domain its ``period`` in master ticks, its
    ``phase``, the ``samples`` recorded and its stored ``signals``. A
    signal of an algebraic block fed from two domains lies on the joined
    domain "CK1+CK2", which has no period and no sample index (6.9.3).

    ``traces``: one SLiCAP trace per stored signal, named as the
    instruction asked, with time on the x axis. :meth:`trace` gives a
    signal against "time", "tick" or "sample"; :meth:`dataset` gives the
    signals of one domain as a dataset for ``sl.make_traces`` with the
    same choice of x (6.9.4, 6.9.5).
    """

    design_data_attrs = ("script", "ticks", "tick", "master_tick",
                         "hyperperiod", "mode", "seconds", "compile_seconds",
                         "runtime", "setup_seconds", "total_ticks", "stopped",
                         "ended", "state_file", "step_params", "clocks",
                         "domains", "traces")
    dataType = "system"
    simType = "numeric"

    #: the x axes of :meth:`trace` and :meth:`dataset`; each is the name
    #: of the x array, an identifier, so an expression may use it
    X_AXES = ("time", "tick", "sample")

    def __init__(self, script, system, result, asked=None, step=None, runs=(),
                 runtime=None):
        """*system* and *result* are the system and the engine result of
        the run, or of the FIRST run of a stepped run, whose other runs
        come as *runs*, ``[(system, result), ...]``, with *step* the
        ``(name, values)`` of the stepped parameter (Specs 10.4.8);
        *runtime* the wall-clock time of the whole instruction."""
        refs = {v: k for k, v in (asked or {}).items()}   # name -> "block.output"
        clocks = system.clocks
        self.script = str(script)
        self.system = system
        self.ticks = result.ticks
        self.tick = result.tick
        self.master_tick = clocks.master_tick
        self.hyperperiod = clocks.hyperperiod
        self.mode = result.mode
        self.reason = result.reason
        every = [result] + [r for _s, r in runs]
        self.seconds = sum(r.seconds for r in every)             # the loops
        self.compile_seconds = sum(r.compile_seconds for r in every)
        self.total_ticks = sum(r.ticks for r in every)
        self.runtime = runtime if runtime is not None else self.seconds + self.compile_seconds
        # the rest of the instruction: the library files, the builds
        self.setup_seconds = max(0.0, self.runtime - self.seconds - self.compile_seconds)
        self.stopped = result.stopped
        self.ended = result.ended
        self.state_file = str(result.state_file) if result.state_file else None
        # the stepped parameter and its value per run: {} for one run
        self.step_params = {step[0]: [float(v) for v in step[1]]} if step else {}
        self.step = bool(step)
        self._runs = [(system, result)] + list(runs)
        # per run: signal -> integer master ticks, signal -> values
        self._ticks = []
        self._values = []
        self._time = []           # per run: (first tick, seconds per tick) or None
        self._domain = {}         # signal -> clock domain
        for sysm, res in self._runs:
            ticks, values = {}, {}
            rt = getattr(res, "time", None)
            self._time.append((int(rt[0][0]), np.asarray(rt[1], dtype=float))
                              if rt is not None and len(rt[0]) else None)
            for name, (k, y) in res.traces.items():
                fn = sysm[refs.get(name, name).rsplit(".", 1)[0]]
                ticks[name] = np.asarray(k, dtype=np.int64)
                values[name] = y
                self._domain[name] = _domain_of(sysm, fn)
            self._ticks.append(ticks)
            self._values.append(values)
        # the clock tree as it ran: every node's frequency, period in
        # master ticks and phase; what the editor annotates on the clock
        # symbols after a run (Specs 10.4.9). Recorded only when every run
        # of a stepped result shares it: a step over a clock parameter
        # leaves no single tree to show (Anton, 2026-11-19: a step over a
        # temperature left the labels empty)
        self.clocks = {}
        for node, parent, f, period, phase in clocks.table():
            self.clocks[node] = {"parent": parent or "", "frequency": float(f),
                                 "period": period, "phase": phase}
        for sysm, _res in self._runs[1:]:
            if sysm.clocks.table() != clocks.table():
                self.clocks = {}
                break
        self.domains = {}
        first = self._ticks[0]
        for dom in sorted(set(self._domain.values())):
            names = [n for n in first if self._domain[n] == dom]
            rec = {}
            if dom in clocks.domains:
                rec["frequency"] = float(clocks.frequency(dom))
                rec["period"] = clocks.period(dom)
                rec["phase"] = clocks.phase(dom)
            rec["samples"] = int(first[names[0]].size)
            rec["signals"] = ", ".join(names)
            self.domains[dom] = rec
        self.traces = {}
        for name in first:
            if not self.step:
                self.traces[name] = self.trace(name)
            else:
                # one trace per run, labelled as make_traces labels a
                # stepped sweep: "f_dev  tau=24" (Specs 10.4.8)
                from SLiCAP.SLiCAPtraces import _step_label
                sname, svalues = step
                for i in range(len(self._runs)):
                    label = _step_label(name, sname, svalues, i)
                    self.traces[label] = self.trace(name, run=i)

    def _x(self, name, x, run=0):
        """``(x array, axis name)`` of signal *name* in *run* for the axis *x*."""
        ticks = self._ticks[run]
        if name not in ticks:
            raise ValueError("no stored signal %r; stored: %s"
                             % (name, ", ".join(ticks) or "none"))
        if x not in self.X_AXES:
            raise ValueError('x must be "time", "tick" or "sample", not %r' % (x,))
        k = ticks[name]
        clocks = self._runs[run][0].clocks
        if x == "time":
            rt = self._time[run]
            if rt is not None:                   # a driven clock: the recorded times
                first, seconds = rt
                return seconds[k - first], "time"
            return k * clocks.master_tick, "time"
        if x == "tick":
            return k, "tick"
        dom = self._domain[name]
        if dom not in clocks.domains:
            raise ValueError("signal %r lies on the joined domain %s, which "
                             "has no sample index; use x=\"tick\" or \"time\""
                             % (name, dom))
        return (k - clocks.phase(dom)) // clocks.period(dom), "sample"

    def trace(self, name, x="time", run=0):
        """The stored signal *name* as a SLiCAP trace against *x*: "time"
        in seconds, "tick" (the integer master tick) or "sample" (the
        integer sample index of its clock domain); *run* selects the run
        of a stepped result."""
        from SLiCAP.SLiCAPtraces import trace
        xd, xname = self._x(name, x, run)
        tr = trace([xd, self._values[run][name]])
        tr.xName, tr.yName, tr.label = xname, name, name
        if self.step:
            from SLiCAP.SLiCAPtraces import _step_label
            sname = next(iter(self.step_params))
            tr.label = _step_label(name, sname, self.step_params[sname], run)
        return tr

    def dataset(self, domain=None, x="time"):
        """The stored signals of one clock *domain* as a ``dataset`` for
        ``sl.make_traces``, against *x* as in :meth:`trace`. Without
        *domain* the stored signals must lie in one domain. A stepped
        result gives one row per run, with the step parameter, so
        ``make_traces`` labels the runs and a goal function gives one
        value per run (Specs 10.4.8); the runs must share the grid, which
        a stepped clock parameter breaks: the traces serve then."""
        from SLiCAP.SLiCAPtraces import dataset
        if domain is None:
            if len(self.domains) != 1:
                raise ValueError("the stepped signals lie in several clock "
                                 "domains (%s): give the domain"
                                 % ", ".join(self.domains))
            domain = next(iter(self.domains))
        if domain not in self.domains:
            raise ValueError("no stored signal in clock domain %r; the run "
                             "has: %s" % (domain, ", ".join(self.domains)))
        names = [n for n in self._ticks[0] if self._domain[n] == domain]
        xd, xname = self._x(names[0], x)
        units = {"time": "s"} if x == "time" else {}
        if not self.step:
            signals = {n: self._values[0][n] for n in names}
            return dataset(xname, xd, signals, {}, {}, units=units)
        for run in range(1, len(self._runs)):
            xr, _ = self._x(names[0], x, run)
            if xr.shape != xd.shape or not np.array_equal(xr, xd):
                raise ValueError("the runs of the stepped parameter %s have "
                                 "different grids (a clock was stepped): use "
                                 "the traces, one per run"
                                 % next(iter(self.step_params)))
        signals = {n: np.vstack([self._values[r][n] for r in range(len(self._runs))])
                   for n in names}
        return dataset(xname, xd, signals, dict(self.step_params), {}, units=units)

    def report(self, head=None) -> str:
        """The report of the run instruction (Anton, 2026-11-19): the runs,
        the mode, the times, the ticks and the slowdown, the simulation
        time per tick over the master tick (1 is real time)."""
        n = len(self._runs)
        head = head or "runSystem %s" % Path(self.script).name
        if self.step:
            name = next(iter(self.step_params))
            values = self.step_params[name]
            runs = "%d runs (%s = %.4g ... %.4g)" % (n, name, values[0], values[-1])
        else:
            runs = "1 run"
        per_tick = self.seconds / self.total_ticks if self.total_ticks else 0.0
        ticks = "{:,}".format(self.total_ticks)
        if n > 1:
            ticks += "   (%d x %s, hyperperiod %d)" % (n, "{:,}".format(self.ticks),
                                                     self.hyperperiod)
        else:
            ticks += "   (hyperperiod %d)" % self.hyperperiod
        compiled = ("(kernels, %d of %d runs)" % (sum(1 for _s, r in self._runs
                                                       if r.compile_seconds), n)
                    if self.mode == "jit" else "(python mode)")
        lines = [
            "%s: %s, mode %s%s" % (head, runs, self.mode,
                                   " (%s)" % self.reason if self.reason else ""),
            "  total runtime            : %.2f s" % self.runtime,
            "  setup time               : %.2f s   (library files, build)" % self.setup_seconds,
            "  compilation time         : %.2f s   %s" % (self.compile_seconds, compiled),
            "  simulation time          : %.2f s" % self.seconds,
            "  total number of ticks    : %s" % ticks,
            "  simulation time per tick : %s" % _si_time(per_tick),
            "  slowdown, per tick / Ts  : %.3g   (Ts = %s)" % (
                per_tick / self.master_tick if self.master_tick else 0.0,
                _si_time(self.master_tick)),
            "  stored: %s" % (", ".join(sorted(self._ticks[0])) or "nothing")]
        return "\n".join(lines)

    def __repr__(self):
        return "SystemResult(%s, ticks=%d, mode=%s, runs=%d, traces=%s)" % (
            self.script, self.ticks, self.mode, len(self._runs), sorted(self.traces))


def _si_time(seconds) -> str:
    """A time with an SI prefix, three significant digits: 200 ns."""
    for scale, unit in ((1.0, "s"), (1e-3, "ms"), (1e-6, "us"), (1e-9, "ns"), (1e-12, "ps")):
        if abs(seconds) >= scale:
            return "%.3g %s" % (seconds / scale, unit)
    return "%.3g s" % seconds


def _domain_of(system, fn, seen=()):
    """The clock domain a function fires in: its own for a clocked
    function; for an algebraic one the domains of its sources, joined
    with "+" when there are several (it fires when any source fires)."""
    if fn.kind == "clocked":
        return fn.domain
    found = set()
    for src in system.sources_of(fn):
        if src not in seen:
            found.add(_domain_of(system, src, seen + (fn,)))
    return "+".join(sorted(d for d in found if d)) or ""


def _system_dataset(obj):
    """``sl.make_traces(R1, ...)`` on a result whose stored signals lie in
    one clock domain (Specs 6.9.5); with several, the domain must be named
    with ``R1.dataset("CK1")``."""
    if not isinstance(obj, SystemResult):
        return None
    if len(obj.domains) == 1:
        return obj.dataset()
    print("Error: the stored signals lie in several clock domains (%s): "
          "give the domain, as in R1.dataset(\"%s\")"
          % (", ".join(obj.domains), next(iter(obj.domains))))
    return None


from SLiCAP.SLiCAPtraces import register_dataset_adapter as _register
_register(_system_dataset)
del _register


def _load_script(script):
    """Import the run script *script* ("osc", "osc.py" or a path, relative
    to the project root, the working directory) and return (module, path)."""
    import importlib.util
    import sys
    path = Path(script)
    if path.suffix != ".py":
        path = path.with_suffix(".py")
    if not path.is_file():
        raise FileNotFoundError("run script %s not found; the instruction file "
                                "creates it with sl.makeCircuit(\"sch/%s.system_sch\")"
                                % (path, path.stem))
    root = str(path.resolve().parent)
    if root not in sys.path:
        sys.path.insert(0, root)              # for the project's lib/<Name>.py
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise ValueError("%s is not a run script: it has no build()" % path)
    return module, path


def _execute(script, build, ticks=None, t_end=None, store=(), resume=False,
             jit="auto", results=None, stem=None, signals=None, params=None,
             step=None):
    """Build, store, run: the core of runSystem() and run_main().
    *signals* is the script's SIGNALS table, ``{name: "block.output"}``:
    a stored signal is named by the label of its wire or by the output
    itself; the traces carry the names asked for. *params* are the
    values of the run, *step* the step dictionary (Specs 10.4.7): one
    build and one run per step value. The script builds its filter
    designs itself (Specs 10.3.1); a ``designs`` argument that passed
    them from the instruction file was REPLACED (2026-11-18)."""
    import os
    stem = stem or Path(script).stem
    results = results if results is not None else ini.results_path
    os.makedirs(results, exist_ok=True)
    if isinstance(store, str):
        store = [store]
    if step is not None:
        name, values = _step_values(step)
        if resume:
            raise ValueError("a stepped run cannot be resumed")
        runs = [dict(params or {}, **{name: float(v)}) for v in values]
    else:
        name, values, runs = None, None, [dict(params or {})]
    import time
    t_start = time.time()
    done = []
    global _DESIGNS_OF_RUN
    _DESIGNS_OF_RUN = {}
    try:
        for i, run_params in enumerate(runs):
            done.append(_build_and_run(build, run_params, ticks, t_end, store, signals,
                                       resume, results, stem if step is None
                                       else "%s_s%d" % (stem, i), jit))
    finally:
        _DESIGNS_OF_RUN = None
    asked = done[0][2]
    done = [(s, r) for s, r, _a in done]
    (system, result), rest = done[0], done[1:]
    out = SystemResult(script, system, result, asked,
                       step=(name, values) if step is not None else None, runs=rest,
                       runtime=time.time() - t_start)
    # per signal the integer master ticks and the values (Specs 6.9.6); a
    # stepped run keeps one block per run
    arrays = {}
    for i in range(len(done)):
        tag = "" if step is None else ":run%d" % i
        for sig in out._ticks[i]:
            arrays[sig + tag + ":tick"] = out._ticks[i][sig]
            arrays[sig + tag + ":value"] = out._values[i][sig]
    if step is not None:
        arrays[name + ":step"] = np.asarray(values, dtype=float)
    np.savez(os.path.join(results, stem + ".signals.npz"), **arrays)
    return out


def _build_and_run(build, run_params, ticks, t_end, store, signals, resume,
                   results, run_stem, jit):
    """One run of a run instruction: build the system for *run_params*,
    register the stored signals, run. Returns ``(system, result,
    asked)``."""
    try:
        system = build(params=run_params)
    except TypeError as exc:
        if "params" not in str(exc):
            raise
        # a script from before the parameter round, or a hand-written
        # one: it runs without values, it cannot take any
        if run_params:
            raise TypeError("the run script takes no parameters: regenerate it "
                            "(the Create run script instruction, or "
                            "makeCircuit)") from exc
        system = build()
    if (ticks is None) == (t_end is None):
        raise ValueError("give the run length as ticks or as t_end")
    n_ticks = ticks
    by_time = None
    if n_ticks is None:
        n_ticks = int(round(float(t_end) / system.clocks.master_tick))
        if system.clock_source is not None:
            # the tick duration follows a signal: the run stops by time,
            # the tick count is a cap of twice the nominal (Specs 15.2)
            by_time = float(t_end)
            n_ticks = 2 * n_ticks + 1
    if int(n_ticks) < 1:
        raise ValueError("the run length is %d master ticks; a run needs at "
                         "least one (the master tick is %g s)"
                         % (int(n_ticks), system.clocks.master_tick))
    asked = _store(system, store, signals)
    start = load_state(system, results, run_stem) if resume else 0
    result = run(system, start + n_ticks, results=results, stem=run_stem,
                 start=start, jit=jit, t_end=by_time)
    result.traces = {asked.get(k, k): v for k, v in result.traces.items()}
    return system, result, asked


def _store(system, store, signals):
    """Register the stored signals of a run on *system*: ``{"block.output":
    name asked for}``."""
    signals = dict(signals or {})
    asked = {}
    for name in store:
        ref = signals.get(str(name), str(name))
        fn_name, _, out = ref.rpartition(".")
        if not fn_name or (signals and ref not in signals.values()):
            raise ValueError("unknown signal %r; the diagram has: %s"
                             % (name, ", ".join(signals) or "none"))
        fn = system[fn_name]
        if fn.kind == "algebraic" and not system.sources_of(fn):
            # a constant (Specs 6.1.3): a held value that never fires
            raise ValueError("%r is the output of %s, a held value that "
                             "never changes: there is nothing to record"
                             % (name, fn_name))
        system.store(fn_name, out)
        asked[ref] = str(name)
    return asked


def runSystem(script, ticks=None, t_end=None, store=(), resume=False,
              jit="auto", results=None, stem=None, params=None, step=None):
    """Run the system of a diagram: the instruction of the system dialect
    (SystemExtensionSpecs.md 6.3, 8.3).

    :param script: the run script the editor wrote into the project root,
                   by stem ("osc"), file name or path relative to the
                   project root
    :type script: str

    :param ticks: the run length in master ticks
    :type ticks: int

    :param t_end: the run length in seconds, instead of *ticks*
    :type t_end: float

    :param store: the signals to store by their names in the diagram:
                  the label of the wire, or ``"<block>.<output>"``, which
                  a script may always use (the script's SIGNALS table);
                  the result holds one trace per signal under the name
                  asked for
    :type store: list, str

    :param resume: True continues from the state file of the last run of
                   this script (Specs 8.3.1); the run length then counts
                   from there
    :type resume: bool

    :param jit: "auto" compiles the tick program when every function has
                kernels and numba is installed; False runs plain Python
    :type jit: str, bool

    :param results: the results folder, default ``ini.results_path``
    :type results: str

    :param stem: the file stem of the state, stop and signal files in the
                 results folder, default the script's stem
    :type stem: str

    :param params: values of parameters for this run, ``{"tau": 30}``, on
                   top of the sheet's parameter table (Specs 10.4.7)
    :type params: dict

    :param step: a parameter step as for an NGspice instruction,
                 ``{"param": "tau", "method": "lin", "start": 20, "stop":
                 30, "num": 5}`` (``lin``, ``log`` or ``list``): one run
                 per value, the traces labelled with the value
    :type step: dict

    :return: the report of the run, the clock domains and the stored
             signals (SystemExtensionSpecs.md 6.9)
    :rtype: SystemResult

    :Example:

    >>> R1 = sl.runSystem("osc", ticks=20000, store=["fdev", "out"])
    >>> R1.traces["fdev"]                      # against time
    >>> R1.trace("fdev", x="sample")           # against its sample index
    >>> T1 = sl.make_traces(R1.dataset("ref", x="tick"), ["fdev - out"])
    """
    module, path = _load_script(script)
    result = _execute(path, module.build, ticks, t_end, store, resume, jit,
                      results, stem, getattr(module, "SIGNALS", None),
                      params, step)
    print(result.report())
    return result


def run_main(build, argv, stem="system", signals=None):
    """The command-line run of a run script: ``python <stem>.py <ticks>
    <signal> ...`` from the project root, or ``--t-end <seconds>`` instead
    of the ticks; ``--python`` keeps the plain-Python mode, ``--resume``
    continues the last run. The signals go to results/<stem>.signals.npz
    and the state to results/<stem>.state.npz (Specs 8.3). The library
    files of the diagram load the project themselves (``load_designs``)."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="python %s.py" % stem,
        description="Run the system of the diagram and store signals.")
    parser.add_argument("ticks", nargs="?", type=int,
                        help="run length in master ticks")
    parser.add_argument("signals", nargs="*",
                        help="signals to store, <block>.<output>")
    parser.add_argument("--t-end", type=float, help="run length in seconds")
    parser.add_argument("--python", action="store_true",
                        help="plain Python, no compilation")
    parser.add_argument("--resume", action="store_true",
                        help="continue from the state file of the last run")
    parser.add_argument("--results", default=ini.results_path,
                        help="results folder (default: the project's)")
    parser.add_argument("--param", action="append", default=[], metavar="NAME=VALUE",
                        help="a parameter value for this run, repeatable")
    args = parser.parse_args(argv)
    params = {}
    for item in args.param:
        name, sep, value = item.partition("=")
        if not sep or not name.strip():
            parser.error("--param takes NAME=VALUE, not %r" % item)
        params[name.strip()] = value.strip()
    result = _execute(stem, build, args.ticks, args.t_end, args.signals,
                      args.resume, False if args.python else "auto",
                      args.results, stem, signals, params)
    print(result.report(head=stem))
    return result
