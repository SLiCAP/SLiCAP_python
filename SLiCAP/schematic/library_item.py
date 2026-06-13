from pathlib import Path

from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import COMMAND_COLOR, COMMAND_FONT, snap


class LibraryItem(QGraphicsTextItem):
    """
    A .lib reference on the canvas.

    Displays '.lib <filename>' on the schematic; the full path is written
    to the netlist.  Double-click opens a file dialog to change the path.
    """

    def __init__(self, file_path: str, pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.file_path: str = file_path
        self._update_text()
        self.setPos(pos)
        self.setFont(COMMAND_FONT)
        self.setDefaultTextColor(COMMAND_COLOR)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def _update_text(self) -> None:
        name = Path(self.file_path).name if self.file_path else ""
        self.setPlainText(f".lib {name}")
        self.setToolTip(self.file_path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
