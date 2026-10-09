from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QCheckBox, QPlainTextEdit, QDialogButtonBox, QLayout,
)
from PySide6.QtCore import Qt
from .sizing import chars, fit_contents
from .color_button import ColorButton
from .config import GENERIC_FONT_FAMILIES

_DEFAULT = "(Preferences)"


class TextDialog(QDialog):
    """Multi-line text input dialog for placing/editing a text annotation,
    with the item's own font family, size, face and colour.

    Every property has a "(Preferences)" state, the default, in which the
    item follows the schematic's drawing preferences: the family combo's
    first entry, a size of 0 and the colour check box unticked. The family
    combo offers the generic families and stays editable for a named font
    (Anton, 2026-10-06: generic families render the same on every machine,
    a named font only where it is installed)."""

    def __init__(self, text: str = "", style=None, parent=None,
                 font_family: str = "", font_size: int = 0,
                 bold: bool = False, italic: bool = False, color: str = "",
                 template: bool = False):
        """*template*: the dialog of the document-properties block. The
        text is then the TEMPLATE, with placeholders for the properties,
        and the block renders it (Anton, 2026-10-09)."""
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Document properties" if template else "Text")
        self.setMinimumWidth(chars(self, 51))
        from .config import default_style
        style = style or default_style()

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(outer)

        if template:
            from .schematic_data import PROPERTIES_FIELDS
            hint = QLabel("The block shows the document properties. Placeholders: "
                          + "  ".join("{" + f + "}" for f in PROPERTIES_FIELDS)
                          + ". A line whose placeholders are all empty is left out.")
            hint.setWordWrap(True)
            hint.setStyleSheet("color: grey; font-size: 9pt;")
            outer.addWidget(hint)
        self._edit = QPlainTextEdit()
        self._edit.setMinimumHeight(100)
        self._edit.setPlainText(text)
        outer.addWidget(self._edit)

        # ── font row ──────────────────────────────────────────────────────────
        row = QHBoxLayout()
        row.addWidget(QLabel("Font:"))
        self._family = QComboBox()
        self._family.setEditable(True)
        self._family.addItem(_DEFAULT)
        self._family.addItems(GENERIC_FONT_FAMILIES)
        self._family.setCurrentText(font_family or _DEFAULT)
        self._family.setToolTip(
            f"Preferences: {style.TEXT_FONT_FAMILY}. The generic families render "
            "the same on every machine; a named font only where it is installed.")
        row.addWidget(self._family)
        row.addWidget(QLabel("Size:"))
        self._size = QSpinBox()
        self._size.setRange(0, 72)
        self._size.setSpecialValueText(_DEFAULT)
        self._size.setSuffix(" pt")
        self._size.setValue(int(font_size or 0))
        self._size.setToolTip(f"Preferences: {style.TEXT_FONT_SIZE} pt")
        fit_contents(self._size)
        row.addWidget(self._size)
        self._bold = QCheckBox("Bold")
        self._bold.setChecked(bool(bold))
        row.addWidget(self._bold)
        self._italic = QCheckBox("Italic")
        self._italic.setChecked(bool(italic))
        row.addWidget(self._italic)
        row.addStretch(1)
        outer.addLayout(row)

        # ── colour row ────────────────────────────────────────────────────────
        crow = QHBoxLayout()
        self._color_on = QCheckBox("Colour:")
        self._color_on.setChecked(bool(color))
        self._color_on.setToolTip(
            f"Unticked: the Preferences colour {style.TEXT_COLOR.name()}")
        crow.addWidget(self._color_on)
        self._color_btn = ColorButton(color or style.TEXT_COLOR.name())
        self._color_btn.setEnabled(bool(color))
        self._color_on.toggled.connect(self._color_btn.setEnabled)
        crow.addWidget(self._color_btn)
        crow.addStretch(1)
        outer.addLayout(crow)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._edit.setFocus()
        # Select all so user can immediately replace existing text.
        self._edit.selectAll()

    # ── result accessors ("" / 0 / False = follow Preferences) ──────────────

    def text(self) -> str:
        return self._edit.toPlainText()

    def font_family(self) -> str:
        fam = self._family.currentText().strip()
        return "" if fam in ("", _DEFAULT) else fam

    def font_size(self) -> int:
        return int(self._size.value())

    def bold(self) -> bool:
        return self._bold.isChecked()

    def italic(self) -> bool:
        return self._italic.isChecked()

    def color(self) -> str:
        return self._color_btn.color() if self._color_on.isChecked() else ""

    def properties(self) -> dict:
        """The keyword arguments of FreeTextItem / set_properties."""
        return dict(font_family=self.font_family(), font_size=self.font_size(),
                    bold=self.bold(), italic=self.italic(), color=self.color())
