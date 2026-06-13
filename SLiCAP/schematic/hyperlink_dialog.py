from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDialogButtonBox, QLabel,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class HyperlinkDialog(QDialog):
    """Dialog for placing or editing a hyperlink annotation."""

    def __init__(self, url: str = "", label: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Hyperlink")
        self.setMinimumWidth(380)

        from .config import (
            HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE,
            HYPERLINK_COLOR, HYPERLINK_UNDERLINE,
        )

        outer = QVBoxLayout()
        self.setLayout(outer)

        form = QFormLayout()
        self._url_edit = QLineEdit(url)
        self._url_edit.setPlaceholderText("https://…")
        form.addRow("URL:", self._url_edit)

        self._label_edit = QLineEdit(label)
        self._label_edit.setPlaceholderText("leave blank to display URL")
        form.addRow("Label:", self._label_edit)
        outer.addLayout(form)

        # Preview line showing appearance.
        preview_font = QFont(HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE)
        preview_font.setUnderline(HYPERLINK_UNDERLINE)
        self._preview = QLabel(label or url or "preview")
        self._preview.setFont(preview_font)
        self._preview.setStyleSheet(
            f"color: {HYPERLINK_COLOR.name()}; padding: 4px;"
        )
        outer.addWidget(self._preview)

        # Update preview as user types.
        self._url_edit.textChanged.connect(self._update_preview)
        self._label_edit.textChanged.connect(self._update_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._url_edit.setFocus()

    def _update_preview(self) -> None:
        display = self._label_edit.text().strip() or self._url_edit.text().strip() or "preview"
        self._preview.setText(display)

    def url(self) -> str:
        return self._url_edit.text().strip()

    def label(self) -> str:
        return self._label_edit.text().strip()
