"""Instruction -> Update schematic images...: pick the drawings whose
images the instruction file re-exports at its end.

The entry lived on the schematic tab's Instruction menu and emitted the
active schematic by circuit object or bare name. Moved to the MAIN
Instruction menu (Anton, 2026-11-08): the images of every drawing of the
project can be updated, not only the active one, and ``updateImages()``
takes the schematic FILE, so the two dialects of one name cannot be
confused. The dialog lists sch/, lib/ and posters/; one
``sl.updateImages("<path>")`` line per pick, lines the file already has
are skipped.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget,
                               QAbstractItemView, QDialogButtonBox)

from . import project


def exportable_drawings(root=None) -> list:
    """The drawings of the project that export images (project_drawings),
    as paths from the project root in POSIX form."""
    base = Path(root) if root is not None else project.project_root()
    return [project.schematic_ref(p, base) for p in project.project_drawings(base)]


def update_images_line(ref: str) -> str:
    return f'sl.updateImages("{ref}")'


class UpdateImagesDialog(QDialog):
    def __init__(self, root=None, instr_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update schematic images")
        self._instr_text = instr_text
        lay = QVBoxLayout(self)
        lab = QLabel("Drawings whose images the instruction file exports "
                     "again at its end, after the figures:")
        lab.setWordWrap(True)
        lay.addWidget(lab)
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for ref in exportable_drawings(root):
            self._list.addItem(ref)
        lay.addWidget(self._list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        self._ok = buttons.button(QDialogButtonBox.Ok)
        self._list.itemSelectionChanged.connect(self._validate)
        self._validate()

    def _validate(self):
        self._ok.setEnabled(bool(self._list.selectedItems()))

    def selected(self) -> list:
        return [it.text() for it in self._list.selectedItems()]

    def generated_snippet(self) -> str:
        """One line per pick; a line the file already has is not repeated."""
        lines = [update_images_line(r) for r in self.selected()]
        return "\n".join(l for l in lines if l not in self._instr_text)
