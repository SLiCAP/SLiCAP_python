"""Create / Edit Figures dialog (TRACES.md phase 7).

Last of the three post-processing dialogs: traces are the DATA, an axis is a
PRESENTATION of trace data, a figure PLACES axes on a canvas. One statement
per object (TRACES.md 7.3)::

    FIG1 = sl.makeFigure([[axMag, axPZ],
                          [axPhase, axPZ]], "views", shareX="col", show=True)

The layout is a grid of cell drop-downs with a read-only mosaic line beside
it (Anton, 2026-08-03). A drag-and-drop editor may replace the grid later
without changing anything that is emitted - the nested list is the one
representation, as section 6.1 settled.

**A span is the SAME axis repeated in adjacent cells.** Nothing is added to
the object model and the source reads like the picture. The repeats must form
a solid rectangle: two non-adjacent cells holding one axis are ambiguous -
span, or two copies - so they are refused with a message, and "duplicate the
axis" is the explicit way to get two copies.

A cell can also make its own axis: "Create new axis…" opens the Axes dialog
and the new axis lands in that cell. Its statement is emitted BEFORE the
figure, so the dependency order in the file is the order of creation
(TRACES.md 7.2).

**Sharing is defined by TWO MARK MATRICES** mirroring the grid - one for x,
one for y (Anton, 2026-08-03: "I only know that I want to share an x-axis or
a y-axis"; group letters were considered and REJECTED as jargon). A tick
means "this cell shares"; vertically adjacent ticks in the x matrix become
ONE x axis (a Bode stack), horizontally adjacent ticks in the y matrix one y
axis. Adjacency answers "who with whom", so two separately ticked columns
are two independent stacks. Emitted as explicit groups -
``shareX=[[axMag, axPhase]]`` - which the renderer already takes; the
positional spellings 'col'/'row'/'all' remain script-level input and are
mapped onto the marks when such a statement is loaded.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDialogButtonBox, QSpinBox, QCheckBox, QWidget, QGroupBox,
    QPushButton,
)

from .instr_file import parse_calls
from .param_table import PARAM_NAME_WIDTH
from .traces_dialog import next_name, _lit, _q
from .axes_dialog import axis_entries

#: what a cell holds when it is empty - makeFigure's own spelling
EMPTY = ""
_EMPTY_LABEL = "(empty)"
_NEW_AXIS = "Create new axis…"

_MAX_SIDE = 6


def figure_entries(calls: list[dict]) -> list[dict]:
    """Existing named figures (``NAME = sl.makeFigure(…)``)."""
    return [c for c in calls if c["func"] == "makeFigure" and c["assigned"]]


def parse_grid(source: str) -> list[list[str]]:
    """The nested list of axis NAMES a makeFigure call was given.

    Its first argument is source text (``[[axMag, axPZ], [axPhase, axPZ]]``),
    not a literal, because the entries are variables - so it is read with the
    parser rather than literal_eval.
    """
    import ast
    try:
        node = ast.parse(str(source).strip(), mode="eval").body
    except SyntaxError:
        return []

    def cell(item):
        if isinstance(item, ast.Name):
            return item.id
        if isinstance(item, ast.Constant) and item.value == "":
            return EMPTY
        return EMPTY

    if isinstance(node, ast.Name):                 # a single axis
        return [[node.id]]
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    rows = []
    for row in node.elts:
        if isinstance(row, (ast.List, ast.Tuple)):
            rows.append([cell(item) for item in row.elts])
        else:
            rows.append([cell(row)])
    return rows


def mosaic(grid: list[list[str]]) -> str:
    """The grid as a matplotlib-style mosaic string: ``AB / CB``.

    Reading aid only - the nested list stays the single representation
    (TRACES.md 6.1). A letter per distinct axis, in reading order; '.' is an
    empty cell.
    """
    letters, out = {}, []
    for row in grid:
        text = ""
        for name in row:
            if not name:
                text += "."
                continue
            if name not in letters:
                letters[name] = chr(ord("A") + len(letters) % 26)
            text += letters[name]
        out.append(text)
    return " / ".join(out)


def span_error(grid: list[list[str]]) -> str:
    """'' when every repeated axis forms a solid rectangle, else the message.

    The rectangle rule of TRACES.md 6.1: an axis in two non-adjacent cells is
    ambiguous - a span, or two copies of the same axis - and is the one place
    where reuse by reference needs a boundary.
    """
    cells = {}
    for r, row in enumerate(grid):
        for c, name in enumerate(row):
            if name:
                cells.setdefault(name, []).append((r, c))
    for name, positions in cells.items():
        if len(positions) < 2:
            continue
        rows = [r for r, _c in positions]
        cols = [c for _r, c in positions]
        area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        if area != len(positions):
            return ("'{0}' sits in cells that do not form a rectangle. "
                    "Repeating an axis SPANS the cells between them; for two "
                    "copies, make a second axis.".format(name))
    return ""


class FigureDialog(QDialog):
    """Create or edit ONE named figure."""

    def __init__(self, existing_text: str = "", results_dir=None,
                 parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Create / Edit Figures")
        # a cell holds an axis NAME plus "Create new axis…": too narrow and
        # both are unreadable
        self.setMinimumWidth(520)

        self._existing_text = existing_text or ""
        self._results_dir = results_dir
        calls = parse_calls(self._existing_text)
        self._axes = [c["name"] for c in axis_entries(calls)]
        self._existing = figure_entries(calls)
        self._taken = {c["name"] for c in calls}
        #: axis statements made from a cell, emitted BEFORE the figure
        self._new_axis_statements: list[str] = []
        self._cells: list[list[QComboBox]] = []

        outer = QVBoxLayout(self)
        head = QGridLayout()
        outer.addLayout(head)

        head.addWidget(QLabel("Select figure:"), 0, 0)
        self._edit = QComboBox()
        self._edit.addItem("New figure")
        self._edit.addItems([c["name"] for c in self._existing])
        self._edit.currentIndexChanged.connect(self._on_load_existing)
        head.addWidget(self._edit, 0, 1)

        head.addWidget(QLabel("Figure variable name:"), 1, 0)
        self._name = QLineEdit(next_name("FIG", self._taken))
        self._name.setMaximumWidth(PARAM_NAME_WIDTH)
        self._name.textChanged.connect(self._update)
        head.addWidget(self._name, 1, 1)

        head.addWidget(QLabel("File name:"), 2, 0)
        self._file = QLineEdit()
        self._file.setPlaceholderText("written to img/, without extension")
        self._file.textChanged.connect(self._update)
        head.addWidget(self._file, 2, 1)

        # ── the grid ──────────────────────────────────────────────────────
        size = QHBoxLayout()
        size.addWidget(QLabel("Rows:"))
        self._rows = QSpinBox()
        self._rows.setRange(1, _MAX_SIDE)
        size.addWidget(self._rows)
        size.addWidget(QLabel("Columns:"))
        self._cols = QSpinBox()
        self._cols.setRange(1, _MAX_SIDE)
        size.addWidget(self._cols)
        size.addStretch(1)
        size.addWidget(QLabel("Mosaic:"))
        self._mosaic = QLabel()
        self._mosaic.setStyleSheet("font-family: monospace;")
        size.addWidget(self._mosaic)
        outer.addLayout(size)
        self._rows.valueChanged.connect(self._rebuild_grid)
        self._cols.valueChanged.connect(self._rebuild_grid)

        self._grid_box = QGroupBox("Axes on the figure")
        self._grid_layout = QGridLayout(self._grid_box)
        outer.addWidget(self._grid_box)

        # ── how the axes relate: two mark matrices (Anton, 2026-08-03) ────
        marks_row = QHBoxLayout()
        self._xmark_box = QGroupBox("Share x")
        self._xmark_box.setToolTip(
            "Vertically adjacent ticked cells get ONE x axis: same scale, "
            "zoom together, gap closed - a Bode stack.")
        self._xmark_grid = QGridLayout(self._xmark_box)
        self._ymark_box = QGroupBox("Share y")
        self._ymark_box.setToolTip(
            "Horizontally adjacent ticked cells get ONE y axis.")
        self._ymark_grid = QGridLayout(self._ymark_box)
        marks_row.addWidget(self._xmark_box)
        marks_row.addWidget(self._ymark_box)
        marks_row.addStretch(1)
        outer.addLayout(marks_row)
        self._xmarks = []
        self._ymarks = []

        options = QHBoxLayout()
        self._show = QCheckBox("show")
        self._save = QCheckBox("save in img/")
        self._save.setChecked(True)
        self._cursors = QCheckBox("A/B cursors")
        self._cursors.setChecked(True)
        for box in (self._show, self._save, self._cursors):
            box.toggled.connect(self._update)
            options.addWidget(box)
        options.addStretch(1)
        outer.addLayout(options)

        self._warning = QLabel()
        self._warning.setWordWrap(True)
        self._warning.setStyleSheet("color: #b34700; font-size: 9pt;")
        outer.addWidget(self._warning)

        self._hint = QLabel(
            "A span is the SAME axis in adjacent cells - the cells it "
            "occupies must form a rectangle. Sharing an axis means ONE "
            "scale for the group, tick labels and axis label on the outer "
            "axis only.")
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: grey; font-size: 9pt;")
        outer.addWidget(self._hint)

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

        self._rows.setValue(1)
        self._cols.setValue(1)
        self._rebuild_grid()

    # ── the grid of cells ─────────────────────────────────────────────────

    def _cell_combo(self, current: str = EMPTY) -> QComboBox:
        combo = QComboBox()
        combo.setMinimumHeight(combo.sizeHint().height())   # never squashed
        combo.addItem(_EMPTY_LABEL, EMPTY)
        for name in self._axes:
            combo.addItem(name, name)
        combo.addItem(_NEW_AXIS, _NEW_AXIS)
        if current and combo.findData(current) < 0:
            combo.insertItem(combo.count() - 1, current, current)
        combo.setCurrentIndex(max(0, combo.findData(current or EMPTY)))
        combo.activated.connect(lambda _i, c=combo: self._on_cell_activated(c))
        return combo

    def _cell_widget(self, current: str = EMPTY) -> QWidget:
        """One cell: which axis, and a button to EDIT that axis.

        An axis could be created from a cell but not changed from one, so
        composing a figure meant closing this dialog to fix an axis and
        opening it again (Anton, 2026-08-03). The edit re-defines the axis:
        its new statement is emitted BEFORE the figure, and the later
        definition wins - append-only editing, as everywhere else.
        """
        holder = QWidget()
        lay = QHBoxLayout(holder)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        combo = self._cell_combo(current)
        button = QPushButton("Edit…")
        button.setToolTip("Edit the axis in this cell")
        button.setMaximumWidth(60)
        button.clicked.connect(lambda _c=False, c=combo: self._edit_axis_in(c))
        combo._edit_button = button
        combo.currentIndexChanged.connect(
            lambda _i, c=combo: self._refresh_edit_button(c))
        lay.addWidget(combo, 1)
        lay.addWidget(button)
        holder.setMinimumHeight(combo.minimumHeight())
        self._refresh_edit_button(combo)
        return holder

    def _refresh_edit_button(self, combo):
        """There is nothing to edit in an empty cell."""
        button = getattr(combo, "_edit_button", None)
        if button is not None:
            name = combo.currentData()
            button.setEnabled(bool(name) and name != _NEW_AXIS)

    def _edit_axis_in(self, combo):
        """Open the Axes dialog on the axis in this cell.

        A renamed axis follows into the cell, so the figure keeps pointing at
        what the user just edited.
        """
        name = combo.currentData()
        if not name or name == _NEW_AXIS:
            return
        statement = self._run_axes_dialog(select=name)
        if not statement:
            return
        self._new_axis_statements.append(statement)
        new_name = statement.split("=", 1)[0].strip()
        if new_name not in self._axes:
            self._axes.append(new_name)
        self._refresh_cells(new_name=new_name, into=combo)
        self._update()

    def _run_axes_dialog(self, select: str = ""):
        """The Axes dialog over this file plus the axes made here; returns the
        statement it produced, or ''."""
        from .axes_dialog import AxesDialog
        text = "\n".join([self._existing_text] + self._new_axis_statements)
        dialog = AxesDialog(existing_text=text,
                            results_dir=self._results_dir, parent=self)
        if select:
            index = dialog._edit.findText(select)
            if index >= 0:
                dialog._edit.setCurrentIndex(index)
        return dialog.generated_snippet() if dialog.exec() else ""

    def _rebuild_grid(self, *_args):
        """Resize the cell table AND the mark matrices, keeping what they
        hold."""
        kept = self.grid()
        kept_x, kept_y = self.marks()
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for grid in (self._xmark_grid, self._ymark_grid):
            while grid.count():
                item = grid.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
        self._cells = []
        self._xmarks = []
        self._ymarks = []
        for r in range(self._rows.value()):
            row = []
            xrow = []
            yrow = []
            for c in range(self._cols.value()):
                current = (kept[r][c] if r < len(kept) and c < len(kept[r])
                           else EMPTY)
                holder = self._cell_widget(current)
                combo = holder.findChild(QComboBox)
                self._grid_layout.addWidget(holder, r, c)
                row.append(combo)
                for marks, grid, kept_m, mrow in (
                        (self._xmarks, self._xmark_grid, kept_x, xrow),
                        (self._ymarks, self._ymark_grid, kept_y, yrow)):
                    box = QCheckBox()
                    box.setChecked(bool(kept_m[r][c]
                                        if r < len(kept_m)
                                        and c < len(kept_m[r]) else False))
                    box.toggled.connect(self._update)
                    grid.addWidget(box, r, c)
                    mrow.append(box)
            self._cells.append(row)
            self._xmarks.append(xrow)
            self._ymarks.append(yrow)
        self._grow_for_the_grid()
        self._update()

    def marks(self):
        """(x marks, y marks) as booleans, in grid shape."""
        def read(rows):
            return [[box.isChecked() for box in row] for row in rows]
        return read(self._xmarks), read(self._ymarks)

    def _share_groups(self):
        """The share groups the marks define: (x groups, y groups).

        Vertically adjacent x-ticks in one column form a group; horizontally
        adjacent y-ticks in one row form one. Empty cells break a run, and a
        run must hold two DIFFERENT axes (a span repeated in its own run
        would share with itself).
        """
        grid = self.grid()

        def runs(marks, lanes, across, cell):
            groups = []
            for lane in range(lanes):
                run = []
                for step in range(across + 1):
                    name = cell(lane, step) if step < across else EMPTY
                    marked = (marks(lane, step) if step < across else False)
                    if name and marked:
                        if name not in run:
                            run.append(name)
                    else:
                        if len(run) >= 2:
                            groups.append(run)
                        run = []
            return groups

        x_marks, y_marks = self.marks()
        x_groups = runs(lambda c, r: x_marks[r][c], self._cols.value(),
                        self._rows.value(), lambda c, r: grid[r][c])
        y_groups = runs(lambda r, c: y_marks[r][c], self._rows.value(),
                        self._cols.value(), lambda r, c: grid[r][c])
        return x_groups, y_groups

    def _grow_for_the_grid(self):
        """Make room for the cells instead of squashing them.

        Adding a row makes the grid taller, but the dialog kept the height it
        opened with, so the group box absorbed the difference and the cell
        drop-downs were drawn 15 px high with their text cut off (Anton,
        2026-08-03). The grid keeps at least the height it asks for, and the
        window grows with it - it never shrinks by itself, so a window the
        user made larger stays that way.
        """
        self._grid_box.setMinimumHeight(self._grid_box.sizeHint().height())
        layout = self.layout()
        if layout is not None:
            layout.activate()
        wanted = self.sizeHint().height()
        if self.height() < wanted:
            self.resize(self.width(), wanted)

    def _on_cell_activated(self, combo: QComboBox):
        if combo.currentData() == _NEW_AXIS:
            self._create_axis_in(combo)
        self._update()

    def _create_axis_in(self, combo: QComboBox):
        """"Create new axis…": the Axes dialog, and the new axis lands here.

        Its statement is kept and emitted BEFORE the figure, so the file
        keeps the dependency order (TRACES.md 7.2)."""
        statement = self._run_axes_dialog()
        if not statement:
            combo.setCurrentIndex(0)              # back to (empty)
            return
        self._new_axis_statements.append(statement)
        name = statement.split("=", 1)[0].strip()
        self._axes.append(name)
        self._refresh_cells(new_name=name, into=combo)

    def _refresh_cells(self, new_name: str = "", into=None):
        """Offer the new axis in every cell, keeping the current choices."""
        for row in self._cells:
            for combo in row:
                current = combo.currentData()
                if combo is into:
                    current = new_name
                combo.blockSignals(True)
                combo.clear()
                combo.addItem(_EMPTY_LABEL, EMPTY)
                for name in self._axes:
                    combo.addItem(name, name)
                combo.addItem(_NEW_AXIS, _NEW_AXIS)
                combo.setCurrentIndex(max(0, combo.findData(current or EMPTY)))
                combo.blockSignals(False)
                self._refresh_edit_button(combo)

    def grid(self) -> list[list[str]]:
        """What the cells hold, as names ('' for an empty cell)."""
        out = []
        for row in self._cells:
            names = []
            for combo in row:
                value = combo.currentData()
                names.append(EMPTY if value in (None, _NEW_AXIS) else value)
            out.append(names)
        return out

    # ── editing an existing figure ────────────────────────────────────────

    def _on_load_existing(self, index: int):
        if index <= 0:
            return
        entry = self._existing[index - 1]
        args = entry.get("args") or []
        kwargs = entry.get("kwargs") or {}
        grid = parse_grid(args[0]) if args else []
        if grid:
            self._rows.blockSignals(True)
            self._cols.blockSignals(True)
            self._rows.setValue(min(len(grid), _MAX_SIDE))
            self._cols.setValue(min(max(len(r) for r in grid), _MAX_SIDE))
            self._rows.blockSignals(False)
            self._cols.blockSignals(False)
            self._rebuild_grid()
            for r, row in enumerate(grid):
                for c, name in enumerate(row):
                    if r < len(self._cells) and c < len(self._cells[r]):
                        combo = self._cells[r][c]
                        if name and combo.findData(name) < 0:
                            combo.insertItem(combo.count() - 1, name, name)
                        combo.setCurrentIndex(max(0, combo.findData(name)))
        self._name.setText(entry["name"])
        self._file.setText(str(_lit(args[1]) or "") if len(args) > 1 else "")
        self._apply_share(kwargs.get("shareX"), self._xmarks)
        self._apply_share(kwargs.get("shareY"), self._ymarks)
        show = _lit(kwargs.get("show"))
        save = _lit(kwargs.get("save"))
        cursors = _lit(kwargs.get("cursors"))
        self._show.setChecked(bool(show))
        self._save.setChecked(True if save is None else bool(save))
        self._cursors.setChecked(True if cursors is None else bool(cursors))
        # loading rebuilt the grid outside the Rows/Columns spinners, so the
        # window kept its opening height and squashed the cells (Anton,
        # 2026-08-03, second time) - grow here too
        self._grow_for_the_grid()
        self._update()

    def _apply_share(self, source, marks) -> None:
        """Tick the marks a shareX=/shareY= argument describes.

        'col'/'all' for x ('row'/'all' for y) tick every non-empty cell -
        adjacency then rebuilds the same stacks. An explicit group list
        ticks the cells holding those axes. The statement is re-emitted as
        explicit groups on Add, so a loaded figure migrates to the one
        spelling.
        """
        import ast
        grid = self.grid()

        def tick(test):
            for r, row in enumerate(marks):
                for c, box in enumerate(row):
                    if grid[r][c] and test(grid[r][c]):
                        box.setChecked(True)

        literal = _lit(source)
        if isinstance(literal, str):
            if literal in ("col", "row", "all"):
                tick(lambda _name: True)
            return
        try:
            node = ast.parse(str(source).strip(), mode="eval").body
        except (SyntaxError, ValueError):
            return
        names = {item.id for group in getattr(node, "elts", [])
                 for item in getattr(group, "elts", [])
                 if isinstance(item, ast.Name)}
        if names:
            tick(lambda name: name in names)

    # ── emission ──────────────────────────────────────────────────────────

    def generated_snippet(self) -> str:
        grid = self.grid()
        if not any(name for row in grid for name in row):
            return ""
        if span_error(grid):
            return ""
        name = self._name.text().strip() or "FIG1"
        file_name = self._file.text().strip() or name.lower()
        pad = " " * (len(name) + len(" = sl.makeFigure(["))
        rows = ["[" + ", ".join(cell or '""' for cell in row) + "]"
                for row in grid]
        body = ("[" + (",\n" + pad).join(rows) + "]")
        parts = ""
        x_groups, y_groups = self._share_groups()
        for key, groups in (("shareX", x_groups), ("shareY", y_groups)):
            if groups:
                parts += ", {0}=[{1}]".format(
                    key, ", ".join("[" + ", ".join(g) + "]" for g in groups))
        if self._show.isChecked():
            parts += ", show=True"
        if not self._save.isChecked():
            parts += ", save=False"
        if not self._cursors.isChecked():
            parts += ", cursors=False"
        statement = "{0} = sl.makeFigure({1}, {2}{3})".format(
            name, body, _q(file_name), parts)
        # the axes made from a cell come FIRST: one statement per object, in
        # dependency order
        return "\n".join(self._new_axis_statements + [statement])

    def _update(self, *_args):
        grid = self.grid()
        self._mosaic.setText(mosaic(grid))
        self._warning.setText(span_error(grid))
        snippet = self.generated_snippet()
        self._preview.setText(snippet or "")
        self._add_btn.setEnabled(bool(snippet)
                                 and bool(self._name.text().strip()))
