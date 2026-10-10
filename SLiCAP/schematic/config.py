from __future__ import annotations

import configparser
import copy
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPen

from .fonts import resolve_family

# The font families every font combo offers (drawing preferences, text
# dialog): the generic families only. An SVG viewer and a PDF printer
# resolve a generic family on every machine, a named font only where it is
# installed, so a named font drifts between machines (Anton, 2026-10-06).
# The combos stay editable: a named font can be typed at the user's risk.
# Offering named fonts (Arial, Helvetica, Times New Roman, Courier New,
# Georgia) was the previous list and is REJECTED for that reason.
GENERIC_FONT_FAMILIES = ["sans-serif", "serif", "monospace"]

# The ground side of a detector pair in the dialogs: shown as "(ground)",
# written as None in an instruction and as the word None in a netlist
# (SLiCAPyacc.GROUND_TOKEN). The ground is not a dependent variable, so the
# entry is this label, never "V_0" (which the core refuses).
GROUND = "(ground)"

# The line styles of drawn shapes and of the border, by name: ONE table for
# the canvas pens; the SVG export keeps the matching dash arrays
# (export._DASH_ARRAY). The border's style was a hard-coded dash until
# 2026-10-06 (Anton: "cannot be changed").
LINE_STYLES = {
    "solid":    Qt.SolidLine,
    "dashed":   Qt.DashLine,
    "dotted":   Qt.DotLine,
    "dash-dot": Qt.DashDotLine,
}
LINE_STYLE_NAMES = list(LINE_STYLES)

# ── grid (functional, not cosmetic) ──────────────────────────────────────────

GRID_SIZE  = 5
GRID_MAJOR = 8   # minor cells between major grid lines (major spacing = 8×GRID_SIZE)

# Device pixels per scene unit at default zoom (the canvas opens and zoom-resets
# at this scale).  Shared so off-canvas previews can render symbols at the exact
# same size the user sees on the canvas.
DEFAULT_ZOOM = 2


def snap(pos: QPointF) -> QPointF:
    x = round(pos.x() / GRID_SIZE) * GRID_SIZE
    y = round(pos.y() / GRID_SIZE) * GRID_SIZE
    return QPointF(x, y)


# ── canvas stacking order (Z-values) ──────────────────────────────────────────
# One distinct value per item type so overlapping items have a deterministic
# selection order.  Qt's itemAt() returns the highest-Z item; for equal Z it
# falls back to insertion order, which is unpredictable — these constants remove
# those ties.  Higher = on top / selected first.
#
# Note: child labels (a component's property labels, a wire's net label) are
# stacked relative to their PARENT, so their Z only orders them against siblings,
# not against unrelated top-level items.  The net label therefore also gets an
# explicit pick in the canvas press handler.
Z_BORDER    = -10   # frame, always behind everything
# The colour in which a selected item shows itself (wires, junctions, shapes,
# component select box): the item is drawn in this colour, no box around it.
SELECTION_COLOR = QColor(0, 120, 215)

# The selection frame of an item is painted with this pen on the item's
# CONTENT rectangle, and the item's boundingRect() is that rectangle grown by
# SELECTION_MARGIN. Qt repaints only the declared rectangle when an item
# moves, so a frame that straddles its edge leaves stripes behind while it
# is dragged, visible when zoomed in or at a high DPI (Anton, 2026-09-30,
# and the ghosting of the Windows report).
SELECTION_MARGIN = 1.0          # scene units, more than half the frame pen


def selection_pen() -> QPen:
    """The selection frame: one screen pixel at every zoom, dashed."""
    pen = QPen(SELECTION_COLOR, 1.0, Qt.DashLine)
    pen.setCosmetic(True)
    return pen

Z_WIRE      = 0
Z_WIRE_DRAG = 5     # a wire lifted above its rubber-band partners during a drag
Z_COMPONENT = 10
Z_JUNCTION  = 20    # small dots stay grabbable on top of components
Z_NET_LABEL = 30    # most clickable (child of a wire; see note above)


# ── per-schematic style ───────────────────────────────────────────────────────
#
# Every open schematic owns its own Style: the global style.ini template
# overlaid with the schematic's sidecar ``<name>.ini``.  Items resolve their
# style through their scene (``style_of``), so several schematics with
# different styles can be open — and visible — at the same time without one
# file's preferences leaking into another file's drawing.  There is no
# process-global style state.

STYLE_FILE = Path(__file__).parent.parent / "files" / "symbols" / "slicap" / "style.ini"


class Style:
    """The drawing style of one schematic (colours, fonts, scales, flags).

    Constructed from the global ``style.ini`` template plus an optional
    per-schematic sidecar overlay.  The Preferences dialog edits a
    ``snapshot()`` and commits it with ``apply_parser()``; ``write()``
    persists the effective style to the schematic's sidecar.
    """

    def __init__(self, sidecar: "Path | str | None" = None):
        self._cfg = style_parser()
        self._cfg.read(STYLE_FILE)
        if sidecar is not None and Path(sidecar).is_file():
            self._cfg.read(str(sidecar))
        self._recompute()

    # -- typed readers ---------------------------------------------------------

    def _c(self, section: str, key: str, default: str) -> QColor:
        try:
            return QColor(self._cfg[section][key])
        except KeyError:
            return QColor(default)

    def _f(self, section: str, key: str, default: float) -> float:
        try:
            return float(self._cfg[section][key])
        except (KeyError, ValueError):
            return default

    def _i(self, section: str, key: str, default: int) -> int:
        try:
            return int(self._cfg[section][key])
        except (KeyError, ValueError):
            return default

    def _s(self, section: str, key: str, default: str) -> str:
        try:
            return self._cfg[section][key].strip()
        except KeyError:
            return default

    def _b(self, section: str, key: str, default: bool) -> bool:
        try:
            return self._cfg[section][key].strip().lower() in ("true", "1", "yes")
        except KeyError:
            return default

    # -- attribute computation -------------------------------------------------

    def _recompute(self) -> None:
        self._dark_variant = None       # display variant is rebuilt on demand
        # LaTeX rendering preference of THIS schematic.  Whether LaTeX is
        # installed on this machine is a separate, global fact
        # (latex_label.LATEX_INSTALLED) — the only global in the LaTeX story.
        self.LATEX_RENDERING_ENABLED = self._b("rendering", "latex_rendering", True)

        # Symbol colours
        self.SYMBOL_STROKE_COLOR = self._c("symbol", "stroke_color", "#000000")
        self.SYMBOL_TEXT_COLOR   = self._c("symbol", "text_color",   "#000000")

        # Wire
        self.WIRE_COLOR = self._c("wire", "color", "#000000")
        self.WIRE_WIDTH = self._f("wire", "width", 1.0)

        # Net labels
        self.NET_LABEL_COLOR     = self._c("net_label", "color",     "#ff0000")
        self.NET_LABEL_FONT_SIZE = self._i("net_label", "font_size", 7)
        self.NET_LABEL_FONT      = QFont(resolve_family("sans-serif"), self.NET_LABEL_FONT_SIZE)

        # Component refdes labels.  IEEE-style element identifiers (customer
        # request, 2026-07-11): render the refdes through the SLiCAP LaTeX
        # chokepoint like parameter names, optionally upright bold.
        self.COMP_REFDES_FONT_FAMILY = self._s("component_label", "font_family", "sans-serif")
        self.COMP_LABEL_COLOR        = self._c("component_label", "color",       "#000000")
        self.COMP_LABEL_FONT_SIZE    = self._i("component_label", "font_size",   7)
        self.COMP_LABEL_LATEX_SCALE  = self._i("component_label", "latex_scale", 30)
        self.COMP_LABEL_LATEX        = self._b("component_label", "latex",       True)
        self.COMP_LABEL_LATEX_BOLD   = self._b("component_label", "latex_bold",  True)
        self.COMP_LABEL_SVG_HEIGHT   = self.COMP_LABEL_LATEX_SCALE / 100.0 * 20.0
        self.COMP_LABEL_FONT         = QFont(resolve_family(self.COMP_REFDES_FONT_FAMILY),
                                             self.COMP_LABEL_FONT_SIZE)

        # Component parameter labels (value, noisetemp, …)
        self.COMP_PARAM_FONT_FAMILY = self._s("component_param", "font_family", "monospace")
        self.COMP_PARAM_FONT_SIZE   = self._i("component_param", "font_size",   6)
        self.COMP_PARAM_COLOR       = self._c("component_param", "color",       "#000000")
        self.COMP_PARAM_FONT        = QFont(resolve_family(self.COMP_PARAM_FONT_FAMILY),
                                            self.COMP_PARAM_FONT_SIZE)
        self.COMP_PARAM_LATEX_SCALE = self._i("component_param", "latex_scale", 30)
        self.COMP_PARAM_SVG_HEIGHT  = self.COMP_PARAM_LATEX_SCALE / 100.0 * 20.0

        # Grid
        self.GRID_MINOR_COLOR = self._c("grid", "minor_color", "#DCDCDC")
        self.GRID_MAJOR_COLOR = self._c("grid", "major_color", "#B4B4B4")
        self.GRID_SUBGRID       = self._b("grid", "subgrid", False)   # dots at FINE_STEP
        self.GRID_SUBGRID_COLOR = self._c("grid", "subgrid_color", "#B4B4B4")

        # Wire vertex handles + unconnected-pin connection markers
        self.HANDLE_COLOR     = self._c("handles", "color", "#3d3846")
        self.HANDLE_SIZE      = self._f("handles", "size",  4.0)
        self.CONNECTION_COLOR = self._c("handles", "connection_color", "#888888")

        # Junctions
        self.JUNCTION_COLOR  = self._c("junctions", "color",  "#000000")
        self.JUNCTION_RADIUS = self._f("junctions", "radius", 2.0)

        # Free text annotations
        self.FREE_TEXT_COLOR     = self._c("free_text", "color",     "#333333")
        self.FREE_TEXT_FONT_SIZE = self._i("free_text", "font_size",  8)
        self.FREE_TEXT_FONT      = QFont(resolve_family("sans-serif"), self.FREE_TEXT_FONT_SIZE)

        # SLiCAP command blocks
        self.COMMAND_COLOR     = self._c("command", "color",     "#004080")
        self.COMMAND_FONT_SIZE = self._i("command", "font_size",  7)
        self.COMMAND_FONT      = QFont(resolve_family("monospace"), self.COMMAND_FONT_SIZE)

        # Text annotations
        self.TEXT_FONT_FAMILY = self._s("text", "font_family", "sans-serif")
        self.TEXT_FONT_SIZE   = self._i("text", "font_size",   7)
        self.TEXT_COLOR       = self._c("text", "color",       "#333333")
        self.TEXT_FONT        = QFont(resolve_family(self.TEXT_FONT_FAMILY), self.TEXT_FONT_SIZE)

        # Hyperlinks
        self.HYPERLINK_FONT_FAMILY = self._s("hyperlink", "font_family", "sans-serif")
        self.HYPERLINK_FONT_SIZE   = self._i("hyperlink", "font_size",   7)
        self.HYPERLINK_COLOR       = self._c("hyperlink", "color",       "#0000cc")
        self.HYPERLINK_UNDERLINE   = self._b("hyperlink", "underline",   True)
        self.HYPERLINK_FONT        = QFont(resolve_family(self.HYPERLINK_FONT_FAMILY),
                                           self.HYPERLINK_FONT_SIZE)
        self.HYPERLINK_FONT.setUnderline(self.HYPERLINK_UNDERLINE)

        # DC operating-point (bias) back-annotations on NGspice schematics
        # ("V: 1.23m" on wires, "I: -2m" on V-sources/inductors).
        self.BIAS_FONT_FAMILY = self._s("bias_annotation", "font_family", "sans-serif")
        self.BIAS_FONT_SIZE   = self._i("bias_annotation", "font_size",   7)
        self.BIAS_COLOR       = self._c("bias_annotation", "color",       "#0000ff")
        self.BIAS_DIGITS      = self._i("bias_annotation", "digits",      4)
        self.BIAS_FONT        = QFont(resolve_family(self.BIAS_FONT_FAMILY), self.BIAS_FONT_SIZE)

        # Text embedded in a symbol (+/- of a source, the pin names of a
        # subcircuit box): ONE family on the canvas and in the export. The
        # canvas drew it with the parameter font (monospace) while the
        # export wrote sans-serif (found 2026-10-10). The size comes from
        # the symbol; the QFont carries the family only.
        self.SYMBOL_TEXT_FONT_FAMILY = self._s("symbol", "font_family", "sans-serif")
        self.SYMBOL_TEXT_FONT        = QFont(resolve_family(self.SYMBOL_TEXT_FONT_FAMILY))

        # Scale (%) of the parameter table / model definition blocks — the
        # single source for their on-canvas size (natural size × this value).
        # LaTeX fragments and images scale per instance in their dialogs.
        self.SCALE_PARAMETER_TABLE = self._i("scales", "parameter_table", 60)

        # Border (export frame): the look a NEW border gets; each border then
        # keeps its own values in the schematic file (Border dialog). A book
        # sets its figure background here once, e.g. bg_color = #ecf3ff,
        # bg_alpha = 100, show_line_in_export = false (Anton, 2026-09-26).
        # Defaults = the palette of the book Structured Electronic Design
        # (Anton, 2026-10-06): blue line, the light blue background of the
        # book's figures at full opacity, and no border line in the export.
        self.BORDER_LINE_COLOR = self._c("border", "line_color", "#0000ff")
        self.BORDER_LINE_WIDTH = self._f("border", "line_width", 0.8)
        self.BORDER_LINE_STYLE = self._s("border", "line_style", "solid")
        self.BORDER_BG_COLOR   = self._c("border", "bg_color",   "#ecf3ff")
        self.BORDER_BG_ALPHA   = self._i("border", "bg_alpha",   100)
        self.BORDER_SHOW_LINE  = self._b("border", "show_line_in_export", False)
        # Border formats defined by the user: name -> (width_mm, height_mm),
        # a side None = free (not fixed). A figure of the book is "a fixed
        # width, the column, and a free height" (Anton, 2026-10-09). Offered
        # next to the paper and screen formats in the Border, Properties and
        # New poster dialogs (document_properties_dialog.border_formats).
        self.BORDER_PRESETS = {}
        if self._cfg.has_section("border_presets"):
            for name, text in self._cfg["border_presets"].items():
                size = parse_border_preset(text)
                if size is not None:
                    self.BORDER_PRESETS[name.strip()] = size

    # -- Preferences-dialog protocol --------------------------------------------

    def snapshot(self) -> configparser.ConfigParser:
        """A copy of the effective style for the Preferences dialog to edit."""
        cfg = style_parser()
        for section in self._cfg.sections():
            cfg[section] = {k: v for k, v in self._cfg[section].items()}
        return cfg

    def apply_parser(self, cfg: configparser.ConfigParser) -> None:
        """Replace the style with `cfg` (the Preferences dialog's result)."""
        self._cfg = style_parser()
        for section in cfg.sections():
            self._cfg[section] = {k: v for k, v in cfg[section].items()}
        self._recompute()

    def write(self, path) -> None:
        """Serialise the effective style to `path` (the schematic's .ini)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            self._cfg.write(fh)


_default_style: Style | None = None


def style_parser() -> configparser.ConfigParser:
    """A parser for style.ini files. Keys keep their case: a border preset
    is named by the user ("Column", "A4 slide")."""
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    return cfg


def parse_border_preset(text: str):
    """``"120 x"``, ``"x 80"`` or ``"210 x 297"`` (mm) -> (width, height)
    with None for a free side. None when the text is not a size."""
    parts = str(text).lower().split("x")
    if len(parts) != 2:
        return None
    try:
        w = float(parts[0]) if parts[0].strip() else None
        h = float(parts[1]) if parts[1].strip() else None
    except ValueError:
        return None
    if w is None and h is None:
        return None
    if (w is not None and w <= 0) or (h is not None and h <= 0):
        return None
    return w, h


def format_border_preset(width_mm, height_mm) -> str:
    """The inverse of parse_border_preset: ``"120 x"`` for a free height."""
    w = f"{width_mm:g}" if width_mm is not None else ""
    h = f"{height_mm:g}" if height_mm is not None else ""
    return f"{w} x {h}".strip()


def default_style() -> Style:
    """The style.ini template style — the style of anything not (yet) tied to
    a schematic: items not added to a scene, previews without a panel."""
    global _default_style
    if _default_style is None:
        _default_style = Style()
    return _default_style


def shift_held() -> bool:
    """Shift is down (queried outside an event, e.g. in itemChange)."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        return bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)
    except Exception:
        return False


FINE_STEP = GRID_SIZE / 5      # the fine grid under Shift: one symbol unit


def snap_fine(pos):
    """Snap to the fine grid (FINE_STEP): Shift held while dragging. Free
    placement was tried and REJECTED (Anton, 2026-09-27): a line shorter
    than a grid step could no longer be kept horizontal or vertical."""
    return QPointF(round(pos.x() / FINE_STEP) * FINE_STEP,
                   round(pos.y() / FINE_STEP) * FINE_STEP)


def snap_pos(item, value):
    """The one snapping rule for a moving item (Anton, 2026-09-27):
    grid-critical items (components, wires, junctions, symbol pins:
    ``GRID_CRITICAL = True``) always snap to the grid, because connectivity
    is computed from their positions; annotations (``SNAPS_TO_GRID = False``)
    never snap; everything else (shapes, border, the parameter / analysis /
    model / library / command blocks) snaps to the grid, or to the fine grid
    while Shift is held during the drag."""
    if getattr(item, "GRID_CRITICAL", False):
        return snap(value)
    if not getattr(item, "SNAPS_TO_GRID", True):
        return value
    return snap_fine(value) if shift_held() else snap(value)


def dark_theme_active() -> bool:
    """True when the canvases must draw dark: the app preference 'colour
    scheme' (~/SLiCAP_gui.ini) says 'dark', or says 'system' and the desktop
    reports a dark scheme through Qt's style hints. The preference decides
    first because a platform may not honour a requested scheme (the
    offscreen platform does not, 2026-09-27)."""
    try:
        from .app_prefs import get_color_scheme
        pref = get_color_scheme()
    except Exception:
        pref = "system"
    if pref == "dark":
        return True
    if pref == "light":
        return False
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtCore import Qt
        app = QGuiApplication.instance()
        return app is not None and app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def _invert_lightness(c: QColor) -> QColor:
    h, sat, l, a = c.getHslF()
    out = QColor.fromHslF(max(0.0, h) if h >= 0 else 0.0, sat, 1.0 - l, a)
    if h < 0:                       # achromatic: keep it achromatic
        out = QColor.fromHslF(0.0, 0.0, 1.0 - l, a)
    return out


def display_color(c) -> QColor:
    """A document colour as drawn on screen: itself in the light theme, its
    lightness inverted in the dark theme, the rule of display_style applied
    to a single colour (a shape's own stroke or fill; Anton, 2026-09-27)."""
    c = QColor(c)
    return _invert_lightness(c) if dark_theme_active() else c


def canvas_background() -> QColor:
    """The colour behind a drawing on screen: the canvas, and every preview
    of a symbol (palette icon, Place Symbol dialog), which shows the symbol as
    it will be placed (Anton, 2026-09-27)."""
    return QColor(30, 30, 30) if dark_theme_active() else QColor(255, 255, 255)


def display_style(style: Style) -> Style:
    """The style to DRAW with on screen: the document style itself in the
    light theme; in the dark theme a copy with every colour's lightness
    inverted (black wires become white, white fills dark, red stays red).
    The document style, and therefore every export, is never changed:
    display and print are separated at this one point (Anton, 2026-09-27)."""
    if not dark_theme_active():
        return style
    cached = getattr(style, "_dark_variant", None)
    if cached is not None:
        return cached
    variant = copy.copy(style)
    for name, value in vars(style).items():
        if isinstance(value, QColor):
            setattr(variant, name, _invert_lightness(value))
    variant._dark_variant = variant
    style._dark_variant = variant
    return variant


def style_of(item) -> Style:
    """Resolve a QGraphicsItem's DISPLAY style through its scene (defaults
    when the item is not in a scene, or is a duck-typed stand-in without one).
    Exports read ``scene.style`` directly and get the document colours."""
    scene = item.scene() if hasattr(item, "scene") else None
    return display_style(getattr(scene, "style", None) or default_style())
