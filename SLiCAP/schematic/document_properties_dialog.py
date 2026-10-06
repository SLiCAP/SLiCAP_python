from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QDoubleSpinBox, QCheckBox,
)
from PySide6.QtCore import Qt

from .schematic_data import DocumentProperties
from .sizing import chars

# (width, height) in mm, portrait for paper; the screen formats are the
# landscape sizes of a poster shown on a display (Anton, 2026-10-06: a
# poster "must have a page format for printing, or displaying").
PAGE_SIZES_MM = {
    "A4": (210.0, 297.0), "A3": (297.0, 420.0), "A2": (420.0, 594.0),
    "A1": (594.0, 841.0), "A0": (841.0, 1189.0),
    "Letter": (215.9, 279.4), "Legal": (215.9, 355.6), "Tabloid": (279.4, 431.8),
    "16:9 screen": (320.0, 180.0), "16:10 screen": (320.0, 200.0),
    "4:3 screen": (320.0, 240.0),
}
DRAWING_SIZE = "Drawing size (no border)"
_PAGE_SIZES = [DRAWING_SIZE] + list(PAGE_SIZES_MM) + ["Custom"]


def page_name_of(width_mm: float, height_mm: float) -> str:
    """The preset name of a page of that size, portrait or landscape, else
    "Custom"."""
    for name, (w, h) in PAGE_SIZES_MM.items():
        if (abs(w - width_mm) < 0.5 and abs(h - height_mm) < 0.5) or \
           (abs(h - width_mm) < 0.5 and abs(w - height_mm) < 0.5):
            return name
    return "Custom"


def page_size_mm(name: str, landscape: bool = False, custom=(210.0, 297.0)) -> tuple:
    """(width, height) in mm of a page size name; *landscape* swaps a paper
    size's sides."""
    w, h = PAGE_SIZES_MM.get(name, tuple(custom))
    if landscape and name in PAGE_SIZES_MM and not name.endswith("screen"):
        w, h = h, w
    return w, h


class DocumentPropertiesDialog(QDialog):
    """Title, author, project and the PAGE of a drawing.

    The page is the border: the export frame is the border when there is
    one, the drawing's extent otherwise, and nothing else ever read a page
    size (a stored page size that the export ignored was the previous
    state, REPLACED 2026-10-06, Anton: "if there is no background, the page
    size must be the drawing size like with schematics"). The dialog shows
    the border's size and sets it: a format creates or resizes the border,
    "Drawing size" removes it. *border_mm* is (width, height) of the
    current border in mm, or None."""

    def __init__(self, props: DocumentProperties, parent=None, border_mm=None,
                 is_poster: bool = False):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Poster properties" if is_poster else "Schematic Properties")
        self._border_mm = border_mm
        self.setMinimumWidth(chars(self, 51))
        layout = QFormLayout(self)
        layout.setRowWrapPolicy(QFormLayout.DontWrapRows)

        self._project = QLineEdit(props.project)
        self._project.setToolTip(
            "SLiCAP project name. Used by sl.initProject() in the generated "
            "main.py that runs the instruction file. Empty → the schematic file "
            "stem is used."
        )
        layout.addRow("Project:", self._project)

        self._title = QLineEdit(props.title)
        layout.addRow("Title:", self._title)

        self._author = QLineEdit(props.author)
        layout.addRow("Author:", self._author)

        self._created = QLineEdit(props.created)
        layout.addRow("Created:", self._created)

        self._modified = QLineEdit(props.last_modified)
        self._modified.setReadOnly(True)
        self._modified.setStyleSheet("color: grey;")
        layout.addRow("Last Modified:", self._modified)

        self._page_size = QComboBox()
        self._page_size.addItems(_PAGE_SIZES)
        if border_mm is None:
            current = DRAWING_SIZE
        else:
            current = page_name_of(*border_mm)
        self._page_size.setCurrentText(current)
        self._page_size.setToolTip(
            "The page is the border: the exported SVG and PDF have its size. "
            "Without a border the export is as large as the drawing.")
        layout.addRow("Page:", self._page_size)

        w0, h0 = border_mm if border_mm is not None else (props.page_width_mm, props.page_height_mm)
        self._width = QDoubleSpinBox()
        self._width.setRange(1.0, 10000.0)
        self._width.setDecimals(1)
        self._width.setSuffix(" mm")
        self._width.setValue(w0)
        layout.addRow("Width:", self._width)

        self._height = QDoubleSpinBox()
        self._height.setRange(1.0, 10000.0)
        self._height.setDecimals(1)
        self._height.setSuffix(" mm")
        self._height.setValue(h0)
        layout.addRow("Height:", self._height)

        self._landscape = QCheckBox("Landscape")
        self._landscape.setChecked(border_mm is not None and border_mm[0] > border_mm[1])
        self._landscape.toggled.connect(lambda *_: self._on_size_changed(self._page_size.currentText()))
        layout.addRow("", self._landscape)

        self._subcircuit = QCheckBox("Save this schematic as a SLiCAP subcircuit (.lib)")
        self._subcircuit.setChecked(props.is_subcircuit)
        self._subcircuit.setToolTip(
            "When checked, File → Save also writes <title>.lib (and on first save "
            "opens the Create Subcircuit dialog to set the node order and parameters)."
        )
        layout.addRow("Subcircuit:", self._subcircuit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._layout = layout
        self._page_size.currentTextChanged.connect(self._on_size_changed)
        self._on_size_changed(self._page_size.currentText())

        self._title.setFocus()

    def _on_size_changed(self, text: str) -> None:
        custom = text == "Custom"
        none = text == DRAWING_SIZE
        self._layout.setRowVisible(self._width,  not none)
        self._layout.setRowVisible(self._height, not none)
        self._layout.setRowVisible(self._landscape, text in PAGE_SIZES_MM and not text.endswith("screen"))
        self._width.setReadOnly(not custom); self._height.setReadOnly(not custom)
        if custom:
            self._width.setFocus()
        elif text in PAGE_SIZES_MM:
            w, h = page_size_mm(text, self._landscape.isChecked())
            self._width.setValue(w); self._height.setValue(h)

    def page_mm(self):
        """(width, height) in mm of the page the user chose, or None for
        "Drawing size": no border."""
        if self._page_size.currentText() == DRAWING_SIZE:
            return None
        return self._width.value(), self._height.value()

    def apply(self, props: DocumentProperties) -> None:
        props.project        = self._project.text().strip()
        props.title          = self._title.text().strip()
        props.author         = self._author.text().strip()
        props.created        = self._created.text().strip()
        page = self.page_mm()
        props.page_size      = self._page_size.currentText()
        props.page_width_mm  = page[0] if page else 0.0
        props.page_height_mm = page[1] if page else 0.0
        props.is_subcircuit  = self._subcircuit.isChecked()
