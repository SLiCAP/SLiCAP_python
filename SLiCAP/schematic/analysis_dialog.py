from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QDialogButtonBox, QFormLayout,
)


class AnalysisDialog(QDialog):
    """
    Structured dialog for .source / .detector / .lgref commands.

    Source:   refdes of one or two independent V- or I-sources.
    Detector: voltage (V_<node>) or current (I_<V-source>) — single type for
              both entries; second entry makes it a differential detector.
    LG ref:   refdes of one or two dependent sources.
    """

    def __init__(self, source=None, detector=None, lgref=None, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Define Source / Detector / Loop Gain Reference")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)

        # ── .source ──────────────────────────────────────────────────────────
        src_box = QGroupBox(".source  (independent V or I sources only)")
        src_form = QFormLayout(src_box)
        self._src1 = QLineEdit()
        self._src1.setPlaceholderText("e.g.  V1  or  I1")
        self._src2 = QLineEdit()
        self._src2.setPlaceholderText("optional — must be same type as Ref 1")
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
        self._det1_ref = QLineEdit()
        self._det1_ref.setPlaceholderText("node name  or  V-source refdes")
        self._det2_ref = QLineEdit()
        self._det2_ref.setPlaceholderText("optional — differential detector (same type)")
        ref_form.addRow("Ref 1:", self._det1_ref)
        ref_form.addRow("Ref 2:", self._det2_ref)
        det_v.addLayout(ref_form)
        layout.addWidget(det_box)

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
        self._lg1 = QLineEdit()
        self._lg1.setPlaceholderText("e.g.  G1")
        self._lg2 = QLineEdit()
        self._lg2.setPlaceholderText("optional — must be same type as Ref 1")
        lg_form.addRow("Ref 1:", self._lg1)
        lg_form.addRow("Ref 2:", self._lg2)
        lg_v.addLayout(lg_form)
        layout.addWidget(lg_box)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # ── pre-fill from existing values ─────────────────────────────────────
        src = list(source)   if source   else []
        det = [list(d) for d in detector] if detector else []
        lgr = list(lgref)    if lgref    else []

        if len(src) > 0:
            self._src1.setText(src[0])
        if len(src) > 1:
            self._src2.setText(src[1])

        # Infer shared detector type from first entry (both entries always same type)
        if len(det) > 0:
            idx = self._det_type.findText(det[0][0])
            if idx >= 0:
                self._det_type.setCurrentIndex(idx)
            self._det1_ref.setText(det[0][1])
        if len(det) > 1:
            self._det2_ref.setText(det[1][1])

        if len(lgr) > 0:
            self._lg1.setText(lgr[0])
        if len(lgr) > 1:
            self._lg2.setText(lgr[1])

    def get_source(self) -> list:
        result = []
        if self._src1.text().strip():
            result.append(self._src1.text().strip())
        if self._src2.text().strip():
            result.append(self._src2.text().strip())
        return result

    def get_detector(self) -> list:
        t = self._det_type.currentText()
        result = []
        if self._det1_ref.text().strip():
            result.append([t, self._det1_ref.text().strip()])
        if self._det2_ref.text().strip():
            result.append([t, self._det2_ref.text().strip()])
        return result

    def get_lgref(self) -> list:
        result = []
        if self._lg1.text().strip():
            result.append(self._lg1.text().strip())
        if self._lg2.text().strip():
            result.append(self._lg2.text().strip())
        return result
