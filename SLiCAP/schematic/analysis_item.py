from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF

from .config import COMMAND_COLOR, COMMAND_FONT, snap


class AnalysisItem(QGraphicsTextItem):
    """
    SLiCAP analysis setup block: .source / .detector / .lgref commands.
    Stores structured data; double-click reopens the dialog for editing.
    """

    def __init__(self,
                 source:   list,   # 0-2 independent source refdes strings
                 detector: list,   # 0-2 [type, ref] pairs; type = "V" or "I"
                 lgref:    list,   # 0-2 dependent source refdes strings
                 pos: QPointF = QPointF(0, 0)):
        super().__init__()
        self.source   = list(source)
        self.detector = [list(d) for d in detector]
        self.lgref    = list(lgref)
        self.setPos(pos)
        self.setFont(COMMAND_FONT)
        self.setDefaultTextColor(COMMAND_COLOR)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.update_text()

    def update_text(self):
        lines = self.commands()
        self.setPlainText("\n".join(lines) if lines else ".source\n.detector\n.lgref")

    def commands(self) -> list:
        result = []
        src_refs = [r.strip() for r in self.source if r.strip()]
        if src_refs:
            result.append(".source " + " ".join(src_refs))
        det_parts = [f"{t}_{r.strip()}" for t, r in self.detector if r.strip()]
        if det_parts:
            result.append(".detector " + " ".join(det_parts))
        lg_refs = [r.strip() for r in self.lgref if r.strip()]
        if lg_refs:
            result.append(".lgref " + " ".join(lg_refs))
        return result

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return snap(value)
        return super().itemChange(change, value)
