"""
LaTeX expression rendering for schematic labels.

Values wrapped in { } are treated as sympy-parseable expressions:

  1. Strip outer braces:  {1/(2*pi*R*C)}  →  1/(2*pi*R*C)
  2. SLiCAP._checkExpression(str)  →  sympy object
  3. SLiCAP._latex_ENG(sympy_obj)  →  LaTeX string
  4. Wrap in a minimal standalone LaTeX document and run pdflatex → PDF
  5. dvisvgm --pdf  PDF → SVG

SVG bytes are cached as <cache>/<sha256>.svg so each expression is rendered only
once.  The cache directory is per-schematic (``<name>.cache``), set by
app.project; until a schematic is saved it is a per-session temp dir.  Returns
None on any failure; callers fall back to plain text.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import contextlib
from pathlib import Path

# ── cache directory ───────────────────────────────────────────────────────────
# Relocated per-schematic by app.project.set_current().  Until something is
# actually rendered it stays None; the first use lazily creates a per-session
# temp dir, so nothing accumulates in a global cache and no dir is made unless
# needed.

CACHE_DIR: Path | None = None


def get_cache_dir() -> Path:
    """Return the current cache dir, lazily creating a session temp on first use."""
    global CACHE_DIR
    if CACHE_DIR is None:
        CACHE_DIR = Path(tempfile.mkdtemp(prefix="slicap_latex_"))
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def set_cache_dir(path: Path) -> None:
    """Point the rendered-LaTeX SVG cache at ``path`` (called by app.project).

    The directory is NOT created here — only when something is actually rendered
    (get_cache_dir), so a schematic with no LaTeX leaves no empty .cache dir."""
    global CACHE_DIR
    CACHE_DIR = Path(path)

# ── tool availability ─────────────────────────────────────────────────────────

# System check — immutable after startup.
_LATEX_INSTALLED: bool = (
    shutil.which("pdflatex") is not None and
    shutil.which("dvisvgm")  is not None
)

# Effective flag: also gated by the user preference in config.
# config._apply() (via load/apply_parser) updates this value when it changes.
try:
    from .config import LATEX_RENDERING_ENABLED as _enabled
    LATEX_AVAILABLE: bool = _LATEX_INSTALLED and _enabled
except ImportError:
    LATEX_AVAILABLE: bool = _LATEX_INSTALLED

# ── LaTeX template ────────────────────────────────────────────────────────────

_TEX_TEMPLATE = r"""\documentclass[preview,varwidth=true,border=2pt]{standalone}
\usepackage{amsmath}
\begin{document}
%s
\end{document}
"""

# ── lazy SLiCAP import ────────────────────────────────────────────────────────
# Imported on first use so that startup is unaffected.
# CWD is changed to CACHE_DIR during the import so that SLiCAP.ini is
# created there rather than in the schematic project folder.

_slicap_ready: bool | None = None   # None = not yet attempted
_slicap_check = None
_slicap_latex = None


def _ensure_slicap() -> bool:
    global _slicap_ready, _slicap_check, _slicap_latex
    if _slicap_ready is not None:
        return _slicap_ready
    orig = os.getcwd()
    try:
        os.chdir(get_cache_dir())
        with contextlib.redirect_stdout(io.StringIO()):
            from SLiCAP.SLiCAPmath import _checkExpression
            from SLiCAP.SLiCAPhtml import _latex_ENG
            from SLiCAP.SLiCAPlatex import sub2rm
        _slicap_check = _checkExpression
        # IEEE typesetting: subscripts that are plain alphanumeric labels are set
        # upright (\mathrm) rather than italic.  Applied here, at the single
        # SLiCAP→LaTeX boundary, so every generated equation/symbol — component
        # value labels and the parameter & model tables alike — is formatted
        # consistently.  (Free-form user LaTeX fragments do not pass through here
        # and keep whatever formatting the user wrote.)
        def _latex_ieee(sympy_obj):
            s = _latex_ENG(sympy_obj)
            return sub2rm(s) if s else s
        _slicap_latex = _latex_ieee
        _slicap_ready = True
    except Exception:
        _slicap_ready = False
    finally:
        os.chdir(orig)
    return _slicap_ready


# ── calibration ───────────────────────────────────────────────────────────────

_reference_line_height: float | None = None


def svg_line_height() -> float | None:
    """
    Return the viewBox height (in SVG units) of a single-line LaTeX expression.

    Renders '$x$' once and caches the result.  This gives the natural height
    of one line of math as produced by the pdflatex + pdf2svg pipeline, so
    callers can derive a scale factor without hard-coding pdf2svg's unit system.
    Returns None when the pipeline is unavailable.
    """
    if not LATEX_AVAILABLE:
        return None
    global _reference_line_height
    if _reference_line_height is not None:
        return _reference_line_height
    svg = _render_cached("x")
    if svg is None:
        return None
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QByteArray
    r = QSvgRenderer(QByteArray(svg))
    if r.isValid() and r.viewBoxF().height() > 0:
        _reference_line_height = r.viewBoxF().height()
    return _reference_line_height


# ── public API ────────────────────────────────────────────────────────────────

def is_expression(value_str: str) -> bool:
    """True when the value string is a {…} expression."""
    s = value_str.strip()
    return s.startswith("{") and s.endswith("}")


def _is_placeholder(expr_str: str) -> bool:
    """True for the bare "?" reminder used for unset values/models.

    It is shown literally as a prompt to the user and must never be handed to
    SLiCAP's expression parser, which would raise a Sympify error on it."""
    return expr_str.strip() == "?"


def render_name_eq_value(name: str, value_str: str) -> bytes | None:
    """
    Render '\text{name} = value' as SVG for component labels (show_name=True).

    Uses _latex_to_svg directly (not _render_cached) so the combined LaTeX
    string is never passed through the SymPy parser.
    """
    if not LATEX_AVAILABLE:
        return None
    safe = name.replace('_', r'\_').replace('^', r'\^{}')
    val = value_str.strip()
    if not (val.startswith("{") and val.endswith("}")):
        val = "{" + val + "}"
    val_tex = expression_to_latex(val)
    if not val_tex:
        val_tex = val[1:-1]
    return _render_latex_str(rf"{{\footnotesize \textsf{{{safe}}}}} = {val_tex}")


def render_expression(value_str: str) -> bytes | None:
    """
    Convert a {…} value string to SVG bytes.

    Returns cached bytes if available, renders fresh otherwise.
    Returns None when LaTeX rendering is disabled, the value is not an
    expression, SLiCAP is unavailable, or any step in the pipeline fails.
    """
    if not LATEX_AVAILABLE:
        return None
    if not is_expression(value_str):
        return None
    expr_str = value_str.strip()[1:-1].strip()
    return _render_cached(expr_str)


def expression_to_latex(value_str: str) -> str:
    """
    Convert a value string to a LaTeX math string using the SLiCAP pipeline.

    If the value is a {…} expression, it is parsed by SLiCAP's
    _checkExpression and converted to LaTeX via _latex_ENG — identical to how
    component value labels are typeset.  Any other string is returned as-is
    (treated as raw LaTeX).

    Used by ParameterItem.build_latex so parameter names and values are
    rendered with the same method as component values.
    """
    if not is_expression(value_str):
        return value_str
    expr_str = value_str.strip()[1:-1].strip()
    if _is_placeholder(expr_str):
        return expr_str                  # unset "?" reminder — render literally
    if not _ensure_slicap():
        return expr_str
    try:
        sympy_obj = _slicap_check(expr_str)
        if sympy_obj is None:
            return expr_str
        result = _slicap_latex(sympy_obj)
        if not result:
            return expr_str
        return result
    except Exception:
        return expr_str


# ── implementation ────────────────────────────────────────────────────────────

# Bump when the SLiCAP→LaTeX formatting changes (e.g. sub2rm IEEE subscripts),
# so SVGs cached under an older formatting are re-rendered rather than reused.
_FORMAT_VERSION = "ieee-sub2rm-1"


def _cache_path(expr_str: str) -> Path:
    h = hashlib.sha256((_FORMAT_VERSION + "\x00" + expr_str).encode()).hexdigest()[:24]
    return get_cache_dir() / f"{h}.svg"


def _render_cached(expr_str: str) -> bytes | None:
    path = _cache_path(expr_str)
    if path.exists():
        return path.read_bytes()
    svg = _render_fresh(expr_str)
    if svg is not None:
        path.write_bytes(svg)
    return svg


def _render_fresh(expr_str: str) -> bytes | None:
    if not LATEX_AVAILABLE or not _ensure_slicap():
        return None
    if _is_placeholder(expr_str):
        return None                      # unset "?" reminder — not an expression
    try:
        sympy_obj = _slicap_check(expr_str)
        if sympy_obj is None:
            return None
        latex_str = _slicap_latex(sympy_obj)
        if not latex_str:
            return None
    except Exception:
        return None
    return _latex_to_svg(latex_str)


def _render_latex_str(latex_str: str) -> bytes | None:
    """Cache and render a pre-built LaTeX math string, bypassing SymPy parsing."""
    if not LATEX_AVAILABLE:
        return None
    h = hashlib.sha256(("raw:" + latex_str).encode()).hexdigest()[:24]
    path = get_cache_dir() / f"{h}.svg"
    if path.exists():
        return path.read_bytes()
    svg = _latex_to_svg(latex_str)
    if svg is not None:
        path.write_bytes(svg)
    return svg


def _latex_to_svg(latex_str: str) -> bytes | None:
    """Compile a LaTeX math string to SVG via pdflatex + dvisvgm."""
    with tempfile.TemporaryDirectory(dir=get_cache_dir()) as tmp:
        tmpdir   = Path(tmp)
        tex_file = tmpdir / "expr.tex"
        tex_file.write_text(
            _TEX_TEMPLATE % f"${latex_str}$",
            encoding="utf-8",
        )
        subprocess.run(
            ["pdflatex", "-interaction=batchmode", "expr.tex"],
            cwd=tmpdir,
            capture_output=True,
        )
        pdf_file = tmpdir / "expr.pdf"
        if not pdf_file.exists():
            return None

        svg_file = tmpdir / "expr.svg"
        subprocess.run(
            ["dvisvgm", "--pdf", "--no-fonts", "expr.pdf", "-o", "expr.svg"],
            cwd=tmpdir,
            capture_output=True,
        )
        if not svg_file.exists():
            return None

        return svg_file.read_bytes()


# ── standalone fragment rendering ─────────────────────────────────────────────

def render_latex_raw(latex_code: str,
                     preamble_path: str = "") -> tuple[bytes | None, str]:
    """
    Compile arbitrary LaTeX code to SVG via pdflatex + dvisvgm.

    latex_code is inserted verbatim inside a standalone document.
    If preamble_path is a readable file its content is included before
    \\begin{document}; otherwise amsmath + amssymb are loaded.

    Returns (svg_bytes, error_text).  On success error_text is "".
    Results are cached in CACHE_DIR keyed on content hash.
    """
    if not LATEX_AVAILABLE:
        return None, "pdflatex or dvisvgm not found"
    if preamble_path:
        p = Path(preamble_path)
        preamble = (p.read_text(encoding="utf-8", errors="replace")
                    if p.is_file() else
                    f"% preamble not found: {preamble_path}\n"
                    r"\usepackage{amsmath}" + "\n" + r"\usepackage{amssymb}" + "\n")
    else:
        preamble = r"\usepackage{amsmath}" + "\n" + r"\usepackage{amssymb}" + "\n"

    cache_key = hashlib.sha256(
        (preamble + "\x00" + latex_code).encode()
    ).hexdigest()[:24]
    cached = get_cache_dir() / f"frag_{cache_key}.svg"
    if cached.exists():
        return cached.read_bytes(), ""

    doc = (
        r"\documentclass[preview,varwidth=true,border=2pt]{standalone}" + "\n"
        + preamble + "\n"
        + r"\begin{document}" + "\n"
        + latex_code + "\n"
        + r"\end{document}" + "\n"
    )
    with tempfile.TemporaryDirectory(dir=get_cache_dir()) as tmp:
        tmpdir = Path(tmp)
        tex = tmpdir / "frag.tex"
        tex.write_text(doc, encoding="utf-8")
        subprocess.run(
            ["pdflatex", "-interaction=batchmode", "frag.tex"],
            cwd=tmpdir, capture_output=True,
        )
        pdf = tmpdir / "frag.pdf"
        if not pdf.exists():
            log = tmpdir / "frag.log"
            if log.exists():
                lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
                errs = [l for l in lines if l.startswith("!")]
                return None, "\n".join(errs[:5]) if errs else "pdflatex failed"
            return None, "pdflatex failed (no output)"
        svg = tmpdir / "frag.svg"
        subprocess.run(
            ["dvisvgm", "--pdf", "--no-fonts", "frag.pdf", "-o", "frag.svg"],
            cwd=tmpdir, capture_output=True,
        )
        if not svg.exists():
            return None, "dvisvgm failed"
        data = svg.read_bytes()
        cached.write_bytes(data)
        return data, ""
