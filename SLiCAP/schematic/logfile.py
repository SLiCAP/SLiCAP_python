"""Tee terminal output to a per-schematic log file.

``install()`` wraps ``sys.stdout`` / ``sys.stderr`` so everything printed also
goes to a log file; output still appears in the terminal (a tee, nothing is
hidden).  ``project.set_current()`` points the log at ``txt/<name>.log`` for the
current schematic — so ``sch/mycircuit.slicap_sch`` logs to ``txt/mycircuit.log``.

The ``txt/`` directory is created only if missing and is never cleared; only the
schematic's own ``<name>.log`` is written, and it is *appended* to (with a
session header) so earlier content — and any other files in ``txt/`` — is kept.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_logfile = None                  # currently open log file object, or None
_log_path: "Path | None" = None  # its path, or None when logging to terminal only
_opened: set = set()             # log paths already opened in this session
_installed = False


class _Tee:
    """Write-through wrapper: forwards to the real stream and the current log."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, s):
        st = self._stream
        if st is not None:
            try:
                st.write(s)
            except Exception:
                pass
        if _logfile is not None:
            try:
                _logfile.write(s)
                _logfile.flush()
            except Exception:
                pass
        return len(s)

    def flush(self):
        st = self._stream
        if st is not None:
            try:
                st.flush()
            except Exception:
                pass

    def isatty(self):
        return bool(getattr(self._stream, "isatty", lambda: False)())

    def fileno(self):
        return self._stream.fileno()


def install() -> None:
    """Install the stdout/stderr tee once (idempotent)."""
    global _installed
    if _installed:
        return
    sys.stdout = _Tee(sys.stdout)
    sys.stderr = _Tee(sys.stderr)
    _installed = True


def set_log_path(path) -> None:
    """Point the tee at *path* (``txt/<name>.log``), or ``None`` for terminal only.

    The file is opened in append mode so nothing is overwritten; a one-line
    session header is written the first time a given log is opened this run.
    Reopens only when the path actually changes, so switching between schematics
    keeps each log intact.
    """
    global _logfile, _log_path
    path = Path(path) if path is not None else None
    if path == _log_path:
        return

    if _logfile is not None:
        try:
            _logfile.close()
        except OSError:
            pass
        _logfile = None
    _log_path = path
    if path is None:
        return

    try:
        path.parent.mkdir(parents=True, exist_ok=True)   # create txt/ if missing
        first = path not in _opened
        _logfile = open(path, "a", buffering=1, encoding="utf-8")
        _opened.add(path)
        if first:
            _logfile.write(
                f"\n===== SLiCAP schematic session "
                f"{datetime.now():%Y-%m-%d %H:%M:%S} =====\n"
            )
            _logfile.flush()
    except OSError:
        _logfile = None
