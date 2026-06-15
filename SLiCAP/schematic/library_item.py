from pathlib import Path

from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import COMMAND_COLOR, COMMAND_FONT, snap


class LibraryItem(QGraphicsTextItem):
    """
    A .lib / .inc reference on the canvas.

    Displays the directive and filename on the schematic; the full path is
    written to the netlist.  Double-click opens the library link dialog.

    Attributes
    ----------
    directive  : "lib" or "inc"
    simulator  : "SLiCAP" or "SPICE"
    corner     : SPICE corner string (only used for SPICE .lib)
    """

    def __init__(self, file_path: str, pos: QPointF = QPointF(0, 0),
                 directive: str = "lib", simulator: str = "SLiCAP",
                 corner: str = ""):
        super().__init__()
        self.file_path: str  = file_path
        self.directive: str  = directive   # "lib" or "inc"
        self.simulator: str  = simulator   # "SLiCAP" or "SPICE"
        self.corner:    str  = corner
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
        if self.corner:
            self.setPlainText(f".{self.directive} {name} {self.corner}")
        else:
            self.setPlainText(f".{self.directive} {name}")
        self.setToolTip(self.file_path)

    def netlist_line(self) -> str:
        """Return the netlist line for this library link."""
        path = self.file_path
        if " " in path:
            path = f'"{path}"'
        parts = [f".{self.directive}", path]
        if self.corner:
            parts.append(self.corner)
        return " ".join(parts)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
