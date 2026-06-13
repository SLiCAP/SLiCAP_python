from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QDialogButtonBox, QLayout,
)
from PySide6.QtCore import Qt


class TextDialog(QDialog):
    """Multi-line text input dialog for placing/editing a text annotation."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Text")
        self.setMinimumWidth(360)

        from .config import TEXT_FONT_FAMILY, TEXT_FONT_SIZE, TEXT_COLOR

        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(outer)

        # Info line showing current Preferences settings (non-editable).
        info = QLabel(
            f"Font: {TEXT_FONT_FAMILY}, {TEXT_FONT_SIZE} pt, "
            f"colour: {TEXT_COLOR.name()}"
        )
        info.setStyleSheet("color: grey; font-size: 8pt;")
        outer.addWidget(info)

        self._edit = QPlainTextEdit()
        self._edit.setMinimumHeight(100)
        self._edit.setPlainText(text)
        outer.addWidget(self._edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._edit.setFocus()
        # Select all so user can immediately replace existing text.
        self._edit.selectAll()

    def text(self) -> str:
        return self._edit.toPlainText()
