"""Create / Edit NGspice control-section instruction (item 5, Anton
2026-07-16 — raw / full-control mode).

Advanced escape hatch: the user references a text file whose content is
inserted VERBATIM as the ``.control … .endc`` block. SLiCAP does not parse a
result object, so the emitted call is a BARE statement (no assignment) and
nothing appears in the Design-data panel. The schematic-derived netlist is
still SLiCAP's; only the control block is the user's.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QFileDialog, QWidget,
)


def _q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def reference_url(page: str, anchor: str = "") -> str:
    """URL of a reference/manual page — the LOCAL installed copy under
    ``ini.doc_path`` (``…/SLiCAP/docs/html/``) when present, else the online
    manual. Local is safer/offline and matches the installed version
    (Anton, 2026-07-16)."""
    from pathlib import Path
    from PySide6.QtCore import QUrl
    import SLiCAP.SLiCAPconfigure as ini
    frag = f"#{anchor}" if anchor else ""
    local = Path(getattr(ini, "doc_path", "")) / page
    if local.is_file():
        return QUrl.fromLocalFile(str(local)).toString() + frag
    return "https://www.slicap.org/" + page + frag


class NGspiceControlDialog(QDialog):
    """Pick a control-section text file for an ``sl.ngspice_control`` call."""

    def __init__(self, cir_stem: str, control_dir: str = "", parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit NGspice control section")
        self._cir_stem = cir_stem
        self._control_dir = control_dir
        outer = QVBoxLayout(self)

        _page = "reference/SLiCAPngspice.html"
        _raw2dict = reference_url(_page, "SLiCAP.SLiCAPngspice.NGspiceRaw2dict")
        _rawfile  = reference_url(_page, "SLiCAP.SLiCAPngspice.RawFile")
        intro = QLabel(
            "Run NGspice with your OWN control section (full-control / raw "
            "mode). The file's text is inserted verbatim between "
            "<tt>.control</tt> and <tt>.endc</tt>. SLiCAP does not parse a "
            "result — have your control <tt>write</tt> a raw file and read it "
            "yourself with "
            f'<a href="{_raw2dict}">NGspiceRaw2dict</a> (one analysis) or '
            f'<a href="{_rawfile}">RawFile</a> (multiple).')
        intro.setWordWrap(True)
        intro.setOpenExternalLinks(True)          # open the reference in a browser
        intro.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(intro)

        row = QHBoxLayout()
        row.addWidget(QLabel("Control file:"))
        self._file = QLineEdit()
        self._file.setPlaceholderText("e.g. txt/mycontrol.txt")
        row.addWidget(self._file, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        pw = QWidget(); pw.setLayout(row)
        outer.addWidget(pw)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok
                                         | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        outer.addWidget(self._buttons)

        self._file.textChanged.connect(self._validate)
        self._validate()

    def _browse(self):
        start = self._control_dir or os.getcwd()
        fn, _ = QFileDialog.getOpenFileName(
            self, "Select control-section file", start,
            "Text files (*.txt *.ctrl *.sp);;All files (*)")
        if fn:
            # store project-relative when inside the project tree
            try:
                rel = os.path.relpath(fn, os.getcwd())
                self._file.setText(rel if not rel.startswith("..") else fn)
            except ValueError:
                self._file.setText(fn)

    def _validate(self):
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(
            bool(self._file.text().strip()))

    def generated_snippet(self) -> str:
        """A BARE ngspice_control call — no assignment, so it never becomes a
        Design-data variable (raw mode carries no result object)."""
        path = self._file.text().strip()
        return (f"sl.ngspice_control({_q(self._cir_stem)}, {_q(path)})\n")
