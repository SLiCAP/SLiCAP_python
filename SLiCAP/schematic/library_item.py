from pathlib import Path

from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import snap, style_of, default_style


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
                 corner: str = "", show: bool = True):
        super().__init__()
        self.file_path: str  = file_path
        self.directive: str  = directive   # "lib" or "inc"
        self.simulator: str  = simulator   # "SLiCAP" or "SPICE"
        self.corner:    str  = corner
        # "Show on schematic" (Anton, 2026-07-11, like the analysis block):
        # a hidden link stays in the scene and is ALWAYS netlisted; only
        # drawing and image export are suppressed.
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)
        self._update_text()
        self.setPos(pos)
        self._apply_style(default_style())
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def _apply_style(self, style) -> None:
        self.setFont(style.COMMAND_FONT)
        self.setDefaultTextColor(style.COMMAND_COLOR)

    def set_show(self, show: bool) -> None:
        self.show_on_schematic = bool(show)
        self.setVisible(self.show_on_schematic)

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
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self._apply_style(style_of(self))
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
