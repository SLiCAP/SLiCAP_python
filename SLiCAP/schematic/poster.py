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
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
    QLabel, QMessageBox,
)

from .document_properties_dialog import PAGE_SIZES_MM, page_size_mm
from .sizing import chars, fit_contents


def create_poster(root, name: str, page_size: str = "A4", landscape: bool = False,
                  title: str = "", author: str = "", style=None) -> Path:
    """Write posters/<name>.slicap_poster with its page size and a border of
    that size (the export frame, in the style's border look); returns the
    path. The project's border and page defaults apply."""
    from .schematic_data import SchematicData, DocumentProperties, BorderData
    from .border_dialog import _units_per
    from .config import default_style
    style = style or default_style()
    root = Path(root)
    folder = root / "posters"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name + ".slicap_poster")
    w_mm, h_mm = page_size_mm(page_size, landscape)
    upm = _units_per()["mm"]
    data = SchematicData.from_json("{}")
    data.properties = DocumentProperties(title=title or name, author=author,
                                         page_size=page_size,
                                         page_width_mm=w_mm, page_height_mm=h_mm)
    data.border = BorderData(
        x=0.0, y=0.0, width=round(w_mm * upm, 2), height=round(h_mm * upm, 2),
        show_in_export=style.BORDER_SHOW_LINE, fixed_w=True, fixed_h=True,
        line_color=style.BORDER_LINE_COLOR.name(), line_width=style.BORDER_LINE_WIDTH,
        bg_color=style.BORDER_BG_COLOR.name(), bg_alpha=style.BORDER_BG_ALPHA,
        line_style=style.BORDER_LINE_STYLE)
    data.save(path)
    return path


class NewPosterDialog(QDialog):
    """Name and page format of a new poster."""

    def __init__(self, root, parent=None):
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
        self._size = QComboBox()
        self._size.addItems(list(PAGE_SIZES_MM))
        self._size.setCurrentText("A4")
        fit_contents(self._size)
        form.addRow("Page format:", self._size)
        self._landscape = QCheckBox("Landscape (paper sizes)")
        form.addRow("", self._landscape)
        hint = QLabel("The border is the page; the exported SVG and PDF have "
                      "this size. Saved as posters/<name>.slicap_poster.")
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
        path = self._root / "posters" / (name + ".slicap_poster")
        if path.exists():
            if QMessageBox.question(
                    self, "New poster", f"{path.name} exists. Replace it?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
        self.path = create_poster(self._root, name, self._size.currentText(),
                                  self._landscape.isChecked(), self._title.text().strip())
        self.accept()
