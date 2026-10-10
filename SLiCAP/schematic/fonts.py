"""
One font family for the editor, the SVG and the PDF (Anton, 2026-10-10).

The generic families of the drawing preferences and the text dialog
(sans-serif, serif, monospace) stay the names in the files and the dialogs,
the decision of 2026-10-06. They are DRAWN with the DejaVu fonts that
matplotlib, a SLiCAP dependency, ships as TTF files:

- the editor loads the files into Qt and draws a generic family with the
  shipped family (resolve_family);
- the SVG names the shipped family first and the generic family as the
  fallback (svg_family), so a browser with DejaVu shows the same outlines;
- the PDF embeds the files: svglib and reportlab get them registered under
  the shipped AND the generic names (register_pdf_fonts).

Before this the canvas, the browser and the PDF used three fonts for the
same text: the system's sans, the browser's sans and Helvetica. The plus
of a source sat half a millimetre lower in the PDF than on the canvas, and
a subcircuit symbol with longer text differed more. The remedy of a
per-renderer correction was not considered: the difference is in the glyph
outlines, and only one set of outlines removes it.
"""
from __future__ import annotations

from pathlib import Path

# generic family -> the shipped family that draws it
SHIPPED = {"sans-serif": "DejaVu Sans", "serif": "DejaVu Serif",
           "monospace": "DejaVu Sans Mono"}
_FILES = {
    "sans-serif": {(False, False): "DejaVuSans.ttf", (True, False): "DejaVuSans-Bold.ttf",
                   (False, True): "DejaVuSans-Oblique.ttf", (True, True): "DejaVuSans-BoldOblique.ttf"},
    "serif":      {(False, False): "DejaVuSerif.ttf", (True, False): "DejaVuSerif-Bold.ttf",
                   (False, True): "DejaVuSerif-Italic.ttf", (True, True): "DejaVuSerif-BoldItalic.ttf"},
    "monospace":  {(False, False): "DejaVuSansMono.ttf", (True, False): "DejaVuSansMono-Bold.ttf",
                   (False, True): "DejaVuSansMono-Oblique.ttf", (True, True): "DejaVuSansMono-BoldOblique.ttf"},
}
_qt_loaded = False
_pdf_registered = False


def font_dir() -> Path | None:
    """matplotlib's TTF folder, or None when matplotlib is absent."""
    try:
        import matplotlib
        d = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        return d if d.is_dir() else None
    except Exception:
        return None


def font_file(generic: str, bold: bool = False, italic: bool = False) -> Path | None:
    """The shipped TTF of a generic family in a weight and style, or None."""
    d = font_dir()
    name = _FILES.get(generic, {}).get((bold, italic))
    if d is None or name is None:
        return None
    p = d / name
    return p if p.is_file() else None


def generic_of(family: str) -> str | None:
    """The generic family a name stands for: itself for a generic name, the
    generic of a shipped name, None for any other named font."""
    family = (family or "").strip()
    if family in SHIPPED:
        return family
    for generic, shipped in SHIPPED.items():
        if family == shipped:
            return generic
    return None


def load_qt_fonts() -> bool:
    """Load the shipped files into Qt's font database, once. False when there
    is no GUI application yet or the files are missing."""
    global _qt_loaded
    if _qt_loaded:
        return True
    try:
        from PySide6.QtGui import QGuiApplication, QFontDatabase
    except Exception:
        return False
    if QGuiApplication.instance() is None:
        return False
    ok = True
    for generic in SHIPPED:
        for bold in (False, True):
            for italic in (False, True):
                f = font_file(generic, bold, italic)
                if f is None or QFontDatabase.addApplicationFont(str(f)) < 0:
                    ok = False
    _qt_loaded = ok
    return ok


def resolve_family(family: str) -> str:
    """The family the editor draws *family* with: the shipped family for a
    generic name once the files are loaded, else the name as given (Qt
    then resolves a generic name to a system font, as before)."""
    generic = generic_of(family)
    if generic is None:
        return family
    return SHIPPED[generic] if load_qt_fonts() else generic


def svg_family(family: str) -> str:
    """The font-family an export writes: "DejaVu Sans, sans-serif" for a
    generic or a shipped name, a named font as it is."""
    generic = generic_of(family)
    if generic is None:
        return family or "sans-serif"
    return f"{SHIPPED[generic]}, {generic}"


def register_pdf_fonts() -> bool:
    """Register the shipped files with svglib/reportlab under the shipped
    and the generic names, once, so the PDF embeds them. False when the
    files are missing: svglib then falls back to Helvetica."""
    global _pdf_registered
    if _pdf_registered:
        return True
    try:
        from svglib.fonts import register_font_family
    except Exception:
        return False
    ok = True
    for generic, shipped in SHIPPED.items():
        files = {k: font_file(generic, *k) for k in ((False, False), (True, False),
                                                      (False, True), (True, True))}
        if any(f is None for f in files.values()):
            ok = False
            continue
        for name in (shipped, generic):
            register_font_family(name, normal=str(files[(False, False)]),
                                 bold=str(files[(True, False)]),
                                 italic=str(files[(False, True)]),
                                 bolditalic=str(files[(True, True)]))
    _pdf_registered = ok
    return ok
