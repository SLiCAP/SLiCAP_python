"""
Posters: drawings that show other drawings (Anton, 2026-10-06).

A poster is a canvas file, posters/<name>.slicap_poster, without a circuit:
it is never netlisted. It holds text, shapes, LaTeX, images and the links
of the Place menu - schematics and other posters of the project, figures
and snippets of the Design data - and its export to img/<name>.svg and .pdf
first brings the exports of the drawings it shows up to date (children
before parents, see schematic.make_schematic). In a browser a click on a
shown drawing opens that drawing's own export. A poster that would contain
itself, directly or through a chain, is refused (provenance.poster_contains).

The poster source lives in posters/, beside the schematics in sch/, never
in img/ with the exports: it is an edited input (considered and REJECTED:
"the poster is an image itself, I would place it in img/").
"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel, QMessageBox,
)

from .document_properties_dialog import (
    DRAWING_SIZE, CUSTOM, BorderFormatFields, border_formats, resolve_format,
    page_name_of)
from .sizing import chars


def create_poster(root, name: str, fmt="A4", landscape: bool = False,
                  title: str = "", author: str = "", style=None) -> Path:
    """Write posters/<name>.slicap_poster and return the path.

    *fmt* is the border: a format name (paper, screen, or a preset of the
    style's [border_presets]), with *landscape* for paper; a tuple
    (width_mm, height_mm, fixed_w, fixed_h); or None / DRAWING_SIZE for a
    poster without a border, whose export is as large as the drawing
    (Anton, 2026-10-09: a poster for a book figure has no page). The
    border has the look of the style's border defaults."""
    from .schematic_data import SchematicData, DocumentProperties, BorderData
    from .border_dialog import _units_per
    from .config import default_style
    style = style or default_style()
    from . import project
    root = Path(root)
    path = project.folder("posters", root, create=True) / (name + ".slicap_poster")
    presets = style.BORDER_PRESETS
    if fmt is None or fmt == DRAWING_SIZE:
        border = None
    elif isinstance(fmt, str):
        border = resolve_format(border_formats(presets), fmt, landscape)
    else:
        border = tuple(fmt)
    data = SchematicData.from_json("{}")
    if border is None:
        data.properties = DocumentProperties(title=title or name, author=author,
                                             page_size=DRAWING_SIZE,
                                             page_width_mm=0.0, page_height_mm=0.0)
        data.save(path)
        return path
    w_mm, h_mm, fixed_w, fixed_h = border
    upm = _units_per()["mm"]
    data.properties = DocumentProperties(
        title=title or name, author=author,
        page_size=page_name_of(w_mm, h_mm, (fixed_w, fixed_h), presets),
        page_width_mm=round(w_mm, 1), page_height_mm=round(h_mm, 1))
    data.border = BorderData(
        x=0.0, y=0.0, width=round(w_mm * upm, 2), height=round(h_mm * upm, 2),
        show_in_export=style.BORDER_SHOW_LINE, fixed_w=fixed_w, fixed_h=fixed_h,
        line_color=style.BORDER_LINE_COLOR.name(), line_width=style.BORDER_LINE_WIDTH,
        bg_color=style.BORDER_BG_COLOR.name(), bg_alpha=style.BORDER_BG_ALPHA,
        line_style=style.BORDER_LINE_STYLE)
    data.save(path)
    return path


class NewPosterDialog(QDialog):
    """Name, title and border of a new poster: the same border formats as
    the properties dialog of a drawing (none, paper, screen, presets,
    custom)."""

    def __init__(self, root, parent=None, style=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("New poster")
        self.setMinimumWidth(chars(self, 48))
        self._root = Path(root)
        self.path = None
        form = QFormLayout(self)
        self._name = QLineEdit()
        self._name.setPlaceholderText("file name without extension")
        form.addRow("Name:", self._name)
        self._title = QLineEdit()
        form.addRow("Title:", self._title)
        from .config import default_style
        self._style  = style or default_style()
        self._format = BorderFormatFields(form, self._style.BORDER_PRESETS)
        self._format.combo.setCurrentText("A4")
        hint = QLabel("The border is the export frame; the exported SVG and "
                      "PDF have its size. Saved as posters/<name>.slicap_poster.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        form.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self._name.setFocus()

    def _on_accept(self) -> None:
        name = self._name.text().strip()
        if not name or any(c in name for c in "/\\:*?\"<>|"):
            QMessageBox.warning(self, "New poster", "Give the poster a file name.")
            return
        from . import project
        path = project.folder("posters", self._root) / (name + ".slicap_poster")
        if path.exists():
            if QMessageBox.question(
                    self, "New poster", f"{path.name} exists. Replace it?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
        self.path = create_poster(self._root, name, self._format.border_mm(),
                                  title=self._title.text().strip(), style=self._style)
        self.accept()
