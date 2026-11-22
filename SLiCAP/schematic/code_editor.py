"""Plain-text panes with one zoom: the code boxes, with line numbers in a
gutter on the left, and the log pane (workshop of 2026-11-17: "add line
numbers in the instruction pane", "enable font zooming in the instruction
pane, the log pane already has").

The zoom is this module's own: Ctrl+wheel, Ctrl+plus (or Ctrl+=),
Ctrl+minus, and Ctrl+0 back to the default size. Qt zooms a text box on
Ctrl+wheel by itself only while it is read-only, without keys, and it
forgets the size: that was the zoom of the log pane until 2026-11-20
(Anton: "In the log window it only works with the scroll wheel"). The size
of each kind of pane is kept in the user's GUI preferences
(``app_prefs.get_font_size``): one size for the code boxes (the
instruction pane, the LaTeX fragment dialog and the filter design dialog
of a system diagram), one for the log pane.

One wheel notch is an angle of 120 eighths of a degree. A fine wheel or a
touchpad sends parts of a notch, which add up until they make a whole
step. Rounding every wheel event on its own was REPLACED on 2026-11-20:
small steps up were lost and small steps down became whole ones (eight
steps of 15, one notch, zoomed in by 0 and out by 8 points).

A code box hands out its text as written (``CodeEditor.text``). One line
of the text is one block of the document, so the line numbers in the
gutter are the line numbers of Python and pdflatex (2026-11-22).
"""
from __future__ import annotations

from PySide6.QtCore import QMimeData, QRect, QSize, Qt
from PySide6.QtGui import QFont, QKeyEvent, QKeySequence, QPainter
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from . import app_prefs

DEFAULT_SIZE = 10            # points, the code boxes
LOG_SIZE = 9                 # points, the log pane
MIN_SIZE, MAX_SIZE = 6, 40
_NOTCH = 120                 # the angleDelta of one wheel notch


def mono_font(size: int) -> QFont:
    """The monospace font of the text panes at *size* points."""
    font = QFont("Monospace")
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(size)
    return font


class ZoomText(QPlainTextEdit):
    """A QPlainTextEdit with the zoom of every text pane. *pane* names the
    size it keeps in the preferences ("code" or "log"); *default* is the
    size of a first start and of Ctrl+0."""

    def __init__(self, text: str = "", parent=None, pane: str = "code",
                 default: int = DEFAULT_SIZE):
        super().__init__(text, parent)
        self._pane = pane
        self._default = default
        self._wheel = 0              # the part of a notch not zoomed yet
        self.setFont(mono_font(app_prefs.get_font_size(pane, default)))

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._wheel += event.angleDelta().y()
            steps = int(self._wheel / _NOTCH)             # toward zero
            if steps:
                self._wheel -= steps * _NOTCH
                self.set_font_size(self.font().pointSize() + steps)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event) -> None:
        ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        if event.matches(QKeySequence.StandardKey.ZoomIn) or (
                ctrl and event.key() == Qt.Key.Key_Equal):
            self.set_font_size(self.font().pointSize() + 1)
        elif event.matches(QKeySequence.StandardKey.ZoomOut):
            self.set_font_size(self.font().pointSize() - 1)
        elif ctrl and event.key() == Qt.Key.Key_0:
            self.set_font_size(self._default)
        else:
            super().keyPressEvent(event)

    def set_font_size(self, size: int) -> None:
        """Show the text at *size* points, within MIN_SIZE and MAX_SIZE,
        and keep the size for every pane of this kind."""
        size = max(MIN_SIZE, min(MAX_SIZE, int(size)))
        self.setFont(mono_font(size))
        app_prefs.set_font_size(self._pane, size)


class _Gutter(QWidget):
    """The strip with the line numbers; the editor paints it."""

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_gutter(event)


class CodeEditor(ZoomText):
    """A text pane for code: the zoom of ZoomText, line numbers, and the
    text as written (``text``)."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent, pane="code", default=DEFAULT_SIZE)
        self._gutter = _Gutter(self)
        self.blockCountChanged.connect(self._fit_gutter)
        self.updateRequest.connect(self._scroll_gutter)
        self._fit_gutter()

    # ── the text: as written, one line per block ──────────────────────────

    def text(self) -> str:
        """The characters as written, with a block break as "\\n". Every
        reader of the code takes the text here.

        toPlainText() was the accessor until 2026-11-22 and was REPLACED
        that day. It is an export for display. It writes a line separator
        (U+2028) as a newline and a no-break space (U+00A0) as a space.
        Save then rewrote characters the user never touched. A string
        with a U+2028 stopped compiling.

        A paragraph separator (U+2029) read from a file cannot be kept.
        It is the block break of the document, so it comes back as "\\n".
        Qt does the same with U+FDD0 and U+FDD1. It drops a byte-order
        mark (U+FEFF) at the start of the text."""
        return self.document().toRawText().replace("\N{PARAGRAPH SEPARATOR}", "\n")

    def keyPressEvent(self, event) -> None:
        """A key that Qt binds to a line separator (Shift+Return,
        Shift+Enter) acts as Return. Python has no soft line break.
        Until 2026-11-22 Qt put a U+2028 inside the block. The gutter
        then showed one line where Python counted two."""
        if event.matches(QKeySequence.StandardKey.InsertLineSeparator):
            enter = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return,
                              Qt.KeyboardModifier.NoModifier, "\r")
            super().keyPressEvent(enter)
            event.setAccepted(enter.isAccepted())
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source) -> None:
        """Paste and drop: a line separator (U+2028) comes in as a line
        break and a no-break space (U+00A0) as a space. Text copied from
        a web page or a PDF carries them, and Python refuses both outside
        a string. Characters read from a file stay as they are. Qt's own
        paste then makes the change one undo step.

        A paste kept exactly as copied was considered and REJECTED on
        2026-11-22. Code pasted with a no-break space then stopped with a
        Python error, where it ran before."""
        if source.hasText():
            text = source.text()
            plain = (text.replace("\N{LINE SEPARATOR}", "\n")
                         .replace("\N{NO-BREAK SPACE}", " "))
            if plain != text:
                source = QMimeData()
                source.setText(plain)
        super().insertFromMimeData(source)

    # ── line numbers ──────────────────────────────────────────────────────

    def gutter_width(self) -> int:
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digits

    def _fit_gutter(self, *_) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _scroll_gutter(self, rect, dy) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._fit_gutter()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def paint_gutter(self, event) -> None:
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), self.palette().window())
        painter.setPen(self.palette().placeholderText().color())
        painter.setFont(self.font())
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, top, self._gutter.width() - 4, height,
                                 Qt.AlignmentFlag.AlignRight, str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1
        painter.end()

    # ── zoom: ZoomText's, the gutter follows the font ───────────────────────

    def set_font_size(self, size: int) -> None:
        super().set_font_size(size)
        self._fit_gutter()
