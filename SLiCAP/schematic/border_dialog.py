from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QDoubleSpinBox, QComboBox,
    QCheckBox, QDialogButtonBox, QLayout, QPushButton, QSpinBox,
    QColorDialog,
)
from PySide6.QtGui import QColor

from .border_item import (DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH,
                          DEFAULT_BG_COLOR)

def _units_per() -> dict:
    """Scene units per physical unit — from the project setting
    ini.sch_scale (units per mm, default 2; 1 inch = 25.4 mm). Read at
    dialog-open time so each project's scale applies."""
    import SLiCAP.SLiCAPconfigure as ini
    upm = float(getattr(ini, "sch_scale", 2.0))
    return {"mm": upm, "inch": 25.4 * upm}


class _ColorButton(QPushButton):
    """Small swatch button opening a QColorDialog."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedWidth(48)
        self._color = color
        self._apply()
        self.clicked.connect(self._pick)

    def _apply(self):
        self.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #888;")

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self, "Select color")
        if c.isValid():
            self._color = c.name()
            self._apply()

    def color(self) -> str:
        return self._color


class _SizeRow:
    """Width/Height row: float value + unit combo + Fixed checkbox.
    The canonical value is scene units; the row displays mm or inch."""

    def __init__(self, grid, row, label, units_value: float, fixed: bool,
                 unit: str, units_per: dict):
        self._units_per = units_per
        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(2)
        self._spin.setRange(0.1, 10000.0)
        self._unit = QComboBox()
        self._unit.addItems(list(units_per.keys()))
        self._unit.setCurrentText(unit)
        self._fixed = QCheckBox("Fixed")
        self._fixed.setToolTip(
            "If checked, this dimension cannot be changed by dragging the "
            "border sides on the canvas.")
        self._fixed.setChecked(fixed)
        self._spin.setValue(units_value / units_per[unit])
        self._unit.currentTextChanged.connect(self._convert)
        self._last_unit = unit
        grid.addWidget(QLabel(label), row, 0)
        grid.addWidget(self._spin, row, 1)
        grid.addWidget(self._unit, row, 2)
        grid.addWidget(self._fixed, row, 3)

    def _convert(self, new_unit):
        value_units = self._spin.value() * self._units_per[self._last_unit]
        self._spin.setValue(value_units / self._units_per[new_unit])
        self._last_unit = new_unit

    def units(self) -> float:
        return self._spin.value() * self._units_per[self._last_unit]

    def fixed(self) -> bool:
        return self._fixed.isChecked()

    def unit_name(self) -> str:
        return self._last_unit


class BorderDialog(QDialog):
    """Dialog for the export border: physical size (mm/inch) with per-axis
    drag locks, line color/width, background color with transparency
    (bottom layer), and export visibility (SLNG.md 2026-07-15)."""

    _last_unit = "mm"    # remembered across dialog openings (session)

    def __init__(self, width: float = 400, height: float = 300,
                 show_in_export: bool = True,
                 fixed_w: bool = False, fixed_h: bool = False,
                 line_color: str = DEFAULT_LINE_COLOR,
                 line_width: float = DEFAULT_LINE_WIDTH,
                 bg_color: str = DEFAULT_BG_COLOR,
                 bg_alpha: int = 0, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Border")
        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        unit = BorderDialog._last_unit
        units_per = _units_per()
        self._w_row = _SizeRow(grid, 0, "Width", width, fixed_w, unit,
                               units_per)
        self._h_row = _SizeRow(grid, 1, "Height", height, fixed_h, unit,
                               units_per)

        grid.addWidget(QLabel("Line"), 2, 0)
        self._line_color = _ColorButton(line_color)
        grid.addWidget(self._line_color, 2, 1)
        self._line_width = QDoubleSpinBox()
        self._line_width.setDecimals(2)
        self._line_width.setRange(0.1, 20.0)
        self._line_width.setValue(line_width)
        self._line_width.setSuffix(" units")
        grid.addWidget(self._line_width, 2, 2)

        grid.addWidget(QLabel("Background"), 3, 0)
        self._bg_color = _ColorButton(bg_color)
        grid.addWidget(self._bg_color, 3, 1)
        self._bg_alpha = QSpinBox()
        self._bg_alpha.setRange(0, 100)
        self._bg_alpha.setValue(bg_alpha)
        self._bg_alpha.setPrefix("opacity ")
        self._bg_alpha.setSuffix(" %")
        self._bg_alpha.setToolTip(
            "Opacity of the background fill: 0 % = fully transparent "
            "(no background), 100 % = solid. The background is the "
            "bottom layer.")
        grid.addWidget(self._bg_alpha, 3, 2)

        outer.addLayout(grid)

        upm = units_per["mm"]
        hint = QLabel(f"1 mm = {upm:g} scene units (project setting "
                      f"[gui] sch_scale); grid square = 5 units = "
                      f"{5 / upm:g} mm, resistor pin-to-pin = 50 units = "
                      f"{50 / upm:g} mm")
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(hint)

        self._show_cb = QCheckBox("Include border line in export")
        self._show_cb.setChecked(show_in_export)
        outer.addWidget(self._show_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_accept(self):
        BorderDialog._last_unit = self._w_row.unit_name()
        self.accept()

    # canonical values (scene units / hex colors / percent)
    def border_width(self) -> float:
        return self._w_row.units()

    def border_height(self) -> float:
        return self._h_row.units()

    def fixed_w(self) -> bool:
        return self._w_row.fixed()

    def fixed_h(self) -> bool:
        return self._h_row.fixed()

    def line_color(self) -> str:
        return self._line_color.color()

    def line_width(self) -> float:
        return self._line_width.value()

    def bg_color(self) -> str:
        return self._bg_color.color()

    def bg_alpha(self) -> int:
        return self._bg_alpha.value()

    def show_in_export(self) -> bool:
        return self._show_cb.isChecked()

    def border_properties(self) -> dict:
        """All border properties as the kwargs of BorderItem (minus x/y)."""
        return dict(width=self.border_width(), height=self.border_height(),
                    show_in_export=self.show_in_export(),
                    fixed_w=self.fixed_w(), fixed_h=self.fixed_h(),
                    line_color=self.line_color(),
                    line_width=self.line_width(),
                    bg_color=self.bg_color(), bg_alpha=self.bg_alpha())
