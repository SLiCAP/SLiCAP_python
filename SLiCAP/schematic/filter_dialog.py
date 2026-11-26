"""Make filter dialog: the instruction ``FLT1 = sl.makeFilter(...)``.

A filter of the project (a design script in ``lib/``) is made for ONE sample
period and ONE set of parameter values, for its frequency and time traces
(Anton, 2026-11-25). The dialog asks for exactly what makeFilter() needs:

- the design script, from those in ``lib/`` that make a filter;
- Ts: the clock period of a non-stationary filter. A stationary filter runs
  at its own Ts, so the field then shows that Ts, greyed out and not
  editable. A Ts pin takes its value from the parameter table;
- the parameter values: the parameter-source table of the instruction
  dialogs, "system" (the sheet parameters of a diagram that runs the
  design), specs or user, written as ``params=sl.selectPars(...)``.

makeFilter() raises an error on a wrong argument. Here they cannot occur:
"Add instruction" stays disabled until everything is given (Anton,
2026-11-25: "if we can prevent errors, we do").

The facts of a design (its pins, stationary or not, its own Ts) are read by
running its script in a child process (``system_script.probe_design``), as
the filter block does when it is placed.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget,
)

from .instr_file import bound_names, quoted, spec_var_name
from .sizing import cap_chars, name_width
from .traces_dialog import next_name
from .value_fields import watch

#: the choice of the system combo when no diagram runs the design
NO_SYSTEM = "(no system diagram)"


def _positive(text: str) -> bool:
    """True for a positive number in SLiCAP notation."""
    from SLiCAP.SLiCAPmath import _checkNumber
    value = _checkNumber(text.strip()) if str(text).strip() else None
    return value is not None and value > 0


def make_filter_line(name: str, file: str, Ts: str = "", params: str = "") -> str:
    """The instruction ``NAME = sl.makeFilter("<file>", Ts=..., params=...)``.
    *Ts* and *params* are left out when empty."""
    parts = [quoted(file)]
    if Ts:
        parts.append("Ts=" + quoted(Ts))
    if params:
        parts.append("params=" + params)
    return "%s = sl.makeFilter(%s)" % (name, ", ".join(parts))


class MakeFilterDialog(QDialog):
    """The dialog behind Instruction -> Make filter… of a system sheet.

    *designs*: ``(file, name)`` per filter design of the project
    (``system_dialect.project_designs``). *probe*: ``probe(file, name) ->
    {"params", "stationary", "Ts"}``, by default the design script run in a
    child process. *runs*: ``runs(file) -> {stem: {param: value}}``, the
    diagrams that run the design, by default ``system_script.design_runs``.
    """

    def __init__(self, designs, existing_text: str = "", root=".",
                 csv_dir: str = "", preset: str = "specs", probe=None,
                 runs=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Make filter")
        self._designs = list(designs)
        self._existing_text = existing_text or ""
        self._taken = bound_names(self._existing_text)
        self._root = Path(root)
        self._csv_dir = csv_dir
        self._preset = preset
        self._probe = probe or self._probe_script
        self._runs_of = runs or self._design_runs
        self._facts = {}                # file -> probed facts, or an error text
        self._runs = {}                 # stem -> sheet parameters, for the design
        self._table = None

        outer = QVBoxLayout(self)
        grid = QGridLayout()
        outer.addLayout(grid)
        grid.addWidget(QLabel("Filter variable name:"), 0, 0)
        self._name = QLineEdit(next_name("FLT", self._taken))
        self._name.setMaximumWidth(name_width(self._name))
        self._name.textChanged.connect(self._update)
        grid.addWidget(self._name, 0, 1)

        grid.addWidget(QLabel("Design script:"), 1, 0)
        self._script = QComboBox()
        for file, name in self._designs:
            self._script.addItem("%s   (%s)" % (file, name), file)
        self._script.currentIndexChanged.connect(self._on_script)
        grid.addWidget(self._script, 1, 1)

        grid.addWidget(QLabel("Sample period Ts:"), 2, 0)
        ts_row = QHBoxLayout()
        self._ts = QLineEdit()
        cap_chars(self._ts, 14)
        watch(self._ts, "number")
        self._ts.textChanged.connect(self._update)
        # what the Ts field holds; a tooltip would be reset by watch()
        self._ts_note = QLabel()
        self._ts_note.setStyleSheet("color: grey;")
        ts_row.addWidget(self._ts)
        ts_row.addWidget(self._ts_note, 1)
        grid.addLayout(ts_row, 2, 1)

        grid.addWidget(QLabel("System diagram:"), 3, 0)
        self._system = QComboBox()
        self._system.setToolTip(
            "A system diagram that runs this design: its sheet parameters are "
            "the 'system' values of the table")
        self._system.currentIndexChanged.connect(self._on_system)
        grid.addWidget(self._system, 3, 1)
        grid.setColumnStretch(1, 1)

        self._table_box = QWidget()
        self._table_lay = QVBoxLayout(self._table_box)
        self._table_lay.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._table_box)

        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet("color: #b34700;")
        self._error.setVisible(False)
        outer.addWidget(self._error)

        self._preview = QLabel()
        self._preview.setWordWrap(True)
        self._preview.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._preview.setStyleSheet("font-family: monospace; font-size: 9pt;")
        outer.addWidget(self._preview)

        buttons = QDialogButtonBox()
        self._add_btn = buttons.addButton(
            "Add instruction", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._on_script()

    # ── the design ────────────────────────────────────────────────────────

    def _probe_script(self, file, name) -> dict:
        from .system_script import probe_design
        return probe_design(self._root, file, name)

    def _design_runs(self, file) -> dict:
        from .system_script import design_runs
        return design_runs(self._root, [file])

    def _chosen(self):
        """``(file, name)`` of the chosen design, ``(None, None)`` without."""
        file = self._script.currentData()
        return (file, dict(self._designs)[file]) if file else (None, None)

    def facts(self) -> dict:
        """What the chosen script makes: ``{"params", "stationary", "Ts"}``,
        or ``{}`` when it failed or nothing is chosen. Probed once per
        script."""
        file, name = self._chosen()
        if file is None:
            return {}
        if file not in self._facts:
            from .netlist import NetlistError
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self._facts[file] = self._probe(file, name)
            except NetlistError as exc:
                self._facts[file] = "\n".join(exc.errors)
            finally:
                QApplication.restoreOverrideCursor()
        found = self._facts[file]
        return found if isinstance(found, dict) else {}

    def _on_script(self, *_args):
        file, _name = self._chosen()
        facts = self.facts()
        problem = self._facts.get(file) if file else None
        failed = isinstance(problem, str)
        self._error.setText(problem if failed else "")
        self._error.setVisible(failed)
        self._show_ts(facts)
        try:
            self._runs = self._runs_of(file) if file else {}
        except Exception:                      # a broken run script lists nothing
            self._runs = {}
        self._system.blockSignals(True)
        self._system.clear()
        for stem in self._runs:
            self._system.addItem(stem, stem)
        self._system.addItem(NO_SYSTEM, "")
        self._system.blockSignals(False)
        self._build_table()
        self._update()

    def _show_ts(self, facts: dict) -> None:
        """A stationary filter runs at its own Ts: shown, greyed out, not
        editable (Anton, 2026-11-25). Its Ts pin: the parameter's name, its
        value in the table. A non-stationary filter: the clock period,
        typed here."""
        own = facts.get("Ts")
        if facts and facts.get("stationary", True):
            self._ts.setText("" if own is None else str(own))
            self._ts.setEnabled(False)
            self._ts_note.setText(
                "the filter's own (stationary)" if not isinstance(own, str)
                else "the value of parameter %s, in the table" % own)
        else:
            if not self._ts.isEnabled():
                self._ts.clear()
            self._ts.setEnabled(bool(facts))
            self._ts.setPlaceholderText("e.g. 10u")
            self._ts_note.setText("the clock period (non-stationary)"
                                  if facts else "")

    # ── the parameter values ──────────────────────────────────────────────

    def _on_system(self, *_args):
        self._build_table()
        self._update()

    def _build_table(self) -> None:
        """One row per pin of the filter, "system" where the chosen diagram's
        sheet defines it. A rebuilt table keeps what the previous one
        selected."""
        from .par_source_table import ParSourceTable, CIRCUIT, SPECS, USER
        from .design_data_panel import find_spec_csvs
        previous = self._params_source()
        if self._table is not None:
            self._table_lay.removeWidget(self._table)
            self._table.deleteLater()
            self._table = None
        pins = list(self.facts().get("params") or [])
        self._table_box.setVisible(bool(pins))
        if not pins:
            return
        sheet = self._runs.get(self._system.currentData() or "", {})
        spec_files = ([p.name for p in find_spec_csvs(Path(self._csv_dir))]
                      if self._csv_dir else [])
        table = ParSourceTable({p: sheet[p] for p in pins if p in sheet},
                               [p for p in pins if p not in sheet],
                               spec_files, self._csv_dir, self._preset,
                               positions=(CIRCUIT, SPECS, USER),
                               title="Filter parameters (params=)",
                               labels={CIRCUIT: "system"})
        if previous:
            table.load_from_source(previous)
        table.changed.connect(self._update)
        self._table_lay.addWidget(table)
        self._table = table

    def _params_source(self) -> str:
        """The ``params=`` value: ``sl.selectPars("<diagram>", ...)``, every
        value read when the line runs. ``None`` as the circuit when no
        diagram is chosen. "" without parameters."""
        table = self._table
        if table is None:
            return ""
        stem = self._system.currentData() or ""
        cir = quoted(stem) if stem else "None"
        if table.mode() == "circuit":
            # makeFilter knows no diagram: "all from the system" is written
            from .par_source_table import CIRCUIT
            return "sl.selectPars({0}, circuit=[{1}])".format(
                cir, ", ".join(quoted(n) for n in table.selection()[CIRCUIT]))
        return table.emission(cir) or ""

    def _params_complete(self) -> bool:
        """Every pin has a value: a valid user value, or a specification
        item with a value in the chosen file."""
        table = self._table
        if table is None:
            return True
        from .par_source_table import SPECS
        if not table.is_valid():
            return False
        values = table.spec_values()
        return all(values.get(n, "").strip() for n in table.selection()[SPECS])

    # ── result ────────────────────────────────────────────────────────────

    def _name_ok(self) -> bool:
        name = self._name.text().strip()
        return name.isidentifier() and name not in self._taken

    def _ts_text(self) -> str:
        """Ts as written: only for a non-stationary filter."""
        facts = self.facts()
        if not facts or facts.get("stationary", True):
            return ""
        return self._ts.text().strip()

    def is_complete(self) -> bool:
        facts = self.facts()
        if not facts or not self._name_ok():
            return False
        if not facts.get("stationary", True) and not _positive(self._ts.text()):
            return False
        return self._params_complete()

    def generated_snippet(self) -> str:
        """The instruction, preceded by the line that loads the spec file
        when the table reads specs and the file does not load it yet."""
        file, _name = self._chosen()
        if file is None:
            return ""
        params = self._params_source()
        line = make_filter_line(self._name.text().strip(), file,
                                self._ts_text(), params)
        spec_file = (self._table.spec_file()
                     if self._table is not None and self._table.spec_var() else "")
        var = spec_var_name(spec_file) if spec_file else ""
        if var and var in params and var not in self._taken:
            return "%s = sl.csv2specs(%s)\n%s" % (var, quoted(spec_file), line)
        return line

    def _update(self, *_args):
        ok = self.is_complete()
        self._add_btn.setEnabled(ok)
        if self._table is not None:
            self._table.show_reason()
        self._preview.setText(self.generated_snippet() if ok else "")
