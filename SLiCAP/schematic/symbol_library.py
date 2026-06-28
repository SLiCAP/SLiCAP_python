"""
Symbol library loader.

A symbol is one ``<g id="name">`` element in an SVG ``<defs>`` block.  Every
piece of information the editor needs is carried by the ``<g>`` itself, so a
symbol file is fully self-describing and the editor needs nothing from the
SLiCAP Python package's model tables:

    <g id="CCCS"
       data-prefix="F"                     device-type prefix / refdes letter
       data-nodes="outp outn"              ordered SLiCAP node names
       data-refs="V?"                      referenced elements (CCCS/CCVS/K)
       data-model="F"                      SLiCAP model name
       data-params="value"                 overridable parameter names
       data-description="..."              shown in Place / Properties dialogs
       data-info="https://..."             clickable help/datasheet link
       data-show-pinnames="true">          draw node names on canvas (block symbols)
        ...artwork...
        <circle cx="0" cy="-20" r="0.5" class="node" data-node="outp"/>
        <circle cx="0" cy="20"  r="0.5" class="node" data-node="outn"/>
    </g>

Pin positions are read from the ``class="node"`` elements (matched to
``data-nodes`` by ``data-node``); they are always explicit, never guessed.

The select box (= drawn extent) is *computed* from the symbol's own geometry
plus one grid-unit of padding for the outline stroke.  This is a deterministic
calculation, not a guess: it always matches what is actually drawn, and because
the node markers are part of the geometry it is guaranteed to enclose every pin.
A symbol with a node name that has no matching marker, or with no drawable
geometry at all, is malformed and raises SymbolError — such mistakes are
reported, never silently worked around.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# Selection margin added on every side of the painted extent.  The painted
# extent already includes each element's stroke (SLiCAPsvgTools accounts for
# stroke width), so this is purely a small breathing space between the artwork
# and the select box / render viewBox — not a stroke compensation.
_BBOX_PAD = 0.5


class SymbolError(ValueError):
    """Raised when a symbol's definition is incomplete or malformed."""


def _local(tag) -> str:
    """Namespace-stripped tag name; '' for comments (whose tag is callable)."""
    return tag.split("}")[-1] if isinstance(tag, str) else ""


def _f(el, attr: str, default: float = 0.0) -> float:
    try:
        return float(el.get(attr, default))
    except (TypeError, ValueError):
        return default


def _stroke_halfwidth(attrib) -> float:
    stroke = attrib.get("stroke", "none")
    if stroke in ("none", ""):
        return 0.0
    try:
        return float(attrib.get("stroke-width", "1")) / 2.0
    except (TypeError, ValueError):
        return 0.0


def _text_bbox(element, attrib) -> tuple | None:
    try:
        x = float(attrib.get("x", "0"))
        y = float(attrib.get("y", "0"))
        font_size = float(attrib.get("font-size", "10"))
    except (TypeError, ValueError):
        return None
    width = len(element.text or "") * 0.6 * font_size
    anchor = attrib.get("text-anchor", "start")
    if anchor == "middle":
        x0, x1 = x - width / 2.0, x + width / 2.0
    elif anchor == "end":
        x0, x1 = x - width, x
    else:
        x0, x1 = x, x + width
    # Cover both alphabetic and middle-baseline Qt rendering (see SLiCAPsvgTools).
    y0, y1 = y - 0.9 * font_size, y + 0.5 * font_size
    return (x0, y0, x1, y1)


def _element_bbox(el) -> tuple | None:
    """Return (x0, y0, x1, y1) for one SVG element, or None if unrecognised.

    Uses direct arithmetic for simple shapes (avoids svgelements.Line.bbox()
    which raises on degenerate lines in some versions).  Text extents are
    estimated from character count and font-size.  Stroke width is added on
    all sides.
    """
    tag = el.tag.split("}")[-1] if isinstance(el.tag, str) else ""
    a = el.attrib
    bbox = None
    try:
        if tag == "text":
            bbox = _text_bbox(el, a)
        elif tag == "line":
            x1, y1 = float(a.get("x1", 0)), float(a.get("y1", 0))
            x2, y2 = float(a.get("x2", 0)), float(a.get("y2", 0))
            bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        elif tag == "rect":
            x, y = float(a.get("x", 0)), float(a.get("y", 0))
            w, h = float(a.get("width", 0)), float(a.get("height", 0))
            bbox = (x, y, x + w, y + h)
        elif tag == "circle":
            cx, cy, r = float(a.get("cx", 0)), float(a.get("cy", 0)), float(a.get("r", 0))
            bbox = (cx - r, cy - r, cx + r, cy + r)
        elif tag == "ellipse":
            cx, cy = float(a.get("cx", 0)), float(a.get("cy", 0))
            rx, ry = float(a.get("rx", 0)), float(a.get("ry", 0))
            bbox = (cx - rx, cy - ry, cx + rx, cy + ry)
        elif tag in ("polyline", "polygon"):
            coords = [float(v) for v in a.get("points", "").replace(",", " ").split()]
            xs, ys = coords[0::2], coords[1::2]
            if xs and ys:
                bbox = (min(xs), min(ys), max(xs), max(ys))
        elif tag == "path":
            from svgelements import Path as _SvgPath
            bb = _SvgPath(d=a.get("d", "")).bbox()
            if bb and len(bb) == 4:
                bbox = (bb[0], bb[1], bb[2], bb[3])
    except Exception:
        pass
    if bbox is not None:
        hw = _stroke_halfwidth(a)
        if hw:
            x0, y0, x1, y1 = bbox
            bbox = (x0 - hw, y0 - hw, x1 + hw, y1 + hw)
    return bbox


def _geometry_bbox(g_element) -> tuple | None:
    """Union bounding box of all drawable children, or None if there are none."""
    boxes = [b for el in g_element.iter()
             if el is not g_element and isinstance(el.tag, str)
             for b in (_element_bbox(el),) if b is not None]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _vb_str(rect: tuple) -> str:
    """Format an (x, y, w, h) tuple as an SVG viewBox attribute string."""
    return f"{rect[0]} {rect[1]} {rect[2]} {rect[3]}"


# ── one parsed symbol ─────────────────────────────────────────────────────────

def description_to_html(desc: str) -> str:
    """Render a symbol's data-description as safe HTML for the place/properties
    dialogs: a literal ``\\n`` (and any real newline) becomes a line break, all
    other text is HTML-escaped."""
    import html as _html
    return _html.escape(desc or "").replace("\\n", "<br>").replace("\n", "<br>")


def _parse_model_field(raw: str, source: str, sym: str) -> tuple[str, bool]:
    """Parse ``data-model`` = ``name|show`` into ``(name, show_on_canvas)``.

    An empty/absent attribute means "no model" → ``("", False)``.  The pipe form
    is required; a bare ``name`` (the old format) is rejected so libraries are
    migrated cleanly."""
    raw = (raw or "").strip()
    if not raw:
        return "", False
    if "|" not in raw:
        raise SymbolError(
            f"Symbol '{sym}' in {source}: data-model='{raw}' is not in the "
            f"'name|show' form (e.g. 'C|0' or '?|1')."
        )
    name, _, show = raw.partition("|")
    return name.strip(), show.strip() == "1"


def _parse_params_field(
    raw: str, source: str, sym: str
) -> tuple[dict[str, str], dict[str, tuple[bool, bool]]]:
    """Parse ``data-params`` = ``name|default|show_name|show_value; …``.

    Returns ``(defaults, display)`` where ``defaults`` maps each parameter name
    to its default value/expression and ``display`` maps it to the
    ``(show_value, show_name)`` pair used by ComponentItem.prop_display.  Insertion
    order (= on-canvas order) is preserved.  Every entry must carry all four
    pipe-separated fields; not-applicable fields are left empty (e.g. ``W||0|0``)."""
    defaults: dict[str, str] = {}
    display:  dict[str, tuple[bool, bool]] = {}
    for entry in (raw or "").split(";"):
        entry = entry.strip()
        if not entry:
            continue
        fields = entry.split("|")
        if len(fields) != 4:
            raise SymbolError(
                f"Symbol '{sym}' in {source}: parameter entry '{entry}' must have "
                f"four pipe-separated fields: name|default|show_name|show_value."
            )
        pname = fields[0].strip()
        defaults[pname] = fields[1].strip()
        display[pname]  = (fields[3].strip() == "1", fields[2].strip() == "1")
    return defaults, display


class Symbol:
    """All metadata + render SVG for a single library symbol."""

    __slots__ = ("name", "prefix", "nodes", "pins", "model", "model_show",
                 "params", "param_defaults", "param_display",
                 "refs", "description", "info", "show_pinnames",
                 "select_box", "svg", "g_xml")

    def __init__(self, g_element, source: str):
        name = g_element.get("id")
        if not name:
            raise SymbolError(f"A <g> in {source} has no id= (symbol name).")
        self.name = name
        self.prefix      = g_element.get("data-prefix", "")
        self.nodes       = (g_element.get("data-nodes") or "").split()
        self.refs        = (g_element.get("data-refs") or "").split()
        self.model, self.model_show = _parse_model_field(
            g_element.get("data-model", ""), source, name)
        self.param_defaults, self.param_display = _parse_params_field(
            g_element.get("data-params", ""), source, name)
        self.params      = list(self.param_defaults.keys())
        self.description = g_element.get("data-description", "")
        self.info        = g_element.get("data-info", "")
        # Whether to draw the SLiCAP node names on the canvas.  Block symbols
        # (auto-generated subcircuit boxes) set this true because their shape
        # carries no pin meaning; hand-drawn symbols leave it unset (false), as
        # their artwork already identifies each pin.
        self.show_pinnames = (g_element.get("data-show-pinnames", "")
                              .strip().lower() in ("true", "1", "yes"))
        self.pins        = self._read_pins(g_element, source)

        box = _geometry_bbox(g_element)
        if box is None:
            raise SymbolError(
                f"Symbol '{name}' in {source} has no drawable geometry; its "
                f"extent cannot be computed."
            )
        x0, y0, x1, y1 = (float(v) for v in box)
        self.select_box = (x0 - _BBOX_PAD, y0 - _BBOX_PAD,
                           (x1 - x0) + 2 * _BBOX_PAD, (y1 - y0) + 2 * _BBOX_PAD)
        self.svg = self._render(g_element)
        # Raw <g> source, kept so the symbol can be re-exported verbatim into a
        # schematic's frozen <name>.symbols bundle.
        self.g_xml = ET.tostring(g_element, encoding="unicode")

    def _read_pins(self, g_element, source: str) -> list[tuple[float, float]]:
        """Pin coordinates in data-nodes order, from the node markers."""
        markers: dict[str, tuple[float, float]] = {}
        for el in g_element.iter():
            if _local(el.tag) == "circle" and el.get("class") == "node":
                node = el.get("data-node")
                if node is not None:
                    markers[node] = (_f(el, "cx"), _f(el, "cy"))
        pins = []
        for node in self.nodes:
            if node not in markers:
                raise SymbolError(
                    f"Symbol '{self.name}' in {source}: data-nodes lists '{node}' "
                    f"but there is no <circle class=\"node\" data-node=\"{node}\">."
                )
            pins.append(markers[node])
        return pins

    def _render(self, g_element) -> bytes:
        """Standalone SVG (viewBox = select box) for palette/canvas rendering.

        Comment nodes are dropped; canvas scale stays 1:1 because paint() always
        renders into the viewBox.
        """
        children = "".join(
            ET.tostring(child, encoding="unicode")
            for child in g_element if not callable(child.tag)
        )
        return (
            f'<svg xmlns="{SVG_NS}" viewBox="{_vb_str(self.select_box)}">'
            f"{children}</svg>"
        ).encode()


class SymbolLibrary:
    """
    Loads symbols from a bundle file (Symbols.svg, one <g id> per symbol in
    <defs>).

    Call add_user_library() afterward to load additional SVGs from any
    directory.  Call inject_into_component_item() to publish all loaded
    metadata into the component_item module-level dicts.
    """

    def __init__(self, svg_path: Path):
        self._symbols: dict[str, Symbol] = {}
        self._load_bundle(svg_path)

    # ── loading ───────────────────────────────────────────────────────────────

    def _add_g(self, g, source: str, override: bool) -> None:
        if not g.get("id"):
            return
        if not override and g.get("id") in self._symbols:
            return
        sym = Symbol(g, source)
        self._symbols[sym.name] = sym

    def _load_bundle(self, path: Path) -> None:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        root = ET.parse(path, parser).getroot()
        defs = root.find(f"{{{SVG_NS}}}defs")
        if defs is None:
            return
        for g in defs.findall(f"{{{SVG_NS}}}g"):
            self._add_g(g, path.name, override=False)

    def add_bundle(self, path) -> list[str]:
        """Overlay a frozen <name>.symbols bundle: its symbols OVERRIDE the
        system ones of the same name (a schematic renders with the symbols it was
        drawn with, and user-defined symbols win).

        The bundle is a cache, so a symbol that no longer parses (e.g. an
        outdated metadata format) is skipped rather than aborting the load — the
        already-loaded system definition is used in its place.  Returns the names
        of any skipped symbols so the caller can report them."""
        skipped: list[str] = []
        if not path or not Path(path).is_file():
            return skipped
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        try:
            root = ET.parse(str(path), parser).getroot()
        except ET.ParseError:
            return skipped
        for g in root.iter(f"{{{SVG_NS}}}g"):
            if g.get("id") and g.get("data-prefix"):
                try:
                    self._add_g(g, Path(path).name, override=True)
                except SymbolError:
                    skipped.append(g.get("id"))
        return skipped

    def add_user_library(self, directory, exclude_stems=()) -> None:
        """Load user symbol libraries from a directory's ``*.svg`` files, AFTER
        the system bundle, so they ADD new symbols or REDEFINE (override) system
        ones.  Files whose stem is in ``exclude_stems`` are skipped — e.g. a
        generated subcircuit block symbol, which pairs with a ``<name>.lib`` and
        loads only when its block is placed, never into a fresh schematic."""
        directory = Path(directory)
        if not directory.is_dir():
            return
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        for svg_file in sorted(directory.glob("*.svg")):
            if svg_file.stem in exclude_stems:
                continue
            try:
                root = ET.parse(svg_file, parser).getroot()
            except ET.ParseError:
                continue
            for g in root.iter(f"{{{SVG_NS}}}g"):
                if g.get("id") and g.get("data-prefix"):
                    self._add_g(g, svg_file.name, override=True)

    def write_bundle(self, names, path) -> None:
        """Write the given symbols' raw <g> definitions to a bundle SVG, so the
        schematic carries a frozen copy of every symbol it uses."""
        seen: set[str] = set()
        parts: list[str] = []
        for n in names:
            if n in seen:
                continue
            seen.add(n)
            sym = self._symbols.get(n)
            if sym is not None:
                parts.append(sym.g_xml)
        content = (f'<svg xmlns="{SVG_NS}">\n  <defs>\n'
                   + "\n".join(parts) + "\n  </defs>\n</svg>\n")
        Path(path).write_text(content, encoding="utf-8")

    def update_symbols(self, other: "SymbolLibrary", names) -> list[str]:
        """Replace this library's definitions of *names* with those from *other*.

        Used to refresh a schematic's frozen symbols with the most recent
        versions from the live symbol library.  Returns the names that were
        actually found in *other* and updated; names absent there are left
        untouched (reported back so the caller can warn the user)."""
        updated: list[str] = []
        for n in names:
            sym = other.symbol(n)
            if sym is not None:
                self._symbols[n] = sym
                updated.append(n)
        return updated

    # ── public API ────────────────────────────────────────────────────────────

    def inject_into_component_item(self) -> None:
        """Publish loaded metadata into the component_item module dicts.

        Merges into the global dicts rather than replacing them so that parent
        and child schematics can both be open: activating the child window must
        not wipe the parent's subcircuit symbol (whose pin names are shown in
        the parent view).  update() overwrites same-named entries, which is
        correct when a symbol is redefined across library versions."""
        import SLiCAP.schematic.component_item as ci
        ci.SYMBOL_PREFIX.update({n: s.prefix for n, s in self._symbols.items()})
        ci.PIN_POSITIONS.update({n: list(s.pins) for n, s in self._symbols.items()})
        ci.SYMBOL_TIGHT_RECT.update({n: s.select_box for n, s in self._symbols.items()})
        ci.SYMBOL_NODES.update({n: list(s.nodes) for n, s in self._symbols.items()})
        ci.SYMBOL_MODEL.update({n: s.model for n, s in self._symbols.items()})
        ci.SYMBOL_MODEL_SHOW.update({n: s.model_show for n, s in self._symbols.items()})
        ci.SYMBOL_PARAMS.update({n: list(s.params) for n, s in self._symbols.items()})
        ci.SYMBOL_PARAM_DEFAULTS.update({n: dict(s.param_defaults) for n, s in self._symbols.items()})
        ci.SYMBOL_PARAM_DISPLAY.update({n: dict(s.param_display) for n, s in self._symbols.items()})
        ci.SYMBOL_REFS.update({n: len(s.refs) for n, s in self._symbols.items()})
        ci.SYMBOL_DESCRIPTION.update({n: s.description for n, s in self._symbols.items()})
        ci.SYMBOL_INFO.update({n: s.info for n, s in self._symbols.items()})
        ci.SYMBOL_SHOW_PINNAMES.update({n: s.show_pinnames for n, s in self._symbols.items()})

    @property
    def names(self) -> list[str]:
        return list(self._symbols.keys())

    def symbol(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def svg_bytes(self, name: str) -> bytes | None:
        sym = self._symbols.get(name)
        return sym.svg if sym else None
