"""
Annotation drawing shapes: line (polyline), rectangle, ellipse, polygon.

One model for all four kinds (Anton, 2026-09-27): a points list, a stroke
(with style "none": a filled shape without contour), a fill, a rotation angle
about the shape's centre, and for lines two line ends whose arrow head is a
filled polygon without contour of a given width and length (defaults as the
current-source arrow of the symbol library: 4 wide, 6 long).

Legacy kinds are migrated in __init__: "arrow" (a line with an arrow end) and
"circle" (centre + radius vector) which becomes an ellipse defined by the two
corners of its bounding rectangle. Scaling is NOT a separate attribute: the
points define the size, dragging them scales; rotation is the one attribute
that the points cannot express (considered and REJECTED as scale_x/scale_y,
2026-09-27: it would encode the geometry twice).

Three kinds added 2026-10-06 for the figures of the book: "arc", a part
of the ellipse of two corners between a start and a sweep angle, with line
ends; "curve", a spline through the clicked points (open with line ends, or
closed with a fill), the hand-drawn curve; "func", sampled data of an
expression or of a trace of the Design data, mapped into the box of two
corners. All three are drawn, hit-tested and exported as the polyline of
their sampled points (stroke_points), so the line machinery serves them.
An SVG elliptical arc and cubic Bezier output were considered and REJECTED
for now: one path through one code path, and 64 samples per arc and 16 per
spline segment are not distinguishable from the exact curve in print.

All coordinates are in item-local space (relative to pos()).
pos() is the anchor: first point for line and polygon, first corner for rect
and ellipse.
"""
import math

from PySide6.QtWidgets import QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QBrush, QPolygonF

from .config import (snap, snap_pos, snap_fine, shift_held, display_color,
                     LINE_STYLES as _LINE_STYLES)

_SEL_COLOR = QColor(0, 120, 215)

KINDS_WITH_FILL = ("rect", "ellipse", "polygon", "curve")   # a curve: when closed
KINDS_WITH_ENDS = ("line", "arc", "curve", "func")
KINDS_SAMPLED   = ("arc", "curve", "func")      # drawn as their sampled polyline
BOX_KINDS       = ("rect", "ellipse", "arc", "func")   # two corners define them
DEFAULT_HEAD_WIDTH  = 4.0
DEFAULT_HEAD_LENGTH = 6.0
ARC_SAMPLES     = 64
SPLINE_SAMPLES  = 16            # per segment


def spline_through(points, closed: bool = False, per_segment: int = SPLINE_SAMPLES) -> list:
    """A Catmull-Rom spline through *points* (QPointF), sampled: the curve
    passes through every clicked point, which is what a hand-drawn curve
    means (a Bezier with control handles was considered and REJECTED for
    that reason, 2026-10-06). Open: the ends are clamped; closed: cyclic."""
    pts = [QPointF(p) for p in points]
    n = len(pts)
    if n < 2:
        return pts
    if n == 2 and not closed:
        return pts
    def P(i):
        if closed:
            return pts[i % n]
        return pts[min(max(i, 0), n - 1)]
    out = []
    segments = n if closed else n - 1
    for i in range(segments):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        for k in range(per_segment):
            t = k / per_segment
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1.x()) + (-p0.x() + p2.x()) * t
                       + (2 * p0.x() - 5 * p1.x() + 4 * p2.x() - p3.x()) * t2
                       + (-p0.x() + 3 * p1.x() - 3 * p2.x() + p3.x()) * t3)
            y = 0.5 * ((2 * p1.y()) + (-p0.y() + p2.y()) * t
                       + (2 * p0.y() - 5 * p1.y() + 4 * p2.y() - p3.y()) * t2
                       + (-p0.y() + 3 * p1.y() - 3 * p2.y() + p3.y()) * t3)
            out.append(QPointF(x, y))
    out.append(QPointF(pts[0]) if closed else QPointF(pts[-1]))
    return out


def arc_points(rect: QRectF, start_deg: float, sweep_deg: float,
               samples: int = ARC_SAMPLES) -> list:
    """The sampled arc of the ellipse in *rect*, from the parametric angle
    *start_deg* over *sweep_deg* (degrees; y down, so a positive sweep
    turns clockwise on the canvas)."""
    c = rect.center()
    rx, ry = rect.width() / 2, rect.height() / 2
    out = []
    n = max(2, int(samples * max(abs(sweep_deg), 1) / 360) + 1)
    for k in range(n + 1):
        a = math.radians(start_deg + sweep_deg * k / n)
        out.append(QPointF(c.x() + rx * math.cos(a), c.y() + ry * math.sin(a)))
    return out


def _nums(seq) -> list:
    """Range limits as floats; SLiCAP notation ("100k") is accepted."""
    from SLiCAP.SLiCAPmath import _checkNumber
    out = []
    for v in seq:
        try:
            out.append(float(_checkNumber(v)))
        except Exception:
            out.append(float(v))
    return out


def map_into_box(data, rect: QRectF, x_range, y_range, x_log: bool,
                 flip_x: bool = False) -> list:
    """The data points ``[[x, y], ...]`` mapped into *rect*: x over
    *x_range* (logarithmic when *x_log*), y over *y_range*, y UP. An empty
    range is taken from the data. *flip_x* draws x from right to left: the
    mirrored graph (the M key)."""
    if not data:
        return []
    xs = [p[0] for p in data]; ys = [p[1] for p in data]
    if x_log:
        pos = [(x, y) for x, y in zip(xs, ys) if x > 0]
        if not pos:
            return []
        xs = [math.log10(x) for x, _ in pos]; ys = [y for _, y in pos]
        xr = [math.log10(v) for v in x_range] if (x_range and len(x_range) == 2
                                                  and x_range[0] > 0 and x_range[1] > 0) else [min(xs), max(xs)]
    else:
        xr = list(x_range) if (x_range and len(x_range) == 2) else [min(xs), max(xs)]
    yr = list(y_range) if (y_range and len(y_range) == 2) else [min(ys), max(ys)]
    dx = (xr[1] - xr[0]) or 1.0
    dy = (yr[1] - yr[0]) or 1.0
    out = []
    for x, y in zip(xs, ys):
        fx = (x - xr[0]) / dx
        if flip_x:
            fx = 1.0 - fx
        fy = (y - yr[0]) / dy
        out.append(QPointF(rect.left() + fx * rect.width(),
                           rect.bottom() - fy * rect.height()))
    return out


class ShapeItem(QGraphicsItem):

    def __init__(self, kind: str,
                 rel_points: list,
                 stroke_color:   str   = "#000000",
                 fill_color:     str   = "#ffffff",
                 fill_style:     str   = "none",    # "none" | "solid"
                 line_style:     str   = "solid",   # "none"|"solid"|"dashed"|"dotted"|"dash-dot"
                 line_end_start: str   = "none",    # "none"|"arrow"|"dot"|"diamond"
                 line_end_end:   str   = "none",
                 line_width:     float = 1.5,
                 pos: QPointF = QPointF(0, 0),
                 rotation:    float = 0.0,          # degrees about the centre
                 head_width:  float = DEFAULT_HEAD_WIDTH,
                 head_length: float = DEFAULT_HEAD_LENGTH,
                 arc_start: float = 0.0, arc_sweep: float = 270.0,
                 closed: bool = False,
                 expression: str = "", var: str = "x", x_range=None,
                 y_range=None, x_log: bool = False, num: int = 200,
                 trace_var: str = "", trace_label: str = "", data=None,
                 flip_x: bool = False):
        super().__init__()
        rel_points = [QPointF(p) for p in rel_points]
        self.flip_x      = bool(flip_x)     # func: the graph mirrored (M)
        # arc
        self.arc_start   = float(arc_start)
        self.arc_sweep   = float(arc_sweep)
        # curve
        self.closed      = bool(closed)
        # func: the source and the sampled data as drawn
        self.expression  = expression or ""
        self.var         = var or "x"
        self.x_range     = _nums(x_range) if x_range else [0.0, 1.0]
        self.y_range     = _nums(y_range) if y_range else []
        self.x_log       = bool(x_log)
        self.num         = int(num or 200)
        self.trace_var   = trace_var or ""
        self.trace_label = trace_label or ""
        self.data        = [list(p) for p in (data or [])]

        # Migrate legacy kinds
        if kind == "arrow":
            kind = "line"
            line_end_end = "arrow"
        if kind == "circle" and len(rel_points) >= 2:
            r = math.hypot(rel_points[1].x(), rel_points[1].y())
            rel_points = [QPointF(-r, -r), QPointF(r, r)]
            kind = "ellipse"

        self.kind            = kind
        self.rel_points      = rel_points
        self.stroke_color    = stroke_color
        self.fill_color      = fill_color
        self.fill_style      = fill_style
        self.line_style      = line_style
        self.line_end_start  = line_end_start
        self.line_end_end    = line_end_end
        self.line_width      = line_width
        self.head_width      = head_width
        self.head_length     = head_length
        self.rotation        = rotation
        self.setPos(pos)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._anchoring = False
        self.apply_rotation()
        self.anchor_to_first_point()

    # ── geometry ──────────────────────────────────────────────────────────────

    def anchor_to_first_point(self) -> None:
        """Keep the invariant that pos() IS the shape's first point (the
        anchor of the drawing, the point the paste holds under the cursor,
        the sort key of the clipboard). Vertex drags, R and M change the
        points and leave pos() behind, so this is called after each of them
        and on construction (files written before it). The drawing does not
        move: the shift of pos() is taken out of the points, and a rotation
        about the centre is unaffected (Anton, 2026-09-30: a pasted arrow
        hung far from the cursor)."""
        if not self.rel_points:
            return
        d = QPointF(self.rel_points[0])
        if d.isNull():
            return
        self.prepareGeometryChange()
        self.rel_points = [QPointF(p.x() - d.x(), p.y() - d.y()) for p in self.rel_points]
        self._anchoring = True          # no snapping: the drawing must not move
        try:
            self.setPos(self.pos() + d)
        finally:
            self._anchoring = False
        self.apply_rotation()

    def _content_rect(self) -> QRectF:
        pts = self.rel_points
        if not pts:
            return QRectF()
        if self.kind in ("line", "polygon", "curve"):
            xs = [p.x() for p in pts]; ys = [p.y() for p in pts]
            return QRectF(min(xs), min(ys),
                          max(xs) - min(xs), max(ys) - min(ys))
        if self.kind in BOX_KINDS and len(pts) >= 2:
            x0, y0 = pts[0].x(), pts[0].y()
            x1, y1 = pts[1].x(), pts[1].y()
            return QRectF(min(x0, x1), min(y0, y1),
                          abs(x1 - x0), abs(y1 - y0))
        return QRectF()

    def centre(self) -> QPointF:
        return self._content_rect().center()

    def apply_rotation(self) -> None:
        """Rotate the item about the centre of its content (call after the
        rotation or the points changed)."""
        self.prepareGeometryChange()
        self.setTransformOriginPoint(self.centre())
        self.setRotation(self.rotation)

    # The R and M keys act on the POINTS, about the centre of the shape, so
    # that the result is what is saved, undone and exported; the rotation
    # attribute stays the free angle of the dialog (Anton, 2026-09-30: R and
    # M did nothing lasting on a drawn line).

    def rotate_quarter(self) -> None:
        """Turn the shape by 90 degrees clockwise about its centre."""
        if self.kind == "func":
            # the box is a frame for the mapping, not the drawing itself:
            # turning its corners would only re-map the graph upright into
            # a turned box (Anton, 2026-10-06). The graph turns as a whole,
            # through the rotation, which the file and the export carry.
            self.rotation = (self.rotation + 90.0) % 360.0
            self.apply_rotation()
            self.update()
            return
        c = self.centre()
        self.prepareGeometryChange()
        self.rel_points = [QPointF(c.x() - (p.y() - c.y()), c.y() + (p.x() - c.x()))
                           for p in self.rel_points]
        if self.kind == "arc":
            self.arc_start += 90.0       # the box turned: same parametric point
        self.anchor_to_first_point()
        self.update()

    def mirror(self) -> None:
        """Mirror the shape about the vertical axis through its centre. A
        rotated shape keeps its look mirrored: the angle changes sign."""
        c = self.centre()
        self.prepareGeometryChange()
        self.rel_points = [QPointF(2 * c.x() - p.x(), p.y()) for p in self.rel_points]
        self.rotation = -self.rotation
        if self.kind == "arc":
            self.arc_start = 180.0 - self.arc_start
            self.arc_sweep = -self.arc_sweep
        if self.kind == "func":
            self.flip_x = not self.flip_x    # the graph itself is mirrored
        self.anchor_to_first_point()
        self.update()

    # ── the sampled geometry of arc, curve and func ─────────────────────────

    def stroke_points(self) -> list:
        """The polyline the item strokes, in local coordinates: the points
        of a line, the samples of an arc, a spline or a function curve."""
        pts = self.rel_points
        if self.kind == "arc" and len(pts) >= 2:
            return arc_points(self._content_rect(), self.arc_start, self.arc_sweep)
        if self.kind == "curve" and len(pts) >= 2:
            return spline_through(pts, self.closed)
        if self.kind == "func" and len(pts) >= 2:
            return map_into_box(self.data, self._content_rect(),
                                self.x_range, self.y_range, self.x_log, self.flip_x)
        return list(pts)

    def has_ends(self) -> bool:
        return (self.kind in KINDS_WITH_ENDS and not (self.kind == "curve" and self.closed)
                and (self.line_end_start != "none" or self.line_end_end != "none"))

    def is_filled(self) -> bool:
        return (self.fill_style == "solid" and self.kind in KINDS_WITH_FILL
                and (self.kind != "curve" or self.closed))

    def resample(self, n_points: int | None = None) -> None:
        """A func item samples its source: the expression through the core
        (sampleExpr), a trace from the Design data (the manifest's
        decimated copy), then keeps as many points as its box can resolve:
        two per scene unit of width (Anton, 2026-10-06: "as large as
        required but not larger"). Without a source or a readable Design
        data entry the stored data stays."""
        if self.kind != "func":
            return
        from .design_data import subsample
        pts = None
        if self.trace_var:
            from . import project
            from .design_data import manifest_traces
            for var, label, data in manifest_traces(project.project_root()):
                if var == self.trace_var and label == self.trace_label:
                    pts = [list(p) for p in data]
                    break
        elif self.expression:
            try:
                from SLiCAP.SLiCAPmath import sampleExpr
                x0, x1 = (self.x_range + [0.0, 1.0])[:2]
                x, y = sampleExpr(self.expression, self.var, x0, x1, self.num, self.x_log)
                pts = [[float(a), float(b)] for a, b in zip(x, y)]
            except Exception as exc:
                print("Function curve: {0}".format(exc))
                pts = None
        if pts is None:
            return
        width = self._content_rect().width() if len(self.rel_points) >= 2 else 0.0
        n = n_points if n_points is not None else max(8, int(2 * width))
        self.prepareGeometryChange()
        self.data = subsample(pts, n)
        self.update()

    def arc_end_points(self) -> list:
        """The two points of the arc's ends on the ellipse (the angle
        handles)."""
        r = self._content_rect()
        c = r.center()
        rx, ry = r.width() / 2, r.height() / 2
        out = []
        for deg in (self.arc_start, self.arc_start + self.arc_sweep):
            a = math.radians(deg)
            out.append(QPointF(c.x() + rx * math.cos(a), c.y() + ry * math.sin(a)))
        return out

    def _angle_of(self, local: QPointF) -> float:
        """The parametric angle (degrees) of the ellipse point nearest to the
        direction of *local* from the centre."""
        r = self._content_rect()
        c = r.center()
        rx, ry = max(r.width() / 2, 1e-6), max(r.height() / 2, 1e-6)
        return math.degrees(math.atan2((local.y() - c.y()) / ry, (local.x() - c.x()) / rx))

    def select_rect(self) -> QRectF:
        """The extent the rubber band tests (canvas._rb_keep_item): the
        geometry plus the stroke and, for a line with heads, the head. A
        generous padding made a small head impossible to enclose (Anton,
        2026-09-27)."""
        m = (self.line_width / 2 if self.line_style != "none" else 0.0) + 0.5
        if self.has_ends():
            m += max(self.head_length, self.head_width) / 2
        rect = self._content_rect()
        if self.kind == "curve":          # a spline overshoots its points
            sp = self.stroke_points()
            if sp:
                xs = [p.x() for p in sp]; ys = [p.y() for p in sp]
                rect = rect.united(QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))
        return rect.adjusted(-m, -m, m, m)

    def boundingRect(self) -> QRectF:
        m = self.HANDLE + 1.0          # room for the selection dots and cross
        return self.select_rect().adjusted(-m, -m, m, m)

    def _outline(self) -> QPainterPath:
        """The drawn geometry as a path (open polyline for a line)."""
        pts, path = self.rel_points, QPainterPath()
        if self.kind in KINDS_SAMPLED:
            sp = self.stroke_points()
            if len(sp) >= 2:
                path.moveTo(sp[0])
                for q in sp[1:]:
                    path.lineTo(q)
                if self.kind == "curve" and self.closed:
                    path.closeSubpath()
        elif self.kind == "line" and len(pts) >= 2:
            path.moveTo(pts[0])
            for q in pts[1:]:
                path.lineTo(q)
        elif self.kind == "polygon" and len(pts) >= 3:
            path.addPolygon(QPolygonF(pts)); path.closeSubpath()
        elif self.kind == "rect" and len(pts) == 2:
            path.addRect(self._content_rect())
        elif self.kind == "ellipse" and len(pts) == 2:
            path.addEllipse(self._content_rect())
        return path

    def shape(self) -> QPainterPath:
        """Hit area = the geometry: a band along the stroke, plus the area of
        a filled shape, plus the handles when selected. The padded bounding
        box used before made a polyline win clicks on its neighbours
        (Anton, 2026-09-27)."""
        from PySide6.QtGui import QPainterPathStroker
        outline = self._outline()
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.line_width, 1.0) + 4.0)
        hit = stroker.createStroke(outline)
        if self.is_filled():
            hit = hit.united(outline)
        if self.isSelected():
            h = self.HANDLE_HIT
            for q in self._handles():
                hit.addRect(QRectF(q.x() - h, q.y() - h, 2 * h, 2 * h))
        # winding, not even-odd: a handle square overlapping the stroke band
        # must not cancel it (the vertex itself was then outside, 2026-09-27)
        hit.setFillRule(Qt.WindingFill)
        return hit

    def hit_exact(self, local: QPointF) -> bool:
        """True when the point lies on the drawn geometry itself: on the
        stroke (its real width, at least 1 unit) or inside a filled shape.
        The tolerance band of shape() is for convenience only."""
        from PySide6.QtGui import QPainterPathStroker
        outline = self._outline()
        if self.is_filled() and outline.contains(local):
            return True
        if self.line_style == "none":
            return False
        stroker = QPainterPathStroker(); stroker.setWidth(max(self.line_width, 1.0) + 0.6)
        return stroker.createStroke(outline).contains(local)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if getattr(self, "_anchoring", False):
                return value            # anchor_to_first_point: exact
            ref = getattr(self, "_snap_ref", None)
            if ref is not None:
                # snap the vertex nearest to the grab point, not the anchor
                fn = snap_fine if shift_held() else snap
                return fn(QPointF(value.x() + ref.x(), value.y() + ref.y())) - ref
            return snap_pos(self, value)
        return super().itemChange(change, value)

    # ── vertex editing (handles on the selected shape) ──────────────────────

    HANDLE = 2.5          # painting margin for the selection marks
    HANDLE_HIT = 1.8      # a press within this distance of a vertex dot is a
                          # vertex press; larger, and a press inside a small
                          # polygon reshaped it instead of moving it (2026-09-27)

    def _handles(self) -> list:
        """Editable points in local coordinates: the points of a line,
        polygon or curve, the two corners of a rect, ellipse, arc or function
        box, and for an arc its two end points (dragging one sets the
        angle)."""
        if self.kind == "arc" and len(self.rel_points) >= 2:
            return list(self.rel_points) + self.arc_end_points()
        return list(self.rel_points)

    def _handle_at(self, local: QPointF):
        tol = self.HANDLE_HIT
        for i, p in enumerate(self._handles()):
            if abs(p.x() - local.x()) <= tol and abs(p.y() - local.y()) <= tol:
                return i
        return None

    def mousePressEvent(self, event):
        self._vertex = None
        self._snap_ref = None
        if self.isSelected() and event.button() == Qt.LeftButton:
            i = self._handle_at(event.pos())
            if i is not None:
                sc = self.scene()
                if sc is not None and hasattr(sc, "_push_undo"):
                    sc._push_undo()
                self._vertex = i
                event.accept()
                return
        if event.button() == Qt.LeftButton:
            sc = self.scene()
            others = [o for o in (sc.items(event.scenePos()) if sc is not None else [])
                      if o is not self and isinstance(o, ShapeItem)]
            # A vertex handle of a SELECTED shape wins every press: a handle
            # of the arrow head under the band of the emitter line must
            # reshape the head, not grab the line (Anton, 2026-09-27).
            if any(o.isSelected() and o._handle_at(o.mapFromScene(event.scenePos())) is not None for o in others):
                event.ignore()
                return
            if not self.hit_exact(event.pos()):
                # Only the tolerance band was hit: if another shape under the
                # cursor is hit on its real geometry, let the press pass on to
                # it (Qt hands an ignored press to the next item below).
                if any(o.hit_exact(o.mapFromScene(event.scenePos())) for o in others):
                    event.ignore()
                    return
        if event.button() == Qt.LeftButton and self.rel_points:
            # the vertex nearest to the grab point is the snap reference of the move
            p = event.pos()
            self._snap_ref = QPointF(min(self.rel_points, key=lambda q: (q.x() - p.x()) ** 2 + (q.y() - p.y()) ** 2))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_vertex", None) is not None:
            p = event.pos()
            fn = snap_fine if shift_held() else snap
            p = self.mapFromScene(fn(self.mapToScene(p)))
            self.prepareGeometryChange()
            if self.kind == "arc" and self._vertex >= len(self.rel_points):
                # an end handle of the arc: the angle, not a point (free, not
                # snapped: the ellipse decides where the end lies)
                angle = self._angle_of(event.pos())
                if self._vertex == len(self.rel_points):
                    end = self.arc_start + self.arc_sweep
                    self.arc_start = angle
                    raw = end - angle
                else:
                    raw = angle - self.arc_start
                # The handle gives an angle in (-180, 180]; the sweep it
                # implies is ambiguous by 360 degrees. Take the candidate
                # nearest to the sweep so far, so a drag runs on through
                # 180 degrees up to a full turn instead of flipping to the
                # short way round (Anton, 2026-10-06: "cannot be made
                # larger than 0.5, after that it flips").
                prev = self.arc_sweep
                self.arc_sweep = min((raw, raw + 360.0, raw - 360.0),
                                     key=lambda c: abs(c - prev))
                self.arc_sweep = max(-359.9, min(359.9, self.arc_sweep))
            else:
                self.rel_points[self._vertex] = QPointF(p)
                if self.kind == "func":
                    self.resample()
            self.apply_rotation()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._snap_ref = None
        if getattr(self, "_vertex", None) is not None:
            self._vertex = None
            self.anchor_to_first_point()
            sc = self.scene()
            if sc is not None and hasattr(sc, "data_changed"):
                sc.data_changed.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── paint ─────────────────────────────────────────────────────────────────

    def _pen(self) -> QPen:
        if self.line_style == "none":
            return QPen(Qt.NoPen)
        pen = QPen(display_color(self.stroke_color), self.line_width)
        pen.setStyle(_LINE_STYLES.get(self.line_style, Qt.SolidLine))
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        return pen

    def paint(self, painter: QPainter, option, widget=None) -> None:
        selected = bool(option.state & QStyle.State_Selected)
        pen = self._pen()
        if selected:
            # a selected shape shows itself in the selection colour; no box
            # around it, a hollow square on every handle, a cross on the
            # active point. Filled squares were REJECTED (2026-09-27: they
            # covered the line ends); the dots that replaced them were too
            # small to find, the user did not know where to drag (Anton,
            # 2026-10-06). The hollow square is the size of the hit zone.
            pen = QPen(pen); pen.setColor(_SEL_COLOR)
            if pen.style() == Qt.NoPen:
                pen = QPen(_SEL_COLOR, 0.6)
        painter.setPen(pen)
        if self.is_filled():
            painter.setBrush(QBrush(display_color(self.fill_color)))
        else:
            painter.setBrush(Qt.NoBrush)

        pts = self.rel_points
        kind = self.kind

        if kind in ("line",) + KINDS_SAMPLED:
            sp = self.stroke_points() if kind in KINDS_SAMPLED else pts
            if kind == "curve" and self.closed and len(sp) >= 3:
                painter.drawPolygon(QPolygonF(sp))
            elif len(sp) >= 2:
                shaft = shaft_points(sp, self.line_end_start, self.line_end_end,
                                     self.head_length)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(QPolygonF(shaft))
                color = display_color(self.stroke_color)   # heads and dots as the stroke
                _draw_end(painter, head_base(sp, self.head_length, False), sp[0],
                          self.line_end_start, self.head_width, self.head_length, color)
                _draw_end(painter, head_base(sp, self.head_length, True), sp[-1],
                          self.line_end_end, self.head_width, self.head_length, color)
            elif kind == "func":
                # no data yet: the box, dashed, so the item can be found
                box_pen = QPen(_SEL_COLOR if selected else QColor(150, 150, 150), 0.5, Qt.DashLine)
                painter.setPen(box_pen); painter.setBrush(Qt.NoBrush)
                painter.drawRect(self._content_rect())

        elif kind == "rect" and len(pts) == 2:
            painter.drawRect(self._content_rect())

        elif kind == "ellipse" and len(pts) == 2:
            painter.drawEllipse(self._content_rect())

        elif kind == "polygon" and len(pts) >= 3:
            painter.drawPolygon(QPolygonF(pts))

        if selected:
            painter.setRenderHint(QPainter.Antialiasing)
            active = None
            if getattr(self, "_vertex", None) is not None:
                active = self._handles()[self._vertex]
            elif getattr(self, "_snap_ref", None) is not None:
                active = self._snap_ref
            painter.setPen(QPen(QColor(30, 30, 30), 0.4))
            painter.setBrush(Qt.NoBrush)
            h = self.HANDLE_HIT
            for p in self._handles():          # handles: drag one to reshape
                painter.drawRect(QRectF(p.x() - h, p.y() - h, 2 * h, 2 * h))
            if active is not None:             # the active point: a dark cross
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.drawLine(QPointF(active.x() - 2.5, active.y()), QPointF(active.x() + 2.5, active.y()))
                painter.drawLine(QPointF(active.x(), active.y() - 2.5), QPointF(active.x(), active.y() + 2.5))


# ── line-end helpers (shared with the SVG export) ───────────────────────────

def _unit(p_from, p_to):
    dx, dy = p_to.x() - p_from.x(), p_to.y() - p_from.y()
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    return dx / length, dy / length


def head_polygon(p_from: QPointF, p_to: QPointF, style: str,
                 head_width: float, head_length: float):
    """Points of the filled head at p_to (pointing away from p_from), or None:
    "arrow" a triangle of the given width and length, "diamond" a rhombus of
    the given width and length. "dot" is a circle, see head_dot."""
    u = _unit(p_from, p_to)
    if u is None or style not in ("arrow", "diamond"):
        return None
    ux, uy = u
    px_, py_ = -uy, ux
    w = head_width / 2
    if style == "arrow":
        base = QPointF(p_to.x() - head_length * ux, p_to.y() - head_length * uy)
        return [p_to,
                QPointF(base.x() + w * px_, base.y() + w * py_),
                QPointF(base.x() - w * px_, base.y() - w * py_)]
    back = QPointF(p_to.x() - head_length * ux, p_to.y() - head_length * uy)
    mid  = QPointF(p_to.x() - head_length / 2 * ux, p_to.y() - head_length / 2 * uy)
    return [p_to,
            QPointF(mid.x() + w * px_, mid.y() + w * py_),
            back,
            QPointF(mid.x() - w * px_, mid.y() - w * py_)]


def trim_polyline(pts, dist: float, at_end: bool):
    """The polyline *pts* shortened by *dist* of arc length at its end (or
    its start): whole segments shorter than the remaining distance are
    dropped, the last one cut at the exact length. A sampled arc or curve
    has segments much shorter than an arrow head; cutting only the last
    segment back by the head length folded the shaft over itself and let
    the round cap poke out beside the head ("dirty arrows", Anton,
    2026-10-06). Returns a list with at least two points."""
    seq = [QPointF(p) for p in (pts if at_end else reversed(pts))]
    remaining = float(dist)
    while len(seq) >= 2 and remaining > 0:
        a, b = seq[-2], seq[-1]
        seg = math.hypot(b.x() - a.x(), b.y() - a.y())
        if seg <= remaining:
            seq.pop()
            remaining -= seg
        else:
            t = (seg - remaining) / seg
            seq[-1] = QPointF(a.x() + t * (b.x() - a.x()), a.y() + t * (b.y() - a.y()))
            remaining = 0
    if len(seq) < 2:                     # shorter than the head: a point at the base
        seq = [QPointF(seq[0]), QPointF(seq[0])] if seq else [QPointF(pts[0]), QPointF(pts[0])]
    return seq if at_end else list(reversed(seq))


def head_base(pts, head_length: float, at_end: bool) -> QPointF:
    """The point *head_length* back along the polyline from its tip: the
    base of the head, which also gives the head its direction (the chord
    over the head length, a smooth tangent on a sampled curve)."""
    trimmed = trim_polyline(pts, head_length, at_end)
    return trimmed[-1] if at_end else trimmed[0]


def shaft_points(pts, end_start: str, end_end: str, head_length: float):
    """The polyline to stroke: shortened by the head length, along the
    curve, at an arrow or diamond end, so that the stroke ends at the base
    of the head and the round line cap does not show beyond the tip."""
    shaft = [QPointF(p) for p in pts]
    if end_end in ("arrow", "diamond"):
        shaft = trim_polyline(shaft, head_length, at_end=True)
    if end_start in ("arrow", "diamond"):
        shaft = trim_polyline(shaft, head_length, at_end=False)
    return shaft


def _draw_end(painter: QPainter, p_from: QPointF, p_to: QPointF, style: str,
              head_width: float, head_length: float, color: QColor) -> None:
    """Filled head without contour: arrow and diamond as polygons, dot as a
    circle of the head width."""
    if style == "none":
        return
    saved_pen, saved_brush = painter.pen(), painter.brush()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color))
    if style == "dot":
        r = head_width / 2
        painter.drawEllipse(p_to, r, r)
    else:
        poly = head_polygon(p_from, p_to, style, head_width, head_length)
        if poly:
            painter.drawPolygon(QPolygonF(poly))
    painter.setPen(saved_pen)
    painter.setBrush(saved_brush)
