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

import SLiCAP.SLiCAPconfigure as ini

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
        self.xData = np.array(traceData[0])
        """
        Array-like data for the x-axis of the trace. On a polar axes this is
        the angle in radians.
        """

        self.yData = np.array(traceData[1])
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
    """
    def __init__(self, x_name=None, x_data=None, signals=None,
                 step_params=None, params=None, units=None, gain_type=None):
        self.x_name      = x_name
        self.x_data      = None if x_data is None else np.asarray(x_data)
        self.signals     = dict(signals) if signals else {}
        self.step_params = dict(step_params) if step_params else {}
        self.params      = dict(params) if params else {}
        self.units       = dict(units) if units else {}
        self.gain_type   = gain_type

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
        if str(name).isidentifier():
            namespace[str(name)] = value
    n_runs = data.n_runs
    for name, values in data.step_params.items():
        if str(name).isidentifier():
            column = np.atleast_1d(values)
            namespace[str(name)] = (column if run is None
                                    else column[run if run < len(column)
                                                else -1])
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
        if name.isidentifier():
            namespace[name] = (np.asarray(values) if run is None
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
    named   = sorted(n for n in data.signals if n.isidentifier())
    unnamed = sorted(n for n in data.signals if not n.isidentifier())
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
    if text.isidentifier():
        if text.startswith("V_"):
            return "V"
        if text.startswith("I_"):
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

    data = as_dataset(data)
    if data is None:
        print("Error: measure() needs a data set or an analysis result.")
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
                   units=units, gain_type=data.gain_type)


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

    def _is_data(node):
        """A name holding run data - what a goal has to swallow."""
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
    data = as_dataset(data)
    data = _rename_signals(data, variables)
    if data is None:
        print("Error: make_traces() needs a data set or an analysis result; "
              "an un-stepped operating point holds scalars and yields no "
              "traces (print them instead).")
        return {}
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
