"""
Place Subcircuit dialog (Place → Subcircuit…).

Pick a subcircuit ``.lib`` file; the dialog parses its ``.subckt`` header and
shows the block's name, overridable parameters and whether a matching editable
schematic (``sch/<name>.slicap_sch``) is present.  A reorderable pin list (the
**visual** placement, clockwise from top-left) drives a live preview of the
block symbol with pin names; reordering only moves where each named pin is
drawn — the ``.subckt`` node order (and thus the netlist) is unchanged.

When the matching schematic is found, each pin's SIDE comes from the port
symbol's orientation in it (subcircuit.schematic_placement): the side counts
are then fixed and Up/Down only permutes the names through those slots.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QDialogButtonBox, QMessageBox, QWidget,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QByteArray

from . import project
from .config import GRID_SIZE
from .subcircuit import (parse_subckt, box_symbol_svg, reskin_symbol_svg,
                         SubcktDef, min_half, schematic_placement,
                         find_subckt_schematic, _normalize_placement, _FLOOR)
from .symbol_library import Symbol
from .component_item import draw_subckt_pin_names, _apply_symbol_colors

_SVG_NS = "{http://www.w3.org/2000/svg}"


def _build_symbol(defn: SubcktDef, placement,
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
        if self._sym.show_pinnames:
            draw_subckt_pin_names(p, self._sym.nodes, self._sym.pins)
        p.end()


class PlaceSubcircuitDialog(QDialog):
    """Create (or re-assign) a subcircuit's block symbol and place its first
    instance; afterwards the symbol is a palette citizen of the project.

    The symbol is either the GENERATED box, or ANY loaded symbol whose pin
    count matches the subcircuit's ports, re-skinned (Anton, 2026-08-04):
    an opamp macromodel gets the opamp artwork. The list below the chooser
    is then the port-to-pin MAPPING instead of the box pin placement.
    """

    def __init__(self, parent=None, sch_type='slicap', library=None):
        super().__init__(parent, Qt.Window)
        self._library = library
        self.setWindowTitle("New Subcircuit Symbol")
        self.setMinimumWidth(560)

        # Type-tagged names keep a SLiCAP and an NGspice subcircuit of the same
        # device from colliding (mirrors .slicap_sch / .spice_sch).
        self._lib_ext    = ".spice_lib" if sch_type == 'ngspice' else ".slicap_lib"
        self._sch_ext    = ".spice_sch" if sch_type == 'ngspice' else ".slicap_sch"
        self._sym_suffix = "_spice_symbol.svg" if sch_type == 'ngspice' else "_slicap_symbol.svg"
        self._defn: SubcktDef | None = None
        self._lib_path: str | None = None
        self._source_pins: list[str] = []
        self._extra_w: float = 0.0      # half-width added beyond the auto-fit min
        self._extra_h: float = 0.0      # half-height added beyond the auto-fit min
        # Pin layout read from the subcircuit's own schematic (port symbol
        # orientations), or None when no schematic supplies one.  The slot
        # PATTERN (side counts) is fixed by the schematic; Up/Down moves
        # names through it.
        self._sch_flat:   list | None = None    # initial clockwise pin order
        self._sch_counts: tuple | None = None   # (n_top, n_right, n_bottom, n_left)

        outer = QVBoxLayout(self)

        # ── library file picker ─────────────────────────────────────────────────
        file_row = QHBoxLayout()
        self._file = QLineEdit(); self._file.setReadOnly(True)
        self._file.setPlaceholderText(f"Select a subcircuit {self._lib_ext} file…")
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
        from PySide6.QtWidgets import QComboBox
        self._symbol = QComboBox()
        self._symbol.setToolTip(
            "The generated box, or any loaded symbol with a matching number "
            "of pins, re-skinned as this subcircuit's symbol.")
        self._symbol.currentIndexChanged.connect(self._on_symbol_choice)
        form.addRow("Symbol:", self._symbol)
        left.addLayout(form)

        self._pins_label = QLabel("Pin placement (top → clockwise):")
        left.addWidget(self._pins_label)
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
            f"Subcircuit Library (*{self._lib_ext});;All Files (*)",
        )
        if not path:
            return
        try:
            defn = parse_subckt(
                path, dialect=("ngspice" if self._lib_ext == ".spice_lib"
                               else "slicap"))
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
        # The schematic is part of the subcircuit package in lib/ (searched
        # beside the .lib first, then project lib/, then legacy sch/).
        sch = find_subckt_schematic(defn.name, self._sch_ext, lib_path=path)
        self._sch.setText(
            f"Found {sch.name}" if sch is not None
            else f"(no matching {self._sch_ext} — symbol only)"
        )
        # Pin sides as the subcircuit's own port symbols suggest them
        # (Anton, 2026-08-05); None → count-based clockwise fallback.
        place = schematic_placement(defn, sch) if sch is not None else None
        if place is not None:
            self._sch_flat, self._sch_counts = _normalize_placement(place)
        else:
            self._sch_flat = self._sch_counts = None

        self._check_stale(Path(path), defn)

        # symbol chooser: the generated box, plus every loaded symbol whose
        # pin COUNT matches the ports (its own generated symbol excluded)
        self._symbol.blockSignals(True)
        self._symbol.clear()
        self._symbol.addItem("Generated box")
        if self._library is not None:
            for name in self._library.names:
                sym = self._library.symbol(name)
                if (sym is not None and name != defn.name
                        and len(sym.pins) == len(defn.ports)):
                    self._symbol.addItem(name)
        self._symbol.setCurrentIndex(0)
        self._symbol.blockSignals(False)
        self._on_symbol_choice()
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(bool(defn.ports))

    def _check_stale(self, lib_path: Path, defn: SubcktDef) -> None:
        """Warn if an existing generated symbol's interface no longer matches the
        library — i.e. ports (names/order) or params changed.  Compared
        semantically (not by mtime), so harmless internal edits don't trip it.
        Placing regenerates the symbol, so this is informational."""
        self._stale.setVisible(False)
        svg_path = lib_path.with_name(f"{defn.name}{self._sym_suffix}")
        if not svg_path.is_file():
            return
        try:
            g = next(e for e in ET.parse(svg_path).getroot().iter(f"{_SVG_NS}g")
                     if e.get("data-prefix"))
        except (ET.ParseError, StopIteration, OSError):
            return
        old_nodes  = (g.get("data-nodes") or "").split()
        # metadata format: 'name|default|show_name|show_value; ...' - the
        # bare .split() of the OLD format flagged every regenerated symbol
        # as stale (fixed 2026-08-04); the legacy form still compares
        raw = g.get("data-params") or ""
        if "|" in raw:
            old_params = [entry.split("|")[0].strip()
                          for entry in raw.split(";") if entry.strip()]
        else:
            old_params = raw.split()
        if old_nodes != defn.ports or old_params != [k for k, _ in defn.params]:
            self._stale.setText(
                "⚠ The library interface changed since the saved symbol "
                "(pins or parameters differ) — the symbol will be regenerated."
            )
            self._stale.setVisible(True)

    # ── pin reordering / preview ───────────────────────────────────────────────────

    def _reskin_source(self) -> str | None:
        """The chosen existing symbol's name, or None for the generated box."""
        if self._symbol.currentIndex() <= 0 or self._library is None:
            return None
        return self._symbol.currentText()

    def _on_symbol_choice(self, *_args) -> None:
        """Switch the list between BOX pin placement and port-to-pin mapping."""
        if self._defn is None:
            return
        source = self._reskin_source()
        # rebuilding fires currentRowChanged per item; without the block the
        # preview ran against a HALF-BUILT mapping, printing one error per
        # item (Anton, 2026-08-04)
        self._pins.blockSignals(True)
        self._pins.clear()
        if source is None:
            if self._sch_flat is not None:
                self._pins_label.setText(
                    "Pin placement (sides from the subcircuit schematic):")
                self._pins.addItems(self._sch_flat)
            else:
                self._pins_label.setText("Pin placement (top → clockwise):")
                self._pins.addItems(self._defn.ports)
            self._source_pins = []
        else:
            self._pins_label.setText("Subcircuit port on each symbol pin "
                                     "(Up/Down moves the port):")
            sym = self._library.symbol(source)
            self._source_pins = list(sym.nodes)
            for pin, port in zip(self._source_pins, self._defn.ports):
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, port)
                self._pins.addItem(item)
            self._refresh_mapping_labels()
        if self._pins.count():
            self._pins.setCurrentRow(0)
        self._pins.blockSignals(False)
        self._refresh_preview()

    def _refresh_mapping_labels(self) -> None:
        for i in range(self._pins.count()):
            item = self._pins.item(i)
            item.setText("{0}  ←  {1}".format(
                self._source_pins[i],
                item.data(Qt.ItemDataRole.UserRole)))

    def mapping(self) -> dict:
        """``{symbol pin: subcircuit port}`` of the re-skin."""
        count = min(self._pins.count(), len(self._source_pins))
        return {self._source_pins[i]:
                self._pins.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(count)}

    def _move(self, delta: int) -> None:
        row = self._pins.currentRow()
        new = row + delta
        if row < 0 or new < 0 or new >= self._pins.count():
            return
        if self._reskin_source() is not None:
            # the PINS stay put (they are the artwork); the PORTS move
            role = Qt.ItemDataRole.UserRole
            a, b = self._pins.item(row), self._pins.item(new)
            a_port, b_port = a.data(role), b.data(role)
            a.setData(role, b_port)
            b.setData(role, a_port)
            self._refresh_mapping_labels()
        else:
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
            source = self._reskin_source()
            if source is not None:
                mapping = self.mapping()
                if len(mapping) != len(self._defn.ports):
                    return                    # mid-rebuild: nothing to draw yet
                svg = reskin_symbol_svg(self._library.symbol(source).g_xml,
                                        self._defn, mapping)
                g = next(e for e in ET.fromstring(svg).iter(f"{_SVG_NS}g")
                         if e.get("data-prefix"))
                self._preview.set_symbol(Symbol(g, "preview"))
                return
            self._preview.set_symbol(_build_symbol(
                self._defn, self.placement(), self._extra_w, self._extra_h))
        except Exception as exc:
            # NEVER silently: a blank preview hid a generator/parser
            # mismatch for weeks (Anton, 2026-08-04)
            print("Error: cannot build the block symbol: {0}".format(exc))
            self._preview.set_symbol(None)

    # ── results ─────────────────────────────────────────────────────────────────

    def lib_path(self) -> str | None:
        return self._lib_path

    def subckt_def(self) -> SubcktDef | None:
        return self._defn

    def placement(self):
        """The visual pin arrangement for box_symbol_svg: a per-side dict when
        the subcircuit schematic dictates the sides, else the flat clockwise
        list.  Up/Down only permutes names through the fixed slot pattern."""
        flat = [self._pins.item(i).text() for i in range(self._pins.count())]
        if self._sch_counts is None:
            return flat
        nt, nr, nb, _nl = self._sch_counts
        return {"top":    flat[:nt],
                "right":  flat[nt:nt + nr],
                "bottom": list(reversed(flat[nt + nr:nt + nr + nb])),
                "left":   list(reversed(flat[nt + nr + nb:]))}

    def extra_size(self) -> tuple[float, float]:
        """Half-width / half-height added beyond the auto-fit minimum."""
        return (self._extra_w, self._extra_h)
