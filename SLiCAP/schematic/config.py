from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont

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
        self._cfg = configparser.ConfigParser()
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
        # LaTeX rendering preference of THIS schematic.  Whether LaTeX is
        # installed on this machine is a separate, global fact
        # (latex_label.LATEX_INSTALLED) — the only global in the LaTeX story.
        self.LATEX_RENDERING_ENABLED = self._b("rendering", "latex_rendering", True)

        # Symbol colours
        self.SYMBOL_STROKE_COLOR = self._c("symbol", "stroke_color", "#000000")
        self.SYMBOL_TEXT_COLOR   = self._c("symbol", "text_color",   "#0000cc")

        # Wire
        self.WIRE_COLOR = self._c("wire", "color", "#000000")
        self.WIRE_WIDTH = self._f("wire", "width", 1.0)

        # Net labels
        self.NET_LABEL_COLOR     = self._c("net_label", "color",     "#26a269")
        self.NET_LABEL_FONT_SIZE = self._i("net_label", "font_size", 7)
        self.NET_LABEL_FONT      = QFont("sans-serif", self.NET_LABEL_FONT_SIZE)

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
        self.COMP_LABEL_FONT         = QFont(self.COMP_REFDES_FONT_FAMILY,
                                             self.COMP_LABEL_FONT_SIZE)

        # Component parameter labels (value, noisetemp, …)
        self.COMP_PARAM_FONT_FAMILY = self._s("component_param", "font_family", "monospace")
        self.COMP_PARAM_FONT_SIZE   = self._i("component_param", "font_size",   6)
        self.COMP_PARAM_COLOR       = self._c("component_param", "color",       "#000000")
        self.COMP_PARAM_FONT        = QFont(self.COMP_PARAM_FONT_FAMILY,
                                            self.COMP_PARAM_FONT_SIZE)
        self.COMP_PARAM_LATEX_SCALE = self._i("component_param", "latex_scale", 30)
        self.COMP_PARAM_SVG_HEIGHT  = self.COMP_PARAM_LATEX_SCALE / 100.0 * 20.0

        # Grid
        self.GRID_MINOR_COLOR = self._c("grid", "minor_color", "#DCDCDC")
        self.GRID_MAJOR_COLOR = self._c("grid", "major_color", "#B4B4B4")

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
        self.FREE_TEXT_FONT      = QFont("sans-serif", self.FREE_TEXT_FONT_SIZE)

        # SLiCAP command blocks
        self.COMMAND_COLOR     = self._c("command", "color",     "#004080")
        self.COMMAND_FONT_SIZE = self._i("command", "font_size",  7)
        self.COMMAND_FONT      = QFont("monospace", self.COMMAND_FONT_SIZE)

        # Text annotations
        self.TEXT_FONT_FAMILY = self._s("text", "font_family", "sans-serif")
        self.TEXT_FONT_SIZE   = self._i("text", "font_size",   7)
        self.TEXT_COLOR       = self._c("text", "color",       "#333333")
        self.TEXT_FONT        = QFont(self.TEXT_FONT_FAMILY, self.TEXT_FONT_SIZE)

        # Hyperlinks
        self.HYPERLINK_FONT_FAMILY = self._s("hyperlink", "font_family", "sans-serif")
        self.HYPERLINK_FONT_SIZE   = self._i("hyperlink", "font_size",   7)
        self.HYPERLINK_COLOR       = self._c("hyperlink", "color",       "#0000cc")
        self.HYPERLINK_UNDERLINE   = self._b("hyperlink", "underline",   True)
        self.HYPERLINK_FONT        = QFont(self.HYPERLINK_FONT_FAMILY,
                                           self.HYPERLINK_FONT_SIZE)
        self.HYPERLINK_FONT.setUnderline(self.HYPERLINK_UNDERLINE)

        # DC operating-point (bias) back-annotations on NGspice schematics
        # ("V: 1.23m" on wires, "I: -2m" on V-sources/inductors).
        self.BIAS_FONT_FAMILY = self._s("bias_annotation", "font_family", "sans-serif")
        self.BIAS_FONT_SIZE   = self._i("bias_annotation", "font_size",   7)
        self.BIAS_COLOR       = self._c("bias_annotation", "color",       "#B00020")
        self.BIAS_DIGITS      = self._i("bias_annotation", "digits",      4)
        self.BIAS_FONT        = QFont(self.BIAS_FONT_FAMILY, self.BIAS_FONT_SIZE)

        # Scale (%) of the parameter table / model definition blocks — the
        # single source for their on-canvas size (natural size × this value).
        # LaTeX fragments and images scale per instance in their dialogs.
        self.SCALE_PARAMETER_TABLE = self._i("scales", "parameter_table", 60)

    # -- Preferences-dialog protocol --------------------------------------------

    def snapshot(self) -> configparser.ConfigParser:
        """A copy of the effective style for the Preferences dialog to edit."""
        cfg = configparser.ConfigParser()
        for section in self._cfg.sections():
            cfg[section] = {k: v for k, v in self._cfg[section].items()}
        return cfg

    def apply_parser(self, cfg: configparser.ConfigParser) -> None:
        """Replace the style with `cfg` (the Preferences dialog's result)."""
        self._cfg = configparser.ConfigParser()
        for section in cfg.sections():
            self._cfg[section] = {k: v for k, v in cfg[section].items()}
        self._recompute()

    def write(self, path) -> None:
        """Serialise the effective style to `path` (the schematic's .ini)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            self._cfg.write(fh)


_default_style: Style | None = None


def default_style() -> Style:
    """The style.ini template style — the style of anything not (yet) tied to
    a schematic: items not added to a scene, previews without a panel."""
    global _default_style
    if _default_style is None:
        _default_style = Style()
    return _default_style


def style_of(item) -> Style:
    """Resolve a QGraphicsItem's style through its scene (defaults when the
    item is not in a scene, or is a duck-typed stand-in without one)."""
    scene = item.scene() if hasattr(item, "scene") else None
    return getattr(scene, "style", None) or default_style()
