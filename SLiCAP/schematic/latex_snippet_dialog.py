"""Backwards-compatible shim.

The LaTeX snippet dialog is now one instantiation of the generic,
formatter-agnostic :class:`~SLiCAP.schematic.snippet_dialog.SnippetDialog`
(RST today; MyST / HTML / plain text later — each just a ``SnippetTarget``).
New code should import from ``snippet_dialog``; this module preserves the
original import path.
"""
from .snippet_dialog import (  # noqa: F401
    SnippetDialog, SnippetTarget,
    LatexSnippetDialog, RstSnippetDialog,
    LATEX_TARGET, RST_TARGET,
    KIND_TEXT, KIND_FILE, KIND_OBJECT, KIND_SPECS,
    _q, _ident,
)
