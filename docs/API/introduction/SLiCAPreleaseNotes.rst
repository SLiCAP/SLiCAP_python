====================
SLiCAP release notes
====================

.. image:: /API/img/colorCode.svg

SLiCAP version 6.2 release notes
================================

Version 6.2 turns the schematic editor into an **SVG editor with
script-updatable objects**. A drawing can show figures, LaTeX snippets and
traces of the Design data by name, and schematics and other drawings of the
project as links. Everything shown follows the runs of the instruction
files, and is updated by its execution. 

A new document type, the **poster**, is a drawing without a circuit, 
with a page format, for design overviews, hand-outs and clickable 
presentations. The Draw menu gained arcs, hand-drawn curves and function 
curves, each with a user-defined stacking order.

#. **Text and LaTeX annotations.** The text dialog sets the font family,
   size, bold, italic and colour of a text annotation. Each setting has a
   *(Preferences)* state, the default, in which the text follows the
   schematic's drawing preferences, so existing schematics are unchanged.
   The family list offers the generic families sans-serif, serif and
   monospace, which render the same on every machine in the editor and in
   the exports. A LaTeX fragment has a colour of its own, applied as for the
   LaTeX labels of a symbol. See :doc:`/GUI/schematics/annotations`.

#. **Linked images update at the end of a run.** An image placed on
   a schematic is a link: the file is read when the schematic is opened,
   and recreated after every run of the instruction file: a plot the
   simulation writes into ``img/`` updates on the canvas and in the
   exported schematic. The new instruction ``sl.updateImages("<schematic name>")``, 
   appended to the instruction file by :menuselection:`Instruction --> Update schematic images…`, 
   exports the schematic with updated annotations. See
   :doc:`/GUI/schematics/netlist_and_export`.

#. **Figure title.** ``makeFigure()`` has a keyword ``title``: a heading
   drawn across the top of the figure, inside the image, so the SVG and
   PDF files carry it and the figure window shows it. The default is no
   heading. The Figures dialog has a Title field.

#. **Figure layout.** Figures with several rows or columns of axes
   kept matplotlib's default margins, more than an inch of white above and
   below a Bode stack, because the grid's own row spacing stopped the tight
   layout from running (the warning "Axes not compatible with
   tight_layout" in the log). The layout now runs on every figure; the
   settings ``subplothspace`` and ``subplotwspace`` of the project
   configuration are the minimum gap between rows and columns.

#. **Stacking order.** Shapes, images, LaTeX fragments, text and hyperlinks
   have a stacking order of their own, saved and exported: the Edit menu's
   Bring to front, Bring forward, Send backward and Send to back move the
   selected ones, also above the circuit. See
   :doc:`/GUI/schematics/annotations`.

#. **Posters.** :menuselection:`File --> New poster…` makes a drawing in
   ``posters/<name>.slicap_poster`` with a page format (paper sizes and
   screen formats) that shows schematics, other posters, figures and
   snippets of the project by name, as links that follow every run and
   export. A poster is never netlisted. Its export first updates the drawings 
   it shows. In a browser a click on a shown drawing opens that drawing's own export.
   ``updateImages()`` also takes a poster name as argument. The project configuration 
   has the new path ``posters``. See :doc:`/GUI/schematics/posters`.

#. **Arc, curve and function curve.** The Draw menu has three more shapes
   for the sketches of a figure: an arc, a part of an ellipse between two
   angles with line ends; a curve through clicked points, open with line
   ends or closed with a fill; and a function curve, a box into which an
   expression sampled over a range, or a trace of the Design
   data is mapped. Such a miniature plot on a schematicupdates every run.
   The new function ``sampleExpr()`` does the sampling. The run manifest
   now records a reduced copy of every trace's data for this purpose. See
   :doc:`/GUI/schematics/annotations`.

#. **Figures and LaTeX snippets on the schematic.** The Place menu has
   :menuselection:`Figure…`, a figure object of the Design data chosen by
   name, and :menuselection:`LaTeX snippet…`, a snippet object of the
   Design data chosen by name, rendered with SLiCAP's preamble, with its
   own scale and colour. Both are links to the run: the figure's image and
   the snippet's text are taken from the Design data after every run. 
   See :doc:`/GUI/schematics/annotations`.

#. **Drawing defaults.** New schematics use the palette of the book
   *Structured Electronic Design*: black symbol text, red net labels, blue
   operating-point annotations, and a border with a solid blue line, the
   light blue background ``#ecf3ff`` at full opacity and no line in the
   export. The border line has a style of its own, solid, dashed, dotted or
   dash-dot, in the Border dialog and in the preferences for new borders;
   it was a fixed dash. Existing schematics keep the values of their
   ``.ini`` sidecar and their border keeps its dash. See
   :doc:`/GUI/schematics/preferences`.

#. **Project folders from the project configuration.** The schematic
   editor and the headless export resolve every project folder, images,
   netlists, libraries, schematics, posters and results, through the
   ``[projectpaths]`` section of the project's ``SLiCAP.ini``, as the
   scripts do. A project that writes its images to ``../Figures/`` gets its
   exported schematics and posters there too; they went to ``img/``
   before. The project root of a file is the nearest folder with a project
   ``SLiCAP.ini``.

#. **Generic font families.** Every font family list, in the drawing
   preferences and in the text dialog, offers sans-serif, serif and
   monospace. They render the same on every machine, in the editor and in
   the exports; a named font can still be typed, at the risk that another
   machine substitutes it.

#. **Design data at export time.** ``updateImages()`` called from inside an
   instruction file first writes the Design data of that file, then
   exports, so a snippet changed in the script is typeset with its new text
   in the exported images. The main script writes the Design data at the
   end of the run as before.

#. **Ground side of a detector pair.** The netlist accepts the word
   ``None`` as one side of ``.detector``: ``.detector None V_2`` is the
   negated node voltage, the netlist form of ``detector=[None, 'V_2']``.
   The source/detector/lgref block dialog of the schematic offers
   *(ground)* for both detector sides. On the minus side it is the single
   form. On the plus side it needs a second reference, and the result is the
   negated second reference. See :doc:`/API/userguide/analysis`.

#. **Save and Save as for a subcircuit.** *Save* writes the subcircuit
   package without a question once the node order is settled. The Create
   Subcircuit dialog opens on the first save and when a new port appears.
   *Save as…* always opens the dialog, with the name editable. Another
   name saves a copy of the package (schematic and library) in ``lib/``
   under that name. The copy becomes the open document. The name must be
   a netlist identifier: a letter, then letters, digits or underscores.

#. **Border formats.** The page of a poster is a border, as on a schematic.
   The New poster dialog, the properties dialog and the Border dialog offer
   the same formats: none, the paper and screen formats, a custom size, and
   the *border formats* of the drawing preferences. A border format of your
   own fixes the width, the height, or both. A free side is sized by hand.
   A figure of several circuits for a book is a poster with the width of
   the document column and a free height. See
   :doc:`/GUI/schematics/posters` and :doc:`/GUI/schematics/preferences`.

#. **Place → Schematic on a poster.** The dialog lists the schematic
   files of the project, ``sch/`` and ``lib/``, by their path. Nothing is
   preselected, and the image path is no longer shown. A placed schematic
   is a link to that file. The poster shows its export. Older posters,
   which name a schematic without its folder, still work. Choosing a
   drawing brings its export up to date, so it is shown at once, at
   100 %, and a placed drawing snaps to the grid, or to the fine grid
   while Shift is held. The default scale of a placed image is 100 % as
   well. A border clips the export: what lies
   outside it is left out, and an item crossing it is cut at the border.
   The export of a drawing without a border is exactly as large as the
   drawing. Only a text at the edge keeps a small guard against clipping.

#. **Document properties block.** :menuselection:`Place --> Document
   properties…` on a schematic or a poster places a text block with the
   project, title, author, created and last-modified fields. The text is
   derived from the document properties through an editable template, so
   it follows every save. One block per drawing. Font, face and colour as
   for a text. See :doc:`/GUI/schematics/annotations`.

#. **Dragging a selection.** A component selected together with its
   wires moves as a block: the selected wires translate with it, and the
   unselected wires at their far ends stretch. A moving point that sits
   on the pin of an unselected component stays connected: when it leaves
   the pin, the pin is bridged to its new position, with a dashed preview
   during the drag. Connections change only where pins end up. Only
   deleting a wire or a component disconnects.

#. **Fixes from a user's report on 6.1.0.** The placement ghost of a
   symbol, and the ghosts of a paste, are drawn in the display colours,
   so they are visible on the dark canvas. R during a paste no longer
   rotates the copied originals. The paste is the new selection, and R
   after placing it turns the pasted items. A label moved away from its
   default position keeps that position on the pasted copy. The project
   folders of SLiCAP.ini, such as an image folder outside the project,
   are honoured by the editor and by the headless export since 6.2.

SLiCAP version 6.1 release notes
================================

Version 6.1 combines the schematic capture for SLiCAP and NGspice with a
simple **SVG editor** (``Draw`` menu) to illustrate schematics, and with a
**symbol editor** for modifying and creating SLiCAP and NGspice symbols.

#. **Symbol editor.** :menuselection:`File --> New symbol` and
   :menuselection:`File --> Edit symbol...` on the main window open a canvas
   in symbol mode: the schematic editor with reduced menus, editing one
   symbol of a ``.slicap_sym`` or ``.spice_sym`` file in the project's
   ``lib`` folder. A double click on such a file in the Project panel does
   the same. The artwork is drawn with the Draw menu. The terminals are
   placed with :menuselection:`Place --> Pin...`, decoration with
   :menuselection:`Place --> Symbol text...`,
   :menuselection:`Place --> LaTeX...` and :menuselection:`Place --> Image...`.
   The element attributes (prefix, model, parameters with defaults,
   description, info link) are set with
   :menuselection:`File --> Symbol properties...`. A LaTeX label is compiled
   once and stored in the symbol as plain paths together with its source.
   An image is embedded. The symbol therefore renders on any machine, and
   the label reopens for editing where LaTeX is installed. A saved symbol is
   offered at once in :menuselection:`Place --> Symbol` of every open
   schematic of the project. See :doc:`/GUI/schematics/symbol_editor`.

#. **Drawing.** The Draw menu has lines, rectangles, ellipses and polygons.
   Double-clicking a shape opens its properties: stroke colour, width and
   style, fill, a rotation about the shape's centre and, for a line, the two
   line ends (arrow heads with their own width and length). A selected shape
   shows a handle at every vertex for reshaping. **R** turns a selected
   shape by a quarter turn and **M** mirrors it, as for a component. See
   :doc:`/GUI/schematics/annotations`.

#. **Shift + drag.** Items snap in three ways. Symbols, wires, junctions
   and symbol pins always snap to the grid, because the connectivity is
   computed from their positions. Text annotations never snap. Everything
   else snaps to the grid, or to a fine grid of one fifth of the grid step
   while **Shift** is held during the drag: the blocks of the Place menu
   (parameters, model definitions, the source, detector and loop gain
   reference definitions, library and command lines), the border, and the
   drawn shapes, which snap the vertex nearest to the point where they were
   grabbed. In the symbol editor the fine grid is one symbol unit, which
   symbol artwork needs. **View subgrid** shows the fine grid as dots, with
   its own colour in the drawing preferences. See
   :doc:`/GUI/schematics/annotations` and :doc:`/GUI/schematics/preferences`.

#. **Assigning symbols to components and subcircuits.** The component
   Properties dialog has a **Change symbol...** button. It offers the
   symbols with the same number of pins and, for a built-in element type,
   the same prefix, also those of the project's ``lib`` folder. The wires
   follow the pins to their new places. For a subcircuit block the ports are
   assigned to the pins of the chosen symbol in a list with a preview. The
   result is stored in the project's library as the block's symbol, so that
   :menuselection:`Tools --> Update symbols from library` keeps it and other
   schematics of the project can use it. See
   :doc:`/GUI/schematics/component_properties`.

#. **Orientation of symbol lettering.** The symbol texts and LaTeX labels of
   a rotated or mirrored component are read from the bottom or from the right
   of the sheet: upright at 0 and 180 degrees, bottom-to-top at 90 and 270
   degrees, never mirrored. This holds on the canvas and in the SVG and PDF
   exports.

#. **Dark and light theme.** :menuselection:`File --> Preferences...` on the
   main window has a colour scheme *system* (following the operating system),
   *light* or *dark*. On a dark scheme the canvases, the symbol previews and
   the Design data panel draw on a dark background with the lightness of
   every colour inverted while its hue is kept, LaTeX renders included:
   black shows white, white fills show dark, red stays red. A change of the
   desktop scheme while SLiCAP runs is followed at once. The schematic
   style, and therefore every SVG and PDF export, keeps the document
   colours. See :doc:`/GUI/schematics/preferences`.

#. **Wires and junctions.** A selected wire turns to the selection colour
   with a dot on each vertex and a cross on the vertex being dragged, like a
   selected shape. The bounding box is gone. Two crossing wires do not
   connect. A junction placed on the crossing splits the wires there and
   connects them, and the dot appears because a connection now exists. See
   :doc:`/GUI/schematics/wiring`.

#. **Copy and paste across canvases.** One clipboard serves all open
   schematics and symbol editors. Components and wires paste from one
   schematic into another. Shapes, LaTeX labels and images paste between
   schematics and symbols. Pins and symbol texts paste between symbols, also
   between the two dialects. Pasted and newly placed items follow the cursor
   and are put down with a click. **R** and **M** rotate and mirror a
   component while it is being placed.

#. **NGspice schematics.** A ``.model`` block on a top-level NGspice
   schematic is now written into the netlist (in a subcircuit it already
   was). The SLiCAP and NGspice netlisters share one writer for the library,
   parameter and model blocks. The model dialog of an NGspice schematic
   offers the SPICE model types with empty parameter lines, because SPICE
   model parameters depend on the model level and are taken from the NGspice
   manual, not from SLiCAP. A voltage or current source with only a ``value``
   is netlisted with that value as its ``dc`` value. Every NGspice run
   reports in the log which netlist it uses and whether it was regenerated
   from the schematic. The heading of a model block on the canvas reads
   ``model`` in the font of the parameter block.

#. **Upright subscripts in every report format.** Every LaTeX, RST, MyST,
   Markdown and HTML snippet sets the subscripts that hold a letter upright
   on creation (``R_\mathrm{a}``, ``V_\mathrm{out}``). A numeric index such
   as ``p_1`` stays italic. The HTML report pages follow the same rule.
   Schematic labels and reports now use one convention. Reports have to be
   regenerated to pick it up.

#. **MS-Windows.** Fixes reported by the first Windows users:

   - The documentation links of the symbols and dialogs point to the current
     layout of the manual. They open the local copy of the manual first.
   - The instruction file writes paths with forward slashes. This removes
     the ``SyntaxWarning`` for a path such as ``"sch\Test.slicap_sch"``.
   - Writing the design-data manifest is retried while Windows still holds
     the file (``WinError 5``).
   - Table cells in the parameter and model dialogs are edited on an opaque
     background.

#. **GUI bug fixes.**

   - Run (F5) always executes the instruction file, also while a symbol
     editor has the focus.
   - A symbol file with an unusable symbol is still loaded. The unusable
     symbol is skipped with a note in the console.
   - The pin markers of a symbol (the circles in the symbol file that give
     the pin positions) are no longer drawn. They were rendered as black
     dots, invisible on a black wire, but a gap in every wire on a dark
     canvas.
   - Pins, symbol texts and pasted items are placed under the cursor, not at
     the origin.
   - A new symbol saved without a name is named after its file.
   - Save as writes the extension of the selected file type.

SLiCAP Version 6.0 release notes
================================

Version 6.0 will be the **tested** release: the design environment as it
stands in the 5.x line, verified end to end, plus the following analysis
work.

#. API part of the manual is updated now using SLiCAP schematics instead of KiCAD.

#. SLiCAP symbols for schematic capture with KiCAD, LTspice, gSchem, and Lepton-EDA
   are provided and supported by makeCircuit(). Working with schematic
   capture programs other than SLiCAP, however, is no longer documented. The last 
   tested version of KiCAD remains 9.1. From version 6, the use of schematic capture
   tools other than SLiCAP is deprecated.

#. **State-space representation** of the circuit equations:
   ``doStateSpace()`` returns the full (MIMO) realization dx/dt = A x + B u,
   y = C x + D u, obtained from the first-order MNA matrix by an exact
   reduction: the number of states equals the number of finite poles, also
   for capacitor loops, inductor cut sets, ideally coupled inductors and
   nullors. Improper outputs appear as a polynomial in the Laplace variable
   in D. Formatter method ``stateSpace()`` (LaTeX, RST, TXT), ``stateSpace2html()``
   and ``listStateSpace()``. A "State space" group in the GUI instruction
   editor. See the user guide page *SLiCAP state-space representation*.

#. **Physical state variables**: ``doStateSpace()`` names its states after
   capacitor voltages, inductor currents and the internal states of device
   models wherever the network allows it.
   
#. **Pole-zero analysis with the state-space engine.** The keyword
   ``method='state'`` on ``doPoles()``, ``doZeros()`` and ``doPZ()`` (and on
   ``doMatrix()``, ``doLaplace()``, ``doNumer()``, ``doDenom()`` for the
   first-order matrix) and the project setting ``ini.pz_method``. The
   default engine remains the determinant. 
   
#. Loop gain and servo function are computed by injection at the
   reference: the reference is replaced with an independent source of its
   own gain and its returned controlling quantity is detected (the loop
   stays closed), instead of from the return difference. For a matched reference pair with a conversion type
   each reference keeps its own gain, so that a gain mismatch shows up in 
   the cd and dc blocks like any other unbalance. Two loop gain references 
   without a conversion type, e.g. a balanced stage in
   an unbalanced amplifier, give the four modal loop gains ``loopgaintype``
   'dd', 'dc', 'cd', 'cc' (servo functions only for 'dd' and 'cc'). 
   
#. A separate exact core on Python's ``fractions`` module for the numeric
   path was built, measured and REMOVED: sympy's rational matrices were
   faster in every case.
   
#. Several bug fixes and speed improvements.

.. _v5-development-line:

SLiCAP Version 5.x release notes
================================

.. note::

   The 5.x series is the **development line of the design environment**.  The
   analysis engine is stable; the graphical environment is not finished yet:
   dialogs, menus and the on-disk layout of new features (subcircuit
   packages, instruction files) may still change until 6.0.  Projects and
   scripts written with the analysis functions are unaffected.

#. **Schematic capture GUI.** SLiCAP now includes its own schematic editor;
   KiCad, LTspice, gSchem, or Lepton-EDA are no longer required for drawing
   circuits (they remain supported). The GUI is started from the command
   line with ``slicap`` (full environment with instruction editing and
   simulation) or ``slicap-schematics`` (schematic editing only), or from
   Python with ``sl.startSchematic()``. It supports two schematic types:

   - **SLiCAP schematics** (``.slicap_sch``): symbolic analysis netlists
   - **NGspice schematics** (``.spice_sch``): numeric simulation netlists

   Features include netlist generation, drawing-size SVG/PDF export with
   LaTeX-rendered labels, hierarchical subcircuits, an instruction editor
   with analysis dialogs, and a log panel. See
   `Schematic capture <../schematics/index.html>`_.

#. **NGspice simulations from the GUI.** Instruction dialogs generate and
   run OP, DC, AC, TRAN, and NOISE analyses, including parameter stepping
   and per-instruction parameter overrides (``params=``).
   All values use SLiCAP notation (case-sensitive scale factors: ``m`` =
   milli, ``M`` = mega); SLiCAP translates automatically wherever values are
   written into NGspice input (``1M`` → ``1E6``). See
   `Value notation <../schematics/component_properties.html#value-notation-scale-factors>`_.

#. **Instruction editing, traces, axes and figures.** Analyses are composed
   through dialogs that offer only what the circuit has — its sources,
   detectors, loop-gain references and parameters — so an instruction is
   correct by construction. Results are turned into plots in three steps,
   each one statement in the instruction file:
   :menuselection:`Instruction --> Create / Edit Traces and Measurements…`,
   :menuselection:`Instruction --> Create / Edit Axes…` and
   :menuselection:`Instruction --> Create / Edit Figures…` (main window).
   All of these dialogs can **edit existing definitions**: pick a name, the
   fields prefill from the instruction file, and the regenerated statement is
   appended — the later definition wins when the file runs; removing the
   superseded line is up to you.

#. **Circuit objects are explicit.** A circuit object is created from its own
   schematic (:menuselection:`Instruction --> Create circuit object…`) and
   appended to the instruction file; instructions are then composed for the
   circuit objects of the schematic you are editing. One instruction file can
   hold the circuits and instructions of any number of schematics.

#. **Project management in the GUI.** The main window's File menu creates,
   opens, saves, and closes SLiCAP projects:

   - :menuselection:`File --> New project…` asks for a project name,
     directory, and author, generates the project ``main.py``, and runs it
     once to create the project structure and its ``SLiCAP.ini``.
   - :menuselection:`File --> Select project folder…` shows the project's files in a
     **Project panel** on the left; double-clicking a schematic opens it in
     the editor, any other file opens with its default application. A
     directory without a ``SLiCAP.ini`` offers to create a project there.
   - :menuselection:`File --> Save project` saves every open panel with
     unsaved content; :menuselection:`File --> Close project` returns to the
     welcome screen. One project is open at a time; switching projects
     prompts for unsaved work first.

#. **No more disk-wide search for installed programs.** SLiCAP no longer
   walks the disk looking for KiCad, LTspice, gEDA/Lepton-EDA or NGspice; on
   MS-Windows that search could take up to two minutes and broke whenever a
   program changed its installation layout. Detection is now non-interactive
   and cheap: programs on the search ``PATH`` are picked up, plus the default
   MS-Windows install locations (e.g. ``C:\Spice64\bin`` for NGspice).

   - The commands are stored in the ``[commands]`` section of
     ``~/SLiCAP.ini`` and can be edited there directly, or from the GUI with
     :menuselection:`File --> Edit main configuration file`; see
     `Installation <../userguide/install.html>`_.
   - The ``pywin32`` and ``windows_tools`` dependencies have been dropped.
   - A dedicated *Configure SLiCAP…* dialog (enter, auto-detect and test the
     program paths) is still to come.

#. **Faster startup.**

   - ``import SLiCAP`` no longer contacts the internet. The check for new
     releases moved to the GUI menu :menuselection:`Help --> Check for
     updates…` (also available as ``sl.ini.check_for_updates()``).
   - The built-in libraries are compiled once and cached
     (``~/SLiCAP_libcache.pkl``); repeated ``initProject()`` calls are
     nearly instant. The cache refreshes automatically when SLiCAP, sympy,
     or a library file changes.

#. `initProject() <../reference/SLiCAP.html#SLiCAP.SLiCAP.initProject>`__
   accepts an optional ``author`` argument that is stored in the project
   configuration file, e.g. ``sl.initProject("My project", author="Me")``.

#. **GUI refinements.**

   - Schematics open as tabs; each keeps the full canvas width.
   - Closing the last schematic returns to the welcome screen;
     :menuselection:`File --> Exit` (:kbd:`Ctrl+Q`) quits the application.
   - The main window and the schematic panel now have separate File menus:
     the main window creates/opens schematics, the schematic panel acts on
     its own schematic only (*Save schematic*, *Schematic properties…*,
     *Export netlist…*, *Print schematic…*, *Schematic drawing
     preferences…*).

#. **Packaging.** Dependencies are declared in ``pyproject.toml``. Install
   from source with ``python -m pip install .``. A ``requirements.txt``
   mirroring those dependencies is kept for the documentation build on
   GitHub, which installs from it.

Changed behaviour in the 5.x line
---------------------------------

These are corrections and design changes rather than additions; they can make
existing output or projects look different.

#. **``parDefs`` in the LaTeX formatter produced the wrong table.**
   ``LaTeXformatter.parDefs()`` listed the circuit's *elements* instead of its
   *parameter definitions* (the RST and HTML formatters were always correct).
   Reports that include a LaTeX ``parDefs`` table have to be regenerated: the
   table is now Name / Symbolic / Numeric, and considerably narrower.

#. **One entry point for expression typesetting.** The private
   ``_latex_ENG`` moved from ``SLiCAPhtml`` to ``SLiCAPlatex`` and is now the
   public ``exprLatex(expr)`` — the counterpart of ``symbolLatex(name)``,
   used by the report formatters and the schematic environment alike. The old
   name still resolves, so existing code keeps working.

#. **An expression that does not parse is no longer rendered.** A component
   value or table entry that is not a valid SLiCAP expression used to be
   passed to LaTeX as if it were LaTeX code, which silently typeset something
   wrong. Such a value now produces an error message and is shown as plain
   text.

#. **A subcircuit is a package in ``lib/``.** Saving a schematic as a
   subcircuit writes the library, the block symbol *and* the subcircuit's own
   schematic into the project's ``lib/`` folder, so the subcircuit can be
   copied into another project complete. Subcircuit schematics saved earlier
   in ``sch/`` are still found.

SLiCAP Version 4.0 release notes
================================

#. RMS noise calculations have been improved:

   - Integration methods can be selected
   - Noise weighting (filter) functions can be added
   
#. The netlist syntax and the matrix stamps of ``F``, ``H``, and ``HZ`` element models has been made SPICE-compatible. All SLiCAP symbol libraries, model libraries, and the netlist parser have been updated accordingly and are NO LONGER compatible with earlier versions.
#. Element branch current names have all been set to ``I_<refdes>``, where ``refdes`` is the reference designator of the element. This is NOT compatible with previous versions.
#. Improved output of noise and dcvar analysis for balanced circuits with ``convtype='dd'`` or ``convtype='cc'``. By default, paired noise or dcvar sources are renamed to common-mode or differential-mode sources.
#. Added `checyshev1Poly() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.chebyshev1Poly>`_ returns a normalized Chebyshev type 1 polynomial.
#. Added `filterFunc() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.filterFunc>`__ for creating unity-gain low-pass, high-pass, band-pass, band-reject, and all-pass transfer functions, based on normalized Butterworth, Bessel, and Chebyshev type-1 (pass-band ripple) polynomials.
#. Added `DIN_A() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.DIN_A>`__, which returns a DIN_A weighting funcion.
#. The code has strongly been simplified: the ``allResults`` object is replaced with a modified ``instruction`` object.
#. The function ``ini.dump()`` has been modified. It displays settings per section. Settings for a specific section are displayed after giving the section name as argument.

   .. code-block:: python

       >>> import SLiCAP as sl
       >>> sl.ini.dump("version")
       
       VERSION
       -------
       ini.install_version        = 4.0.11
       ini.latest_version         = 4.0.11
    
#. The execution of the ``reduce_circuit`` and the ``reduce_matrix`` options have been improved. ``reduce_matrix`` now also works for matrices that do not include Laplace expressions and it only performs multiplication and addition on symbolic expressions.
#. ``listPZ`` displays frequencies in rad/s if ``ini.hz=False``
#. Canceling of poles and zeros in `doPZ() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPZ>`__ also works for symbolic pole-zero analysis
#. RST and LaTeX snippets for tables are improved
#. RST snippet for equations now supports multiline expressions
#. The documentation has been updated. It automatically generates ``rst`` and ``LaTeX`` snippets by executing `manual.py <https://github.com/SLiCAP/SLiCAP_python/tree/main/docs/manual.py>`_ when running ``make html``.
#. Examples (Python scripts and Jupyter Notebooks) have been added to the `SLiCAP Examples reporitory <https://github.com/SLiCAP/SLiCAPexamples>`_
#. SLiCAP 4.0 has an improved interface with NGspice:

   #. Added a KiCAD SPICE symbol library with NGspice symbols for all standard NGspice devices (no Xspice devices yet)
   #. A simple python instruction for the following analysis types including (non-nested) parameter stepping:
   
      #. .OP
      #. .DC
      #. .AC
      #. .NOISE
      #. .TRAN
      
      These NGspice analyses return a dictionary with traces that can be plotted with the SLiCAP `plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`__ function, or added to an existing plot using `addTraces() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.addTraces>`__.
      
      The results of an operating point information (without parameter stepping) can be displayed on the KiCAD schematic and its ``svg`` and ``pdf`` image files.

#. Library files have been updated; some names of subcircuits modeling the noise behavior of CMOS devices have been modified. See     `Subcircuits with noise <../userguide/noise.html#subcircuits-with-noise>`__.  
#. The function ``_reduce_circuit`` and its associated ini setting ``ini.reduce_circuit`` have been removed. The improved matrix reduction algorithm made it obsolete. 
#. Clean-up code and minor bug fixes.
      
SLiCAP Version 3.5 release notes
================================

#. SLiCAP version 3.5 has an improved interface to LaTeX and Sphinx:

   - The `LaTeXformatter <../reference/SLiCAPlatex.html#SLiCAP.SLiCAPlatex.LaTeXformatter>`__ creates LaTeX snippets to be imported in `LaTeX <https://www.latex-project.org/>`_ documents.
   - The `RSTformatter <../reference/SLiCAPrst.html#SLiCAP.SLiCAPrst.RSTformatter>`__ creates ReStructuredText snippets to be imported in `Sphinx <https://www.sphinx-doc.org/en/master/>`_ generated websites.

SLiCAP Version 3.4 release notes
================================

#. SLiCAP 3.4 is compatible with KiCad 9

SLiCAP Version 3.3 release notes
================================

#. SLiCAP Version 3.3 is prepared for PyPi pip install:

   - Examples are no longer part of the package, they can be pulled of downloaded from `github <https://github.com/SLiCAP/SLiCAPexamples>`_.
   - Libraries are no longer placed in the ``~/SLiCAP/`` folder. Library locations are found in ``~/SLiCAP.ini`` under the section **[installpaths]**. Settings for symbol library locations in schematic editors (KiCAD, LTspice, etc.) need to be adjusted accordingly.

SLiCAP Version 3.2 release notes
================================

#. SLiCAP Version 3.2 is compatible with previous versions. The use of the *instruction* object for creating instructions, however, is deprecated and no longer described in this documentation.

#. Version 3.2.4 has a KiCAD library symbol, SLiCAP CMOS18 sub circuits, and extra math functions for the design of a feedback amplifiers' MOS input stage based on its noise performance.

   - KiCAD symbol: *XM_noisyNullor*
   - Use with SLiCAP library sub circuits: *MN18_noisyNullor* and *MP18_noisyNullor* for PMOS and NMOS, respectively
   - SLiCAP functions:

     - 'integrate_monomial_coeffs() see `integrate_monomial_coeffs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrate_monomial_coeffs>`__.
     - 'integrated_monomial_coeffs() see `integrated_monomial_coeffs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrated_monomial_coeffs>`__.
     - 'monomial_coeffs2html() see `monomial_coeffs2html <../reference/SLiCAPhtml.html#SLiCAP.SLiCAPhtml.monomial_coeffs2html>`__.

#. From version 3.2.3 the analysis time for large circuits has been considerably reduced. By default, two methods will be applied:

   #. Reduction of the circuit through elimination of all independent voltage sources that are not used as signal source or current detector.
   
      This circuit reduction can be switched off by setting 
      
      .. code::
      
          reduce_circuit = False
          
      in the **[math]** section of the ``SLiCAP.ini`` file in the project directory
      
   #. Reduction of the size of the MNA matrix before calculation of the determinant, for matrices with Laplace expressions.
   
      This matrix reduction can be switched off by setting 
      
      .. code::
      
          reduce_matrix = False
          
      in the **[math]** section of the ``SLiCAP.ini`` file in the project directory

#. KiCAD is the preferred schematic capture program for SLiCAP version 3.2. From version 3.2.3 Inkscape is no longer needed for creating image-size svg and pdf files of KiCAD schematics. SLiCAP uses dedicated Python scrips for this purpose.

#. The function *ENG(<number>, scaleFactors=False)* has been added to write numbers in enginering notation. It is used in the following functions:

   - elementData2html
   - params2html
   - expr2html
   - eqn2html
   - pz2html
   - specs2html
          
   If ``ini.scalefactors=True``, scale factors from :math:`y=10^{-24}\cdots P=10^{15}` are used. If ``ini.scalefactors=False`` and ``ini.eng_notation=True``, engineering notation will be used (powers of 10 are an integer multiple of 3).
    
   Application of this function is defined in the **[display]** section of the ``SLiCAP.ini`` file in the project folder. Default setting are:
   
   .. code::
 
       scalefactors = False
       eng_notation = True

#. The ``SLiCAP.ini`` files in the ``~/SliCAP/`` folder and in the project folder are automatically updated in case in which they are corrupted or incomplete.

.. image:: /API/img/colorCode.svg
