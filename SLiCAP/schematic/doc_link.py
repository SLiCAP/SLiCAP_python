"""
Links into the SLiCAP manual (2026-09-28).

The manual ships with the package (``ini.doc_path`` = ``…/SLiCAP/docs/html``),
so a documentation link opens the INSTALLED copy when it has the page, and
the online manual only when it has not: offline-safe, and the page matches
the installed version (Anton, 2026-07-16). One resolver for every link the
GUI shows: the dialogs' reference links and the symbols' ``data-info``
links, which point at ``https://www.slicap.org/<page>#<anchor>`` (a user
found them opening the site's front page, 2026-09-25).
"""
from pathlib import Path

ONLINE_ROOT = "https://www.slicap.org/"
_API_SECTIONS = ("introduction", "userguide", "tutorials", "syntax", "reference")


def reference_url(page: str, anchor: str = "") -> str:
    """URL of a manual page: the local installed copy when present, else
    the online manual. *page* is the path inside the manual, e.g.
    ``API/syntax/devices.html``."""
    from PySide6.QtCore import QUrl
    import SLiCAP.SLiCAPconfigure as ini
    frag = f"#{anchor}" if anchor else ""
    local = Path(getattr(ini, "doc_path", "")) / page
    if local.is_file():
        return QUrl.fromLocalFile(str(local)).toString() + frag
    return ONLINE_ROOT + page + frag


def resolve_link(url: str) -> str:
    """A link as written in a symbol's ``data-info``: a link into the
    online manual is resolved through :func:`reference_url` (local copy
    first); any other link is returned unchanged."""
    if not url.startswith(ONLINE_ROOT):
        return url
    page, _, anchor = url[len(ONLINE_ROOT):].partition("#")
    if page and not page.endswith((".html", "/")):
        page += ".html"                    # ``syntax/devices`` in older symbols
    # the manual lives under API/ and GUI/ (slicap.org, 2026-09-28); links
    # written before that layout name the section directly
    if page.split("/", 1)[0] in _API_SECTIONS:
        page = "API/" + page
    return reference_url(page, anchor)
