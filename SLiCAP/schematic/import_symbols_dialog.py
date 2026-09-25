"""Tools -> Import symbols from file... (Anton, 2026-09-25).

The user draws symbols in any SVG tool (the format is documented on the
manual page "Symbol libraries"); this dialog reads a symbol library file, a
``.slicap_sym``, ``.spice_sym`` or plain ``.svg`` holding one or more
``<g id=... data-prefix=...>`` symbols, validates each one with the same
parser the editor uses, lets the user tick the ones to import, and writes
each ticked symbol as its own file into the project's ``lib/`` folder under
the dialect extension of the schematic the dialog was opened from:
``lib/<name>.slicap_sym`` or ``lib/<name>.spice_sym``. From there the
library loader offers it on every schematic of that type, exactly like a
subcircuit block symbol: the frozen bundle caches it on save, "Load symbols
from library" heals it. The dialect is NOT a tag inside the symbol: the same
artwork may serve both, and the content cannot prove a dialect anyway.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDialogButtonBox, QFileDialog,
    QMessageBox, QHeaderView,
)

from .symbol_library import Symbol, SymbolError, SVG_NS, symbol_file_name
from .sizing import chars


def scan_symbol_file(path) -> list:
    """Every ``<g id data-prefix>`` in *path* as (name, symbol_or_None,
    error_text, g_element). A symbol that does not parse is listed with
    its reason, so the user sees what to fix."""
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(str(path), parser).getroot()
    found = []
    for g in root.iter(f"{{{SVG_NS}}}g"):
        if not (g.get("id") and g.get("data-prefix")):
            continue
        try:
            found.append((g.get("id"), Symbol(g, Path(path).name), "", g))
        except SymbolError as exc:
            found.append((g.get("id"), None, str(exc), g))
    return found


def write_symbol_file(g, libdir, name: str, sch_type: str) -> Path:
    """Write one symbol ``<g>`` as ``libdir/<name>.<dialect ext>`` (plain
    SVG inside). Returns the path."""
    libdir = Path(libdir)
    libdir.mkdir(parents=True, exist_ok=True)
    target = libdir / symbol_file_name(name, sch_type)
    body = ET.tostring(g, encoding="unicode")
    target.write_text('<svg xmlns="%s">\n  %s\n</svg>\n' % (SVG_NS, body),
                      encoding="utf-8")
    return target


class ImportSymbolsDialog(QDialog):
    """Pick a symbol file, tick symbols, import them into the project lib/."""

    def __init__(self, parent, sch_type: str, library, libdir):
        super().__init__(parent)
        self._sch_type = sch_type
        self._library = library
        self._libdir = Path(libdir)
        self._found = []
        self.imported: list[Path] = []
        kind = "NGspice" if sch_type == "ngspice" else "SLiCAP"
        self.setWindowTitle(f"Import symbols from file ({kind} schematic)")
        self.setMinimumWidth(chars(self, 91))
        lay = QVBoxLayout(self)

        row = QHBoxLayout()
        self._path = QLineEdit()
        self._path.setPlaceholderText("a .slicap_sym, .spice_sym or .svg symbol library file")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(QLabel("File:")); row.addWidget(self._path, 1); row.addWidget(browse)
        lay.addLayout(row)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Import", "Name", "Prefix", "Pins", "Description / problem"])
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

        self._note = QLabel(f"Imported symbols are stored as lib/<name>{symbol_file_name('', sch_type)} "
                            f"and offered on every {kind} schematic of this project.")
        self._note.setWordWrap(True)
        lay.addWidget(self._note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _browse(self):
        # Qt's own chooser for every dialog: AA_DontUseNativeDialogs in
        # main.py (the GTK chooser choked on symbol files without a size).
        path, _ = QFileDialog.getOpenFileName(
            self, "Symbol library file", str(self._libdir.parent),
            "Symbol files (*.slicap_sym *.spice_sym *.svg);;All files (*)")
        if path:
            self._path.setText(path)
            self.load(path)

    def load(self, path) -> None:
        """Fill the table from *path* (also used without the file dialog)."""
        try:
            self._found = scan_symbol_file(path)
        except (ET.ParseError, OSError) as exc:
            QMessageBox.critical(self, "Import symbols", f"Cannot read {path}:\n{exc}")
            self._found = []
        self._table.setRowCount(0)
        for name, sym, error, _g in self._found:
            r = self._table.rowCount(); self._table.insertRow(r)
            tick = QTableWidgetItem()
            tick.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                          if sym is not None else Qt.ItemFlag.ItemIsEnabled)
            tick.setCheckState(Qt.CheckState.Checked if sym is not None else Qt.CheckState.Unchecked)
            self._table.setItem(r, 0, tick)
            self._table.setItem(r, 1, QTableWidgetItem(name))
            self._table.setItem(r, 2, QTableWidgetItem(sym.prefix if sym else ""))
            self._table.setItem(r, 3, QTableWidgetItem(str(len(sym.nodes)) if sym else ""))
            text = error if sym is None else (sym.description or "")
            if sym is not None and self._library is not None and self._library.symbol(name) is not None:
                text = (text + "  " if text else "") + "[overrides the existing symbol of this name]"
            self._table.setItem(r, 4, QTableWidgetItem(text))
        if not self._found:
            QMessageBox.information(self, "Import symbols",
                                    "No symbol found: a symbol is a <g> element with an id and a data-prefix attribute.")

    def selected(self) -> list:
        """(name, g) of the ticked, valid symbols."""
        out = []
        for r, (name, sym, _e, g) in enumerate(self._found):
            item = self._table.item(r, 0)
            if sym is not None and item is not None and item.checkState() == Qt.CheckState.Checked:
                out.append((name, g))
        return out

    def _accept(self):
        chosen = self.selected()
        if not chosen:
            QMessageBox.information(self, "Import symbols", "Nothing ticked.")
            return
        self.imported = [write_symbol_file(g, self._libdir, name, self._sch_type)
                         for name, g in chosen]
        self.accept()
