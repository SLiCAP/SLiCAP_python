"""Structured dialog for the .source / .detector / .lgref commands.

The reference selectors are editable drop-downs pre-filled from the expanded
circuit object (see ``CanvasPanel._analysis_candidates``): independent
sources (``cir.indepVars``) for .source, dependent variables
(``cir.depVars()``) for .detector, and controlled sources
(``cir.controlled``) for .lgref — expanded elements such as ``E_O1`` only
exist after model expansion, so the candidates cannot come from the schematic
component list.  Free typing remains possible when the circuit cannot be
built yet (unsaved or incomplete schematic).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox, QDialogButtonBox, QFormLayout,
)


def _ref_combo(items, placeholder: str) -> QComboBox:
    cb = QComboBox()
    cb.setEditable(True)
    cb.addItems([str(i) for i in items])
    cb.setCurrentText("")
    if cb.lineEdit() is not None:
        cb.lineEdit().setPlaceholderText(placeholder)
    return cb


class AnalysisDialog(QDialog):
    """
    Structured dialog for .source / .detector / .lgref commands.

    Source:   refdes of one or two independent V- or I-sources.
    Detector: voltage (V_<node>) or current (I_<V-source>) — single type for
              both entries; second entry makes it a differential detector.
    LG ref:   refdes of one or two dependent sources.
    """

    def __init__(self, source=None, detector=None, lgref=None,
                 sources=(), det_v_refs=(), det_i_refs=(), lgrefs=(),
                 show=True, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Add / Edit Source / Detector / Loop Gain "
                            "Reference")
        self.setMinimumWidth(440)
        self._det_v_refs = [str(r) for r in det_v_refs]
        self._det_i_refs = [str(r) for r in det_i_refs]

        layout = QVBoxLayout(self)

        # ── .source ──────────────────────────────────────────────────────────
        src_box = QGroupBox(".source  (independent V or I sources only)")
        src_form = QFormLayout(src_box)
        self._src1 = _ref_combo(sources, "e.g.  V1  or  I1")
        self._src2 = _ref_combo(sources, "optional — must be same type as Ref 1")
        src_form.addRow("Ref 1:", self._src1)
        src_form.addRow("Ref 2:", self._src2)
        layout.addWidget(src_box)

        # ── .detector ────────────────────────────────────────────────────────
        det_box = QGroupBox(".detector")
        det_v = QVBoxLayout(det_box)

        type_row = QHBoxLayout()
        self._det_type = QComboBox()
        self._det_type.addItems(["V", "I"])
        type_row.addWidget(QLabel("Type:"))
        type_row.addWidget(self._det_type)
        type_row.addStretch()
        det_v.addLayout(type_row)

        hint = QLabel(
            "V — voltage at node  (result: V_<ref>)\n"
            "I — current through V-source  (result: I_<ref>)"
        )
        hint.setEnabled(False)
        det_v.addWidget(hint)

        ref_form = QFormLayout()
        self._det1_ref = _ref_combo(self._det_v_refs,
                                    "node name  or  V-source refdes")
        self._det2_ref = _ref_combo(self._det_v_refs,
                                    "optional — differential detector (same type)")
        ref_form.addRow("Ref 1:", self._det1_ref)
        ref_form.addRow("Ref 2:", self._det2_ref)
        det_v.addLayout(ref_form)
        layout.addWidget(det_box)
        self._det_type.currentIndexChanged.connect(self._on_det_type)

        # ── .lgref ────────────────────────────────────────────────────────────
        lg_box = QGroupBox(".lgref")
        lg_v = QVBoxLayout(lg_box)

        lg_hint = QLabel(
            "Controlled (dependent) sources only: E, G, H, F.\n"
            "Differential refs must be the same type (e.g. both G or both E)."
        )
        lg_hint.setEnabled(False)
        lg_v.addWidget(lg_hint)

        lg_form = QFormLayout()
        self._lg1 = _ref_combo(lgrefs, "e.g.  G1")
        self._lg2 = _ref_combo(lgrefs, "optional — must be same type as Ref 1")
        lg_form.addRow("Ref 1:", self._lg1)
        lg_form.addRow("Ref 2:", self._lg2)
        lg_v.addLayout(lg_form)
        layout.addWidget(lg_box)

        # "Show on schematic" (Anton, 2026-07-11): controls only whether the
        # command block is drawn on the canvas and in image exports — the
        # commands are ALWAYS written to the netlist.
        self._show_cb = QCheckBox(
            "Show on schematic  (the commands are always netlisted)")
        self._show_cb.setChecked(bool(show))
        layout.addWidget(self._show_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # ── pre-fill from existing values ─────────────────────────────────────
        src = list(source)   if source   else []
        det = [list(d) for d in detector] if detector else []
        lgr = list(lgref)    if lgref    else []

        if len(src) > 0:
            self._src1.setCurrentText(src[0])
        if len(src) > 1:
            self._src2.setCurrentText(src[1])

        # Infer shared detector type from first entry (both entries always
        # same type); set the type BEFORE the refs — switching it repopulates
        # the candidate lists.
        if len(det) > 0:
            idx = self._det_type.findText(det[0][0])
            if idx >= 0:
                self._det_type.setCurrentIndex(idx)
            self._det1_ref.setCurrentText(det[0][1])
        if len(det) > 1:
            self._det2_ref.setCurrentText(det[1][1])

        if len(lgr) > 0:
            self._lg1.setCurrentText(lgr[0])
        if len(lgr) > 1:
            self._lg2.setCurrentText(lgr[1])

    def _on_det_type(self, _idx: int) -> None:
        """Swap the detector candidate lists (V ↔ I), keeping typed text."""
        items = (self._det_v_refs if self._det_type.currentText() == "V"
                 else self._det_i_refs)
        for cb in (self._det1_ref, self._det2_ref):
            cur = cb.currentText()
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(items)
            cb.setCurrentText(cur)
            cb.blockSignals(False)

    def get_source(self) -> list:
        result = []
        if self._src1.currentText().strip():
            result.append(self._src1.currentText().strip())
        if self._src2.currentText().strip():
            result.append(self._src2.currentText().strip())
        return result

    def get_detector(self) -> list:
        t = self._det_type.currentText()
        result = []
        if self._det1_ref.currentText().strip():
            result.append([t, self._det1_ref.currentText().strip()])
        if self._det2_ref.currentText().strip():
            result.append([t, self._det2_ref.currentText().strip()])
        return result

    def get_lgref(self) -> list:
        result = []
        if self._lg1.currentText().strip():
            result.append(self._lg1.currentText().strip())
        if self._lg2.currentText().strip():
            result.append(self._lg2.currentText().strip())
        return result

    def show_on_schematic(self) -> bool:
        return self._show_cb.isChecked()
