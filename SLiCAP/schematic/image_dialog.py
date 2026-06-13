from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QLineEdit,
    QFileDialog, QDialogButtonBox, QLayout,
)
from PySide6.QtGui import QImageReader

_FILE_FILTER = (
    "Images (*.svg *.pdf *.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;"
    "Vector (*.svg *.pdf);;"
    "Raster (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;"
    "All Files (*)"
)


class ImageDialog(QDialog):
    """
    Dialog for placing or editing an image on the schematic.

    A single Scale % spinbox controls the display size relative to the
    image's natural pixel dimensions.  Width and Height in scene units
    are shown as read-only feedback.
    """

    def __init__(self, file_path: str = "", display_width: int = 200,
                 display_height: int = 200, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Image")
        self._natural_w: int | None = None
        self._natural_h: int | None = None

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        # ── file picker ───────────────────────────────────────────────────────
        file_row = QHBoxLayout()
        self._path_edit = QLineEdit(file_path)
        self._path_edit.setReadOnly(True)
        self._path_edit.setMinimumWidth(300)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self._path_edit)
        file_row.addWidget(browse_btn)
        outer.addLayout(file_row)

        # ── scale row ─────────────────────────────────────────────────────────
        from .config import SCALE_IMAGE
        # For an existing image, load natural size and back-calculate scale.
        if file_path:
            self._load_natural_size(file_path)
        if self._natural_w and self._natural_w > 0:
            init_scale = max(1, round(display_width / self._natural_w * 100))
        else:
            init_scale = SCALE_IMAGE

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        self._scale_spin = QSpinBox()
        self._scale_spin.setRange(1, 1000)
        self._scale_spin.setValue(init_scale)
        self._scale_spin.setSuffix(" %")
        scale_row.addWidget(self._scale_spin)
        scale_row.addSpacing(16)
        self._size_lbl = QLabel()
        scale_row.addWidget(self._size_lbl)
        scale_row.addSpacing(10)
        hint = QLabel("(1 grid square = 5 units,  resistor pin-to-pin = 50 units)")
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        scale_row.addWidget(hint)
        scale_row.addStretch(1)
        outer.addLayout(scale_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._scale_spin.valueChanged.connect(self._on_scale_changed)
        self._update_size_labels()

    # ── internal ──────────────────────────────────────────────────────────────

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image",
            self._path_edit.text() or "",
            _FILE_FILTER,
        )
        if path:
            self._path_edit.setText(path)
            self._load_natural_size(path)
            # Reset scale to preference default for newly chosen file.
            from .config import SCALE_IMAGE
            self._scale_spin.setValue(SCALE_IMAGE)
            self._update_size_labels()

    def _load_natural_size(self, path: str) -> None:
        """Read the file's natural pixel dimensions and store them."""
        ext = Path(path).suffix.lower()
        w, h = 0, 0
        if ext == ".svg":
            from PySide6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(path)
            if renderer.isValid():
                s = renderer.defaultSize()
                w, h = s.width(), s.height()
        elif ext == ".pdf":
            try:
                from PySide6.QtPdf import QPdfDocument
                doc = QPdfDocument(None)
                doc.load(path)
                if doc.pageCount() > 0:
                    pt = doc.pagePointSize(0)
                    w, h = round(pt.width()), round(pt.height())
                doc.close()
            except Exception:
                pass
        else:
            reader = QImageReader(path)
            size   = reader.size()
            if size.isValid():
                w, h = size.width(), size.height()
        if w > 0 and h > 0:
            self._natural_w = w
            self._natural_h = h

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

    def image_path(self) -> str:
        return self._path_edit.text().strip()

    def image_width(self) -> int:
        if self._natural_w:
            return max(1, round(self._natural_w * self._scale_spin.value() / 100))
        return 200

    def image_height(self) -> int:
        if self._natural_h:
            return max(1, round(self._natural_h * self._scale_spin.value() / 100))
        return 200
