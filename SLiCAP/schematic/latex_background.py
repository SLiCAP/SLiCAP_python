"""The editor's side of the LaTeX renders that run in the background
(Anton, 2026-11-20: "With MikTeX it can be really slow so users think it
locks up").

The rendering itself has no Qt: ``latex_label.BackgroundRenders`` renders
the labels of live edits on worker threads, and ``latex_label.render_batch``
renders the misses of a whole schematic. This module connects them to the
editor:

- ``relay()``: one object in the editor's thread whose signals carry the
  worker's news into that thread. ``rendered(cache)`` makes the scenes
  build their waiting labels again (``SchematicScene.await_labels``),
  ``pending(n)`` feeds the line "Rendering n LaTeX labels" in the status
  bar of the main window.
- ``wait_for(work, count)``: runs a render on a worker thread and waits
  for it with the window responsive. Opening a schematic, undo, redo and
  an export wait this way. After half a second a line says what is going
  on, with a hint at the package prompt of MiKTeX, which can open behind
  the editor's window.

A signal is emitted from a worker thread to an object that lives in the
editor's thread, so Qt delivers it there as a queued call. The relay is
created once and never deleted, so no worker can emit into a deleted
object. When the application quits, the workers stop notifying.
"""
from __future__ import annotations

import itertools
import threading

from PySide6.QtCore import QEventLoop, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QProgressDialog

from .latex_label import background

WAIT_SHOWN_AFTER_MS = 500          # a shorter wait shows nothing


class _Relay(QObject):
    rendered = Signal(str)         # a round of renders for this cache is done
    pending = Signal(int)          # renders still to do, all schematics
    waited = Signal(int)           # the work of wait_for(token) is done


_relay: "_Relay | None" = None
_tokens = itertools.count(1)


def relay() -> _Relay:
    """The relay, made at the first call, which must be on the editor's
    thread."""
    global _relay
    if _relay is None:
        _relay = _Relay()

        def notify(cache, finished):
            _relay.pending.emit(background.pending())
            if finished:
                _relay.rendered.emit(str(cache))

        background.notify = notify
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(background.stop)
    return _relay


def _wait_text(count: int) -> str:
    return ("Rendering %d LaTeX label%s ...\n\n"
            "MiKTeX may ask in a window of its own to install a package."
            % (count, "" if count == 1 else "s"))


def wait_for(work, count: int, parent=None) -> bool:
    """Run *work* on a worker thread and wait for it, with the window
    responsive. Returns False when the user chose to continue with plain
    text: *work* then goes on to its end, unseen.

    For the first half second no input is taken, so nothing can change the
    schematic that waits. Then a window-modal line names the *count* of
    labels and offers "Continue with plain text"."""
    rel = relay()
    token = next(_tokens)
    done = threading.Event()
    loop = QEventLoop()

    def run():
        try:
            work()
        finally:
            done.set()
            rel.waited.emit(token)

    def on_waited(finished_token):
        if finished_token == token:
            loop.quit()

    rel.waited.connect(on_waited)
    try:
        threading.Thread(target=run, daemon=True,
                         name="SLiCAP LaTeX wait").start()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(WAIT_SHOWN_AFTER_MS)
        if not done.is_set():
            loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        timer.stop()
        if done.is_set():
            return True
        # The wait line takes the activation and the keyboard focus. Both go
        # back to the window and the widget that had them when it closes: the
        # canvas was left without focus, so a raised tab could not take it
        # (tests/test_bug_report_2026_10_21.py, 2026-11-20).
        window_before = QApplication.activeWindow()
        focus_before = QApplication.focusWidget()
        dialog = QProgressDialog(_wait_text(count), "Continue with plain text",
                                 0, 0, parent)
        dialog.setWindowTitle("LaTeX")
        dialog.setWindowModality(Qt.WindowModality.WindowModal if parent is not None
                                 else Qt.WindowModality.ApplicationModal)
        dialog.setMinimumDuration(0)
        dialog.canceled.connect(loop.quit)
        dialog.show()
        if not done.is_set():
            loop.exec()
        dialog.close()
        dialog.deleteLater()
        if window_before is not None and window_before.isVisible():
            window_before.activateWindow()
        if focus_before is not None and focus_before.isVisible():
            focus_before.setFocus()
        return done.is_set()
    finally:
        rel.waited.disconnect(on_waited)
