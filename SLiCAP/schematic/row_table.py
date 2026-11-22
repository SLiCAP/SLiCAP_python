"""A table of typed rows, used by every table where the user types rows:
the specifications, the circuit parameters, the parameters of a model
definition and of a subcircuit, and the border presets (workshop of
2026-11-17: "use TAB in last column to jump to first column of next row.
If not existing generate new row. Also for other tables such as circuit
parameters", and "allow sorting in create/edit specifications").
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QTableWidget


class RowTable(QTableWidget):
    """Tab on the last cell of a row goes to the first cell of the next
    row, as in any QTableWidget. Tab on the last cell of the LAST row adds
    a row through *add_row*, the owner's function that makes an empty row
    with its own defaults, and goes to its first cell; without *add_row*
    Tab wraps to the first row, Qt's default.

    With *sortable*, a click on a column header sorts the rows by that
    column, once; the next click on it sorts the other way round. The rows
    do not move while a value is being typed: a table that keeps itself
    sorted moves the row away from the cursor at every edit.

    The cell editor is opaque: at a fractional display scale (Windows,
    125 %) its text sat a pixel off the cell's own text, showing as
    ghosting (a user's report, 2026-09-25). That style sheet was set in
    two dialogs, it is set here for every row table."""

    def __init__(self, rows: int, columns: int, add_row=None, sortable: bool = False,
                 parent=None):
        super().__init__(rows, columns, parent)
        self._add_row = add_row
        self._sorted = None                   # (column, order) of the last sort
        self.setStyleSheet("QTableWidget QLineEdit { background: palette(base); }")
        if sortable:
            header = self.horizontalHeader()
            header.setSectionsClickable(True)
            header.setSortIndicatorShown(True)
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            header.sectionClicked.connect(self.sort_by)

    def sort_by(self, column: int) -> None:
        """Sort the rows by *column*: ascending, or descending when the
        last sort was ascending by the same column."""
        order = (Qt.SortOrder.DescendingOrder
                 if self._sorted == (column, Qt.SortOrder.AscendingOrder)
                 else Qt.SortOrder.AscendingOrder)
        self.sortItems(column, order)
        self.horizontalHeader().setSortIndicator(column, order)
        self._sorted = (column, order)

    def moveCursor(self, action, modifiers):
        if (action == QAbstractItemView.CursorAction.MoveNext
                and self._add_row is not None):
            current = self.currentIndex()
            if (current.isValid() and current.row() == self.rowCount() - 1
                    and current.column() == self.columnCount() - 1):
                self._add_row()
                return self.model().index(self.rowCount() - 1, 0)
        return super().moveCursor(action, modifiers)
