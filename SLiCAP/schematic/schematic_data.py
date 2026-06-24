from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from datetime import date as _date

# Rename map for files saved before the Symbols.svg IDs were shortened.
_SYMBOL_NAME_MIGRATION: dict[str, str] = {
    "resistor":         "R",
    "capacitor":        "C",
    "inductor":         "L",
    "v-source":         "V",
    "i-source":         "I",
    "i-ctrld-v-source": "CCVS",
    "i-ctrld-i-source": "CCCS",
    "v-ctrld-v-source": "VCVS",
    "v-ctrld-i-source": "VCCS",
}


@dataclass
class DocumentProperties:
    title:          str   = ""
    author:         str   = ""
    created:        str   = ""    # ISO date, set once on New
    last_modified:  str   = ""    # ISO date, auto-updated on every Save
    page_size:      str   = "A4"  # standard name or "Custom"
    page_width_mm:  float = 210.0
    page_height_mm: float = 297.0
    # ── hierarchy ──────────────────────────────────────────────────────────────
    # When True, Save writes this schematic as a SLiCAP subcircuit (.lib) in
    # addition to its .slicap_sch source.  subcircuit_ports is the user-chosen
    # node order; subcircuit_params are the overridable .subckt parameters.
    is_subcircuit:     bool = False
    subcircuit_ports:  list = field(default_factory=list)   # ordered port names
    subcircuit_params: list = field(default_factory=list)   # list of [name, default]

    @staticmethod
    def new() -> "DocumentProperties":
        return DocumentProperties(created=_date.today().isoformat())


@dataclass
class ComponentData:
    symbol_name: str
    instance_id: str
    x: float
    y: float
    rotation: float = 0.0
    h_flip: bool = False
    v_flip: bool = False
    params: dict[str, str] = field(default_factory=dict)
    model: str = ""
    refs: list[str] = field(default_factory=list)
    # prop_display: {key: [show_value, show_name]}
    # show_value=False → no label; show_name only meaningful when show_value is True
    prop_display: dict[str, list[bool]] = field(
        default_factory=lambda: {"refdes": [True, False]}
    )
    # Label positions in component-local coordinates: {key: [x, y]}
    prop_offsets: dict[str, list[float]] = field(default_factory=dict)


@dataclass
class WireData:
    points: list[tuple[float, float]]
    net_name: str | None = None
    display_name: bool = False
    label_offset: tuple[float, float] = (0.0, -3.0)
    net_locked: bool = False
    user_net_name: str | None = None


@dataclass
class JunctionData:
    x: float
    y: float


@dataclass
class FreeTextData:
    x: float
    y: float
    text: str


@dataclass
class HyperlinkData:
    x: float
    y: float
    url: str
    label: str


@dataclass
class CommandData:
    x: float
    y: float
    text: str


@dataclass
class LibraryData:
    x: float
    y: float
    file_path: str
    directive: str = "lib"    # "lib" or "inc"
    simulator: str = "SLiCAP" # "SLiCAP" or "SPICE"
    corner:    str = ""       # SPICE corner (only for SPICE .lib)


@dataclass
class ModelData:
    x: float
    y: float
    model_name:    str
    model_type:    str
    simulator:     str          # "SLiCAP" or "SPICE"
    params:        list         # list of [name, value] string pairs
    preamble_path: str  = ""
    svg_b64:       str  = ""
    display_width:  int = 200
    display_height: int = 80


@dataclass
class ImageData:
    x: float
    y: float
    file_path: str
    display_width: int
    display_height: int


@dataclass
class BorderData:
    x: float
    y: float
    width: float
    height: float
    show_in_export: bool = True


@dataclass
class ParameterData:
    x: float
    y: float
    params: list          # list of [name, value] string pairs
    preamble_path: str
    display_width: int
    display_height: int
    svg_b64: str = ""    # kept for reading old files; no longer written


@dataclass
class AnalysisData:
    x: float
    y: float
    source:   list   # 0-2 refdes strings
    detector: list   # 0-2 [type, ref] pairs; type = "V" or "I"
    lgref:    list   # 0-2 refdes strings


@dataclass
class LatexFragmentData:
    x: float
    y: float
    latex_code: str
    preamble_path: str
    display_width: int
    display_height: int
    svg_b64: str = ""  # kept for reading old files; no longer written


@dataclass
class ShapeData:
    kind:           str                       # "line" | "rect" | "circle"
    x:              float                     # pos() anchor
    y:              float
    rel_points:     list[tuple[float, float]] # local coords relative to (x, y)
    stroke_color:   str   = "#000000"
    fill_color:     str   = "#ffffff"
    fill_style:     str   = "none"            # "none" | "solid"
    line_style:     str   = "solid"           # "solid"|"dashed"|"dotted"|"dash-dot"
    line_end_start: str   = "none"            # "none"|"arrow"|"dot"|"diamond"
    line_end_end:   str   = "none"
    line_width:     float = 1.5


@dataclass
class SchematicData:
    components:  list[ComponentData]  = field(default_factory=list)
    wires:       list[WireData]       = field(default_factory=list)
    junctions:   list[JunctionData]   = field(default_factory=list)
    free_texts:  list[FreeTextData]   = field(default_factory=list)
    hyperlinks:  list[HyperlinkData]  = field(default_factory=list)
    commands:    list[CommandData]    = field(default_factory=list)
    libs:             list[LibraryData]          = field(default_factory=list)
    images:           list[ImageData]            = field(default_factory=list)
    border:           BorderData | None          = None
    latex_fragments:  list[LatexFragmentData]    = field(default_factory=list)
    parameters:       list[ParameterData]        = field(default_factory=list)
    analysis_items:   list[AnalysisData]         = field(default_factory=list)
    shapes:           list[ShapeData]            = field(default_factory=list)
    model_defs:       list[ModelData]            = field(default_factory=list)
    properties:       DocumentProperties         = field(default_factory=DocumentProperties)

    def to_json(self) -> str:
        data = {
            "components": [
                {
                    "symbol_name": c.symbol_name,
                    "instance_id": c.instance_id,
                    "x": c.x,
                    "y": c.y,
                    "rotation": c.rotation,
                    "h_flip": c.h_flip,
                    "v_flip": c.v_flip,
                    "params": c.params,
                    "model": c.model,
                    "refs": c.refs,
                    "prop_display": c.prop_display,
                    "prop_offsets": c.prop_offsets,
                }
                for c in self.components
            ],
            "wires": [
                {
                    "points": list(w.points),
                    "net_name": w.net_name,
                    "display_name": w.display_name,
                    "label_offset": list(w.label_offset),
                    "net_locked": w.net_locked,
                    "user_net_name": w.user_net_name,
                }
                for w in self.wires
            ],
            "junctions": [
                {"x": j.x, "y": j.y}
                for j in self.junctions
            ],
            "free_texts": [
                {"x": t.x, "y": t.y, "text": t.text}
                for t in self.free_texts
            ],
            "hyperlinks": [
                {"x": h.x, "y": h.y, "url": h.url, "label": h.label}
                for h in self.hyperlinks
            ],
            "commands": [
                {"x": c.x, "y": c.y, "text": c.text}
                for c in self.commands
            ],
            "libs": [
                {
                    "x": l.x, "y": l.y, "file_path": l.file_path,
                    "directive": l.directive, "simulator": l.simulator,
                    "corner": l.corner,
                }
                for l in self.libs
            ],
            "images": [
                {
                    "x": i.x, "y": i.y,
                    "file_path": i.file_path,
                    "display_width": i.display_width,
                    "display_height": i.display_height,
                }
                for i in self.images
            ],
            "border": {
                "x": self.border.x,
                "y": self.border.y,
                "width": self.border.width,
                "height": self.border.height,
                "show_in_export": self.border.show_in_export,
            } if self.border is not None else None,
            "latex_fragments": [
                {
                    "x": f.x, "y": f.y,
                    "latex_code": f.latex_code,
                    "preamble_path": f.preamble_path,
                    "display_width":  f.display_width,
                    "display_height": f.display_height,
                }
                for f in self.latex_fragments
            ],
            "parameters": [
                {
                    "x": p.x, "y": p.y,
                    "params": p.params,
                    "preamble_path": p.preamble_path,
                    "display_width":  p.display_width,
                    "display_height": p.display_height,
                }
                for p in self.parameters
            ],
            "analysis_items": [
                {
                    "x": a.x, "y": a.y,
                    "source":   a.source,
                    "detector": a.detector,
                    "lgref":    a.lgref,
                }
                for a in self.analysis_items
            ],
            "shapes": [
                {
                    "kind":           s.kind,
                    "x":              s.x,
                    "y":              s.y,
                    "rel_points":     s.rel_points,
                    "stroke_color":   s.stroke_color,
                    "fill_color":     s.fill_color,
                    "fill_style":     s.fill_style,
                    "line_style":     s.line_style,
                    "line_end_start": s.line_end_start,
                    "line_end_end":   s.line_end_end,
                    "line_width":     s.line_width,
                }
                for s in self.shapes
            ],
            "model_defs": [
                {
                    "x": m.x, "y": m.y,
                    "model_name":    m.model_name,
                    "model_type":    m.model_type,
                    "simulator":     m.simulator,
                    "params":        [list(p) for p in m.params],
                    "preamble_path": m.preamble_path,
                    "display_width":  m.display_width,
                    "display_height": m.display_height,
                }
                for m in self.model_defs
            ],
            "properties": {
                "title":          self.properties.title,
                "author":         self.properties.author,
                "created":        self.properties.created,
                "last_modified":  self.properties.last_modified,
                "page_size":      self.properties.page_size,
                "page_width_mm":  self.properties.page_width_mm,
                "page_height_mm": self.properties.page_height_mm,
                "is_subcircuit":     self.properties.is_subcircuit,
                "subcircuit_ports":  list(self.properties.subcircuit_ports),
                "subcircuit_params": [list(p) for p in self.properties.subcircuit_params],
            },
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, text: str) -> SchematicData:
        data = json.loads(text)
        components = [
            ComponentData(
                symbol_name=_SYMBOL_NAME_MIGRATION.get(c["symbol_name"], c["symbol_name"]),
                instance_id=c["instance_id"],
                x=c["x"],
                y=c["y"],
                rotation=c.get("rotation", 0.0),
                h_flip=c.get("h_flip", False),
                v_flip=c.get("v_flip", False),
                params=c.get("params", {}),
                model=c.get("model", ""),
                refs=c.get("refs", []),
                prop_display=c.get("prop_display", {"refdes": [True, False]}),
                prop_offsets=c.get("prop_offsets", {}),
            )
            for c in data.get("components", [])
        ]
        wires = [
            WireData(
                points=[tuple(p) for p in w["points"]],
                net_name=w.get("net_name"),
                display_name=w.get("display_name", False),
                label_offset=tuple(w.get("label_offset", [0.0, -3.0])),
                net_locked=w.get("net_locked", False),
                user_net_name=w.get("user_net_name"),
            )
            for w in data.get("wires", [])
        ]
        junctions = [
            JunctionData(x=j["x"], y=j["y"])
            for j in data.get("junctions", [])
        ]
        free_texts = [
            FreeTextData(x=t["x"], y=t["y"], text=t.get("text", ""))
            for t in data.get("free_texts", [])
        ]
        hyperlinks = [
            HyperlinkData(x=h["x"], y=h["y"],
                          url=h.get("url", ""), label=h.get("label", ""))
            for h in data.get("hyperlinks", [])
        ]
        commands = [
            CommandData(x=c["x"], y=c["y"], text=c.get("text", ""))
            for c in data.get("commands", [])
        ]
        libs = [
            LibraryData(
                x=l["x"], y=l["y"], file_path=l["file_path"],
                directive=l.get("directive", "lib"),
                simulator=l.get("simulator", "SLiCAP"),
                corner=l.get("corner", ""),
            )
            for l in data.get("libs", [])
        ]
        images = [
            ImageData(
                x=i["x"], y=i["y"],
                file_path=i["file_path"],
                display_width=i["display_width"],
                display_height=i["display_height"],
            )
            for i in data.get("images", [])
        ]
        bd = data.get("border")
        border = BorderData(
            x=bd["x"], y=bd["y"],
            width=bd["width"], height=bd["height"],
            show_in_export=bd.get("show_in_export", True),
        ) if bd else None
        latex_fragments = [
            LatexFragmentData(
                x=f["x"], y=f["y"],
                latex_code=f.get("latex_code", ""),
                preamble_path=f.get("preamble_path", ""),
                svg_b64=f.get("svg_b64", ""),
                display_width=f.get("display_width", 200),
                display_height=f.get("display_height", 100),
            )
            for f in data.get("latex_fragments", [])
        ]
        parameters = [
            ParameterData(
                x=pd["x"], y=pd["y"],
                params=[list(pair) for pair in pd.get("params", [])],
                preamble_path=pd.get("preamble_path", ""),
                svg_b64=pd.get("svg_b64", ""),
                display_width=pd.get("display_width", 200),
                display_height=pd.get("display_height", 80),
            )
            for pd in data.get("parameters", [])
        ]
        analysis_items = [
            AnalysisData(
                x=a["x"], y=a["y"],
                source=list(a.get("source", [])),
                detector=[list(d) for d in a.get("detector", [])],
                lgref=list(a.get("lgref", [])),
            )
            for a in data.get("analysis_items", [])
        ]
        shapes = [
            ShapeData(
                kind=s["kind"],
                x=s["x"], y=s["y"],
                rel_points=[tuple(pt) for pt in s.get("rel_points", [])],
                # "color" is the legacy field name — migrate transparently
                stroke_color=s.get("stroke_color", s.get("color", "#000000")),
                fill_color=s.get("fill_color", "#ffffff"),
                fill_style=s.get("fill_style", "none"),
                line_style=s.get("line_style", "solid"),
                line_end_start=s.get("line_end_start", "none"),
                line_end_end=s.get("line_end_end", "none"),
                line_width=float(s.get("line_width", 1.5)),
            )
            for s in data.get("shapes", [])
        ]
        model_defs = [
            ModelData(
                x=m["x"], y=m["y"],
                model_name=m.get("model_name", ""),
                model_type=m.get("model_type", ""),
                simulator=m.get("simulator", "SLiCAP"),
                params=[list(p) for p in m.get("params", [])],
                preamble_path=m.get("preamble_path", ""),
                svg_b64=m.get("svg_b64", ""),
                display_width=m.get("display_width", 200),
                display_height=m.get("display_height", 80),
            )
            for m in data.get("model_defs", [])
        ]
        p = data.get("properties", {})
        properties = DocumentProperties(
            title=p.get("title", ""),
            author=p.get("author", ""),
            created=p.get("created", ""),
            last_modified=p.get("last_modified", ""),
            page_size=p.get("page_size", "A4"),
            page_width_mm=float(p.get("page_width_mm", 210.0)),
            page_height_mm=float(p.get("page_height_mm", 297.0)),
            is_subcircuit=p.get("is_subcircuit", False),
            subcircuit_ports=list(p.get("subcircuit_ports", [])),
            subcircuit_params=[list(pair) for pair in p.get("subcircuit_params", [])],
        )
        return cls(components=components, wires=wires,
                   junctions=junctions, free_texts=free_texts,
                   commands=commands, libs=libs, images=images,
                   border=border, latex_fragments=latex_fragments,
                   parameters=parameters, analysis_items=analysis_items,
                   hyperlinks=hyperlinks, shapes=shapes,
                   model_defs=model_defs, properties=properties)

    def normalize_origin(self, grid_size: int = 5) -> None:
        """Shift all positions so the bounding-rect centre lands on the origin.

        Keeps every item on the grid by snapping the shift to grid_size.
        Called before saving so the file always loads with content near (0,0).
        """
        xs, ys = [], []
        for c in self.components:
            xs.append(c.x); ys.append(c.y)
        for w in self.wires:
            for px, py in w.points:
                xs.append(px); ys.append(py)
        for j in self.junctions:
            xs.append(j.x); ys.append(j.y)
        for item in (*self.free_texts, *self.hyperlinks, *self.commands,
                     *self.libs, *self.images, *self.latex_fragments,
                     *self.parameters, *self.analysis_items, *self.model_defs):
            xs.append(item.x); ys.append(item.y)
        for s in self.shapes:
            xs.append(s.x); ys.append(s.y)
        if self.border is not None:
            xs.append(self.border.x); ys.append(self.border.y)

        if not xs:
            return

        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        dx = round(cx / grid_size) * grid_size
        dy = round(cy / grid_size) * grid_size
        if dx == 0 and dy == 0:
            return

        for c in self.components:
            c.x -= dx; c.y -= dy
        for w in self.wires:
            w.points = [(px - dx, py - dy) for px, py in w.points]
        for j in self.junctions:
            j.x -= dx; j.y -= dy
        for item in (*self.free_texts, *self.hyperlinks, *self.commands,
                     *self.libs, *self.images, *self.latex_fragments,
                     *self.parameters, *self.analysis_items, *self.model_defs):
            item.x -= dx; item.y -= dy
        for s in self.shapes:
            s.x -= dx; s.y -= dy
        if self.border is not None:
            self.border.x -= dx; self.border.y -= dy

    def save(self, path: Path) -> None:
        self.normalize_origin()
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SchematicData:
        return cls.from_json(path.read_text(encoding="utf-8"))
