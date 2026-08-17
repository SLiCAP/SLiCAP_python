"""Source stimuli dialog for NGspice independent V and I sources.

Edits the DC / AC / TRAN stimuli of an independent source.  The dialog is
**item-agnostic**: it reads and writes a plain ``params`` string-dict (and an
optional ``prop_display`` dict for canvas show/hide flags) using the flat-dict
convention shared by the rest of the schematic:

  dc           -- DC/TRAN value string (written as "dc <val>" in netlist)
  ac           -- "<ACMAG> <ACPHASE>" string (written as "ac <val>" in netlist)
  tran         -- full waveform string e.g. "PULSE({1} {0} {1n} ...)"
  _tran_type   -- active waveform name (internal; stripped by netlist builder)
  _<wf>_<par>  -- individual waveform field values (internal; stripped at netlist time)
  _pwl_file    -- path to PWL data file (internal)
  _pwl_r       -- PWL repeat time (internal)
  _pwl_td      -- PWL delay (internal)

Two reuse contexts share this one dialog (SLNG.md, 2026-07-16):

- **canvas** — double-click a V/I source: all three sections shown, the
  "Show" checkboxes toggle the on-canvas label (``prop_display``).  The caller
  passes ``item.params``/``item.prop_display`` and, after ``apply()``, redraws
  the component labels itself.
- **per-run override** (NGspice instruction dialog): only the section for the
  analysis's domain is shown (``domains=("ac",)`` etc.) and the canvas-only
  "Show" checkboxes are hidden (``show_display=False``).

``apply()`` mutates the ``params`` (and ``prop_display``) dict passed to the
constructor; the caller inspects it afterwards.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QCheckBox, QRadioButton, QStackedWidget,
    QPushButton, QFileDialog, QDialogButtonBox, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# Waveform definitions: (name, [positional param names in NGspice order])
_WAVEFORMS = [
    ("PULSE",    ["V1", "V2", "TD", "TR", "TF", "PW", "PER", "NP"]),
    ("SIN",      ["VO", "VA", "FREQ", "TD", "THETA", "PHASE"]),
    ("EXP",      ["V1", "V2", "TD1", "TAU1", "TD2", "TAU2"]),
    ("SFFM",     ["VO", "VA", "FM", "MDI", "FC", "TD", "PHASEM", "PHASEC"]),
    ("AM",       ["VO", "VMO", "VMA", "FM", "FC", "TD", "PHASEM", "PHASEC"]),
    ("TRNOISE",  ["NA", "NT", "NALPHA", "NAMP", "RTSAM", "RTSCAPT", "RTSEMT"]),
    ("TRRANDOM", ["TYPE", "TS", "TD", "PARAM1", "PARAM2"]),
    ("PWL",      []),
]

_WAVEFORM_INDEX = {name: i for i, (name, _) in enumerate(_WAVEFORMS)}
_WAVEFORM_FIELDS = {name: fields for name, fields in _WAVEFORMS}

# V→I renaming for current source display labels only (not stored keys)
_V_TO_I = {
    "V1": "I1", "V2": "I2",
    "VO": "IO", "VA": "IA",
    "VMO": "IMO", "VMA": "IMA",
}


def _display_label(name: str, is_current: bool) -> str:
    return _V_TO_I.get(name, name) if is_current else name


def _param_key(wf_name: str, field: str) -> str:
    return f"_{wf_name.lower()}_{field.lower()}"


class SourceStimuliDialog(QDialog):
    """Edit DC / AC / TRAN stimuli of an NGspice independent source.

    :param params: source parameter string-dict, mutated in place by ``apply()``.
    :param prop_display: optional canvas show/hide dict (``{key: (show_value,
        show_name)}``); ignored when *show_display* is False.
    :param is_current: True for an I-source (relabels waveform amplitude fields).
    :param domains: which sections to show, any of ``("dc", "ac", "tran")``.
    :param show_display: show the canvas-only "Show" checkboxes (default True).
    :param title: window title.
    """

    def __init__(self, params, prop_display=None, *, is_current: bool = False,
                 domains=("dc", "ac", "tran"), show_display: bool = True,
                 title: str = None, parent=None):
        super().__init__(parent, Qt.Window)
        self._params = params
        self._prop_display = prop_display if prop_display is not None else {}
        self._is_current = is_current
        self._domains = tuple(domains)
        self._show_display = show_display
        self.setWindowTitle(title or "Source stimuli")

        outer = QVBoxLayout(self)

        if "dc" in self._domains:
            outer.addWidget(self._build_dc_section())
        if "ac" in self._domains:
            outer.addWidget(self._build_ac_section())
        if "tran" in self._domains:
            outer.addWidget(self._build_tran_section())

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    # ── section builders ──────────────────────────────────────────────────────

    def _build_dc_section(self) -> QGroupBox:
        p = self._params
        grp = QGroupBox("DC")
        grp.setCheckable(True)
        grp.setChecked(bool(p.get("dc", "").strip()))

        layout = QHBoxLayout(grp)
        layout.addWidget(QLabel("DC/TRAN VALUE"))
        self._dc_edit = QLineEdit(p.get("dc", ""))
        layout.addWidget(self._dc_edit)
        if self._show_display:
            self._dc_show = QCheckBox("Show")
            sv, _ = self._prop_display.get("dc", (False, False))
            self._dc_show.setChecked(sv)
            layout.addWidget(self._dc_show)

        self._dc_grp = grp
        return grp

    def _build_ac_section(self) -> QGroupBox:
        p = self._params
        grp = QGroupBox("AC")
        grp.setCheckable(True)
        ac_val = p.get("ac", "")
        grp.setChecked(bool(ac_val.strip()))

        ac_parts = ac_val.split()
        ac_mag   = ac_parts[0] if len(ac_parts) > 0 else ""
        ac_phase = ac_parts[1] if len(ac_parts) > 1 else ""

        layout = QHBoxLayout(grp)
        layout.addWidget(QLabel("ACMAG"))
        self._ac_mag = QLineEdit(ac_mag)
        layout.addWidget(self._ac_mag)
        layout.addWidget(QLabel("ACPHASE"))
        self._ac_phase = QLineEdit(ac_phase)
        layout.addWidget(self._ac_phase)
        if self._show_display:
            self._ac_show = QCheckBox("Show")
            sv, _ = self._prop_display.get("ac", (False, False))
            self._ac_show.setChecked(sv)
            layout.addWidget(self._ac_show)

        self._ac_grp = grp
        return grp

    def _on_wf_selected(self, checked: bool, idx: int, name: str) -> None:
        if checked:
            self._stack.setCurrentIndex(idx)
            self._wf_title_lbl.setText(f"{name} parameters")

    def _build_tran_section(self) -> QGroupBox:
        p = self._params
        grp = QGroupBox("TRAN")
        grp.setCheckable(True)
        grp.setChecked(bool(p.get("tran", "").strip()))

        tran_layout = QVBoxLayout(grp)

        body = QHBoxLayout()
        tran_layout.addLayout(body)

        # Left column: radio buttons
        radio_col = QVBoxLayout()
        body.addLayout(radio_col)

        # Right column: bold title + stacked parameter panels
        right_col = QVBoxLayout()
        self._wf_title_lbl = QLabel()
        f = QFont()
        f.setBold(True)
        self._wf_title_lbl.setFont(f)
        right_col.addWidget(self._wf_title_lbl)
        self._stack = QStackedWidget()
        right_col.addWidget(self._stack)
        body.addLayout(right_col)

        self._radios: list[QRadioButton] = []
        self._wf_edits: dict[str, dict[str, QLineEdit]] = {}

        active_type = p.get("_tran_type", "PULSE")

        for wf_name, fields in _WAVEFORMS:
            radio = QRadioButton(wf_name)
            radio_col.addWidget(radio)
            self._radios.append(radio)

            if wf_name == "PWL":
                panel = self._build_pwl_panel()
            else:
                panel = self._build_wf_panel(wf_name, fields)

            self._stack.addWidget(panel)
            idx = len(self._radios) - 1
            radio.toggled.connect(
                lambda checked, i=idx, n=wf_name: self._on_wf_selected(checked, i, n)
            )

        # Set active waveform
        active_idx = _WAVEFORM_INDEX.get(active_type, 0)
        self._radios[active_idx].setChecked(True)
        self._stack.setCurrentIndex(active_idx)
        self._wf_title_lbl.setText(f"{active_type} parameters")

        if self._show_display:
            # Show checkbox at the bottom of the TRAN group
            show_row = QHBoxLayout()
            show_row.addStretch()
            self._tran_show = QCheckBox("Show")
            sv, _ = self._prop_display.get("tran", (False, False))
            self._tran_show.setChecked(sv)
            show_row.addWidget(self._tran_show)
            tran_layout.addLayout(show_row)

        self._tran_grp = grp
        return grp

    def _build_wf_panel(self, wf_name: str, fields: list) -> QWidget:
        p = self._params
        panel = QWidget()
        grid = QGridLayout(panel)
        grid.setColumnStretch(1, 1)
        edits: dict[str, QLineEdit] = {}
        for row, field in enumerate(fields):
            label = _display_label(field, self._is_current)
            grid.addWidget(QLabel(label), row, 0)
            val = p.get(_param_key(wf_name, field), "")
            edit = QLineEdit(val)
            grid.addWidget(edit, row, 1)
            edits[field] = edit
        self._wf_edits[wf_name] = edits
        return panel

    def _build_pwl_panel(self) -> QWidget:
        p = self._params
        panel = QWidget()
        layout = QVBoxLayout(panel)

        path_row = QHBoxLayout()
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_pwl)
        path_row.addWidget(browse_btn)
        stored_path = p.get("_pwl_file", "")
        self._pwl_path_lbl = QLabel(stored_path if stored_path else "(no file selected)")
        self._pwl_path_lbl.setWordWrap(True)
        path_row.addWidget(self._pwl_path_lbl, stretch=1)
        layout.addLayout(path_row)

        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("r="))
        self._pwl_r = QLineEdit(p.get("_pwl_r", ""))
        self._pwl_r.setPlaceholderText("repeat time (optional)")
        opt_row.addWidget(self._pwl_r)
        opt_row.addWidget(QLabel("td="))
        self._pwl_td = QLineEdit(p.get("_pwl_td", ""))
        self._pwl_td.setPlaceholderText("delay (optional)")
        opt_row.addWidget(self._pwl_td)
        layout.addLayout(opt_row)
        layout.addStretch()

        return panel

    # ── slots ─────────────────────────────────────────────────────────────────

    def _browse_pwl(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PWL data file", "",
            "PWL files (*.pwl *.txt *.dat);;All Files (*)",
        )
        if path:
            self._pwl_path_lbl.setText(path)

    # ── apply ─────────────────────────────────────────────────────────────────

    def apply(self) -> None:
        """Write the chosen stimuli back into the ``params`` (and, when
        *show_display*, ``prop_display``) dict passed to the constructor.

        Only the shown sections (``domains``) are touched; the caller redraws
        any canvas labels itself."""
        p  = self._params
        pd = self._prop_display

        # ── DC ───────────────────────────────────────────────────────────────
        if "dc" in self._domains:
            dc_val = self._dc_edit.text().strip()
            if self._dc_grp.isChecked() and dc_val:
                p["dc"] = dc_val
                if self._show_display:
                    pd["dc"] = (self._dc_show.isChecked(), False)
            else:
                p.pop("dc", None)
                pd.pop("dc", None)

        # ── AC ───────────────────────────────────────────────────────────────
        if "ac" in self._domains:
            mag   = self._ac_mag.text().strip()
            phase = self._ac_phase.text().strip()
            if self._ac_grp.isChecked() and (mag or phase):
                p["ac"] = f"{mag} {phase}".strip() if phase else mag
                if self._show_display:
                    pd["ac"] = (self._ac_show.isChecked(), False)
            else:
                p.pop("ac", None)
                pd.pop("ac", None)

        # ── TRAN ─────────────────────────────────────────────────────────────
        if "tran" in self._domains:
            if self._tran_grp.isChecked():
                idx     = self._stack.currentIndex()
                wf_name = _WAVEFORMS[idx][0]
                fields  = _WAVEFORMS[idx][1]
                p["_tran_type"] = wf_name

                if wf_name == "PWL":
                    path = self._pwl_path_lbl.text()
                    p["_pwl_file"] = "" if path == "(no file selected)" else path
                    p["_pwl_r"]    = self._pwl_r.text().strip()
                    p["_pwl_td"]   = self._pwl_td.text().strip()
                    p["tran"] = "_PWL_"
                else:
                    edits    = self._wf_edits[wf_name]
                    all_vals: list = []
                    for field in fields:
                        val = edits[field].text().strip()
                        p[_param_key(wf_name, field)] = val
                        all_vals.append(val)
                    while all_vals and not all_vals[-1]:
                        all_vals.pop()
                    inner   = " ".join(f"{{{v}}}" for v in all_vals)
                    p["tran"] = f"{wf_name}({inner})"

                if self._show_display:
                    pd["tran"] = (self._tran_show.isChecked(), False)

            else:
                p.pop("tran",       None)
                p.pop("_tran_type", None)
                pd.pop("tran",      None)
