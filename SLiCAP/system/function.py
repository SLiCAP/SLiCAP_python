"""Function base classes of the system-level simulator.

A *function* is the Python unit behind a lowest-level block of a system
diagram (SystemExtensionSpecs.md section 2). Two kinds exist, decided by
the base class:

``Algebraic``
    Can never have a state. It has ``output()`` only, all its outputs
    are direct (they depend on the inputs of the same tick), and it has
    no clock. It fires at every tick where a function feeding it fires.

``Clocked``
    Can have a state. It has a clock domain and the methods
    ``output()``, ``update()``, ``read_state()`` and ``load_state()``.
    Whether an instance has a state and which outputs are direct follows
    from its parameters and is set in the constructor (``self.order``,
    ``self.direct``).

Declaration pattern (SystemExtensionSpecs.md 2.8): the arithmetic is
written ONCE, as kernels, plain functions on plain values. The class
names them and nothing else::

    def biquad_out(x, state, b, a):
        return b[0] * x + state[0]

    def biquad_upd(x, y, state, b, a):
        state[0] = state[1] + b[1] * x - a[1] * y
        state[1] = b[2] * x - a[2] * y

    class Biquad(Clocked):
        inputs  = ("x",)              # class data: the pins of the symbol
        outputs = ("y",)
        kernels = (biquad_out, biquad_upd)

        def __init__(self, b, a):
            super().__init__(order=2)
            self.b, self.a = np.array(b), np.array(a)
            self.params = (self.b, self.a)
            if b[0] != 0:
                self.direct = {"y"}   # feedthrough
            else:
                self.direct = set()

``inputs``, ``outputs`` and ``kernels`` are class attributes because the
GUI reads the pins before any instance exists and the engine copies
the kernels into the tick program. Everything else is set in
``__init__``.

The base class provides ``output()`` and ``update()``: they read the
input attributes, call the kernel with the state and the parameters,
and write the output attributes. A call by hand and the tick program
therefore run the same code. (Methods written per class next to the
kernels were REPLACED by this on 2026-11-16: two copies of one
arithmetic, and a subclass could inherit kernels that did not match
its methods.)

Kernel signatures, inputs and outputs in the order of the class data:

- algebraic: ``k_out(in_1, ..., in_m, *params)``;
- clocked: ``k_out(in_1, ..., in_m, state, *params)`` and
  ``k_upd(in_1, ..., in_m, out_1, ..., out_k, state, *params)``.

``k_out`` returns the output value, or a tuple when there are several
outputs. ``k_upd`` changes ``state`` in place. ``params`` is a tuple of
floats, ints, bools or numpy arrays; the sample time ``Ts`` is one of
them where the kernel needs it, so a class that needs it builds
``params`` as a property (``Ts`` is set when the function is added to
a system). A kernel uses only plain arithmetic, numpy arrays and
module-level helper functions of the same kind, so that numba compiles
it.

A function whose arithmetic cannot be a kernel has ``kernels = None``
and writes ``output()`` and ``update()`` itself. The tick program then
drives it by its methods and runs in plain Python (Specs 4.7).

Two hooks connect a function to the run as a whole, both optional:
``limit()`` returns the number of firings the function can still
deliver (a recorded signal), and ``prepare(firings)`` receives the
number of firings of the coming run (a noise source draws its samples
then). Sources of both kinds are an array and an index in the state,
so they are kernels (Specs 6.1, 6.2).

Port values are instance attributes named after the ports. ``output()``
reads the input attributes and writes the output attributes. The engine
copies output values to the connected inputs after ``output()`` ran.

Data types: the optional class attribute ``types`` maps a port name to
a numpy dtype. A port without an entry is ``numpy.float64``. The
engine wraps integer-typed outputs to their width when ``output()``
returns (SystemExtensionSpecs.md 5.3).
"""

import numpy as np


class Function:
    """Common part of ``Algebraic`` and ``Clocked``. Not used directly."""

    inputs = ()
    outputs = ()
    types = {}
    kind = None
    kernels = None
    params = ()
    #: True for a function that lives in physical time (a signal source):
    #: its kernels take the time of the tick, ``tm`` in seconds, as their
    #: first argument, and a method reads ``self.time`` (Specs 15.2: the
    #: duration of a tick may vary, so time is not the tick count)
    uses_time = False

    def __init__(self):
        self.name = None
        self.time = 0.0
        for port in tuple(self.inputs) + tuple(self.outputs):
            if not hasattr(self, port):
                setattr(self, port, 0.0)

    def output(self):
        """Compute the outputs from the inputs and the state by the
        output kernel. No side effect on the state.

        A class without kernels overrides this.
        """
        if self.kernels is None:
            raise NotImplementedError(
                "%s has no kernels and no output() method"
                % type(self).__name__)
        values = self.kernels[0](*self._time_arg(), *self._kernel_inputs(),
                                 *self.params)
        if len(self.outputs) == 1:
            values = (values,)
        for name, value in zip(self.outputs, values):
            setattr(self, name, value)

    def _kernel_inputs(self):
        """The input values, plus the state for a clocked function."""
        return [getattr(self, name) for name in self.inputs]

    def _time_arg(self):
        """``[self.time]`` for a function in physical time, else []."""
        return [float(self.time)] if self.uses_time else []

    def limit(self):
        """Number of firings this function can still deliver, or None
        when there is no limit. The engine shortens a run to the
        smallest limit before it starts (Specs 6.2). A source with
        recorded data overrides this."""
        return None

    def prepare(self, firings):
        """Called by the engine before a run with the number of times
        this function fires in that run. A source that draws its samples
        in advance overrides this; the default does nothing."""
        return None

    def dtype(self, port):
        """numpy dtype of *port*; float64 when not declared."""
        return np.dtype(self.types.get(port, np.float64))

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.name or "")


class Algebraic(Function):
    """A function that can never have a state.

    No clock, no ``update()``. All outputs are direct.
    """

    kind = "algebraic"
    order = 0

    @property
    def direct(self):
        return set(self.outputs)


class Clocked(Function):
    """A function that can have a state, in one clock domain.

    :param order: length of the state vector. Zero for an instance
                  without state (for example a CORDIC without register
                  stages).

    The constructor of a subclass sets ``self.direct``, the set of
    output names with feedthrough. The default is the empty set: all
    outputs computed from the state only.

    The default state is ``self.state``, a float64 vector of length
    *order*. ``read_state()`` and ``load_state()`` work on it. A
    subclass with another state layout overrides both.

    ``self.Ts`` is the sample time of the function's clock domain in
    seconds. The ``System`` sets it when the function is added with its
    domain; a constructor cannot use it. A block therefore never has
    the sample time as a parameter: it comes from the clock wire.
    """

    kind = "clocked"

    def __init__(self, order=0):
        super().__init__()
        self.order = int(order)
        self.direct = set()
        self.state = np.zeros(self.order)
        self.domain = None
        self.Ts = None

    def _kernel_inputs(self):
        return [getattr(self, name) for name in self.inputs] + [self.state]

    def update(self):
        """Move the state to the next cycle of the domain by the update
        kernel. Reads the current inputs, the outputs and the state.

        A class without kernels overrides this; one without state
        leaves it as it is.
        """
        if self.kernels is None:
            return None
        outs = [getattr(self, name) for name in self.outputs]
        self.kernels[1](*self._time_arg(),
                        *[getattr(self, name) for name in self.inputs],
                        *outs, self.state, *self.params)

    def read_state(self):
        """The state vector, a copy."""
        return np.array(self.state, copy=True)

    def load_state(self, vector):
        """Set the state vector."""
        vector = np.asarray(vector, dtype=float).ravel()
        if vector.size != self.order:
            raise ValueError(
                "%s: state vector of length %d, expected %d"
                % (self, vector.size, self.order))
        self.state = np.array(vector, copy=True)


def check_function(fn):
    """Raise ``TypeError`` when *fn* is not a usable function instance.

    Catches the common mistake of a subclass whose ``__init__`` did not
    call ``super().__init__()``.
    """
    if not isinstance(fn, Function) or type(fn) in (Function, Algebraic,
                                                     Clocked):
        raise TypeError("%r is not an Algebraic or Clocked function" % (fn,))
    if not hasattr(fn, "name"):
        raise TypeError(
            "%s.__init__ did not call super().__init__()"
            % type(fn).__name__)
    if fn.kind == "clocked":
        unknown = set(fn.direct) - set(fn.outputs)
        if unknown:
            raise ValueError(
                "%s: direct outputs %s are not outputs"
                % (fn, sorted(unknown)))
    ks = fn.kernels
    if ks is not None:
        need = 2 if fn.kind == "clocked" else 1
        if (not isinstance(ks, tuple) or len(ks) != need
                or not all(callable(k) for k in ks)):
            raise TypeError(
                "%s: kernels must be a tuple of %d function%s"
                % (fn, need, "s" if need > 1 else ""))
        if not isinstance(fn.params, tuple):
            raise TypeError("%s: params must be a tuple" % (fn,))
