"""The engine: runs a ``System`` (SystemExtensionSpecs.md sections 4, 6, 8).

At the start of a run the engine builds the schedule from the instances
(sort, algebraic loop check, hyperperiod), shortens the run to the
smallest ``limit()`` of the functions (a recorded signal, Specs 6.2),
tells every function its number of firings by ``prepare()``, gives
every wire a value by one initialisation pass, generates the tick
program (Specs 4.7, Design 9.1) and, when possible, compiles it. It is scalar: one tick at a time,
one value per signal (a vectorised engine was REJECTED, Specs 4.6).

The tick program runs the master loop in blocks of ``stop_check``
ticks. Between blocks the driver here moves the sample buffers into the
stored signals, checks for a stop request (a file ``<stem>.stop`` in the
results folder, Specs 8.3.1) and continues. A pacing domain, the update
clock of a programmable filter (Specs 10.3.6), ends a block at each of
its ticks: the functions of that domain then fire in Python, by their
methods, before the next block starts. They read the signal values the
program holds between blocks, the values at the end of the previous
tick (one tick earlier than the rule of Specs 4.4 for a slow domain
inside the program; harmless for an update clock, which is slow by
definition, and recorded here, 2026-11-17). Their outputs are not
signals of the program: the ``System`` refuses such a wire. Before the
first block of every run, a continuation included, every pacing
function computes its outputs once, so that a filter has coefficients
from its first tick whatever the phase of the update clock (Specs
10.3.4). A function without kernels
ends a run by raising ``EndOfData`` from ``output()`` (Specs 6.2, 8.3).
On a stop, at the end, and on ``EndOfData`` the state of every clocked
function and the tick count go to ``<stem>.state.npz``; ``load_state()``
reads it back for a continuation.

The interpreting loop that this replaced, one ``output()`` call and one
attribute copy per wire per tick, was REPLACED by the generated program
(2026-11-16): it was half of a 14 us tick.
"""

import os
import re
import time

import numpy as np

from .program import Program
from .record import Record, DEPTH_LIMIT
from .schedule import Schedule

STOP_CHECK = 10_000


class EndOfData(Exception):
    """Raised by a source function when its data is exhausted."""


class RunResult:
    """What a run returns.

    ``traces``   ``{name: (ticks, y)}`` of the stored signals: the integer
                 master tick of every sample and its value (Specs 6.9.1)
    ``ticks``    master ticks executed in this run
    ``tick``     master tick count after the run (for a continuation)
    ``stopped``  True when a stop request ended the run
    ``ended``    True when the data of a source ended the run: by its
                 ``limit()`` before the start, or by ``EndOfData``
    ``state_file`` path of the written state file, or None
    ``seconds``  wall-clock time of the loop
    ``mode``     "jit" or "python"
    ``reason``   why the mode is "python", or ""
    ``compile_seconds`` time of the compilation, 0 in python mode
    ``program``  the source of the tick program
    """

    def __init__(self):
        self.time = None          # (ticks, seconds) of every tick of a driven clock
        self.end_time = 0.0       # physical time after the last tick
        self.traces = {}
        self.records = {}
        self.ticks = 0
        self.tick = 0
        self.stopped = False
        self.ended = False
        self.state_file = None
        self.seconds = 0.0
        self.mode = "python"
        self.reason = ""
        self.compile_seconds = 0.0
        self.program = ""

    def __repr__(self):
        return ("RunResult(ticks=%d, mode=%s, stopped=%s, ended=%s, traces=%s)"
                % (self.ticks, self.mode, self.stopped, self.ended,
                   sorted(self.traces)))


def _int_wrapper(dtype):
    """Function that wraps a value to integer *dtype* (Specs 5.3)."""
    info = np.iinfo(dtype)
    span = int(info.max) - int(info.min) + 1
    lo = int(info.min)

    def wrap(v):
        return (int(v) - lo) % span + lo
    return wrap


def _initialise(system, order):
    """The initialisation pass: every ``output()`` once, in order, and
    the outputs copied to the connected inputs, so that every wire has
    a value before the first tick (Specs 4.1)."""
    for fn in order:
        fn.output()
        for out in fn.outputs:
            dt_out = fn.dtype(out)
            if dt_out.kind in "iu":
                setattr(fn, out, _int_wrapper(dt_out)(getattr(fn, out)))
        for w in system.wires_from(fn):
            setattr(w.dst, w.inp, getattr(fn, w.out))


def _jit_choice(program, jit):
    """``(use_jit, reason)`` for the requested *jit* setting."""
    if program.methods:
        reason = ("function%s without kernels: %s"
                  % ("s" if len(program.methods) > 1 else "",
                     ", ".join(program.methods)))
        if jit is True:
            raise ValueError("jit=True, but " + reason)
        return False, reason
    if jit is False:
        return False, "jit=False"
    try:
        import numba  # noqa: F401
    except ImportError as exc:
        if jit is True:
            raise
        # the import error itself: numba may be installed, but too old for
        # the installed numpy (Anton's Windows test, 2026-11-20)
        return False, "numba cannot be imported: %s" % exc
    return True, ""


def run(system, ticks, results=None, stem="system", start=0,
        stop_check=STOP_CHECK, depth=DEPTH_LIMIT, state_file=True,
        jit="auto", t_end=None):
    """Run *system* for *ticks* master ticks, or until the physical time
    reaches *t_end* seconds when that comes first (Specs 15.2: with a
    driven reference clock the number of ticks of a run by time is not
    known in advance; *ticks* is then the cap).

    :param results: results folder for chunk files, the state file, the
                    stop request and the program source. None:
                    everything in memory, no files.
    :param stem: file stem in the results folder
    :param start: master tick to start from (a continuation after
                  ``load_state()``)
    :param stop_check: block length in ticks; the stop request is
                       checked between blocks
    :param depth: chunk size of the stored signals
    :param state_file: write the state file at the end (needs *results*)
    :param jit: "auto" compiles the tick program with numba when every
                function has kernels and numba is installed; True
                requires that; False runs plain Python
    :param t_end: stop when the time at the start of a tick reaches this
                  many seconds (None: by ticks only)
    :rtype: RunResult
    """
    sched = Schedule(system)
    hp = sched.hyperperiod
    result = RunResult()
    clocks = system.clocks

    # -- a recorded signal ends the run where its data ends
    for fn in sched.order + sched.pacing:
        lim = fn.limit()
        if lim is None:
            continue
        n = sched.ticks_until(fn, lim, start)
        if n is not None and start + n < ticks:
            ticks, result.ended = start + n, True
    if ticks <= start:
        result.tick = start
        return result
    for fn in sched.order + sched.pacing:
        fn.prepare(sched.firings(fn, ticks - start))

    if start == 0:
        _initialise(system, sched.order)

    program = Program(system, sched)
    result.program = program.source
    if results is not None:
        with open(os.path.join(results, stem + ".tick.py"), "w") as f:
            f.write(program.source)
    use_jit, result.reason = _jit_choice(program, jit)
    t0 = time.time()
    block = program.build(use_jit)
    result.mode = "jit" if use_jit else "python"

    # -- stored signals: records, block buffers and firing masks
    records, buffers, masks = {}, [], []
    n_block = max(1, int(stop_check))
    per_block = -(-n_block // hp) + 1          # hyperperiods per block, rounded up
    for fn, out in program.stored:
        name = "%s.%s" % (fn.name, out)
        count = sched.firings(fn, ticks - start)
        records[name] = Record(name, count, fn.dtype(out), results, depth)
        mask = np.array([fn in outs for outs, _ in sched.ticks])
        size = per_block * int(mask.sum())
        buffers.append(np.zeros(max(size, 1), dtype=fn.dtype(out)))
        masks.append(mask)
    cnt = np.zeros(max(len(buffers), 1), dtype=np.int64)
    held = program.held_values()
    paced = [(fn, out) for fn, out in system.stored if fn in sched.pacing]
    for fn, out in paced:
        name = "%s.%s" % (fn.name, out)
        records[name] = Record(name, sched.firings(fn, ticks - start),
                               fn.dtype(out), results, depth)

    # physical time (Specs 15.2): the clock array the program reads and
    # writes, [time at the start of the next tick, duration of the last
    # tick, nominal master tick, t_end]; with a driven clock the time of
    # every tick is recorded and the run may stop by time
    Ts = clocks.master_tick
    driven = system.clock_source is not None
    tm0 = float(system.start_time) if (driven and start) else start * Ts
    clk = np.array([tm0, Ts, Ts, np.inf if t_end is None else float(t_end)])
    tbuf = np.zeros(max(1, int(stop_check)))
    time_rec = (Record("time", ticks - start, np.float64, results, depth)
                if driven else None)

    def pace(t, fire):
        """The pacing functions at master tick *t*: inputs from the held
        signals, ``output()``; with *fire* also ``update()`` and the
        recording. Before the first block *fire* is False: the outputs
        exist, the domain has not fired."""
        for fn in sched.pacing:
            if fire and (fn.domain is None or not clocks.fires(fn.domain, t)):
                continue                   # "once": the pass before the first block
            program.feed(fn, held)
            fn.time = float(clk[0])
            fn.output()
            for out in fn.outputs:
                dt_out = fn.dtype(out)
                if dt_out.kind in "iu":
                    setattr(fn, out, _int_wrapper(dt_out)(getattr(fn, out)))
            if not fire:
                continue
            for out in fn.outputs:
                if (fn, out) in paced:
                    rec = records["%s.%s" % (fn.name, out)]
                    rec.extend(np.array([t], dtype=np.int64),
                               np.array([getattr(fn, out)], dtype=fn.dtype(out)))
            fn.update()

    pace(start, False)
    prog = np.array([start], dtype=np.int64)
    args = []
    k = 0
    for name, value in program.args:
        if re.match(r"r\d+_", name):
            args.append(buffers[k])
            k += 1
        else:
            args.append(value)
    args = tuple(args)

    def flush(t_from, t_to):
        base = np.arange(t_from, t_to)
        if time_rec is not None and t_to > t_from:
            time_rec.extend(base, tbuf[:t_to - t_from])
        for j, (fn, out) in enumerate(program.stored):
            n = int(cnt[j])
            xs = base[masks[j][base % hp]][:n]        # master ticks, exact
            rec = records["%s.%s" % (fn.name, out)]
            rec.extend(xs, buffers[j][:n])
            cnt[j] = 0

    stop_path = (os.path.join(results, stem + ".stop")
                 if results is not None else None)
    if use_jit:
        # a call with no ticks compiles the program for these types
        block(0, start, prog, clk, held, cnt, program.pattern_of_tick, tbuf, *args)
        result.compile_seconds = time.time() - t0
    t = start
    t_loop = time.time()
    next_pace = clocks.next_pacing(t)
    try:
        while t < ticks:
            if next_pace is not None and next_pace == t:
                pace(t, True)
                next_pace = clocks.next_pacing(t + 1)
            n = min(n_block, ticks - t)
            if next_pace is not None:
                n = min(n, next_pace - t)
            try:
                block(n, t, prog, clk, held, cnt, program.pattern_of_tick, tbuf, *args)
            finally:
                t_new = int(prog[0])
                flush(t, t_new)
                t = t_new
            if clk[0] + 0.5 * clk[1] >= clk[3]:   # t_end reached, by time (half a tick)
                result.ended = True
                break
            if stop_path is not None and os.path.exists(stop_path):
                os.remove(stop_path)
                result.stopped = True
                break
    except EndOfData:
        result.ended = True
    result.seconds = time.time() - t_loop
    result.ticks = t - start
    result.tick = t
    result.end_time = float(clk[0])
    system.start_time = result.end_time
    program.set_outputs(held)

    for name, rec in records.items():
        result.traces[name] = rec.values()
        result.records[name] = rec
    if time_rec is not None:
        result.time = time_rec.values()          # (ticks, seconds) of every tick
        result.records["time"] = time_rec
    if results is not None and state_file:
        result.state_file = save_state(system, t, results, stem, result.end_time)
    return result


def _state_path(results, stem):
    return os.path.join(results, stem + ".state.npz")


def save_state(system, tick, results, stem="system", end_time=None):
    """Write the state of every clocked function, the output values of
    every function, *tick* and the physical time *end_time* (Specs
    15.2, a continuation goes on from it) to ``<results>/<stem>.state.npz``.
    Returns the path.

    The outputs are part of the state of the run: a value of a slow
    domain is held until that domain fires again, across a continuation
    too, and a pacing function reads the held values before the first
    block. Without them a continuation restarted every held value at
    zero (found 2026-11-17 with the pacing test)."""
    arrays = {"__tick__": np.array([tick]),
              "__time__": np.array([float(end_time if end_time is not None
                                          else tick * system.clocks.master_tick)])}
    for fn in system.functions:
        if fn.kind == "clocked":
            arrays["state:" + fn.name] = np.asarray(fn.read_state())
        for out in fn.outputs:
            arrays["out:%s.%s" % (fn.name, out)] = np.asarray(getattr(fn, out))
    path = _state_path(results, stem)
    np.savez(path, **arrays)
    return path


def load_state(system, results, stem="system"):
    """Load the state file into *system*. Returns the tick to continue
    from, to be passed as ``start`` to :func:`run`."""
    path = _state_path(results, stem)
    with np.load(path) as f:
        tick = int(f["__tick__"][0])
        # the physical time to go on from (a state file of an older run
        # has none: the nominal clock)
        system.start_time = (float(f["__time__"][0]) if "__time__" in f
                             else tick * system.clocks.master_tick)
        for fn in system.functions:
            if fn.kind == "clocked":
                key = "state:" + fn.name
                if key not in f:
                    raise ValueError("state file %s has no state for %s"
                                     % (path, fn.name))
                fn.load_state(f[key])
            for out in fn.outputs:
                key = "out:%s.%s" % (fn.name, out)
                if key in f:                 # a state file of an older run has none
                    value = f[key][()]
                    setattr(fn, out, int(value) if fn.dtype(out).kind in "iu"
                            else float(value))
    return tick


def request_stop(results, stem="system"):
    """Ask a running engine to stop: creates ``<results>/<stem>.stop``."""
    path = os.path.join(results, stem + ".stop")
    with open(path, "w") as f:
        f.write("stop\n")
    return path
