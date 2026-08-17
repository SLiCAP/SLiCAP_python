=============================
Creating / editing schematics
=============================

Launching the schematic editor from the GUI
===========================================

The *Structured Electronic Design Environment* interfaces with both SLiCAP and NGspice. Although schematics for both applications may look similar, models and component attributes differ for both applications. SLiCAP is intended for symbolic analysis of linear continuous-time, dynamic circuits, whereas NGspice supports numeric analysis of nonlinear, time-variant, dynamic circuits. For this reason, The GUI uses different symbol sets and libraries for SLiCAP and NGspice. SLiCAP schematic files use the file extension ``.slicap_sch`` and NGspice schematics use ``.spice_sch`` as file extension.

The schematic edditor can be started as follows:

#. From the main menu select File -> New SLiCAP Schematic
#. From the main menu select File -> New NGspice Schematic
#. From the main menu select File -> Open schematic

Below the screenshot after creating a new SLiCAP schematic.

.. Figure:: /GUI/img/new_schematic.png

After saving it as "my_circuit.slicap_sch" it becomes visible in the Project panel (in the ``.sch`` folder):

.. Figure:: /GUI/img/my_circuit.png

Launching the schematic editor from outside the GUI
===================================================

**From a Python session or Jupyter notebook** (the usual way):

.. code-block:: python

   import SLiCAP as sl
   sl.initProject("My Design")

   sl.startSchematic()                                # empty editor; choose type from the File menu
   sl.startSchematic(config='basic')                  # SLiCAP basic-symbol capture mode
   sl.startSchematic(file='sch/mydesign.slicap_sch')  # open an existing file
   sl.startSchematic(config='basic', file='sch/mydesign.slicap_sch')

The call returns immediately; the editor runs as an independent process alongside
the Python session (schematic-only: no Instruction/Log panels).

``config`` selects the **capture mode**.  It sets the symbol library *and*
restricts which schematic type may be created or opened:

.. list-table::
   :header-rows: 1
   :widths: 12 46 42

   * - ``config``
     - Symbol set loaded
     - Schematic type
   * - ``None`` *(default)*
     - chosen per schematic
     - both SLiCAP and NGspice allowed
   * - ``'basic'``
     - ``Symbols.svg`` only (basic IEC/SLiCAP symbols only)
     - SLiCAP only (NGspice disabled)
   * - ``'slicap'``
     - the complete SLiCAP library (all SVG files in the system symbols directory)
     - SLiCAP only (NGspice disabled)
   * - ``'ngspice'``
     - the NGspice symbol library
     - NGspice only (SLiCAP disabled)

In a restricted mode the disallowed :menuselection:`File --> New ... Schematic`
entry is greyed out and :menuselection:`File --> Open` lists only files of the
permitted type.

``file`` is the path to a schematic to open at startup; its type is inferred from
the extension (``.slicap_sch`` or ``.spice_sch``).  **A canvas is shown only when
a file is given** — otherwise the editor opens empty and you create or open a
schematic from the File menu (honouring the capture mode).

**From the command line** (for scripting or desktop shortcuts):

.. code-block:: console

   $ slicap                                                       # full editor, both types
   $ slicap-schematics                                            # schematic-only editor, empty
   $ slicap-schematics --config basic                             # basic SLiCAP mode, empty
   $ slicap-schematics --config ngspice sch/mydesign.spice_sch    # open an NGspice file
   $ python -m SLiCAP.schematic.main --schematic-only --config basic

Without a ``file`` the editor opens empty; use the File menu to create or open a
schematic in the selected mode.

.. figure:: /GUI/img/main_window.png
   :alt: The main window
   :width: 100%
   
The schematic menu bar at a glance
==================================

By default each schematic is displayed in a separate tab, but each open schematic has its own panel with its own menu bar with actions on that schematic:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Menu
     - Contents
   * - **File**
     - Save schematic (:kbd:`Ctrl+S`), Save schematic as
       (:kbd:`Ctrl+Shift+S`), Schematic properties, Export netlist
       (:kbd:`Ctrl+E`), Export SVG, Export PDF, Print schematic
       (:kbd:`Ctrl+P`), Schematic drawing preferences.
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
   * - **Instruction**
     - Create circuit object and Create / edit SLiCAP instruction (SLiCAP
       schematics), or Create / edit NGspice instruction and control section
       (NGspice schematics) — see :doc:`/GUI/instruction/instructions`.

Creating and opening schematics, and application-wide actions, live in the
**main window's** menu bar:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Menu
     - Contents
   * - **File**
     - New project, Select project folder, Save project, Close project;
       New SLiCAP Schematic, New NGspice Schematic, Open (:kbd:`Ctrl+O`);
       Exit (:kbd:`Ctrl+Q`).
   * - **Instruction**
     - Create / edit Traces, Axes, Figures and specifications;
       Run (:kbd:`F5`), Stop (:kbd:`F6`).
   * - **View**
     - Show/hide the Project, Instructions, and Log panels.
   * - **Help**
     - Show HTML Documentation (:kbd:`F1`), Check for updates, About.

A first schematic in five steps
===============================

#. **Place a symbol.**  Open :menuselection:`Place --> Symbol…` (shortcut
   :kbd:`S`), pick a resistor and click on the canvas to drop it.  See
   :doc:`/GUI/schematics/placing_symbols`.

#. **Wire it up.**  Choose :menuselection:`Place --> Wire` (shortcut :kbd:`W`)
   and click from one pin to the next.  Unconnected pins show a small grey
   marker that disappears once a wire reaches them.  See :doc:`/GUI/schematics/wiring`.

#. **Set values.**  Double-click a component to open its **Properties** dialog
   and enter a value (for example ``R_s`` for a resistance).  See
   :doc:`/GUI/schematics/component_properties`.

#. **Mark source and detector.**  Use
   :menuselection:`Place --> Define src / det / lg ref…` to designate the
   independent source and the detector.

#. **Save and export.**  :menuselection:`File --> Save schematic` writes the
   ``.slicap_sch`` file; :menuselection:`File --> Export netlist…` produces a
   ``.cir`` netlist for SLiCAP.  See :doc:`/GUI/schematics/netlist_and_export`.
   
   
Below an example of a SLiCAP schematic with default preferences and LaTeX rendering enabled.

.. Figure:: /GUI/img/RCcircuit.png
   
Sidecar files
=============

A schematic is **self-contained**: everything it needs to look and behave the
same on another machine travels next to it in ``sch/``.  Saving
``my_circuit.slicap_sch`` creates and maintains a small set of sidecar files
with the same base name.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - File
     - Contents
   * - ``my_circuit.slicap_sch``
     - The schematic itself (components, wires, labels, annotations) — the file
       you open and save.
   * - ``my_circuit.ini``
     - This schematic's **style** (line widths, colours, fonts), so it always
       looks as it did when saved.  See :doc:`/GUI/schematics/preferences`.
   * - ``my_circuit.symbols``
     - **Frozen copies** of every symbol the schematic uses, so it renders with
       the exact symbols it was drawn with.  See :doc:`/GUI/reference/symbol_libraries`.
   * - ``my_circuit.cache``
     - A cache of rendered LaTeX labels, so re-opening is fast.  Created only if
       the schematic actually contains typeset expressions; safe to delete.

Why sidecar files
=================

* **Portability** — copy the ``.slicap_sch`` together with its ``.ini`` and
  ``.symbols`` to another computer and it looks and netlists identically.
* **Reproducibility** — a figure in a book keeps its appearance even if the
  application's default symbols or style change later.
* **No clutter** — the render cache lives next to the schematic, not in a global
  folder that quietly grows over time.  Deleting a project removes all its
  files together.

.. note::

   The ``.ini`` and ``.symbols`` files are part of the project and should be
   kept (and version-controlled) with the schematic.  The ``.cache`` directory
   is regenerated automatically and can be ignored or deleted.
   


