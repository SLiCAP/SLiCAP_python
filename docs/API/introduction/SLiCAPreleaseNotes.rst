====================
SLiCAP release notes
====================

.. image:: /API/img/colorCode.svg

SLiCAP version 6.4 release notes
================================

Version 6.4 completes the 6.3 work on derivations and converted
circuits, and makes the schematic editor ready for a long stable period:
its menus are named by function, a selected group turns and mirrors as
one, the labels of a turned component stay beside it, and a round of
canvas fixes follows the first weeks of use.

#. **Exact fractions in derivations.** The formatter methods ``eqn()``,
   ``eqnInline()``, ``expr()`` and ``matrixEqn()`` of the LaTeX and RST
   formatters, and the functions ``exprLatex()``, ``roundN()`` and
   ``rational2float()``, have an argument ``intlen``. A rational coefficient
   whose numerator and denominator have at most ``intlen`` digits is shown
   as a fraction, for instance :math:`\frac{1}{2}` and :math:`\frac{1}{4}`
   in a derivation, while longer ones become floats. The default ``0`` keeps
   the earlier behaviour: all rational coefficients are shown as floats.

#. **Several equations in one display.** The LaTeX and RST formatters have
   the method ``eqns(pairs, label="", order=None, intlen=0)``. It shows a
   list of (left-hand side, right-hand side) pairs as one numbered display,
   one equation per line, aligned on the equal sign, for instance the
   solution of a set of equations: ``eqns(solution.items())``.

#. **Converted variables in lower case.** The differential-mode and
   common-mode variables, detectors, references and noise sources of a
   balanced circuit carry the suffixes ``_d`` and ``_c``, in lower case like
   the conversion types ``dd``, ``dc``, ``cd`` and ``cc``: the pair
   ``V_outP``, ``V_outN`` becomes ``V_out_d`` and ``V_out_c`` (it was
   ``V_out_D`` and ``V_out_C``). A detector given as a pair is renamed
   automatically, so scripts that pass pairs need no change; scripts that use
   the converted names themselves must use the lower-case suffixes.

#. **Names with several subscripts.** A name with several subscript parts,
   such as ``V_in_d`` or ``I_noise_R1``, is displayed with its parts
   separated by commas, each part upright when it holds a letter:
   :math:`V_{\mathrm{in},\mathrm{d}}`. It was shown as
   :math:`V_{in d}`, italic and with the parts run together.

#. **Analyses with a conversion type use the complete converted matrix.**
   All instructions other than ``doMatrix()`` now compute with the complete
   converted matrix, the conversion blocks included. The conversion type
   selects the mode of the source (second letter) and of the detector (first
   letter): ``dd`` and ``cc`` give the differential-mode and common-mode
   results, ``dc`` and ``cd`` the conversion transfers, which were not
   available before. The new keyword argument ``use_submatrix=True`` (all
   instructions, and the analysis dialog of the schematic editor) restores
   the earlier behaviour for ``dd`` and ``cc``: the analysis of the
   differential-mode or common-mode equivalent network alone. For fully
   balanced circuits the transfers do not change. Results that do change:
   the transfers of circuits that are not fully balanced (they now include
   the mode conversion), and ``doPoles()``, ``doZeros()`` and
   ``doStateSpace()`` with ``dd`` or ``cc``, which now include the poles of
   both modes unless ``use_submatrix=True`` is given.

#. **Controlled sources with node references.** The schematic editor has two
   new symbols, ``VCVS-ref`` and ``VCCS-ref``: a voltage-controlled voltage
   or current source with only its output terminals. The controlling nodes
   are entered as references (ref 1: + node, ref 2: - node), so that the
   controlling voltage can be taken anywhere in the drawing without wires.
   The netlist line is the same as that of ``VCVS`` and ``VCCS``.

#. **Bug fixes.**

   - The orthogonality test of a balanced circuit (attribute
     ``orthogonal`` of a result with a conversion type) returns ``False``
     whenever the block ``M_dc`` or ``M_cd`` has an entry that is not
     identically zero. For a symbolic entry such as ``C_1*s/2 - 1/(4*R_2)``
     it returned ``None``.
   - The conversion matrix of a balanced circuit is exact. Its entries 1/2
     were Python floats, so that every symbolic converted matrix carried
     floats, for instance ``0.5/R_1`` instead of :math:`\frac{1}{2R_1}`. The
     results were numerically the same.

   - ``convtype='dc'`` and ``convtype='cd'`` return the right blocks of the
     converted matrix again. Version 6.0 had swapped them: ``dc`` returned
     the common-mode equations in the differential-mode variables, the block
     of ``cd``. ``dc`` now returns the differential-mode equations in the
     common-mode variables, the path by which a common-mode stimulus
     produces a differential-mode response, as the manual states. Analyses
     with ``dd`` and ``cc``, the orthogonality test and the loop gain types
     were not affected.
   - Roots are displayed as roots again. The rounding of expressions for
     display (``roundN()``) converted every rational number into a float,
     the exponent of a root included, so that, for instance, the coupling
     term ``k*s*sqrt(L_a*L_b)`` of coupled inductors was shown as
     ``(L_a L_b)^0.5``. The exponents 1/n and -1/n of roots are now kept.
     Other rational exponents, such as 41/50, and rational coefficients are
     still shown as floats. The computations were not affected.
   - The LaTeX table of symbolic poles and zeros (``pz()`` of the LaTeX
     formatter) typesets the roots as mathematics again. The roots were
     passed to the table as LaTeX text, in which every underscore was
     escaped, so that, for instance, ``C_2`` was printed as ``C\_{2}``. The
     column of symbolic roots is now headed :math:`s` [rad/s] or
     :math:`s` [Hz], for poles and zeros alike. All headers of the table are
     set as mathematics, with upright units, so that they keep their shape
     in an italic environment such as an example.
   - The Design data panel lists the results of ``doMatrix()`` with
     ``method="tc"``: ``Nr``, ``Cr``, ``Rr`` and ``reactances`` appear under
     the result, next to ``M``, ``Iv`` and ``Dv``.

#. **Group rotate and mirror.** R and M on a selection of several items
   turn or mirror them as one, about the grid point nearest the centre of
   the selection. The wires that stay behind follow the moved pins. A
   single selected item turns or mirrors in place, as before.

#. **Menus named by function.** The schematic editor's *Place* and *Draw*
   menus are replaced by four menus that say what their items do.
   *Circuit* holds what reaches the netlist: symbol, wire, net label,
   junction, library, subcircuit symbol, parameters, source, detector
   and loop gain reference, model definition. *Insert* holds the objects
   that exist elsewhere and follow the runs: the figures and LaTeX
   snippets of the Design data, image files, and on a poster the drawings
   of the project. *Draw* holds the hand-made annotation that nothing
   updates: shapes, text, hyperlinks and typed LaTeX. *Document* holds
   the page: the document properties block and the border. The entries
   for the Design data's objects are called *Figure from design data*
   and *LaTeX from design data*; the typed one is *LaTeX text*. The symbol editor's *Place* menu is now *Symbol*. The shortcuts
   are unchanged.

#. **Labels of turned and mirrored components.** The labels of a
   component keep their column beside the symbol when it is turned, and
   move to its other side when it is mirrored, as if the symbol stood
   upright. They turned with the symbol, so the column became a row of
   overlapping texts on every turned component. A label moved by hand
   keeps its place relative to the symbol's footprint. The file stores
   the label offsets in this new meaning and marks it; older files are
   converted when they are read, so nothing moves in an existing
   schematic.

#. **Canvas fixes from the test round of 21 October.**

   - Ctrl+A selects everything on the canvas: the components, wires and
     annotations.
   - Ctrl+click on a selected item takes it out of the selection.
   - R and M turn and mirror a pasted group before it is placed, about
     the point under the cursor.
   - A group dragged by one of its wires keeps the component labels on
     their components. They were moved twice.
   - The junction dots follow a dragged component or group. They jumped
     to their place only at the drop.
   - A junction dragged off a component pin shows the bridge to the pin
     while dragging, as a wire end does.
   - A LaTeX fragment is drawn with exact glyph boxes, so the raised A
     of ``\LaTeX`` no longer sticks out of its box, and its selection
     frame lies inside its repaint rectangle. Dragging one left ghosts
     and a hole in the grid.
   - The schematic tab that comes to the front takes the keyboard. A
     paste after a tab click went to the hidden schematic, where it
     waited for a click, and Escape could not cancel it.

Version 6.4.1
-------------

#. **Faster opening of a schematic with LaTeX rendering.** A schematic
   opened for the first time, for instance in a cloned project, has an
   empty render cache. Its LaTeX labels, tables and blocks are now
   rendered together, in one pdflatex run and one dvisvgm run. Before,
   each of them took its own pair of runs, about 0.4 s. A schematic with
   25 labels took about 10 s to open, with the window frozen. It now
   takes about 1 s. The labels look the same as before. An existing
   render cache stays valid. LaTeX fragments are still rendered one by
   one. An equation number in a fragment would otherwise depend on the
   fragments before it.

#. **A poster follows its drawings.** A poster places schematics and other
   posters by their file name, so it follows those files. When a poster
   opens, the drawings that changed since their last export are exported
   again and shown. The same happens when you save such a drawing in
   another tab, and before :menuselection:`File --> Export`. Before, a
   poster showed the old exports until the instruction file ran
   ``updateImages()``. A drawing that cannot be exported keeps its previous
   image, and a message names it.

#. **An install no longer exports the images again.** An image is exported
   again only when one of its sources changed: the schematic, its sidecars,
   the operating-point results or the linked images. A new version of
   SLiCAP therefore leaves the figures of a book as they are, until you
   change their drawings. ``updateImages(..., force=True)`` exports them on
   request. The netlist still counts SLiCAP itself. ``makeCircuit()``
   rebuilds it once after an install, so that a correction of the
   netlister reaches it.

#. **Bug fix.** Choosing a drawing to place on a poster switched the
   editor's log to the log file of that drawing. The log now stays with
   the poster.

#. **One drag for everything on the canvas.** A component, a group, a
   wire moved by its body, a label of a component and a net label were
   dragged by four different mechanisms, each with its own rules. They
   are now one gesture of the schematic editor. The rules are the same
   for every drag: the attached wires and junction dots follow, a pin
   or wire end pulled off a pin shows and gets a bridge wire, and the
   move is one undo step. Three things changed as a result. A wire
   moved by its body takes a wire that ends on its interior with it,
   where it was left behind before. Moving a net label can be undone.
   A group whose wires were merged at the drop stays selected. The
   cursor is the arrow during every drag, where a group showed the
   cross.

#. **The command block is gone.** The schematic editor once had a text
   block for raw netlist lines. It lost its menu entry long ago, no
   schematic was found that holds one, and the parameter, model and
   analysis blocks cover what it did. Its remains are removed from the
   editor, the file format and the netlister.

#. **Bug fix: ground overrides a net name.** A net that you had named and
   then connected to a ground symbol kept its name on the schematic, and
   stayed renamable, while the netlist already used node 0. The wires of
   such a net now show the name 0 and are locked, as the wires of a net
   with a port symbol were. A ground on the same net as a port wins.
   Removing the ground gives the net its name back.

#. **Bug fix: a saved file updates the tab that shows it.** Saving a
   schematic under the name of a file that is open in another tab, after
   the overwrite warning, left that tab showing the old drawing. The tab
   now reloads the file.

Version 6.4.2
-------------

#. **A net name belongs to one segment.** A net name used to be copied
   onto every segment of its net, and only the net-label dialog kept the
   copies in step. Deleting a middle segment left two drawn nets that the
   netlist still joined by their common name. Renaming one part and
   reconnecting showed two names until a double-click. The name now lives
   on the segment you named, where its label is. When a net falls apart,
   the part with the label keeps the name and the other part gets a
   number. Deleting the labelled segment removes the name. Joining two
   named nets opens a dialog that asks which name the net keeps, with
   Undo to revert the connection. A netlist of a net with two names is
   refused, which can only happen in a file written before this version.
   Typing a net name checks "Display net name on schematic".

Version 6.4.3
-------------

#. **Bug fix: the first save of a subcircuit.** The Create Subcircuit
   dialog opened by Save keeps the name read-only, so that Save keeps the
   name and only settles the node order. On the first save there is no
   name yet, and the empty field could not be filled. The name is now
   editable whenever the subcircuit has none.

Version 6.4.4
-------------

#. **selectPars().** The new function ``selectPars(cir, specList,
   circuit=[...], specs=[...], user={...})`` returns a ``pardefs``
   dictionary with the parameters named per source: the definition of the
   circuit, the value of the specification item with the same symbol, or a
   value given in the call. Parameters not named stay undefined. The
   circuit definitions and the specification values are read when the
   instruction runs, so a value a design script writes to the specification
   CSV is used by the next analysis. A parameter named under two sources, a
   circuit parameter without a definition and a specification without a
   value raise an error that names the parameter. The circuit may also be
   the file name of an NGspice circuit; its ``.param`` definitions are then
   the circuit source, and the ``params`` argument of the NGspice analyses
   accepts the returned dictionary next to the list of pairs.

#. **Parameter substitution in the instruction dialog.** The pardefs group
   of the SLiCAP instruction dialog lists every parameter of the circuit
   and asks per row where its value comes from: undefined, circuit, specs
   or user. Positions without a value are greyed out. "Set all to" applies
   *specs first*, *circuit first* or *all undefined* to every row, and the
   preset the dialog opens in is a preference. The emitted call is
   ``pardefs='circuit'`` or no ``pardefs`` where that says the same, and
   ``pardefs=sl.selectPars(...)`` otherwise. The table of value literals,
   with its "Load circuit definitions" button, is gone: it copied values
   into the file at compose time. The NGspice instruction dialog has the
   same table in place of its ordered parameter list, without the
   *undefined* position: *circuit* is the ``.param`` definition from the
   schematic, and only rows that take a specification or a user value
   reach the ``params`` argument.

#. **Instruction files and the main script.** The manual describes how
   GUI-generated instruction files and a designer's own script work
   together: instruction files are self-contained steps owned by the GUI,
   the main script imports them and computes between them, and the
   specification CSV carries values from the script to the next step.

#. **Bug fix: circuit object in snippets.** The snippet dialog emitted the
   literal ``cir`` for the element data, parameter definitions and
   undefined parameters tables, whether or not the instruction file
   defined it. It now offers the circuit objects the file defines. The
   Result list no longer accepts typed names, for the same reason.

#. **Snippet dialog wording and manual.** The kind "Text output (txt file
   + include)" is called "Text output". The manual has a page on snippets
   that explains the two lines it emits.

Version 6.4.5
-------------

#. **Bug fix: crash after the net-name dialog.** Joining two named nets
   and choosing the name could end in a segmentation fault at the next
   repaint, not every time. The wire that lost its name hid its label, and
   the label is part of the wire's bounding rectangle. The change was not
   announced to the scene index, so when the merge that follows removed
   that wire, a stale entry stayed behind. The wire now announces every
   label change before it happens.

#. **Bug fix: a chosen net name could disappear.** When the connecting
   wire lay exactly over the segment that carried the chosen name, the
   duplicate removal dropped whichever segment came second, the owner
   included, and the net had no name left. The segment that carries a name
   is now the one that stays.

Version 6.4.6
-------------

#. **Bug fix: a percent sign in a specification description.** The text
   cells of the LaTeX tables, among them the description of a
   specification, escaped only the underscore. A ``%`` in a description
   started a LaTeX comment that swallowed the rest of the row and the
   whole next row. A text cell is now text with inline maths: outside
   ``$...$`` spans the characters ``%``, ``&``, ``#`` and ``_`` are
   escaped, unless they are escaped already, and a ``$...$`` span is
   passed to LaTeX unchanged. "Output voltage at $I_{max}$" renders with
   its subscript, and "0.1% of final value" renders as typed. An unclosed
   ``$`` is shown as text.

#. **Boltzmann's constant is a circuit parameter.** The thermal-noise model
   of a resistor uses ``k``. The netlist never names it, so the circuit did
   not list it: ``k`` was inserted at execution time, just before the
   parameter substitution. ``pardefs='circuit'`` therefore substituted it,
   but the instruction dialog and ``selectPars()`` never saw it, and a
   ``selectPars()`` dict always left it symbolic. The circuit now claims
   ``k`` for every resistor with a non-zero ``noisetemp``, like ``T``. It
   appears in ``parDefs``, in the parameter tables and in the instruction
   dialog, where it can be set to circuit, specs, user or undefined. A
   ``.param k=...`` in the netlist still wins.

#. **Bug fix: the instruction dialog showed an outdated circuit.** The
   circuit data for the dialog were built once per schematic and kept for
   the whole session. Parameters deleted from the schematic were still
   offered. The circuit is now rebuilt every time the dialog opens.

#. **Unsaved schematic changes before an instruction.** The instruction
   dialogs netlist the schematic file on disk, so an unsaved edit is not in
   what they offer. A schematic with unsaved changes now asks to be saved
   first, the same rule as Run.

#. **Row colour of LaTeX tables in the snippet dialog.** The table methods
   of the LaTeX formatter take ``color``, but the snippet dialog left it at
   its default. A **Row colour** field now offers the colours of
   ``preambuleSLiCAP.tex`` and ``none``. The default ``myyellow`` emits no
   argument, ``none`` emits ``color=None``, another choice its name. The
   field appears only for methods that take a colour, never for RST.

#. **One editor for the stimuli of an NGspice source.** The Properties
   dialog of an independent source on an NGspice schematic showed the
   rows ``value``, ``ac`` and ``tran`` next to the button that opens the
   **Source stimuli** dialog. Both edited the same stimuli. The rows are
   gone. The Properties dialog keeps the refdes, the orientation, the
   symbol and the operating-point check-box. The **Source stimuli** dialog
   sets the DC value, the AC magnitude and phase, and the transient
   waveform, each with its own **Show** check-box for the canvas label.
   The DC value serves every analysis, so its field is named **DC VALUE**.
   A double-click on a dc, ac or tran label of a source on an NGspice
   schematic opens that dialog too.
   A source saved by an earlier version is converted when the schematic
   is loaded: its ``value`` becomes the DC value, the ``?`` reminder of an
   unset value is dropped, and the schematic's frozen symbol cache is
   updated at the next save.

#. **The netlist extension names the dialect.** A SLiCAP schematic
   ``sch/x.slicap_sch`` now writes ``cir/x.slicap_cir``, an NGspice
   schematic ``sch/x.spice_sch`` writes ``cir/x.spice_cir``. Both wrote
   ``cir/x.cir`` before. A project with a SLiCAP and an NGspice schematic
   of the same name then ran NGspice on the SLiCAP netlist, whichever was
   written last. A netlist written by hand keeps ``.cir``, in either
   dialect. ``makeCircuit()`` accepts ``.slicap_cir`` next to ``.cir``. An
   NGspice instruction names the circuit, as before: ``sl.op("x")`` runs
   ``cir/x.spice_cir``, else ``cir/x.cir``. The old ``cir/x.cir`` of a
   schematic stays behind as a dead file.

#. **The netlist step of an NGspice schematic is explicit.** An NGspice
   instruction no longer regenerates the netlist when the schematic is
   newer. The line ``sl.makeCircuit("sch/x.spice_sch")`` in the
   instruction file writes the netlist, as a circuit object does for a
   SLiCAP circuit; the manual's example already had it. The schematic
   editor's Instruction menu has **Create netlist…**, which appends that
   line, and an NGspice instruction or control section can only be added
   when the instruction file has it. The instruction functions report a
   missing netlist with the line to add.

#. **Every parameter an NGspice netlist needs is listed.** The parameter
   table of the NGspice instruction dialog listed the ``.param``
   definitions only. A schematic with ``R1 out 1 {R_s}`` and no ``.param``
   showed an empty table. The table now lists every name used in an
   element value, a source stimulus or a ``.param`` expression. A name
   without a ``.param`` has no *circuit* position and takes its value from
   the specs, else from the user. The NGspice functions check the deck
   before the run and name every parameter that is still undefined,
   instead of leaving the search to the NGspice log.

#. **Bug fix: operating-point annotation read the wrong netlist.** The
   schematic editor takes the net names of an operating-point run from the
   netlist that produced the raw file. It asked for ``cir/<stem>.cir`` by
   name, while an NGspice schematic now runs ``cir/<stem>.spice_cir``. It
   now uses the same lookup as the run: ``.spice_cir``, else the
   hand-written ``.cir``.

#. **Bug fix: netlist snippet from the Browse button.** ``ltx.netlist()``
   and ``rst.netlist()`` take a file name in the project's cir folder and
   add the folder themselves. The snippet dialog's Browse button filled an
   absolute path, so the snippet pointed nowhere. For a netlist snippet
   Browse now opens the cir folder and fills the file name only. A path
   with a directory part is refused there. A snippet from any other file
   still takes a full path.

#. **updateImages() takes the schematic file.** ``sl.updateImages()``
   accepted a bare circuit name and looked it up as ``sch/<name>.slicap_sch``,
   then ``sch/<name>.spice_sch``, then a poster. With a SLiCAP and an
   NGspice schematic of one name it silently took the SLiCAP one. It now
   takes the file: ``"sch/<name>.slicap_sch"``, ``"sch/<name>.spice_sch"``
   or ``"posters/<name>.slicap_poster"``. A circuit object made from a
   ``.slicap_sch`` is still accepted, it carries that file. A bare name
   raises a ``ValueError`` that names the three forms. Instruction files
   with ``sl.updateImages("<name>")`` must be changed to the file.

#. **Update schematic images moved to the main Instruction menu.** The
   entry lived on the schematic tab's Instruction menu and emitted only
   the active schematic. It now lives on the main menu and offers every
   drawing of the project: the schematics of ``sch/`` and ``lib/`` and the
   posters. Each pick appends one ``sl.updateImages("<file>")`` line. A
   line the file already has is not repeated.

#. **A drawing name is unique in a project.** Every drawing, a schematic
   in ``sch/`` or ``lib/`` or a poster, writes ``img/<name>.svg`` and
   ``.pdf`` into the one ``img/`` folder. Two drawings with one name, for
   instance ``amp.slicap_sch`` and ``amp.spice_sch``, overwrote each
   other's images, and the last export won without a message. New poster,
   Save as and the subcircuit save now refuse a name that another drawing
   of the project has, and name that drawing. Existing files are not
   touched. A project with two drawings of one name should rename one of
   them.

#. **Schematic properties: the subcircuit box.** Its text read "Save this
   schematic as a SLiCAP subcircuit (.lib)". The box applies to both
   dialects, and the file is ``.slicap_lib`` or ``.spice_lib``. It now
   reads "Save this schematic as a subcircuit".

#. **Snippet dialog: the Expression list.** For ``eqn``, ``eqnInline`` and
   ``expr`` the dialog offered only ``<name>.laplace``, and only for the
   results of ``doLaplace()``, ``doNumer()``, ``doDenom()`` and ``doDC()``.
   A ``doTime()`` or ``doNoise()`` result was never offered. The list now
   comes from the Design data of the file's last run: every expression
   attribute of every result, and every variable that holds an expression.
   The list is empty until the file has run. The field stays editable.

#. **Insert → LaTeX snippet file…** places a LaTeX snippet file of the
   project (``tex/SLiCAPdata/``) on a schematic or poster. The item
   follows the file: it re-renders after a run, when the drawing opens,
   before an export and with ``updateImages()``, so a snippet written by
   a script outside the GUI stays up to date too. A missing file gives a
   warning, not an error. Insert → LaTeX from design data…, which places
   a snippet object by name, is unchanged.

#. **Listing snippets hold the text of the file.** ``file()`` and
   ``netlist()`` of the LaTeX and RST formatters wrote a path into the
   snippet, as ``\lstinputlisting`` or ``literalinclude``. LaTeX and
   Sphinx resolve such a path from the folder of the document, which
   differs per report: a book has its main document above the chapter
   folders. The snippet now holds the lines of the file as a
   ``lstlisting`` environment or a ``code-block``, read when the run
   happens. It compiles from any folder, and the listing is the file as
   it was at the last run. The line range and the first line number work
   as before; ``lineRange`` also takes ``"3"`` and ``"1-2, 8-10"``. A
   file that cannot be read stops the run with a clear message. In the
   snippet dialog, Browse for a file starts in the project folder and
   stores the project-relative path. Its *Listing style* field offers
   SLiCAP's listing styles, ``slicap`` and ``latex``, before the
   languages: a style carries the colours of the preamble, a bare
   language such as ``python`` does not.

#. **Bug fix: the Border dialog gave portrait only.** Its Format row had
   no Landscape box, so a paper format always set the portrait size and
   a landscape poster could not be made from the border. The box is
   there now, for paper formats, and the dialog opens on the format of
   the present border.

#. **Bug fix: makeCircuit() of an NGspice subcircuit schematic.** A
   ``.spice_sch`` saved as a subcircuit exports ``lib/<name>.spice_lib``
   and no circuit netlist. ``makeCircuit()`` nevertheless made the HTML
   circuit page and printed ``could not open 'cir/<name>.spice_cir'``. It
   now skips the page and returns ``None``, as for a ``.slicap_sch``
   subcircuit.

#. **Bug fix: "Create the netlist first" with the netlist line present.**
   The NGspice instruction dialog reads the netlist lines from the
   instruction file. The file inventory kept one entry per first argument,
   so ``sl.updateImages("sch/x.spice_sch")`` hid the earlier
   ``sl.makeCircuit("sch/x.spice_sch")`` of the same schematic. Bare calls
   are now identified by function and argument together.

#. **Simulation settings from parameters.** A numeric argument of an
   NGspice analysis, the stop time of ``tran()``, a frequency limit of
   ``ac()`` or ``noise()``, the limits of ``dc()``, the start, stop and
   number of steps of a ``lin`` or ``log`` ``step``, may name a parameter
   instead of a number. The run resolves
   it from the ``.param`` definitions of the netlist with the ``params``
   argument on top, so the value comes from the circuit, the specs or a
   user value through ``selectPars()``, like a component value. The value
   is read when the line runs. A parameter without a value stops the run
   before NGspice starts, with a message that names it. The limits of
   ``sweepData()`` may name a parameter of the result in the same way. In
   the NGspice instruction dialog every setting field has a source
   selector, *manual*, *circuit* or *specs*, and for a parameter source a
   list of the parameters with a numeric value, from the netlist or from
   the chosen spec file, with the value of the chosen one shown. A spec parameter the netlist does not have gets a
   row in the parameter table, so ``params`` passes it with the run. The
   sweep limits of the Traces dialog offer the circuit parameters of the
   result and every numeric item of the spec file. A specification the
   instruction did not select is passed to the sweep with its own
   ``params`` argument. The sweep fields of the Traces and the Axes
   dialogs open empty, and all three values are required.
   The start, stop and number of steps of a SLiCAP ``stepdict`` resolve
   from the ``pardefs`` of the instruction in the same way, and the
   stepping fields of both instruction dialogs offer the parameters.

Version 6.4.7
-------------

#. **A schematic moves with its subcircuit box.** A schematic saved in
   ``sch/`` and then ticked as a subcircuit got its package in ``lib/``
   and left the ``sch/`` file behind: two drawings of one name, which
   the unique-name rule refuses to save, so Save failed and a project
   switch could not proceed. The next save now moves the schematic:
   into ``lib/`` when the box is ticked, back into ``sch/`` when it is
   unticked. A question before the save names the files that the move
   removes and says that the drawing is moved, not copied; Cancel
   leaves everything as it is. The old file goes with its sidecars, and
   on the way back the library file too. A drawn block symbol is kept.
   Save as under another name still copies. A poster that shows the
   schematic finds it at the new place.

Version 6.4.8
-------------

Many changes of version 6.4.8 follow the comments of a workshop. The bug
fixes say what was wrong and how it is solved. The additions describe what
is new.

Bug fixes
~~~~~~~~~

#. **Large dialogs fit the screen.** Some dialogs were taller than a laptop
   screen. Their OK button could then not be reached. Now these dialogs
   scroll their contents. Their buttons stay visible below the scrolling
   part. A dialog opens as large as its contents, but never larger than the
   screen. This applies to the drawing and the application preferences, the
   SLiCAP and NGspice instruction dialogs, the component properties, the
   source stimuli, and the Traces, Axes and Transfer function dialogs.

#. **Parameter tables when LaTeX fails.** LaTeX can be installed but unable
   to compile a table, for instance when a package is missing. The preview
   of the circuit parameters or of a model definition then disabled OK. The
   table could not be placed at all. Now the preview offers *Place as plain
   text*.

#. **The project folder.** *File > New project* took the project name as a
   folder name. It created that folder in the working directory of the
   program, wherever the program had been started. Now the name is only the
   title of the project. The dialog asks for a location, an existing folder
   chosen with *Browse*, and a folder name. The line *Project folder* shows
   the folder that *Create project* will make.

#. **The Type column of the specifications.** The Type column was a
   drop-down box in each row. :kbd:`Tab` did not pass through it. The last
   column did not fill the width of the table. Now the Type column is an
   ordinary cell. :kbd:`Tab` passes through it. The new sorting of the
   specifications includes it. The last column fills the width of the table.

#. **Old text behind an edited cell.** At a display scaling of 125 %, a
   cell being edited showed the old text behind the new one. This happened
   in the specifications, the subcircuit parameters and the border formats.
   Now the edited cell hides the old text, as it already did in the other
   tables.

#. **The parameters of the transmission line.** The list of the
   transmission line ``T`` in ``SLiCAPprotos.py`` named a parameter ``is``.
   NGspice does not know that parameter. Now the list names ``ic``, the
   initial condition.

#. **A port takes the name of its net.** A port without a name stayed
   unnamed, even on a net that already had a name. It was then no pin of
   the subcircuit. Now such a port takes the name of its net. The name can
   come from a net label or from another port. From then on the port names
   the net, as if you had typed the name. The ground name ``0`` is not
   taken over.

#. **Pin names on subcircuit symbols.** On a wide box, a pin near a corner
   could get its name beside its stub, outside the box. Now the side of
   each pin name follows from the box itself. The names also sit a little
   further from their pins.

#. **A label switched on later goes under its neighbour.** A label without
   a stored position went to its default place. That place could be far
   from labels that had been moved. An example is an NGspice instance
   parameter switched on after *Tools > Update symbols from library*. Now
   such a label goes one line below the previous label, in the column of
   that label. Nothing changes when no label was moved.

#. **The Traces, Axes and Figures dialogs read one instruction file.**
   These dialogs collected the results of every instruction file of the
   project. A result with the same name in another file, such as an older
   ``TR1``, then added its signals and traces. Now they offer only the
   results of the instruction file being edited. An instruction file that
   has never been run offers nothing.

#. **New names are free in the whole instruction file.** *Create circuit
   object* and the Traces, Axes and Figures dialogs propose a name for a
   new object. They could propose a name that the instruction file already
   used. They knew only the names assigned with an ``sl.`` call. So a plain
   assignment such as ``gain = 5``, a merged trace set such as ``TR3 =
   {**TR1, **TR2}``, an ``import numpy as np`` or a loop variable did not
   count. Now every name that the file binds counts as used. Such a name is
   not proposed. In *Create circuit object*, typing it gives *Name in use*.
   Two new measurements in the Traces dialog no longer get the same name.

#. **Quitting ends the instruction runs.** Quitting the GUI with figure
   windows of earlier runs still open could crash the program. Now quitting
   ends the running instruction run and every earlier run with open figure
   windows. Their figure windows close.

#. **No warning at every run without slicap_det.** A project can ask for
   the determinant method ``MECPP``. Without the program ``slicap_det``,
   SLiCAP uses ``ME`` instead. It then printed a warning at every run. Now
   it uses ``ME`` without a warning. A ``slicap_det`` that is configured but
   does not work still gives a warning.

#. **An out-of-date netlist.** A netlist did not count as out of date after
   a change of the symbol library. Now it does.

#. **A poster that linked to itself.** A new poster, once saved, could
   offer itself as one of its own links. Now it does not.

#. **The license in pyproject.toml.** ``pyproject.toml`` gave the license
   in a form that setuptools refuses from February 2027. Now it reads
   ``license = "MIT"``. The build therefore requires setuptools 77 or
   newer.

#. **numpy and numba.** SLiCAP allowed any numpy from 2.4 on. pip could
   then install a numpy that the installed numba does not support, and
   numba stopped importing. Now SLiCAP requires numba 0.66 or newer. pip
   then keeps numpy within the range that numba supports. numba runs the
   system-level simulator.

#. **Long periodic pulse responses.** ``step2PeriodicPulse()`` builds a
   pulse train from delayed copies of a step response. Each copy is
   switched on at its delay. Since version 6.0 a long train could show
   gaps in its plot. Before its switch, a delayed copy was still evaluated,
   and its exponential overflowed. Zero times infinity gave no number. This
   happened when the magnitude of the fastest pole, in rad/s, times the
   longest delay exceeded about 709. Now each copy is evaluated only after
   its switch. The symbolic expression is unchanged.

#. **Descend keeps the typed values.** *Descend into subcircuit* closed the
   properties dialog as *Cancel* does. A value typed just before was lost
   without a message. Now *Descend* applies the values, as *OK* does, and
   then opens the subcircuit. *Undo* takes the change back in one step.

#. **Pin names in the exported image.** A generated subcircuit box shows
   the names of its pins on the canvas. The SVG and PDF export left them
   out, so the box came out empty. Now the export writes them at the same
   places as the canvas.

#. **Instructions written by a dialog.** When a dialog added the line
   ``import SLiCAP as sl`` to an instruction file, the editor lost its undo
   history and its mark for unsaved changes. Text typed but not yet saved
   could then be lost without a question. Now the line is added as an
   ordinary edit, together with the instruction. *Undo* takes both back in
   one step. The line goes after a module docstring and after ``from
   __future__`` imports, which must stay first. The dialogs for traces,
   axes, figures and snippets now also add the line when it is missing. A
   dialog that added an instruction to a file whose last line held only
   spaces wrote it on that line, indented. Now every added instruction
   starts on a line of its own.

#. **Save keeps the characters of the instruction file.** Save and Run
   wrote the instruction file through Qt's plain-text export. A line
   separator (U+2028) became a new line. A no-break space (U+00A0) became
   a plain space. This changed characters you had not touched. A string
   with a line separator then no longer compiled. Now the editor writes the
   characters as they are. A file written in another editor can hold a
   no-break space or a line separator in its code, outside a string or a
   comment. Code copied from a PDF can carry them. Before, Save replaced
   such a character without a message, and the file ran. Now Run stops
   with a Python error that names the character. Without the GUI, Python
   stopped on such a file already. Text pasted into the instruction pane
   or the LaTeX fragment dialog still comes in with plain line breaks and
   spaces. A paragraph separator (U+2029) in a file still becomes a line
   break. The editor cannot keep it.

#. **Text in generated instructions reads back as typed.** The Traces,
   Axes and Figures dialogs and the parameter tables wrote a backslash as
   it was. An axis name ``$\tau$`` then read back as a tab and "au". These
   dialogs also turned a double quote into a single quote. No dialog wrote
   a line break correctly, so a free-text snippet of two lines did not run.
   One function now writes the typed texts of these dialogs and of the
   snippet and NGspice dialogs. It doubles every backslash, so a LaTeX command reaches the plot as typed. It writes a
   line break as ``\n``. It chooses the quotes as you would by hand:
   ``"Gain 'open loop'"`` and ``'Gain "open loop"'``. Only a text with both
   kinds of quote changes: its double quotes become single quotes. A
   backslash in a dialog field is always a LaTeX backslash. A title typed
   as ``Line 1\nLine 2`` therefore shows the ``\n``. Write such a title in
   the instruction file by hand.

#. **A subcircuit Title with a space.** A Title that is not a valid
   subcircuit name, such as "Input stage", stopped the save. Save opened
   *Create Subcircuit* with the name locked, and the dialog then refused
   that name. Cancel was the only way out. After a Title change on a saved
   subcircuit, Save even wrote ``lib/Input stage.*`` without a question.
   Its ``.subckt`` line read ``stage`` as a port. Save now opens the
   dialog with the name editable whenever the Title is not a valid name.
   The manual and the tooltip of the Subcircuit box give the rule: a
   letter, then letters, digits or underscores. A package whose name breaks
   the rule, such as a ``lib/Input stage.*`` written by 6.4.7, therefore
   needs a new name at its next Save. Save then writes a copy under the new
   name. The old package stays in ``lib/``. Remove it by hand, and update
   the parents that use it.

#. **Dimmed labels in the export.** The canvas draws a dimmed
   operating-point label grey and italic. Examples are the placeholder
   "I: —" of a V source or an inductor and a stale current value. SVG, PDF,
   Print and command-line images showed these labels grey but upright. They
   are now italic in the export too. All other texts export unchanged.

#. **Fonts in print and in placed drawings.** Print, and schematics and
   posters placed on a sheet, drew serif and monospace text in the default
   sans font. The component parameters are an example. Qt read the font
   family of the exported SVG, such as "DejaVu Sans Mono, monospace", as one
   unknown name. SLiCAP now tells Qt which font that name stands for. These
   views now use the same fonts as the canvas. The SVG and PDF files do not
   change. The fault dates from 6.2.4.

#. **No console windows during a PDF export.** Under MS-Windows, every
   PDF export flashed console windows. The PDF is made with svglib.
   Versions of svglib before 2.1.0 split the font name "DejaVu Sans Mono,
   monospace" at every space. They then looked up "DejaVu", "Sans" and
   "Mono" with the program ``fc-match``, one console window each. SLiCAP
   now requires svglib 2.3.0 or newer, and with it reportlab 4.4.3 or
   newer.

#. **NGspice on MS-Windows.** The example on the installation page named
   ``ngspice.exe``. That program opens a window of its own at every run.
   The page now names ``ngspice_con.exe``, which runs without a window. If
   the ``ngspice`` line in ``~/SLiCAP/SLiCAP.ini`` ends in ``ngspice.exe``,
   change it to ``ngspice_con.exe`` in the same folder.

#. **Menu paths in messages and in the manual.** Version 6.4 named the
   menus by function. Some texts kept the old paths. After *Tools > Import
   symbols from file* the message named *Place -> Symbol*. Now it names
   *Circuit > Symbol…*. The note after saving a symbol names *Tools > Load
   selected symbols from library*. The tooltip of the subcircuit check box
   names *File > Save schematic*. The manual names the menus as they are.
   Its tables of the schematic menus and the main menus are complete again.
   The manual described a dialog *File > Configure SLiCAP…* that was never
   built. It now names *File > Edit main configuration file*, which opens
   ``~/SLiCAP/SLiCAP.ini`` in the system's text editor. The installation
   page still named the old location ``~/SLiCAP.ini`` of that file. It now
   names ``~/SLiCAP/SLiCAP.ini``.

Additions
~~~~~~~~~

#. **An icon for SLiCAP.** The GUI shows its own icon: the nullor of SLiCAP
   on a light badge. It appears in the title bar, in the taskbar and in the
   task switcher. On Windows, SLiCAP gets a taskbar button of its own. It no
   longer shares the button and the icon of Python. The HTML report of a new
   project shows the same icon as its logo. An existing project keeps its
   logo. The icon files are in ``SLiCAP/files/icons``: an SVG, PNG pictures
   from 16 to 256 pixels, and a Windows ``.ico`` file.

#. **Help > Create shortcut.** This new entry puts SLiCAP in the launcher of
   the system, with its icon. On Windows it makes a shortcut in the start
   menu and on the desktop. From the start menu, SLiCAP can be pinned to the
   taskbar. A pinned SLiCAP and the running one then share one taskbar
   button. On Linux it makes the entry ``slicap.desktop``, which shows
   SLiCAP in the applications overview. The shortcut starts SLiCAP with the
   Python environment that runs the GUI when the shortcut is made. In an
   Anaconda environment on Windows, it first activates that environment.
   Started from the shortcut, SLiCAP has no console window. Its messages
   then go to ``~/SLiCAP/gui.log``. The programs it starts, such as
   pdflatex and NGspice, open no console window either.
   See :doc:`/GUI/schematics/schematic`.

#. **LaTeX renders in the background.** The editor no longer waits while
   LaTeX renders a label. A placed, edited or pasted component shows its
   labels as plain text at once. The LaTeX replaces the text when it is
   ready. Meanwhile the status bar shows *Rendering n LaTeX labels*. A
   label is never replaced while a mouse button is down. Opening a
   schematic, undo, redo, export and print wait for their labels. The
   window stays responsive during that wait. After half a second a window
   says that LaTeX is rendering. It also says that MiKTeX may ask to
   install a package in a window of its own. *Continue with plain text*
   ends the wait. The components then get their LaTeX labels when the
   rendering is done. Parameter tables and LaTeX fragments keep their plain
   text until the schematic is opened again. A value whose LaTeX does not
   compile keeps its plain text. Scripts and the command line render as
   before. Before, the editor waited about half a second per label on
   Linux. With MiKTeX it waited longer. A question of MiKTeX to install a
   package could appear behind the editor's window. The editor then seemed
   to hang. See :doc:`/GUI/schematics/schematic`.

#. **Line numbers and zoom in the instruction pane and the log.** The
   instruction pane shows line numbers. They are the line numbers of
   Python's error messages. :kbd:`Shift+Enter` therefore starts a new line,
   as :kbd:`Enter` does. In the instruction pane and in the log, :kbd:`Ctrl` with the mouse wheel, :kbd:`Ctrl++` and :kbd:`Ctrl+-`
   change the text size. :kbd:`Ctrl+0` restores the default size. Each
   pane keeps its size for the next session. The LaTeX fragment dialog uses
   the size of the instruction pane.

#. **Tables you type in.** :kbd:`Tab` on the last cell adds a row and moves
   to it. This holds for the specifications, the circuit parameters, the
   parameters of a model definition and of a subcircuit, and the border
   formats. A click on a column header of the specifications sorts the rows
   by that column. A second click sorts them the other way round.

#. **Help > Keyboard shortcuts.** This new entry lists every keyboard
   shortcut of the menus and of the canvas, such as :kbd:`R` to rotate and
   :kbd:`M` to mirror. The list is read from the program, so it always
   matches it.

#. **NGspice instance parameters.** Every NGspice symbol offers the
   instance parameters that ``SLiCAPprotos.py`` lists for its device type.
   Examples are ``temp``, ``tc1`` and ``noisy`` of a resistor, and ``ic`` of
   a transistor. They are empty by default. They are hidden on the
   schematic. An empty parameter is not written to the netlist.
   ``onoff = 0`` of a diode or a transistor writes the keyword ``off``. An
   ``ic`` of several values, such as ``vbe,vce``, is written as one
   comma-separated value. On a schematic made with an older version,
   *Tools > Update symbols from library* adds the new parameters to the
   placed components.

#. **Instruction > Transfer function.** This new entry on the Instruction
   menu of a SLiCAP schematic puts a Laplace transfer function into the
   Design data without a circuit. Its dialog adds one line to the
   instruction file, in one of three forms:

   - a filter of a classic family:
     ``H1 = sl.filterFunc("butterworth", "bp", 2, f_c="1k", B=100)``
   - one section by type, frequency and quality factor:
     ``H1 = sl.sectionFunc("bp", "10k", Q=5)``
   - a typed expression: ``H1 = sl.transferFunc("1/(1+s*T)")``

   A frequency or a quality factor typed as a name stays a symbol in the
   transfer function.

#. **Traces with millions of points.** A trace with millions of points,
   such as a long NGspice transient, is now drawn reduced. Plotting and
   zooming then stay fast. ``ini.plot_points`` sets the number of bins,
   4000 by default. A trace with more than twice that number of points is
   reduced. The visible range is cut into these bins. Each bin contributes
   its minimum and its maximum. The envelope and every peak therefore stay
   visible, as on an oscilloscope. Plotting only every n-th point would
   hide narrow peaks. Every zoom or pan repeats the reduction. A close zoom
   therefore shows the samples themselves. The A/B cursors read the full
   data. The crosshair reads the reduced line. A saved image holds the
   reduced trace of the full range. Only traces with monotonic x values are
   reduced, such as time and frequency sweeps. ``plotpoints = 0`` in the
   ``[plot]`` section of ``SLiCAP.ini`` switches the reduction off. See
   :doc:`/API/userguide/plots`.

#. **filterFunc() with a centre frequency.** ``filterFunc()`` also takes
   one frequency ``f_c``. For a low-pass, high-pass or all-pass filter,
   ``f_c`` is the -3 dB corner. For a band-pass or band-stop filter,
   ``f_c`` is the geometric centre of the band. These two filters also take
   the bandwidth ``B``. It is the difference between the two -3 dB
   frequencies. ``f_low`` and ``f_high`` still work. A frequency, the
   bandwidth or the ripple may now be text in SLiCAP notation, such as
   ``"10k"``. It may also be a name, which stays a symbol. See
   :doc:`/API/userguide/laplace`.

#. **sectionFunc() and transferFunc().** These two new functions serve
   *Instruction > Transfer function*. Scripts can use them as well.
   ``sectionFunc(f_type, f_0, Q)`` returns the Laplace transfer function of
   one filter section. Without ``Q`` it is a first-order low-pass,
   high-pass or all-pass section with corner frequency ``f_0``. With ``Q``
   it is a second-order section, which can also be a band-pass or a
   band-stop. ``transferFunc(expr)`` turns a transfer function typed as
   text in SLiCAP notation into an expression in ``ini.laplace``.

#. **Discrete-time transfer functions.** New functions turn a Laplace
   transfer function into a discrete-time one, with the sample period
   ``Ts``.

   - ``laplace2z()`` returns the z-domain transfer function.
   - ``laplace2sections()`` realises it as a cascade of first-order and
     second-order sections.
   - ``coeffs2sections()`` does the same from numeric coefficients.
   - ``sectionsZ()`` returns the z-domain transfer function of such a
     cascade.
   - ``coeffs2taps()`` returns the samples of the impulse response: the
     taps of a FIR filter.
   - ``z2fourier()`` returns the frequency response of a z-domain transfer
     function.

   The z-domain variable is ``ini.z``. The key ``z`` in the ``[math]``
   section of ``SLiCAP.ini`` sets it. It is ``z`` by default.

SLiCAP version 6.3 release notes
================================

Version 6.3 gives access to the **time-constant matrix** of a network,
makes symbolic state-space realizations readable and small, and lets the
formatters print the terms of an equation in the order they were written.

#. **Reactive elements of a network.** ``doMatrix()`` with
   ``method="tc"`` returns the first-order (expanded) MNA matrix and, in
   addition, the incidence matrix of the reactive elements (``.Nr``), the
   matrix of their values (``.Cr``) and their names (``.reactances``), with
   :math:`\mathbf{C} = \mathbf{N}_r \mathbf{C}_r \mathbf{N}_r^T`. They give 
   the time-constant matrix 
   :math:`\mathbf{T} = \mathbf{N}_r^T \mathbf{G}^{-1} \mathbf{N}_r \mathbf{C}_r`
   of the    network. See :doc:`/API/userguide/matrices`.

#. **Readable state-space realizations.** ``doStateSpace()`` chooses the
   state coordinates on the pivots of the reduced row echelon form of the
   matrices in each elimination round. A coordinate is then a network
   variable, or a combination with simple coefficients such as the voltage
   across a floating capacitor, and the element values no longer pile up
   in the coordinates from round to round. The elimination itself works
   on fractions of polynomials in the element values that are kept reduced
   at every step, so the expressions stay compact and a rank is decided
   exactly. The poles, the transfers and the feedthrough are unchanged.
   Symbolic realizations of networks with fixed reactances come out much
   smaller and faster: a transimpedance amplifier with a phantom-zero
   capacitor takes 0.06 s instead of 50 s. See :doc:`/API/userguide/statespace`.

#. **Order of the terms in equations.** The method ``eqn()`` of the LaTeX
   and RST formatters, and the function ``exprLatex()``, have an argument
   ``order``. By default the terms appear in sympy's order. With
   ``order='none'`` they keep the order of the expression, so that, for
   instance, ``G + s*C`` with the matrices ``G`` and ``C`` built as an
   unevaluated sum is printed as written, and not as ``s*C + G``. Other
   values are passed to sympy's ``latex()``, for example ``'lex'``.

#. **Bug fixes.**

   - The dialogs of the parameter table, the library block, the model
     table and the analysis block open again. The 6.2.5 and 6.2.6
     packages lacked the module of their LaTeX scale field.
   - Undo after moving a parameter table, a library block, an analysis
     block or a model table of a schematic saved before 6.2.5 no longer
     enlarges it. The conversion of the LaTeX scales of such a file is now
     done once, when the file is read. It was repeated at every undo, redo
     and re-render.

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
   which name a schematic without its folder, still work. The dialog's one
   action is *Place*. The *Open* button, which opened the drawing in its
   own tab, is gone: a drawing is edited from the project tree, not from
   a poster. Choosing a
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

#. **One font for the canvas, the SVG and the PDF.** The generic families
   sans-serif, serif and monospace are drawn with the DejaVu fonts that
   come with matplotlib. The editor loads them, the SVG names them with
   the generic fallback, and the PDF embeds them. Text embedded in a
   symbol, the plus and minus of a source or the pin names of a
   subcircuit, uses one family on the canvas and in the export, and the
   SVG carries an explicit baseline for it. Before, the canvas, the
   browser and the PDF used three fonts for the same text, and the PDF
   placed symbol text visibly off.

#. **Export netlist of a subcircuit.** :menuselection:`File --> Export
   netlist…` on a subcircuit schematic writes the subcircuit library to
   ``lib/``, for SLiCAP and NGspice alike, the file the headless export
   and Save write. It wrote a flat netlist into ``cir/``.

#. **Crash prevention.** An item removed from a drawing during an event,
   such as a label rebuilt after its own double-click, is released only
   when the event has been fully handled. Releasing it at once could
   crash the editor on the next click.

#. **Fixes from a user's report on 6.1.0.** The placement ghost of a
   symbol, and the ghosts of a paste, are drawn in the display colours,
   so they are visible on the dark canvas. R during a paste no longer
   rotates the copied originals. The paste is the new selection, and R
   after placing it turns the pasted items. A label moved away from its
   default position keeps that position on the pasted copy. The project
   folders of SLiCAP.ini, such as an image folder outside the project,
   are honoured by the editor and by the headless export since 6.2.

#. **One LaTeX scale per schematic.** The Rendering group of the
   preferences has one **LaTeX scale**, 150 % by default. At 100 %, LaTeX
   is drawn at its natural size of 10 pt in a drawing at 2 units per mm,
   the default ``sch_scale``. The same percentage therefore gives the same
   text size relative to the symbols in every project. The component
   labels always use this scale. LaTeX fragments, parameter and model
   tables, and the analysis and library blocks use it as well, unless the
   user gives them a scale of their own: their dialogs have a **LaTeX
   scale** field with a **Default** box. The separate scales of the
   reference designators, the parameter labels and the tables are gone.
   Schematics made with an earlier version are converted on loading,
   and no drawing changes size. The script ``tools/set_latex_scale.py``
   of the repository sets one scale for all schematics and posters under
   a folder, and puts all their LaTeX items on Default. See
   :doc:`/GUI/schematics/preferences`.

#. **Image export without a netlist.** ``updateImages()`` exports the SVG
   and PDF of a schematic or poster without building a netlist, so a
   drawing that is not a valid circuit, such as one with a ``?`` value, is
   exported as well. It no longer writes the netlist, it no longer has the
   argument ``cirTitle``, and it returns the path of the SVG. The PDF is
   converted from the SVG that was just written. ``makeCircuit()`` still
   writes the netlist, the SVG and the PDF together. When the netlist
   cannot be built, it writes the images first and then reports the
   netlist errors.

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
   - A click on a wire where it enters a component's selection box
     selects the wire. It selected the component, so a short wire
     between two pins could not be selected or given a net name.
   - Save as offers the current file name, and the Open and Save as
     dialogs no longer list the cache directories of the schematics.
   - A click near the end of a wire that belongs to a group selection
     drags the group. It dragged the wire end and replaced the selection
     by that wire. A wire end is dragged only when the wire is the only
     selected item.
   - A segmentation fault after mirroring a component and then editing
     its properties is fixed. The labels of a mirrored component were
     left behind in Qt's spatial index, and the editor crashed on the
     next mouse move after the properties dialog had rebuilt them.

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
