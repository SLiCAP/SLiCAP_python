"""
Change symbol dialog (Properties → Change symbol…, Anton, 2026-09-27).

A placed component gets another symbol: one of the schematic's library
with the same number of pins, and for a built-in element type the same
prefix (another prefix would be another element, not another look).

For a subcircuit (prefix X) any symbol with the right pin count qualifies.
With the ports assigned to the pins in the symbol's own order the component
simply takes that library symbol, by name, so Tools → Load symbols from
library keeps it (Anton, 2026-09-27: a copy under the old name reverted).
Only a changed assignment needs a copy: the artwork re-skinned the way
Place → Subcircuit does it (``subcircuit.reskin_symbol_svg``), named after
the component's model and written into the project's lib folder, the
ports on the pin markers, so the netlist order is unchanged.  For a
built-in element the pin order is the element's syntax, which a symbol
drawn for that prefix already follows; it is not remapped here.
"""
import re
import xml.etree.ElementTree as ET

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox,
)
from PySide6.QtCore import Qt

from .symbol_library import Symbol
from .subcircuit import SubcktDef, reskin_symbol_svg
from .place_subcircuit_dialog import _SymbolPreview

_SVG_NS = "{http://www.w3.org/2000/svg}"


def candidates(item, library) -> list[str]:
    """Names of the library symbols a component may switch to."""
    n = len(item.symbol.pins)
    prefix = item.prefix
    out = []
    for name in library.names:
        sym = library.symbol(name)
        if sym is None or len(sym.pins) != n:
            continue
        if prefix != "X" and sym.prefix != prefix:
            continue
        out.append(name)
    return out


class ChangeSymbolDialog(QDialog):
    def __init__(self, item, library, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Change symbol — {item.instance_id}")
        self._item = item
        self._library = library
        self._is_sub = item.prefix == "X"
        self._source_pins: list[str] = []

        outer = QVBoxLayout(self)
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Symbol (same number of pins"
                              + ("" if self._is_sub else ", same element type") + "):"))
        self._list = QListWidget()
        for name in candidates(item, library):
            it = QListWidgetItem(name)
            sym = library.symbol(name)
            if sym is not None and sym.description:
                it.setToolTip(sym.description)
            self._list.addItem(it)
            if name == item.symbol_name:
                self._list.setCurrentItem(it)
        left.addWidget(self._list, 1)
        row.addLayout(left, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Preview:"))
        self._preview = _SymbolPreview()
        right.addWidget(self._preview, 1)
        if self._is_sub:
            right.addWidget(QLabel("Subcircuit port on each symbol pin (Up/Down moves the port):"))
            self._pins = QListWidget()
            right.addWidget(self._pins)
            btns = QHBoxLayout()
            up, down = QPushButton("Up"), QPushButton("Down")
            up.clicked.connect(lambda: self._move(-1))
            down.clicked.connect(lambda: self._move(+1))
            btns.addWidget(up); btns.addWidget(down); btns.addStretch(1)
            right.addLayout(btns)
        else:
            self._pins = None
        row.addLayout(right, 1)
        outer.addLayout(row, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self._ok = buttons.button(QDialogButtonBox.Ok)

        self._list.currentItemChanged.connect(lambda *_: self._on_choice())
        self._on_choice()

    # ── choice and mapping ────────────────────────────────────────────────────

    def chosen_name(self) -> str | None:
        it = self._list.currentItem()
        return it.text() if it is not None else None

    def _on_choice(self) -> None:
        name = self.chosen_name()
        self._ok.setEnabled(name is not None)
        if self._pins is not None:
            self._pins.blockSignals(True)
            self._pins.clear()
            self._source_pins = []
            sym = self._library.symbol(name) if name else None
            if sym is not None:
                self._source_pins = list(sym.nodes)
                # the current symbol's markers already carry the ports: keep
                # that assignment where the names match, else by position
                ports = list(self._item.symbol.nodes)
                assigned = [p if p in ports else None for p in self._source_pins]
                rest = [p for p in ports if p not in assigned]
                for i, a in enumerate(assigned):
                    if a is None:
                        assigned[i] = rest.pop(0)
                for port in assigned:
                    it = QListWidgetItem()
                    it.setData(Qt.ItemDataRole.UserRole, port)
                    self._pins.addItem(it)
                self._refresh_mapping_labels()
                if self._pins.count():
                    self._pins.setCurrentRow(0)
            self._pins.blockSignals(False)
        self._refresh_preview()

    def _refresh_mapping_labels(self) -> None:
        for i in range(self._pins.count()):
            it = self._pins.item(i)
            it.setText("{0}  ←  {1}".format(self._source_pins[i], it.data(Qt.ItemDataRole.UserRole)))

    def mapping(self) -> dict:
        """``{symbol pin: subcircuit port}`` (subcircuits only)."""
        if self._pins is None:
            return {}
        count = min(self._pins.count(), len(self._source_pins))
        return {self._source_pins[i]: self._pins.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(count)}

    def _move(self, delta: int) -> None:
        row = self._pins.currentRow()
        new = row + delta
        if row < 0 or new < 0 or new >= self._pins.count():
            return
        role = Qt.ItemDataRole.UserRole
        a, b = self._pins.item(row), self._pins.item(new)
        a_port, b_port = a.data(role), b.data(role)
        a.setData(role, b_port); b.setData(role, a_port)
        self._refresh_mapping_labels()
        self._pins.setCurrentRow(new)
        self._refresh_preview()

    # ── result ────────────────────────────────────────────────────────────────

    def positional(self) -> bool:
        """True when the ports sit on the pins in the symbol's own order:
        the netlist takes the pins by position, so the library symbol
        serves as it is."""
        cur = list(self._item.symbol.nodes)
        m = self.mapping()
        return all(m.get(pin) == port for pin, port in zip(self._source_pins, cur))

    def _copy_name(self) -> str:
        """The name of a re-skinned copy: the component's model, as Place ->
        Subcircuit names a block's symbol; a placeholder model falls back to
        <symbol>_<refdes>."""
        model = (self._item.model or "").strip()
        if re.match(r"^[A-Za-z0-9_\-]+$", model):
            return model
        return f"{self.chosen_name()}_{self._item.instance_id}"

    def reskinned_svg(self) -> str | None:
        """The re-skinned copy as an SVG document (a subcircuit with a
        changed port assignment only): to be written into the project's
        lib folder. None when the library symbol serves as it is."""
        name = self.chosen_name()
        if not self._is_sub or name is None or self.positional():
            return None
        source = self._library.symbol(name)
        if source is None:
            return None
        cur = self._item.symbol
        defn = SubcktDef(name=self._copy_name(), ports=list(cur.nodes),
                         params=list(cur.param_defaults.items()))
        return reskin_symbol_svg(source.g_xml, defn, self.mapping())

    def new_symbol(self) -> Symbol | None:
        """The symbol the component switches to."""
        name = self.chosen_name()
        if name is None:
            return None
        svg = self.reskinned_svg()
        if svg is None:
            return self._library.symbol(name)
        g = next(e for e in ET.fromstring(svg).iter(f"{_SVG_NS}g") if e.get("data-prefix"))
        return Symbol(g, "change symbol")

    def _refresh_preview(self) -> None:
        try:
            self._preview.set_symbol(self.new_symbol())
        except Exception as exc:
            print("Error: cannot build the symbol preview: {0}".format(exc))
            self._preview.set_symbol(None)
