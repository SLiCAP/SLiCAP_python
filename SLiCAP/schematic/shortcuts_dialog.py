"""Help > Keyboard shortcuts (workshop of 2026-11-17: "create shortcut
overview in the menu bar of the circuit editor as help").

The overview is read from the program, never written by hand, so it
cannot go out of date: the keys of the canvas from
``SchematicView.CANVAS_KEYS``, the table the key handler dispatches from,
and the menu shortcuts from the menu actions themselves, those of the
active schematic and those of the main window.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox,
                               QHeaderView, QMenu, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)



def canvas_rows() -> list:
    """``(keys, what, where)`` of the keys the canvas handles itself."""
    from .canvas import SchematicView
    return [(shown, what, "Canvas")
            for _key, _mods, shown, what, _method in SchematicView.CANVAS_KEYS if shown]


def menu_actions(menu_bar) -> list:
    """Every action of the menus of *menu_bar*, submenus included, in menu
    order."""
    out = []

    def walk(actions):
        for act in actions:
            sub = act.menu()
            if sub is not None:
                walk(sub.actions())
            elif not act.isSeparator():
                out.append(act)
    walk(menu_bar.actions() if menu_bar is not None else [])
    return out


def shortcut_rows(actions) -> list:
    """``(keys, what, where)`` of every action in *actions* with a shortcut:
    its keys as the platform shows them, its text without the mnemonic and
    the ellipsis, and the menu that holds it. One row per keys and text."""
    rows, seen = [], set()
    for act in actions:
        sequence = act.shortcut()
        if sequence.isEmpty():
            continue
        keys = sequence.toString(QKeySequence.SequenceFormat.NativeText)
        what = act.text().replace("&&", "\0").replace("&", "").replace("\0", "&")
        what = what.replace("…", "").replace("...", "").strip()
        menus = [obj.title().replace("&", "") for obj in act.associatedObjects()
                 if isinstance(obj, QMenu) and obj.title()]
        if (keys, what) in seen:
            continue
        seen.add((keys, what))
        rows.append((keys, what, ", ".join(menus)))
    return rows


class ShortcutsDialog(QDialog):
    """The overview: one row per shortcut, keys, action and where it acts."""

    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard shortcuts")
        lay = QVBoxLayout(self)
        table = QTableWidget(len(rows), 3, self)
        table.setHorizontalHeaderLabels(["Keys", "Action", "Where"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        for r, row in enumerate(rows):
            for c, text in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(text))
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(table)
        self._table = table
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        self.resize(table.horizontalHeader().length() + 60,
                    min(640, table.verticalHeader().length() + 120))
