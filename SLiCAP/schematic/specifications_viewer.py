"""Specification viewer (SLNG.md FINAL SPEC part C, 2026-07-15).

Reads a spec CSV (``csv2specs``), groups by specType, and shows one table
per type — rendered through the same pdflatex→SVG pipeline as the report
(``ltx.specs`` + latex_label.render_latex_raw), so the viewer tables look
exactly like the LaTeX report. Falls back to a native Qt table per type
when no LaTeX toolchain is present.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from .design_data_viewer import _SvgZoomView   # shared wheel-zoom + pan view


def read_spec_types(specs) -> list:
    """Distinct specTypes in first-appearance order (== CSV order)."""
    seen, out = set(), []
    for s in specs:
        t = s.specType or "(no type)"
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _render_all_types_svg(specs, types):
    """One SVG with all per-specType tables stacked (a heading + table per
    type) — a single image so the viewer zooms/pans exactly like the other
    LaTeX previews (Anton, 2026-07-15). Returns None when LaTeX is absent
    or the render fails."""
    try:
        import SLiCAP as sl
        import SLiCAP.SLiCAPconfigure as ini
        from .latex_label import render_latex_raw
        ltx = sl.LaTeXformatter()
        preamble = os.path.join(ini.latex_files, "preambuleSLiCAP.tex")
        has_preamble = os.path.isfile(preamble)
        color = "myyellow" if has_preamble else None
        parts = []
        for t in types:
            heading = t.replace("_", r"\_")
            parts.append(r"\noindent\textbf{" + heading
                         + r" specification}\par\smallskip")
            parts.append(ltx.specs(specs, t, color=color).snippet)  # tabular
            parts.append(r"\par\bigskip")
        svg, _err = render_latex_raw(
            "\n".join(parts),
            preamble_path=preamble if has_preamble else "",
            max_width="50cm")
        return svg
    except Exception:
        return None


def _qt_table(specs, spectype) -> QTableWidget:
    """Native fallback table for one specType."""
    import sympy as sp
    rows = [s for s in specs if (s.specType or "(no type)") == spectype]
    t = QTableWidget(len(rows), 4)
    t.setHorizontalHeaderLabels(["Name", "Description", "Value", "Units"])
    t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    for r, s in enumerate(rows):
        val = "" if s.value == "" else str(sp.N(s.value, 4))
        for c, txt in enumerate((str(s.symbol), s.description, val, s.units)):
            t.setItem(r, c, QTableWidgetItem(txt))
    t.resizeColumnsToContents()
    h = t.horizontalHeader().height() + sum(
        t.rowHeight(r) for r in range(len(rows))) + 4
    t.setMaximumHeight(max(h, 60))
    return t


class SpecificationsViewer(QDialog):
    """Read-only, per-specType tables for one spec CSV.

    When *reload_fn* and *watch_path* are given, the viewer watches the CSV
    on disk and rebuilds itself whenever it changes — so saving in the
    editor, or a running design-step script appending specs, updates the
    tables live (Anton, 2026-07-16: watch the design table "grow" during a
    run). Reuses the settings-watcher pattern (debounce + re-arm)."""

    def __init__(self, specs, title="Specifications", reload_fn=None,
                 watch_path="", only_type="", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(title)
        self.resize(640, 520)
        self._reload_fn = reload_fn
        self._only_type = only_type          # "" = all types stacked
        self._content = None
        self._outer = QVBoxLayout(self)
        self._build_content(specs)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        self._outer.addWidget(buttons)

        if reload_fn and watch_path:
            self._setup_watch(watch_path)

    def _build_content(self, specs):
        """(Re)build the central widget from a fresh specs list."""
        if self._content is not None:
            self._outer.removeWidget(self._content)
            self._content.deleteLater()
            self._content = None
        types = read_spec_types(specs)
        if self._only_type:                  # single-type view (panel child)
            types = [t for t in types if t == self._only_type]
        svg = _render_all_types_svg(specs, types) if types else None
        if svg:
            # one zoomable/pannable image — same view as the other LaTeX
            # previews (wheel zooms, drag pans, fits on open)
            widget = _SvgZoomView(svg)
        else:
            # LaTeX unavailable: stacked native Qt tables in a scroll area
            inner = QWidget()
            vlay = QVBoxLayout(inner)
            if not types:
                vlay.addWidget(
                    QLabel("This file contains no specifications."))
            for spectype in types:
                head = QLabel(f"{spectype} specification")
                head.setStyleSheet("font-weight: bold; margin-top: 8px;")
                vlay.addWidget(head)
                vlay.addWidget(_qt_table(specs, spectype))
            vlay.addStretch(1)
            widget = QScrollArea()
            widget.setWidgetResizable(True)
            widget.setWidget(inner)
        self._outer.insertWidget(0, widget, 1)   # above the button box
        self._content = widget

    # ── live update (watch the CSV on disk) ──────────────────────────────

    def _setup_watch(self, path):
        from PySide6.QtCore import QFileSystemWatcher, QTimer
        self._watch_path = str(path)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._reload)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_change)
        self._watcher.directoryChanged.connect(self._on_change)
        self._arm_watch()

    def _arm_watch(self):
        # editors/scripts replace the file (write + rename), which drops it
        # from the watcher — re-add the file and its directory each time
        paths = self._watcher.files() + self._watcher.directories()
        if paths:
            self._watcher.removePaths(paths)
        if os.path.isfile(self._watch_path):
            self._watcher.addPath(self._watch_path)
        d = os.path.dirname(self._watch_path)
        if os.path.isdir(d):
            self._watcher.addPath(d)

    def _on_change(self, *_):
        self._timer.start(300)                    # debounce write+rename

    def _reload(self):
        self._arm_watch()
        try:
            specs = self._reload_fn()
        except Exception:
            return                                # transient mid-write state
        self._build_content(specs)


def _spec_reader(path):
    """A closure that reads *path*'s specs fresh each call — the viewer uses
    it both to build and to live-reload. csv2specs handles files in the
    project csv/ dir; anything else is parsed directly."""
    import SLiCAP as sl
    import SLiCAP.SLiCAPconfigure as ini
    from .specifications_dialog import _read_specs_any

    def read():
        abspath = os.path.abspath(path)
        in_csv_dir = os.path.dirname(abspath).endswith(
            os.path.normpath(ini.csv_path))
        try:
            return (sl.csv2specs(os.path.basename(path)) if in_csv_dir
                    else _read_specs_any(path))
        except Exception:
            return _read_specs_any(path)
    return read


def open_spec_file(path, spectype="", parent=None):
    """Open the viewer for a spec CSV; *spectype* restricts it to one type
    (the panel opens one type per sub-item, Anton 2026-07-16), "" shows all
    types stacked. Live-updates while the CSV changes on disk."""
    read = _spec_reader(path)
    title = os.path.basename(path)
    if spectype:
        title += f" — {spectype}"
    dlg = SpecificationsViewer(read(), title=title, reload_fn=read,
                               watch_path=str(path), only_type=spectype,
                               parent=parent)
    return dlg
