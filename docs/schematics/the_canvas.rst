==========
The Canvas
==========

The canvas is the drawing area.  It uses a square grid; everything you place
snaps to the grid so pins and wires line up exactly.

.. figure:: images/canvas_grid.png
   :alt: The grid
   :width: 70%

   The grid: fine snap cells with a heavier line every eight cells.

Grid and snapping
=================

* The **snap step** is the fine grid spacing — every component, pin and wire
  vertex lands on it.
* A **major grid line** is drawn every eight fine cells to help you judge
  distances.
* Grid colours can be changed under :menuselection:`File --> Preferences`
  (see :doc:`preferences`).

Selecting items
===============

* **Click** an item to select it.
* **Rubber-band select** by dragging on empty canvas.  Dragging
  **left-to-right** selects items fully enclosed; dragging **right-to-left**
  selects anything the box touches (KiCad-style).
* A selected component shows a blue outline; a selected wire shows square
  **handles** at its vertices.

Moving items
============

* Drag a selected item to move it.  Components and wires keep their existing
  connections while you move them (see :doc:`wiring`).
* Movement is snapped to the grid.

Zoom and pan
============

* :menuselection:`View --> Fit` (:kbd:`F`) frames the whole drawing.
* :kbd:`+` / :kbd:`-` zoom in and out; :kbd:`Ctrl+0` resets the zoom.
* Use the scroll bars or the mouse wheel to pan.

Undo and redo
=============

Every edit can be reversed with :menuselection:`Edit --> Undo` (:kbd:`Ctrl+Z`)
and re-applied with :menuselection:`Edit --> Redo` (:kbd:`Ctrl+Y`).
