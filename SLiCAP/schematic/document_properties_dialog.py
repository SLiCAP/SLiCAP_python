from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QDoubleSpinBox, QCheckBox,
)
from PySide6.QtCore import Qt

from .schematic_data import DocumentProperties

_PAGE_SIZES = ["A4", "A3", "A2", "A1", "Letter", "Legal", "Tabloid", "Custom"]


class DocumentPropertiesDialog(QDialog):
    def __init__(self, props: DocumentProperties, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Document Properties")
        self.setMinimumWidth(360)

        layout = QFormLayout(self)
        layout.setRowWrapPolicy(QFormLayout.DontWrapRows)

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
        idx = self._page_size.findText(props.page_size)
        self._page_size.setCurrentIndex(idx if idx >= 0 else 0)
        layout.addRow("Page Size:", self._page_size)

        self._width = QDoubleSpinBox()
        self._width.setRange(1.0, 10000.0)
        self._width.setDecimals(1)
        self._width.setSuffix(" mm")
        self._width.setValue(props.page_width_mm)
        layout.addRow("Width:", self._width)

        self._height = QDoubleSpinBox()
        self._height.setRange(1.0, 10000.0)
        self._height.setDecimals(1)
        self._height.setSuffix(" mm")
        self._height.setValue(props.page_height_mm)
        layout.addRow("Height:", self._height)

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
        self._layout.setRowVisible(self._width,  custom)
        self._layout.setRowVisible(self._height, custom)
        if custom:
            self._width.setFocus()

    def apply(self, props: DocumentProperties) -> None:
        props.title          = self._title.text().strip()
        props.author         = self._author.text().strip()
        props.created        = self._created.text().strip()
        props.page_size      = self._page_size.currentText()
        props.page_width_mm  = self._width.value()
        props.page_height_mm = self._height.value()
        props.is_subcircuit  = self._subcircuit.isChecked()
