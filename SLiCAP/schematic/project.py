"""
Project layout + per-schematic sidecar file locations.

A SLiCAP project directory is organised into subdirectories (mirroring the
SLiCAP Python project structure, plus a new ``sch/``)::

  sch/   schematic sources and their sidecars
  cir/   exported top-level netlists (``<name>.cir``)
  lib/   subcircuit libraries (``<name>.lib``) and their symbols
  img/   exported images (``<name>.svg`` / ``<name>.pdf``)

``project_root()`` / ``subdir()`` resolve these directories; the root is derived
from the open schematic (its ``sch/`` parent) or the app root when unsaved.

A schematic saved as ``<name>.<ext>`` (e.g. ``design.slicap_sch`` or
``design.spice_sch``) owns sidecar files that live right next to it in ``sch/``,
named by appending the sidecar suffix to the *full* filename so that same-named
schematics of different types never collide:

  ``<name>.<ext>.cache``    directory of rendered-LaTeX SVGs
  ``<name>.<ext>.ini``      per-schematic style overrides
  ``<name>.<ext>.symbols``  frozen copies of every symbol the schematic uses

Until a schematic is first saved it has no name; its sidecars then live in a
per-session temporary directory (auto-removed on exit) and are migrated to the
real locations on the first save.

``set_current()`` tracks the schematic the user is working in; it drives only
the genuinely focus-bound state (the stdout log tee, project-root fallback).
Per-schematic state — style, symbol library, render cache — is owned by the
panels and resolved through the explicit ``*_for(path)`` helpers.
"""
from __future__ import annotations

from pathlib import Path

_base: Path | None = None          # the schematic path, or None when unsaved

# The default project root — the directory holding the cir/ sch/ img/ lib/ and
# symbols/ subdirectories.  Defaults to the working directory at start-up so
# that launching via sl.startSchematic() (which inherits the project's cwd)
# puts new schematics in <project>/sch/ instead of the install directory.
APP_ROOT = Path.cwd()


def current() -> Path | None:
    """The current schematic path, or None when never saved."""
    return _base


def set_app_root(path) -> None:
    """Set the default project root used when no schematic is open.

    File → Select project folder switches the project while the welcome screen
    is still showing (no ``_base`` yet); without this, ``project_root()`` would
    keep returning the start-up working directory, so Open-schematic and new
    schematics would land in the wrong ``sch/``.
    """
    global APP_ROOT
    APP_ROOT = Path(path)


def project_root() -> Path:
    """Directory holding the SLiCAP project subdirs (cir/ sch/ img/ lib/).

    Derived from the open schematic — if it lives in a ``sch/`` or ``lib/``
    directory the root is that directory's parent (subcircuit schematics are
    part of the package in ``lib/``, Anton 2026-08-05) — so a schematic
    opened from any project resolves its netlists, images and libraries next
    to itself.  Falls back to the app root when nothing is open (a brand-new,
    unsaved schematic).
    """
    if _base is not None:
        parent = _base.parent
        return parent.parent if parent.name in ("sch", "lib") else parent
    return APP_ROOT


def subdir(name: str) -> Path:
    """Return ``<project_root>/<name>`` (cir, sch, img, lib), creating it."""
    d = project_root() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def root_for(path) -> Path:
    """Project root derived from an explicit schematic ``path`` — independent
    of the app-wide current schematic.  A schematic may live in ``sch/`` or,
    for subcircuit packages, in ``lib/``."""
    parent = Path(path).parent
    return parent.parent if parent.name in ("sch", "lib") else parent


def subdir_for(path, name: str) -> Path:
    """``<root_for(path)>/<name>`` (cir, sch, img, lib), creating it."""
    d = root_for(path) / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sidecar(ext: str) -> Path:
    """Return the sidecar path for the current schematic.

    Uses ``<name>.<schematic_ext>.<sidecar_ext>`` so that ``design.slicap_sch``
    and ``design.spice_sch`` never share a sidecar directory or file.
    """
    return _base.parent / (_base.name + ext)


def sidecar_for(path, ext: str) -> Path:
    """Sidecar path for an explicit schematic ``path`` — independent of the
    app-wide current schematic, so panels resolve their own sidecars
    regardless of which schematic holds the global context (e.g. during a
    save-all loop)."""
    p = Path(path)
    return p.parent / (p.name + ext)


def ini_path_for(path) -> Path:
    """Style-sidecar path for an explicit schematic ``path``."""
    return sidecar_for(path, ".ini")


def cache_path_for(path) -> Path:
    """LaTeX render-cache sidecar for an explicit schematic ``path``."""
    return sidecar_for(path, ".cache")


def symbols_path_for(path) -> Path:
    """Frozen-symbols sidecar for an explicit schematic ``path``."""
    return sidecar_for(path, ".symbols")


def _migrate_sidecar(old: Path, new: Path) -> None:
    """Rename an old-style sidecar to the new name if only the old one exists."""
    if old != new and old.exists() and not new.exists():
        try:
            old.rename(new)
        except OSError:
            pass


def set_current(path: "Path | str | None") -> None:
    """Record the schematic the user is working in, None when unsaved.

    Called by the window on New, Open, Save and focus changes.  This drives
    only the genuinely focus-bound state: the stdout/stderr log tee (one
    process stream, split by focused schematic) and the project-root
    fallback for dialogs.  Per-schematic state — style, symbol library,
    LaTeX render cache — is owned by the panels themselves and never
    follows this pointer.

    Also performs a one-time migration of old-style sidecars (``<stem>.cache``
    etc.) to the new full-filename style (``<name>.<ext>.cache`` etc.) so that
    existing SLiCAP schematics keep their style preferences.
    """
    global _base
    _base = Path(path) if path else None

    if _base is not None:
        # One-time migration: old sidecars used _base.with_suffix(ext) which
        # strips the schematic extension — e.g. design.slicap_sch → design.cache.
        # Rename to the new full-filename form if only the old one exists.
        for ext in (".cache", ".ini", ".symbols"):
            _migrate_sidecar(_base.with_suffix(ext), _sidecar(ext))

    # Point terminal-output logging at txt/<name>.<ext>.log for this schematic
    # (or terminal only when unsaved).  subdir() creates txt/ only if missing.
    from . import logfile
    logfile.set_log_path(subdir("txt") / (_base.name + ".log") if _base else None)
