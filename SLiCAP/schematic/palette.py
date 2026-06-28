from PySide6.QtWidgets import QListWidget, QListView
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QByteArray, QSize, Signal

from .symbol_library import SymbolLibrary

_ICON_PX = 64       # rendered icon size in pixels
_GRID_PX = 80       # grid cell size (icon + label)


class SymbolPalette(QListWidget):
    """
    Displays all symbols from a SymbolLibrary as clickable icon+label tiles.
    Emits symbol_selected(name) when the user clicks a tile.
    """

    symbol_selected = Signal(str)

    def __init__(self, library: SymbolLibrary, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(_ICON_PX, _ICON_PX))
        self.setGridSize(QSize(_GRID_PX, _GRID_PX + 20))
        self.setResizeMode(QListWidget.Adjust)
        self.setWordWrap(True)
        self.setSpacing(4)
        self.setFixedWidth(200)

        self._populate(library)
        self.itemClicked.connect(
            lambda item: self.symbol_selected.emit(item.data(Qt.UserRole))
        )

    def _populate(self, library: SymbolLibrary):
        for name in library.names:
            svg = library.svg_bytes(name)
            if svg is None:
                continue
            item_icon = _render_icon(svg, _ICON_PX)
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(item_icon, name)
            item.setData(Qt.UserRole, name)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            self.addItem(item)


def _render_icon(svg_bytes: bytes, size: int) -> QIcon:
    from PySide6.QtCore import QRectF
    from .component_item import paint_symbol
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    # Render through the canvas' symbol path so embedded text is centred and
    # matches a placed component (KeepAspectRatio is handled inside paint_symbol).
    paint_symbol(painter, svg_bytes, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)
