================================
Instructions and Circuit Objects
================================

A schematic is a *drawing*; an analysis is a *Python instruction*.  The editor
composes those instructions for you and appends them to the project's
**instruction file** — a plain Python script you can also edit by hand, run
from the command line, or import from a design script.

The instruction file
====================

The instruction file lives at the **project root** (not in ``sch/``), and it is
**project-level**: one file may hold instructions for several schematics.  Its
purpose is to produce variables — results, traces, figures — that design
scripts and reports import.

Running it (:menuselection:`Instruction --> Run`) does not execute the file
directly.  The editor generates a small ``main.py`` beside it that calls
``sl.initProject(...)`` and then imports your instruction file, so the file
itself stays import-safe: it has no side effects of its own and can be reused
from another script.

The main script
===============

A design is more than its analyses. Between two analyses a designer computes:
the compensation capacitance from the poles of the uncompensated loop gain,
the bias current from a noise budget. That computation needs sympy or numpy
and belongs in a Python file written in your own editor. The environment
divides the work so that every file has one owner:

* **Instruction files** are generated and edited by the GUI. Each one is a
  self-contained step: it creates its own circuit object, loads the
  specifications it needs, runs its instructions and makes its plots and
  snippets. It does not import another instruction file.
* **The main script** is yours, in any editor. It calls ``sl.initProject()``
  once, imports the instruction files in order, computes between them, and
  writes the values it finds into the specification CSV with
  ``sl.specs2csv()``. The ``main.py`` the editor generates is the trivial
  form of this script: one import.
* **The specification CSV** is the handover. The main script writes it, the
  next instruction file reads it.

A GUI-generated instruction therefore refers only to objects defined
earlier in the same file. Its analysis inputs are schematics and
specification CSV files, nothing else. Results leave an instruction file by
``import``; values enter it per instruction, through the parameter
substitution described below. Compose an instruction file after the main
script has run through the previous step, so that every specification it
needs is in the CSV.

.. code-block:: python

   # main.py, written by the designer
   import SLiCAP as sl
   sl.initProject("Compensated amplifier")
   specs = [sl.specItem("R_s", "source resistance", "50", "Ohm", "Interface"),
            sl.specItem("C_L", "load capacitance", "10p", "F", "Interface")]
   sl.specs2csv(specs, "specs.csv")      # the initial specifications
   import step1                          # LG1: the uncompensated loop gain
   C_f = design_equation(step1.LG1)      # your sympy work
   specs = sl.csv2specs("specs.csv")
   specs.append(sl.specItem("C_f", "compensation", C_f, "F", "Design"))
   sl.specs2csv(specs, "specs.csv")
   import step2                          # LG2: C_f taken from the specifications

Circuit objects
===============

Every SLiCAP analysis works on a **circuit object**, created from a schematic:

.. code-block:: python

   RC = sl.makeCircuit("sch/myFirstRCnetwork.slicap_sch")

Creating that object is an explicit, separate step:
:menuselection:`Instruction --> Create circuit object…` on the schematic's own
tab.  You choose the variable name (the schematic's name is offered); the line
is **appended** to the instruction file.

:menuselection:`Instruction --> Update schematic images…` on the main menu lets
you pick drawings of the project and appends one
``sl.updateImages("sch/<name>.slicap_sch")`` line per drawing, the export of
the schematic to its netlist and images without a circuit object. Placed after the figures it
exports the schematic with the plots the run has written (see
:doc:`/GUI/schematics/netlist_and_export`).

Two rules protect the file:

* **A name, once bound to a circuit, keeps its meaning.**  Re-using a name that
  already refers to another schematic's circuit is possible, but only after a
  warning that says what the name refers to now — instructions *above* the new
  line keep the old circuit, instructions *below* it get the new one.
* **Circuit objects are appended, never inserted at the top**, so adding one
  can never change the meaning of instructions that are already there.

You may create several circuit objects from the same schematic (to give them
different parameter definitions later); the editor asks before doing so.

Composing an instruction
========================

:menuselection:`Instruction --> Create / edit SLiCAP instruction…` opens a form
that composes one ``sl.do…()`` call: analysis type, circuit variable, result
variable, transfer, signal references, parameter substitution and stepping.
The call is appended to the instruction file when you press **Add instruction**.

The form is filled from the circuit itself: the *source*, *detector* and
*loop-gain reference* drop-downs offer exactly the elements and nodes that
circuit has, and the parameter fields offer its parameters.

The analysis groups are *Network equations*, *Laplace / DC*, *Poles / zeros*,
*State space*, *Noise / DC variance* and *Time*. The *State space* group
composes ``sl.doStateSpace()``, the full realization with every source an
input and every network variable an output; it takes no transfer, no
references and no stepping, only the conversion type, the parameter
substitution and the numeric flag. The *Poles / zeros* group (and
``doMatrix()``) offers a *method* selector: *default* follows the project
setting ``ini.pz_method``, *det* uses the determinant, *state* the exact
state-space engine; only a non-default choice is written into the call.

.. important::

   **The editor only composes instructions for the schematic you are editing.**
   The circuit variable drop-down lists the circuit objects of the active
   schematic, and *Edit existing* lists only the instructions that address
   them.  An instruction belonging to another schematic is edited from that
   schematic's tab.

   This keeps what you see and what is emitted in step: the lists offered are
   always built from the drawing in front of you.  If the active schematic has
   no circuit object yet, the editor says so and points you at
   *Create circuit object…* rather than silently using another schematic's
   circuit.

   Knowledge of the rest of the instruction file is used for **name conflicts
   only** — never to address or modify another schematic's circuit objects or
   instructions.

The restriction applies to the *editor*, not to the file: a hand-written
instruction file may mix circuits and instructions of any number of schematics
in any order, and it will run exactly as written.

.. _parameter-substitution:

Parameter substitution
----------------------

The **Parameter substitution** group lists every parameter of the circuit,
defined and undefined, one row each, and asks where the analysis takes its
value from:

* **undefined**: nothing is substituted. The element keeps its value
  attribute, ``C_f`` stays ``C_f`` in the result. This is ``pardefs=None``.
  A circuit definition ``C_f = 0`` is a definition like any other, so
  choosing *undefined* is the way to keep a parameter symbolic.
* **circuit**: the definition from the schematic, read when the instruction
  runs. Offered only where the circuit defines the parameter. The value is
  shown next to the button.
* **specs**: the value of the specification with the same symbol in the
  **Spec file** chosen above the table, read when the instruction runs, so a
  value your main script writes later is used. Offered only where that CSV
  has the symbol with a value.
* **user**: a value typed in the row. Always offered. A row set to *user*
  without a value blocks **Add instruction** and says why.

The start, stop and number of steps of a *lin* or *log* **Parameter
stepping** have the same source selector: *manual* for a number, *circuit*
or *specs* for a parameter with a numeric value, shown with its value. A
parameter of the specs that the circuit does not have gets a row in this
table, set to *specs*, so the ``pardefs`` pass its value with the run. The
same fields exist on the NGspice instruction dialog.

**Set all to** applies one choice to every row at once. *specs first* takes
the specification where there is one, else the circuit definition, else
leaves the parameter undefined. *circuit first* takes the circuit definition
where there is one. *all undefined* clears every substitution. The dialog
opens in the preset chosen under :menuselection:`File --> Preferences...`,
*specs first* unless you change it. Single rows are changed afterwards.

The emitted call stays short where it can. All rows undefined: no
``pardefs`` argument. Every defined parameter from the circuit and nothing
else: ``pardefs='circuit'``. Any other selection:

.. code-block:: python

   SPECS_specs = sl.csv2specs("specs.csv")
   LG2 = sl.doLaplace(cir, transfer='loopgain', lgref='E1',
                      pardefs=sl.selectPars(cir, SPECS_specs, circuit=["R_s", "C_L"], specs=["C_f"]))

The CSV is loaded once per instruction file, into ``SPECS_<file stem>``.
``selectPars()`` reads the circuit definitions and the specification values
when it runs and raises an error that names the parameter when a
specification has disappeared or lost its value. See `selectPars()
<../../API/userguide/analysis.html#the-parameter-definitions>`_ in the API
manual.

Editing an existing instruction
===============================

Editing is **append-only**: selecting an instruction under *Edit existing*
loads it back into the form, and pressing **Add instruction** appends the
regenerated call under the same result name.  The earlier line stays in the
file; delete it in the editor if you no longer want it.  Nothing is rewritten
behind your back.

NGspice schematics
==================

NGspice schematics have no circuit object. Their netlist step is a bare
line:

.. code-block:: python

   sl.makeCircuit("sch/myAmp.spice_sch")

It writes ``cir/myAmp.spice_cir``, and the instructions name the circuit:
``sl.op("myAmp")`` runs that file as it is. :menuselection:`Instruction -->
Create netlist…` on the schematic's own tab appends the line, once per
schematic. An NGspice instruction or control section can only be added
when the instruction file has that line, as a SLiCAP instruction needs a
circuit object; the editor says so otherwise. A netlist left in ``cir/`` by
an earlier session does not count: the file, not the disk, says which
netlists the run makes.

:menuselection:`Instruction --> Create / edit NGspice instruction…`
composes the call, and
:menuselection:`Instruction --> Create / edit NGspice control section…`
adds a ``.control`` block.  Everything above about the instruction file, the
append-only editing and running through ``main.py`` applies unchanged.

The dialog's **Compatibility (behavior)** check boxes select NGspice's
compatibility flags for the run, PSpice, LTspice, HSPICE, Spectre, Spice3,
KiCad, EAGLE, and "whole netlist (a)".  Without the last one a syntax flag
applies to included libraries only; a model in PSpice syntax inside the
circuit needs PSpice together with "whole netlist", which becomes
``behavior="psa"`` in the instruction file.  See `Compatibility mode
<../../API/userguide/ngspice.html#compatibility-mode>`_ in the API manual.

Every numeric setting of an analysis, a stop time, a frequency limit, the
limits of a DC sweep, starts with a source selector: *manual*, *circuit*
or *specs*. With *manual* you type a number in SLiCAP notation. With
*circuit* or *specs* a list offers the parameters of that source that
have a numeric value, the ``.param`` definitions of the netlist, or the
items of the spec file chosen in the parameter table, and the value of
the chosen parameter is shown next to it. A parameter without a numeric
value is not offered.
A value that must be computed from other values is computed in the main
script, and its numeric result is written to the specs. The instruction
file names the parameter, ``sl.tran("amp", "1n", "t_stop", ...)``, and the
run reads its value when it runs, so a new value in the specs is used
without an edit. A parameter of the specs that the netlist does not have
gets a row in the parameter table below, set to *specs*, so the ``params``
argument passes it with the run. See `Simulation settings from parameters
<../../API/userguide/ngspice.html#simulation-settings-from-parameters>`_ in
the API manual.

The **Circuit parameters** group is the parameter table described under
:ref:`parameter-substitution`, with the same presets and the same preference.
It lists every parameter the netlist needs: the ``.param`` definitions and
every name used in an element value, a source stimulus or the expression of
a ``.param``. *circuit* means the ``.param`` definitions that the netlist
export wrote from the schematic's parameter table; a parameter the netlist
uses without defining it has no *circuit* position and takes its value from
the specs, else from you. There is no *undefined* position, because NGspice
cannot run with an undefined parameter: the dialog does not add the
instruction while a parameter has no value, and the run stops before NGspice
starts when the deck still lacks one. When every parameter keeps
its circuit definition the call has no ``params`` argument. Otherwise the
dialog writes the same call as for SLiCAP, with the circuit name in place of
the circuit object:

.. code-block:: python

   SPECS_specs = sl.csv2specs("specs.csv")
   AC1 = sl.ac("amp", "dec", 20, 1, 1e9,
               params=sl.selectPars("amp", SPECS_specs, circuit=["R_s"], specs=["C_f"]))

The **NGspice options** table sets simulator options for this instruction
only: convergence aids, tolerances, iteration limits, the integration method.
Each row becomes an ``option name = value`` command in the control section,
and the dialog writes them as ``options={"rshunt": "1e12"}``.  A row with an
empty value is a flag, such as ``noopiter``.  Vendor macro-models of op-amps
often have internal nodes without a DC path to ground; NGspice then reports
"singular matrix" and every operating-point method fails.  A shunt resistance
of ``1e12`` ohm from every node to ground (``rshunt``), or a minimum
conductance of ``1e-10`` (``gmin``), gives such a model an operating point
without disturbing the results.  See `Simulator options
<../../API/userguide/ngspice.html#simulator-options>`_ in the API manual.
