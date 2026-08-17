"""
LaTeX expression rendering for schematic labels.

Values wrapped in { } are treated as sympy-parseable expressions:

  1. Strip outer braces:  {1/(2*pi*R*C)}  →  1/(2*pi*R*C)
  2. SLiCAP._checkExpression(str)  →  sympy object
  3. SLiCAP.exprLatex(sympy_obj)   →  LaTeX string
  4. Wrap in a minimal standalone LaTeX document and run pdflatex → DVI
     (``-output-format=dvi``)
  5. dvisvgm  DVI → SVG   (DVI input needs no Ghostscript; ``--pdf`` would)

SVG bytes are cached as <cache>/<sha256>.svg so each expression is rendered only
once.  The cache directory is per-schematic (the ``<name>.cache`` sidecar,
carried by the scene and passed explicitly as ``cache_dir``); non-schematic
callers use the session temp.  Returns None on any failure; callers fall back
to plain text.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import contextlib
import re
from pathlib import Path

# ── cache directories ─────────────────────────────────────────────────────────
# The render cache is PER-SCHEMATIC (the ``<name>.cache`` sidecar): every
# render function takes an explicit ``cache_dir``.  Callers not bound to a
# schematic (dialog previews, the design-data viewer, calibration) omit it and
# use one process-wide session temp, auto-created on first use.  There is no
# repointable global cache pointer.

_session_cache: Path | None = None


def session_cache_dir() -> Path:
    """The session-temp cache for renders not owned by any schematic."""
    global _session_cache
    if _session_cache is None:
        _session_cache = Path(tempfile.mkdtemp(prefix="slicap_latex_"))
    _session_cache.mkdir(parents=True, exist_ok=True)
    return _session_cache


def _resolve_cache(cache_dir) -> Path:
    if cache_dir is None:
        return session_cache_dir()
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir_of(item):
    """The render-cache dir of an item's schematic (its scene), or None —
    meaning the session temp — when the item is not scene-bound (yet)."""
    scene = item.scene() if hasattr(item, "scene") else None
    return getattr(scene, "cache_dir", None)


# ── cache garbage collection (Anton, 2026-07-12) ─────────────────────────────
# Every cache READ or WRITE records the filename per cache dir.  On schematic
# save the panel sweeps the sidecar: files not used this session are deleted.
# Everything currently displayed IS used (labels re-render — with cache hits —
# on load), so nothing live is ever removed; entries orphaned by edits are
# used no more after the edit and age out on the next session's first save at
# the latest.

_touched: dict[str, set] = {}


def _touch(cache: Path, filename: str) -> None:
    _touched.setdefault(str(cache), set()).add(filename)


def sweep_cache(cache_dir) -> int:
    """Delete renders in a schematic's ``.cache`` sidecar that were not used
    this session (called on schematic save).  Returns the number removed."""
    if cache_dir is None:
        return 0
    cache = Path(cache_dir)
    if not cache.is_dir():
        return 0
    used = _touched.get(str(cache), set())
    if not used:
        # This session never rendered/read from this cache (e.g. LaTeX
        # rendering disabled for the schematic) — it knows nothing about
        # which entries are live, so it must not sweep (Anton, 2026-07-12:
        # "the whole cache is cleared!").
        return 0
    removed = 0
    for f in cache.glob("*.svg"):
        if f.name not in used:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed

# ── tool availability ─────────────────────────────────────────────────────────

# Tool paths come from SLiCAP.ini (the [commands] section, like ngspice), so
# rendering uses an ABSOLUTE path and never depends on the GUI's launch-time
# PATH — the source of the "checkbox is greyed out" confusion. A PATH lookup is
# the fallback when the config has no entry. Resolved lazily and CWD-safely via
# _ensure_slicap (which reads the config in the session cache dir, not the
# project folder), then cached once complete.
#
# Whether LaTeX rendering is *wanted* is a per-schematic preference
# (Style.LATEX_RENDERING_ENABLED); schematic-bound callers check both,
# non-schematic callers (e.g. the design-data viewer) only LATEX_INSTALLED.
_latex_tools_cache: "tuple[str, str] | None" = None


def _latex_tools() -> "tuple[str, str]":
    """(pdflatex, dvisvgm) executable paths — SLiCAP.ini first, PATH fallback."""
    global _latex_tools_cache
    if _latex_tools_cache is not None:
        return _latex_tools_cache
    pdftex = dvisvgm = ""
    if _ensure_slicap():
        try:
            import SLiCAP.SLiCAPconfigure as _ini
            pdftex  = (getattr(_ini, "pdflatex", "") or "").strip()
            dvisvgm = (getattr(_ini, "dvisvgm",  "") or "").strip()
        except Exception:
            pass
    pdftex  = pdftex  or (shutil.which("pdflatex") or "")
    dvisvgm = dvisvgm or (shutil.which("dvisvgm")  or "")
    tools = (pdftex, dvisvgm)
    if pdftex and dvisvgm:          # cache only a complete resolution, so a
        _latex_tools_cache = tools  # later config edit / install can still take
    return tools                    # effect on the next check


def _latex_installed() -> bool:
    pdftex, dvisvgm = _latex_tools()
    return bool(pdftex) and bool(dvisvgm)


def __getattr__(name):
    # PEP 562: LATEX_INSTALLED resolves lazily against the config at each read
    # (all callers import it inside functions, so this evaluates at runtime).
    if name == "LATEX_INSTALLED":
        return _latex_installed()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ── LaTeX template ────────────────────────────────────────────────────────────

_TEX_TEMPLATE = r"""\documentclass[preview,varwidth=true,border=2pt]{standalone}
\usepackage{amsmath}
\usepackage{graphicx}
\begin{document}
%s
\end{document}
"""

# ── lazy SLiCAP import ────────────────────────────────────────────────────────
# Imported on first use so that startup is unaffected.
# CWD is changed to the session cache dir during the import so that SLiCAP.ini
# is created there rather than in the schematic project folder.

_slicap_ready: bool | None = None   # None = not yet attempted
_slicap_check = None
_slicap_latex = None                # exprLatex + sub2rm (IEEE, single values)
_slicap_latex_eng = None            # exprLatex alone (tables: sub2rm runs
                                    # once over the finished snippet instead)


def _ensure_slicap() -> bool:
    global _slicap_ready, _slicap_check, _slicap_latex, _slicap_latex_eng
    if _slicap_ready is not None:
        return _slicap_ready
    orig = os.getcwd()
    try:
        os.chdir(session_cache_dir())
        with contextlib.redirect_stdout(io.StringIO()):
            from SLiCAP.SLiCAPmath import _checkExpression
            from SLiCAP.SLiCAPlatex import exprLatex
            from SLiCAP.SLiCAPlatex import sub2rm
        _slicap_check = _checkExpression
        # IEEE typesetting: subscripts that are plain alphanumeric labels are set
        # upright (\mathrm) rather than italic.  Applied here, at the single
        # SLiCAP→LaTeX boundary, so every generated equation/symbol — component
        # value labels and the parameter & model tables alike — is formatted
        # consistently.  (Free-form user LaTeX fragments do not pass through here
        # and keep whatever formatting the user wrote.)
        def _latex_ieee(sympy_obj):
            s = exprLatex(sympy_obj)
            return sub2rm(s) if s else s
        _slicap_latex = _latex_ieee
        _slicap_latex_eng = exprLatex    # tables: sub2rm afterwards, once
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
    if not _latex_installed():
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


def render_stimuli_label(prefix: str, pairs: list, cache_dir=None) -> bytes | None:
    """Render a stimuli canvas label as SVG.

    Shows: prefix on the first line, then each name=value pair on its own
    indented line.  Names are in {\\footnotesize \\textsf{}}; values are
    LaTeX rendered.

    prefix -- waveform label incl. colon, e.g. 'pulse:'
    pairs  -- list of (param_name, value_str) tuples; value_str is a bare
              number or a {…} expression
    """
    if not _latex_installed():
        return None
    safe_pfx = prefix.replace('_', r'\_')
    rows = [rf"\text{{{safe_pfx}}}"]
    for name, value in pairs:
        safe_name = name.replace('_', r'\_').replace('^', r'\^{}')
        val = value.strip()
        if not (val.startswith("{") and val.endswith("}")):
            val = "{" + val + "}"
        val_tex = expression_to_latex(val)
        if not val_tex:
            return None          # does not parse -> not rendered (plain text)
        rows.append(rf"\quad {{\footnotesize \textsf{{{safe_name}}}}} = {val_tex}")
    latex = r"\begin{array}{l}" + r" \\".join(rows) + r"\end{array}"
    return _render_latex_str(latex, cache_dir)


def render_name_eq_value(name: str, value_str: str, cache_dir=None) -> bytes | None:
    """
    Render '\text{name} = value' as SVG for component labels (show_name=True).

    Uses _latex_to_svg directly (not _render_cached) so the combined LaTeX
    string is never passed through the SymPy parser.
    """
    if not _latex_installed():
        return None
    safe = name.replace('_', r'\_').replace('^', r'\^{}')
    val = value_str.strip()
    if not (val.startswith("{") and val.endswith("}")):
        val = "{" + val + "}"
    val_tex = expression_to_latex(val)
    if not val_tex:
        return None              # does not parse -> not rendered (plain text)
    return _render_latex_str(rf"{{\footnotesize \textsf{{{safe}}}}} = {val_tex}", cache_dir)


def refdes_to_latex(name: str, bold: bool = False) -> str:
    """LaTeX string for a refdes: the symbol name (see :func:`symbol_to_latex`)
    set UPRIGHT (``\\mathrm`` — reference designators are roman, never italic),
    optionally bold (``\\mathbf``).  Upright applies whether or not boldface is
    on.  Shared by ``render_refdes`` (component labels) and the analysis block
    (source / lgref names), so all refdesses render identically."""
    tex = symbol_to_latex(name)
    if not tex:
        return tex
    if bold:
        tex = r"\mathbf{" + tex + "}"
    return r"\mathrm{" + tex + "}"


def render_refdes(refdes: str, bold: bool = False, cache_dir=None) -> bytes | None:
    """Render an element identifier as LaTeX for IEEE-style schematics
    (customer request via Anton, 2026-07-11).

    The refdes is rendered as a *symbol name* (sympy ``latex`` + IEEE ``sub2rm``
    upright subscripts: R1 → R_1), NOT number-parsed — so a refdes like ``I1P``
    stays ``I1P`` instead of being misread as I·peta (``I1e15``). *bold* wraps
    the result in ``\\mathrm{\\mathbf{…}}``. Returns None when LaTeX is
    unavailable or the refdes cannot be rendered — the caller falls back to text.
    """
    if not _latex_installed():
        return None
    name = refdes.strip()
    if not name or _is_placeholder(name):
        return None
    tex = refdes_to_latex(name, bold)
    if not tex:
        return None
    return _render_latex_str(tex, cache_dir)


def recolor_svg(svg_bytes: bytes, color: str) -> bytes:
    """Tint a rendered LaTeX SVG (pdf2svg output is black): explicit black
    fills/strokes are replaced, and a fill on the root element recolours
    the paths that inherit. *color* is a #rrggbb string."""
    s = svg_bytes.decode("utf-8", "replace")
    s = s.replace("rgb(0%,0%,0%)", color).replace("#000000", color)
    s = re.sub(r"<svg\b", f'<svg fill="{color}"', s, count=1)
    return s.encode("utf-8")


def render_expression(value_str: str, cache_dir=None) -> bytes | None:
    """
    Convert a {…} value string to SVG bytes.

    Returns cached bytes if available, renders fresh otherwise.
    Returns None when LaTeX rendering is disabled, the value is not an
    expression, SLiCAP is unavailable, or any step in the pipeline fails.
    """
    if not _latex_installed():
        return None
    if not is_expression(value_str):
        return None
    expr_str = value_str.strip()[1:-1].strip()
    return _render_cached(expr_str, cache_dir)


# Parse results per expression string: LaTeX on success, None on failure.
# Memoised because update_labels() runs on every repaint — without it a bad
# expression is re-parsed (and re-reported) endlessly.
_expr_latex_memo: dict = {}
_expr_reported: set = set()


def expression_sympy(value_str: str):
    """The SYMPY OBJECT for a ``{…}`` value string, or None when it does not parse.

    The typed handover: derived labels and tables pass sympy objects on to
    SLiCAP's LaTeX formatter, which decides maths-vs-text BY TYPE and does its
    own escaping.  A value that does not parse never becomes an object, so it
    can never be typeset as maths - the rule is structural rather than a
    convention at each call site (Anton, 2026-08-16).
    """
    if not is_expression(value_str):
        return None
    expr_str = value_str.strip()[1:-1].strip()
    if _is_placeholder(expr_str):
        return None
    return _expression_parse(expr_str)[0]


def _expression_parse(expr_str: str):
    """``(sympy object, LaTeX)`` for an expression string; ``(None, None)`` when
    it does not parse.  Memoised and reported once - see :func:`_expression_latex`."""
    if expr_str in _expr_latex_memo:
        return _expr_latex_memo[expr_str]
    if not _ensure_slicap():
        return (None, None)              # transient: do not memoise
    result = (None, None)
    try:
        import sympy as sp
        sympy_obj = _slicap_check(expr_str)
        if isinstance(sympy_obj, sp.Basic):
            latex = _slicap_latex(sympy_obj)
            if latex:
                result = (sympy_obj, latex)
    except Exception:
        result = (None, None)
    _expr_latex_memo[expr_str] = result
    if result[0] is None and expr_str not in _expr_reported:
        _expr_reported.add(expr_str)
        # ASCII only - this goes to the console/log on every platform.
        print("Error: '{0}' is not a valid SLiCAP expression; it is NOT "
              "rendered (the label shows the plain text).".format(expr_str))
    return result


def _expression_latex(expr_str: str) -> "str | None":
    """The ONE SLiCAP expression -> LaTeX boundary.  None when it does not parse.

    Rendering runs over SLiCAP: ``_checkExpression`` (SLiCAPmath) must yield a
    SYMPY object, which ``exprLatex`` + ``sub2rm`` then typeset.  The result is
    type-checked rather than trusted, because a failed parse does not raise:
    ``_checkExpression`` prints its message and hands the RAW STRING back, and
    an input like ``I(x)`` raises TypeError instead (``I`` is SymPy's imaginary
    unit).  Both used to flow on into LaTeX, which typeset ``V_DS*(1+tanh(x))``
    as "V_D S * (1 + tanh(x))" and SUCCEEDED - a silently wrong label.

    A value that does not parse is NEVER rendered; the caller falls back to
    plain text and the reason is reported once (Anton, 2026-08-16).
    """
    return _expression_parse(expr_str)[1]


def slicap_table(header: list, rows: list, title=None) -> "str | None":
    """A SLiCAP LaTeX table for canvas blocks (parameters, model definitions).

    Built by SLiCAP's OWN formatter (``LaTeXformatter.nestedLists``) rather
    than by concatenating LaTeX here: cells that are sympy objects are set as
    maths, plain strings are set as escaped text, and the escaping is the
    formatter's business.  ``color=None`` drops the alternating row colour
    (the canvas has no preamble colour definitions), and ``sub2rm`` runs once
    over the finished snippet for IEEE upright subscripts - it only rewrites
    ``_{alphanumeric}``, is idempotent, and leaves escaped underscores in text
    cells alone (Anton, 2026-08-16: "sub2rm can run afterwards on any LaTeX
    object").  Values are formatted with SLiCAP's engineering notation so a
    table matches the component labels beside it.

    :param header: column headers; all-empty means no header row.
    :param rows: list of ``[name, value]`` cells; sympy objects -> maths.
    :param title: heading centred ACROSS the columns (so a long title does
                  not widen the first column - Anton, 2026-08-16).
    :return: LaTeX snippet, or None when SLiCAP is unavailable.
    """
    if not _ensure_slicap():
        return None
    from SLiCAP.SLiCAPlatex import LaTeXformatter, sub2rm
    snippet = LaTeXformatter().nestedLists(header, rows, color=None,
                                           value_fn=_slicap_latex_eng,
                                           title=title)
    return sub2rm(str(snippet))


def expression_to_latex(value_str: str) -> "str | None":
    """
    Convert a value string to a LaTeX math string using the SLiCAP pipeline.

    If the value is a {…} expression, it is parsed by SLiCAP's
    _checkExpression and converted to LaTeX via exprLatex — identical to how
    component value labels are typeset.  Any other string is returned as-is
    (treated as raw LaTeX).

    Returns **None** when a {…} expression does not parse: an invalid
    expression must produce an error message, never a wrongly rendered label
    (Anton, 2026-08-16).  Callers skip rendering and fall back to plain text.

    Used by ParameterItem.build_latex so parameter names and values are
    rendered with the same method as component values.
    """
    if not is_expression(value_str):
        return value_str
    expr_str = value_str.strip()[1:-1].strip()
    if _is_placeholder(expr_str):
        return expr_str                  # unset "?" reminder — render literally
    return _expression_latex(expr_str)


def symbol_to_latex(name: str) -> str:
    """LaTeX for an identifier rendered as a *symbol name*, never number-parsed.

    Schematic wrapper around ``SLiCAP.SLiCAPlatex.symbolLatex`` (the core lives
    there, next to ``sub2rm``, reusable package-wide): adds the schematic-only
    placeholder guard and availability gate, and falls back to the plain name.
    Used for refdesses and detector names, so a name like ``I1P`` stays ``I1P``
    instead of being misread as I·peta (``I1e15``) by the number formatter.
    """
    name = (name or "").strip()
    if not name or _is_placeholder(name):
        return name
    if not _ensure_slicap():
        return name
    try:
        from SLiCAP.SLiCAPlatex import symbolLatex
        return symbolLatex(name) or name
    except Exception:
        return name


# ── implementation ────────────────────────────────────────────────────────────

# Bump when the SLiCAP→LaTeX formatting changes (e.g. sub2rm IEEE subscripts),
# so SVGs cached under an older formatting are re-rendered rather than reused.
_FORMAT_VERSION = "ieee-sub2rm-1"


def _cache_path(expr_str: str, cache: Path) -> Path:
    h = hashlib.sha256((_FORMAT_VERSION + "\x00" + expr_str).encode()).hexdigest()[:24]
    return cache / f"{h}.svg"


def _render_cached(expr_str: str, cache_dir=None) -> bytes | None:
    cache = _resolve_cache(cache_dir)
    path = _cache_path(expr_str, cache)
    if path.exists():
        _touch(cache, path.name)
        return path.read_bytes()
    svg = _render_fresh(expr_str, cache)
    if svg is not None:
        path.write_bytes(svg)
        _touch(cache, path.name)
    return svg


def _render_fresh(expr_str: str, cache: Path) -> bytes | None:
    if not _latex_installed() or not _ensure_slicap():
        return None
    if _is_placeholder(expr_str):
        return None                      # unset "?" reminder — not an expression
    latex_str = _expression_latex(expr_str)      # the one parse boundary
    if not latex_str:
        return None
    return _latex_to_svg(latex_str, cache)


def _render_latex_str(latex_str: str, cache_dir=None) -> bytes | None:
    """Cache and render a pre-built LaTeX math string, bypassing SymPy parsing."""
    if not _latex_installed():
        return None
    cache = _resolve_cache(cache_dir)
    h = hashlib.sha256(("raw:" + latex_str).encode()).hexdigest()[:24]
    path = cache / f"{h}.svg"
    if path.exists():
        _touch(cache, path.name)
        return path.read_bytes()
    svg = _latex_to_svg(latex_str, cache)
    if svg is not None:
        path.write_bytes(svg)
        _touch(cache, path.name)
    return svg


def _latex_to_svg(latex_str: str, cache: Path) -> bytes | None:
    """Compile a LaTeX math string to SVG via pdflatex (DVI) + dvisvgm.

    pdflatex is run with ``-output-format=dvi`` so dvisvgm reads a DVI, not a
    PDF.  DVI needs NO Ghostscript (``dvisvgm --pdf`` on a PDF would), so a
    plain TeX distribution is the only prerequisite -- no extra packages."""
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        tmpdir   = Path(tmp)
        tex_file = tmpdir / "expr.tex"
        tex_file.write_text(
            _TEX_TEMPLATE % f"${latex_str}$",
            encoding="utf-8",
        )
        subprocess.run(
            [_latex_tools()[0], "-interaction=batchmode",
             "-output-format=dvi", "expr.tex"],
            cwd=tmpdir,
            capture_output=True,
        )
        dvi_file = tmpdir / "expr.dvi"
        if not dvi_file.exists():
            return None

        svg_file = tmpdir / "expr.svg"
        subprocess.run(
            [_latex_tools()[1], "--no-fonts", "expr.dvi", "-o", "expr.svg"],
            cwd=tmpdir,
            capture_output=True,
        )
        if not svg_file.exists():
            return None

        return svg_file.read_bytes()


# ── standalone fragment rendering ─────────────────────────────────────────────

def render_latex_raw(latex_code: str,
                     preamble_path: str = "",
                     max_width: str = "",
                     cache_dir=None) -> tuple[bytes | None, str]:
    """
    Compile arbitrary LaTeX code to SVG via pdflatex + dvisvgm.

    latex_code is inserted verbatim inside a standalone document.
    If preamble_path is a readable file its content is included before
    \\begin{document}; otherwise amsmath + amssymb are loaded.

    Returns (svg_bytes, error_text).  On success error_text is "".
    Results are cached in ``cache_dir`` (session temp when omitted),
    keyed on content hash.
    """
    if not _latex_installed():
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
        (preamble + "\x00" + latex_code + "\x00" + max_width).encode()
    ).hexdigest()[:24]
    cache = _resolve_cache(cache_dir)
    cached = cache / f"frag_{cache_key}.svg"
    if cached.exists():
        _touch(cache, cached.name)
        return cached.read_bytes(), ""

    # varwidth default (≈345pt) wraps text nicely for user fragments, but
    # CLIPS wide single boxes — a 7-column MNA matrix lost its right
    # bracket (Anton, 2026-07-12). Callers rendering natural-width content
    # (viewer math, snippet tables) pass a huge max_width so the page
    # grows to fit instead.
    varwidth = f"varwidth={max_width}" if max_width else "varwidth=true"
    doc = (
        rf"\documentclass[preview,{varwidth},border=2pt]{{standalone}}" + "\n"
        + preamble + "\n"
        + r"\begin{document}" + "\n"
        + latex_code + "\n"
        + r"\end{document}" + "\n"
    )
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        tmpdir = Path(tmp)
        tex = tmpdir / "frag.tex"
        tex.write_text(doc, encoding="utf-8")
        subprocess.run(
            [_latex_tools()[0], "-interaction=batchmode",
             "-output-format=dvi", "frag.tex"],
            cwd=tmpdir, capture_output=True,
        )
        dvi = tmpdir / "frag.dvi"
        if not dvi.exists():
            log = tmpdir / "frag.log"
            if log.exists():
                lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
                errs = [l for l in lines if l.startswith("!")]
                return None, "\n".join(errs[:5]) if errs else "pdflatex failed"
            return None, "pdflatex failed (no output)"
        svg = tmpdir / "frag.svg"
        subprocess.run(
            [_latex_tools()[1], "--no-fonts", "frag.dvi", "-o", "frag.svg"],
            cwd=tmpdir, capture_output=True,
        )
        if not svg.exists():
            return None, "dvisvgm failed"
        data = svg.read_bytes()
        cached.write_bytes(data)
        _touch(cache, cached.name)
        return data, ""
