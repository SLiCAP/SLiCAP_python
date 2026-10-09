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


# The project folders that hold EDITED sources: schematics, subcircuit
# packages and posters (Anton, 2026-10-06: a poster is an editable input, so
# it lives beside the schematics, in its own folder, never in img/ with the
# exports). A file in one of them belongs to the project one level up.
SOURCE_DIRS = ("sch", "lib", "posters")
POSTER_SUFFIX = ".slicap_poster"

# ── the project's folders ────────────────────────────────────────────────────
# A project's SLiCAP.ini names its folders in [projectpaths] (img = ../Figures/
# is how the book's chapter projects write their images into the chapter's
# figure folder). The schematic package used the DEFAULT names regardless and
# exported into img/ (Anton, 2026-10-08). Every folder of the project is now
# resolved here, from that section when the project has one, else by its
# default name; the core (SLiCAPconfigure) reads the same file, so scripts
# and the editor agree. A SLiCAP.ini without [projectpaths] is the user's
# global configuration, never a project.
_INI_NAME = "SLiCAP.ini"
_folder_cache: dict = {}


def _project_paths(root: Path) -> dict:
    """The [projectpaths] section of <root>/SLiCAP.ini, {} when absent."""
    ini = Path(root) / _INI_NAME
    try:
        stamp = ini.stat().st_mtime_ns
    except OSError:
        return {}
    key = (str(ini), stamp)
    if key in _folder_cache:
        return _folder_cache[key]
    import configparser
    cfg = configparser.ConfigParser()
    try:
        cfg.read(str(ini), encoding="utf-8")
        paths = dict(cfg["projectpaths"]) if cfg.has_section("projectpaths") else {}
    except (configparser.Error, OSError, UnicodeDecodeError):
        paths = {}
    _folder_cache.clear()
    _folder_cache[key] = paths
    return paths


def folder_rel(name: str, root=None) -> str:
    """The project folder *name* (cir, img, lib, sch, posters, results, txt,
    ...) as the project's SLiCAP.ini names it, relative to the root and
    without a trailing slash, in POSIX form: ``"img"`` or ``"../Figures"``.
    The form a schematic stores in a link."""
    base = Path(root) if root is not None else project_root()
    value = _project_paths(base).get(name, "")
    value = value.strip().replace("\\", "/").rstrip("/") if value else ""
    return value or name


def folder(name: str, root=None, create: bool = False) -> Path:
    """The project folder *name* as a path (see folder_rel); *create* makes
    it."""
    base = Path(root) if root is not None else project_root()
    rel = folder_rel(name, base)
    d = Path(rel) if Path(rel).is_absolute() else base / rel
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _has_project_ini(d: Path) -> bool:
    return (d / _INI_NAME).is_file() and bool(_project_paths(d))


def doc_type(path) -> str:
    """The document type of a canvas file by its suffix: 'ngspice'
    (.spice_sch), 'poster' (.slicap_poster) or 'slicap' (.slicap_sch)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".spice_sch":
        return "ngspice"
    if suffix == POSTER_SUFFIX:
        return "poster"
    return "slicap"


SCHEMATIC_SUFFIXES = (".slicap_sch", ".spice_sch")


def project_schematics(root=None) -> list:
    """The schematic sources of the project, sorted: those of sch/ and then
    those of lib/ (the subcircuit packages). What Place -> Schematic
    offers (Anton, 2026-10-09: the subcircuits of a figure live in lib/)."""
    base = Path(root) if root is not None else project_root()
    out = []
    for name in ("sch", "lib"):
        d = folder(name, base)
        if d.is_dir():
            out += sorted(p for p in d.iterdir()
                          if p.suffix.lower() in SCHEMATIC_SUFFIXES)
    return out


def schematic_ref(path, root=None) -> str:
    """How a link names a schematic of the project: its source path from
    the root, POSIX form ("sch/amp.slicap_sch", "lib/nullor.spice_sch").
    A bare name was the previous form and was REPLACED: it could not tell
    sch/ from lib/, and it showed nothing of what was linked (Anton,
    2026-10-09). Older files with a bare name still resolve."""
    return relative_to_root(path, path if root is None else None) if root is None \
        else Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def schematic_file_for(ref: str, root=None):
    """The schematic a link refers to, or None: a source path from the
    project root (schematic_ref), or, in older files, a bare name looked
    up in sch/ and then in lib/."""
    base = Path(root) if root is not None else project_root()
    if "/" in ref or Path(ref).suffix.lower() in SCHEMATIC_SUFFIXES:
        p = base / ref
        return p if p.is_file() else None
    for name in ("sch", "lib"):
        for ext in SCHEMATIC_SUFFIXES:
            p = folder(name, base) / (ref + ext)
            if p.is_file():
                return p
    return None


def poster_file_for(name: str, root=None):
    """The poster of the project called *name*, or None."""
    base = Path(root) if root is not None else project_root()
    p = folder("posters", base) / (name + POSTER_SUFFIX)
    return p if p.is_file() else None


def link_source(link: str, root=None):
    """The source file of a schematic or poster link ("schematic:<source
    path>", "poster:<name>"), or None: a figure link has no drawing."""
    kind, _, name = link.partition(":")
    if kind == "schematic":
        return schematic_file_for(name, root)
    if kind == "poster":
        return poster_file_for(name, root)
    return None


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
        return root_for(_base)
    return APP_ROOT


def subdir(name: str) -> Path:
    """The project folder *name* (cir, sch, img, lib, posters, ...) as the
    project's SLiCAP.ini names it, created."""
    return folder(name, project_root(), create=True)


def root_for(path) -> Path:
    """Project root derived from an explicit schematic ``path`` — independent
    of the app-wide current schematic.  A schematic may live in ``sch/`` or,
    for subcircuit packages, in ``lib/``."""
    p = Path(path)
    # the nearest ancestor that holds a project SLiCAP.ini is the root: this
    # also serves a project whose source folders have other names
    for ancestor in p.parents:
        if _has_project_ini(ancestor):
            return ancestor
    parent = p.parent
    return parent.parent if parent.name in SOURCE_DIRS else parent


def relative_to_root(file_path, sch_path=None) -> str:
    """How a schematic stores a linked file (an image): relative to the
    project root when the file lies inside the project, else as given.
    POSIX separators, the form an instruction file uses too. A project then
    moves between machines, or into a book folder, with its links intact
    (Anton, 2026-10-06). *sch_path* is the schematic the link belongs to;
    None means the current one."""
    root = root_for(sch_path) if sch_path is not None else project_root()
    p = Path(file_path)
    if not p.is_absolute():
        return p.as_posix()
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def resolve_from_root(file_path, sch_path=None) -> Path:
    """The file a stored link refers to: a relative link is taken from the
    project root (see relative_to_root), an absolute one as it is."""
    p = Path(file_path)
    if p.is_absolute():
        return p
    root = root_for(sch_path) if sch_path is not None else project_root()
    return root / p


def subdir_for(path, name: str) -> Path:
    """The folder *name* of the project *path* belongs to, created."""
    return folder(name, root_for(path), create=True)


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
        # Legacy '<name>_<type>_symbol.svg' project symbols -> '<name>.<type>_sym'
        # (2026-09-25), once, when a schematic of the project is opened.
        from .symbol_library import migrate_symbol_files
        migrate_symbol_files(subdir_for(_base, "lib"))

    # Point terminal-output logging at txt/<name>.<ext>.log for this schematic
    # (or terminal only when unsaved).  subdir() creates txt/ only if missing.
    from . import logfile
    logfile.set_log_path(subdir("txt") / (_base.name + ".log") if _base else None)
