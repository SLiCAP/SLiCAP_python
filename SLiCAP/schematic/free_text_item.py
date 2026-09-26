from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import style_of, default_style


class FreeTextItem(QGraphicsTextItem):
    """
    Text annotation on the schematic.

    Font, size, and colour come from the schematic's style (Preferences).
    Placement and editing go through TextDialog; there is no inline editing.
    Double-click is intercepted by the canvas and opens the dialog.
    """
    SNAPS_TO_GRID = False   # an annotation: placed and dragged freely (canvas: group move, _FREE_PLACEMENT_MODES)

    def __init__(self, text: str = "Text", pos: QPointF = QPointF(0, 0)):
        super().__init__(text)
        self.setPos(pos)
        self._apply_style(default_style())
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def _apply_style(self, style) -> None:
        self.setFont(style.TEXT_FONT)
        self.setDefaultTextColor(style.TEXT_COLOR)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self._apply_style(style_of(self))
        # No grid snap: an annotation (see canvas._FREE_PLACEMENT_MODES).
        return super().itemChange(change, value)
