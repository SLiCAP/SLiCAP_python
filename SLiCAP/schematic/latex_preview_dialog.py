"""
Modal "LaTeX preview" shown by the Place flow of the Circuit-parameters and
Model-definition dialogs (Anton, 2026-07-12): the rendered table with a Close
button (back to editing) and an OK button (accept and place).

The table is data for the netlist; its picture is cosmetic. A render that
fails therefore never blocks: OK places the table as plain text, with the
error in its tooltip (``confirm_render``, the one rule of both dialogs).
OK disabled on a failed render was the first form and was REPLACED
(Anton, 2026-11-20, workshop: a MiKTeX that misses a package made placing
a parameter table impossible, while editing one offered "accept anyway").
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
    """Shows a rendered LaTeX SVG, or the render error. OK places; after a
    failed render it reads "Place as plain text"."""

    def __init__(self, svg_bytes: bytes | None, error: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("LaTeX preview")

        outer = QVBoxLayout(self)

        body = QLabel()
        body.setAlignment(Qt.AlignCenter)
        from .config import canvas_background
        body.setStyleSheet(f"background: {canvas_background().name()}; padding: 6px;")
        if svg_bytes:
            px = self._render_pixmap(svg_bytes)
            if px is not None:
                body.setPixmap(px)
            else:
                body.setText("(invalid SVG)")
                svg_bytes = None
        else:
            body.setText((f"Render failed:\n{error}" if error else "(nothing rendered)")
                         + "\n\nThe canvas shows the table as plain text.")

        scroll = QScrollArea()
        scroll.setWidget(body)
        scroll.setWidgetResizable(True)
        scroll.setMinimumSize(min(_MAX_W, 360), min(_MAX_H, 160))
        outer.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if svg_bytes is None:
            buttons.button(QDialogButtonBox.Ok).setText("Place as plain text")
        self._buttons = buttons
        outer.addWidget(buttons)

    @staticmethod
    def _render_pixmap(svg_bytes: bytes) -> "QPixmap | None":
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        from .config import canvas_background
        from .latex_label import display_svg
        renderer = QSvgRenderer(QByteArray(display_svg(svg_bytes)))
        if not renderer.isValid():
            return None
        vb = renderer.viewBoxF()
        sw = vb.width()  if vb.width()  > 0 else renderer.defaultSize().width()
        sh = vb.height() if vb.height() > 0 else renderer.defaultSize().height()
        if sw <= 0 or sh <= 0:
            return None
        scale = min(_MAX_W / sw, _MAX_H / sh, 3.0)
        px = QPixmap(max(1, int(sw * scale)), max(1, int(sh * scale)))
        px.fill(canvas_background())
        p = QPainter(px)
        renderer.render(p)
        p.end()
        return px


def confirm_render(parent, latex, preamble, what, placing) -> bool:
    """Render the LaTeX of a table block (circuit parameters, a model
    definition) and let the user confirm it: True to accept. *placing*:
    the Place flow, which shows the preview; OK places, also after a
    failed render (plain text). Otherwise a failed render asks whether to
    accept anyway, as the canvas then shows plain text. *what* names the
    table in the question, "The parameter table"."""
    from PySide6.QtWidgets import QApplication, QMessageBox
    from .latex_label import render_latex_raw
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        svg, error = render_latex_raw(latex, preamble)
    finally:
        QApplication.restoreOverrideCursor()
    if placing:
        return bool(LatexPreviewDialog(svg, error, parent).exec())
    if svg is not None:
        return True
    return QMessageBox.warning(
        parent, "LaTeX error",
        "%s does not compile:\n\n%s\n\nAccept anyway? (The canvas shows "
        "plain text.)" % (what, error),
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

