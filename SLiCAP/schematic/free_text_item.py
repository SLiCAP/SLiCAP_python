from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont, QColor

from .config import style_of, default_style, display_color


class FreeTextItem(QGraphicsTextItem):
    """
    Text annotation on the schematic.

    Font family, size, face (bold, italic) and colour are the item's own
    when set, and the schematic's style (Preferences) otherwise: an empty
    family, a size of 0 and an empty colour mean "follow Preferences", so
    schematics written before 2026-10-06 look as they did.
    Placement and editing go through TextDialog; there is no inline editing.
    Double-click is intercepted by the canvas and opens the dialog.
    """
    SNAPS_TO_GRID = False   # an annotation: placed and dragged freely (canvas: group move, _FREE_PLACEMENT_MODES)

    def __init__(self, text: str = "Text", pos: QPointF = QPointF(0, 0),
                 font_family: str = "", font_size: int = 0,
                 bold: bool = False, italic: bool = False, color: str = "",
                 template: str = ""):
        super().__init__(text)
        # Non-empty: THE document-properties block of the drawing, whose
        # text is render_properties(template, properties), re-rendered on
        # load, after the properties dialog and at save (Anton, 2026-10-09).
        self.template    = template or ""
        self.font_family = font_family or ""
        self.font_size   = int(font_size or 0)
        self.bold        = bool(bold)
        self.italic      = bool(italic)
        self.color       = color or ""
        self.setPos(pos)
        self._apply_style(default_style())
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    # ── effective properties (own value or the style's) ─────────────────────

    def effective_family(self, style) -> str:
        return self.font_family or style.TEXT_FONT_FAMILY

    def effective_size(self, style) -> int:
        return self.font_size or style.TEXT_FONT_SIZE

    def effective_font(self, style) -> QFont:
        """The document font: family and size own or the style's, bold and
        italic own. Used on the canvas and by the SVG and PDF export."""
        font = QFont(self.effective_family(style), self.effective_size(style))
        font.setBold(self.bold)
        font.setItalic(self.italic)
        return font

    def effective_color(self, style) -> QColor:
        """The item's own colour, or the style's text colour. With the
        scene's document style (the export) that is the document colour."""
        return QColor(self.color) if self.color else QColor(style.TEXT_COLOR)

    @property
    def is_properties(self) -> bool:
        return bool(self.template)

    def own_properties(self) -> dict:
        """The item's own font and colour, as TextDialog takes them."""
        return dict(font_family=self.font_family, font_size=self.font_size,
                    bold=self.bold, italic=self.italic, color=self.color)

    def render(self, props) -> None:
        """A properties block takes its text from the document properties."""
        if not self.template or props is None:
            return
        from .schematic_data import render_properties
        text = render_properties(self.template, props)
        if text != self.toPlainText():
            self.prepareGeometryChange()
            self.setPlainText(text)
            self.update()

    def set_properties(self, font_family: str = "", font_size: int = 0,
                       bold: bool = False, italic: bool = False,
                       color: str = "") -> None:
        self.font_family = font_family or ""
        self.font_size   = int(font_size or 0)
        self.bold        = bool(bold)
        self.italic      = bool(italic)
        self.color       = color or ""
        self.prepareGeometryChange()
        self._apply_style(style_of(self) if self.scene() is not None else default_style())
        self.update()

    def _apply_style(self, style) -> None:
        self.setFont(self.effective_font(style))
        # an own colour is a document colour and follows the theme like a
        # shape's stroke; the style colour is already the on-screen colour
        self.setDefaultTextColor(display_color(self.color) if self.color
                                 else style.TEXT_COLOR)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged and self.scene() is not None:
            self._apply_style(style_of(self))
        # No grid snap: an annotation (see canvas._FREE_PLACEMENT_MODES).
        return super().itemChange(change, value)
