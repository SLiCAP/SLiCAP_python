"""
The LaTeX scale of one item (fragment, parameter or model table, analysis
or library block): "Default" follows the schematic's LaTeX scale
(Style.LATEX_SCALE, in the Rendering preferences); otherwise the item keeps
its own percentage (Anton, 2026-10-11). One widget, so that every dialog
offers the choice in the same way.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QDoubleSpinBox, QLabel


class LatexScaleField(QWidget):
    """``value()`` is None for "Default", else the own scale in %."""

    def __init__(self, latex_scale=None, default_scale: float = 150.0, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel("LaTeX scale:"))
        self._spin = QDoubleSpinBox()
        self._spin.setRange(1.0, 1000.0)
        self._spin.setDecimals(1)
        self._spin.setSuffix(" %")
        own = isinstance(latex_scale, (int, float))
        self._spin.setValue(float(latex_scale) if own else float(default_scale))
        lay.addWidget(self._spin)
        self._default = QCheckBox("Default (%g %%)" % default_scale)
        self._default.setToolTip("Follow the LaTeX scale of the schematic "
                                 "(Preferences, Rendering)")
        self._default.setChecked(not own)
        self._default.toggled.connect(lambda on: self._spin.setEnabled(not on))
        self._spin.setEnabled(own)
        lay.addWidget(self._default)
        lay.addStretch(1)
        self._default_scale = float(default_scale)

    def value(self):
        return None if self._default.isChecked() else self._spin.value()

    def percent(self) -> float:
        """The effective scale in %, also when following the default."""
        return self._default_scale if self._default.isChecked() else self._spin.value()
