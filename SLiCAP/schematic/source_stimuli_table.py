"""Per-run source-stimulus table for the NGspice instruction dialog.

One row per independent source; the source keeps its two nodes and gets a
single stimulus for THIS run (``stimuli={"V1": ["AC", "1", "0"], …}`` — the
flat one-stimulus-per-source format consumed by ``_apply_stimuli`` in
SLiCAPngspice).  The stimulus is entered with the SAME dialog used on the
canvas (:class:`SourceStimuliDialog`), filtered to the analysis's domain:

    op / dc / dc_temp → DC        ac / noise → AC        tran → TRAN

A source can appear in only one row: once chosen, it is removed from the other
rows' dropdowns.  Because a stimulus is domain-specific, switching the analysis
tab (domain) clears the table.

PWL waveforms reference an external data file and cannot be inlined into the
flat per-run override, so selecting PWL here is rejected with a note — define a
PWL source on the schematic instead.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QAbstractItemView, QHeaderView, QMessageBox,
)

from .component_item import strip_braces
from .source_stimuli_dialog import (
    SourceStimuliDialog, _WAVEFORM_FIELDS, _param_key,
)

# Analysis type (tab key) → the single stimulus domain it uses.
_ANALYSIS_DOMAIN = {
    "op": "dc", "dc": "dc", "dc_temp": "dc",
    "ac": "ac", "noise": "ac", "tran": "tran",
}

_DOMAIN_HINT = {
    "dc":   "DC operating value",
    "ac":   "AC small-signal magnitude and phase",
    "tran": "a transient waveform (SIN, PULSE, …)",
}


# ── flat-list ⇄ params-dict conversion ─────────────────────────────────────────
# The backend stimuli= format is a flat list ``[type, arg1, …]`` (one stimulus
# per source); SourceStimuliDialog works in the schematic's params dict.  These
# translate between the two for the active domain only.

def _flat_to_params(domain: str, flat) -> dict:
    """Seed a params dict for SourceStimuliDialog from a flat stimulus list."""
    if not flat:
        return {}
    typ  = str(flat[0]).upper()
    args = [str(a) for a in flat[1:]]
    if domain == "dc":
        return {"dc": " ".join(args)}
    if domain == "ac":
        return {"ac": " ".join(args)}
    # tran: restore the waveform radio + per-field edits (stored un-braced)
    params = {"_tran_type": typ}
    raw = [strip_braces(a) for a in args]
    for field, val in zip(_WAVEFORM_FIELDS.get(typ, []), raw):
        params[_param_key(typ, field)] = val
    params["tran"] = f"{typ}({' '.join('{' + v + '}' for v in raw)})"
    return params


def _params_to_flat(domain: str, params: dict):
    """Read a flat stimulus list back from a SourceStimuliDialog params dict.

    Returns None when the domain's section was left empty, or for PWL (not
    representable as an inline per-run stimulus)."""
    if domain == "dc":
        v = params.get("dc", "").strip()
        return ["DC", *v.split()] if v else None
    if domain == "ac":
        v = params.get("ac", "").strip()
        return ["AC", *v.split()] if v else None
    # tran
    tran = params.get("tran", "").strip()
    typ  = params.get("_tran_type", "").strip()
    if not tran or not typ or tran == "_PWL_":
        return None
    inner = tran[tran.find("(") + 1: tran.rfind(")")]
    return [typ, *inner.split()]


def _summary(flat) -> str:
    """Human/netlist-style rendering of a flat stimulus for the row button.

    Mirrors ``_format_stimulus`` in SLiCAPngspice; kept local so the schematic
    editor subprocess need not import the numpy/sympy-heavy analysis backend."""
    typ  = str(flat[0]).upper()
    args = " ".join(str(a) for a in flat[1:])
    if typ in ("AC", "DC"):
        return f"{typ} {args}".strip()
    return f"{typ}({args})"


class SourceStimuliTable(QGroupBox):
    """Checkable source-stimulus table (see the module docstring)."""

    changed = Signal()

    def __init__(self, sources=(), domain: str = "dc", parent=None):
        super().__init__(
            "Source stimuli (stimuli=; unchecked = netlist stimuli)", parent)
        self._sources = [str(s) for s in sources]
        self._domain = domain
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(lambda *_: self.changed.emit())

        outer = QVBoxLayout(self)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Source", "Stimulus"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # narrow source
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(110)
        outer.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self.add_row())
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_selected_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        outer.addLayout(btn_row)

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(self._hint)
        self._update_hint()

    # ── rows ────────────────────────────────────────────────────────────────

    def add_row(self, source: str = "", stim=None) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        combo = QComboBox()                       # fixed list — no free text
        combo.currentIndexChanged.connect(self._on_source_changed)
        self._table.setCellWidget(row, 0, combo)

        btn = QPushButton()
        btn._stim = list(stim) if stim else None
        btn.clicked.connect(lambda _=False, b=btn: self._define(b))
        self._table.setCellWidget(row, 1, btn)

        self._refresh_sources()
        if source:
            combo.setCurrentText(source)
        self._update_button(btn)
        self.changed.emit()

    def _remove_selected_row(self) -> None:
        rows = sorted({i.row() for i in self._table.selectedIndexes()},
                      reverse=True)
        if not rows and self._table.rowCount():
            rows = [self._table.rowCount() - 1]
        for r in rows:
            self._table.removeRow(r)
        self._refresh_sources()
        self.changed.emit()

    def _row_source(self, row: int) -> str:
        c = self._table.cellWidget(row, 0)
        return c.currentText().strip() if c else ""

    def _on_source_changed(self, *_):
        self._refresh_sources()
        self.changed.emit()

    def _refresh_sources(self) -> None:
        """Rebuild each row's dropdown so an already-chosen source is offered
        only in its own row (a source may carry one stimulus per run)."""
        used = {self._row_source(r) for r in range(self._table.rowCount())}
        used.discard("")
        for r in range(self._table.rowCount()):
            c = self._table.cellWidget(r, 0)
            if c is None:
                continue
            cur = c.currentText()
            opts = [s for s in self._sources if s not in used or s == cur]
            c.blockSignals(True)
            c.clear()
            c.addItem("")
            c.addItems(opts)
            c.setCurrentText(cur)
            c.blockSignals(False)

    # ── stimulus definition ───────────────────────────────────────────────────

    def _button_row(self, btn: QPushButton) -> int:
        for r in range(self._table.rowCount()):
            if self._table.cellWidget(r, 1) is btn:
                return r
        return -1

    def _update_button(self, btn: QPushButton) -> None:
        btn.setText(_summary(btn._stim) if btn._stim else "Define stimulus…")

    def _define(self, btn: QPushButton) -> None:
        row = self._button_row(btn)
        src = self._row_source(row)
        is_current = src[:1].upper() == "I"
        params = _flat_to_params(self._domain, btn._stim or [])
        # parent=None (no transient parent) so the modal picker is a normal,
        # freely movable window — a parented modal is rendered as a frozen,
        # centered sheet under GNOME/Mutter (Anton, 2026-07-16).
        dlg = SourceStimuliDialog(
            params, is_current=is_current, domains=(self._domain,),
            show_display=False,
            title=f"Stimulus — {src}" if src else "Stimulus",
            parent=None)
        if not dlg.exec():
            return
        dlg.apply()
        if self._domain == "tran" and params.get("tran") == "_PWL_":
            QMessageBox.information(
                self, "PWL not supported here",
                "A PWL stimulus references an external data file and cannot be "
                "used as a per-run override. Define the PWL source on the "
                "schematic instead.")
            return
        btn._stim = _params_to_flat(self._domain, params)
        self._update_button(btn)
        self.changed.emit()

    # ── domain / analysis type ────────────────────────────────────────────────

    def set_domain(self, domain: str) -> None:
        """Set the analysis's stimulus domain. Stimuli are domain-specific, so
        changing it clears the table."""
        if domain == self._domain:
            return
        self._domain = domain
        self._table.setRowCount(0)
        self.setChecked(False)
        self._update_hint()
        self.changed.emit()

    def _update_hint(self) -> None:
        what = _DOMAIN_HINT.get(self._domain, "a stimulus")
        self._hint.setText(
            f"Override a source's stimulus for this run only. This "
            f"analysis uses {what}; the source keeps its nodes.")

    # ── state / emission ──────────────────────────────────────────────────────

    def active(self) -> bool:
        return self.isChecked()

    def stimuli_dict(self) -> dict:
        """``{source: [type, arg1, …]}`` for every complete row."""
        out: dict = {}
        for r in range(self._table.rowCount()):
            src = self._row_source(r)
            btn = self._table.cellWidget(r, 1)
            flat = getattr(btn, "_stim", None)
            if src and flat:
                out[src] = list(flat)
        return out

    def set_stimuli(self, stimuli, active: bool = True) -> None:
        """Prefill from a ``{source: [type, arg1, …]}`` dict (append-only edit)."""
        self._table.setRowCount(0)
        stimuli = dict(stimuli or {})
        for src, flat in stimuli.items():
            self.add_row(str(src), list(flat))
        if self.isCheckable():
            self.setChecked(active and bool(stimuli))
        self.changed.emit()

    def is_valid(self) -> bool:
        """When active: every present row must name a source and a stimulus."""
        if not self.active():
            return True
        rows = self._table.rowCount()
        if rows == 0:
            return False
        for r in range(rows):
            btn = self._table.cellWidget(r, 1)
            if not self._row_source(r) or not getattr(btn, "_stim", None):
                return False
        return True
