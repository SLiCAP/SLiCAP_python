===========
Preferences
===========

:menuselection:`File --> Schematic drawing preferences…` controls the **appearance** of the
current schematic — line widths, colours and fonts.

.. figure:: /GUI/img/preferences.png
   :alt: The Preferences dialog
   :width: 75%

   The Preferences dialog, grouped by element type.

Per-schematic styling
=====================

Styling works on two levels:

* The application's **global defaults** are the template for every *new*
  schematic.
* When you change a setting in Preferences, it applies to the **current
  schematic** and is saved into its ``<name>.ini`` sidecar file (see
  :doc:`/GUI/project/project`).  Re-opening that schematic restores exactly the look it
  was saved with — independent of the machine's global defaults.

This is what lets a book or report keep a consistent house style across all its
figures.

What you can change
===================

The dialog is grouped by element type, including:

* **Symbol** — stroke and text colour.
* **Wire** — colour and width.
* **Net label**, **Component refdes**, **Component parameters** — colour, font
  and size.
* **Text annotations**, **Hyperlinks** — fonts and colours.
* **Grid** — minor and major line colours.
* **Wire handles / connections** — the colour and size of wire selection
  handles, and the **connection colour** used for the unconnected-pin markers
  (see :doc:`wiring`).
* **Junctions** — colour and radius.
* **Rendering** — turn LaTeX typesetting of labels on or off, and set the
  LaTeX scale of the schematic (see `LaTeX scales`_ below).
  Leave typesetting **off in NGspice schematics**: a simulator expression is code, not
  mathematics, and only the part of it that is also valid mathematics can be
  typeset. A value that cannot be typeset is shown as plain text — it is never
  rendered wrongly. If you want a typeset expression on an NGspice schematic,
  either accept the generated form, or hide the value and place the formula
  yourself with :menuselection:`Draw --> LaTeX text...`; such a snippet is for
  display only and is not netlisted.

Every font family list offers the generic families **sans-serif**, **serif**
and **monospace**. They render the same on every machine, in the editor and
in the SVG and PDF export, because the viewer resolves a generic family to a
font it has. A named font can be typed in the list, at the risk that another
machine substitutes it.

Changes take effect immediately on the canvas.

LaTeX scales
============

A schematic has one **LaTeX scale**, in the **Rendering** group of the
preferences, 150 % by default. The GUI typesets LaTeX at 10 pt. At 100 %,
the text has that size in a drawing at 2 units per mm, the default of the
project setting ``sch_scale``. The reference does not depend on the
project's ``sch_scale``, so a percentage gives the same text size relative
to the symbols in every project. On paper, in a figure that is included at
its natural size, the text is 10 pt × scale × 2 / ``sch_scale``: at 150 %
this is 15 pt at 2 units per mm and 8.5 pt at 3.54 units per mm. The component
labels (reference designators and parameter values) always use this scale.
LaTeX fragments, parameter and model tables, and the analysis and library
blocks use it too, unless they have a scale of their own: their dialogs
have a **LaTeX scale** field with a **Default** box. With **Default**
checked, the item follows the schematic's scale, and changing the scale in
the preferences resizes it. Without it, the item keeps its own percentage.
New items start at **Default**.

Schematics saved before this scale was introduced are converted on
loading. The schematic's scale becomes the scale at which the labels were
drawn, and the tables, blocks and fragments get their old size as their own
scale, so no drawing changes size.

Grid
====

Three grids: the minor lines (the grid step), the major lines (every
eight minor cells) and the subgrid, a dot on every point of the fine grid,
one fifth of the grid step, the grid that shapes snap to while Shift is
held. Each has its colour; **View subgrid** switches the dots on, and they
appear when the zoom keeps them apart.

Border
======

The **Border** group sets the look that a *new* border gets when it is placed
(Place > Border): line colour, width and style (solid, dashed, dotted,
dash-dot), background colour and opacity, and whether the line is drawn in
the exported SVG/PDF. An existing border
keeps its own values, edited in the Border dialog. A background at opacity
0 % is invisible; choosing a background colour in the Border dialog therefore
sets the opacity to 100 % when it was 0 %.

The defaults are those of the figures in the book *Structured Electronic
Design*: a solid blue line, the light blue background ``#ecf3ff`` at 100 %
opacity, and no border line in the export, so an exported schematic is a
figure on a tinted panel. The same palette sets black symbol text, red net
labels and blue operating-point annotations. A schematic's own values live
in the ``[border]`` and other sections of its ``.ini`` sidecar; give every
border the width of the document column (see the ``sch_scale`` setting
under :doc:`/GUI/project/project`).

The **Border formats** table holds formats of your own, offered next to the
paper and screen formats in the Border dialog, the properties dialog and
the New poster dialog. A row is a name, a width and a height in mm. Leave
the width or the height empty for a free side: that side is not fixed, and
you size it by hand on the canvas. The row ``Column``, ``120``, empty is a
figure of a book with a 120 mm column: a fixed width and a free height.
The table is the ``[border_presets]`` section of the sidecar, one line per
format, ``Column = 120 x``.

Colour scheme
=============

:menuselection:`File --> Preferences...` on the main window has a **Colour
scheme**: *system* follows the desktop, *light* and *dark* force one. The
window chrome follows through Qt. On a dark scheme the canvases draw on a
dark background with every colour's lightness inverted for the screen only:
black wires show white, white fills dark, red stays red; LaTeX renders
(labels, parameter table, model and analysis blocks, fragments) show their
black as white. A change of the desktop scheme while SLiCAP runs is followed
at once. The schematic style, and therefore every SVG and PDF export, keeps
the document colours.
