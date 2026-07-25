"""
Dialog for defining THE circuit parameter table of a schematic (one table per
schematic; opened prefilled whether the table is shown or hidden).

Workflow (Anton, 2026-07-12):
- "Show on schematic" checked (new table): the action button reads "Place";
  with LaTeX rendering enabled it first shows the modal LaTeX preview
  (Close = back to editing, OK = accept), then the caller runs the
  click-to-place ghost.
- "Show on schematic" unchecked: the action button reads "OK" — the
  definitions are accepted without placement; the (hidden) table still
  netlists its .param lines.
- Edit mode (the table already exists): the button reads "OK" and changes
  apply in place; toggling the checkbox shows/hides the existing item.

The table's on-canvas SCALE is a schematic preference (Preferences →
"Scaling defaults"), deliberately not settable here — one value, one place.
"""
from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QCheckBox, QDialogButtonBox, QFileDialog, QApplication, QLayout,
    QHeaderView,
)
from PySide6.QtCore import Qt


def _find_slicap_preamble() -> str:
    try:
        import importlib
        sl = importlib.import_module("SLiCAP")
        install_path = getattr(getattr(sl, "ini", None), "install_path", None)
        if install_path:
            c = Path(install_path) / "tex" / "preambuleSLiCAP.tex"
            if c.exists():
                return str(c)
    except Exception:
        pass
    ini = Path.home() / "SLiCAP.ini"
    if ini.exists():
        try:
            cfg = configparser.ConfigParser()
            cfg.read(str(ini))
            install_path = cfg.get("install", "installpath", fallback="")
            if install_path:
                c = Path(install_path) / "tex" / "preambuleSLiCAP.tex"
                if c.exists():
                    return str(c)
        except Exception:
            pass
    return ""


class ParameterDialog(QDialog):

    def __init__(self, params=None,
                 preamble_path: str = "",
                 show: bool = True,
                 edit_mode: bool = False,
                 style=None,
                 parent=None):
        super().__init__(parent, Qt.Window)
        from .config import default_style
        from .latex_label import LATEX_INSTALLED
        self._style = style or default_style()
        # Preview rendering needs the tools AND the schematic's preference.
        self._latex_ok = LATEX_INSTALLED and self._style.LATEX_RENDERING_ENABLED
        self._edit_mode = edit_mode
        self.setWindowTitle("Circuit Parameters")
        self.setMinimumWidth(520)

        outer = QVBoxLayout(self)
        outer.setSizeConstraint(QLayout.SetMinimumSize)

        # ── preamble row ──────────────────────────────────────────────────────
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preamble:"))
        self._preamble_edit = QLineEdit(preamble_path or _find_slicap_preamble())
        self._preamble_edit.setReadOnly(True)
        self._preamble_edit.setPlaceholderText("(default: amsmath + amssymb)")
        self._preamble_edit.setMinimumWidth(260)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_preamble)
        clear_btn  = QPushButton("Clear")
        clear_btn.clicked.connect(self._preamble_edit.clear)
        prow.addWidget(self._preamble_edit, stretch=1)
        prow.addWidget(browse_btn)
        prow.addWidget(clear_btn)
        outer.addLayout(prow)

        # ── parameter table ───────────────────────────────────────────────────
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setMinimumHeight(130)
        outer.addWidget(self._table)

        for name, value in (params or []):
            self._add_row(name, value)

        # ── table action buttons ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self._add_row)
        del_btn = QPushButton("Remove row")
        del_btn.clicked.connect(self._remove_selected_row)
        # Names and values are SLiCAP netlist syntax — they become .param
        # lines; the LaTeX typesetting happens automatically (the same
        # chokepoint as the component value labels). Raw LaTeX here would
        # break the netlist.
        hint = QLabel("SLiCAP syntax, e.g. R_s and 10k or 1/(2*pi*R_s*C_c) — "
                      "netlisted as .param lines, typeset automatically")
        hint.setStyleSheet("color: grey; font-size: 9pt;")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(hint)
        btn_row.addStretch(1)
        outer.addLayout(btn_row)

        # ── show on schematic ─────────────────────────────────────────────────
        self._show_cb = QCheckBox("Show on schematic (parameters are always netlisted)")
        self._show_cb.setChecked(show)
        self._show_cb.toggled.connect(self._update_action_button)
        outer.addWidget(self._show_cb)

        # ── action buttons ────────────────────────────────────────────────────
        self._btn_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self._action_btn = QPushButton()
        self._btn_box.addButton(self._action_btn, QDialogButtonBox.AcceptRole)
        self._btn_box.accepted.connect(self._on_action)
        self._btn_box.rejected.connect(self.reject)
        outer.addWidget(self._btn_box)
        self._update_action_button()

    # ── table helpers ─────────────────────────────────────────────────────────

    def _add_row(self, name: str = "", value: str = "") -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name or ""))
        self._table.setItem(row, 1, QTableWidgetItem(value or ""))

    def _remove_selected_row(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()},
                      reverse=True)
        if rows:
            for r in rows:
                self._table.removeRow(r)
        else:
            rc = self._table.rowCount()
            if rc > 0:
                self._table.removeRow(rc - 1)

    def _current_params(self) -> list:
        result = []
        for row in range(self._table.rowCount()):
            n = self._table.item(row, 0)
            v = self._table.item(row, 1)
            name  = n.text().strip() if n else ""
            value = v.text().strip() if v else ""
            if name:
                result.append((name, value))
        return result

    # ── slots ─────────────────────────────────────────────────────────────────

    def _browse_preamble(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Preamble File",
            self._preamble_edit.text() or str(Path.home()),
            "LaTeX Files (*.tex);;All Files (*)",
        )
        if path:
            self._preamble_edit.setText(path)

    def _update_action_button(self) -> None:
        # "Place" only when a NEW table will be placed on the schematic;
        # editing an existing table applies in place ("OK"), and a hidden
        # table is accepted without placement ("OK").
        place = self._show_cb.isChecked() and not self._edit_mode
        self._action_btn.setText("Place" if place else "OK")

    def _on_action(self) -> None:
        if self._latex_ok:
            from .latex_label import render_latex_raw
            from .parameter_item import ParameterItem
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                svg, error = render_latex_raw(
                    ParameterItem.build_latex(self._current_params()),
                    self._preamble_edit.text())
            finally:
                QApplication.restoreOverrideCursor()
            if self._action_btn.text() == "Place":
                # Modal LaTeX preview: Close returns to editing, OK accepts.
                from .latex_preview_dialog import LatexPreviewDialog
                if not LatexPreviewDialog(svg, error, self).exec():
                    return                  # back to editing
            elif svg is None:
                # OK mode has no preview step, but a LaTeX error must not
                # pass silently (Anton, 2026-07-12). Accepting stays
                # possible: the netlist is unaffected, the canvas falls
                # back to plain text (with the error in its tooltip).
                from PySide6.QtWidgets import QMessageBox
                if QMessageBox.warning(
                        self, "LaTeX error",
                        "The parameter table does not compile:\n\n"
                        f"{error}\n\n"
                        "Accept anyway? (The canvas shows plain text.)",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No) != QMessageBox.Yes:
                    return                  # back to editing
        self.accept()

    # ── result accessors ──────────────────────────────────────────────────────

    def get_params(self) -> list:
        return self._current_params()

    def preamble_path(self) -> str:
        return self._preamble_edit.text()

    def show_on_schematic(self) -> bool:
        return self._show_cb.isChecked()
