from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QPalette

_PREVIEW_SIZE = 200   # square preview area in pixels


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

        # ── SVG preview ───────────────────────────────────────────────────────
        preview_col = QVBoxLayout()
        preview_col.addStretch(1)
        self._svg = QSvgWidget()
        self._svg.setFixedSize(_PREVIEW_SIZE, _PREVIEW_SIZE)
        pal = self._svg.palette()
        pal.setColor(QPalette.Window, Qt.white)
        self._svg.setAutoFillBackground(True)
        self._svg.setPalette(pal)
        preview_col.addWidget(self._svg, 0, Qt.AlignCenter)
        self._hint = QLabel()
        self._hint.setAlignment(Qt.AlignCenter)
        preview_col.addWidget(self._hint)
        preview_col.addStretch(1)
        body.addLayout(preview_col)

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
            self._hint.setText("")
            return
        name = current.text()
        svg = self._library.svg_bytes(name)
        self._svg.load(QByteArray(svg) if svg else QByteArray())
        # Keep the symbol's aspect ratio so non-square symbols are not stretched
        # to fill the square preview area.
        self._svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        self._hint.setText(name)

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
