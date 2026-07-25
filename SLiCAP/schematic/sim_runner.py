"""NGspice subprocess runner.

GUI mode — use SimRunner as a QObject with signals::

    runner = SimRunner(parent)
    runner.line_ready.connect(log_panel.append_line)
    runner.finished.connect(on_finished)
    runner.run(netlist_path, raw_path, cwd)
    runner.stop()

CLI / blocking mode — no Qt event loop required::

    rc = SimRunner.run_blocking(netlist_path, raw_path, cwd,
                                on_line=print)

Both modes run NGspice as::

    ngspice -b <netlist>

The ``-r`` flag is intentionally omitted: it only captures deck-level
analysis directives, not analyses run inside a ``.control`` block.  Raw
output is written via an explicit ``write <raw_path>`` command appended
to the ``.control`` section by the netlist builder.

The working directory is set to *cwd* so that relative ``.include``
and ``.lib`` paths in the netlist resolve correctly.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal


# ── helpers ───────────────────────────────────────────────────────────────────

def _ngspice_binary() -> str:
    """Return the NGspice binary path or raise FileNotFoundError."""
    path = shutil.which("ngspice")
    if path is None:
        raise FileNotFoundError(
            "NGspice not found on PATH. "
            "Install NGspice or set its path in Preferences."
        )
    return path


# ── internal thread ───────────────────────────────────────────────────────────

class _RunThread(QThread):
    line_ready  = Signal(str)
    finished_rc = Signal(int)

    def __init__(self, netlist: Path, cwd: Path):
        super().__init__()
        self._netlist = netlist
        self._cwd     = cwd
        self._proc: subprocess.Popen | None = None

    def run(self):
        try:
            binary = _ngspice_binary()
        except FileNotFoundError as exc:
            self.line_ready.emit(f"Error: {exc}")
            self.finished_rc.emit(1)
            return

        # Path relative to cwd so it stays short in the log.
        try:
            netlist_rel = self._netlist.relative_to(self._cwd)
        except ValueError:
            netlist_rel = self._netlist

        cmd = [binary, "-b", str(netlist_rel)]
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self._cwd),
            )
            for line in self._proc.stdout:
                self.line_ready.emit(line.rstrip())
            self._proc.wait()
            rc = self._proc.returncode
        except Exception as exc:
            self.line_ready.emit(f"Error launching NGspice: {exc}")
            rc = 1

        self.finished_rc.emit(rc)

    def stop(self):
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()


# ── public class ──────────────────────────────────────────────────────────────

class SimRunner(QObject):
    """NGspice subprocess manager.

    Create one instance per window; call run() for each simulation.
    A new internal thread is started on every run() call; calling run()
    while a simulation is already running is a no-op (call stop() first).
    """

    line_ready = Signal(str)
    finished   = Signal(int)   # emitted with the NGspice return code

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: _RunThread | None = None

    def run(
        self,
        netlist:  Path | str,
        raw_path: Path | str,
        cwd:      Path | str,
    ) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        t = _RunThread(Path(netlist), Path(cwd))
        t.line_ready.connect(self.line_ready)
        t.finished_rc.connect(self.finished)
        t.finished_rc.connect(self._on_thread_done)
        self._thread = t
        t.start()

    def stop(self) -> None:
        if self._thread is not None:
            self._thread.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_thread_done(self, _rc: int) -> None:
        self._thread = None

    # ── CLI / blocking helper ─────────────────────────────────────────────────

    @staticmethod
    def run_blocking(
        netlist:  Path | str,
        raw_path: Path | str,
        cwd:      Path | str,
        on_line:  "callable | None" = None,
    ) -> int:
        """Run NGspice synchronously and return its exit code.

        Calls *on_line(line: str)* for each output line when provided.
        Does not require a running Qt event loop.
        """
        binary  = _ngspice_binary()
        netlist = Path(netlist)
        cwd     = Path(cwd)

        try:
            netlist_rel = netlist.relative_to(cwd)
        except ValueError:
            netlist_rel = netlist

        cmd = [binary, "-b", str(netlist_rel)]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(cwd),
        )
        for line in proc.stdout:
            if on_line is not None:
                on_line(line.rstrip())
        proc.wait()
        return proc.returncode
