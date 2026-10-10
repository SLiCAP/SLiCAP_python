from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QLineEdit,
    QFileDialog, QDialogButtonBox, QLayout,
)
from .sizing import chars

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

    _TITLES = {"figure": "Figure", "schematic": "Schematic", "poster": "Poster"}
    _EMPTY  = {"figure": "(choose a figure of the Design data)",
               "schematic": "(choose a schematic of the project)",
               "poster": "(choose a poster of the project)"}
    _NONE   = {"figure": "(no figures in the Design data: run the instruction file)",
               "schematic": "(no schematics in sch/ or lib/ of the project)",
               "poster": "(no other poster to show)"}

    def __init__(self, file_path: str = "", display_width: float = 200,
                 display_height: float = 200, style=None, parent=None,
                 link_kind: str = "", choices=None, link_name: str = "",
                 size_scale: float | None = None):
        """*link_kind* with *choices* ``[(key, "img/<file>.svg"), ...]``
        turns the dialog into the dialog of a LINK: a figure object of the
        Design data by name, a schematic of the project by source path, a
        poster by name; its image is the file shown (Anton, 2026-10-06).
        The combo shows the key only, never the image: the image is what
        the link derives, and showing it read as "an image is placed"
        (Anton, 2026-10-09). *link_name* preselects one (editing a link);
        otherwise nothing is chosen and OK waits for a choice. Without a
        kind it is the plain image dialog."""
        super().__init__(parent, Qt.Window)
        from .config import default_style
        self._style = style or default_style()
        self._link_kind = link_kind or ""
        self._figures = list(choices or [])
        self.setWindowTitle(self._TITLES.get(self._link_kind, "Image"))
        self._natural_w: float | None = None
        self._natural_h: float | None = None

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        # ── file picker, or the figure combo ─────────────────────────────────
        file_row = QHBoxLayout()
        self._path_edit = QLineEdit(file_path)
        self._path_edit.setReadOnly(True)
        self._path_edit.setMinimumWidth(chars(self._path_edit, 43))
        self._figure_combo = None
        if self._link_kind:
            file_row.addWidget(QLabel(self._TITLES[self._link_kind] + ":"))
            self._figure_combo = QComboBox()
            if self._figures and self._figure_combo.findData(link_name) < 0:
                self._figure_combo.addItem(self._EMPTY[self._link_kind], "")
            for name, _file in self._figures:
                self._figure_combo.addItem(name, name)
            if self._figure_combo.findData(link_name) >= 0:
                self._figure_combo.setCurrentIndex(self._figure_combo.findData(link_name))
            self._figure_combo.currentIndexChanged.connect(self._on_figure_chosen)
            file_row.addWidget(self._figure_combo, stretch=1)
            if not self._figures:
                self._figure_combo.setEnabled(False)
                self._figure_combo.addItem(self._NONE[self._link_kind], "")
            else:
                self._on_figure_chosen()
            # No "Open the linked drawing" button here, in placing or in
            # editing: beside the list it read as the confirm and abandoned
            # the placement, and a poster is not the place to start editing
            # a schematic (Anton, 2026-10-10: REMOVED, not moved). The
            # drawing is opened from the project tree.
        else:
            browse_btn = QPushButton("Browse…")
            browse_btn.clicked.connect(self._browse)
            file_row.addWidget(self._path_edit)
            file_row.addWidget(browse_btn)
        outer.addLayout(file_row)

        # ── scale row ─────────────────────────────────────────────────────────
        # For an existing image, load natural size and back-calculate scale.
        if file_path:
            self._load_natural_size(file_path)
        # 100 %: a placed drawing then has the scale of its export, so its
        # grid and text match the poster's (Anton, 2026-10-09; 50 % was the
        # previous default and was REPLACED).
        if size_scale is not None:
            init_scale = max(1, round(size_scale * 100))
        elif self._natural_w and self._natural_w > 0:
            init_scale = max(1, round(display_width / self._natural_w * 100))
        else:
            init_scale = 100

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
        self._ok = buttons.button(QDialogButtonBox.Ok)
        if self._link_kind and not link_name:
            self._ok.setText("Place")        # the placement dialog's one action

        self._scale_spin.valueChanged.connect(self._on_scale_changed)
        self._update_size_labels()
        self._update_ok()

    def _update_ok(self) -> None:
        """OK needs a choice: a link, or a file."""
        if hasattr(self, "_ok"):
            self._ok.setEnabled(bool(self.link() if self._link_kind else self.image_path()))

    # ── internal ──────────────────────────────────────────────────────────────

    def _on_figure_chosen(self, *_args) -> None:
        name = self._figure_combo.currentData()
        file = dict(self._figures).get(name, "")
        self._path_edit.setText(file)
        if name:
            self._ensure_export(name)
        self._load_natural_size(file)
        if hasattr(self, "_scale_spin"):        # not yet during construction
            self._update_size_labels()
        self._update_ok()

    def _ensure_export(self, key: str) -> None:
        """A chosen drawing is shown at once: its export is brought up to
        date here, with the rule the poster export applies (children
        first), so the item has its image and its size when it is placed.
        Without this the item was a grey box until the poster's first
        export (Anton, 2026-10-09). A figure's image comes from a run."""
        if self._link_kind not in ("schematic", "poster"):
            return
        from . import project
        src = project.link_source(f"{self._link_kind}:{key}")
        if src is None:
            return
        from PySide6.QtWidgets import QApplication, QMessageBox
        from . import make_schematic
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            make_schematic(src)
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, self._TITLES[self._link_kind],
                                f"{src.name} could not be exported:\n\n{exc}")
            return
        QApplication.restoreOverrideCursor()

    def link(self) -> str:
        """The typed link, "<kind>:<name>" ("" for a plain image)."""
        name = (self._figure_combo.currentData() or "") if self._figure_combo else ""
        return f"{self._link_kind}:{name}" if self._link_kind and name else ""

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image",
            self._path_edit.text() or "",
            _FILE_FILTER,
        )
        if path:
            from . import project
            from .provenance import own_exports
            cur = project.current()
            if cur is not None and Path(path).resolve() in own_exports(cur):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Image",
                    "That file is this schematic's own exported image. A "
                    "schematic cannot show itself: the export would be its "
                    "own input, stale after every run and nested in every "
                    "export.\n\nPlace a Figure for a simulation plot, or "
                    "choose another file.")
                return
            self._path_edit.setText(project.relative_to_root(path))
            self._load_natural_size(path)
            # Reset scale to the default for a newly chosen file.
            self._scale_spin.setValue(100)
            self._update_size_labels()
            self._update_ok()

    def _load_natural_size(self, path: str) -> None:
        """The file's size at 100 %, in scene units, from the one authority
        image_item.natural_size (real numbers, no rounding)."""
        from . import project
        from .image_item import natural_size
        size = natural_size(project.resolve_from_root(path))
        if size:
            self._natural_w, self._natural_h = size

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

    def image_scale(self) -> float:
        """The chosen scale, 1.0 = 100 %; the image item derives its size
        from the file with it."""
        return self._scale_spin.value() / 100

    def image_width(self) -> float:
        if self._natural_w:
            return self._natural_w * self.image_scale()
        return 200

    def image_height(self) -> float:
        if self._natural_h:
            return self._natural_h * self.image_scale()
        return 200
