"""Design data panel (SLNG.md "Design data panel", 2026-07-11).

Right-side dock (mirroring the Project panel on the left) listing the
variables of the executed instruction files with their runtime type, read
from the run manifest ``results/design_data.json`` — the panel never
executes anything and never holds state of its own (ACDE: files are the
source of truth, this is a viewer over a rebuildable index).

- Shows ONLY what was run in THIS session (Anton, 2026-07-11): the
  manifest on disk may hold sections from earlier sessions, but those
  objects are not "available" — the panel stays empty on project open and
  a section appears once its script has been run (any script, not
  necessarily the project's main one; ``mark_run()``).
- One top-level item per instruction file (the manifest section); greyed
  when the current file no longer hashes to the recorded run (stale).
- Variables filtered by the object kinds enabled in the preferences; a
  footer counts what is hidden and links to the Preferences dialog —
  nothing silently disappears.
- Double-click actions: the per-kind ACTION registry maps a kind to
  (label, callback(entry, panel)) pairs; double-click runs the first
  action, the context menu offers the rest. The default viewers live in
  design_data_viewer.py: figures open their saved image, everything else
  opens the read-only viewer (rendered LaTeX with pprint fallback, copy
  LaTeX/pprint/srepr).
- Empty before the first run (spec decision 4).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QFileSystemWatcher, Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QHeaderView, QLabel, QMenu, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from . import app_prefs
from .design_data import (MANIFEST_NAME, read_manifest,
                          section_is_stale, filter_kind)

# Per-kind action registry: kind → [(label, callback(entry, panel)), …].
# Double-click = first action; context menu = all of them. The default
# viewers (design_data_viewer.py — roadmap item 2) are registered below;
# imports are lazy so the panel stays cheap to import.
ACTIONS: dict[str, list[tuple[str, Callable[[dict, object], None]]]] = {}


def _act_open_figure(entry, panel):
    from .design_data_viewer import open_figure
    open_figure(entry, panel)


def _act_view(entry, panel):
    from .design_data_viewer import show_viewer
    show_viewer(entry, panel)


def _act_open_spectype(entry, panel):
    from .specifications_viewer import open_spec_file
    dlg = open_spec_file(entry.get("path", ""), entry.get("spectype", ""),
                         parent=panel)
    if dlg is not None:
        dlg.show()


ACTIONS.update({
    "figure":     [("Open image", _act_open_figure),
                   ("View info", _act_view)],
    "result":     [("View", _act_view)],
    "expression": [("View", _act_view)],
    "matrix":     [("View", _act_view)],
    "circuit":    [("View", _act_view)],
    "traces":     [("View trace labels", _act_view)],
    "trace":      [("View", _act_view)],
    "measurements": [("View", _act_view)],
    "measurement":  [("View", _act_view)],
    "snippet":    [("View", _act_view)],
    "number":     [("View", _act_view)],
    "text":       [("View", _act_view)],
    "array":      [("View", _act_view)],
    "list":       [("View", _act_view)],
    # one clickable sub-item per specType (Anton, 2026-07-16); the CSV-file
    # node is just an expandable container
    "spectype":   [("View specification table", _act_open_spectype)],
})

_SPEC_HEADER = "symbol"           # first column of a SLiCAP spec CSV


def find_spec_csvs(csv_dir: Path) -> list:
    """Spec CSV files in *csv_dir*, header-sniffed (first column 'symbol')
    so ordinary data CSVs (NGspice etc.) are not listed. Sorted by name."""
    out = []
    if not csv_dir.is_dir():
        return out
    for p in sorted(csv_dir.glob("*.csv")):
        try:
            with open(p) as f:
                header = f.readline()
        except OSError:
            continue
        cols = [c.strip().lower() for c in header.split(",")]
        if cols[:1] == [_SPEC_HEADER]:
            out.append(p)
    return out


def spec_types_of(path) -> list:
    """Distinct specTypes in a spec CSV, in first-appearance (CSV) order —
    the type column, read cheaply without a full sympy parse. Same field
    split as csv2specs (descriptions escape their commas as &#44;)."""
    types = []
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return types
    for line in lines[1:]:                     # skip the header
        parts = line.rstrip("\n").split(",")
        if len(parts) >= 5 and parts[0].strip():
            t = parts[4].strip() or "(no type)"
            if t not in types:
                types.append(t)
    return types


class DesignDataPanel(QDockWidget):
    """Variables of the executed instruction files, from the run manifest."""

    configure_requested = Signal()      # footer link / context "Configure…"

    def __init__(self, parent=None):
        super().__init__("Design data", parent)
        self.setObjectName("design_data_panel")
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Variable", "Type"])
        # The NAME is what is read; the type is one short word ("measurement"
        # is the longest). So the type column takes only what it needs and
        # the variable column gets the rest (Anton, 2026-08-03) - before this
        # the two shared the width and names came out as "VampQs…".
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        self._tree.setRootIsDecorated(True)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        lay.addWidget(self._tree)
        self._footer = QLabel("")
        self._footer.setContentsMargins(6, 2, 6, 2)
        # word wrap: without it the footer text width becomes the dock's
        # MINIMUM width and the panel cannot be narrowed (Anton, live)
        self._footer.setWordWrap(True)
        self._footer.linkActivated.connect(
            lambda *_: self.configure_requested.emit())
        self._footer.hide()
        lay.addWidget(self._footer)
        self.setWidget(body)
        self._project_root: Path | None = None
        self._session_sources: set[str] = set()
        # The manifest is written the moment the SCRIPT finishes, but the
        # runner process stays alive while show=True figures are open —
        # waiting for process exit would leave the panel empty until the
        # user closes every plot (Anton, live 2026-07-11). Watch the
        # manifest instead; the window decides whether an active run makes
        # a section available (session semantics stay intact).
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_fs_change)
        self._watcher.directoryChanged.connect(self._on_fs_change)

    manifest_updated = Signal()

    # ── refresh ────────────────────────────────────────────────────────────

    def set_project_root(self, root) -> None:
        """Switching (or opening) a project resets the session: nothing has
        run yet, so nothing is available to show."""
        self._project_root = Path(root) if root else None
        self._session_sources.clear()
        self._rearm_watcher()
        self.refresh()

    def _rearm_watcher(self) -> None:
        # the atomic write REPLACES the manifest file, which drops it from
        # the watcher — re-add after every change
        paths = self._watcher.files() + self._watcher.directories()
        if paths:
            self._watcher.removePaths(paths)
        if self._project_root is None:
            return
        rdir = self._project_root / "results"
        if rdir.is_dir():
            self._watcher.addPath(str(rdir))
            mf = rdir / MANIFEST_NAME
            if mf.exists():
                self._watcher.addPath(str(mf))
        # specs are read LIVE from csv/ (created without a run, updated by
        # external design-step scripts — SLNG.md FINAL SPEC part B); watch
        # the directory (new/removed files) + each spec file (edits)
        cdir = self._project_root / "csv"
        if cdir.is_dir():
            self._watcher.addPath(str(cdir))
            for p in find_spec_csvs(cdir):
                self._watcher.addPath(str(p))

    def _on_fs_change(self, *_args) -> None:
        self._rearm_watcher()
        self.manifest_updated.emit()
        self.refresh()

    def mark_run(self, source_name: str) -> None:
        """Record that *source_name* (e.g. "GUItest.py") was run in this
        session — its manifest section becomes visible."""
        self._session_sources.add(source_name)
        self.refresh()

    def refresh(self) -> None:
        """Rebuild from the manifest and the current view preferences."""
        self._tree.clear()
        self._footer.hide()
        if self._project_root is None:
            return
        # Specifications: live from csv/, independent of any run (part B).
        self._add_specifications_node()
        if not self._session_sources:
            return
        manifest = read_manifest(self._project_root / "results")
        visible = set(app_prefs.get_visible_kinds())
        hidden_vars = 0
        hidden_kinds: set[str] = set()
        for source, section in sorted(manifest["sections"].items()):
            if source not in self._session_sources:
                continue
            top = QTreeWidgetItem([source, ""])
            stale = section_is_stale(section, self._project_root / source)
            if stale:
                top.setToolTip(0, "The instruction file changed since this "
                                  "run — results may be outdated. Run again "
                                  "to refresh.")
            shown = 0
            for entry in section.get("variables", []):
                kind = entry.get("kind", "other")
                if filter_kind(kind) not in visible:
                    hidden_vars += 1
                    hidden_kinds.add(kind)
                    continue
                label = kind if kind != "other" else entry.get("class", kind)
                item = QTreeWidgetItem([entry.get("name", "?"), label])
                item.setData(0, Qt.ItemDataRole.UserRole, entry)
                if stale:
                    item.setForeground(0, Qt.GlobalColor.gray)
                    item.setForeground(1, Qt.GlobalColor.gray)
                # results expand into their return-value attributes
                # (poles, zeros, DCvalue, matrices, … — Anton 2026-07-12);
                # children are part of the result, not kind-filtered
                self._add_children(item, entry, stale)
                top.addChild(item)
                shown += 1
            if stale:
                top.setForeground(0, Qt.GlobalColor.gray)
                top.setText(1, "(stale)")
            if shown or stale:
                self._tree.addTopLevelItem(top)
                top.setExpanded(True)
        if hidden_vars:
            self._footer.setText(
                f'{hidden_vars} variable{"s" if hidden_vars != 1 else ""} '
                f'hidden ({len(hidden_kinds)} type'
                f'{"s" if len(hidden_kinds) != 1 else ""} not in the view '
                f'preferences) — <a href="prefs">configure…</a>')
            self._footer.show()

    def _add_specifications_node(self) -> None:
        """Top-level 'Specifications' node → one expandable node per spec CSV
        → one clickable child per specType (Anton, 2026-07-16). The file node
        is a container (not viewable); double-click a type child opens the
        single-type table viewer. Rebuilt on every refresh, so the type
        children track the CSV live (a script adding a new type grows a new
        child)."""
        spec_files = find_spec_csvs(self._project_root / "csv")
        if not spec_files:
            return
        top = QTreeWidgetItem(["Specifications", ""])
        for p in spec_files:
            file_item = QTreeWidgetItem([p.name, ""])   # container, no entry
            for t in spec_types_of(p):
                entry = {"kind": "spectype", "name": t,
                         "path": str(p), "spectype": t}
                child = QTreeWidgetItem([t, "specification table"])
                child.setData(0, Qt.ItemDataRole.UserRole, entry)
                file_item.addChild(child)
            top.addChild(file_item)
            file_item.setExpanded(True)
        self._tree.addTopLevelItem(top)
        top.setExpanded(True)

    def _add_children(self, item: QTreeWidgetItem, entry: dict,
                      stale: bool) -> None:
        """Attach an entry's attributes, and THEIR attributes, recursively.

        A trace dictionary holds traces and a trace holds its xData and yData
        (Anton, 2026-07-31: "clicking on the xData or yData attribute should
        show the array - then we can really check if the trace is ready for
        plotting"), so one level of children is not enough.
        """
        for attr in entry.get("attributes", []):
            child = QTreeWidgetItem(
                [attr.get("name", "?"), attr.get("kind", "")])
            child.setData(0, Qt.ItemDataRole.UserRole, attr)
            if stale:
                child.setForeground(0, Qt.GlobalColor.gray)
                child.setForeground(1, Qt.GlobalColor.gray)
            item.addChild(child)
            self._add_children(child, attr, stale)

    # ── actions (prepared mechanism; registry ships empty) ─────────────────

    @staticmethod
    def _entry_of(item: QTreeWidgetItem) -> dict | None:
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def _on_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        entry = self._entry_of(item)
        if entry:
            actions = ACTIONS.get(entry.get("kind", ""), [])
            if actions:
                actions[0][1](entry, self)

    def _on_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        entry = self._entry_of(item)
        menu = QMenu(self)
        if entry:
            for label, cb in ACTIONS.get(entry.get("kind", ""), []):
                menu.addAction(label, lambda cb=cb: cb(entry, self))
            if not menu.isEmpty():
                menu.addSeparator()
        menu.addAction("Configure view…",
                       lambda: self.configure_requested.emit())
        menu.exec(self._tree.viewport().mapToGlobal(pos))
