"""
Dialog for placing or editing a LaTeX fragment on the schematic canvas.
"""
from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QPlainTextEdit, QSpinBox, QDialogButtonBox,
    QFileDialog, QApplication, QLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter


def _find_slicap_preamble() -> str:
    try:
        import importlib
        sl = importlib.import_module("SLiCAP")
        install_path = getattr(getattr(sl, "ini", None), "install_path", None)
        if install_path:
            c = Path(install_path) / "tex" / "preambuleSLiCAP.tex"
            if c.exists():
                return str(c)
    except Exception:
        pass
    ini = Path.home() / "SLiCAP.ini"
    if ini.exists():
        try:
            cfg = configparser.ConfigParser()
            cfg.read(str(ini))
            install_path = cfg.get("install", "installpath", fallback="")
            if install_path:
                c = Path(install_path) / "tex" / "preambuleSLiCAP.tex"
                if c.exists():
                    return str(c)
        except Exception:
            pass
    return ""


class LatexFragmentDialog(QDialog):
    _PREVIEW_MAX_W = 500
    _PREVIEW_MAX_H = 250

    def __init__(self, latex_code: str = "",
                 preamble_path: str = "",
                 svg_bytes: bytes | None = None,
                 display_width: int | None = None,
                 display_height: int | None = None,
                 parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("LaTeX Fragment")
        self.setMinimumWidth(560)
        self._svg_bytes: bytes | None = svg_bytes
        self._natural_w: int | None = None
        self._natural_h: int | None = None

        outer = QVBoxLayout(self)
        outer.setSizeConstraint(QLayout.SetMinimumSize)

        # ── preamble row ──────────────────────────────────────────────────────
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preamble:"))
        self._preamble_edit = QLineEdit(preamble_path or _find_slicap_preamble())
        self._preamble_edit.setReadOnly(True)
        self._preamble_edit.setPlaceholderText("(default: amsmath + amssymb)")
        self._preamble_edit.setMinimumWidth(280)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_preamble)
        clear_btn  = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_preamble)
        prow.addWidget(self._preamble_edit, stretch=1)
        prow.addWidget(browse_btn)
        prow.addWidget(clear_btn)
        outer.addLayout(prow)

        # ── code editor ───────────────────────────────────────────────────────
        mono = QFont("Courier New", 10)
        mono.setStyleHint(QFont.Monospace)
        self._code_edit = QPlainTextEdit()
        self._code_edit.setFont(mono)
        self._code_edit.setMinimumHeight(130)
        self._code_edit.setPlainText(latex_code)
        outer.addWidget(self._code_edit)

        # ── preview button + status ───────────────────────────────────────────
        prev_row = QHBoxLayout()
        self._prev_btn = QPushButton("Preview")
        self._prev_btn.clicked.connect(self._render)
        self._status_lbl = QLabel("")
        self._status_lbl.setWordWrap(True)
        prev_row.addWidget(self._prev_btn)
        prev_row.addWidget(self._status_lbl, stretch=1)
        outer.addLayout(prev_row)

        # ── preview area ──────────────────────────────────────────────────────
        self._preview_lbl = QLabel("(click Preview to render)")
        self._preview_lbl.setAlignment(Qt.AlignCenter)
        self._preview_lbl.setMinimumHeight(120)
        self._preview_lbl.setStyleSheet(
            "border: 1px solid #999; background: white; padding: 4px;"
        )
        outer.addWidget(self._preview_lbl)

        # ── scale row ─────────────────────────────────────────────────────────
        from .config import SCALE_LATEX_FRAGMENT
        if svg_bytes:
            self._compute_natural_size(svg_bytes)
        if self._natural_w and display_width:
            init_scale = max(1, round(display_width / self._natural_w * 100))
        else:
            init_scale = SCALE_LATEX_FRAGMENT

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        self._scale_spin = QSpinBox()
        self._scale_spin.setRange(1, 500)
        self._scale_spin.setValue(init_scale)
        self._scale_spin.setSuffix(" %")
        scale_row.addWidget(self._scale_spin)
        scale_row.addSpacing(16)
        self._size_lbl = QLabel()
        scale_row.addWidget(self._size_lbl)
        scale_row.addSpacing(10)
        grid_hint = QLabel("(1 grid square = 5 units,  resistor pin-to-pin = 50 units)")
        grid_hint.setStyleSheet("color: grey; font-size: 9pt;")
        scale_row.addWidget(grid_hint)
        scale_row.addStretch(1)
        outer.addLayout(scale_row)

        # ── OK / Cancel ───────────────────────────────────────────────────────
        self._btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self._btn_box.accepted.connect(self.accept)
        self._btn_box.rejected.connect(self.reject)
        self._ok_btn = self._btn_box.button(QDialogButtonBox.Ok)
        self._ok_btn.setEnabled(svg_bytes is not None)
        outer.addWidget(self._btn_box)

        self._scale_spin.valueChanged.connect(self._on_scale_changed)
        self._update_size_labels()

        self._code_edit.textChanged.connect(self._mark_dirty)

        if svg_bytes:
            self._show_svg(svg_bytes)
            self._status_lbl.setText("Ready.")

    # ── slots ─────────────────────────────────────────────────────────────────

    def _mark_dirty(self) -> None:
        self._ok_btn.setEnabled(False)

    def _browse_preamble(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Preamble File",
            self._preamble_edit.text() or str(Path.home()),
            "LaTeX Files (*.tex);;All Files (*)",
        )
        if path:
            self._preamble_edit.setText(path)
            self._mark_dirty()

    def _clear_preamble(self) -> None:
        self._preamble_edit.clear()
        self._mark_dirty()

    def _render(self) -> None:
        from .latex_label import render_latex_raw
        code     = self._code_edit.toPlainText()
        preamble = self._preamble_edit.text()
        self._prev_btn.setEnabled(False)
        self._status_lbl.setText("Rendering…")
        QApplication.processEvents()
        svg_bytes, error = render_latex_raw(code, preamble)
        self._prev_btn.setEnabled(True)
        if svg_bytes:
            self._svg_bytes = svg_bytes
            self._status_lbl.setText("OK")
            self._show_svg(svg_bytes)
            self._compute_natural_size(svg_bytes)
            self._update_size_labels()
            self._ok_btn.setEnabled(True)
        else:
            self._svg_bytes = None
            self._status_lbl.setText(f"Error: {error}")
            self._preview_lbl.setText("(render failed)")
            self._ok_btn.setEnabled(False)

    def _show_svg(self, svg_bytes: bytes) -> None:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if not renderer.isValid():
            self._preview_lbl.setText("(invalid SVG)")
            return
        vb = renderer.viewBoxF()
        sw = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
        sh = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
        if sw <= 0 or sh <= 0:
            self._preview_lbl.setText("(empty SVG)")
            return
        scale = min(self._PREVIEW_MAX_W / sw, self._PREVIEW_MAX_H / sh, 3.0)
        pw, ph = max(1, int(sw * scale)), max(1, int(sh * scale))
        px = QPixmap(pw, ph)
        px.fill(Qt.white)
        p = QPainter(px)
        renderer.render(p)
        p.end()
        self._preview_lbl.setPixmap(px)

    def _compute_natural_size(self, svg_bytes: bytes) -> None:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        from .latex_label import svg_line_height
        from .config import COMP_LABEL_FONT_SIZE
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if not renderer.isValid():
            return
        vb = renderer.viewBoxF()
        svg_w = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
        svg_h = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
        if svg_w <= 0 or svg_h <= 0:
            return
        ref_h = svg_line_height()
        base = (COMP_LABEL_FONT_SIZE / ref_h) if (ref_h and ref_h > 0) else 0.5
        self._natural_w = max(1, round(svg_w * base))
        self._natural_h = max(1, round(svg_h * base))

    def _on_scale_changed(self, _: int) -> None:
        self._update_size_labels()

    def _update_size_labels(self) -> None:
        if self._natural_w and self._natural_h:
            pct = self._scale_spin.value()
            w = max(1, round(self._natural_w * pct / 100))
            h = max(1, round(self._natural_h * pct / 100))
            self._size_lbl.setText(f"Width: {w} units   Height: {h} units")
        else:
            self._size_lbl.setText("Width: — units   Height: — units")

    # ── result accessors ──────────────────────────────────────────────────────

    def latex_code(self) -> str:
        return self._code_edit.toPlainText()

    def preamble_path(self) -> str:
        return self._preamble_edit.text()

    def svg_bytes(self) -> bytes | None:
        return self._svg_bytes

    def display_width(self) -> int:
        if self._natural_w:
            return max(1, round(self._natural_w * self._scale_spin.value() / 100))
        return 200

    def display_height(self) -> int:
        if self._natural_h:
            return max(1, round(self._natural_h * self._scale_spin.value() / 100))
        return 100
