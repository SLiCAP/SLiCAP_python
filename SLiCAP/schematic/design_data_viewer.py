"""Viewers for Design data panel entries (SLNG.md: roadmap item 2 — the
expressions/tables Viewer — delivered as the panel's double-click actions).

Everything shown here comes from the run manifest (design_data.py): the
LaTeX string rendered via the same pdflatex pipeline as the schematic
labels, the pprint text as fallback, trace labels for figures/trace dicts.
Copy buttons put the LaTeX math string / the pprint text on the clipboard
— the starting point of the export-snippet function.
"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QUrl, QTimer
from PySide6.QtGui import QDesktopServices, QFont, QPainter
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
    QVBoxLayout,
)


_DISPLAY_ENV = re.compile(
    r"\\begin\{(equation\*?|displaymath|align\*?|gather\*?)\}"
    r"(.*?)\\end\{\1\}", re.S)


def _last_lines(text: str, n: int = 6) -> str:
    """The last *n* non-empty lines of a build log, for an error label."""
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(lines[-n:])


def _display_env_to_natural(code: str) -> str:
    """Preview normalization for snippets that consist of ONE display-math
    environment (ltx.eqn output): display math is set on a full-linewidth
    line, which blows the varwidth page up to the 500cm cap — the formula
    became a speck in a giant page (LPCltx, Anton 2026-07-12).  The math
    content is previewed as a natural-width box instead; \\label{} is
    dropped (a standalone preview has no meaningful numbering anyway).
    Only the PREVIEW is transformed — the snippet text stays untouched.
    Tables and mixed snippets pass through unchanged."""
    m = _DISPLAY_ENV.fullmatch(code.strip())
    if not m:
        return code
    body = re.sub(r"\\label\{[^}]*\}", "", m.group(2)).strip()
    env = m.group(1)
    if env.startswith("align"):
        return r"$\displaystyle \begin{aligned}" + body + r"\end{aligned}$"
    if env.startswith("gather"):
        return r"$\displaystyle \begin{gathered}" + body + r"\end{gathered}$"
    return r"$\displaystyle " + body + r"$"


class _SvgZoomView(QGraphicsView):
    """Scalable vector viewer (Anton, 2026-07-12: for presentations):
    mouse wheel zooms about the cursor, dragging pans, and the SVG stays
    crisp at any magnification. Opens fitted to the window."""

    def __init__(self, svg_bytes: bytes, parent=None):
        super().__init__(parent)
        self._renderer = QSvgRenderer(QByteArray(svg_bytes))  # keep alive
        item = QGraphicsSvgItem()
        item.setSharedRenderer(self._renderer)
        scene = QGraphicsScene(self)
        scene.addItem(item)
        self.setScene(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing
                            | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._fitted = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._fitted:
            self._fitted = True
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        step = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(step, step)

_KIND_TITLES = {"result": "SLiCAP / NGspice result", "circuit": "Circuit",
                "figure": "Figure", "traces": "Trace dictionary",
                "expression": "Expression", "matrix": "Matrix",
                "snippet": "Report snippet", "number": "Number",
                "list": "List", "array": "Array", "text": "String"}


def open_figure(entry: dict, panel) -> None:
    """Open a figure entry's saved image with the desktop viewer — plots
    are always saved to the img folder, so no object is needed."""
    root = getattr(panel, "_project_root", None)
    if root is None:
        return
    img_dir = Path(root) / "img"
    name = entry.get("fileName", "")
    for suffix in (".svg", "." + entry.get("fileType", "svg"), ".pdf"):
        path = img_dir / f"{name}{suffix}"
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            return
    QMessageBox.information(
        panel, "Open image",
        f"No saved image found for figure “{name}” in {img_dir}.\n"
        "Run the instruction file to (re)create it.")


def show_viewer(entry: dict, panel) -> None:
    """Open the viewer as a FREE-FLOATING, non-modal window (Anton,
    2026-07-12): GNOME glues modal dialogs centered onto their parent
    ("attach modal dialogs"), which covered the information being read.
    Non-modal also means several viewers can be open side by side."""
    dlg = DesignDataViewer(entry, parent=panel)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()


class DesignDataViewer(QDialog):
    """Read-only viewer for one manifest entry: rendered LaTeX when
    available (same pipeline as the schematic labels), pprint text as
    fallback, plus kind-specific information and copy buttons."""

    _preview_seq = 0                        # unique-URL counter for RST previews

    def __init__(self, entry: dict, parent=None):
        # Qt.Window: a real top-level window (own titlebar, freely movable
        # and resizable) instead of a parent-glued dialog.
        super().__init__(parent, Qt.WindowType.Window)
        self._project_root = getattr(parent, "_project_root", None)
        kind = entry.get("kind", "other")
        name = entry.get("name", "?")
        self.setWindowTitle(f"{name}  —  {_KIND_TITLES.get(kind, kind)}")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)

        info = []
        for key, label in (("dataType", "dataType"), ("gainType", "gainType"),
                           ("detLabel", "detector"), ("simType", "simType")):
            if entry.get(key):
                info.append(f"{label}: {entry[key]}")
        if entry.get("step"):
            info.append("stepped")
        if kind == "figure":
            info.append(f'file: {entry.get("fileName", "")}')
        if kind == "array":
            info.append(f'shape: {entry.get("shape")}, '
                        f'dtype: {entry.get("dtype")}')
        if kind == "trace":
            # what the trace plots, in the words it was built with
            info.append(f'{entry.get("y", "y")} vs {entry.get("x", "x")}')
            if entry.get("value"):
                info.append(entry["value"])
        if info:
            head = QLabel("   ".join(info))
            head.setWordWrap(True)
            lay.addWidget(head)

        if kind == "circuit":
            if entry.get("title"):
                info.append(f'title: {entry["title"]}')
            if entry.get("value"):
                info.append(entry["value"])
            if entry.get("errors"):
                info.append(f'errors: {entry["errors"]}')

        rendered = False
        self._render_error = ""
        latex = entry.get("latex", "")
        if entry.get("sections"):
            # A circuit is not ONE table: element data, parameter
            # definitions and undefined parameters are shown in sequence,
            # each typeset when LaTeX is available and as plain text
            # otherwise (Anton, 2026-08-16).
            rendered = self._add_sections(lay, entry)
        elif latex:
            rendered = self._add_latex(lay, latex)
        elif kind == "snippet" and entry.get("format") == "latex" \
                and entry.get("value"):
            # LaTeX report snippets compile to their TYPESET form (a pz
            # table renders as the actual table — Anton, 2026-07-12),
            # using the project preamble for the formatter's macros/colors.
            preamble = ""
            root = getattr(parent, "_project_root", None)
            if root is not None:
                p = Path(root) / "tex" / "preambuleSLiCAP.tex"
                if p.is_file():
                    preamble = str(p)
            rendered = self._add_latex(lay, entry["value"], raw=True,
                                       preamble=preamble)
        elif kind == "snippet" and entry.get("format") == "rst" \
                and entry.get("value"):
            # RST renders in the web browser — a real browser loads MathJax,
            # which the embedded file:// view cannot (Anton, 2026-07-16). Like
            # the LaTeX preview it never shows the source: the window is just a
            # note + the actions, and the browser preview opens automatically.
            note = QLabel("The rendered preview opens in your web browser.")
            note.setWordWrap(True)
            lay.addWidget(note)
            lay.addStretch(1)
            rendered = True
            QTimer.singleShot(0, lambda: self._preview_in_browser(entry))
        if not rendered:
            if self._render_error:
                # never fall back SILENTLY — say why the typeset preview
                # is missing (Anton, 2026-07-12)
                err = QLabel(f"LaTeX preview failed: {self._render_error}")
                err.setWordWrap(True)
                err.setStyleSheet("color: #a04000;")
                lay.addWidget(err)
            text = (entry.get("pprint") or entry.get("value")
                    or "\n".join(entry.get("traces", [])
                                 or entry.get("labels", [])))
            if text:
                view = QPlainTextEdit(str(text))
                view.setReadOnly(True)
                mono = QFont("Monospace")
                mono.setStyleHint(QFont.StyleHint.Monospace)
                view.setFont(mono)
                lay.addWidget(view, 1)
        elif kind in ("figure", "traces"):
            labels = entry.get("traces") or entry.get("labels") or []
            if labels:
                lbl = QLabel("traces: " + ", ".join(labels))
                lbl.setWordWrap(True)
                lay.addWidget(lbl)

        btns = QHBoxLayout()
        if kind == "snippet" and entry.get("value"):
            b = QPushButton("Save to SLiCAPdata")
            b.setToolTip("Save into the project's snippets folder "
                         "(tex/SLiCAPdata for LaTeX) so a report imports "
                         "it with \\input{…} and stays up-to-date with "
                         "every run.")
            b.clicked.connect(lambda: self._save_snippet(entry))
            btns.addWidget(b)
            b = QPushButton("Copy snippet")
            b.clicked.connect(
                lambda: QApplication.clipboard().setText(entry["value"]))
            btns.addWidget(b)
            if entry.get("format") == "rst":
                b = QPushButton("Open preview in browser")
                b.setToolTip("Render the snippet with Sphinx in the project's "
                             "style and open it in your web browser.")
                b.clicked.connect(lambda: self._preview_in_browser(entry))
                btns.addWidget(b)
        if latex:
            b = QPushButton("Copy LaTeX")
            b.clicked.connect(
                lambda: QApplication.clipboard().setText(latex))
            btns.addWidget(b)
        if entry.get("pprint"):
            b = QPushButton("Copy pprint")
            b.clicked.connect(
                lambda: QApplication.clipboard().setText(entry["pprint"]))
            btns.addWidget(b)
        if entry.get("srepr"):
            b = QPushButton("Copy srepr")
            b.clicked.connect(
                lambda: QApplication.clipboard().setText(entry["srepr"]))
            btns.addWidget(b)
        btns.addStretch()
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        btns.addWidget(close)
        lay.addLayout(btns)

    def _save_snippet(self, entry: dict) -> None:
        """Save the snippet under its variable name via Snippet.save() —
        the same folders the formatters use, so \\input in a report picks
        it up (Anton, 2026-07-12: keeps design documents up-to-date)."""
        try:
            from SLiCAP.SLiCAPprotos import Snippet
            import SLiCAP.SLiCAPconfigure as ini
            name = entry.get("name", "snippet")
            fmt = entry.get("format") or None
            Snippet(entry["value"], format=fmt).save(name)
            folder = {"latex": ini.tex_snippets,
                      "rst": ini.rst_snippets}.get(fmt, "")
            QMessageBox.information(
                self, "Save snippet",
                f"Saved as “{name}” in {folder or 'the project folder'}.")
        except Exception as exc:
            QMessageBox.warning(self, "Save snippet",
                                f"Could not save the snippet:\n{exc}")

    def _add_sections(self, lay, entry: dict) -> bool:
        """Render the entry's tables one below the other, each with its
        heading: typeset when LaTeX is available, plain text otherwise.
        Returns True when at least one section produced content."""
        from PySide6.QtWidgets import QPlainTextEdit
        preamble = ""
        root = self._project_root
        if root is not None:
            p = Path(root) / "tex" / "preambuleSLiCAP.tex"
            if p.is_file():
                preamble = str(p)
        shown = False
        for sec in entry["sections"]:
            head = QLabel(f'<b>{sec.get("title", "")}</b>')
            lay.addWidget(head)
            done = False
            if sec.get("latex"):
                done = self._add_latex(lay, sec["latex"], raw=True,
                                       preamble=preamble)
            if not done:
                text = sec.get("text") or "(none)"
                view = QPlainTextEdit(text)
                view.setReadOnly(True)
                view.setFont(QFont("Monospace"))
                lay.addWidget(view, 1)
            shown = True
        return shown

    def _add_latex(self, lay, latex: str, raw: bool = False,
                   preamble: str = "") -> bool:
        """Render LaTeX with the label pipeline; False → caller falls back
        to the pprint/source text. *raw* renders the code verbatim (report
        snippets: tables, equations with labels); otherwise the string is
        treated as math and wrapped in a display environment."""
        # Not schematic-bound: only the system fact gates rendering here —
        # per-schematic latex preferences do not apply to the data viewer.
        from .latex_label import LATEX_INSTALLED, render_latex_raw
        if not LATEX_INSTALLED:
            self._render_error = "pdflatex/dvisvgm not installed"
            return False
        # math renders as a natural-width box (NOT \[…\]: display math is
        # set to the full line width, so wide matrices were clipped at the
        # page edge — the missing right bracket, Anton 2026-07-12); the
        # huge varwidth cap lets the page grow to the content.
        code = _display_env_to_natural(latex) if raw else (
            r"$\displaystyle " + latex + r"$")
        try:
            svg, err = render_latex_raw(code, preamble, max_width="500cm")
        except Exception as exc:
            self._render_error = str(exc)
            return False
        if not svg:
            self._render_error = err or "unknown LaTeX error"
            return False
        probe = QSvgRenderer(QByteArray(svg))
        if not probe.isValid() or probe.viewBoxF().height() <= 0:
            self._render_error = "invalid SVG from the LaTeX pipeline"
            return False
        vb = probe.viewBoxF()
        view = _SvgZoomView(svg)
        # sensible opening size; the content then zooms/pans freely
        view.setMinimumHeight(min(max(int(vb.height() * 1.6) + 24, 120),
                                  420))
        lay.addWidget(view, 1)
        return True

    def _preview_in_browser(self, entry: dict) -> None:
        """Render the RST snippet with Sphinx (the project's style when it has a
        ``sphinx/source/conf.py``) and open the page in the default web browser
        — where MathJax loads, unlike the embedded file:// view."""
        import webbrowser
        from SLiCAP.SLiCAPrst import snippet2html
        sphinx_source = None
        if self._project_root is not None:
            cand = Path(self._project_root) / "sphinx" / "source"
            if (cand / "conf.py").is_file():
                sphinx_source = str(cand)
        # Build UNDER the user's home, not /tmp: a snap-packaged browser (the
        # default Firefox/Chromium on Ubuntu) is confined and cannot open a
        # file:// URL in /tmp — only non-hidden files under $HOME (Anton,
        # 2026-07-16). The project's sphinx/build is the natural spot.
        if self._project_root is not None:
            workdir = str(Path(self._project_root) / "sphinx" / "build"
                          / "slicap_preview")
        else:
            workdir = str(Path.home() / "SLiCAP_preview")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            html, log = snippet2html(entry["value"],
                                     name=entry.get("name", "snippet"),
                                     sphinx_source=sphinx_source,
                                     workdir=workdir)
        except Exception as exc:
            html, log = None, str(exc)
        finally:
            QApplication.restoreOverrideCursor()
        if not html:
            QMessageBox.warning(self, "Preview snippet",
                                "Could not render the snippet:\n\n"
                                + (_last_lines(log) or "Sphinx build failed"))
            return
        # open_new_tab + a unique fragment so a previously-opened (possibly
        # stale) tab for the same file is not merely re-focused without reload.
        DesignDataViewer._preview_seq += 1
        webbrowser.open_new_tab(
            Path(html).as_uri() + f"#v{DesignDataViewer._preview_seq}")
