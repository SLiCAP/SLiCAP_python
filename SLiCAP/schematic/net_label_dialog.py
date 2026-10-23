from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLayout,
    QLineEdit, QCheckBox, QDialogButtonBox, QLabel, QRadioButton,
)
from PySide6.QtCore import Qt
from .sizing import chars


class NetLabelDialog(QDialog):
    def __init__(self, current_name: str | None, display: bool,
                 locked: bool = False, offer_dc: bool = False,
                 show_dc: bool = False, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Net Label")
        self.setMinimumWidth(chars(self, 40))
        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)

        form = QFormLayout()
        self._name_edit = QLineEdit(current_name or "")

        if locked:
            self._name_edit.setEnabled(False)   # disables input and greys out reliably
            form.addRow("Net name (port):", self._name_edit)
            outer.addLayout(form)
            note = QLabel("Name is set by the connected port and cannot be changed.")
            note.setWordWrap(True)
            note.setAlignment(Qt.AlignLeft)
            note.setStyleSheet("color: grey; font-style: italic;")
            outer.addWidget(note)
        else:
            self._name_edit.setPlaceholderText("leave blank for auto-number")
            form.addRow("Net name:", self._name_edit)
            outer.addLayout(form)

        self._display_cb = QCheckBox("Display net name on schematic")
        self._display_cb.setChecked(display)
        outer.addWidget(self._display_cb)
        # Typing a name checks "Display" (Anton, 2026-10-23): a name that is
        # not shown is invisible on the canvas and only the netlist knows
        # it. The user can still uncheck it before OK.
        self._name_edit.textEdited.connect(
            lambda text: self._display_cb.setChecked(True) if text.strip() else None)

        # DC operating-point back-annotation — NGspice schematics only.
        self._dc_cb = QCheckBox("Show DC operating voltage")
        self._dc_cb.setChecked(show_dc)
        self._dc_cb.setToolTip(
            "Places a 'V: <value>' text on this wire segment; the value is\n"
            "updated after an operating-point (op) run and greyed when the\n"
            "schematic changed since that run.")
        if offer_dc:
            outer.addWidget(self._dc_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        if not locked:
            self._name_edit.setFocus()
        else:
            self._display_cb.setFocus()

    def net_name(self) -> str | None:
        text = self._name_edit.text().strip()
        return text if text else None

    def display(self) -> bool:
        return self._display_cb.isChecked()

    def show_dc(self) -> bool:
        return self._dc_cb.isChecked()


class NetConflictDialog(QDialog):
    """Two named nets were just joined into one. The user picks the name
    the net keeps; the other label disappears (Anton, 2026-10-23: direct
    feedback at the moment of the connection, a forced choice with radio
    buttons, as in Pulsonix). There is no Cancel: Undo reverts the
    connection itself."""

    def __init__(self, names: list, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Net names")
        outer = QVBoxLayout()
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(outer)
        note = QLabel("This connection joins nets with different names.\n"
                      "Which name does the net keep? (Undo reverts the connection.)")
        note.setWordWrap(True)
        outer.addWidget(note)
        self._buttons = []
        for i, name in enumerate(names):
            rb = QRadioButton(name)
            rb.setChecked(i == 0)
            outer.addWidget(rb)
            self._buttons.append(rb)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        outer.addWidget(buttons)

    def chosen(self) -> str:
        for rb in self._buttons:
            if rb.isChecked():
                return rb.text()
        return self._buttons[0].text()
