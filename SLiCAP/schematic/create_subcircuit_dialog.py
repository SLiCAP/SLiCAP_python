"""
Create-subcircuit dialog (File → Save schematic with the "Subcircuit" box
ticked).

Shows the subcircuit name, the ordered list of port nodes (reorderable — the
order here *is* the .subckt node order), and an editable table of overridable
parameters. The name is the document title. "Save as" makes it editable: a
new name saves a copy of the package under that name (Anton, 2026-10-09).
"Save" opens the dialog while the node order is unsettled or while the title
is not a valid name. It keeps a valid name read-only. An empty or invalid name
is editable, so that the save can finish (2026-10-23, 2026-11-22).
:func:`subcircuit.is_subckt_name` owns the name rule.  On accept the window writes the schematic and the
subcircuit library, type-tagged so a SLiCAP and an NGspice device of the same
name don't collide: ``<title>.slicap_sch`` + ``<title>.slicap_lib`` for
SLiCAP schematics, ``<title>.spice_sch`` + ``<title>.spice_lib`` for NGspice
(with ``build_ngspice_subckt`` and a ``*``-commented title for the latter).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QListWidget, QPushButton,
    QTableWidgetItem, QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt
from .row_table import RowTable
from .sizing import chars
from .subcircuit import is_subckt_name


class CreateSubcircuitDialog(QDialog):
    def __init__(self, name: str, ports: list[str],
                 params: list | None = None, parent=None,
                 name_editable: bool = True):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create Subcircuit")
        self.setMinimumWidth(chars(self, 60))
        outer = QVBoxLayout(self)

        # ── name ───────────────────────────────────────────────────────────────
        head = QGridLayout()
        head.addWidget(QLabel("<b>Subcircuit name:</b>"), 0, 0)
        # Editable: the name is the .subckt name AND the stem of the files
        # in lib/. Typing another name saves a copy of the package under
        # that name and makes it the document title. A read-only label was
        # the previous form and was REJECTED: "Save as" could not rename a
        # subcircuit at all (Anton, 2026-10-09).
        self._name = QLineEdit(name)
        self._name.setPlaceholderText("letter, then letters, digits or _")
        self._name.setToolTip(
            "The .subckt name and the stem of the files in lib/.\n"
            "Another name saves a copy of the subcircuit under that name.")
        # Save keeps the name: the dialog then only settles the node order
        # (a new port). Save as makes it editable. Only a name that Create
        # Subcircuit accepts can be kept. Any other name is editable,
        # whatever the caller asked. That is an empty name on the first
        # save (Anton, 2026-10-23: the read-only empty field could not be
        # filled and the save was stuck). It is also a Title that is not
        # a valid name, such as "Input stage" (2026-11-22: the same
        # dead end, the locked name was refused).
        self._name.setReadOnly(not name_editable and is_subckt_name(name.strip()))
        head.addWidget(self._name, 0, 1)
        outer.addLayout(head)

        # ── ports (reorderable node list) ──────────────────────────────────────
        outer.addWidget(QLabel("Nodes (top → bottom = left → right node order):"))
        port_row = QHBoxLayout()
        self._ports = QListWidget()
        for p in ports:
            self._ports.addItem(p)
        if self._ports.count():
            self._ports.setCurrentRow(0)
        port_row.addWidget(self._ports)

        btn_col = QVBoxLayout()
        up = QPushButton("Up")
        dn = QPushButton("Down")
        up.clicked.connect(lambda: self._move(-1))
        dn.clicked.connect(lambda: self._move(+1))
        btn_col.addWidget(up)
        btn_col.addWidget(dn)
        btn_col.addStretch(1)
        port_row.addLayout(btn_col)
        outer.addLayout(port_row)

        if not ports:
            warn = QLabel("No ports found — add 'port' symbols and name them.")
            warn.setStyleSheet("color: #b00;")
            outer.addWidget(warn)

        # ── parameters ─────────────────────────────────────────────────────────
        # *params* None: the block's parameters are the sheet's parameter
        # table, not a list of their own (a system diagram, whose block
        # is its diagram; SystemExtensionSpecs.md 10.4.6)
        self._params = None
        if params is None:
            note = QLabel("Parameters: the sheet's parameter table (Insert > "
                          "Parameters) declares them, with their defaults.")
            note.setWordWrap(True)
            outer.addWidget(note)
        else:
            outer.addWidget(QLabel("Parameters (overridable defaults):"))
            self._params = RowTable(0, 2, add_row=lambda: self._add_param_row("", ""))
            self._params.setHorizontalHeaderLabels(["Name", "Default"])
            self._params.horizontalHeader().setStretchLastSection(True)
            for pair in params:
                self._add_param_row(*(list(pair) + ["", ""])[:2])
            outer.addWidget(self._params)

            param_btns = QHBoxLayout()
            add_btn = QPushButton("Add parameter")
            del_btn = QPushButton("Remove")
            add_btn.clicked.connect(lambda: self._add_param_row("", ""))
            del_btn.clicked.connect(self._remove_param_row)
            param_btns.addWidget(add_btn)
            param_btns.addWidget(del_btn)
            param_btns.addStretch(1)
            outer.addLayout(param_btns)

        # ── actions ────────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        create_btn = QPushButton("Create Subcircuit")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._on_create)
        buttons.addButton(create_btn, QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    # ── port reordering ─────────────────────────────────────────────────────────

    def _move(self, delta: int) -> None:
        row = self._ports.currentRow()
        new = row + delta
        if row < 0 or new < 0 or new >= self._ports.count():
            return
        item = self._ports.takeItem(row)
        self._ports.insertItem(new, item)
        self._ports.setCurrentRow(new)

    # ── parameter rows ───────────────────────────────────────────────────────────

    def _add_param_row(self, name: str, value: str) -> None:
        r = self._params.rowCount()
        self._params.insertRow(r)
        self._params.setItem(r, 0, QTableWidgetItem(name))
        self._params.setItem(r, 1, QTableWidgetItem(value))

    def _remove_param_row(self) -> None:
        r = self._params.currentRow()
        if r >= 0:
            self._params.removeRow(r)

    # ── create ───────────────────────────────────────────────────────────────────

    def _on_create(self) -> None:
        name = self.name()
        if not is_subckt_name(name):
            QMessageBox.warning(
                self, "Subcircuit name",
                f"'{name}' is not a valid subcircuit name.\n"
                "Use a letter, then letters, digits or underscores.")
            return
        if self._ports.count() == 0:
            if QMessageBox.question(
                self, "No ports",
                "This subcircuit has no ports. Create it anyway?",
            ) != QMessageBox.Yes:
                return
        self.accept()

    # ── results ──────────────────────────────────────────────────────────────────

    def name(self) -> str:
        return self._name.text().strip()

    def ports(self) -> list[str]:
        return [self._ports.item(i).text() for i in range(self._ports.count())]

    def params(self) -> list[list[str]]:
        if self._params is None:
            return []
        out: list[list[str]] = []
        for r in range(self._params.rowCount()):
            name = (self._params.item(r, 0) or QTableWidgetItem()).text().strip()
            val  = (self._params.item(r, 1) or QTableWidgetItem()).text().strip()
            if name:
                out.append([name, val])
        return out
