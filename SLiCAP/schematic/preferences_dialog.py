from __future__ import annotations

import configparser

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
    QCheckBox, QComboBox,
    QDialogButtonBox, QColorDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

_FONT_FAMILIES = [
    "sans-serif", "serif", "monospace",
    "Arial", "Helvetica", "Times New Roman", "Courier New", "Georgia",
]

_SPIN_W   = 65   # fixed width for all spinboxes
_COMBO_W  = 130  # fixed width for font-family combos
_COLOR_W  = 56   # fixed width for colour buttons


class _ColorButton(QPushButton):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent, Qt.Window)
        self._color = QColor(color)
        self.setFixedWidth(_COLOR_W)
        self._refresh()
        self.clicked.connect(self._pick)

    def color(self) -> QColor:
        return self._color

    def _pick(self):
        c = QColorDialog.getColor(self._color, self)
        if c.isValid():
            self._color = c
            self._refresh()

    def _refresh(self):
        self.setStyleSheet(
            f"background-color: {self._color.name()};"
            "border: 1px solid #888;"
        )
        self.setText("")


class PreferencesDialog(QDialog):
    """Edits ONE schematic's drawing style (the panel's own Style object)."""

    def __init__(self, style, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(520)

        self._style = style
        self._widgets: dict[tuple[str, str], object] = {}

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(
            "<small><i>Changes take effect immediately after clicking OK.</i></small>"
        ))

        # ── two-column body ───────────────────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(12)
        left  = QVBoxLayout()
        right = QVBoxLayout()
        cols.addLayout(left)
        cols.addLayout(right)
        outer.addLayout(cols)

        # ── widget factories ─────────────────────────────────────────────────

        def cbtn(c: QColor) -> _ColorButton:
            return _ColorButton(c)

        def fspin(val, lo=0.1, hi=10.0, step=0.1, dec=1) -> QDoubleSpinBox:
            sb = QDoubleSpinBox()
            sb.setRange(lo, hi)
            sb.setSingleStep(step)
            sb.setDecimals(dec)
            sb.setValue(val)
            sb.setFixedWidth(_SPIN_W)
            return sb

        def ispin(val, lo=1, hi=500) -> QSpinBox:
            sb = QSpinBox()
            sb.setRange(lo, hi)
            sb.setValue(val)
            sb.setFixedWidth(_SPIN_W)
            return sb

        def combo(current: str) -> QComboBox:
            cb = QComboBox()
            cb.setEditable(True)
            cb.addItems(_FONT_FAMILIES)
            idx = cb.findText(current)
            if idx >= 0:
                cb.setCurrentIndex(idx)
            else:
                cb.setCurrentText(current)
            cb.setFixedWidth(_COMBO_W)
            return cb

        def check(checked: bool) -> QCheckBox:
            cb = QCheckBox()
            cb.setChecked(checked)
            return cb

        # ── group builder ─────────────────────────────────────────────────────
        def group(col: QVBoxLayout, title: str,
                  rows: list[tuple[str, str, str, object]]) -> None:
            """rows = [(label, section, key, widget), ...]"""
            grp = QGroupBox(title)
            form = QFormLayout()
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
            form.setSpacing(4)
            grp.setLayout(form)
            for label, sec, key, widget in rows:
                self._widgets[(sec, key)] = widget
                if isinstance(widget, _ColorButton):
                    # Right-align colour buttons with a stretch spacer
                    h = QHBoxLayout()
                    h.setContentsMargins(0, 0, 0, 0)
                    h.addStretch(1)
                    h.addWidget(widget)
                    form.addRow(label, h)
                else:
                    form.addRow(label, widget)
            col.addWidget(grp)

        # ── left column ───────────────────────────────────────────────────────
        group(left, "Symbol", [
            ("Outline colour", "symbol", "stroke_color", cbtn(style.SYMBOL_STROKE_COLOR)),
            ("Text colour",    "symbol", "text_color",   cbtn(style.SYMBOL_TEXT_COLOR)),
        ])
        group(left, "Wire", [
            ("Colour", "wire", "color", cbtn(style.WIRE_COLOR)),
            ("Width",  "wire", "width", fspin(style.WIRE_WIDTH, 0.2, 5.0)),
        ])
        group(left, "Net label", [
            ("Colour",    "net_label", "color",     cbtn(style.NET_LABEL_COLOR)),
            ("Font size", "net_label", "font_size", ispin(style.NET_LABEL_FONT_SIZE, 4, 32)),
        ])
        group(left, "Component refdes", [
            ("Font family", "component_label", "font_family", combo(style.COMP_REFDES_FONT_FAMILY)),
            ("Font size",   "component_label", "font_size",   ispin(style.COMP_LABEL_FONT_SIZE, 4, 32)),
            ("Colour",      "component_label", "color",       cbtn(style.COMP_LABEL_COLOR)),
            # IEEE-style element identifiers (customer request): refdes via
            # the SLiCAP LaTeX method, optionally \mathrm{\mathbf{…}}.
            ("LaTeX rendering", "component_label", "latex",
             check(style.COMP_LABEL_LATEX)),
            ("Bold face",       "component_label", "latex_bold",
             check(style.COMP_LABEL_LATEX_BOLD)),
            ("LaTeX scale %",   "component_label", "latex_scale",
             ispin(style.COMP_LABEL_LATEX_SCALE, 25, 400)),
        ])
        group(left, "Component parameters", [
            ("Font family",   "component_param", "font_family",   combo(style.COMP_PARAM_FONT_FAMILY)),
            ("Font size",     "component_param", "font_size",     ispin(style.COMP_PARAM_FONT_SIZE, 4, 32)),
            ("Colour",        "component_param", "color",         cbtn(style.COMP_PARAM_COLOR)),
            ("LaTeX scale %", "component_param", "latex_scale",   ispin(style.COMP_PARAM_LATEX_SCALE, 25, 400)),
        ])
        group(left, "Text annotations", [
            ("Font family", "text", "font_family", combo(style.TEXT_FONT_FAMILY)),
            ("Font size",   "text", "font_size",   ispin(style.TEXT_FONT_SIZE, 4, 72)),
            ("Colour",      "text", "color",       cbtn(style.TEXT_COLOR)),
        ])
        left.addStretch(1)

        # ── right column ──────────────────────────────────────────────────────
        # "Rendering" group — the per-schematic LaTeX preference; disabled when
        # the tools are absent (the only global aspect of LaTeX rendering).
        from .latex_label import LATEX_INSTALLED
        latex_cb = check(style.LATEX_RENDERING_ENABLED and LATEX_INSTALLED)
        if not LATEX_INSTALLED:
            latex_cb.setEnabled(False)
            latex_cb.setToolTip("pdflatex / dvisvgm not found on this system")
        self._widgets[("rendering", "latex_rendering")] = latex_cb
        rend_grp = QGroupBox("Rendering")
        rend_form = QFormLayout()
        rend_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        rend_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        rend_form.setSpacing(4)
        rend_grp.setLayout(rend_form)
        rend_form.addRow("LaTeX rendering", latex_cb)
        right.addWidget(rend_grp)

        group(right, "Hyperlinks", [
            ("Font family", "hyperlink", "font_family", combo(style.HYPERLINK_FONT_FAMILY)),
            ("Font size",   "hyperlink", "font_size",   ispin(style.HYPERLINK_FONT_SIZE, 4, 72)),
            ("Colour",      "hyperlink", "color",       cbtn(style.HYPERLINK_COLOR)),
            ("Underline",   "hyperlink", "underline",   check(style.HYPERLINK_UNDERLINE)),
        ])
        group(right, "Grid", [
            ("Minor colour", "grid", "minor_color", cbtn(style.GRID_MINOR_COLOR)),
            ("Major colour", "grid", "major_color", cbtn(style.GRID_MAJOR_COLOR)),
        ])
        group(right, "Wire handles / connections", [
            ("Handle colour",     "handles", "color",            cbtn(style.HANDLE_COLOR)),
            ("Handle size",       "handles", "size",             fspin(style.HANDLE_SIZE, 2.0, 12.0)),
            ("Connection colour", "handles", "connection_color", cbtn(style.CONNECTION_COLOR)),
        ])
        group(right, "Junctions", [
            ("Colour", "junctions", "color",  cbtn(style.JUNCTION_COLOR)),
            ("Radius", "junctions", "radius", fspin(style.JUNCTION_RADIUS, 1.0, 10.0, 0.5)),
        ])
        group(right, "Bias annotation (DC operating point)", [
            ("Font family", "bias_annotation", "font_family", combo(style.BIAS_FONT_FAMILY)),
            ("Font size",   "bias_annotation", "font_size",   ispin(style.BIAS_FONT_SIZE, 4, 32)),
            ("Colour",      "bias_annotation", "color",       cbtn(style.BIAS_COLOR)),
            ("Digits",      "bias_annotation", "digits",      ispin(style.BIAS_DIGITS, 1, 10)),
        ])
        # LaTeX fragments and images scale per instance in their own
        # dialogs — one value, one place (Anton, 2026-07-12); only the
        # table/model scale is a schematic preference (applies live to all
        # tables/models on this schematic).
        group(right, "Parameter and model definitions", [
            ("Scaling (%)", "scales", "parameter_table", ispin(style.SCALE_PARAMETER_TABLE, 1, 500)),
        ])
        right.addStretch(1)

        # ── buttons ───────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def result_parser(self) -> configparser.ConfigParser:
        """The edited style: the panel's effective config (so unedited keys are
        preserved) overlaid with the dialog's widget values.  The caller applies
        it to the panel's Style and persists it to the schematic's sidecar."""
        cfg = self._style.snapshot()
        for (section, key), widget in self._widgets.items():
            if section not in cfg:
                cfg[section] = {}
            if isinstance(widget, _ColorButton):
                cfg[section][key] = widget.color().name()
            elif isinstance(widget, QDoubleSpinBox):
                cfg[section][key] = str(widget.value())
            elif isinstance(widget, QSpinBox):
                cfg[section][key] = str(widget.value())
            elif isinstance(widget, QComboBox):
                cfg[section][key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                cfg[section][key] = "true" if widget.isChecked() else "false"
        return cfg
