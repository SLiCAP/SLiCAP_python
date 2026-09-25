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
