"""
Property dialog for ShapeItem — stroke, fill, line style, line ends.

Sections shown / hidden depending on shape kind:
  fill      : rect, circle only
  line ends : line only
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QDoubleSpinBox, QComboBox, QPushButton, QDialogButtonBox, QLabel,
    QColorDialog,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

_KINDS_WITH_FILL     = {"rect", "circle"}
_KINDS_WITH_LINEENDS = {"line"}

_LINE_STYLES = ["solid", "dashed", "dotted", "dash-dot"]
_LINE_ENDS   = ["none", "arrow", "dot", "diamond"]
_FILL_STYLES = ["none", "solid"]


class _ColorButton(QPushButton):
    def __init__(self, color: str, parent=None):
        super().__init__(parent, Qt.Window)
        self.setFixedWidth(56)
        self._color = QColor(color)
        self._refresh()
        self.clicked.connect(self._pick)

    def color(self) -> str:
        return self._color.name()

    def _pick(self):
        c = QColorDialog.getColor(self._color, self)
        if c.isValid():
            self._color = c
            self._refresh()

    def _refresh(self):
        self.setStyleSheet(
            f"background-color: {self._color.name()}; border: 1px solid #888;"
        )
        self.setText("")


class ShapeDialog(QDialog):
    def __init__(self, item, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Shape Properties")
        self._kind = item.kind

        layout = QVBoxLayout(self)

        # ── Stroke ───────────────────────────────────────────────────────────
        stroke_box = QGroupBox("Stroke")
        sf = QFormLayout(stroke_box)

        self._stroke_btn = _ColorButton(item.stroke_color)
        sf.addRow("Colour:", self._stroke_btn)

        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.25, 20.0)
        self._width_spin.setSingleStep(0.25)
        self._width_spin.setDecimals(2)
        self._width_spin.setValue(item.line_width)
        self._width_spin.setFixedWidth(80)
        sf.addRow("Width:", self._width_spin)

        self._style_combo = QComboBox()
        self._style_combo.addItems(_LINE_STYLES)
        self._style_combo.setCurrentText(item.line_style)
        sf.addRow("Style:", self._style_combo)

        layout.addWidget(stroke_box)

        # ── Line ends (line kind only) ────────────────────────────────────────
        if self._kind in _KINDS_WITH_LINEENDS:
            ends_box = QGroupBox("Line ends")
            ef = QFormLayout(ends_box)

            self._end_start = QComboBox()
            self._end_start.addItems(_LINE_ENDS)
            self._end_start.setCurrentText(item.line_end_start)
            ef.addRow("Start:", self._end_start)

            self._end_end = QComboBox()
            self._end_end.addItems(_LINE_ENDS)
            self._end_end.setCurrentText(item.line_end_end)
            ef.addRow("End:", self._end_end)

            layout.addWidget(ends_box)
        else:
            self._end_start = None
            self._end_end   = None

        # ── Fill (rect / circle only) ─────────────────────────────────────────
        if self._kind in _KINDS_WITH_FILL:
            fill_box = QGroupBox("Fill")
            ff = QFormLayout(fill_box)

            self._fill_style = QComboBox()
            self._fill_style.addItems(_FILL_STYLES)
            self._fill_style.setCurrentText(item.fill_style)
            ff.addRow("Style:", self._fill_style)

            self._fill_btn = _ColorButton(item.fill_color)
            ff.addRow("Colour:", self._fill_btn)

            self._fill_style.currentTextChanged.connect(
                lambda t: self._fill_btn.setEnabled(t == "solid")
            )
            self._fill_btn.setEnabled(item.fill_style == "solid")

            layout.addWidget(fill_box)
        else:
            self._fill_style = None
            self._fill_btn   = None

        # ── buttons ───────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── result accessors ──────────────────────────────────────────────────────

    def get_stroke_color(self) -> str:
        return self._stroke_btn.color()

    def get_line_width(self) -> float:
        return self._width_spin.value()

    def get_line_style(self) -> str:
        return self._style_combo.currentText()

    def get_line_end_start(self) -> str:
        return self._end_start.currentText() if self._end_start else "none"

    def get_line_end_end(self) -> str:
        return self._end_end.currentText() if self._end_end else "none"

    def get_fill_style(self) -> str:
        return self._fill_style.currentText() if self._fill_style else "none"

    def get_fill_color(self) -> str:
        return self._fill_btn.color() if self._fill_btn else "#ffffff"
