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
       data-info="https://...">            clickable help/datasheet link
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

from SLiCAP.SLiCAPsvgTools import _calculate_element_bbox

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


def _geometry_bbox(g_element) -> tuple | None:
    """Union of every drawable child's bounding box, or None if there is none.

    Geometry is measured by SLiCAPsvgTools._calculate_element_bbox so there is a
    single implementation of SVG bbox math.  Comment nodes (callable tag) are
    skipped to keep that helper from logging spurious errors.
    """
    boxes = []
    for el in g_element.iter():
        if el is g_element or not isinstance(el.tag, str):
            continue
        b = _calculate_element_bbox(el)
        if b:
            boxes.append(b)
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _vb_str(rect: tuple) -> str:
    """Format an (x, y, w, h) tuple as an SVG viewBox attribute string."""
    return f"{rect[0]} {rect[1]} {rect[2]} {rect[3]}"


# ── one parsed symbol ─────────────────────────────────────────────────────────

class Symbol:
    """All metadata + render SVG for a single library symbol."""

    __slots__ = ("name", "prefix", "nodes", "pins", "model", "params",
                 "refs", "description", "info", "select_box", "svg", "g_xml")

    def __init__(self, g_element, source: str):
        name = g_element.get("id")
        if not name:
            raise SymbolError(f"A <g> in {source} has no id= (symbol name).")
        self.name = name
        self.prefix      = g_element.get("data-prefix", "")
        self.nodes       = (g_element.get("data-nodes") or "").split()
        self.refs        = (g_element.get("data-refs") or "").split()
        self.model       = g_element.get("data-model", "")
        self.params      = (g_element.get("data-params") or "").split()
        self.description = g_element.get("data-description", "")
        self.info        = g_element.get("data-info", "")
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
    <defs>) and from individual *.svg files in the same directory.

    Each individual file may hold one or more <g id="name" data-prefix=...>
    symbol definitions anywhere in the tree.  Individual files take effect only
    for names not already provided by the bundle.

    After construction call inject_into_component_item() to publish all loaded
    metadata into the component_item module-level dicts.
    """

    def __init__(self, svg_path: Path):
        self._symbols: dict[str, Symbol] = {}
        self._load_bundle(svg_path)
        self._scan_individual(svg_path.parent, exclude=svg_path.name)

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

    def add_bundle(self, path) -> None:
        """Overlay a frozen <name>.symbols bundle: its symbols OVERRIDE the
        system ones of the same name (a schematic renders with the symbols it was
        drawn with, and user-defined symbols win)."""
        if not path or not Path(path).is_file():
            return
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        try:
            root = ET.parse(str(path), parser).getroot()
        except ET.ParseError:
            return
        for g in root.iter(f"{{{SVG_NS}}}g"):
            if g.get("id") and g.get("data-prefix"):
                self._add_g(g, Path(path).name, override=True)

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

    def _scan_individual(self, directory: Path, exclude: str) -> None:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        for svg_file in sorted(directory.glob("*.svg")):
            if svg_file.name == exclude:
                continue
            try:
                root = ET.parse(svg_file, parser).getroot()
            except ET.ParseError:
                continue
            for g in root.iter(f"{{{SVG_NS}}}g"):
                name = g.get("id")
                if not name or not g.get("data-prefix") or name in self._symbols:
                    continue  # not a symbol, or bundle already provides it
                self._symbols[name] = Symbol(g, svg_file.name)

    # ── public API ────────────────────────────────────────────────────────────

    def inject_into_component_item(self) -> None:
        """Publish loaded metadata into the component_item module dicts.

        Authoritative: the dicts are cleared first so they mirror exactly the
        symbols in THIS library (rebuilding on Open/New never leaves a previous
        schematic's symbols behind)."""
        import SLiCAP.schematic.component_item as ci
        for d in (ci.SYMBOL_PREFIX, ci.PIN_POSITIONS, ci.SYMBOL_TIGHT_RECT,
                  ci.SYMBOL_NODES, ci.SYMBOL_MODEL, ci.SYMBOL_PARAMS,
                  ci.SYMBOL_REFS, ci.SYMBOL_DESCRIPTION, ci.SYMBOL_INFO):
            d.clear()
        ci.SYMBOL_PREFIX.update({n: s.prefix for n, s in self._symbols.items()})
        ci.PIN_POSITIONS.update({n: list(s.pins) for n, s in self._symbols.items()})
        ci.SYMBOL_TIGHT_RECT.update({n: s.select_box for n, s in self._symbols.items()})
        ci.SYMBOL_NODES.update({n: list(s.nodes) for n, s in self._symbols.items()})
        ci.SYMBOL_MODEL.update({n: s.model for n, s in self._symbols.items()})
        ci.SYMBOL_PARAMS.update({n: list(s.params) for n, s in self._symbols.items()})
        ci.SYMBOL_REFS.update({n: len(s.refs) for n, s in self._symbols.items()})
        ci.SYMBOL_DESCRIPTION.update({n: s.description for n, s in self._symbols.items()})
        ci.SYMBOL_INFO.update({n: s.info for n, s in self._symbols.items()})

    @property
    def names(self) -> list[str]:
        return list(self._symbols.keys())

    def symbol(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def svg_bytes(self, name: str) -> bytes | None:
        sym = self._symbols.get(name)
        return sym.svg if sym else None
