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
# The stored name of a drawing without a border. The word "page" survives
# in the stored keys (page_size, page_width_mm): a record of the border's
# size, never a second source (see DocumentPropertiesDialog).
DRAWING_SIZE = "Drawing size (no border)"
CUSTOM       = "Custom"
# The free side of a one-sided format gets this fraction of the fixed side
# when there is no border to take its size from: the proportion of a
# typical figure.
FREE_SIDE_RATIO = 0.75


def border_formats(presets=None) -> dict:
    """name -> (width_mm, height_mm), a side None = free: the paper and
    screen formats (both sides fixed), then the user's presets of the
    style ([border_presets], Preferences). A preset of the same name as a
    built-in format replaces it."""
    out = {n: (w, h) for n, (w, h) in PAGE_SIZES_MM.items()}
    out.update(presets or {})
    return out


def is_paper(name: str) -> bool:
    """A built-in paper format: the only kind with a landscape variant."""
    return name in PAGE_SIZES_MM and not name.endswith("screen")


def page_name_of(width_mm: float, height_mm: float, fixed=(True, True),
                 presets=None) -> str:
    """The format name of a border of that size with those fixed sides,
    portrait or landscape for paper, else "Custom". A one-sided preset
    matches on its fixed side when the other side is free."""
    def same(a, b):
        return abs(a - b) < 0.5
    fw, fh = fixed
    for name, (w, h) in border_formats(presets).items():
        if w is not None and h is not None:
            if fw and fh and (same(w, width_mm) and same(h, height_mm) or
                              is_paper(name) and same(h, width_mm) and same(w, height_mm)):
                return name
        elif w is not None:
            if fw and not fh and same(w, width_mm):
                return name
        elif fh and not fw and same(h, height_mm):
            return name
    return CUSTOM


def resolve_format(formats: dict, name: str, landscape: bool = False,
                   current=None) -> tuple:
    """The border a format name stands for: (width_mm, height_mm, fixed_w,
    fixed_h). *landscape* swaps the sides of a paper format. A free side
    keeps the size of *current* ((width, height) of the present border),
    or gets FREE_SIDE_RATIO of the fixed side."""
    if name not in formats:
        raise ValueError(f"unknown border format '{name}'")
    w, h = formats[name]
    if landscape and is_paper(name):
        w, h = h, w
    if w is None:
        w = current[0] if current else h / FREE_SIDE_RATIO
    if h is None:
        h = current[1] if current else w * FREE_SIDE_RATIO
    fw, fh = formats[name][0] is not None, formats[name][1] is not None
    if landscape and is_paper(name):
        fw, fh = fh, fw
    return w, h, fw, fh


class BorderFormatFields:
    """The Border rows of a form: the format, width, height and landscape.
    One implementation for the document properties dialog and the New
    poster dialog. *border* is (width, height) in mm of the present border
    or None, *fixed* its fixed sides. border_mm() is the user's choice:
    None for no border, else (width, height, fixed_w, fixed_h)."""

    def __init__(self, form: QFormLayout, presets=None, border=None,
                 fixed=(True, True), size_mm=(210.0, 297.0)):
        self._form    = form
        self._formats = border_formats(presets)
        self._border  = border
        self.combo = QComboBox()
        self.combo.addItems([DRAWING_SIZE] + list(self._formats) + [CUSTOM])
        self.combo.setToolTip(
            "The border is the export frame: the exported SVG and PDF have "
            "its size. Without a border the export is as large as the "
            "drawing. Formats of your own: Preferences, Border formats.")
        self.width  = self._spin()
        self.height = self._spin()
        w0, h0 = border if border is not None else size_mm
        self.width.setValue(w0); self.height.setValue(h0)
        self.landscape = QCheckBox("Landscape")
        self.landscape.setChecked(border is not None and border[0] > border[1])
        form.addRow("Border:", self.combo)
        form.addRow("Width:",  self.width)
        form.addRow("Height:", self.height)
        form.addRow("",        self.landscape)
        current = (DRAWING_SIZE if border is None
                   else page_name_of(*border, fixed=fixed, presets=presets))
        self.combo.setCurrentText(current)
        self.combo.currentTextChanged.connect(self._on_changed)
        self.landscape.toggled.connect(
            lambda *_: self._on_changed(self.combo.currentText()))
        self._on_changed(current)

    @staticmethod
    def _spin() -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(1.0, 10000.0)
        sb.setDecimals(1)
        sb.setSuffix(" mm")
        return sb

    def _on_changed(self, text: str) -> None:
        none, custom = text == DRAWING_SIZE, text == CUSTOM
        self._form.setRowVisible(self.width,  not none)
        self._form.setRowVisible(self.height, not none)
        self._form.setRowVisible(self.landscape, is_paper(text))
        if text in self._formats:
            w, h, fw, fh = resolve_format(self._formats, text,
                                          self.landscape.isChecked(), self._border)
            self.width.setValue(w); self.height.setValue(h)
            self.width.setReadOnly(fw); self.height.setReadOnly(fh)
        else:
            self.width.setReadOnly(not custom); self.height.setReadOnly(not custom)
        if custom:
            self.width.setFocus()

    def border_mm(self):
        text = self.combo.currentText()
        if text == DRAWING_SIZE:
            return None
        fw = fh = True
        if text in self._formats:
            w, h = self._formats[text]
            fw, fh = w is not None, h is not None
            if self.landscape.isChecked() and is_paper(text):
                fw, fh = fh, fw
        return self.width.value(), self.height.value(), fw, fh


class DocumentPropertiesDialog(QDialog):
    """Title, author, project and the BORDER of a drawing.

    The border is the export frame: the export is the border when there is
    one, the drawing's extent otherwise, and nothing else ever read a page
    size (a stored page size that the export ignored was the previous
    state, REPLACED 2026-10-06, Anton: "if there is no background, the page
    size must be the drawing size like with schematics"). The dialog shows
    the border's size and sets it: a format creates or resizes the border,
    "Drawing size" removes it. The formats are the paper and screen sizes
    and the user's presets, which may fix one side only (Anton,
    2026-10-09: a book figure has the column width and a free height).
    *border_mm* is (width, height) of the current border in mm, or None;
    *fixed* its fixed sides; *presets* the style's BORDER_PRESETS."""

    def __init__(self, props: DocumentProperties, parent=None, border_mm=None,
                 is_poster: bool = False, fixed=(True, True), presets=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Poster properties" if is_poster else "Schematic Properties")
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

        size0 = ((props.page_width_mm, props.page_height_mm)
                 if props.page_width_mm >= 1.0 and props.page_height_mm >= 1.0
                 else (210.0, 297.0))
        self._format = BorderFormatFields(layout, presets, border_mm, fixed, size0)

        self._subcircuit = QCheckBox("Save this schematic as a SLiCAP subcircuit (.lib)")
        self._subcircuit.setChecked(props.is_subcircuit)
        self._subcircuit.setToolTip(
            "When checked, File → Save writes the package <title>.*_sch + "
            "<title>.*_lib to lib/. The Create Subcircuit dialog opens on the "
            "first save and when a new port appears (node order, parameters). "
            "File → Save as… always opens it, with the name editable."
        )
        layout.addRow("Subcircuit:", self._subcircuit)
        layout.setRowVisible(self._subcircuit, not is_poster)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self._title.setFocus()

    def border_mm(self):
        """None for "Drawing size" (no border), else (width, height,
        fixed_w, fixed_h) of the border the user chose."""
        return self._format.border_mm()

    def apply(self, props: DocumentProperties) -> None:
        props.project        = self._project.text().strip()
        props.title          = self._title.text().strip()
        props.author         = self._author.text().strip()
        props.created        = self._created.text().strip()
        border = self.border_mm()
        props.page_size      = self._format.combo.currentText()
        props.page_width_mm  = border[0] if border else 0.0
        props.page_height_mm = border[1] if border else 0.0
        props.is_subcircuit  = self._subcircuit.isChecked()
