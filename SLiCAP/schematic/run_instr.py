"""Instruction file runner for NGspice simulation scripts.

A ``.py`` instruction file is a plain Python module.  It imports
``SLiCAP.SLiCAPngspice as sim`` (and any other helpers it needs) at the
top, then assigns simulation results to module-level variables::

    import SLiCAP.SLiCAPngspice as sim
    import numpy as np

    AC1 = sim.ac("MyCircuit", "dec", 50, 20, 20e3,
                 names={"V_out": "v(out)"})

Usage (CLI / test script)::

    from SLiCAP.schematic.run_instr import run_instr
    namespace = run_instr("design.py")
    print(namespace["AC1"])

Usage (GUI)::

    namespace = run_instr("design.py", log_fn=log_panel.append_line)

Any ``print()`` output from the script goes to *log_fn* when provided,
otherwise to ``sys.stdout``.

If an exception occurs:
  - *log_fn* provided → formatted traceback written via *log_fn*; returns ``{}``.
  - *log_fn* is ``None`` → exception propagates to the caller.

The returned dict is the module's global namespace after execution.
Each result stored by the script (e.g. ``AC1 = sim.ac(...)``) is
accessible by the name used in the script (e.g. ``namespace["AC1"]``).
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal


# ── background runner (GUI mode) ──────────────────────────────────────────────

class _InstrThread(QThread):
    line_ready  = Signal(str)
    finished_rc = Signal(int)
    script_done = Signal()     # script finished; process now only holds figures

    def __init__(self, stem: str, cwd: Path):
        super().__init__()
        self._stem = stem
        self._cwd  = cwd
        self._proc: subprocess.Popen | None = None

    def run(self):
        # -u: unbuffered stdout. With a pipe (not a tty) Python block-buffers,
        # so the log would stay empty until process exit — and since shown
        # matplotlib figures keep the process alive after the script ends
        # (SLiCAPplots._show_nonblocking), the run would LOOK blocked at the
        # first plot even though every instruction already executed.
        cmd = [sys.executable, "-u", "-m", self._stem]
        # SLICAP_GUI_RUN makes the plot atexit handler print _SCRIPT_DONE_SENTINEL
        # before it blocks on open figures, so we can report the run finished
        # (and free the runner for a new run) while the plots stay on screen.
        import os
        from SLiCAP.SLiCAPplots import _SCRIPT_DONE_SENTINEL
        env = {**os.environ, "SLICAP_GUI_RUN": "1"}
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self._cwd),
                env=env,
            )
            for line in self._proc.stdout:
                line = line.rstrip()
                if line == _SCRIPT_DONE_SENTINEL:
                    self.script_done.emit()    # swallowed — never shown in log
                    continue
                self.line_ready.emit(line)
            self._proc.wait()
            rc = self._proc.returncode
        except Exception as exc:
            self.line_ready.emit(f"Error launching instruction file: {exc}")
            rc = 1
        self.finished_rc.emit(rc)

    def stop(self):
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()


class InstrRunner(QObject):
    """Run a Python instruction file as ``python -m <stem>`` in *cwd*.

    Mirrors the ``SimRunner`` interface so the same connection pattern works::

        runner = InstrRunner(parent)
        runner.line_ready.connect(log_panel.append_line)
        runner.finished.connect(on_finished)
        runner.run(instr_path, cwd)
        runner.stop()
    """

    line_ready = Signal(str)
    finished   = Signal(int)   # logical completion — the script finished executing

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: _InstrThread | None = None
        # Runs whose script has finished but whose process lingers to keep
        # show=True figures on screen. Kept referenced so the QThread is not
        # garbage-collected mid-flight; dropped when the process finally exits.
        self._lingering: list[_InstrThread] = []

    def run(self, instr_path: Path | str, cwd: Path | str) -> None:
        # Block only while a run is still EXECUTING; a previous run that merely
        # lingers to display plots does not prevent starting a new one.
        if self._thread is not None and self._thread.isRunning():
            return
        instr_path = Path(instr_path)
        t = _InstrThread(instr_path.stem, Path(cwd))
        t.line_ready.connect(self.line_ready)
        t.script_done.connect(lambda t=t: self._on_script_done(t))
        t.finished_rc.connect(lambda rc, t=t: self._on_thread_finished(rc, t))
        self._thread = t
        t.start()

    def stop(self) -> None:
        if self._thread is not None:
            self._thread.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_script_done(self, t: _InstrThread) -> None:
        # The script executed to completion; its process now only holds figure
        # windows. Report the run finished and free the runner for a new run,
        # keeping the thread referenced until the process actually exits.
        if t is self._thread:
            self._thread = None
            self._lingering.append(t)
            self.finished.emit(0)

    def _on_thread_finished(self, rc: int, t: _InstrThread) -> None:
        if t in self._lingering:
            self._lingering.remove(t)     # figures closed; run already reported
            return
        if t is self._thread:
            self._thread = None
        self.finished.emit(rc)


def run_instr(path: str | Path, log_fn=None) -> dict:
    """Execute *path* as a Python instruction module and return its namespace.

    The caller is responsible for ensuring the working directory is the
    SLiCAP project root before calling this function.  In the GUI this is
    set once via File → Select project folder; in a standalone script the
    user runs from the project directory.

    :param path: Path to the ``.py`` instruction file.
    :param log_fn: Optional callable ``f(line: str)`` that receives each
                   output line (print output + tracebacks on error).
                   When ``None``, output goes to ``sys.stdout`` and
                   exceptions propagate normally.
    :return: The module's ``vars()`` dict after execution, or ``{}``
             if an exception occurred and *log_fn* was provided.
    """
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod  = importlib.util.module_from_spec(spec)
    # Remove stale cached version so the file is always re-executed.
    sys.modules.pop(path.stem, None)

    if log_fn is None:
        spec.loader.exec_module(mod)
        return vars(mod)

    buf        = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        spec.loader.exec_module(mod)
    except Exception:
        tb = traceback.format_exc()
        for line in tb.splitlines():
            log_fn(line)
        return {}
    finally:
        sys.stdout = old_stdout
        for line in buf.getvalue().splitlines():
            log_fn(line)

    return vars(mod)
