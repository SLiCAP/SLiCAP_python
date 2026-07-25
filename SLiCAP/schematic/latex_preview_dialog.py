"""
Modal "LaTeX preview" shown by the Place flow of the Circuit-parameters and
Model-definition dialogs (Anton, 2026-07-12): the rendered table with a Close
button (back to editing) and an OK button (accept and place).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter

_MAX_W = 700
_MAX_H = 500


class LatexPreviewDialog(QDialog):
    """Shows a rendered LaTeX SVG (or the render error).  OK is offered only
    when there is something to place."""

    def __init__(self, svg_bytes: bytes | None, error: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("LaTeX preview")

        outer = QVBoxLayout(self)

        body = QLabel()
        body.setAlignment(Qt.AlignCenter)
        body.setStyleSheet("background: white; padding: 6px;")
        if svg_bytes:
            px = self._render_pixmap(svg_bytes)
            if px is not None:
                body.setPixmap(px)
            else:
                body.setText("(invalid SVG)")
                svg_bytes = None
        else:
            body.setText(f"Render failed:\n{error}" if error else "(nothing rendered)")

        scroll = QScrollArea()
        scroll.setWidget(body)
        scroll.setWidgetResizable(True)
        scroll.setMinimumSize(min(_MAX_W, 360), min(_MAX_H, 160))
        outer.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Ok).setEnabled(svg_bytes is not None)
        outer.addWidget(buttons)

    @staticmethod
    def _render_pixmap(svg_bytes: bytes) -> "QPixmap | None":
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if not renderer.isValid():
            return None
        vb = renderer.viewBoxF()
        sw = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
        sh = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
        if sw <= 0 or sh <= 0:
            return None
        scale = min(_MAX_W / sw, _MAX_H / sh, 3.0)
        px = QPixmap(max(1, int(sw * scale)), max(1, int(sh * scale)))
        px.fill(Qt.white)
        p = QPainter(px)
        renderer.render(p)
        p.end()
        return px
