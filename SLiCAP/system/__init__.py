"""System-level discrete-time simulator: the engine.

Local only until released (SystemExtensionSpecs.md section 13). The
public script API for users is ``SLiCAP.SLiCAPsystem``; this package
holds the engine behind it.

::

    from SLiCAP.system import Algebraic, Clocked, ClockTree, System, run
"""

from .function import Algebraic, Clocked, Function
from .clock import ClockTree
from .system import System
from .schedule import Schedule, AlgebraicLoop
from .record import Record, envelope, DEPTH_LIMIT, ENVELOPE_BINS
from .engine import (run, RunResult, EndOfData, save_state, load_state,
                     request_stop)

__all__ = ["Algebraic", "Clocked", "Function", "ClockTree", "System",
           "Schedule", "AlgebraicLoop", "Record", "envelope",
           "DEPTH_LIMIT", "ENVELOPE_BINS", "run", "RunResult",
           "EndOfData", "save_state", "load_state", "request_stop"]
