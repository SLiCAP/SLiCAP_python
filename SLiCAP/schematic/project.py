"""
Project layout + per-schematic sidecar file locations.

A SLiCAP project directory is organised into subdirectories (mirroring the
SLiCAP Python project structure, plus a new ``sch/``)::

  sch/   schematic sources (``<name>.slicap_sch``) and their sidecars
  cir/   exported top-level netlists (``<name>.cir``)
  lib/   subcircuit libraries (``<name>.lib``) and their symbols
  img/   exported images (``<name>.svg`` / ``<name>.pdf``)

``project_root()`` / ``subdir()`` resolve these directories; the root is derived
from the open schematic (its ``sch/`` parent) or the app root when unsaved.

A schematic saved as ``<name>.slicap_sch`` owns sidecar files that live right
next to it (i.e. in ``sch/``), so everything belonging to a circuit travels with
it and nothing accumulates in a global cache:

  ``<name>.cache``    directory of rendered-LaTeX SVGs (was ~/.cache/slicap_schematic)
  ``<name>.ini``      per-schematic style overrides (over the global style.ini)
  ``<name>.symbols``  frozen copies of every symbol the schematic uses

Until a schematic is first saved it has no name; its sidecars then live in a
per-session temporary directory (auto-removed on exit) and are migrated to the
real ``<name>.*`` locations on the first save.

``set_current()`` is the single entry point: the window calls it on New, Open,
and Save, and it repoints every subsystem (currently the LaTeX cache).
"""
from __future__ import annotations

import shutil
from pathlib import Path

_base: Path | None = None          # the .slicap_sch path, or None when unsaved

# The default project root — the directory holding the cir/ sch/ img/ lib/ and
# symbols/ subdirectories.  Defaults to the working directory at start-up so
# that launching via sl.startSchematic() (which inherits the project's cwd)
# puts new schematics in <project>/sch/ instead of the install directory.
APP_ROOT = Path.cwd()


def current() -> Path | None:
    """The current schematic's .slicap_sch path, or None when never saved."""
    return _base


def project_root() -> Path:
    """Directory holding the SLiCAP project subdirs (cir/ sch/ img/ lib/).

    Derived from the open schematic — if it lives in a ``sch/`` directory the
    root is that directory's parent — so a schematic opened from any project
    resolves its netlists, images and libraries next to itself.  Falls back to
    the app root when nothing is open (a brand-new, unsaved schematic).
    """
    if _base is not None:
        parent = _base.parent
        return parent.parent if parent.name == "sch" else parent
    return APP_ROOT


def subdir(name: str) -> Path:
    """Return ``<project_root>/<name>`` (cir, sch, img, lib), creating it."""
    d = project_root() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    """Directory holding rendered-LaTeX SVGs for the current schematic.

    When saved it is ``<name>.cache``; when unsaved it is the LaTeX module's
    lazily-created session temp (the single source of the unsaved cache, so a
    later save migrates exactly what was rendered).
    """
    if _base is not None:
        # Not created here — only when a render actually happens, so a schematic
        # with no LaTeX leaves no empty <name>.cache dir.
        return _base.with_suffix(".cache")
    from . import latex_label
    return latex_label.get_cache_dir()


def ini_path() -> Path | None:
    """Path to the per-schematic style overrides, or None when unsaved."""
    return _base.with_suffix(".ini") if _base else None


def symbols_path() -> Path | None:
    """Path to the per-schematic frozen symbol library, or None when unsaved."""
    return _base.with_suffix(".symbols") if _base else None


def set_current(path: "Path | str | None") -> None:
    """Point all sidecars at ``path`` (the .slicap_sch file), None when unsaved.

    Called by the window on New, Open and Save.  On the first save (unsaved →
    named) the session-temp LaTeX cache is migrated to ``<name>.cache`` so the
    saved schematic is immediately self-contained.
    """
    global _base
    from . import latex_label
    old_cache = latex_label.CACHE_DIR     # where renders have gone so far (may be None)
    _base = Path(path) if path else None
    new_cache = cache_dir()

    if path is not None and old_cache is not None and Path(old_cache) != new_cache:
        svgs = list(Path(old_cache).glob("*.svg"))
        if svgs:
            new_cache.mkdir(parents=True, exist_ok=True)
            for f in svgs:
                dest = new_cache / f.name
                if not dest.exists():
                    try:
                        shutil.copy2(f, dest)
                    except OSError:
                        pass

    latex_label.set_cache_dir(new_cache)

    # Point terminal-output logging at txt/<name>.log for this schematic (or the
    # terminal only when unsaved).  subdir() creates txt/ only if missing.
    from . import logfile
    logfile.set_log_path(subdir("txt") / (_base.stem + ".log") if _base else None)
