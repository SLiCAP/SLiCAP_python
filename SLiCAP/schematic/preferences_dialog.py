from __future__ import annotations

import configparser

from .sizing import chars, fit_contents
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QDoubleSpinBox, QSpinBox,
    QCheckBox, QComboBox, QWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialogButtonBox,
)
from .color_button import ColorButton
from .config import LINE_STYLE_NAMES, format_border_preset
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .config import GENERIC_FONT_FAMILIES as _FONT_FAMILIES

class BorderPresetTable(QWidget):
    """The user's border formats: rows of name, width and height in mm. An
    empty width or height is a free side (Anton, 2026-10-09: a book figure
    is "a fixed width and a free height"). The table owns the whole
    [border_presets] section: section_values() is what gets written."""

    def __init__(self, presets: dict, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Name", "Width mm", "Height mm"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setToolTip("Leave the width or the height empty for a "
                               "free side, sized by hand on the canvas.")
        for name, (w, h) in presets.items():
            self._add_row(name, "" if w is None else f"{w:g}",
                          "" if h is None else f"{h:g}")
        lay.addWidget(self._table)
        btns = QHBoxLayout()
        add = QPushButton("Add"); rem = QPushButton("Remove")
        add.clicked.connect(lambda: self._add_row("", "", ""))
        rem.clicked.connect(self._remove_row)
        btns.addWidget(add); btns.addWidget(rem); btns.addStretch(1)
        lay.addLayout(btns)

    def _add_row(self, name: str, w: str, h: str) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)
        for col, text in enumerate((name, w, h)):
            self._table.setItem(r, col, QTableWidgetItem(text))

    def _remove_row(self) -> None:
        r = self._table.currentRow()
        if r >= 0:
            self._table.removeRow(r)

    def _cell(self, r: int, c: int) -> str:
        item = self._table.item(r, c)
        return item.text().strip() if item is not None else ""

    def problems(self) -> list[str]:
        """What keeps the table from being written, one line per row."""
        out = []
        for r in range(self._table.rowCount()):
            name, w, h = (self._cell(r, c) for c in range(3))
            if not name and not w and not h:
                continue
            if not name:
                out.append(f"row {r + 1}: no name"); continue
            if not w and not h:
                out.append(f"{name}: a width or a height is needed"); continue
            for label, text in (("width", w), ("height", h)):
                try:
                    if text and float(text) <= 0:
                        raise ValueError
                except ValueError:
                    out.append(f"{name}: {label} '{text}' is not a size in mm")
        return out

    def section_values(self) -> dict:
        """name -> "w x h" for the [border_presets] section; rows that
        problems() lists are left out."""
        out = {}
        for r in range(self._table.rowCount()):
            name, w, h = (self._cell(r, c) for c in range(3))
            try:
                wv = float(w) if w else None
                hv = float(h) if h else None
            except ValueError:
                continue
            if name and (wv is not None or hv is not None) and \
               (wv is None or wv > 0) and (hv is None or hv > 0):
                out[name] = format_border_preset(wv, hv)
        return out


# Widths come from the font (sizing.py); the pixel constants 65/130/56 that
# sat here cut off two-digit sizes and long font names on Windows
# (Anton, 2026-09-25).
class PreferencesDialog(QDialog):
    """Edits ONE schematic's drawing style (the panel's own Style object)."""

    def __init__(self, style, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(chars(self, 72))

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

        def cbtn(c: QColor) -> ColorButton:
            return ColorButton(c)

        def fspin(val, lo=0.1, hi=10.0, step=0.1, dec=1) -> QDoubleSpinBox:
            sb = QDoubleSpinBox()
            sb.setRange(lo, hi)
            sb.setSingleStep(step)
            sb.setDecimals(dec)
            sb.setValue(val)
            fit_contents(sb)
            return sb

        def ispin(val, lo=1, hi=500) -> QSpinBox:
            sb = QSpinBox()
            sb.setRange(lo, hi)
            sb.setValue(val)
            fit_contents(sb)
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
            fit_contents(cb)
            return cb

        def choice(current: str, items: list) -> QComboBox:
            cb = QComboBox()
            cb.addItems(items)
            cb.setCurrentText(current if current in items else items[0])
            fit_contents(cb)
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
                if isinstance(widget, ColorButton):
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
            ("View subgrid (1/5 of the grid)", "grid", "subgrid", check(style.GRID_SUBGRID)),
            ("Subgrid colour", "grid", "subgrid_color", cbtn(style.GRID_SUBGRID_COLOR)),
        ])
        group(right, "Border (new borders; the Border dialog edits an existing one)", [
            ("Line colour",          "border", "line_color",          cbtn(style.BORDER_LINE_COLOR)),
            ("Line width",           "border", "line_width",          fspin(style.BORDER_LINE_WIDTH, 0.2, 3.0)),
            ("Line style",           "border", "line_style",          choice(style.BORDER_LINE_STYLE, LINE_STYLE_NAMES)),
            ("Background colour",    "border", "bg_color",            cbtn(style.BORDER_BG_COLOR)),
            ("Background opacity %", "border", "bg_alpha",            ispin(style.BORDER_BG_ALPHA, 0, 100)),
            ("Line in export",       "border", "show_line_in_export", check(style.BORDER_SHOW_LINE)),
        ])
        # The user's border formats, offered next to the paper and screen
        # formats in the Border, Properties and New poster dialogs. The
        # widget owns its section: key None in self._widgets.
        presets_grp = QGroupBox("Border formats (next to the paper and screen formats)")
        presets_lay = QVBoxLayout(presets_grp)
        self._presets = BorderPresetTable(style.BORDER_PRESETS)
        presets_lay.addWidget(self._presets)
        right.addWidget(presets_grp)
        self._widgets[("border_presets", None)] = self._presets
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
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_accept(self) -> None:
        problems = self._presets.problems()
        if problems:
            QMessageBox.warning(self, "Border formats", "\n".join(problems))
            return
        self.accept()

    def result_parser(self) -> configparser.ConfigParser:
        """The edited style: the panel's effective config (so unedited keys are
        preserved) overlaid with the dialog's widget values.  The caller applies
        it to the panel's Style and persists it to the schematic's sidecar."""
        cfg = self._style.snapshot()
        for (section, key), widget in self._widgets.items():
            if key is None:                       # a widget that owns its section
                cfg[section] = widget.section_values()
                continue
            if section not in cfg:
                cfg[section] = {}
            if isinstance(widget, ColorButton):
                cfg[section][key] = widget.color()
            elif isinstance(widget, QDoubleSpinBox):
                cfg[section][key] = str(widget.value())
            elif isinstance(widget, QSpinBox):
                cfg[section][key] = str(widget.value())
            elif isinstance(widget, QComboBox):
                cfg[section][key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                cfg[section][key] = "true" if widget.isChecked() else "false"
        return cfg
