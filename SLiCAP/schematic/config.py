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


# ── style — loaded from style.ini, falls back to defaults ────────────────────

STYLE_FILE = Path(__file__).parent.parent / "files" / "symbols" / "slicap" / "style.ini"

_cfg = configparser.ConfigParser()
_cfg.read(STYLE_FILE)


def _c(section: str, key: str, default: str) -> QColor:
    try:
        return QColor(_cfg[section][key])
    except KeyError:
        return QColor(default)


def _f(section: str, key: str, default: float) -> float:
    try:
        return float(_cfg[section][key])
    except (KeyError, ValueError):
        return default


def _i(section: str, key: str, default: int) -> int:
    try:
        return int(_cfg[section][key])
    except (KeyError, ValueError):
        return default


def _s(section: str, key: str, default: str) -> str:
    try:
        return _cfg[section][key].strip()
    except KeyError:
        return default


def _b(section: str, key: str, default: bool) -> bool:
    try:
        return _cfg[section][key].strip().lower() in ("true", "1", "yes")
    except KeyError:
        return default


# LaTeX rendering preference
LATEX_RENDERING_ENABLED = _b("rendering", "latex_rendering", True)

# Symbol colours
SYMBOL_STROKE_COLOR = _c("symbol", "stroke_color", "#000000")
SYMBOL_TEXT_COLOR   = _c("symbol", "text_color",   "#000000")

# Wire
WIRE_COLOR = _c("wire", "color", "#000000")
WIRE_WIDTH = _f("wire", "width", 1.0)

# Net labels
NET_LABEL_COLOR     = _c("net_label", "color",     "#0055BB")
NET_LABEL_FONT_SIZE = _i("net_label", "font_size", 7)
NET_LABEL_FONT      = QFont("sans-serif", NET_LABEL_FONT_SIZE)

# Component refdes labels
COMP_REFDES_FONT_FAMILY = _s("component_label", "font_family", "sans-serif")
COMP_LABEL_COLOR        = _c("component_label", "color",       "#000000")
COMP_LABEL_FONT_SIZE    = _i("component_label", "font_size",   7)
COMP_LABEL_LATEX_SCALE  = _i("component_label", "latex_scale", 100)
COMP_LABEL_SVG_HEIGHT   = COMP_LABEL_LATEX_SCALE / 100.0 * 20.0
COMP_LABEL_FONT         = QFont(COMP_REFDES_FONT_FAMILY, COMP_LABEL_FONT_SIZE)

# Component parameter labels (value, noisetemp, …)
COMP_PARAM_FONT_FAMILY = _s("component_param", "font_family", "sans-serif")
COMP_PARAM_FONT_SIZE   = _i("component_param", "font_size",   7)
COMP_PARAM_COLOR       = _c("component_param", "color",       "#0055BB")
COMP_PARAM_FONT        = QFont(COMP_PARAM_FONT_FAMILY, COMP_PARAM_FONT_SIZE)
COMP_PARAM_LATEX_SCALE = _i("component_param", "latex_scale", 60)
COMP_PARAM_SVG_HEIGHT  = COMP_PARAM_LATEX_SCALE / 100.0 * 20.0

# Grid
GRID_MINOR_COLOR = _c("grid", "minor_color", "#DCDCDC")
GRID_MAJOR_COLOR = _c("grid", "major_color", "#B4B4B4")

# Wire vertex handles + unconnected-pin connection markers (same section)
HANDLE_COLOR     = _c("handles", "color", "#0078D7")
HANDLE_SIZE      = _f("handles", "size",  4.0)
CONNECTION_COLOR = _c("handles", "connection_color", "#888888")

# Junctions
JUNCTION_COLOR  = _c("junctions", "color",  "#000000")
JUNCTION_RADIUS = _f("junctions", "radius", 3.0)

# Free text annotations
FREE_TEXT_COLOR     = _c("free_text", "color",     "#333333")
FREE_TEXT_FONT_SIZE = _i("free_text", "font_size",  8)
FREE_TEXT_FONT      = QFont("sans-serif", FREE_TEXT_FONT_SIZE)

# SLiCAP command blocks
COMMAND_COLOR     = _c("command", "color",     "#004080")
COMMAND_FONT_SIZE = _i("command", "font_size",  7)
COMMAND_FONT      = QFont("monospace", COMMAND_FONT_SIZE)

# Text annotations
TEXT_FONT_FAMILY = _s("text", "font_family", "sans-serif")
TEXT_FONT_SIZE   = _i("text", "font_size",   8)
TEXT_COLOR       = _c("text", "color",       "#333333")
TEXT_FONT        = QFont(TEXT_FONT_FAMILY, TEXT_FONT_SIZE)

# Hyperlinks
HYPERLINK_FONT_FAMILY = _s("hyperlink", "font_family", "sans-serif")
HYPERLINK_FONT_SIZE   = _i("hyperlink", "font_size",   8)
HYPERLINK_COLOR       = _c("hyperlink", "color",       "#0000cc")
HYPERLINK_UNDERLINE   = _b("hyperlink", "underline",   True)
HYPERLINK_FONT        = QFont(HYPERLINK_FONT_FAMILY, HYPERLINK_FONT_SIZE)

# Default scaling (%) applied when first placing canvas items
SCALE_PARAMETER_TABLE = _i("scales", "parameter_table", 100)
SCALE_LATEX_FRAGMENT  = _i("scales", "latex_fragment",  100)
SCALE_IMAGE           = _i("scales", "image",            50)


def load(schematic_ini=None) -> None:
    """Load global defaults (style.ini), then a schematic's overrides on top.

    The global style.ini is the template for new schematics; an opened
    schematic's ``<name>.ini`` (a full style snapshot) overrides it so the
    drawing always looks as it did when saved, regardless of this machine's
    global defaults.
    """
    _cfg.clear()
    _cfg.read(STYLE_FILE)
    if schematic_ini is not None and Path(schematic_ini).is_file():
        _cfg.read(str(schematic_ini))
    _apply()


def reload() -> None:
    """Re-read the current sources (global + current schematic .ini) and apply."""
    from . import project
    load(project.ini_path())


def apply_parser(cfg) -> None:
    """Replace the in-memory style with `cfg` and propagate live (used by the
    Preferences dialog, which edits the current schematic's style)."""
    _cfg.clear()
    for section in cfg.sections():
        _cfg[section] = {k: v for k, v in cfg[section].items()}
    _apply(rescale_items=True)


def snapshot() -> "configparser.ConfigParser":
    """A copy of the current effective style (for the Preferences dialog)."""
    cfg = configparser.ConfigParser()
    for section in _cfg.sections():
        cfg[section] = {k: v for k, v in _cfg[section].items()}
    return cfg


def write(path) -> None:
    """Serialise the current effective style to `path` (the schematic's .ini)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        _cfg.write(fh)


def _apply(*, rescale_items: bool = False) -> None:
    """Recompute every style constant from _cfg and push into all app modules."""
    import sys

    # Recompute every style constant and update this module's globals.
    g = sys.modules[__name__].__dict__

    g["LATEX_RENDERING_ENABLED"] = _b("rendering", "latex_rendering", True)

    # Push updated LATEX_AVAILABLE into latex_label (depends on both system
    # check and user preference, so it needs special handling here).
    ll = sys.modules.get("SLiCAP.schematic.latex_label")
    if ll is not None:
        ll.__dict__["LATEX_AVAILABLE"] = (
            ll.__dict__.get("_LATEX_INSTALLED", False)
            and g["LATEX_RENDERING_ENABLED"]
        )

    g["SYMBOL_STROKE_COLOR"] = _c("symbol", "stroke_color", "#000000")
    g["SYMBOL_TEXT_COLOR"]   = _c("symbol", "text_color",   "#000000")

    g["WIRE_COLOR"] = _c("wire", "color", "#000000")
    g["WIRE_WIDTH"] = _f("wire", "width", 1.2)

    g["NET_LABEL_COLOR"]     = _c("net_label", "color",     "#0055BB")
    g["NET_LABEL_FONT_SIZE"] = _i("net_label", "font_size", 7)
    g["NET_LABEL_FONT"]      = QFont("sans-serif", g["NET_LABEL_FONT_SIZE"])

    g["COMP_REFDES_FONT_FAMILY"] = _s("component_label", "font_family", "sans-serif")
    g["COMP_LABEL_COLOR"]       = _c("component_label", "color",       "#000000")
    g["COMP_LABEL_FONT_SIZE"]   = _i("component_label", "font_size",   7)
    g["COMP_LABEL_LATEX_SCALE"] = _i("component_label", "latex_scale", 100)
    g["COMP_LABEL_SVG_HEIGHT"]  = g["COMP_LABEL_LATEX_SCALE"] / 100.0 * 20.0
    g["COMP_LABEL_FONT"]        = QFont(g["COMP_REFDES_FONT_FAMILY"], g["COMP_LABEL_FONT_SIZE"])

    g["COMP_PARAM_FONT_FAMILY"] = _s("component_param", "font_family", "sans-serif")
    g["COMP_PARAM_FONT_SIZE"]   = _i("component_param", "font_size",   7)
    g["COMP_PARAM_COLOR"]       = _c("component_param", "color",       "#0055BB")
    g["COMP_PARAM_FONT"]        = QFont(g["COMP_PARAM_FONT_FAMILY"], g["COMP_PARAM_FONT_SIZE"])
    g["COMP_PARAM_LATEX_SCALE"] = _i("component_param", "latex_scale", 60)
    g["COMP_PARAM_SVG_HEIGHT"]  = g["COMP_PARAM_LATEX_SCALE"] / 100.0 * 20.0

    g["GRID_MINOR_COLOR"] = _c("grid", "minor_color", "#DCDCDC")
    g["GRID_MAJOR_COLOR"] = _c("grid", "major_color", "#B4B4B4")

    g["HANDLE_COLOR"]     = _c("handles", "color", "#0078D7")
    g["HANDLE_SIZE"]      = _f("handles", "size",  4.0)
    g["CONNECTION_COLOR"] = _c("handles", "connection_color", "#888888")

    g["JUNCTION_COLOR"]  = _c("junctions", "color",  "#000000")
    g["JUNCTION_RADIUS"] = _f("junctions", "radius", 3.0)

    g["FREE_TEXT_COLOR"]     = _c("free_text", "color",     "#333333")
    g["FREE_TEXT_FONT_SIZE"] = _i("free_text", "font_size",  8)
    g["FREE_TEXT_FONT"]      = QFont("sans-serif", g["FREE_TEXT_FONT_SIZE"])

    g["COMMAND_COLOR"]     = _c("command", "color",     "#004080")
    g["COMMAND_FONT_SIZE"] = _i("command", "font_size",  7)
    g["COMMAND_FONT"]      = QFont("monospace", g["COMMAND_FONT_SIZE"])

    g["TEXT_FONT_FAMILY"] = _s("text", "font_family", "sans-serif")
    g["TEXT_FONT_SIZE"]   = _i("text", "font_size",   8)
    g["TEXT_COLOR"]       = _c("text", "color",       "#333333")
    g["TEXT_FONT"]        = QFont(g["TEXT_FONT_FAMILY"], g["TEXT_FONT_SIZE"])

    g["HYPERLINK_FONT_FAMILY"] = _s("hyperlink", "font_family", "sans-serif")
    g["HYPERLINK_FONT_SIZE"]   = _i("hyperlink", "font_size",   8)
    g["HYPERLINK_COLOR"]       = _c("hyperlink", "color",       "#0000cc")
    g["HYPERLINK_UNDERLINE"]   = _b("hyperlink", "underline",   True)
    g["HYPERLINK_FONT"]        = QFont(g["HYPERLINK_FONT_FAMILY"], g["HYPERLINK_FONT_SIZE"])

    old_param_scale = g.get("SCALE_PARAMETER_TABLE", 100)
    old_latex_scale = g.get("SCALE_LATEX_FRAGMENT",  100)
    old_image_scale = g.get("SCALE_IMAGE",            50)
    g["SCALE_PARAMETER_TABLE"] = _i("scales", "parameter_table", 100)
    g["SCALE_LATEX_FRAGMENT"]  = _i("scales", "latex_fragment",  100)
    g["SCALE_IMAGE"]           = _i("scales", "image",            50)

    # Names to push to any app.* module that imported them via 'from .config import ...'
    _names = {
        "LATEX_RENDERING_ENABLED",
        "SYMBOL_STROKE_COLOR", "SYMBOL_TEXT_COLOR",
        "WIRE_COLOR", "WIRE_WIDTH",
        "NET_LABEL_COLOR", "NET_LABEL_FONT_SIZE", "NET_LABEL_FONT",
        "COMP_REFDES_FONT_FAMILY",
        "COMP_LABEL_COLOR", "COMP_LABEL_FONT_SIZE", "COMP_LABEL_LATEX_SCALE",
        "COMP_LABEL_SVG_HEIGHT", "COMP_LABEL_FONT",
        "COMP_PARAM_FONT_FAMILY", "COMP_PARAM_FONT_SIZE", "COMP_PARAM_COLOR", "COMP_PARAM_FONT",
        "COMP_PARAM_LATEX_SCALE", "COMP_PARAM_SVG_HEIGHT",
        "GRID_MINOR_COLOR", "GRID_MAJOR_COLOR",
        "HANDLE_COLOR", "HANDLE_SIZE", "CONNECTION_COLOR",
        "JUNCTION_COLOR", "JUNCTION_RADIUS",
        "FREE_TEXT_COLOR", "FREE_TEXT_FONT_SIZE", "FREE_TEXT_FONT",
        "COMMAND_COLOR", "COMMAND_FONT_SIZE", "COMMAND_FONT",
        "TEXT_FONT_FAMILY", "TEXT_FONT_SIZE", "TEXT_COLOR", "TEXT_FONT",
        "HYPERLINK_FONT_FAMILY", "HYPERLINK_FONT_SIZE", "HYPERLINK_COLOR",
        "HYPERLINK_UNDERLINE", "HYPERLINK_FONT",
        "SCALE_PARAMETER_TABLE", "SCALE_LATEX_FRAGMENT", "SCALE_IMAGE",
    }
    for mod in list(sys.modules.values()):
        if mod is None or mod is sys.modules[__name__]:
            continue
        if not getattr(mod, "__name__", "").startswith("SLiCAP.schematic."):
            continue
        md = mod.__dict__
        for name in _names:
            if name in md:
                md[name] = g[name]

    # component_item caches module-level aliases that need separate update
    ci = sys.modules.get("SLiCAP.schematic.component_item")
    if ci is not None:
        scale_changed = (
            ci.__dict__.get("_LABEL_SVG_HEIGHT") != g["COMP_LABEL_SVG_HEIGHT"] or
            ci.__dict__.get("_PARAM_SVG_HEIGHT")  != g["COMP_PARAM_SVG_HEIGHT"]
        )
        ci.__dict__["_LABEL_FONT"]       = g["COMP_LABEL_FONT"]
        ci.__dict__["_LABEL_SVG_HEIGHT"] = g["COMP_LABEL_SVG_HEIGHT"]
        ci.__dict__["_PARAM_FONT"]       = g["COMP_PARAM_FONT"]
        ci.__dict__["_PARAM_SVG_HEIGHT"] = g["COMP_PARAM_SVG_HEIGHT"]
        ci.__dict__["COMP_PARAM_COLOR"]  = g["COMP_PARAM_COLOR"]
        if scale_changed:
            for comp in list(ci._live_components):
                comp.refresh_svg_labels()

    # Rescale placed items (ParameterItem, ModelItem, LatexFragmentItem, ImageItem)
    # only when called from apply_parser() — a live Preferences change, not a reload.
    if rescale_items:
        param_ratio = (g["SCALE_PARAMETER_TABLE"] / old_param_scale
                       if old_param_scale else 1.0)
        latex_ratio = (g["SCALE_LATEX_FRAGMENT"]  / old_latex_scale
                       if old_latex_scale else 1.0)
        image_ratio = (g["SCALE_IMAGE"]           / old_image_scale
                       if old_image_scale else 1.0)

        if param_ratio != 1.0:
            pi = sys.modules.get("SLiCAP.schematic.parameter_item")
            mi = sys.modules.get("SLiCAP.schematic.model_item")
            if pi is not None:
                for item in list(pi._live_param_items):
                    item.rescale(param_ratio)
            if mi is not None:
                for item in list(mi._live_model_items):
                    item.rescale(param_ratio)

        if latex_ratio != 1.0:
            li = sys.modules.get("SLiCAP.schematic.latex_fragment_item")
            if li is not None:
                for item in list(li._live_latex_items):
                    item.rescale(latex_ratio)

        if image_ratio != 1.0:
            ii = sys.modules.get("SLiCAP.schematic.image_item")
            if ii is not None:
                for item in list(ii._live_image_items):
                    item.rescale(image_ratio)
