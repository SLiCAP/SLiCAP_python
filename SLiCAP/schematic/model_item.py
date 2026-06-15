from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from .config import COMMAND_COLOR, COMMAND_FONT, snap


class ModelItem(QGraphicsTextItem):
    """
    A .model definition on the canvas.
    Double-click opens the model definition dialog to edit.
    """

    def __init__(self, model_name: str, model_type: str, simulator: str,
                 params: list, pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.model_name: str  = model_name
        self.model_type: str  = model_type
        self.simulator:  str  = simulator    # "SLiCAP" or "SPICE"
        self.params:     list = list(params) # list of [name, value]
        self._update_text()
        self.setPos(pos)
        self.setFont(COMMAND_FONT)
        self.setDefaultTextColor(COMMAND_COLOR)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def _update_text(self) -> None:
        filled = [(n, v) for n, v in self.params if n.strip() and v.strip()]
        if filled:
            param_str = " ".join(f"{n}={v}" for n, v in filled)
            text = f".model {self.model_name} {self.model_type} ({param_str})"
        else:
            text = f".model {self.model_name} {self.model_type}"
        self.setPlainText(text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)

    def netlist_line(self) -> str:
        """Return the netlist line for this model definition."""
        filled = [(n, v) for n, v in self.params if n.strip() and v.strip()]
        if filled:
            param_str = " ".join(f"{n}={v}" for n, v in filled)
            return f".model {self.model_name} {self.model_type} ({param_str})"
        return f".model {self.model_name} {self.model_type}"
