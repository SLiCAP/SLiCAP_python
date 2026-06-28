#. Bugs, modifications and additions

##. Completed 2026-06-27

### Bugs

1. Net label selection — fixed.

   Net labels are already separate, selectable items, but they are *children* of
   their wire, so their high Z only orders them among siblings — an unrelated
   junction or crossing wire could still win hit-testing. The canvas press
   handler now explicitly prefers a net label under the cursor, and its click
   target is padded (shape()).

   Also introduced a single, centralized per-type stacking order in config.py
   (border < wire < wire-drag < component < junction < net label) so overlapping
   items select deterministically — this removed the old component/junction Z tie.

2. Wiring / rubber-banding connection loss — fixed.

   The actual failing case was *dragging a junction that sits on a component pin*:
   the attached wires follow the junction (JunctionItem._rubber_band_wires) but
   the pin was left behind and silently disconnected. On release the pin is now
   bridged to the junction's new position, so the connection is kept. Connections
   are only removed by deleting the wire segment or the component.

### Modifications

1. Default LaTeX scale for parameter values = 60%
   (config: component_param/latex_scale).

2. SVG symbol metadata schema (the keystone) — implemented as a strict,
   positional, pipe-delimited grammar (not the JSON-like sketch, which could not
   carry capitalized parameter names cleanly):

   - data-model  = "name|show"            (show = 0/1; "?|1" replaces the old
                                            hard-coded ?-reminder logic)
   - data-params = "name|default|show_name|show_value; ..."   (4 fields per entry;
     a not-applicable field is just an extra pipe, e.g. "W||0|0"; positional
     fields are reserved for future use, e.g. unit/min/max)
   - data-description: a literal "\n" becomes a line break in the Place Symbol
     and Properties dialogs.

   Old/bare metadata is rejected with a clear per-symbol error. Both Symbols.svg
   and symbol_extras.svg were migrated; parameter defaults and visibility now come
   from the symbol definition rather than hard-coded rules. A frozen
   <name>.symbols cache in the old format is skipped gracefully (falls back to the
   system library) so existing schematics still open. Added
   Tools -> "Update symbols from library" (drops the frozen cache, reloads every
   symbol from the system library).

3. Attribute order and placement: refdes -> references -> model -> parameters;
   left-aligned, 5 units from the select-box right edge, 10-unit line spacing
   (1 "grid unit" = 1 scene unit; GRID_SIZE = 5).

4. Clicking an attribute shows the dashed leader line to only that attribute
   (selecting the component body still shows them all); driven by an active-label
   key on the component.

5. Double-clicking an attribute opens a single-attribute dialog (value + show
   value / show name) — attribute_dialog.py.

6. Symbol embedded <text> (e.g. +/-, ib, vo, io) stays upright and unmirrored
   under any rotation/flip, on the canvas AND in SVG/PDF export.

   The text is stripped from the artwork at load and redrawn separately, centred
   on its x/y so the rotation/mirror pivots on the glyph centre (no shift). The
   palette icons and Place Symbol preview render through the same path
   (paint_symbol), so canvas, previews and export match exactly. Copy/paste
   re-fetches the full library SVG so embedded text is preserved on the copy.
   Note: x/y are now the glyph *centre* (the tool always centres; Qt's SVG
   renderer had been ignoring dominant-baseline). All <text> y-coordinates were
   batch-shifted up by 0.32 x font-size to restore the previous visual placement.

##. Completed 2026-06-24

1. Properties dialog: the "model" field is a free text input (was a single-item
   drop-down).

2. A "?" placeholder model (the symbol's data-model field) is shown on the canvas
   by default, as a reminder that a .model definition is still required.

3. Parameter values/expressions no longer require curly brackets to be typed. The
   user enters the bare expression; the program adds `{ }` only for the netlist and
   for LaTeX rendering (rendering is the default). Braces are stripped in the
   Properties dialog, and a bare "?" is never braced.

4. File -> Export defaults the save-dialog filename to `<schematic>.cir`,
   `<schematic>.svg` and `<schematic>.pdf` respectively.

5. Tools -> "Load selected symbols from library": replaces the cached definition of
   the selected symbol(s) — and every instance on the canvas — with the most recent
   version from the symbol library. Pin positions may change, so connections may
   break; restoring them is left to the user.

6. IEEE-compatible LaTeX formatting: subscripts that are plain alphanumeric labels
   are set upright (`\mathrm`) rather than italic, applied at the single SLiCAP->LaTeX
   boundary so component value labels and the parameter & model tables are all
   consistent. Manually entered LaTeX fragments are kept user-defined. A bare "?"
   reminder is rendered literally and never sent to the SLiCAP expression parser
   (no more Sympify errors).

7. Netlist generation (GUI export, CLI, and subcircuit creation) aborts with an
   error and writes nothing when an unresolved "?" remains: missing value, missing
   model, missing reference, or missing connection. All problems are reported
   together so the netlist never contains "?".

8. Fixed: on the canvas the gap between a parameter name and its LaTeX-rendered
   value is no longer too large (now at most one non-LaTeX character wide).


#. SLiCAP-NGspice GUI

Design notes / direction for converging the schematic editor into a combined
SLiCAP / NGspice GUI (see also SLiCAP_GUI.md). Two separable problems:

  (A) an NGspice editor = a second "target" (symbols + netlister) on the same
      editor core;
  (B) back-annotation = a target-agnostic placeholder system for values,
      expressions and tiny plots.

(B) is the more reusable piece and is independent of (A): design it once and
feed it from either SLiCAP or NGspice.

##. A. NGspice editor as a "target"

The editor core (canvas, wires, components, labels, selection, SVG/PDF export,
logging) is already target-neutral. Only three things are SLiCAP-specific today:

- Symbol set — hard-wired to files/symbols/slicap/ (window.py _SYMBOLS_SVG/_DIR).
- Netlister — netlist.py emits SLiCAP element syntax.
- Auxiliary items — CommandItem, AnalysisItem, ModelItem, LibraryItem,
  ParameterItem encode SLiCAP / .model / .param syntax.

Proposal:

- Introduce a small Target object (registry entry) holding: symbol directory,
  netlister callable, netlist file extension (.cir vs .sp/.net), and which
  auxiliary dialogs/items are offered.
- Store the chosen target IN the schematic file so a circuit knows what it is.
- Lean on the existing metadata-driven netlisting (data-prefix, data-model,
  data-params, data-refs): an NGspice netlister can be largely metadata-driven
  too, with target-specific element-line formatting
  (e.g. "M1 d g s b model W=.. L=..").

Open question: one schematic for both targets, or target-per-schematic? SLiCAP
uses simplified symbolic models (nullor, behavioral sources); NGspice uses device
.models — different abstraction levels. Recommendation: target-per-schematic,
with a shared generic core (R, L, C, V, I, subcircuits) plus target-specific
symbol sets; the .slicap_sch declares its target and the editor adapts.

##. B. Unified back-annotation (placeholders)

Generalize SLiCAP's backAnnotateSchematic (KiCAD: text-field placeholders keyed
by op-point names like V_out, I_R1, replaced by actual values in the schematic +
SVG/PDF) into a data-bound annotation item — same idea as the existing
LatexFragmentItem / ParameterItem, but the content is RESOLVED from a results
dictionary instead of typed.

Three pieces:

1. Annotation placeholder (new canvas item):
   - key    — canonical result name: V(out), I(R1), gm(M1), or a SLiCAP symbolic
              expression.
   - kind   — value | expression | plot.
   - source — which analysis (op, ac, tran, or a named SLiCAP result).
   - format — sig-digits / units / eng-notation (reuse ENG + the LaTeX pipeline).
   - Unbound -> shows the key as a stub (V(out)=?, or a dashed box for a plot).
     Bound -> shows the value/expression (LaTeX) or a tiny plot.

2. Results model — ONE canonical naming scheme both providers map onto. SLiCAP
   already uses V_<net>, I_<refdes>; NGspice .op gives v(net), i(vsrc),
   @m1[gm]. Define the canonical names once; write two thin adapters
   (SLiCAP results -> dict, NGspice raw/.op -> dict). The placeholder + engine
   never know which simulator produced the numbers.

3. Back-annotation engine (target-agnostic): run analysis -> results dict ->
   for each placeholder look up key, format, render. Used both live in the GUI
   and at export (values baked into SVG/PDF, like KiCAD back-annotation).

Content kinds:

- Values — start here; trivial reuse of ENG + the property-label renderer; bind
  by net/device name.
- Expressions — a SymPy/LaTeX expression over result symbols; already rendered
  via latex_label. Where SLiCAP shines (symbolic transfer/noise next to the
  circuit).
- Tiny plots (sparklines) — bind to a trace (AC mag vs f, v(out) vs t); render
  to SVG and place like a LatexFragmentItem. Choice: matplotlib->SVG
  (full-featured, heavier) vs a QPainter sparkline (light, fast, fewer deps).
  Likely: QPainter sparklines for inline annotation + a matplotlib "full plot"
  item for detailed views.

##. Key decisions to pin down

- Binding stability: bind placeholders by stable NAME (net/refdes), never by
  position, so they survive re-netlisting and edits.
- Canonical naming both simulators map onto — the linchpin; get it right early.
- Authoring UX: type the key, or pick from an auto-populated net/device list, or
  drop a probe on a wire/pin (KiCAD-style; reuses the net-label work).
- Live vs baked: support both (live overlay in the GUI; baked into export).
- Results storage: a per-schematic results sidecar (fits the existing <name>.*
  sidecar pattern) so annotations persist and export is reproducible.

##. Suggested incremental path

1. Target abstraction -> NGspice symbol set + netlister -> NGspice .sp export
   (editor unchanged).
2. Run NGspice from the GUI (-b, .op/.ac/.tran) -> results dict (NGspice panel).
3. Value placeholders (op point), reusing ENG + label rendering, bound by
   net/device name — the minimal, highest-value slice.
4. Expression placeholders, then sparkline plots.
5. Wire the SLiCAP results adapter into the same engine so symbolic results
   annotate too.

Reusable win: one placeholder item + one annotation engine + two result adapters
serves both SLiCAP and NGspice, and reuses the LaTeX pipeline, the ENG fix, the
sidecar pattern, and the SVG/PDF exporter.

References:
- https://www.slicap.org/userguide/ngspice
- https://www.slicap.org/userguide/schematiccapture.html
- SLiCAP backAnnotateSchematic (KiCAD operating-point annotation)
