"""How the GUI starts other programs (Anton, 2026-11-20).

Started from its shortcut (Help > Create shortcut), the GUI runs in
pythonw.exe on Windows, without a console. A console program it starts
then opens a console window of its own, which flashes on the screen:
pdflatex and dvisvgm at every LaTeX render, NGspice, an instruction run.

- NO_WINDOW, the creation flag of every program the GUI starts: the
  program gets a console without a window, and whatever it starts in turn
  shares that console. Its output still comes through the pipes. Outside
  Windows it is 0 and changes nothing.
- python(): the Python for a child process, always that of this
  environment: python.exe next to pythonw.exe, so that an instruction run
  has a console (without a window) for the programs it starts, such as
  NGspice or slicap_det. pythonw.exe would leave them without one.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def python() -> str:
    """The console Python of this environment, for a child process."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        console = exe.with_name("python.exe")
        if console.is_file():
            return str(console)
    return sys.executable
