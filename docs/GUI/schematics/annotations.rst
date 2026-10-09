===========
Annotations
===========

Annotations are non-electrical additions that make a schematic into a finished
figure.  They are ignored by the netlister but appear in the SVG/PDF export.

Free text
=========

:menuselection:`Draw --> Text…` (shortcut :kbd:`T`) adds a line of text.  Use it
for notes, titles or callouts.

The text dialog sets the font family, the size, bold and italic, and the
colour of that text. Every setting has a *(Preferences)* state, the default,
in which the text follows the schematic's drawing preferences. The family
list offers the generic families **sans-serif**, **serif** and
**monospace**. They render the same on every machine, in the editor and in
the SVG and PDF export, because the viewer resolves a generic family to a
font it has. A named font can be typed in the list, at the risk that another
machine substitutes it.

Document properties
===================

:menuselection:`Place --> Document properties…` places a text block that
shows the document properties: project, title, author, created and last
modified. Its text is derived, not typed. The dialog holds a template with
the placeholders ``{project}``, ``{title}``, ``{author}``, ``{created}`` and
``{modified}``, one field per line by default. Edit the template for
another layout, such as ``{title}, {author}``, or delete lines for fewer
fields. A line whose placeholders are all empty is left out.

The block is rendered on load, after the properties dialog and at every
save, so an exported figure carries the date of the save that produced it.
In the editor the block shows the date of the previous save until you save
again. There is one block per drawing. The menu opens that block when it
exists, as it does for the parameter table. The font, the face and the
colour are those of the text dialog, with the drawing preferences as the
default. The block is plain text in the export, never LaTeX, and it is
placed and dragged freely like any text.

LaTeX fragments
===============

:menuselection:`Draw --> LaTeX…` adds a block of typeset LaTeX — equations,
aligned derivations, anything a ``standalone`` LaTeX document can produce.
(Requires ``pdflatex`` and ``dvisvgm``.)

The dialog's **Colour** tints the fragment, on the canvas and in the export,
in the same way the LaTeX labels of a symbol take the symbol's colour: the
black of the render is replaced, a colour written in the LaTeX code itself
is kept. Unticked, the fragment is black.

.. figure:: /GUI/img/latex_fragment.png
   :alt: A LaTeX fragment
   :width: 55%

   A typeset equation placed next to the circuit it describes.

Hyperlinks
==========

:menuselection:`Draw --> Hyperlink…` adds clickable link text (for example to a
course or datasheet).  In the editor, right-click the link to open or edit it.

Images
======

:menuselection:`Place --> Image…` places a raster or vector image — a logo,
a photo of a measurement, a plot.

The image is a link, not a copy: the schematic stores the file's path and
reads the file whenever it is opened, exported, or after a run of the
instruction file. A plot written by the simulation into ``img/`` therefore
updates on the canvas and in the exported schematic by itself (see
:doc:`netlist_and_export` for the export at the end of a run). A file inside
the project is stored relative to the project root, so the project can move
between machines; a file elsewhere is stored with its absolute path.
An image can be anything but the schematic's own exported image: a
schematic that showed itself would make its export its own input, stale
after every run and nested in every export, so the dialog refuses that
file.

Figures
=======

:menuselection:`Place --> Figure…` places a **figure object** of the
Design data, chosen by name from the figures the last runs made with
``makeFigure()``. The image it shows is the file that figure writes to
``img/``, taken from the Design data, so a figure whose file name changes
in the instruction file follows on the canvas after the next run, and the
picture updates after every run like a placed image. The dialog sets the
scale as for an image. A figure is never the schematic's own export, so a
Figure cannot link a schematic to itself. Run the instruction file first:
the dialog offers what the Design data panel shows.

LaTeX snippets
==============

:menuselection:`Place --> LaTeX snippet…` places a **LaTeX snippet object**
of the Design data, chosen by name: ``EX1 = ltx.expr(G)`` makes one, a saved
file is not needed. The item takes the snippet's text from the Design data,
renders it with SLiCAP's LaTeX preamble, and re-renders it after every run
that changed it. Scale and colour are the item's own, set in the dialog as
for a LaTeX fragment; the snippet itself is never touched. A numbered
equation renders without its number, because a schematic has no equation
numbers to refer to, while the snippet keeps its number in the report. Only
LaTeX snippets are offered: an RST or HTML snippet cannot be typeset on a
schematic.

Drawing primitives
==================

The :menuselection:`Draw` menu also provides simple shapes — **Line**,
**Rectangle**, **Ellipse**, **Polygon**, **Arc**, **Curve** and **Function
curve** — for framing, grouping or highlighting parts of the diagram and for
the sketches of a figure. A line and a polygon take a click per
vertex and end with a double click, Enter or Escape (a polygon needs three
vertices); a rectangle and an ellipse take two opposite corners, so a
square or a circle is the special case of equal sides.

An **arc** is a part of the ellipse of two corners, from a start angle over
a sweep, both set in its properties or by dragging the two end handles on
the canvas, with line ends as a line has them: the loop and rotation arrow
of many figures. A **curve** is clicked like a polygon, but passes smoothly
through its points, open with line ends or closed with a fill: the
hand-drawn curve. A **function curve** is a box of two corners into which
sampled data is mapped, y upward: either an expression in one variable over
a range, in SLiCAP notation (``exp(x) - 1``, ``1/(1+(f/1k)**2)``, with a
linear or logarithmic x axis), sampled by SLiCAP itself, or a **trace of the
Design data**, chosen by name, which makes it a miniature plot that follows
every run of the instruction file. The y range is taken from the data
unless given. Only as many points as the box can resolve are kept. The
properties dialog opens first, because a function curve is nothing without
its source; after OK the two opposite corners of the rectangle the curve
is drawn in are clicked.

A selected shape shows a small square on every point that can be dragged:
the vertices of a line, polygon or curve, the two corners that define a
rectangle, ellipse, arc or function box, and the two ends of an arc.
Dragging one reshapes the shape, also when it is rotated. Double-click a shape
for its properties: stroke colour, width and style (**none** shows a filled
shape without contour), fill, a rotation angle about the shape's centre,
and for a line the two line ends. An arrow head is a filled triangle
without contour with its own width and length (the defaults 4 and 6 are
those of the current-source arrow of the symbol library); a wide arrow with
a shaft that has width is a polygon. **R** turns a selected shape by a
quarter turn about its centre and **M** mirrors it about the vertical axis
through its centre, as for a component. Both act on the shape's points, so
a line with an arrow head keeps its head at the same end; the rotation
angle of the properties stays as it is (mirroring changes its sign).

Stacking order
==============

Every annotation, a shape, image, LaTeX fragment, text or hyperlink, has a
place in the stacking order of its own, saved with it, and the exports draw
in that order. :menuselection:`Edit --> Bring to front` (:kbd:`Ctrl+Shift+]`),
:menuselection:`Bring forward` (:kbd:`Ctrl+]`), :menuselection:`Send
backward` (:kbd:`Ctrl+[`) and :menuselection:`Send to back`
(:kbd:`Ctrl+Shift+[`) move the selected annotations. An annotation can go
above the circuit, a figure over a component, or two schematics overlapping
on a poster, and below the wires, but never under the border. The circuit
itself keeps its layers: wires, components, junctions and net labels in
that order.

.. _border-formats:

Borders and document properties
===============================

* :menuselection:`Place --> Border` (:kbd:`B`) adds a drawing border/frame.
  The border is the export frame: the exported SVG and PDF have its size,
  and the border clips. Everything outside it is left out of the export,
  and an item that crosses it is cut at the border. Without a border the
  export is exactly as large as the drawing. Only a text at the edge gets
  a small guard against clipping. The Border dialog has a *Format* row
  that fills the width, the height and their Fixed boxes from a format.
* :menuselection:`File --> Schematic properties…` sets the title, author and
  the border. The *Border* field shows the border's format, a format creates
  or resizes the border, and **Drawing size** removes it.

The formats are the paper sizes A4 to A0, Letter, Legal and Tabloid,
portrait or landscape, the screen formats 16:9, 16:10 and 4:3, and the
**border formats** of the drawing preferences. A border format of your own
has a width, a height, or both. A side that is left empty is free: it is
not fixed, and you size it by hand on the canvas. A figure for a book is a
border with the width of the document column and a free height. The same
formats serve the New poster dialog, so a poster of posters of schematics
is one hierarchy of drawings with one border model.

Renaming components
===================

:menuselection:`Tools --> Rename Components…` renumbers reference designators in
bulk — handy after a lot of editing.

Placement and grid
------------------

Free text, LaTeX fragments, hyperlinks and images are annotations: they are
placed and dragged freely, at any position, so that a caption such as a
polarity sign or a voltage name can be aligned with a symbol. Symbols, wires
and junctions always snap to the grid, because the connectivity is computed
from their positions. Everything else (the border, drawn shapes, and the
parameter, analysis, model, library and command blocks) snaps to the grid,
or to a fine grid of one fifth of it while **Shift** is held while dragging,
so that a short line keeps its alignment. A shape snaps the vertex nearest to
the point where it was grabbed, so a polyline whose first point is off the
grid can still be placed with any vertex on a grid point; a selected shape
shows a handle at every vertex, and dragging a handle reshapes it.
