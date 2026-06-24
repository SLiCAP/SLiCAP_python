import html

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QLayout, QSizePolicy,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QWidget,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QByteArray, QSize
from PySide6.QtGui import QPalette

from .config import DEFAULT_ZOOM, GRID_SIZE

# Breathing space around the largest symbol inside the fixed preview area,
# measured in grid units at canvas scale (so it matches what 5 grid squares look
# like on the canvas).  Vertical is the value the layout guarantees above and
# below every symbol; horizontal is just a little side margin.
_PAD_GRID_V = 5
_PAD_GRID_H = 2


class PlaceSymbolDialog(QDialog):
    """
    Symbol picker for Place → Component….

    Scroll through the list to preview each symbol.
    Double-click a symbol to close the dialog and start placement.
    Escape or Cancel to dismiss without placing.
    """

    def __init__(self, library, parent=None, pre_select: str | None = None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Place Symbol")
        self._library = library
        self._selected: str | None = None

        outer = QVBoxLayout(self)
        body  = QHBoxLayout()
        outer.addLayout(body)

        # ── symbol list ───────────────────────────────────────────────────────
        list_col = QVBoxLayout()
        list_col.addWidget(QLabel("Select a symbol:"))
        self._list = QListWidget()
        self._list.setFixedWidth(160)
        for name in sorted(library.names):
            self._list.addItem(QListWidgetItem(name))
        list_col.addWidget(self._list)
        body.addLayout(list_col)

        # ── right side: graphic preview (top) and text info (bottom) ──────────
        preview_col = QVBoxLayout()
        # "Preview:" mirrors "Select a symbol:" on the left, so the preview area
        # lines up with the top of the list.
        preview_col.addWidget(QLabel("Preview:"))

        # ── part 1: SVG graphic, centered in a fixed white preview area ───────
        # The widget is sized per symbol to the symbol's own extent × DEFAULT_ZOOM
        # (see _on_selection_changed), so it appears at the exact same pixels-per-
        # grid-unit as on the canvas at default zoom — never stretched or clipped.
        self._svg = QSvgWidget()

        # The preview area has a FIXED width (the widest symbol plus side margin)
        # so the column does not jiggle horizontally as the selection scrolls.
        # Its HEIGHT is its content's: the SVG widget (resized per symbol in
        # _on_selection_changed) plus the vertical margins below — 5 grid units of
        # clearance above and below every symbol.  No border line: the symbol
        # simply sits on a white field.
        max_w = 0.0
        for n in library.names:
            sym = library.symbol(n)
            if sym is None:
                continue
            _x, _y, w, _h = sym.select_box
            max_w = max(max_w, w)
        pad_h = int(_PAD_GRID_H * GRID_SIZE * DEFAULT_ZOOM)
        pad_v = int(_PAD_GRID_V * GRID_SIZE * DEFAULT_ZOOM)
        area_w = round(max_w * DEFAULT_ZOOM + 2 * pad_h)

        preview_area = QWidget()
        preview_area.setFixedWidth(area_w)
        preview_area.setAutoFillBackground(True)
        pal = preview_area.palette()
        pal.setColor(QPalette.Window, Qt.white)
        preview_area.setPalette(pal)
        # The vertical margins ARE the clearance.  Because the area's height comes
        # from its content this way, its minimumSizeHint correctly reports
        # symbol+clearance and propagates up — so the dialog's own minimum size
        # (SetMinimumSize, below) grows to fit it and the window can never be
        # shrunk until the symbol overlaps the description text.
        area_layout = QVBoxLayout(preview_area)
        area_layout.setContentsMargins(0, pad_v, 0, pad_v)
        area_layout.addWidget(self._svg, 0, Qt.AlignCenter)
        preview_col.addWidget(preview_area, 0, Qt.AlignLeft)

        # ── part 2: description + clickable info link ─────────────────────────
        # Left-aligned and word-wrapped: the label fills the column width, so
        # widening the window puts more characters per line.
        self._meta = QLabel()
        self._meta.setTextFormat(Qt.RichText)
        self._meta.setOpenExternalLinks(True)      # open the link in the browser
        self._meta.setWordWrap(True)
        self._meta.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # A word-wrapped label's height depends on its width.  Enabling
        # height-for-width makes it report the height it actually needs at the
        # current width, so the layout (and the dialog minimum) reserve enough
        # room — without this the label under-reports and the symbol can overlap.
        sp = self._meta.sizePolicy()
        sp.setHeightForWidth(True)
        sp.setVerticalPolicy(QSizePolicy.MinimumExpanding)
        self._meta.setSizePolicy(sp)
        preview_col.addWidget(self._meta)

        preview_col.addStretch(1)
        # Stretch factor 1: the right side absorbs any extra window width, so the
        # description text re-wraps wider as the user enlarges the dialog.
        body.addLayout(preview_col, 1)

        # The dialog cannot be resized smaller than its content needs, so the
        # preview area and the description text can never be squeezed into overlap.
        # Growing it wider is still allowed — that just re-wraps the text.
        outer.setSizeConstraint(QLayout.SetMinimumSize)

        # ── OK / Cancel buttons ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self._ok_btn = QPushButton("OK")
        self._ok_btn.setDefault(True)
        self._ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._ok_btn)
        btn_row.addWidget(cancel_btn)
        outer.addLayout(btn_row)

        # ── connections ───────────────────────────────────────────────────────
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(self._on_double_click)

        if pre_select:
            items = self._list.findItems(pre_select, Qt.MatchExactly)
            if items:
                self._list.setCurrentItem(items[0])
            elif self._list.count():
                self._list.setCurrentRow(0)
        elif self._list.count():
            self._list.setCurrentRow(0)

    # ── slots ─────────────────────────────────────────────────────────────────

    def _on_selection_changed(self, current, _previous):
        if current is None:
            self._svg.load(QByteArray())
            self._meta.setText("")
            return
        sym = self._library.symbol(current.text())
        self._svg.load(QByteArray(sym.svg) if sym else QByteArray())
        # Size the widget to the symbol's own extent (the SVG viewBox is in scene
        # units) × DEFAULT_ZOOM, so the symbol shows at exactly the pixels-per-
        # grid-unit of the canvas at default zoom, whole and unstretched.  The
        # preview area then sizes itself to this plus its vertical margins, and the
        # dialog minimum grows with it.
        vb = self._svg.renderer().viewBoxF()
        self._svg.setFixedSize(QSize(round(vb.width() * DEFAULT_ZOOM),
                                     round(vb.height() * DEFAULT_ZOOM)))

        lines = []
        if sym is not None:
            if sym.description:
                lines.append(html.escape(sym.description))
            if sym.info:
                url = html.escape(sym.info, quote=True)
                lines.append(f'<a href="{url}">{html.escape(sym.info)}</a>')
        self._meta.setText("<br>".join(lines))

    def _on_ok(self):
        current = self._list.currentItem()
        if current is not None:
            self._selected = current.text()
            self.accept()

    def _on_double_click(self, item):
        self._selected = item.text()
        self.accept()

    # ── public API ────────────────────────────────────────────────────────────

    def selected_name(self) -> str | None:
        return self._selected
