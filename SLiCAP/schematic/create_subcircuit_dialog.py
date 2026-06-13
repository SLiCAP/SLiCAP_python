"""
Create-subcircuit dialog (File → Save with the "Subcircuit" box ticked).

Shows the subcircuit name (the document title), the ordered list of port nodes
(reorderable — the order here *is* the .subckt node order), and an editable
table of overridable parameters.  The window writes ``<title>.slicap_sch`` to
``sch/`` and ``<title>.lib`` to ``lib/`` of the project on accept.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QListWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt


class CreateSubcircuitDialog(QDialog):
    def __init__(self, name: str, ports: list[str],
                 params: list | None = None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create Subcircuit")
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)

        # ── name ───────────────────────────────────────────────────────────────
        head = QGridLayout()
        head.addWidget(QLabel("<b>Subcircuit name:</b>"), 0, 0)
        head.addWidget(QLabel(name or "(set a title in Document Properties)"), 0, 1)
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
        outer.addWidget(QLabel("Parameters (overridable defaults):"))
        self._params = QTableWidget(0, 2)
        self._params.setHorizontalHeaderLabels(["Name", "Default"])
        self._params.horizontalHeader().setStretchLastSection(True)
        for pair in (params or []):
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
        if self._ports.count() == 0:
            if QMessageBox.question(
                self, "No ports",
                "This subcircuit has no ports. Create it anyway?",
            ) != QMessageBox.Yes:
                return
        self.accept()

    # ── results ──────────────────────────────────────────────────────────────────

    def ports(self) -> list[str]:
        return [self._ports.item(i).text() for i in range(self._ports.count())]

    def params(self) -> list[list[str]]:
        out: list[list[str]] = []
        for r in range(self._params.rowCount()):
            name = (self._params.item(r, 0) or QTableWidgetItem()).text().strip()
            val  = (self._params.item(r, 1) or QTableWidgetItem()).text().strip()
            if name:
                out.append([name, val])
        return out
