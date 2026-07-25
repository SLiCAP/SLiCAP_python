"""Application-level GUI preferences (SLNG.md "Design data panel" spec).

Stored in the USER ini ``~/SLiCAP_gui.ini`` — these are application-level
panel settings (which object kinds the Design data panel shows, which
directories / file types the Project panel shows), not per-project or
per-document state. Edited through the File → Preferences… dialog; the
panels' "Configure view…" context entries and their "N hidden" footers
open the same dialog.
"""
from __future__ import annotations

import configparser
import json
from pathlib import Path

PREFS_PATH = Path.home() / "SLiCAP_gui.ini"

# Design data panel: stored as EXCLUSIONS (Anton live finding 2026-07-12:
# an inclusion list saved earlier hides every kind curated later — the
# snippet kind stayed invisible although default-visible). Same model as
# the project view: hiding is an explicit act; a newly curated kind is
# visible unless the user hid it. Genuinely unknown object types classify
# as "other", which is hidden by default — the original spec rule holds.
from .design_data import KNOWN_KINDS

DEFAULT_HIDDEN_KINDS = ["array", "list", "text", "other"]
DEFAULT_KINDS = [k for k in KNOWN_KINDS if k not in DEFAULT_HIDDEN_KINDS]

# Project panel (Anton, 2026-07-11 live check): one EXCLUSION model for
# everything — the formerly hard-coded hidden machinery (caches, GUI
# sidecars, build helpers) is just the DEFAULT exclusion set, editable in
# the same preferences tree as everything else. Type exclusions are PER
# top-level DIRECTORY ("" = files in the project root); a directory not
# in the "types" map uses the defaults, so new directories behave sanely.
# Exclusion (not inclusion) storage means a NEW file type is visible by
# default — hiding is always an explicit user act.
DEFAULT_EXCLUDED_DIRS = ["__pycache__", "*.cache"]
DEFAULT_EXCLUDED_TYPES = [".pyc", ".symbols", ".cache", ".slicap_sch.ini",
                          ".spice_sch.ini", "Makefile", "make.bat"]


def _read() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(PREFS_PATH)
    return cfg


def _write(cfg: configparser.ConfigParser) -> None:
    with open(PREFS_PATH, "w", encoding="utf-8") as fh:
        cfg.write(fh)


def _get_list(section: str, key: str, default: list[str]) -> list[str]:
    cfg = _read()
    try:
        raw = cfg[section][key]
    except KeyError:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _set_list(section: str, key: str, values: list[str]) -> None:
    cfg = _read()
    if section not in cfg:
        cfg[section] = {}
    cfg[section][key] = ", ".join(values)
    _write(cfg)


def get_visible_kinds() -> list[str]:
    hidden = set(_get_list("panels", "design_data_hidden_kinds",
                           DEFAULT_HIDDEN_KINDS))
    return [k for k in KNOWN_KINDS if k not in hidden]


def set_visible_kinds(kinds: list[str]) -> None:
    _set_list("panels", "design_data_hidden_kinds",
              [k for k in KNOWN_KINDS if k not in kinds])


def get_project_view() -> dict:
    """Project-panel view: ``{"excluded_dirs": [names, "*.suffix"…],
    "types": {top_level_dir_or_"": [excluded type keys]}}``."""
    cfg = _read()
    try:
        data = json.loads(cfg["panels"]["project_view"])
        if isinstance(data, dict):
            data.setdefault("excluded_dirs", list(DEFAULT_EXCLUDED_DIRS))
            data.setdefault("types", {})
            return data
    except (KeyError, ValueError):
        pass
    return {"excluded_dirs": list(DEFAULT_EXCLUDED_DIRS), "types": {}}


def set_project_view(view: dict) -> None:
    cfg = _read()
    if "panels" not in cfg:
        cfg["panels"] = {}
    cfg["panels"]["project_view"] = json.dumps(view)
    _write(cfg)


def excluded_types_for(view: dict, bucket: str) -> set[str]:
    """Excluded type keys for a directory, keyed by its project-relative
    path ("" = project root, "sch", "tex/SLiCAPdata", …); directories the
    user never configured use the defaults."""
    types = view.get("types", {})
    if bucket in types:
        return set(types[bucket])
    return set(DEFAULT_EXCLUDED_TYPES)


def dir_excluded(name: str, excluded_dirs, rel_path: str | None = None) -> bool:
    """Directory exclusion. Entries match by NAME at any depth
    (``__pycache__``), by suffix pattern (``*.cache`` — the LaTeX label
    caches), or — entries containing "/" — by exact project-relative PATH
    (``tex/SLiCAPdata``: hides that one, not sphinx/SLiCAPdata)."""
    for e in excluded_dirs:
        if "/" in e:
            if rel_path is not None and rel_path == e:
                return True
        elif e.startswith("*"):
            if name.endswith(e[1:]):
                return True
        elif name == e:
            return True
    return False
