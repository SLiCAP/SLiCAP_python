#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace objects and post-processing of numeric simulation results.

A trace holds the numeric data of ONE run - x values, y values - together
with the presentation attributes that belong to the data itself (label,
colour, marker, line style). Traces are placed on an ``axis`` and axes on a
``figure``; both live in :mod:`SLiCAP.SLiCAPplots`.

This module is deliberately **backend neutral**: it knows about named
numeric arrays, sweeps, runs, expressions and goal functions - never about
NGspice, raw files, sympy result types or matplotlib. Dependencies point one
way only::

    producers (NGspice, csv, LTspice, Cadence, SLiCAP results)
        -> SLiCAPtraces (data)
            -> SLiCAPplots (axis, figure, rendering)

See TRACES.md for the architecture and the phased plan.

``trace`` is re-exported by :mod:`SLiCAP.SLiCAPplots`, so both
``from SLiCAP.SLiCAPplots import trace`` and ``sl.trace`` keep working.
"""
import numpy as np
import sympy as sp

import SLiCAP.SLiCAPconfigure as ini

def _missing_as_nan(data):
    """
    Returns the array of trace data with None as NaN, which matplotlib draws
    as a gap. A None is a missing value, e.g. phaseMargin() of a step that
    did not converge (Anton, 2026-11-23). Other data is converted as by
    numpy.array().
    """
    arr = np.array(data)
    if arr.dtype == object and arr.ndim == 1:
        arr = np.array([np.nan if v is None else v for v in arr])
    return arr

class trace(object):
    """
    Trace prototype.

    Traces are plotted on axes, which are part of a figure.

    :param traceData: list with list array-like X and Y data of the trace.
    :type traceData: list

    :Example:

    >>> x_data = np.linspace(0, 2*np.pi, 50)
    >>> y_data = np.sin(x_data)
    >>> sin_trace = trace([x_data, y_data])
    """
    def __init__(self, traceData):
        self.xData = _missing_as_nan(traceData[0])
        """
        Array-like data for the x-axis of the trace. On a polar axes this is
        the angle in radians.
        """

        self.yData = _missing_as_nan(traceData[1])
        """
        Array-like data for the y-axis of the trace. On a polar axes this is
        the radius.
        """

        try:
            if len(self.xData) != len(self.yData):
                print('Error in plot data.')
        except:
            pass

        self.xName = 'x'
        """
        Heading (*str*) for the x column of a table. Defaults to 'x'.
        """

        self.yName = 'y'
        """
        Heading (*str*) for the y column of a table. Defaults to 'y'.
        """

        self.label = ''
        """
        Trace label (*str*) that will be displayed in legend box. Defaults to ''.
        """

        self.color = False
        """
        Trace color (*str*) in matplotlib format. Defaults to False.
        """

        self.marker = False
        """
        Marker type (*str*) in matplotlib format. Defaults to False.
        """

        self.markerColor = False
        """
        Marker color (*str*) in matplotlib format. Defaults to False.
        """

        self.markerFaceColor = 'none'
        """
        Marker face color (*str*) in matplotlib format. Defaults to 'none'.
        """

        self.markerSize = ini.marker_size
        """
        Marker size (*int*). Defaults to 7.
        """

        self.lineWidth = ini.line_width
        """
        Line width (*int*) in pixels. Defaults to 2.
        """

        self.lineType = ini.line_type
        """
        Line type (*str*) in matplotlib format. Defaults to '-'.
        """
        
        # NO xScaleFactor / yScaleFactor on a trace: scaling lives on the
        # AXIS (Anton, 2026-07-30, TRACES.md phase 7). Trace data is always
        # in base units, so the same trace object can sit on axes with
        # different scale factors; an attribute that rescaled yData would
        # silently change every other axis holding it. The two attributes
        # were REMOVED on 2026-08-02, after the new path had left them
        # unread - do not reintroduce them.

        self.xUnits = ""
        """
        Units of self.xData
        """
        
        self.yUnits = ""
        """
        Units of self.yData
        """

    def makeTable(self):
        """
        Returns a table with trace data in CSV format.

        :return: table: CSV table with column headings and x-data and y-data in
                 columns
        :rtype: str

        :Example:

        >>> x_data = np.linspace(0, 2*np.pi, 10)
        >>> y_data = np.sin(x_data)
        >>> sin_trace = trace([x_data, y_data])
        >>> sin_trace.yName = 'sin(x)'
        >>> print(sin_trace.makeTable())
        x,sin(x)
          0.000000000000e+00,   0.000000000000e+00
          6.981317007977e-01,   6.427876096865e-01
          1.396263401595e+00,   9.848077530122e-01
          2.094395102393e+00,   8.660254037844e-01
          2.792526803191e+00,   3.420201433257e-01
          3.490658503989e+00,  -3.420201433257e-01
          4.188790204786e+00,  -8.660254037844e-01
          4.886921905584e+00,  -9.848077530122e-01
          5.585053606382e+00,  -6.427876096865e-01
          6.283185307180e+00,  -2.449293598295e-16
        """
        table = str(self.xName) + ',' + str(self.yName) + '\n'
        for i in range(len(self.xData)):
            table += '%20.12e,%20.12e'%(self.xData[i], self.yData[i]) + '\n'
        return table


# ── post-processing: dataset -> traces ───────────────────────────────────────
# One implementation of the trace matrix (TRACES.md section 3), shared by
# every producer:
#
#   result   | stepping     | goal | one trace per          | x axis
#   ---------|--------------|------|------------------------|----------------
#   OP       | none         | -    | nothing (scalars)      | -
#   OP       | any          | -    | output variable        | step par / run
#   sweep    | none         | -    | output variable        | sweep variable
#   sweep    | any          | no   | output variable x run  | sweep variable
#   sweep    | any          | yes  | goal(output variable)  | step par / run
#
# The rule underneath it: a trace is ONE run, so it can only live along an
# abscissa that is not the run index. Without a sweep, or when a goal
# function collapses each run to a single number, the run index becomes the
# abscissa and the runs collapse into one trace.


class dataset(object):
    """
    Numeric arrays of one analysis, backend neutral.

    Producers (NGspice, measurement import, evaluated SLiCAP results) build
    a dataset; :func:`make_traces` turns it into traces. Stating the
    provenance explicitly replaces guessing it back from array lengths.

    :param x_name: Name of the sweep variable, None for an OP result.
    :type x_name: str, NoneType

    :param x_data: Sweep values, shape (n_sweep,); None for an OP result.
    :type x_data: numpy.ndarray, NoneType

    :param signals: ``{name: array}``; 1-D for an un-stepped sweep or a
                    stepped OP, 2-D (n_runs, n_sweep) for a stepped sweep.
    :type signals: dict

    :param step_params: ``{name: one value per run}``. Empty when the
                        analysis was not stepped; more than one entry for
                        multi-parameter (array) stepping.
    :type step_params: dict

    :param params: ``{name: value}`` of the circuit parameters as they were
                   SIMULATED - the circuit's definitions with the
                   per-instruction ``params=`` overrides applied. Numeric
                   (float): the producer resolves the symbolic definitions,
                   this layer only substitutes. A stepped parameter is not
                   here but in *step_params*, because it has a value per run.
    :type params: dict

    :param units: ``{signal name: units}`` for what only the PRODUCER can
                  know - SLiCAP's ``laplace`` is detector units over source
                  units, ``onoise`` is detUnits^2/Hz (
                  units are a property of the trace variable, and a name
                  convention cannot answer these). The abscissa is in here
                  under its own name. Signals not listed fall back to the
                  naming conventions of :func:`units_of`.
    :type units: dict

    :param gain_type: gain type of the analysis this came from ('gain',
                      'asymptotic', 'loopgain', 'servo', 'direct', 'vi'),
                      None for data that has none. It decides the automatic
                      trace COLOUR, SLiCAP's convention for the five
                      transfers of the asymptotic-gain model.
    :type gain_type: str, NoneType

    :param sampled: True when the signals are samples at discrete instants,
                    such as the time-domain response of a discrete filter:
                    :func:`make_traces` then draws them as points, unless a
                    trace specification gives a style (Anton, 2026-11-24).
    :type sampled: bool
    """
    def __init__(self, x_name=None, x_data=None, signals=None,
                 step_params=None, params=None, units=None, gain_type=None,
                 sampled=False):
        self.x_name      = x_name
        self.x_data      = None if x_data is None else np.asarray(x_data)
        self.signals     = dict(signals) if signals else {}
        self.step_params = dict(step_params) if step_params else {}
        self.params      = dict(params) if params else {}
        self.units       = dict(units) if units else {}
        self.gain_type   = gain_type
        self.sampled     = bool(sampled)

    @property
    def n_runs(self):
        """Number of runs: 1 when the analysis was not stepped."""
        for values in self.step_params.values():
            return len(np.atleast_1d(values))
        for arr in self.signals.values():
            a = np.asarray(arr)
            if a.ndim == 2:
                return a.shape[0]
        return 1

    @property
    def stepped(self):
        """True when the analysis has more than one run."""
        return bool(self.step_params) or self.n_runs > 1


def _plotted(arr):
    """Complex data plots as its MAGNITUDE; real data passes through.

    All that is left of the trace-type machinery, retired 2026-08-03 with
    the old plot dialog: everything else is written in the expression
    (dB_20, phase, real, imag, delay). A frequency-domain result without
    further instruction means its magnitude (Anton, 2026-07-31).
    """
    arr = np.asarray(arr)
    return np.abs(arr) if np.iscomplexobj(arr) else arr


def _goal_wrapper(function, params, x_data):
    """One goal function as an expression may call it: ``RMS(y)``.

    The registered goal functions take ``(x, y)`` and the parameterised ones
    are factories (:data:`SLiCAP.SLiCAPmath._GOAL_FUNCTIONS`). In an
    expression the abscissa is not written out - it is the run's own - so it
    is curried here and the parameters follow *y*::

        RMS(I_V1**2*R_a)          # goal_rms(x, y)
        Y_AT_X(V_out, 1e3)        # goal_y_at_x(1e3)(x, y)
        X_AT_NTH_Y(V_out, 0.5, 2) # goal_x_at_nth_y(0.5, 2)(x, y)

    Omitted parameters take the registry default.
    """
    labels   = [label for label, _default in params]
    defaults = [default for _label, default in params]

    def _wrapped(y, *args, **kwargs):
        if len(args) > len(labels):
            raise ValueError(
                "goal takes the signal and {0} parameter(s) ({1})".format(
                    len(labels), ", ".join(labels) or "none"))
        values = list(defaults)
        for i, value in enumerate(args):
            values[i] = value
        for label, value in kwargs.items():
            if label not in labels:
                raise ValueError(
                    "unknown goal parameter '{0}'; accepted: {1}".format(
                        label, ", ".join(labels) or "none"))
            values[labels.index(label)] = value
        goal = function(*values) if labels else function
        return goal(x_data, np.asarray(y))

    return _wrapped


#: Functions a trace expression may use besides the whole of numpy, as
#: ``(name, what it does)``. They replace the trace TYPES: everything a trace
#: is, is written in its expression (Anton, 2026-07-31), so there is one
#: mechanism instead of two. ``delay`` needs the run's abscissa and gets it
#: curried, like a goal function.
_TRACE_FUNCTIONS = [
    ("dB_20",      "20*log10(|y|) - amplitude ratio in dB"),
    ("dB_10",      "10*log10(|y|) - power ratio in dB"),
    ("dB",         "dB(y) = dB_20, dB(y, power=True) = dB_10"),
    ("phase",      "phase in degrees, UNWRAPPED"),
    ("delay",      "group delay, -dphi/domega"),
    ("mag",        "magnitude (SLiCAPmath)"),
    ("abs",        "magnitude (numpy)"),
    ("real",       "real part"),
    ("imag",       "imaginary part"),
    ("angle",      "phase in radians (numpy)"),
    ("sqrt",       "square root"),
    ("exp",        "exponential"),
    ("log",        "natural logarithm"),
    ("log10",      "logarithm base 10"),
    ("groupDelay", "group delay from (frequency, real, imag)"),
]


def function_names():
    """
    The functions a trace expression may use, as ``{name: description}``.

    The one place the list is defined: the GUI's "Insert Function" menu and
    the manual read it from here, so a function added to
    :data:`_TRACE_FUNCTIONS` appears in both without further work - the same
    arrangement as :func:`goal_names`.

    :return: ``{name: description}``
    :rtype: dict
    """
    return {name: description for name, description in _TRACE_FUNCTIONS}


def goal_names():
    """
    The goal functions as an expression writes them: the registry's display
    name in upper case with the spaces as underscores ('y at x' ->
    ``Y_AT_X``), with the parameters that follow the signal.

    Upper case for two reasons: it marks a token as REDUCING one run to one
    number, and ``max`` / ``min`` are already taken by the builtins the
    expression layer needs.  A goal function added to
    a goal function appears in expressions - and in
    the GUI menu, which reads its names from here - without further work.

    :return: ``{name: [(parameter label, default), …]}``
    :rtype: dict
    """
    try:
        from SLiCAP.SLiCAPmath import _GOAL_FUNCTIONS
    except Exception:
        return {}
    return {str(display).upper().replace(' ', '_'): list(params)
            for display, _function, params in _GOAL_FUNCTIONS}


def _goal_namespace(x_data):
    """The goal functions ready to be called in an expression, with the
    run's abscissa curried (:func:`goal_names` fixes the spelling)."""
    namespace = {}
    try:
        from SLiCAP.SLiCAPmath import _GOAL_FUNCTIONS
    except Exception:
        return namespace
    for display, function, params in _GOAL_FUNCTIONS:
        name = str(display).upper().replace(' ', '_')
        namespace[name] = _goal_wrapper(function, params, x_data)
    return namespace


class _sl_alias(object):
    """``sl.`` inside an expression: the same names, prefixed.

    An expression is evaluated in the factory's namespace, not in the
    instruction file's, so ``sl`` does not exist there by itself. Both
    ``RMS(V_out)`` and ``sl.RMS(V_out)`` are accepted, so an expression can
    be written the way the rest of the instruction file reads.
    """
    def __init__(self, namespace):
        self._namespace = namespace

    def __getattr__(self, name):
        try:
            return self._namespace[name]
        except KeyError:
            raise AttributeError(
                "'{0}' is not available in a trace expression".format(name))


class _Source(object):
    """One source of a dataset made by ``makeDataset()`` in an expression:
    ``FLT1.H_fs`` is the attribute ``H_fs`` of the name ``FLT1``, so the
    expression reads like the Design data (TRACES.md phase 9)."""

    def __repr__(self):
        return "<source: %s>" % ", ".join(sorted(vars(self)))


def _is_name(text):
    """True for a Python identifier or a dotted chain of them, the names of
    a dataset made by ``makeDataset()``: ``V_out``, ``AC1.V_out``."""
    parts = str(text).split(".")
    return all(part.isidentifier() for part in parts)


def _bind(namespace, name, value):
    """Bind *name* in *namespace*; a dotted name as the attribute of its
    source (``_Source``)."""
    parts = str(name).split(".")
    if len(parts) == 1:
        namespace[parts[0]] = value
        return
    holder = namespace.get(parts[0])
    if not isinstance(holder, _Source):
        holder = namespace[parts[0]] = _Source()
    for part in parts[1:-1]:
        inner = getattr(holder, part, None)
        if not isinstance(inner, _Source):
            inner = _Source()
            setattr(holder, part, inner)
        holder = inner
    setattr(holder, parts[-1], value)


def _run_slice(values, run, n_runs):
    """The data of ONE run: a row of a stepped sweep, one value of a stepped
    OP, or the whole array when the analysis has a single run."""
    array = np.asarray(values)
    if array.ndim == 2:
        return array[run] if run < array.shape[0] else array[-1]
    if n_runs > 1 and array.ndim == 1 and len(array) == n_runs:
        return array[run]          # stepped OP: one value per run
    return array


def _expression_namespace(data, run=0):
    """Names an expression may use for ONE run - or for the WHOLE result when
    *run* is None: the signals, the sweep variable, the circuit and step
    parameters, the goal functions and the whole of numpy.

    ``run=None`` binds every quantity in FULL, so a goal function reduces the
    run dimension as well: ``MEAN(-V_1*I_v2)`` over a stepped OP is the mean
    over its runs, one value (Anton, 2026-08-03 - everything is specified on
    array dimensions).

    Signal names that are not valid Python identifiers - ``v(out)``,
    ``@q1[gm]`` - cannot appear in an expression; assign them a Python name
    with ``variables={"V_out": "v(out)"}`` and use that name.
    """
    namespace = {}
    for key in dir(np):
        if not key.startswith('_'):
            try:
                namespace[key] = getattr(np, key)
            except Exception:
                pass
    namespace['np'] = np
    try:
        # The SLiCAPmath family - ONE implementation each, shared with
        # plotSweep (Anton, 2026-08-01: "otherwise we get multiple
        # implementations of the same functions"). They are polymorphic
        # (numpy array or Laplace expression); here they always see arrays.
        from SLiCAP.SLiCAPmath import groupDelay, mag, dB, phase, delay
        namespace['groupDelay'] = groupDelay
        namespace['mag'] = mag
        namespace['dB'] = dB
        namespace['phase'] = phase
        # the abscissa of THIS run is curried, as for a goal function, so an
        # expression does not have to name it
        namespace['delay'] = lambda y: delay(np.asarray(y), data.x_data)
        # spelled-out aliases (Anton asked for dB_20 / dB_10): one line each,
        # no second implementation
        namespace['dB_20'] = lambda y: dB(np.asarray(y))
        namespace['dB_10'] = lambda y: dB(np.asarray(y), power=True)
    except Exception:
        pass
    namespace.update(_goal_namespace(data.x_data))
    # The run number, 1-based: the implicit abscissa of an array-stepped
    # result, which must also be writable as x="run" (phase 6b).
    namespace['run'] = (run + 1 if run is not None
                        else np.arange(1, data.n_runs + 1))
    # Circuit parameters as simulated, then the step parameters: a stepped
    # parameter has a value PER RUN and overrides the circuit definition,
    # which is the order in which the simulator applied them.
    for name, value in data.params.items():
        if _is_name(name):
            _bind(namespace, name, value)
    n_runs = data.n_runs
    for name, values in data.step_params.items():
        if _is_name(name):
            column = np.atleast_1d(values)
            _bind(namespace, name, column if run is None
                  else column[run if run < len(column) else -1])
    # The abscissa, SLICED FOR THIS RUN like every other quantity (and
    # winning over any numpy name of the same spelling). It is a whole array
    # only when it is swept WITHIN a run - frequency, time. For a stepped OP
    # the abscissa is the run number or the step parameter, one value per
    # run, so x="run" and x="V_S" must give THIS run's value; binding the
    # whole column made them "an array per run" against a y of one value per
    # run, and array stepping could not be plotted at all (Anton,
    # 2026-08-03: "the run number must be an x variable").
    if data.x_name and data.x_name.isidentifier() and data.x_data is not None:
        namespace[data.x_name] = (data.x_data if run is None
                                  else _run_slice(data.x_data, run, n_runs))
    for name, values in data.signals.items():
        if _is_name(name):
            _bind(namespace, name, np.asarray(values) if run is None
                  else _run_slice(values, run, n_runs))
    namespace['sl'] = _sl_alias(namespace)
    return namespace


# Builtins an expression may use. The expression comes from the user's own
# instruction file, so this is not a security boundary; the point is a clean
# error for a mistyped signal name instead of a stray builtin resolving.
_SAFE_BUILTINS = {name: __builtins__[name] if isinstance(__builtins__, dict)
                  else getattr(__builtins__, name)
                  for name in ('abs', 'all', 'any', 'bool', 'complex',
                               'divmod', 'enumerate', 'float', 'int', 'len',
                               'list', 'max', 'min', 'pow', 'range', 'round',
                               'sorted', 'sum', 'tuple', 'zip')}


def _report_expression_error(expression, data, err, name_error):
    """One message per expression, whatever the number of runs."""
    print("Error: cannot evaluate '{0}': {1}".format(expression, err))
    if not name_error:
        return
    # Say what CAN be used and what exists but has no name: the data is
    # there either way, and a signal is referenced by its name, never by
    # its raw simulator spelling (Anton, 2026-07-29 - raw-name arithmetic
    # belongs in names=, which NGspice evaluates itself).
    named   = sorted(n for n in data.signals if _is_name(n))
    unnamed = sorted(n for n in data.signals if not _is_name(n))
    print("  usable in expressions   : " + (', '.join(named) or 'none'))
    parameters = sorted(set(list(data.params) + list(data.step_params)),
                        key=str)
    if parameters:
        print("  circuit parameters      : "
              + ', '.join(str(p) for p in parameters))
    print("  goal functions          : "
          + ', '.join(sorted(_goal_namespace(data.x_data))))
    if unnamed:
        print("  available as data only  : " + ', '.join(unnamed))
        print("  A simulator vector is not a Python name. Map it here, in "
              "post-processing, and use the Python name in the expression: "
              "make_traces(RESULT, specs, variables={\"V_out\": \"v(out)\"}).")


def _evaluate_runs(expression, data):
    """Evaluate *expression* once PER RUN; ``(kind, results)``, or
    ``(None, None)`` on failure.

    Per run, not over the whole 2-D array, because a goal function inside the
    expression - ``RMS(I_V1**2*R_a)`` - reduces ONE run to one number
    (TRACES.md section 3.1). Each run therefore sees 1-D signals, the value
    its step parameters had, and the goal functions with its abscissa
    curried.

    What the expression RETURNED says what it is, so select / transform /
    reduce need no separate declaration:

    - ``'reduced'``: a number per run - the runs become the abscissa and the
      whole set collapses into ONE trace;
    - ``'runs'``:    an array per run - one trace per run along the sweep;
    - ``'pairs'``:   an (x, y) pair per run - the expression brought its own
      abscissa (the FFT case, where time becomes frequency).
    """
    results = []
    for run in range(data.n_runs):
        namespace = _expression_namespace(data, run)
        try:
            value = eval(expression, {"__builtins__": _SAFE_BUILTINS},
                         namespace)
        except NameError as err:
            _report_expression_error(expression, data, err, True)
            return None, None
        except Exception as err:
            _report_expression_error(expression, data, err, False)
            return None, None
        results.append(value)
    if all(isinstance(v, (tuple, list)) and len(v) == 2 for v in results):
        return 'pairs', results
    if all(np.asarray(v).ndim == 0 for v in results):
        return 'reduced', results
    return 'runs', results


def _evaluate_all(expression, data):
    """Evaluate *expression* over the WHOLE result - every run at once.

    What a measurement needs: the answer's DIMENSION says whether it is one,
    so a goal function may reduce the run dimension itself instead of the
    caller having to select a run first.
    """
    namespace = _expression_namespace(data, run=None)
    try:
        return eval(expression, {"__builtins__": _SAFE_BUILTINS}, namespace)
    except NameError as err:
        _report_expression_error(expression, data, err, True)
        return None
    except Exception as err:
        _report_expression_error(expression, data, err, False)
        return None


def _step_label(name, step_name, step_values, i):
    """Default label of the i-th run of *name* (TRACES.md section 3).

    Single-parameter stepping puts the parameter and its value in the label.
    Multi-parameter (array) stepping cannot: the label carries the RUN
    NUMBER and the values per run go into :func:`run_table`, for the figure
    caption or the running text.
    """
    if step_name is not None and step_values is not None and i < len(step_values):
        return f"{name}  {step_name}={step_values[i]:.4g}"
    return f"{name}  run={i + 1}"


def run_table(data, columns=False):
    """
    The step parameters per run: what a multi-parameter stepped label cannot
    carry.

    With more than one step parameter a trace label can only hold the run
    number, so the values belong in a table - in the figure caption or in
    the running text. It comes from the same data set as the traces, so the
    table and the labels cannot drift apart.

    :param data: data set or analysis result.
    :type data: SLiCAPtraces.dataset, SLiCAPinstruction.instruction

    :param columns: False (default) returns one dict per run, with 'run'
                    first. True returns ``(names, columns)``: the parameter
                    names and a list of values per parameter - the argument
                    pair taken by the ``stepArray()`` method of the RST,
                    LaTeX and TXT formatters.
    :type columns: bool

    :return: list of dicts, or (names, columns); empty when not stepped.
    :rtype: list, tuple

    :Example:

    >>> OP4 = sl.op("amp", step={"method": "array", "params": ["V_S", "TEMP"],
    ...                          "values": [[9, 0], [12, 25], [15, 50]]})
    >>> sl.run_table(OP4)
    [{'run': 1, 'V_S': 9.0, 'TEMP': 0.0}, ...]
    >>> names, cols = sl.run_table(OP4, columns=True)
    >>> rst.stepArray(names, cols, caption="Run parameters").save("runs")
    """
    data = as_dataset(data)
    if data is None or not data.step_params:
        return ([], []) if columns else []
    names = list(data.step_params)
    values = [list(np.atleast_1d(data.step_params[name])) for name in names]
    if columns:
        return names, values
    n_runs = max(len(column) for column in values)
    table = []
    for i in range(n_runs):
        row = {"run": i + 1}
        for name, column in zip(names, values):
            if i < len(column):
                row[name] = column[i]
        table.append(row)
    return table


# Producers register a converter here, so make_traces() accepts a result
# object directly without this module knowing anything about the producer:
# the dependency keeps pointing producers -> traces (TRACES.md section 2).
_DATASET_ADAPTERS = []


def register_dataset_adapter(function):
    """Register ``function(obj) -> dataset or None``, used by
    :func:`as_dataset` to accept a producer's result object."""
    _DATASET_ADAPTERS.append(function)


def as_dataset(obj):
    """A :class:`dataset` for *obj*, or None when nothing can convert it.

    Accepts a dataset unchanged and asks the registered producer adapters
    (NGspice results, ...) for anything else.
    """
    if isinstance(obj, dataset):
        return obj
    for function in _DATASET_ADAPTERS:
        try:
            converted = function(obj)
        except Exception:
            converted = None
        if converted is not None:
            return converted
    return None


def _no_dataset(function, obj):
    """The refusal of *function* when :func:`as_dataset` gives nothing for
    *obj*. It names the cause it can see. ``None`` is what a producer
    returns after its own error, such as ``sweepData()`` on a filter. The
    one text for every case blamed an un-stepped operating point for that
    too, and was REPLACED (Anton, 2026-11-25)."""
    dataType = getattr(obj, "dataType", None)
    if obj is None:
        why = ("got no data: the instruction that makes it failed (see the "
               "error above)")
    elif dataType == "op":
        why = ("got an un-stepped operating point: it holds scalars and "
               "yields no traces (print them instead)")
    elif dataType in _DATASET_FUNCTIONS or dataType in _FILTER_TYPES:
        why = ("got a symbolic result ({0}): make its data with "
               "sl.makeDataset()".format(dataType))
    else:
        why = ("needs a data set or an analysis result; got {0}"
               .format(dataType or type(obj).__name__))
    return "Error: {0}() {1}.".format(function, why)


def axis_label(name, scale="", units=""):
    """
    The text of an axis label: ``name [scale units]``, with the units set as
    text through :func:`SLiCAP.SLiCAPmath.units2text` (Ohm as the ohm sign,
    the prefix u as the micro sign, exponents as superscripts). The ONE
    builder of axis labels (2026-09-12): plotSweep, plotPZ, plot and the GUI
    axes dialog all call it, so a script and the GUI write the same label.

    :param name: quantity, may contain Matplotlib mathtext ('$V_{out}$').
    :type name: str
    :param scale: scale factor letter ('', 'k', 'u', ...).
    :type scale: str
    :param units: units in SLiCAP spelling ('V', 'V^2/Hz', 'rad/s', 'Ohm').
    :type units: str
    :return: the label, '' when name, scale and units are all empty.
    :rtype: str
    """
    from SLiCAP.SLiCAPmath import units2text
    name = str(name or "").strip()
    bracket = units2text(str(scale or "") + str(units or ""))
    if bracket:
        return (name + " [" + bracket + "]").strip()
    return name


# Units follow the NAME where a convention says so, and stay empty where it
# does not (Anton, 2026-07-30): 'frequency' is Hz, but abs(V_out)**2/R_a is W
# and no naming convention can know that. SLiCAP's own conventions live here;
# a producer registers its own spellings, keeping the dependency pointing
# producers -> traces (TRACES.md section 2).
_UNITS_HINTS = []


def register_units_hint(function):
    """Register ``function(name, result) -> units str or None``, asked by
    :func:`units_of` for the producer's own signal spellings."""
    _UNITS_HINTS.append(function)


def units_of(name, result=None, known=None):
    """
    The units the NAME *name* implies, or '' when no convention says so.

    Used to pre-fill the units field of an axis. It is a
    SUGGESTION: the user states the units, and this saves the typing where a
    name carries its meaning::

        frequency -> Hz (rad/s)    V_out, v(out) -> V     time, t -> s
        I_V1, i(v1)  -> A          abs(V_out)**2/R_a -> ''   (an expression)

    The empty answer is the important one - a guess in a units field is worse
    than an empty field.

    :param name: signal, abscissa or expression name.
    :type name: str

    :param result: the analysis result the name came from, when available.
                   A producer hint may need it - the units of SLiCAP's
                   ``onoise`` follow the DETECTOR, not the name.
    :type result: SLiCAPinstruction.instruction, NoneType

    :param known: ``{name: units}`` the producer supplied (a dataset's
                  ``units``). Consulted FIRST: what the producer knows beats
                  any convention.
    :type known: dict, NoneType

    :return: units, or '' when nothing knows them.
    :rtype: str
    """
    text = str(name).strip()
    if not text:
        return ""
    if known and text in known:
        return known[text] or ""
    if text in ("frequency", "f"):
        return "Hz" if ini.hz else "rad/s"
    if text == "t":
        # 't' is SLiCAP's abscissa symbol. NOT 'time': that is the NAME OF
        # THE RESULT ATTRIBUTE holding the time-domain response, which is in
        # detector units, not seconds. NGspice's abscissa IS called time and
        # is answered by the producer, which knows (dataset.units).
        return "s"
    if _is_name(text):
        # the convention of the name itself, also for AC1.V_out
        tail = text.rsplit(".", 1)[-1]
        if tail.startswith("V_"):
            return "V"
        if tail.startswith("I_"):
            return "A"
    for hint in _UNITS_HINTS:
        try:
            units = hint(text, result)
        except Exception:
            units = None
        if units:
            return units
    return _wrapped_units(text, result, known)


# What a wrapping FUNCTION does to the units. dB(V_out) is dB whatever
# V_out is; abs() and the goal functions keep the units of what they reduce;
# everything else - a sum, a product, an integral - changes them in a way no
# convention can know, so it gets nothing.
_FUNCTION_UNITS = {"dB": "dB", "dB_10": "dB", "dB_20": "dB",
                   "delay": "s", "groupDelay": "s"}
_KEEPS_UNITS = {"abs", "real", "imag", "RMS", "MEAN", "MAX", "MIN", "Y_AT_X"}


def _wrapped_units(text, result=None, known=None):
    """Units of an expression that is ONE function call around a name."""
    import ast
    try:
        node = ast.parse(text.strip(), mode="eval").body
    except SyntaxError:
        return ""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return ""
    name = node.func.id
    if name in _FUNCTION_UNITS:
        return _FUNCTION_UNITS[name]
    if name == "phase":
        return "deg" if ini.hz else "rad"
    if name in _KEEPS_UNITS and node.args:
        return units_of(ast.unparse(node.args[0]), result, known)
    return ""


class measurement(object):
    """
    One measured value: a number taken from a simulation result, with its
    units.

    A measurement is an **n x 1** object - n variables at ONE condition -
    where a trace is 1 x m: one variable across m conditions (Anton,
    A trace is therefore a row of measurements of the same
    variable, and this class is one entry of such a row.

    It carries only what DISPLAY needs. Where the number came from - which
    result, which expression, which step - is the call that produced it, in
    the instruction file, and that call is re-executed on every run: SLiCAP
    auto-updates, so a copy of the provenance on the object could only go
    stale.

    :param value: the measured number.
    :type value: float

    :param units: units of the value, assigned by the user ('V', 'A',
                  'V^2/Hz', 'dB'); SLiCAP does not derive them.
    :type units: str

    :Example:

    >>> V_n = sl.measure(NOISE1, "RMS_NOISE(onoise_spectrum)", units="V")
    >>> print(V_n)
    1.71812e-06 V
    """
    def __init__(self, value, units=""):
        self.value = float(np.real(value))
        """The measured number (*float*)."""
        self.units = str(units or "")
        """Units of :attr:`value` (*str*), assigned by the user."""

    def __float__(self):
        return self.value

    def __repr__(self):
        return "{0:.6g}{1}".format(self.value,
                                   " " + self.units if self.units else "")

    __str__ = __repr__


#: no run was selected: the expression is evaluated over every run at once
_WHOLE_RESULT = object()


def _select_run(data, step, run):
    """Index of the run a measurement is taken from, or None with a message.

    *step* selects by VALUE (``{"C_c": 18e-12}``, or the bare value when the
    analysis stepped one parameter), *run* by number, 1-based. An un-stepped
    result has one run and needs neither.
    """
    n_runs = data.n_runs
    if run is not None:
        index = int(run) - 1
        if 0 <= index < n_runs:
            return index
        print("Error: run {0} does not exist; the result has {1} "
              "run(s).".format(run, n_runs))
        return None
    if step is not None:
        if not isinstance(step, dict):
            names = list(data.step_params)
            if len(names) != 1:
                print("Error: step= needs a parameter name for a result "
                      "stepped over {0}.".format(", ".join(names) or "nothing"))
                return None
            step = {names[0]: step}
        candidates = set(range(n_runs))
        for name, wanted in step.items():
            values = np.atleast_1d(data.step_params.get(name, []))
            if not len(values):
                print("Error: '{0}' is not a step parameter of this result; "
                      "it stepped {1}.".format(
                          name, ", ".join(data.step_params) or "nothing"))
                return None
            wanted = float(wanted)
            matching = {i for i, v in enumerate(values)
                        if np.isclose(float(v), wanted, rtol=1e-9, atol=0.0)}
            if not matching:
                print("Error: {0} = {1:.6g} is not among the step values "
                      "({2}).".format(name, wanted,
                                      ", ".join("%.6g" % float(v)
                                                for v in values)))
                return None
            candidates &= matching
        if not candidates:
            print("Error: no single run matches step={0}.".format(step))
            return None
        return sorted(candidates)[0]
    if n_runs > 1:
        # NOT an error: whether this is a measurement is decided by the
        # DIMENSION of what the expression returns, not by the number of
        # runs - MEAN(...) over a stepped OP gives one value (Anton,
        #  measure() evaluates the whole result and looks.
        return _WHOLE_RESULT
    return 0


def measure(data, expression, step=None, run=None, variables=None,
            units=""):
    """
    Measures ONE value from a simulation result - or several, given a dict.

    A measurement is n x 1: n variables at one condition. The expression is the SAME language the traces use - the goal
    functions reduce a run to one number, the circuit parameters and the
    assigned Python names are in scope - and *step* / *run* say WHICH
    condition, which is data selection rather than mathematics.

    :param data: the result, or a :class:`dataset`.
    :type data: SLiCAPtraces.dataset, SLiCAPinstruction.instruction

    :param expression: one expression, or ``{name: expression}`` for several
                       values of the same result (an operating point).
    :type expression: str, dict

    :param step: the condition, by step VALUE: ``{"C_c": 18e-12}``, or the
                 bare value when one parameter was stepped.
    :type step: dict, float, NoneType

    :param run: the condition, by run number (1-based) - for array stepping,
                where there is no single value to name.
    :type run: int, NoneType

    :param variables: ``{python_name: simulator_vector}``, as in
                      :func:`make_traces`.
    :type variables: dict, NoneType

    :param units: units of the value, or ``{name: units}`` for a dict of
                  expressions. User-assigned; SLiCAP does not derive them.
    :type units: str, dict

    :return: a :class:`measurement`, or ``{name: measurement}``; None (or an
             empty dict) when the expression cannot be measured.
    :rtype: SLiCAPtraces.measurement, dict, NoneType

    :Example:

    >>> V_n  = sl.measure(NOISE1, "RMS_NOISE(onoise_spectrum)", units="V")
    >>> A_0  = sl.measure(AC1, "Y_AT_X(dB_20(V_out), 1e3)",
    ...                   step={"C_c": 18e-12},
    ...                   variables={"V_out": "v(out)"},
    ...                   units="dB")
    >>> OP   = sl.measure(OP1, {"I_c": "i(v2)", "V_ce": "v(c) - v(e)"},
    ...                   units={"I_c": "A", "V_ce": "V"})
    """
    if isinstance(expression, dict):
        unit_map = units if isinstance(units, dict) else {}
        out = {}
        for name, one in expression.items():
            value = measure(data, one, step=step, run=run,
                            variables=variables,
                            units=unit_map.get(name, "" if unit_map else units))
            if value is not None:
                out[str(name)] = value
        return out

    source, data = data, as_dataset(data)
    if data is None:
        print(_no_dataset("measure", source))
        return None
    data = _rename_signals(data, variables)
    index = _select_run(data, step, run)
    if index is None:
        return None
    if index is _WHOLE_RESULT:
        # Several runs and no selection: reduce them. One value is a
        # measurement, several are a trace - the array dimension answers it.
        value = _evaluate_all(str(expression), data)
        if value is None:
            return None
        array = np.asarray(value)
        if array.size != 1:
            print("Error: '{0}' gives {1} values over the {2} runs of this "
                  "result - that is a trace, not a measurement. Reduce it "
                  "with a goal function, e.g. MEAN({0}), or take one run "
                  "with step={{...}} or run=n.".format(expression,
                                                       array.size,
                                                       data.n_runs))
            return None
        return measurement(array.reshape(-1)[0], units)
    kind, results = _evaluate_runs(str(expression), data)
    if kind is None:
        return None
    if kind != 'reduced':
        print("Error: '{0}' gives an array, not one value - that is a trace. "
              "Reduce it with a goal function, e.g. "
              "RMS({0}).".format(expression))
        return None
    return measurement(results[index], units)


def _rename_signals(data, variables):
    """A view of *data* whose signals carry the PYTHON names of *names*.

    ``{python_name: simulator_vector}``. The dataset itself is not touched -
    the same result may be used again with a different mapping - and a vector
    that is not listed keeps its own name.
    """
    if data is None or not variables:
        return data
    signals = dict(data.signals)
    for python_name, vector in variables.items():
        vector = str(vector)
        if vector in signals:
            signals[str(python_name)] = signals.pop(vector)
        else:
            print("Warning: '{0}' is not a signal of this result; "
                  "'{1}' is not defined. Available: {2}".format(
                      vector, python_name,
                      ", ".join(sorted(data.signals)) or "none"))
    # EVERYTHING the producer knew comes along: renaming a signal must not
    # cost the units or the gain type. It did - and since the GUI always
    # emits variables={...}, every trace lost its gain colour and its units
    # the moment it was named ( "colors still wrong").
    units = dict(data.units)
    for python_name, vector in (variables or {}).items():
        if str(vector) in units:
            units[str(python_name)] = units.pop(str(vector))
    return dataset(x_name=data.x_name, x_data=data.x_data, signals=signals,
                   step_params=data.step_params, params=data.params,
                   units=units, gain_type=data.gain_type,
                   sampled=getattr(data, "sampled", False))


def _unique_key(traces, label):
    """A free key for *label* in *traces*.

    The label is the trace's NAME and the dictionary's key at once, so two
    traces with the same label - the magnitude and the phase of one transfer,
    both called "gain" - would have made the second replace the first
    (Anton,  The label stays what it is; only the KEY is made
    unique, so both traces exist and both legends read "gain".
    """
    if label not in traces:
        return label
    n = 2
    while "{0} ({1})".format(label, n) in traces:
        n += 1
    return "{0} ({1})".format(label, n)


def _merge(traces, new_traces):
    """Add *new_traces* to *traces*, keeping every one of them.

    ``dict.update`` would drop a trace whose label is already there - which
    is exactly what a Bode pair does, both halves being called "gain".
    """
    for label, trc in new_traces.items():
        traces[_unique_key(traces, label)] = trc
    return traces


def _new_trace(x_values, y_values, label, attrs, x_name=None, y_name=None):
    """One trace with its label, its column headings and its presentation
    attributes.

    Label and colour belong to the DATA and are settled here, where the
    trace is created (TRACES.md decisions 3 and 4), so no caller needs to
    mutate a trace afterwards. ``xName`` / ``yName`` are the headings
    :meth:`trace.makeTable` writes into an exported table, which used to be
    the useless 'x' and 'y'; they carry what the axes ACTUALLY hold.
    """
    new = trace([x_values, y_values])
    new.label = label
    if x_name:
        new.xName = x_name
    if y_name:
        new.yName = y_name
    for key, value in attrs.items():
        setattr(new, key, value)
    return new


def _assign_colors(traces, data=None):
    """Give every trace whose spec named no colour the next default colour.

    The colour is settled HERE, when the trace is made, and NOT when an axis
    is drawn (Anton, 2026-08-02; TRACES.md section 6.1, detail 1, option b).
    A stepped result therefore keeps run *n* in the same colour in EVERY axis
    it appears in, so the magnitude and the phase of a Bode pair agree by
    construction instead of by accident, and placing a trace on a second axis
    cannot recolour it.

    The index is the trace's position in the set being built, which for one
    expression over n runs IS the run number.

    :param traces: the trace dictionary in creation order.
    :type traces: dict

    :return: the same dictionary.
    :rtype: dict
    """
    gain_type = getattr(data, "gain_type", None)
    single_run = getattr(data, "n_runs", 1) == 1
    for i, trc in enumerate(traces.values()):
        if not trc.color:
            trc.color = automatic_color(i, gain_type, single_run)
    return traces


def _assign_units(traces, data):
    """Give every trace the units of what it PLOTS, unless its spec said so.

    Units are a property of the trace variable, not of the axis that happens
    to show it (Anton, 2026-08-02): the same trace reads as amps on any axis,
    while the SCALE FACTOR - a display choice - stays on the axis. The axis
    then takes its units FROM the traces instead of guessing them.

    ``xName`` / ``yName`` hold what the trace plots, so the same rules that
    answer for a signal answer here: what the producer supplied first
    (``dataset.units``), then the naming conventions, then nothing.
    """
    for trc in traces.values():
        if not trc.yUnits:
            trc.yUnits = units_of(trc.yName, known=data.units)
        if not trc.xUnits:
            trc.xUnits = units_of(trc.xName, known=data.units)
    return traces


def _gain_colors():
    """``{gain type: colour}`` from the ini - SLiCAP's own convention for
    the five gain types of the asymptotic-gain model."""
    return {"ideal":      ini.gain_colors_ideal,
            "gain":       ini.gain_colors_gain,
            "asymptotic": ini.gain_colors_asymptotic,
            "loopgain":   ini.gain_colors_loopgain,
            "direct":     ini.gain_colors_direct,
            "servo":      ini.gain_colors_servo,
            "vi":         ini.gain_colors_vi}


def automatic_color(index, gain_type=None, single_run=True):
    """
    The colour a trace gets when its specification names none.

    SLiCAP colours the gain types of the asymptotic-gain model by CONVENTION
    - asymptotic red, gain blue, loopgain black, servo magenta, direct green
    (``ini.gain_colors_*``) - which is what makes a set of five transfers
    readable in one plot. ``plotSweep`` has always done this; the new path
    did not, so five results each holding one trace all came out red (Anton,
    

    The colour identifies the RESULT, so EVERY trace built from a named gain
    type gets it - a magnitude and a phase of the same transfer are the same
    thing seen twice, and they land on different axes (
    with two expressions per set the colours went red/blue again). Only the
    RUNS of a stepped result take the cycle instead: those must be told apart
    from each other on one axis.

    :param index: position of the trace in its set.
    :type index: int

    :param gain_type: gain type of the result it came from, None for data
                      that has none (an NGspice run, a csv import).
    :type gain_type: str, NoneType

    :param single_run: False when the result was stepped - then the runs are
                       distinguished by the colour cycle instead.
    :type single_run: bool

    :return: matplotlib colour.
    :rtype: str
    """
    if single_run and gain_type and gain_type != "vi":
        colour = _gain_colors().get(str(gain_type))
        if colour:
            return colour
    return default_color(index)


def default_color(index):
    """
    The *index*-th colour of the default cycle (``ini.default_colors``).

    ONE definition of the cycle: :func:`make_traces` colours a trace with it
    and a GUI previews the same colour, so the swatch cannot disagree with
    the plot.

    :param index: position of the trace in its set.
    :type index: int

    :return: matplotlib colour.
    :rtype: str
    """
    colors = ini.default_colors or ["r"]
    return str(colors[int(index) % len(colors)]).strip()


def reduces(expression, signals=None):
    """
    True when *expression* collapses a run to one number, judged from its
    STRUCTURE: every reference to run data sits inside a goal-function call.

    Used to pre-fill the x axis in the GUI: as soon as y
    reduces, the natural abscissa is the step parameter instead of the sweep
    variable. Searching the text for a goal name cannot answer this -
    ``V_out/MAX(V_out)`` mentions a goal but stays a curve against the sweep
    variable, because the bare ``V_out`` is evaluated per sweep point.

    The real behaviour of :func:`make_traces` follows the SHAPE the expression
    returns, which is authoritative; this is the static approximation of it.

    :param expression: trace expression in numpy syntax.
    :type expression: str

    :param signals: names that hold run data. Circuit parameters and
                    constants are scalars and do not stop a reduction, so
                    ``RMS(V_out)/R_a`` reduces. Defaults to None: every name
                    is taken to be run data, the conservative reading.
    :type signals: list, set, NoneType

    :return: True when the expression reduces a run to a single value.
    :rtype: bool

    :Example:

    >>> names = ["V_out"]
    >>> sl.reduces("RMS(V_out)", names), sl.reduces("RMS(V_out)/R_a", names)
    (True, True)
    >>> sl.reduces("V_out/MAX(V_out)", names), sl.reduces("V_out*2", names)
    (False, False)
    """
    import ast
    goals = set(goal_names())
    names = None if signals is None else set(signals)
    try:
        body = ast.parse(str(expression), mode='eval').body
    except SyntaxError:
        return False

    def _goal_call(node):
        """The goal function this call node calls, or None."""
        function = node.func
        if isinstance(function, ast.Attribute):     # sl.RMS(...)
            return function.attr if function.attr in goals else None
        return (function.id if isinstance(function, ast.Name)
                and function.id in goals else None)

    def _dotted(node):
        """``AC1.V_out`` for an attribute chain on a name, else None."""
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        return ".".join([node.id] + parts[::-1])

    def _is_data(node):
        """A name holding run data - what a goal has to swallow. A dotted
        name of makeDataset(), AC1.V_out, is ONE name."""
        if isinstance(node, ast.Attribute):
            name = _dotted(node)
            return name is not None and (names is None or name in names)
        if not isinstance(node, ast.Name):
            return False
        return True if names is None else node.id in names

    def _all_inside_goals(node):
        if isinstance(node, ast.Call) and _goal_call(node):
            return True                             # the goal swallows its arg
        if _is_data(node):
            return False
        return all(_all_inside_goals(child)
                   for child in ast.iter_child_nodes(node))

    # a bare number, parameter or constant is not a reduction of a run
    if not any(isinstance(n, ast.Call) and _goal_call(n)
               for n in ast.walk(body)):
        return False
    return _all_inside_goals(body)


def _default_abscissa_name(data, kind, step_name):
    """Name of the automatic abscissa: the sweep variable, the step parameter
    or the run number (TRACES.md section 3)."""
    if kind == 'reduced':
        return step_name if step_name is not None else 'run'
    return data.x_name if data.x_name else 'index'


def _trace_label(label, y_text, x_text, data, step_name, step_values, run):
    """Default label: ``y vs x``, which is what a plot shows (Anton,
    2026-07-30), with the step parameter appended per run when there is one."""
    base = label or "{0} vs {1}".format(y_text, x_text)
    return (_step_label(base, step_name, step_values, run) if data.stepped
            else base)


def _x_axis_traces(x_expr, y_expr, data, label, attrs,
                   step_name, step_values):
    """Traces with an EXPLICIT abscissa expression (phase 6b).

    Both sides are evaluated per run and must AGREE in shape: two arrays give
    a parametric curve per run (``V_GS`` against ``I_D``, real against imag),
    two reduced values give one trace whose points are the runs - a
    design-space curve, e.g. bandwidth against dissipated power over a step.
    A mismatch is a mistake and is reported, never broadcast.

    Data order is kept: sorting by x would destroy a Nyquist plot or a
    hysteresis loop.
    """
    kind_y, results_y = _evaluate_runs(y_expr, data)
    if kind_y is None:
        return {}
    kind_x, results_x = _evaluate_runs(x_expr, data)
    if kind_x is None:
        return {}
    for kind, side, expression in ((kind_y, 'y', y_expr),
                                   (kind_x, 'x', x_expr)):
        if kind == 'pairs':
            print("Error: '{0}' returns its own abscissa, which conflicts "
                  "with the {1} expression given for this trace: use one or "
                  "the other.".format(expression, 'x' if side == 'y' else 'y'))
            return {}
    if kind_x != kind_y:
        shape = {'reduced': 'one value per run', 'runs': 'an array per run'}
        print("Error: x and y of this trace do not match: '{0}' gives {1} "
              "and '{2}' gives {3}.".format(x_expr, shape[kind_x],
                                            y_expr, shape[kind_y]))
        return {}

    traces = {}
    if kind_y == 'reduced':
        if not data.stepped:
            # both axes reduced with a single run is a MEASUREMENT, an object
            # SLiCAP has not defined yet (TRACES.md section 1)
            print("Note: '{0}' and '{1}' both reduce the run to a single "
                  "value; that is a measurement, not a trace.".format(y_expr,
                                                                      x_expr))
            return {}
        x_values = np.array([_plotted(v) for v in results_x])
        y_values = np.array([_plotted(v) for v in results_y])
        new = _new_trace(x_values, y_values,
                         label or "{0} vs {1}".format(y_expr, x_expr), attrs,
                         x_name=x_expr, y_name=y_expr)
        traces[_unique_key(traces, new.label)] = new
        return traces

    for run, (x_run, y_run) in enumerate(zip(results_x, results_y)):
        x_values = _plotted(x_run)
        y_values = _plotted(y_run)
        if len(np.atleast_1d(x_values)) != len(np.atleast_1d(y_values)):
            print("Error: x and y of this trace differ in length: '{0}' gives "
                  "{1} points and '{2}' gives {3}.".format(
                      x_expr, len(np.atleast_1d(x_values)),
                      y_expr, len(np.atleast_1d(y_values))))
            return {}
        text = _trace_label(label, y_expr, x_expr, data, step_name,
                            step_values, run)
        new = _new_trace(x_values, y_values, text, attrs,
                         x_name=x_expr, y_name=y_expr)
        traces[_unique_key(traces, new.label)] = new
    return traces


def _expression_traces(expression, data, label, attrs,
                       step_name, step_values):
    """Traces of ONE expression over the named signals and parameters, on the
    automatic abscissa.

    The expression is evaluated per run and its RESULT shape decides the
    outcome (:func:`_evaluate_runs`). The default label is ``y vs x`` with the
    automatic abscissa named, so a goal function written inside the expression
    - ``RMS(I_V1**2*R_a)`` - reads as the mathematics does.
    """
    kind, results = _evaluate_runs(expression, data)
    if kind is None:
        return {}
    y_text = expression
    x_data = data.x_data
    # a pair supplies its own abscissa, so only the automatic cases have a
    # name to put in the label
    x_text = ('' if kind == 'pairs'
              else _default_abscissa_name(data, kind, step_name))
    base = label or (y_text if kind == 'pairs'
                     else "{0} vs {1}".format(y_text, x_text))

    traces = {}
    if kind == 'reduced':
        if not data.stepped:
            # one run reduced to one number is a scalar, and a scalar is not
            # a trace (TRACES.md section 3): it belongs in a table
            print("Note: '{0}' reduces the run to a single value ({1:.6g}); "
                  "a scalar is not a trace - use it in a table or a "
                  "parameter definition.".format(expression,
                                                 float(np.real(results[0]))))
            return {}
        reduced = np.array([_plotted(value) for value in results])
        abscissa = (step_values if step_values is not None
                    else np.arange(len(reduced)))
        new = _new_trace(abscissa, reduced, base, attrs,
                         x_name=x_text, y_name=y_text)
        traces[_unique_key(traces, new.label)] = new
        return traces

    for run, values in enumerate(results):
        if kind == 'pairs':
            own_x  = np.asarray(values[0])
            y_data = _plotted(values[1])
        else:
            own_x  = (x_data if x_data is not None
                      else np.arange(len(np.atleast_1d(values))))
            y_data = _plotted(values)
        text = (_step_label(base, step_name, step_values, run)
                if data.stepped else base)
        new = _new_trace(own_x, y_data, text, attrs,
                         x_name=x_text, y_name=y_text)
        traces[_unique_key(traces, new.label)] = new
    return traces


def make_traces(data, specs=None, variables=None):
    """
    Builds a dictionary of :class:`trace` objects from a :class:`dataset`.

    :param data: the numeric arrays and their step provenance - a
                 :class:`dataset`, or an analysis result a registered
                 producer can convert (an NGspice op/dc/ac/tran/noise
                 result).
    :type data: SLiCAPtraces.dataset, SLiCAPinstruction.instruction

    :param specs: list of trace specifications; a plain string is shorthand
                  for ``{"y": name}``. Defaults to None: one spec per signal.

                  - ``y``:     signal name, or an EXPRESSION over the named
                    signals, the circuit parameters and the goal functions
                    (see below).
                  - ``x``:     expression for the ABSCISSA, evaluated exactly
                    like ``y``. Defaults to None: the sweep variable, or the
                    step parameter / run number when ``y`` reduces each run to
                    one value. Both sides must agree in shape - two arrays give
                    a parametric curve per run, two reduced values give one
                    trace whose points are the runs (a design-space curve).
                    Data order is kept, never sorted.
                  - ``label``: label of the trace; defaults to None, the
                    label of the table in the manual, or the
                    expression itself.
                  - other keys: attributes set on the trace object
                    (``color``, ``marker``, ``lineWidth``, …)
    :type specs: list, NoneType

    :param variables: ``{python_name: simulator_vector}`` - what the signals are
                  CALLED in expressions. The simulator writes its own vector
                  names (``v(out)``, ``@q1[gm]``, ``x1.mid``,
                  ``onoise_q1_rb``), which are not Python identifiers; this
                  mapping is chosen AFTER the run, when the vectors are known
                  (it used to sit in the analysis call,
                  where it could only guess). A vector not listed keeps its
                  own name and stays usable when that name happens to be an
                  identifier.
    :type variables: dict, NoneType

    :return: ``{label: trace}``
    :rtype: dict

    **Expressions are evaluated by numpy, on numbers.** This is the numeric
    post-processing layer: the arrays are ``numpy.ndarray`` and nothing is
    symbolic, so an expression may use the whole numpy namespace - every
    function (``sqrt``, ``exp``, ``fft.rfft``, ``convolve``, …) and every
    constant (``pi``, ``e``, ``inf``, ``nan``). ``pi`` is therefore the float
    3.141592…, not the sympy symbol of a SLiCAP expression, and units are not
    tracked. Use ``sl.doLaplace`` and the SLiCAP math functions where symbolic
    results are wanted.

    An expression is written over IDENTIFIER names: the signals named with
    ``variables=``, the sweep variable, the circuit parameters as simulated, the step parameters (their value for the run), and the goal
    functions in upper case (``RMS``, ``MEAN``, ``Y_AT_X``, …; ``sl.RMS`` is
    accepted as well). Raw simulator names - ``v(out)``, ``@q1[gm]`` - are not
    identifiers: assign them a Python name with ``variables=``.

    The names are bound in this order: numpy, goal functions, circuit
    parameters, step parameters, sweep variable, signals. The DATA therefore
    wins on a clash - a signal or parameter of your own called ``pi`` shadows
    the numpy constant, so a circuit's names can never be captured by a numpy
    spelling.

    An expression is evaluated PER RUN and its result decides the outcome:
    an array gives one trace per run, a number per run gives one trace
    against the step parameter, and an ``(x, y)`` pair brings its own
    abscissa.

    The default label is ``y vs x``, which is what a plot shows, with the step
    parameter appended per run when there is one. ``trace.xName`` and
    ``trace.yName`` - the column headings of :meth:`trace.makeTable` - carry
    the two expressions, so an exported table is readable.

    :Example:

    >>> T = sl.make_traces(AC1, [{"y": "V_outp - V_outn", "color": "r"},
    ...                          {"y": "RMS(I_V1**2*R_a)"},
    ...                          {"y": "Y_AT_X(V_outp, 1e3)"}])
    >>> P = sl.make_traces(AC1, [{"x": "real(V_out)", "y": "imag(V_out)"}])
    >>> D = sl.make_traces(AC1, [{"x": "RMS(I_V1)**2*R_a", "y": "MAX(V_out)",
    ...                           "label": "gain vs dissipation"}])
    """
    source, data = data, as_dataset(data)
    if data is None:
        print(_no_dataset("make_traces", source))
        return {}
    data = _rename_signals(data, variables)
    if specs is None:
        specs = list(data.signals.keys())
    # A label can name the step parameter only when there is exactly one;
    # with several, the run number identifies the run and run_table() holds
    # the values.
    step_names  = list(data.step_params)
    step_name   = step_names[0] if len(step_names) == 1 else None
    step_values = (np.asarray(data.step_params[step_name])
                   if step_name is not None else None)
    x_data = data.x_data
    traces = {}
    for spec in specs:
        if isinstance(spec, str):
            spec = {"y": spec}
        name = spec["y"]
        x_expr = spec.get("x")
        label = spec.get("label")
        attrs = {k: v for k, v in spec.items()
                 if k not in ("x", "y", "label")}
        if getattr(data, "sampled", False):
            # samples at discrete instants are drawn as points, unless the
            # spec gives a style (Anton, 2026-11-24)
            attrs.setdefault("marker", "o")
            attrs.setdefault("lineType", "None")
        # An EXPLICIT abscissa expression takes its own route: both sides are
        # evaluated and must agree in shape (phase 6b). The
        # automatic abscissa keeps the proven path below, which the harness
        # covers, so a parametric trace cannot disturb an ordinary one.
        if x_expr:
            _merge(traces, _x_axis_traces(x_expr, name, data, label, attrs,
                                          step_name, step_values))
            continue
        # a signal name is taken as such; anything else is an expression
        # over the named signals, the circuit parameters and the goal
        # functions (differential mode, power, weighting, FFT, reduction)
        if name not in data.signals:
            _merge(traces, _expression_traces(name, data, label, attrs,
                                              step_name, step_values))
            continue
        values = np.asarray(data.signals[name])
        kind = ('runs' if (values.ndim > 1 or x_data is not None)
                else 'reduced')
        x_text = _default_abscissa_name(data, kind, step_name)
        if values.ndim == 1:
            # un-stepped sweep, or a stepped OP: one trace, the abscissa is
            # the sweep variable or the step parameter
            abscissa = x_data if x_data is not None else step_values
            if abscissa is None:
                abscissa = np.arange(len(values))
            new = _new_trace(abscissa, _plotted(values),
                             label or "{0} vs {1}".format(name, x_text), attrs,
                             x_name=x_text, y_name=name)
            traces[_unique_key(traces, new.label)] = new
            continue

        # stepped sweep: 2-D (n_runs, n_sweep)
        n_runs = values.shape[0]
        for i in range(n_runs):
            # the run label follows the same rule whether or not the trace
            # was named: the step parameter and its value for single-
            # parameter stepping, the run number only when there is no
            # single value to show (array stepping)
            lbl = _step_label(label or "{0} vs {1}".format(name, x_text),
                              step_name, step_values, i)
            new = _new_trace(x_data, _plotted(values[i]),
                             lbl, attrs, x_name=x_text, y_name=name)
            traces[_unique_key(traces, lbl)] = new
    return _assign_units(_assign_colors(traces, data), data)

# ---------------------------------------------------------------------------
# Building datasets: sweepData() and makeDataset()
#
# Building a dataset is the entry of the traces layer (section 2 of
# TRACES.md: producers -> traces -> plots). Both functions were in
# SLiCAPplots and MOVED here (Anton, 2026-11-25): SLiCAPplots only draws.
# ---------------------------------------------------------------------------

_PLOT_DATA_TYPES = ['laplace', 'numer', 'denom', 'noise', 'step', 'impulse',
                    'time', 'params', None]
_FREQ_TYPES      = ['laplace', 'numer', 'denom', 'noise']
_TIME_TYPES      = ['time', 'impulse', 'step']


def _sweep_limit(value, parDefs):
    """A sweep limit as a float: a number in SLiCAP notation, or the name
    of a parameter with a numeric value in *parDefs*. Raises ValueError
    naming the parameter otherwise."""
    from SLiCAP.SLiCAPmath import _checkNumber
    number = _checkNumber(value, parDefs)
    if number is None:
        raise ValueError("'{0}' is not a number and not a numeric parameter "
                         "of the sweep: give it a value with params="
                         "sl.selectPars(...) or in the pardefs of the "
                         "instruction.".format(value))
    return float(number)


def _sweep_par_defs(results, params):
    """The parameters a sweep limit is resolved from: those of the result
    (the pardefs of its instruction) with the ``params`` of the sweep on
    top, as the ``params`` of an NGspice analysis (Anton, 2026-11-09)."""
    from SLiCAP.SLiCAPmath import _checkExpression
    par_defs = dict(getattr(results, "parDefs", None) or {})
    for key, value in (params or {}).items():
        par_defs[sp.Symbol(str(key))] = _checkExpression(str(value))
    return par_defs


#: the dataType of a filter (createIIR, createFIR); makeFilter() gives it
#: H_s, H_z and Ts
_FILTER_TYPES = ("iir", "fir")


def _sweep_axis(start, stop, num, sweepMethod):
    """The sweep values: *num* points from *start* to *stop*, "log" or
    "lin"; None with an error for a logarithmic sweep over a limit <= 0."""
    if sweepMethod == 'log':
        if start <= 0 or stop <= 0:
            print("Error: a logarithmic sweep needs positive limits.")
            return None
        return np.geomspace(start, stop, num)
    return np.linspace(start, stop, num)


def _laplace_data(expression, x):
    """An expression in s as a complex array over the frequencies *x*: the
    numeric rational fast path, else s replaced and evaluated."""
    from SLiCAP.SLiCAPmath import _freq_response, _makeNumData
    response = _freq_response(expression, x)
    if response is not None:
        return response                             # complex, fast path
    data = sp.N(expression)
    if ini.hz:
        data = data.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = data.xreplace({ini.laplace: sp.I*ini.frequency})
    return np.asarray(_makeNumData(data, ini.frequency, x, normalize=False),
                      dtype=complex)


#: the attributes of a SLiCAP result that are swept, per dataType
_SLICAP_SIGNALS = {'laplace': ['laplace'], 'numer': ['numer'],
                   'denom': ['denom'], 'time': ['time'],
                   'impulse': ['impulse'], 'step': ['stepResp'],
                   'noise': ['onoise', 'inoise']}


def _slicap_runs(results, name):
    """The attribute *name* of a SLiCAP result as a list of expressions,
    one per run."""
    value = getattr(results, name, None)
    if value is None or (isinstance(value, list) and not value):
        return []
    return value if isinstance(value, list) else [value]


def _slicap_noise_terms(results):
    """``{onoise_<source>: [expression per run], inoise_<source>: ...}``:
    the noise contributions per source of a SLiCAP noise result."""
    out = {}
    for attribute, prefix in (("onoiseTerms", "onoise"),
                              ("inoiseTerms", "inoise")):
        for source, expression in (getattr(results, attribute, None) or {}).items():
            name = "{0}_{1}".format(prefix, str(source))
            name = "".join(c if (c.isalnum() or c == "_") else "_" for c in name)
            out[name] = expression if isinstance(expression, list) else [expression]
    return out


def _slicap_step_params(results):
    """The step parameters of a stepped SLiCAP result: one value per run."""
    step_params = {}
    if getattr(results, "step", False):
        if getattr(results, "stepVar", None) is not None:
            step_params[str(results.stepVar)] = np.asarray(
                results.stepList, dtype=float)
        elif getattr(results, "stepVars", None):
            rows = np.asarray(results.stepArray, dtype=float)
            for j, name in enumerate([str(v) for v in results.stepVars]):
                if j < rows.shape[0]:
                    step_params[name] = rows[j]
    return step_params


def _slicap_params(results):
    """The circuit parameters of a SLiCAP result with a numeric value."""
    from SLiCAP.SLiCAPmath import fullSubs
    params = {}
    par_defs = getattr(getattr(results, "circuit", None), "parDefs", None) or {}
    for symbol, value in par_defs.items():
        try:
            params[str(symbol)] = float(sp.N(fullSubs(value, par_defs)))
        except (TypeError, ValueError):
            continue
    return params


def sweepData(results, sweepStart, sweepStop, sweepNum, sweepMethod='auto',
              sweepVar='auto', params=None):
    """
    Evaluates a SLiCAP result over a sweep and returns the numbers as a
    :class:`SLiCAPtraces.dataset`, ready for
    :func:`SLiCAPtraces.make_traces` and :func:`SLiCAPtraces.measure`.

    A SLiCAP result is SYMBOLIC - `laplace` is an expression in *s* - so it
    has no sweep of its own; NGspice hands over numbers, SLiCAP hands over a
    formula. This function supplies the missing sweep, which is why the traces
    dialog asks for start / stop / points 

    It lives in SLiCAPtraces: building a dataset is the entry of the traces
    layer (producers -> traces -> plots). It was in SLiCAPplots and MOVED
    here (Anton, 2026-11-25).

    The signals are named after what they are (``SWEEP_SIGNAL_NAMES``):

    - *H_s*, *N_s*, *D_s*: the transfer (``laplace``), its numerator
      (``numer``) and its denominator (``denom``), COMPLEX arrays with s
      replaced by 2*pi*j*f (``ini.hz``) or j*omega. ``mag(...)``,
      ``dB(mag(...))``, ``phase(...)`` and ``delay(...)`` give the
      magnitude, the magnitude in dB, the phase and the group delay;
    - *noise*: ``onoise`` and ``inoise`` (V^2/Hz), plus one signal per noise
      source from ``onoiseTerms`` / ``inoiseTerms``, named
      ``onoise_<source>`` - the symbolic counterpart of NGspice's
      ``onoise_r1``;
    - *time*, *impulse*, *step*: real arrays over *t*.

    A stepped result carries one expression per run, so its signals become
    2-D (n_runs, n_sweep) and ``step_params`` holds the step values - exactly
    like a stepped NGspice sweep. The circuit's numeric parameter definitions
    become ``dataset.params``.

    A filter made with ``makeFilter()`` and several results together are
    combined by :func:`makeDataset`. Two forms of this function built during
    6.5.0 were REMOVED (Anton, 2026-11-25): a plain expression with the
    fixed name *H_s*, and a filter with the columns *H_s*, *H_z*,
    *impulse*, *step*.

    Trace data stays in BASE UNITS (Hz, s, V): scaling belongs to the axis,
    never to the trace, so this function has no
    counterpart of ``plotSweep``'s *sweepScale*.

    :param results: result of one SLiCAP instruction.
    :type results: SLiCAPinstruction.instruction

    :param sweepStart: start of the sweep; SLiCAP notation ('10', '1M'), or
                       the name of a parameter, ``"f_min"``, resolved from
                       the parameter definitions of the result (the
                       ``pardefs`` of the instruction) with *params* on top.
                       A sweep limit then follows the specs like a component
                       value does (Anton, 2026-11-09).
    :type sweepStart: str, float, int

    :param sweepStop: end of the sweep; as *sweepStart*.
    :type sweepStop: str, float, int

    :param sweepNum: number of points.
    :type sweepNum: str, int

    :param sweepMethod: 'lin' or 'log'; 'auto' takes 'log' for a frequency
                        sweep and 'lin' for a time sweep.
    :type sweepMethod: str

    :param sweepVar: name of the swept parameter for ``dataType='params'``;
                     'auto' for the frequency or time sweep of the other data
                     types.
    :type sweepVar: str

    :param params: parameter definitions for the sweep limits, on top of
                   those of the result: the dictionary ``selectPars()``
                   returns, ``params=sl.selectPars(cir, specs,
                   specs=["t_settle"])``, for a specification the
                   instruction itself did not select.
    :type params: dict, NoneType

    :return: the evaluated data, or None when the result cannot be swept.
    :rtype: SLiCAPtraces.dataset, NoneType

    :Example:

    >>> D   = sl.sweepData(LAPLACE1, 10, "1M", 200)
    >>> TR  = sl.make_traces(D, [{"y": "dB(mag(H_s))"}])
    >>> A_0 = sl.measure(D, "Y_AT_X(dB(mag(H_s)), 1e3)", units="dB")
    """
    from SLiCAP.SLiCAPmath import _makeNumData
    from SLiCAP.SLiCAPlex import _scale_float

    if isinstance(results, list):
        print("Error: sweepData() takes ONE result; combining results is what "
              "an axis does (TRACES.md phase 7).")
        return None
    dataType = getattr(results, "dataType", None)
    if dataType in _FILTER_TYPES or isinstance(results, sp.Basic):
        # the two removed forms: the refusal names the call that replaces
        # them, not only the data type (Anton, 2026-11-25)
        print("Error: sweepData() sweeps one SLiCAP result. A filter or an "
              "expression goes through makeDataset(), for example "
              "sl.makeDataset({\"FLT1\": FLT1}, x=\"frequency\", "
              "start=\"10\", stop=\"1M\", num=200).")
        return None
    if dataType not in _PLOT_DATA_TYPES or dataType is None:
        print("Error: cannot sweep dataType '{0}'.".format(dataType))
        return None
    try:
        par_defs = _sweep_par_defs(results, params)
        start = _sweep_limit(sweepStart, par_defs)
        stop  = _sweep_limit(sweepStop, par_defs)
        num   = int(_scale_float(sweepNum))
    except (ValueError, TypeError) as exc:
        print("Error: the sweep needs numbers in SLiCAP notation ('10', "
              "'1M') or parameters of the result; got {0}, {1}, {2}. {3}"
              .format(sweepStart, sweepStop, sweepNum, exc))
        return None
    if sweepMethod == 'auto':
        sweepMethod = 'lin' if dataType in _TIME_TYPES else 'log'
    x = _sweep_axis(start, stop, num, sweepMethod)
    if x is None:
        return None

    # the abscissa of a time-domain result is 't', SLiCAP's own symbol - NOT
    # 'time', which is the name of the RESULT ATTRIBUTE (result.time) and
    # would collide with it in an expression
    x_name = 't' if dataType in _TIME_TYPES else 'frequency'
    x_var  = sp.Symbol('t') if dataType in _TIME_TYPES else ini.frequency

    def _numeric(expression):
        """One expression -> one array over the sweep."""
        if dataType in _FREQ_TYPES and dataType != 'noise':
            return _laplace_data(expression, x)
        return np.asarray(_makeNumData(sp.N(expression), x_var, x,
                                       normalize=False), dtype=float)

    signals = {}
    for name in _SLICAP_SIGNALS.get(dataType, []):
        runs = _slicap_runs(results, name)
        if not runs:
            continue
        arrays = [_numeric(expression) for expression in runs]
        signals[SWEEP_SIGNAL_NAMES.get(name, name)] = (
            arrays[0] if len(arrays) == 1 else np.array(arrays))
    if dataType == 'noise':
        # per-source contributions: the symbolic counterpart of NGspice's
        # onoise_r1 (Anton, 2026-08-01)
        for name, runs in _slicap_noise_terms(results).items():
            arrays = [_numeric(one) for one in runs]
            signals[name] = arrays[0] if len(arrays) == 1 else np.array(arrays)
    if not signals:
        print("Error: result '{0}' holds no data to sweep.".format(dataType))
        return None

    step_params = _slicap_step_params(results)
    params = _slicap_params(results)
    # What only the RESULT knows: a transfer is detector units over source
    # units, noise is squared detector units per Hz. The naming conventions
    # cannot answer these (Anton, 2026-08-02).
    units = {x_name: ("s" if dataType in _TIME_TYPES
                      else ("Hz" if ini.hz else "rad/s"))}
    for name in signals:
        found = _slicap_units_hint(name, results)
        if found:
            units[name] = found
    return dataset(x_name=x_name, x_data=x, signals=signals,
                   step_params=step_params, params=params, units=units,
                   gain_type=getattr(results, "gainType", None))



#: the x names of a frequency axis and of a time axis (TRACES.md phase 9)
_FREQ_X = ("frequency", "f")
_TIME_X = ("time", "t")
#: what makeDataset() takes of a SLiCAP result, per dataType: its functions
_DATASET_FUNCTIONS = {'laplace': 'frequency', 'numer': 'frequency',
                      'denom': 'frequency', 'noise': 'frequency',
                      'time': 'time', 'impulse': 'time', 'step': 'time'}


def _dataset_source(name, source):
    """``(kind, domain, object)`` of one source of :func:`makeDataset`:
    kind "data" (a dataset), "filter" (made with makeFilter), "slicap" (a
    SLiCAP result) or "expr" (an expression in s, f or t); domain
    "frequency", "time", another x name of data, or None when the source
    adapts (a filter, a constant). Raises ValueError for what it cannot
    use."""
    if not str(name).isidentifier():
        raise ValueError("makeDataset: the name {0!r} is not a Python "
                         "identifier".format(name))
    if isinstance(source, sp.Basic):
        symbols = source.free_symbols
        t = sp.Symbol('t')
        if not symbols:
            return "expr", None, source
        if symbols == {ini.laplace} or symbols == {ini.frequency}:
            return "expr", "frequency", source
        if symbols == {t}:
            return "expr", "time", source
        raise ValueError("makeDataset: {0} is an expression in {1}; it must "
                         "be an expression in {2}, {3} or t without other "
                         "symbols".format(name, ", ".join(sorted(
                             str(v) for v in symbols)), ini.laplace,
                             ini.frequency))
    dataType = getattr(source, "dataType", None)
    if dataType in _FILTER_TYPES:
        if getattr(source, "H_z", None) is None:
            raise ValueError("makeDataset: {0} is a filter design; make the "
                             "filter with sl.makeFilter()".format(name))
        return "filter", None, source
    if dataType in _DATASET_FUNCTIONS and hasattr(source, "laplace"):
        return "slicap", _DATASET_FUNCTIONS[dataType], source
    data = as_dataset(source)
    if data is None:
        raise ValueError("makeDataset: {0} is not a result makeDataset can "
                         "use: a dataset, an NGspice or system run, a SLiCAP "
                         "result ({1}), a filter or an expression".format(
                             name, ", ".join(sorted(_DATASET_FUNCTIONS))))
    if data.x_data is None or not data.x_name:
        return "data", None, data              # an operating point: alone only
    x_name = str(data.x_name)
    domain = ("frequency" if x_name in _FREQ_X else
              "time" if x_name in _TIME_X else x_name)
    return "data", domain, data


def _prefixed(name, data):
    """*data* with its signals, units and parameters as ``NAME.key``."""
    return dataset(x_name=data.x_name, x_data=data.x_data,
                   signals={"{0}.{1}".format(name, k): v
                            for k, v in data.signals.items()},
                   step_params=data.step_params,
                   params={"{0}.{1}".format(name, k): v
                           for k, v in data.params.items()},
                   units={("{0}.{1}".format(name, k) if k in data.signals else k): v
                          for k, v in data.units.items()},
                   gain_type=data.gain_type,
                   sampled=getattr(data, "sampled", False))


def _same_points(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return a.shape == b.shape and np.allclose(a, b, rtol=1e-9, atol=0.0)


def makeDataset(sources, x=None, start=None, stop=None, num=None,
                method=None, params=None):
    """Builds ONE :class:`SLiCAPtraces.dataset` from named results, for
    :func:`SLiCAPtraces.make_traces` and :func:`SLiCAPtraces.measure`
    (TRACES.md phase 9, Anton, 2026-11-25). Its columns carry dotted
    names, the names of the Design data, so one expression can combine
    several results::

        D1  = sl.makeDataset({"AC1": AC1, "LAPLACE1": LAPLACE1})
        TR1 = sl.make_traces(D1, [{"y": "dB(mag(AC1.V_out)) - dB(mag(LAPLACE1.laplace))"}],
                             variables={"AC1.V_out": "AC1.v(out)"})
        D2  = sl.makeDataset({"FLT1": FLT1, "FLT2": FLT2}, x="frequency",
                             start="79.99M", stop="80.01M", num=500, method="lin")
        TR2 = sl.make_traces(D2, [{"y": "dB(mag(FLT1.H_fs + FLT2.H_fs))"}])

    A source is DATA or gives FUNCTIONS:

    - data: an NGspice run, a system run's dataset (``R1.dataset("ref")``)
      or any dataset: its signals as ``NAME.signal``, on its own points;
    - a filter made with ``makeFilter()``: in frequency the functions
      ``NAME.H_fs`` and ``NAME.H_fz``; in time DATA, ``NAME.impulse`` and
      ``NAME.stepResp`` at the sample times k Ts from *start* to *stop*;
    - a SLiCAP result: ``NAME.laplace``, ``NAME.numer``, ``NAME.denom``,
      ``NAME.onoise``, ``NAME.inoise`` and ``NAME.onoise_<source>``
      (frequency) or ``NAME.time``, ``NAME.impulse``, ``NAME.stepResp``
      (time), one row per run when it is stepped;
    - an expression in s, f or t, such as ``FLT1.H_fs + FLT2.H_fs``: the
      column ``NAME``.

    Functions are evaluated where the data lie: an expression in s or f on
    a frequency axis (s = j 2 pi f), one in t on a time axis. Data of
    several sources must lie on the same points; resampling was REJECTED
    (Anton, 2026-11-25): interpolation is not exact. Without data the range
    is given: *x* ("frequency" or "time"), *start*, *stop*, *num* and
    *method* ("log" or "lin", default "log" in frequency and "lin" in
    time); a limit may name a parameter of *params*, as in sweepData()
    (Anton, 2026-11-09). The circuit parameters of a source are
    ``NAME.parameter``. Data without an axis (an operating point) can only
    stand alone: its signals are measured, not combined.

    Errors, not warnings, like makeFilter(): the dataset is used further
    on. The tool checks the abscissa only, never the units or the meaning
    (Anton, 2026-11-25).

    :param sources: ``{name: source}``; a name is a Python identifier
    :type sources: dict
    :param x: "frequency" or "time" when no data source fixes the axis
    :type x: str, NoneType
    :param start: start of the range, SLiCAP notation; for the sample
                  times of a filter in time also with data
    :param stop: end of the range, as *start*
    :param num: number of points, without data
    :param method: "log" or "lin", without data
    :param params: parameter definitions for limits that name a parameter,
                   the dict ``selectPars()`` returns
    :type params: dict, NoneType
    :return: the dataset
    :rtype: SLiCAPtraces.dataset
    :raises ValueError: a source it cannot use, or sources that do not
                        match
    """
    from SLiCAP.SLiCAPmath import _zResponse, _makeNumData
    from SLiCAP.SLiCAPlex import _scale_float
    if not isinstance(sources, dict) or not sources:
        raise ValueError("makeDataset: give the sources as a dict "
                         "{name: result}")
    found = {name: _dataset_source(name, src) for name, src in sources.items()}
    axisless = [name for name, (kind, dom, _o) in found.items()
                if kind == "data" and dom is None]
    if axisless:
        if len(found) > 1:
            raise ValueError("makeDataset: {0} has no axis (an operating point) "
                             "and cannot be combined".format(axisless[0]))
        name, (_kind, _dom, data) = next(iter(found.items()))
        return _prefixed(name, data)
    limit_defs = _sweep_par_defs(None, params)

    # the axis: every source that fixes one must agree
    domains = {name: dom for name, (kind, dom, _o) in found.items() if dom}
    if x is not None:
        if str(x) in _FREQ_X:
            domains["x"] = "frequency"
        elif str(x) in _TIME_X:
            domains["x"] = "time"
        else:
            raise ValueError("makeDataset: x must be 'frequency' or 'time', "
                             "not {0!r}".format(x))
    if len(set(domains.values())) > 1:
        raise ValueError("makeDataset: the sources lie on different axes: "
                         + ", ".join("{0} {1}".format(n, d)
                                     for n, d in domains.items()))
    if not domains:
        raise ValueError("makeDataset: give x='frequency' or x='time'")
    domain = next(iter(domains.values()))
    if domain not in ("frequency", "time") and any(
            kind != "data" for kind, _d, _o in found.values()):
        raise ValueError("makeDataset: functions need a frequency or a time "
                         "axis, not {0!r}".format(domain))

    # the points: the data, the sample times of a filter in time, or the range
    grids = {name: obj for name, (kind, _d, obj) in found.items()
             if kind == "data"}
    filters_in_time = [name for name, (kind, _d, _o) in found.items()
                       if kind == "filter" and domain == "time"]
    if grids and not filters_in_time and (start is not None or stop is not None):
        raise ValueError("makeDataset: the points of {0} fix the axis; leave "
                         "start and stop out".format(", ".join(grids)))
    if filters_in_time and (start is None or stop is None):
        raise ValueError("makeDataset: the sample times of {0} need start and "
                         "stop".format(", ".join(filters_in_time)))
    points = {name: np.asarray(data.x_data, dtype=float)
              for name, data in grids.items()}
    responses = {}
    for name in filters_in_time:
        flt = found[name][2]
        lo, hi = _sweep_limit(start, limit_defs), _sweep_limit(stop, limit_defs)
        t, impulse = flt.impulse(lo, hi)
        responses[name] = {"impulse": impulse,
                           "stepResp": flt.stepResp(lo, hi)[1]}
        points[name] = t
    if points:
        first = next(iter(points))
        for name, values in points.items():
            if not _same_points(values, points[first]):
                raise ValueError("makeDataset: {0} and {1} do not lie on the "
                                 "same points; data is not resampled".format(
                                     first, name))
        xs = points[first]
        if first in grids:
            x_name = grids[first].x_name
            x_units = grids[first].units.get(x_name)
        else:
            x_name, x_units = "t", "s"
    else:
        if start is None or stop is None or num is None:
            raise ValueError("makeDataset: without data give start, stop and "
                             "num")
        lo, hi = _sweep_limit(start, limit_defs), _sweep_limit(stop, limit_defs)
        if method is None:
            method = "log" if domain == "frequency" else "lin"
        xs = _sweep_axis(lo, hi, int(_scale_float(num)), method)
        if xs is None:
            raise ValueError("makeDataset: a logarithmic axis needs positive "
                             "limits")
        x_name = "frequency" if domain == "frequency" else "t"
        x_units = ("Hz" if ini.hz else "rad/s") if domain == "frequency" else "s"
    if domain == "frequency" and x_units is None:
        x_units = "Hz" if ini.hz else "rad/s"
    # the frequency as SLiCAP takes it (ini.hz): data in Hz with ini.hz
    # False is evaluated at omega = 2 pi f
    fx = xs
    if domain == "frequency":
        if x_units == "Hz" and not ini.hz:
            fx = 2 * np.pi * xs
        elif x_units == "rad/s" and ini.hz:
            fx = xs / (2 * np.pi)
    t = sp.Symbol('t')

    def function_values(expression, real=False):
        """One expression in s, f or t over the points; *real* for a noise
        spectrum, a real function of f."""
        if real:
            return np.asarray(_makeNumData(sp.N(expression), ini.frequency, fx,
                                           normalize=False), dtype=float)
        if domain == "frequency":
            if ini.laplace in expression.free_symbols:
                return _laplace_data(expression, fx)
            f = sp.lambdify(ini.frequency, expression, "numpy")
            return np.broadcast_to(np.asarray(f(fx), dtype=complex),
                                   fx.shape).copy()
        return np.asarray(_makeNumData(sp.N(expression), t, xs,
                                       normalize=False), dtype=float)

    signals, units, params, step_params = {}, {x_name: x_units}, {}, {}
    sampled, runs_of = bool(filters_in_time), {}
    for name, (kind, _dom, obj) in found.items():
        if kind == "data":
            for key, values in obj.signals.items():
                signals["{0}.{1}".format(name, key)] = values
                if key in obj.units:
                    units["{0}.{1}".format(name, key)] = obj.units[key]
            for key, value in obj.params.items():
                params["{0}.{1}".format(name, key)] = value
            if obj.stepped:
                runs_of[name] = (obj.n_runs, obj.step_params)
            sampled = sampled or getattr(obj, "sampled", False)
        elif kind == "filter" and domain == "time":
            for key, values in responses[name].items():
                signals["{0}.{1}".format(name, key)] = values
        elif kind == "filter":
            signals[name + ".H_fs"] = _laplace_data(obj.H_s, fx)
            signals[name + ".H_fz"] = _zResponse(obj.H_z, obj.Ts, fx)
        elif kind == "slicap":
            noise = obj.dataType == "noise"
            columns = {attr: _slicap_runs(obj, attr)
                       for attr in _SLICAP_SIGNALS[obj.dataType]}
            if noise:
                columns.update(_slicap_noise_terms(obj))
            for attr, expressions in columns.items():
                if not expressions:
                    continue
                arrays = [function_values(sp.sympify(e), real=noise)
                          for e in expressions]
                key = "{0}.{1}".format(name, attr)
                signals[key] = arrays[0] if len(arrays) == 1 else np.array(arrays)
                hint = _slicap_units_hint(SWEEP_SIGNAL_NAMES.get(attr, attr), obj)
                if hint:
                    units[key] = hint
            for key, value in _slicap_params(obj).items():
                params["{0}.{1}".format(name, key)] = value
            stepped = _slicap_step_params(obj)
            if stepped:
                runs_of[name] = (len(next(iter(stepped.values()))), stepped)
        else:
            signals[name] = function_values(obj)

    # the runs: stepped sources must agree; a function applies to every run
    n_runs = 1
    for name, (count, steps) in runs_of.items():
        if n_runs not in (1, count):
            raise ValueError("makeDataset: the stepped sources {0} have "
                             "different numbers of runs".format(", ".join(runs_of)))
        n_runs = count
        for key, values in steps.items():
            if key in step_params and not np.allclose(step_params[key], values):
                raise ValueError("makeDataset: the step parameter {0} differs "
                                 "between {1}".format(key, ", ".join(runs_of)))
            step_params[key] = values
    if n_runs > 1:
        # one row per run, so that a run selects a row whatever the number
        # of points (_run_slice reads a 1-D array of n_runs values as one
        # value per run)
        for key, values in signals.items():
            values = np.asarray(values)
            if values.ndim == 1:
                signals[key] = np.tile(values, (n_runs, 1))
    only = next(iter(found.values())) if len(found) == 1 else None
    gain_type = (getattr(only[2], "gainType", None)
                 if only is not None and only[0] == "slicap" else None)
    return dataset(x_name=x_name, x_data=xs, signals=signals,
                   step_params=step_params, params=params, units=units,
                   gain_type=gain_type, sampled=sampled)

# The trace names of the attributes of a swept SLiCAP result: what the
# quantity IS, the transfer H_s at s = j 2 pi f, its numerator N_s and its
# denominator D_s, as the filter traces name their transfers H_z and H_s.
# The attribute names laplace, numer and denom WERE the trace names.
# REPLACED (Anton, 2026-11-25): they name a transform and two polynomials,
# not the quantities. The result keeps its attributes: LAPLACE1.laplace is
# still the transfer expression. The Traces dialog reads this table.
SWEEP_SIGNAL_NAMES = {"laplace": "H_s", "numer": "N_s", "denom": "D_s"}


def _slicap_units_hint(name, result=None):
    """Units of the signals :func:`sweepData` writes.

    The name alone cannot say them: ``onoise`` is V^2/Hz for a voltage
    detector and A^2/Hz for a current one, and a transfer is detector units
    over source units. They are read from the result, exactly as the axis
    labels of :func:`plotSweep` read them (Anton, 2026-07-30: units are
    stated, and suggested only where something KNOWS them).
    """
    if result is None:
        return None
    det = getattr(result, "detUnits", "") or ""
    src = getattr(result, "srcUnits", "") or ""
    if name in SWEEP_SIGNAL_NAMES.values():
        return "{0}/{1}".format(det, src) if det and src else det or None
    if name in ("time", "impulse", "stepResp"):
        return det or None
    if name == "onoise" or name.startswith("onoise_"):
        return "{0}^2/Hz".format(det) if det else None
    if name == "inoise" or name.startswith("inoise_"):
        return "{0}^2/Hz".format(src) if src else None
    return None


register_units_hint(_slicap_units_hint)
