"""
Property dialog for ShapeItem — stroke, fill, line style, line ends, rotation.

Sections shown / hidden depending on shape kind:
  fill      : rect, ellipse, polygon
  line ends : line only (with the head width and length)
  rotation  : rect, ellipse, polygon (a line is rotated by its points)
"""
from .sizing import fit_contents
from .color_button import ColorButton
from PySide6.QtWidgets import (
    QCheckBox, QLabel,
    QDialog, QVBoxLayout, QFormLayout, QGroupBox,
    QDoubleSpinBox, QComboBox, QDialogButtonBox,
)
from PySide6.QtCore import Qt

_KINDS_WITH_FILL     = {"rect", "ellipse", "polygon", "curve"}
_KINDS_WITH_LINEENDS = {"line", "arc", "curve", "func"}
_KINDS_WITH_ROTATION = {"rect", "ellipse", "polygon", "arc", "curve", "func"}

_LINE_STYLES = ["none", "solid", "dashed", "dotted", "dash-dot"]
_LINE_ENDS   = ["none", "arrow", "dot", "diamond"]
_FILL_STYLES = ["none", "solid"]


class _FuncSource(QGroupBox):
    """The source of a function curve: an expression in one variable over a
    range, sampled by the core (SLiCAPmath.sampleExpr), or a trace of the
    Design data (its decimated data in the run manifest); and the mapping
    of the data into the box: x linear or logarithmic, y from the data or a
    given range (Anton, 2026-10-06)."""

    def __init__(self, item, trace_choices):
        super().__init__("Function curve")
        from PySide6.QtWidgets import QRadioButton, QLineEdit, QSpinBox, QWidget, QHBoxLayout
        form = QFormLayout(self)
        self._use_expr = QRadioButton("Expression")
        self._use_trace = QRadioButton("Trace of the Design data")
        form.addRow(self._use_expr, self._use_trace)

        self._expr = QLineEdit(item.expression)
        self._expr.setPlaceholderText("e.g. exp(x) - 1   (SLiCAP notation)")
        form.addRow("Expression:", self._expr)
        self._var = QLineEdit(item.var or "x")
        fit = QWidget(); h = QHBoxLayout(fit); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self._var)
        h.addWidget(QLabel("from")); self._x0 = QLineEdit(str(item.x_range[0]) if item.x_range else "0")
        h.addWidget(self._x0)
        h.addWidget(QLabel("to")); self._x1 = QLineEdit(str(item.x_range[1]) if len(item.x_range) > 1 else "1")
        h.addWidget(self._x1)
        h.addWidget(QLabel("samples")); self._num = QSpinBox(); self._num.setRange(8, 5000)
        self._num.setValue(item.num); fit_contents(self._num); h.addWidget(self._num)
        form.addRow("Variable:", fit)

        self._trace = QComboBox()
        for var, label in trace_choices:
            self._trace.addItem(f"{var}: {label}", (var, label))
        if not trace_choices:
            self._trace.addItem("(no traces in the Design data: run the instruction file)")
            self._trace.setEnabled(False)
        idx = self._trace.findData((item.trace_var, item.trace_label))
        if idx >= 0:
            self._trace.setCurrentIndex(idx)
        form.addRow("Trace:", self._trace)

        self._x_log = QCheckBox("logarithmic x")
        self._x_log.setChecked(item.x_log)
        form.addRow("x axis:", self._x_log)
        yw = QWidget(); yh = QHBoxLayout(yw); yh.setContentsMargins(0, 0, 0, 0)
        self._y_auto = QCheckBox("from the data"); self._y_auto.setChecked(not item.y_range)
        yh.addWidget(self._y_auto)
        yh.addWidget(QLabel("or from")); self._y0 = QLineEdit(str(item.y_range[0]) if item.y_range else "")
        yh.addWidget(self._y0)
        yh.addWidget(QLabel("to")); self._y1 = QLineEdit(str(item.y_range[1]) if len(item.y_range) > 1 else "")
        yh.addWidget(self._y1)
        form.addRow("y range:", yw)
        self._y_auto.toggled.connect(lambda on: (self._y0.setEnabled(not on), self._y1.setEnabled(not on)))
        self._y0.setEnabled(bool(item.y_range)); self._y1.setEnabled(bool(item.y_range))

        use_trace = bool(item.trace_var) and self._trace.isEnabled()
        self._use_trace.setChecked(use_trace); self._use_expr.setChecked(not use_trace)
        self._use_trace.setEnabled(self._trace.isEnabled())
        for rb in (self._use_expr, self._use_trace):
            rb.toggled.connect(self._sync)
        self._sync()

    def _sync(self, *_):
        expr = self._use_expr.isChecked()
        for w in (self._expr, self._var, self._x0, self._x1, self._num):
            w.setEnabled(expr)
        self._trace.setEnabled(not expr and self._trace.count() > 0
                               and self._trace.currentData() is not None)

    def values(self) -> dict:
        from SLiCAP.SLiCAPmath import _checkNumber
        def num(text, default):
            try:
                return float(_checkNumber(text.strip()))
            except Exception:
                return default
        y_range = [] if self._y_auto.isChecked() else [num(self._y0.text(), 0.0), num(self._y1.text(), 1.0)]
        if self._use_trace.isChecked() and self._trace.currentData():
            var, label = self._trace.currentData()
            return dict(expression="", var=self._var.text().strip() or "x",
                        x_range=[], y_range=y_range, x_log=self._x_log.isChecked(),
                        num=self._num.value(), trace_var=var, trace_label=label)
        return dict(expression=self._expr.text().strip(), var=self._var.text().strip() or "x",
                    x_range=[num(self._x0.text(), 0.0), num(self._x1.text(), 1.0)],
                    y_range=y_range, x_log=self._x_log.isChecked(), num=self._num.value(),
                    trace_var="", trace_label="")


class ShapeDialog(QDialog):
    def __init__(self, item, parent=None, trace_choices=None, hint: str = ""):
        """*trace_choices*: ``[(trace_var, label), ...]`` of the Design data,
        the trace source of a function curve. *hint*: a line shown at the
        top, what happens after OK (Draw -> Function curve: the box is
        clicked after the dialog, Anton, 2026-10-06)."""
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Shape Properties")
        self._kind = item.kind

        layout = QVBoxLayout(self)
        if hint:
            lbl = QLabel(hint)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-weight: bold;")
            layout.addWidget(lbl)

        # ── Arc: the part of the ellipse ─────────────────────────────────────
        self._arc_start = self._arc_sweep = None
        if self._kind == "arc":
            arc_box = QGroupBox("Arc")
            af = QFormLayout(arc_box)
            self._arc_start = QDoubleSpinBox()
            self._arc_start.setRange(-360.0, 360.0); self._arc_start.setDecimals(1)
            self._arc_start.setSuffix(" deg"); self._arc_start.setValue(item.arc_start)
            fit_contents(self._arc_start)
            af.addRow("Start angle:", self._arc_start)
            self._arc_sweep = QDoubleSpinBox()
            self._arc_sweep.setRange(-360.0, 360.0); self._arc_sweep.setDecimals(1)
            self._arc_sweep.setSuffix(" deg"); self._arc_sweep.setValue(item.arc_sweep)
            fit_contents(self._arc_sweep)
            af.addRow("Sweep:", self._arc_sweep)
            hint = QLabel("Angles turn clockwise from 3 o'clock; drag the two "
                          "end handles on the canvas as well.")
            hint.setStyleSheet("color: grey; font-size: 9pt;")
            af.addRow(hint)
            layout.addWidget(arc_box)

        # ── Curve: open or closed ────────────────────────────────────────────
        self._closed = None
        if self._kind == "curve":
            self._closed = QCheckBox("Closed curve (fill possible, no line ends)")
            self._closed.setChecked(item.closed)
            layout.addWidget(self._closed)

        # ── Function curve: the source and the mapping ───────────────────────
        self._func = None
        if self._kind == "func":
            self._func = _FuncSource(item, trace_choices or [])
            layout.addWidget(self._func)

        # ── Stroke ───────────────────────────────────────────────────────────
        stroke_box = QGroupBox("Stroke")
        sf = QFormLayout(stroke_box)

        self._stroke_btn = ColorButton(item.stroke_color)
        sf.addRow("Colour:", self._stroke_btn)

        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.25, 20.0)
        self._width_spin.setSingleStep(0.25)
        self._width_spin.setDecimals(2)
        self._width_spin.setValue(item.line_width)
        fit_contents(self._width_spin)
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

            self._head_width = QDoubleSpinBox()
            self._head_width.setRange(0.5, 200.0)
            self._head_width.setSingleStep(0.5)
            self._head_width.setDecimals(1)
            self._head_width.setValue(item.head_width)
            fit_contents(self._head_width)
            ef.addRow("Head width:", self._head_width)

            self._head_length = QDoubleSpinBox()
            self._head_length.setRange(0.5, 200.0)
            self._head_length.setSingleStep(0.5)
            self._head_length.setDecimals(1)
            self._head_length.setValue(item.head_length)
            fit_contents(self._head_length)
            ef.addRow("Head length:", self._head_length)

            layout.addWidget(ends_box)
        else:
            self._end_start  = None
            self._end_end    = None
            self._head_width = None
            self._head_length = None

        # ── Rotation (rect / ellipse / polygon) ──────────────────────────────
        if self._kind in _KINDS_WITH_ROTATION:
            rot_box = QGroupBox("Rotation")
            rf = QFormLayout(rot_box)
            self._rotation = QDoubleSpinBox()
            self._rotation.setRange(-360.0, 360.0)
            self._rotation.setSingleStep(5.0)
            self._rotation.setDecimals(1)
            self._rotation.setSuffix(" deg")
            self._rotation.setValue(item.rotation)
            fit_contents(self._rotation)
            rf.addRow("Angle:", self._rotation)
            layout.addWidget(rot_box)
        else:
            self._rotation = None

        # ── Fill (rect / circle only) ─────────────────────────────────────────
        if self._kind in _KINDS_WITH_FILL:
            fill_box = QGroupBox("Fill")
            ff = QFormLayout(fill_box)

            self._fill_style = QComboBox()
            self._fill_style.addItems(_FILL_STYLES)
            self._fill_style.setCurrentText(item.fill_style)
            ff.addRow("Style:", self._fill_style)

            self._fill_btn = ColorButton(item.fill_color)
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

    def get_arc(self) -> tuple:
        if self._arc_start is None:
            return 0.0, 270.0
        return self._arc_start.value(), self._arc_sweep.value()

    def get_closed(self) -> bool:
        return bool(self._closed is not None and self._closed.isChecked())

    def get_func(self) -> dict:
        return self._func.values() if self._func is not None else {}

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

    def get_head_width(self) -> float:
        return self._head_width.value() if self._head_width else 4.0

    def get_head_length(self) -> float:
        return self._head_length.value() if self._head_length else 6.0

    def get_rotation(self) -> float:
        return self._rotation.value() if self._rotation else 0.0
