"""File → Preferences… — application preferences (SLNG.md decision:
one dialog, three entry points: the File menu, each panel's
"Configure view…" context entry, and the panels' "N hidden" footer links).

Panels group:

- Design data panel: checkboxes for the visible object kinds.
- Project panel: a checkable TREE (Anton, 2026-07-11 live check — the
  most flexible model): one item per top-level directory (checked =
  visible; an unchecked directory hides its whole subtree — highest
  precedence), with the file TYPES found inside as checkable children —
  so exclusions are per type PER DIRECTORY (e.g. hide .ini in sch/ but
  not in the project root). The formerly hard-coded hidden machinery
  (__pycache__, *.cache label caches, .pyc, GUI sidecars, build helpers)
  appears in the same tree, default-unchecked, overridable like anything
  else. New file types are visible by default — hiding is an explicit
  user act.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QLabel,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from . import app_prefs
from .design_data import KNOWN_KINDS
from .project_panel import type_key

_KIND_LABELS = {"result":     "SLiCAP / NGspice results",
                "circuit":    "Circuits",
                "figure":     "Figures (plots)",
                "traces":     "Trace dictionaries",
                "expression": "Sympy expressions",
                "matrix":     "Matrices",
                "snippet":    "Report snippets (LaTeX/RST)",
                "number":     "Numbers",
                "array":      "Numpy arrays",
                "list":       "Lists",
                "text":       "Strings",
                "other":      "Other object types"}

_ROOT_LABEL = "(project root files)"
_CACHE_GROUP = "*.cache"


def _tree_key(name: str) -> str:
    """Tree entry for a file: files excluded BY NAME in the defaults
    (make.bat) keep their name so unchecking/checking them matches the
    filter's exclusion entries exactly."""
    if name in app_prefs.DEFAULT_EXCLUDED_TYPES:
        return name
    return type_key(name)


_MAX_DEPTH = 6


def _scan_dir(path: Path, depth: int = 0) -> tuple[dict, set, bool]:
    """Recursive scan: ``(subdirs {name: scan-tuple}, direct file type
    keys, cache-dir-seen)``. Machinery directories controlled globally by
    NAME (__pycache__ at nested levels, *.cache) are not recursed into —
    they stay one global switch; everything else appears per directory so
    subdirectories like tex/SLiCAPdata are individually controllable
    (Anton, 2026-07-11)."""
    subdirs: dict = {}
    types: set[str] = set()
    has_cache = False
    try:
        entries = sorted(os.listdir(path))
    except OSError:
        return subdirs, types, has_cache
    for name in entries:
        if name.startswith('.'):
            continue
        full = path / name
        if full.is_dir():
            if name.endswith(".cache"):
                has_cache = True
            elif name == "__pycache__" and depth > 0:
                pass                     # global switch at top level only
            elif depth < _MAX_DEPTH:
                sub = _scan_dir(full, depth + 1)
                subdirs[name] = sub
                has_cache = has_cache or sub[2]
        else:
            types.add(_tree_key(name))
    return subdirs, types, has_cache


class AppPreferencesDialog(QDialog):
    """Application preferences; call ``apply()`` after ``exec()`` is True."""

    def __init__(self, project_root=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(440)
        lay = QVBoxLayout(self)

        # ── Design data panel: visible object kinds ────────────────────────
        dd = QGroupBox("Design data panel — visible object types")
        grid = QGridLayout(dd)
        visible = set(app_prefs.get_visible_kinds())
        self._kind_boxes: dict[str, QCheckBox] = {}
        for i, kind in enumerate(KNOWN_KINDS):
            cb = QCheckBox(_KIND_LABELS.get(kind, kind))
            cb.setChecked(kind in visible)
            grid.addWidget(cb, i // 2, i % 2)
            self._kind_boxes[kind] = cb
        lay.addWidget(dd)

        # ── Project panel: recursive checkable tree, per-directory types ───
        pp = QGroupBox("Project panel — visible directories && file types")
        pv = QVBoxLayout(pp)
        self._ptree = QTreeWidget()
        self._ptree.setHeaderHidden(True)
        style = self.style()
        from PySide6.QtWidgets import QStyle
        dir_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        view = app_prefs.get_project_view()
        excluded_dirs = view.get("excluded_dirs", [])

        def _add_dir(parent_add, name: str, rel: str, scan) -> QTreeWidgetItem:
            """Directory item (folder icon, AutoTristate) with its DIRECT
            file types and its subdirectories as children, recursively."""
            subdirs, types, _ = scan
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("dir", rel))
            item.setIcon(0, dir_icon)
            if rel == "":
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)   # root: types only
            else:
                # AutoTristate (Anton): unchecking a directory clears its
                # whole subtree; checking a child sets the branch above it.
                item.setFlags(Qt.ItemFlag.ItemIsEnabled
                              | Qt.ItemFlag.ItemIsUserCheckable
                              | Qt.ItemFlag.ItemIsAutoTristate)
            for t in sorted(types):
                child = QTreeWidgetItem([t])
                child.setData(0, Qt.ItemDataRole.UserRole, ("type", rel, t))
                child.setFlags(Qt.ItemFlag.ItemIsEnabled
                               | Qt.ItemFlag.ItemIsUserCheckable)
                item.addChild(child)
            parent_add(item)
            for sub in sorted(subdirs):
                _add_dir(item.addChild, sub,
                         f"{rel}/{sub}" if rel else sub, subdirs[sub])
            return item

        def _set_states(item: QTreeWidgetItem) -> None:
            """Top-down, AFTER insertion (tristate propagation is live).
            The directory's own state comes FIRST — an AutoTristate parent
            without children (empty directory) would otherwise never get a
            check state and render without a checkbox; an excluded
            directory then clears its subtree."""
            role = item.data(0, Qt.ItemDataRole.UserRole)
            rel = role[1]
            if rel != "":
                item.setCheckState(0, Qt.CheckState.Checked)
            excl = app_prefs.excluded_types_for(view, rel)
            for j in range(item.childCount()):
                child = item.child(j)
                crole = child.data(0, Qt.ItemDataRole.UserRole)
                if crole[0] == "type":
                    child.setCheckState(
                        0, Qt.CheckState.Unchecked
                        if crole[2] in excl else Qt.CheckState.Checked)
                else:
                    _set_states(child)
            if rel != "" and app_prefs.dir_excluded(
                    rel.rsplit("/", 1)[-1],
                    excluded_dirs, rel):
                item.setCheckState(0, Qt.CheckState.Unchecked)

        if project_root is not None:
            subdirs, root_types, has_cache = _scan_dir(Path(project_root))
            root_item = _add_dir(self._ptree.addTopLevelItem, _ROOT_LABEL,
                                 "", ({}, root_types, False))
            root_item.setExpanded(True)
            tops = [root_item]
            for name in sorted(subdirs):
                tops.append(_add_dir(self._ptree.addTopLevelItem, name,
                                     name, subdirs[name]))
            for t in tops:
                _set_states(t)
            if has_cache or app_prefs.dir_excluded(
                    "x.cache", excluded_dirs):
                grp = QTreeWidgetItem(
                    [f"{_CACHE_GROUP}  (LaTeX label caches)"])
                grp.setData(0, Qt.ItemDataRole.UserRole,
                            ("dir", _CACHE_GROUP))
                grp.setFlags(Qt.ItemFlag.ItemIsEnabled
                             | Qt.ItemFlag.ItemIsUserCheckable)
                grp.setCheckState(
                    0, Qt.CheckState.Unchecked
                    if app_prefs.dir_excluded("x.cache", excluded_dirs)
                    else Qt.CheckState.Checked)
                self._ptree.addTopLevelItem(grp)
        else:
            self._ptree.setEnabled(False)
            pv.addWidget(QLabel("Open a project to configure its view."))
        pv.addWidget(self._ptree)
        note = QLabel("Checked = visible, per directory. Unchecking a "
                      "directory clears its whole subtree; checking a file "
                      "type automatically enables its directory.")
        note.setWordWrap(True)
        pv.addWidget(note)
        lay.addWidget(pp)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        self._had_project = project_root is not None

    def apply(self) -> None:
        """Persist the choices to the user ini (~/SLiCAP_gui.ini)."""
        app_prefs.set_visible_kinds(
            [k for k, cb in self._kind_boxes.items() if cb.isChecked()])
        if not self._had_project:
            return
        excluded_dirs: list[str] = []
        types: dict[str, list[str]] = {}
        represented: set[str] = set()

        def _collect(item) -> None:
            role = item.data(0, Qt.ItemDataRole.UserRole)
            if not role or role[0] != "dir":
                return
            rel = role[1]
            represented.add(rel)
            unchecked = (item.flags() & Qt.ItemFlag.ItemIsUserCheckable
                         and item.checkState(0) == Qt.CheckState.Unchecked)
            if rel == _CACHE_GROUP:
                if unchecked:
                    excluded_dirs.append(_CACHE_GROUP)
                return
            if rel != "" and unchecked:
                excluded_dirs.append(rel)
            unchecked_types: list[str] = []
            for j in range(item.childCount()):
                child = item.child(j)
                crole = child.data(0, Qt.ItemDataRole.UserRole)
                if crole and crole[0] == "type":
                    if child.checkState(0) == Qt.CheckState.Unchecked:
                        unchecked_types.append(crole[2])
                else:
                    _collect(child)            # nested directory
            types[rel] = unchecked_types

        for i in range(self._ptree.topLevelItemCount()):
            _collect(self._ptree.topLevelItem(i))
        # Exclusions with no tree representation (e.g. __pycache__ when the
        # project has none YET) must survive the save — dropping them would
        # silently un-hide future machinery.
        excluded_dirs += [e for e in
                          app_prefs.get_project_view()["excluded_dirs"]
                          if e not in represented
                          and e not in excluded_dirs]
        app_prefs.set_project_view({"excluded_dirs": excluded_dirs,
                                    "types": types})
