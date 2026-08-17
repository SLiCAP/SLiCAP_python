.. _design:

Program Design
==============

This section describes the internal structure of the SLiCAP Schematic Capture
program — which module is responsible for what, how the layers relate to each
other, and what data each layer owns.  It is written for contributors and for
users who want to understand the reasoning behind the architecture.

Overview
--------

The program is built in Python on top of **PySide6** (Qt for Python).
It follows a classic model–view split:

* A :ref:`data model <design-data-model>` (plain Python dataclasses,
  serialised as JSON) is the sole definition of a schematic on disk.
* A :ref:`scene / canvas <design-scene>` (a ``QGraphicsScene`` populated with
  ``QGraphicsItem`` subclasses) is the live, interactive view of that model.
* :ref:`Export pipelines <design-export>` read the scene directly and produce
  netlist files, SVG images, and PDF/print output without going through an
  intermediate format.

The following diagram shows the main modules and their relationships::

    ┌─────────────────────────────────────────────────────────────────────┐
    │  symbol_library.py  ─── Symbols.svg + user lib/*.svg                │
    │  (SymbolLibrary / Symbol)   reads: SVG <g id>; writes: component_item│
    │                             module dicts + SVG bytes for rendering   │
    └──────────────────────────────┬──────────────────────────────────────┘
                                   │ inject_into_component_item()
    ┌──────────────────────────────▼──────────────────────────────────────┐
    │  component_item.py  ─── module-level metadata dicts                 │
    │  (ComponentItem + helpers)   SYMBOL_PREFIX, PIN_POSITIONS, …        │
    └──────────────────────────────┬──────────────────────────────────────┘
                                   │ used by
    ┌──────────────────────────────▼──────────────────────────────────────┐
    │  canvas.py  ─── SchematicScene (QGraphicsScene)                     │
    │  + *_item.py                  all scene items live here             │
    │                               interaction modes, undo/redo          │
    └──────────┬────────────────────────────────────────────────┬─────────┘
               │ to_data() / from_data()                        │ items
    ┌──────────▼──────────────────────────────┐   ┌────────────▼─────────┐
    │  schematic_data.py                      │   │  connectivity.py     │
    │  SchematicData  (pure-Python dataclasses│   │  net resolution,     │
    │  + JSON serialisation)                  │   │  union-find, junction│
    │  → .slicap_sch  (JSON on disk)          │   │  detection           │
    └──────────┬──────────────────────────────┘   └──────────────────────┘
               │ save / load
    ┌──────────▼──────────────────────────────┐
    │  project.py  ─── project root, sidecars │
    │  (sch/, cir/, lib/, img/, .cache, .ini) │
    └─────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  export.py / netlist.py  ─── read scene items, write files          │
    │  SVG / PDF / Print  /  SLiCAP .cir netlist                         │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  window.py  ─── MainWindow (QMainWindow) + SchematicView            │
    │  menus, file dialogs, zoom, grid rendering                          │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  config.py / style.ini / <name>.ini  ─── visual constants           │
    │  grid size, colours, fonts, snap()                                  │
    └─────────────────────────────────────────────────────────────────────┘


.. _design-symbol-library:

Layer 1 — Symbol Definitions (``symbol_library.py``)
-----------------------------------------------------

**What it contains:**
All schematic symbol definitions live in one SVG bundle file,
``app/symbols/Symbols.svg``.  Each symbol is a single ``<g id="name">``
element inside the SVG ``<defs>`` block.  User-defined symbols are individual
``*.svg`` files placed in the project's ``lib/`` directory; their ``<g>``
elements are parsed by the same loader and added to (or override) the bundle.

A symbol group carries everything the editor needs as SVG attributes:

.. code-block:: xml

   <g id="R"
      data-prefix="R"
      data-nodes="p n"
      data-model="R"
      data-params="value"
      data-description="Resistor"
      data-info="https://…">
      …artwork…
      <circle cx="0" cy="-20" r="0.5" class="node" data-node="p"/>
      <circle cx="0" cy="20"  r="0.5" class="node" data-node="n"/>
   </g>

Pin positions are read from ``class="node"`` circles whose ``data-node``
attribute matches a name in ``data-nodes``.  The editor never infers pin
positions from artwork geometry; if a name in ``data-nodes`` has no matching
marker the file is rejected with a ``SymbolError``.

**What it does NOT contain:**
Model equations, SPICE parameters, simulation instructions.  The symbol layer
is purely visual + structural metadata.

**Key classes / functions:**

``Symbol``
    Parsed representation of one ``<g>`` definition.  Holds ``name``,
    ``prefix``, ``nodes``, ``pins`` (pin coordinates in ``data-nodes``
    order), ``model``, ``params``, ``refs``, ``description``, ``info``,
    ``select_box`` (computed bounding box with padding), ``svg`` (standalone
    SVG bytes for rendering), and ``g_xml`` (raw XML for frozen-bundle export).

``SymbolLibrary``
    Loads the bundle, then scans individual SVG files.  Provides
    ``svg_bytes(name)`` (bytes for canvas rendering) and
    ``inject_into_component_item()`` (publishes metadata to the scene layer).

**Frozen symbol bundle (``<name>.symbols``):**
When a schematic is saved, ``write_bundle()`` copies the raw ``<g>`` XML of
every symbol the schematic uses into ``<name>.symbols``.  On the next open,
``add_bundle()`` re-loads these frozen definitions and they *override* the
system bundle.  This means a saved schematic always renders with the symbols
it was originally drawn with, even after the system library changes.


.. _design-component-metadata:

Layer 2 — Component Metadata Registry (``component_item.py``)
--------------------------------------------------------------

**What it contains:**
Module-level Python dictionaries that map symbol name → metadata value:

* ``SYMBOL_PREFIX``      — refdes letter (e.g. ``"R"``, ``"M"``)
* ``PIN_POSITIONS``      — list of ``(x, y)`` tuples in ``data-nodes`` order
* ``SYMBOL_TIGHT_RECT``  — ``(x, y, w, h)`` select box
* ``SYMBOL_NODES``       — ordered node name list
* ``SYMBOL_MODEL``       — SLiCAP model identifier
* ``SYMBOL_PARAMS``      — overridable parameter names
* ``SYMBOL_REFS``        — number of ``data-refs`` entries
* ``SYMBOL_DESCRIPTION`` — human-readable description
* ``SYMBOL_INFO``        — help/datasheet URL

These dicts are populated by ``SymbolLibrary.inject_into_component_item()``
and **cleared first**, so they always mirror exactly the current library.
They are the only channel through which the symbol layer talks to the scene
layer; the scene layer never imports ``symbol_library`` directly.

**Why module-level dicts (not instance attributes):**
``ComponentItem`` and ``SchematicScene`` need to look up pin positions during
mouse events, connectivity checks, and undo/redo restoration.  Placing the
data in module-level dicts avoids threading library references through every
call site and keeps the scene items self-contained.


.. _design-data-model:

Layer 3 — Data Model (``schematic_data.py``)
--------------------------------------------

**What it contains:**
``SchematicData`` is a plain-Python dataclass tree that represents the complete,
serialisable state of a schematic.  It contains **no Qt objects and no display
logic**.  Its fields map one-to-one onto the item types in the scene layer:

``DocumentProperties``
    Title, author, creation/modification dates, page size, subcircuit flag,
    subcircuit port order and parameter defaults.

``ComponentData``
    Symbol name, instance ID (refdes), position ``(x, y)``, rotation, flip
    flags, parameter values (as strings), model override, ``refs`` (referenced
    elements), label display/offset settings.

``WireData``
    Ordered list of ``(x, y)`` waypoints defining the polyline, net name,
    whether the name label is shown, label offset, lock flag (set by port
    symbols).

``JunctionData``
    Position of a junction dot.

``FreeTextData``, ``CommandData``, ``LibraryData``, ``HyperlinkData``
    Position and text/URL content.

``ImageData``
    File path and display size.

``LatexFragmentData``, ``ParameterData``
    LaTeX source, preamble path, base64-encoded SVG render, display size.

``AnalysisData``
    SLiCAP ``source``, ``detector``, and ``lgref`` lists.

``ShapeData``
    Kind (line/rect/circle), anchor position, relative waypoints, stroke/fill
    colour, line style, arrow-end markers, line width.

``BorderData``
    Position, size, and whether the border is included in exports.

**Serialisation:**
``SchematicData.to_json()`` / ``from_json()`` round-trip to compact JSON.
The file is normalised before writing: ``normalize_origin()`` shifts all
coordinates so the bounding-box centre lands on the origin (snapped to grid),
keeping the file content stable regardless of where the user positioned the
schematic on the canvas.

The on-disk format is ``*.slicap_sch`` (a JSON text file).  It is the only
persistent representation of a schematic; there is no separate binary format.


.. _design-scene:

Layer 4 — Canvas Scene (``canvas.py`` + ``*_item.py``)
-------------------------------------------------------

**What it contains:**
The live, interactive representation of the schematic.  ``SchematicScene``
subclasses ``QGraphicsScene`` and owns a flat list of ``QGraphicsItem``
subclasses.  Qt's z-order (insertion order / ``setZValue``) determines which
items appear on top; there are no named "layers" in the Qt sense.

The item types divide into two groups:

*Persistent items* (serialised into ``SchematicData`` on save):

``ComponentItem``
    Renders the symbol SVG via ``QSvgRenderer`` inside a ``QGraphicsSvgItem``.
    Hosts child ``QGraphicsSimpleTextItem`` labels for refdes, parameter values,
    and (for subcircuit blocks) pin names.  Carries its own ``params`` dict,
    ``model``, and ``refs``; these are the live values that get written into
    ``ComponentData.params`` / ``model`` / ``refs`` when ``to_data()`` is called.

``WireItem``
    A ``QPainterPath`` representing a single straight axis-aligned segment
    between two grid-snapped endpoints.  Carries the net name, display flag,
    label offset, and lock state.

    Every committed wire in the scene is **exactly two points** (no elbows).
    An L-shaped route drawn by the user is split by ``_split_wire_elbows()``
    into two separate ``WireItem``\s meeting at the corner.  This invariant
    ensures that a single mouse-click selects exactly one straight segment,
    which can then be moved independently.

``JunctionItem``
    A filled circle drawn at T-intersections.  Created and removed automatically
    by ``_sync_junctions()``; the user can also place one manually.

``FreeTextItem``, ``CommandItem``
    Editable ``QGraphicsTextItem`` subclasses.  ``CommandItem`` renders in a
    distinct colour/font to distinguish SLiCAP commands (``.param``, ``.lib``,
    etc.) from free annotation text.

``BorderItem``
    A rectangle marking the schematic page boundary.  Only one border is
    allowed per schematic; placing a second one removes the first.

``LibraryItem``
    Displays a ``.lib`` filename annotation and records the library path for
    netlist export.

``ImageItem``
    Renders an embedded raster or SVG image.  Stores the file path and display
    size; the image is re-loaded from the path on each open.

``LatexFragmentItem``, ``ParameterItem``
    Display a LaTeX-rendered SVG pixmap.  Store the LaTeX source and the
    rendered SVG bytes (base64 in the save file) so the schematic opens
    correctly without re-running ``pdflatex``.

``AnalysisItem``
    Displays the SLiCAP ``source`` / ``detector`` / ``lgref`` specification as
    a text annotation.

``HyperlinkItem``
    A styled text item that opens a URL in the browser on double-click.

``ShapeItem``
    A drawing-primitive item (line, rectangle, circle) with configurable stroke,
    fill, line style, and end markers.

*Transient items* (not saved; discarded when placement ends):

* **Ghost items** — semi-transparent previews of the item being placed,
  tracking the cursor.  Created in each ``start_*_placement()`` call and
  removed when the item is committed or placement is cancelled.
* **Wire preview** — a dashed ``QGraphicsPathItem`` showing the in-progress
  wire routing, updated on every ``mouseMoveEvent`` while in WIRING mode.

**The scene as the single source of truth for the view:**
The canvas does not keep a separate "logical" model alongside the items.  The
dataclass model is generated on demand by ``to_data()``, which walks
``scene.items()`` and serialises each item.  Conversely, ``from_data()`` calls
``reset()`` (clears the scene) and then adds fresh items from the dataclass
tree.  Undo/redo is implemented as a stack of ``SchematicData`` snapshots:
``_push_undo()`` calls ``to_data()`` before a change; ``undo()`` calls
``_restore()`` which calls ``from_data()`` with the saved snapshot.


.. _design-interaction:

Layer 5 — Interaction and Editing Modes (``canvas.py``)
-------------------------------------------------------

``SchematicScene`` uses an explicit finite-state machine to route mouse and
keyboard events:

.. code-block:: none

    NORMAL               ← default; selection, drag, double-click to edit
    PLACING              ← placing a symbol (ghost follows cursor)
    WIRING               ← drawing wires (click adds waypoints)
    PLACING_JUNCTION     ← placing a junction dot
    PLACING_TEXT         ← placing a free-text item
    PLACING_COMMAND      ← placing a command text item
    PLACING_BORDER       ← placing the page border
    PLACING_LIBRARY      ← placing a .lib annotation
    PLACING_IMAGE        ← placing an embedded image
    PLACING_LATEX        ← placing a LaTeX fragment
    PLACING_PARAMETER    ← placing a parameter table
    PLACING_ANALYSIS     ← placing a source/detector/lgref block
    PLACING_HYPERLINK    ← placing a hyperlink
    PASTING              ← moving the clipboard paste ghost to the drop point
    DRAWING_LINE         ← free-draw polyline
    DRAWING_RECT         ← free-draw rectangle
    DRAWING_CIRCLE       ← free-draw circle

Every ``mousePressEvent``, ``mouseMoveEvent``, and ``mouseReleaseEvent``
dispatches on ``self._mode`` first, so each mode has a clean, isolated code
path.  The ``Escape`` key always returns to ``NORMAL`` by calling
``_cancel_placement()`` or ``_end_wire(commit=False)``.

**Wire selection:**
Because every committed wire is a single straight 2-point segment, a click
selects exactly one segment.  Rubber-band selection (left-to-right or
right-to-left) selects multiple segments just like components.

**Wire drag sub-modes (within NORMAL):**
When the user presses on a selected wire, the scene checks whether the cursor
is within ``_HIT_TOL`` of a vertex (endpoint).

* **Vertex drag** — ``_vdrag_wire`` / ``_vdrag_idx`` track the wire and which
  endpoint is moving.  The opposite endpoint stays fixed; one rubber-band wire
  tracks each adjacent connection.
* **Body drag** — the whole segment (and any rubber-band wires tracking its
  endpoints) moves rigidly.  A body drag is only triggered when the cursor is
  closer to the wire interior than to either vertex.

On mouse release both paths call ``_sync_junctions()`` (which can split, merge,
or remove the wire), then ``_reselect_on_footprint()`` to restore the Qt
selection so the user can immediately move the wire again.

**Undo / redo:**
``_push_undo()`` snapshots the current state with ``to_data()`` and pushes it
onto ``_undo_stack`` (capped at 50 entries).  ``undo()`` / ``redo()`` call
``_restore(data)`` which re-populates the scene from the snapshot.  The undo
stack is separate from the data model: each entry is a complete, independent
``SchematicData`` object.


.. _design-connectivity:

Layer 6 — Connectivity (``connectivity.py`` + ``canvas.py``)
-------------------------------------------------------------

**What it contains:**
Net resolution and topological maintenance.  It has no persistent state: all
functions operate on the current contents of the scene and are re-run whenever
the topology changes.

``connectivity.py`` — ``resolve_nets()``
    Builds a ``{grid_point: net_name}`` mapping using a union-find structure
    (``_UF``) over wire points and component pins.  Net names are assigned by
    priority: ground symbol → ``"0"``, port symbol name, explicit user
    ``net_name`` on a wire, auto-generated sequential integer.

``canvas.py`` — ``_sync_junctions()``
    Called after every topological edit (place, delete, move, wire commit).
    Runs the following wire-normalisation pipeline in order, then updates
    junctions and markers:

    1. Remove zero-length wires (endpoints coincide).
    2. ``_split_through_wires()`` — break any wire whose interior is crossed
       by another wire endpoint or a component pin (T-tap rule).
    3. ``_split_wire_elbows()`` — decompose every multi-segment (elbow) wire
       into individual two-point straight segments.  After this pass every
       ``WireItem`` in the scene has exactly two grid-snapped endpoints.
    4. ``_merge_collinear_wires()`` — fuse pairs of collinear adjacent segments
       that share a junction-free endpoint into a single longer segment.  Also
       removes exact duplicate segments.  Fusion is blocked at endpoints that
       coincide with a component pin, so component connections are never silently
       absorbed.  Net attributes (name, lock, label) are inherited from the
       segment that carried a locked or named net.
    5. Compute the required junction set with ``_find_junction_points()``.
    6. Add missing ``JunctionItem``\s and remove superfluous ones.
    7. ``_sync_port_net_names()`` — propagate port names to all wires on the
       same net.
    8. ``_refresh_pin_markers()`` — mark unconnected pins.

``canvas.py`` — ``_remove_short_circuit_wires()``
    Called when a component or wire is moved.  Removes any single wire segment
    whose **both** endpoints land exactly on pins of the **same** component
    (e.g. a wire accidentally connecting drain to source of a transistor).

    The check is strictly per-segment: only a direct pin-to-pin connection
    expressed as one straight line segment is removed.  Intentional multi-hop
    connections such as a bulk–source tie routed with an elbow survive because
    the elbow is already decomposed into two separate segments by
    ``_split_wire_elbows()``, and each individual segment touches at most one
    pin of the same component.

``canvas.py`` — ``_reselect_on_footprint(moved_segs)``
    Helper called by both the body-move and vertex-drag release handlers after
    ``_sync_junctions()`` has run.  Re-applies the Qt selection state to any
    ``WireItem`` that overlaps the footprint of the just-moved wire(s).

    Two cases are handled:

    * **Split** — the moved segment was broken into shorter pieces; each piece
      has all its points inside the original footprint so it is re-selected.
    * **Merge** — the moved segment was fused with a rubber-band partner into a
      longer wire; the moved segment is a strict sub-range of the new wire, so
      the new (longer) wire is re-selected.

    Without this helper, ``_sync_junctions()`` would destroy the Qt selection
    and the user would be unable to immediately move the wire again.

``canvas.py`` — ``_sync_port_net_names()``
    Runs the same union-find as ``resolve_nets()`` but operates on the live
    scene items rather than the data model.  Wires whose net contains a port
    symbol have their ``net_name`` locked to the port name and their original
    user label saved in ``_user_net_name``; removing the port restores the
    original name.

Junction detection rule (``_find_junction_points``):
    A junction is required when the total number of connections (wire endpoints
    + component pins) at a grid point is ≥ 3, *or* when a wire endpoint lands
    on the interior of another wire (T-tap safety rule).


.. _design-project:

Layer 7 — Project and File Layout (``project.py``)
---------------------------------------------------

**What it contains:**
Resolution of the project directory structure and per-schematic sidecar file
paths.  It is a module with a single piece of mutable state: ``_base``, the
path of the currently open ``.slicap_sch`` file (``None`` when unsaved).

A SLiCAP project directory has a fixed layout::

    <project>/
      sch/   <name>.slicap_sch     ← schematic source (JSON)
             <name>.cache/         ← rendered LaTeX SVGs (one per fragment)
             <name>.ini            ← per-schematic style overrides
             <name>.symbols        ← frozen symbol bundle
      cir/   <name>.cir            ← exported SLiCAP / NGspice netlist
      lib/   <name>.lib            ← exported subcircuit library
             *.svg                 ← user symbol definitions
      img/   <name>.svg            ← exported schematic image
             <name>.pdf

``project_root()`` derives the root from the schematic path (if the
``.slicap_sch`` file is in ``sch/``, root is its parent) or falls back to the
application root for unsaved schematics.

On the first save of a previously-unsaved schematic, the session-temporary
LaTeX cache directory is migrated to ``<name>.cache/`` so the saved file is
immediately self-contained and portable.


.. _design-export:

Layer 8 — Export (``export.py``, ``netlist.py``)
-------------------------------------------------

**SVG export (``export.py``):**
Iterates ``scene.items()`` directly.  For each ``ComponentItem`` it inlines the
symbol SVG content as a transformed ``<g>`` element; labels, wires, junctions,
text items, and shapes are each rendered to SVG geometry.  LaTeX fragments and
images are embedded as ``<image>`` elements with ``data:`` URIs.  The output
is a self-contained SVG file with no external dependencies.

**PDF / Print export (``export.py``):**
The SVG generated above is fed to ``QSvgRenderer`` and rendered onto a
``QPainter`` backed by a ``QPrinter`` (PDF mode or system printer).  This
produces vector PDF output with the same fidelity as the SVG.

**Netlist export (``netlist.py``):**
Walks the scene to collect ``ComponentItem``\s, ``WireItem``\s, ``LibraryItem``\s,
and ``CommandItem``\s.  Calls ``connectivity.resolve_nets()`` to assign net
names, then formats each component as a SLiCAP/SPICE element line.  The
resulting ``.cir`` file is written to ``cir/<name>.cir``.  If the schematic is
marked as a subcircuit (``DocumentProperties.is_subcircuit``), the netlist is
wrapped in a ``.subckt`` / ``.ends`` block and written to ``lib/<name>.lib``
instead.


.. _design-window:

Layer 9 — Application Window (``window.py``, ``canvas.py``)
------------------------------------------------------------

``MainWindow(QMainWindow)``
    Top-level window.  Builds the menu bar (File, Edit, View, Draw, Place,
    Tools, Help) and connects menu actions to scene methods and file-dialog
    handlers.  Manages ``_dirty`` state (set by ``scene.data_changed``).
    Owns the ``SymbolLibrary`` instance and rebuilds it on every New / Open.

``SchematicView(QGraphicsView)``
    The viewport.  Renders the grid (minor grey lines every ``GRID_SIZE``
    units, major lines every ``GRID_MAJOR`` multiples) in ``drawBackground()``.
    Handles wheel zoom and drag-scroll.  Switches between ``RubberBandDrag``
    and ``NoDrag`` scroll modes depending on the scene's active mode (placement
    and wiring use ``NoDrag`` so clicks are not intercepted by drag-selection).


.. _design-config:

Layer 10 — Configuration (``config.py``, ``style.ini``)
-------------------------------------------------------

``config.py``
    Module-level constants for visual appearance: ``GRID_SIZE``,
    ``GRID_MAJOR``, ``GRID_MINOR_COLOR``, ``GRID_MAJOR_COLOR``,
    ``JUNCTION_COLOR``, ``JUNCTION_RADIUS``, ``COMMAND_COLOR``, ``COMMAND_FONT``,
    ``COMP_LABEL_FONT``, ``COMP_LABEL_COLOR``, etc.  Also defines the ``snap()``
    function that rounds a scene ``QPointF`` to the nearest ``GRID_SIZE`` integer.

``style.ini``
    INI file at the project root with user-adjustable overrides for the same
    constants (loaded by ``config.py`` at startup).

``<name>.ini``
    Per-schematic style overrides (loaded alongside ``style.ini`` when a
    schematic is opened, so different schematics can have different visual
    styles).


Data-Flow Summary
-----------------

The following table shows which layer owns which data and in which direction
information flows:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Layer
     - Owns / is responsible for
     - Does NOT contain
   * - Symbol definitions (SVG)
     - Artwork, pin positions, metadata attributes
     - Instance data, net names, parameter values
   * - Metadata registry (dicts)
     - Per-symbol lookup tables for the scene layer
     - Qt objects, schematic state
   * - Data model (dataclasses)
     - Serialisable schematic state (positions, params, net hints)
     - Qt objects, rendering, interaction logic
   * - Canvas scene (items)
     - Live Qt items, rendering, undo snapshots
     - On-disk format, connectivity logic
   * - Interaction / modes
     - Mouse-event dispatch, placement ghosts, undo stack
     - Persistent state (ghosts are discarded after each action)
   * - Connectivity
     - Net names, junction placement, wire splitting
     - Visual appearance, serialisation
   * - Project layout
     - Path resolution, sidecar locations, cache migration
     - Scene state, symbol data
   * - Export
     - SVG/PDF/netlist file generation
     - Scene mutation, UI state
   * - Window / view
     - Menus, zoom, grid rendering, file dialogs
     - Schematic data, symbol metadata
   * - Configuration
     - Visual constants, snap function
     - Circuit data of any kind
