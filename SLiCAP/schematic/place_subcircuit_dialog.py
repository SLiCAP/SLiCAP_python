"""
Place Subcircuit dialog (Place → Subcircuit…).

Pick a subcircuit ``.lib`` file; the dialog parses its ``.subckt`` header and
shows the block's name, overridable parameters and whether a matching editable
schematic (``sch/<name>.slicap_sch``) is present.  A reorderable pin list (the
**visual** placement, clockwise from top-left) drives a live preview of the
block symbol with pin names; reordering only moves where each named pin is
drawn — the ``.subckt`` node order (and thus the netlist) is unchanged.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QDialogButtonBox, QMessageBox, QWidget,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QByteArray

from app import project
from .config import GRID_SIZE
from .subcircuit import parse_subckt, box_symbol_svg, SubcktDef, min_half, _FLOOR
from .symbol_library import Symbol
from .component_item import draw_subckt_pin_names, _apply_symbol_colors

_SVG_NS = "{http://www.w3.org/2000/svg}"


def _build_symbol(defn: SubcktDef, placement: list,
                  extra_w: float = 0.0, extra_h: float = 0.0) -> Symbol:
    """Parse a generated block symbol for the given placement into a Symbol."""
    svg = box_symbol_svg(defn, placement, extra_w, extra_h)
    g = next(e for e in ET.fromstring(svg).iter(f"{_SVG_NS}g")
             if e.get("data-prefix"))
    return Symbol(g, "preview")


class _SymbolPreview(QWidget):
    """Renders a block symbol (box + pin names) the same way the canvas does."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setMinimumSize(200, 200)
        self._sym: Symbol | None = None

    def set_symbol(self, sym: Symbol | None) -> None:
        self._sym = sym
        self.update()

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.white)
        if self._sym is None:
            return
        p.setRenderHint(QPainter.Antialiasing)
        renderer = QSvgRenderer(QByteArray(_apply_symbol_colors(self._sym.svg)))
        vb = renderer.viewBoxF()
        scale = min(self.width() / vb.width(), self.height() / vb.height()) * 0.7
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(scale, scale)
        p.translate(-vb.center().x(), -vb.center().y())
        renderer.render(p, vb)
        draw_subckt_pin_names(p, self._sym.nodes, self._sym.pins)
        p.end()


class PlaceSubcircuitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Place Subcircuit")
        self.setMinimumWidth(560)

        self._defn: SubcktDef | None = None
        self._lib_path: str | None = None
        self._extra_w: float = 0.0      # half-width added beyond the auto-fit min
        self._extra_h: float = 0.0      # half-height added beyond the auto-fit min

        outer = QVBoxLayout(self)

        # ── library file picker ─────────────────────────────────────────────────
        file_row = QHBoxLayout()
        self._file = QLineEdit(); self._file.setReadOnly(True)
        self._file.setPlaceholderText("Select a subcircuit .lib file…")
        browse = QPushButton("Browse…"); browse.clicked.connect(self._choose_file)
        file_row.addWidget(self._file); file_row.addWidget(browse)
        outer.addLayout(file_row)

        self._stale = QLabel()
        self._stale.setWordWrap(True)
        self._stale.setStyleSheet("color:#b00;")
        self._stale.setVisible(False)
        outer.addWidget(self._stale)

        # ── interface (left) + preview (right) ──────────────────────────────────
        body = QHBoxLayout()

        left = QVBoxLayout()
        form = QFormLayout()
        self._name   = QLabel("—")
        self._params = QLabel("—")
        self._sch    = QLabel("—")
        form.addRow("<b>Subcircuit:</b>", self._name)
        form.addRow("Parameters:", self._params)
        form.addRow("Schematic:", self._sch)
        left.addLayout(form)

        left.addWidget(QLabel("Pin placement (top → clockwise):"))
        pin_row = QHBoxLayout()
        self._pins = QListWidget()
        self._pins.currentRowChanged.connect(lambda _r: self._refresh_preview())
        pin_row.addWidget(self._pins)
        btns = QVBoxLayout()
        up = QPushButton("Up"); dn = QPushButton("Down")
        up.clicked.connect(lambda: self._move(-1))
        dn.clicked.connect(lambda: self._move(+1))
        btns.addWidget(up); btns.addWidget(dn); btns.addStretch(1)
        pin_row.addLayout(btns)
        left.addLayout(pin_row)
        body.addLayout(left, 1)

        right = QVBoxLayout()
        self._preview = _SymbolPreview()
        right.addWidget(self._preview, 1)
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Width"))
        wm = QPushButton("−"); wp = QPushButton("+")
        wm.clicked.connect(lambda: self._resize("w", -1))
        wp.clicked.connect(lambda: self._resize("w", +1))
        size_row.addWidget(wm); size_row.addWidget(wp)
        size_row.addSpacing(12)
        size_row.addWidget(QLabel("Height"))
        hm = QPushButton("−"); hp = QPushButton("+")
        hm.clicked.connect(lambda: self._resize("h", -1))
        hp.clicked.connect(lambda: self._resize("h", +1))
        size_row.addWidget(hm); size_row.addWidget(hp)
        size_row.addStretch(1)
        right.addLayout(size_row)
        body.addLayout(right, 1)
        outer.addLayout(body)

        # ── actions ─────────────────────────────────────────────────────────────
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        outer.addWidget(self._buttons)

    # ── file selection ────────────────────────────────────────────────────────────

    def _choose_file(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Library File", str(project.subdir("lib")),
            "Library Files (*.lib *.spi *.sp);;All Files (*)",
        )
        if not path:
            return
        try:
            defn = parse_subckt(path)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid library", str(exc))
            return

        self._defn = defn
        self._lib_path = path
        self._extra_w = self._extra_h = 0.0
        self._file.setText(Path(path).name)
        self._name.setText(defn.name)
        self._params.setText(
            ", ".join(f"{k}={v}" for k, v in defn.params) or "(none)"
        )
        sch = project.subdir("sch") / f"{defn.name}.slicap_sch"
        self._sch.setText(
            f"Found {sch.name}" if sch.is_file()
            else "(no matching .slicap_sch — symbol only)"
        )

        self._check_stale(Path(path), defn)

        self._pins.clear()
        self._pins.addItems(defn.ports)
        if self._pins.count():
            self._pins.setCurrentRow(0)
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(bool(defn.ports))
        self._refresh_preview()

    def _check_stale(self, lib_path: Path, defn: SubcktDef) -> None:
        """Warn if an existing generated symbol's interface no longer matches the
        library — i.e. ports (names/order) or params changed.  Compared
        semantically (not by mtime), so harmless internal edits don't trip it.
        Placing regenerates the symbol, so this is informational."""
        self._stale.setVisible(False)
        svg_path = lib_path.with_name(f"{defn.name}.svg")
        if not svg_path.is_file():
            return
        try:
            g = next(e for e in ET.parse(svg_path).getroot().iter(f"{_SVG_NS}g")
                     if e.get("data-prefix"))
        except (ET.ParseError, StopIteration, OSError):
            return
        old_nodes  = (g.get("data-nodes") or "").split()
        old_params = (g.get("data-params") or "").split()
        if old_nodes != defn.ports or old_params != [k for k, _ in defn.params]:
            self._stale.setText(
                "⚠ The library interface changed since the saved symbol "
                "(pins or parameters differ) — the symbol will be regenerated."
            )
            self._stale.setVisible(True)

    # ── pin reordering / preview ───────────────────────────────────────────────────

    def _move(self, delta: int) -> None:
        row = self._pins.currentRow()
        new = row + delta
        if row < 0 or new < 0 or new >= self._pins.count():
            return
        self._pins.insertItem(new, self._pins.takeItem(row))
        self._pins.setCurrentRow(new)
        self._refresh_preview()

    def _resize(self, which: str, delta: int) -> None:
        # One click = one grid cell per half (so the full width/height changes by
        # 2·GRID, staying symmetric and on-grid).  The user may shrink below the
        # auto-fit size all the way to the absolute floor (overlap is then theirs).
        hw_min, hh_min = min_half(self._defn, self.placement())
        if which == "w":
            self._extra_w = max(_FLOOR - hw_min, self._extra_w + delta * GRID_SIZE)
        else:
            self._extra_h = max(_FLOOR - hh_min, self._extra_h + delta * GRID_SIZE)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self._defn is None:
            return
        try:
            self._preview.set_symbol(_build_symbol(
                self._defn, self.placement(), self._extra_w, self._extra_h))
        except Exception:
            self._preview.set_symbol(None)

    # ── results ─────────────────────────────────────────────────────────────────

    def lib_path(self) -> str | None:
        return self._lib_path

    def subckt_def(self) -> SubcktDef | None:
        return self._defn

    def placement(self) -> list:
        return [self._pins.item(i).text() for i in range(self._pins.count())]

    def extra_size(self) -> tuple[float, float]:
        """Half-width / half-height added beyond the auto-fit minimum."""
        return (self._extra_w, self._extra_h)
