"""Widget widths from the font, not from pixels.

The dialogs used to size their fields with pixel literals (``setFixedWidth(65)``
for a spin box, 130 for a font combo, 120 for a name field).  Those numbers
were read off a Linux desktop; on Windows the spin-box arrows are wider and
the default font differs, so two-digit font sizes and "Times New Roman" were
cut off in the schematic preferences (Anton, 2026-09-25).

Two tools replace every literal:

- :func:`fit_contents` keeps a spin box, combo or button at its own size
  hint, which Qt derives from the font, the widest value or item and the
  platform's arrow section.  A width the widget computes itself is right on
  every platform; a literal is right on one.
- :func:`chars` turns a width in DIGITS into pixels of the widget's font, for
  text fields whose width is a design decision ("room for 16 characters")
  rather than a property of the contents.

Pixel literals for widget widths were the previous approach and are
REJECTED (2026-09-25): they do not survive a change of platform or font.
"""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QSizePolicy, QStyle, QWidget

# The share of the screen a dialog opens on at most; beyond it the body
# scrolls (fit_to_screen).
SCREEN_WIDTH_SHARE = 0.95
SCREEN_HEIGHT_SHARE = 0.9

# The "name" width of the instruction dialogs: variable and parameter names,
# table columns that hold them.  Interactive columns start at this width; the
# user can drag them wider.
NAME_CHARS = 16


def chars(widget: QWidget, n: int) -> int:
    """Pixels for *n* digit widths in *widget*'s font, plus its frame."""
    fm = widget.fontMetrics()
    frame = widget.style().pixelMetric(QStyle.PM_DefaultFrameWidth, None, widget)
    return int(round(fm.horizontalAdvance("0") * n)) + 2 * frame + 8


def cap_chars(widget: QWidget, n: int) -> None:
    """Let *widget* grow to at most *n* digit widths (``setMaximumWidth``)."""
    widget.setMaximumWidth(chars(widget, n))


def fix_chars(widget: QWidget, n: int) -> None:
    """Hold *widget* at exactly *n* digit widths (``setFixedWidth``)."""
    widget.setFixedWidth(chars(widget, n))


def name_width(widget: QWidget) -> int:
    """The shared name-field width, in *widget*'s font (NAME_CHARS)."""
    return chars(widget, NAME_CHARS)


def fit_contents(widget: QWidget) -> None:
    """Hold *widget* at its own size hint horizontally.

    For a combo box the hint follows the longest item (AdjustToContents);
    for a spin box Qt already sizes it to its widest value plus the arrows;
    for a button, to its text.
    """
    if isinstance(widget, QComboBox):
        widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    policy = widget.sizePolicy()
    policy.setHorizontalPolicy(QSizePolicy.Policy.Fixed)
    widget.setSizePolicy(policy)


def scroll_body(dialog: QWidget) -> tuple:
    """The layouts of a dialog whose body can be taller than a small screen:
    ``(foot, body, scroll)``. *body* lies in the scroll area *scroll*, with
    the margins of a normal dialog; the caller adds its buttons to *foot*,
    below the scroll area, so they stay on the screen whatever the body
    holds. The scroll area reaches the edges of the window: when it does
    not scroll, the dialog looks as one without it. Size the dialog at the
    end of its construction with :func:`fit_to_screen`.

    The pattern of the NGspice instruction dialog, made one function for
    every large dialog (workshop of 2026-11-17: the drawing preferences
    needed 1120 pixels of height, and their OK button was off the screen
    of a laptop). Two ways of fitting existed, in that dialog and in the
    SLiCAP instruction dialog; both use this one now."""
    from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout
    frame = QVBoxLayout(dialog)
    frame.setContentsMargins(0, 0, 0, 0)
    frame.setSpacing(0)
    scroll = QScrollArea(dialog)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    content = QWidget()
    body = QVBoxLayout(content)          # the style's margins, as a dialog's own
    scroll.setWidget(content)
    frame.addWidget(scroll, 1)
    foot = QVBoxLayout()
    style = dialog.style()
    foot.setContentsMargins(
        style.pixelMetric(QStyle.PixelMetric.PM_LayoutLeftMargin, None, dialog), 0,
        style.pixelMetric(QStyle.PixelMetric.PM_LayoutRightMargin, None, dialog),
        style.pixelMetric(QStyle.PixelMetric.PM_LayoutBottomMargin, None, dialog))
    frame.addLayout(foot)
    return foot, body, scroll


def _screen_of(dialog: QWidget):
    """The screen *dialog* opens on: that of its parent's window, over which
    it opens, else the primary screen. ``dialog.screen()`` of the dialog
    itself, not shown yet, was the first form and was REPLACED
    (2026-11-20): with it, a dialog constructed after a series of such
    dialogs crashed in its own constructor (the suite: test_bias_annotation
    after test_axes_dialog; the primary screen in its place, nothing else
    changed, removed the crash)."""
    from PySide6.QtGui import QGuiApplication
    parent = dialog.parentWidget()
    handle = parent.window().windowHandle() if parent is not None else None
    if handle is not None:
        return handle.screen()
    return QGuiApplication.primaryScreen()


def fit_to_screen(dialog: QWidget, scroll, width: "int | None" = None,
                  extra_height: int = 0) -> None:
    """Open *dialog*, built with :func:`scroll_body`, at the size that shows
    its whole body and the rest of its layout, but at most
    SCREEN_WIDTH_SHARE of the width and SCREEN_HEIGHT_SHARE of the height
    of its screen: beyond that the body scrolls and the buttons stay
    visible. *width* replaces the natural width (the NGspice instruction
    dialog keeps its tabs from widening it); *extra_height* adds to the
    natural height (table rows that would otherwise scroll)."""
    from PySide6.QtGui import QGuiApplication
    # the rest of the layout, the buttons below the body: the layout's own
    # size hint less that of the scroll area
    natural = scroll.widget().sizeHint()
    whole = dialog.layout().sizeHint()
    w = max(natural.width(), whole.width())
    h = natural.height() + extra_height + whole.height() - scroll.sizeHint().height()
    if width is not None:
        w = width
    screen = _screen_of(dialog)
    if screen is not None:
        available = screen.availableGeometry()
        if h > int(available.height() * SCREEN_HEIGHT_SHARE):
            h = int(available.height() * SCREEN_HEIGHT_SHARE)
            # the body scrolls: room for the vertical scroll bar
            w += dialog.style().pixelMetric(QStyle.PM_ScrollBarExtent, None, dialog)
        w = min(w, int(available.width() * SCREEN_WIDTH_SHARE))
    dialog.resize(max(w, dialog.minimumWidth()), h)

