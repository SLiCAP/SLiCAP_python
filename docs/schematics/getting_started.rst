===============
Getting Started
===============

Requirements
============

* Python 3.10 or newer
* `PySide6 <https://pypi.org/project/PySide6/>`_ (the Qt 6 bindings)
* A working **SLiCAP** installation (used for symbol metadata and for typesetting
  parameter values)
* For LaTeX-typeset labels and figure export: ``pdflatex`` and ``dvisvgm``
  (a TeX distribution such as TeX Live).  These are optional — without them the
  editor falls back to plain-text labels.

Launching the editor
=====================

From the project root directory, run:

.. code-block:: console

   $ python -m app.main

The main window opens with an empty canvas.

.. figure:: images/main_window.png
   :alt: The main window
   :width: 100%

   The main window: menu bar, symbol palette (left) and the drawing canvas.

A first schematic in five steps
===============================

#. **Place a symbol.**  Open :menuselection:`Place --> Symbol…` (shortcut
   :kbd:`S`), pick a resistor and click on the canvas to drop it.  See
   :doc:`placing_symbols`.

#. **Wire it up.**  Choose :menuselection:`Place --> Wire` (shortcut :kbd:`W`)
   and click from one pin to the next.  Unconnected pins show a small grey
   marker that disappears once a wire reaches them.  See :doc:`wiring`.

#. **Set values.**  Double-click a component to open its **Properties** dialog
   and enter a value (for example ``{R_s}`` for a symbolic resistance).  See
   :doc:`component_properties`.

#. **Mark source and detector.**  Use
   :menuselection:`Place --> Define src / det / lg ref…` to designate the
   independent source and the detector.

#. **Save and export.**  :menuselection:`File --> Save` writes the
   ``.slicap_sch`` file; :menuselection:`File --> Export Netlist…` produces a
   ``.cir`` netlist for SLiCAP.  See :doc:`netlist_and_export`.

The menu bar at a glance
========================

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Menu
     - Contents
   * - **File**
     - New (:kbd:`Ctrl+N`), Open (:kbd:`Ctrl+O`), Save (:kbd:`Ctrl+S`),
       Save As (:kbd:`Ctrl+Shift+S`), Document Properties, Export Netlist
       (:kbd:`Ctrl+E`), Export SVG, Export PDF, Print (:kbd:`Ctrl+P`),
       Preferences.
   * - **Edit**
     - Undo (:kbd:`Ctrl+Z`), Redo (:kbd:`Ctrl+Y`).
   * - **View**
     - Fit (:kbd:`F`), Zoom In (:kbd:`+`), Zoom Out (:kbd:`-`),
       Reset Zoom (:kbd:`Ctrl+0`).
   * - **Draw**
     - Line, Rectangle, Circle, Text (:kbd:`T`), Hyperlink, LaTeX.
   * - **Tools**
     - Rename Components.
   * - **Place**
     - Symbol (:kbd:`S`), Wire (:kbd:`W`), Net Label (:kbd:`L`),
       Junction (:kbd:`J`), Border (:kbd:`B`), Library, Image, Parameters,
       Define src / det / lg ref.
   * - **Help**
     - Show HTML Documentation (:kbd:`F1`), About.
