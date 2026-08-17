============
Introduction
============

Why this environment exists
===========================

SLiCAP is a circuit-analysis program driven from Python.  Everything it can do
is available by writing instructions — and that is where the friction has
always been.  A designer who knows exactly which transfer to evaluate still has
to get the syntax right: the correct analysis function, a circuit object, a
transfer type with the source, detector and loop-gain reference it requires,
parameter substitution, stepping.  A misspelt detector or a transfer that does
not go with the chosen gain type costs an edit-run-read cycle every time.

The Structured Electronic Design Environment removes that burden.  It is a
graphical front end for **SLiCAP** (Symbolic Linear Circuit Analysis Program,
https://www.slicap.org) and **NGspice** in which you draw the circuit and
compose the instructions through dialogs.  The dialogs offer only what the
circuit in front of you actually has — its independent sources, its detectors,
its controlled sources, its parameters — and only the fields the chosen
analysis accepts.  An instruction is then correct by construction rather than
by proofreading.

What it does **not** do is design your circuit.  There is no automatic
topology, no optimiser, no hidden reasoning about your amplifier.  Design
remains yours; the environment removes the clerical work around it.

What it produces
================

The environment's product is an **instruction file**: a plain Python script at
the root of your project.

.. code-block:: python

   import SLiCAP as sl

   Vamp = sl.makeCircuit("sch/Vamp.slicap_sch")

   GG   = sl.doLaplace(Vamp, pardefs='circuit', numeric=True)
   LG   = sl.doLaplace(Vamp, transfer='loopgain', pardefs='circuit', numeric=True)
   PZ1  = sl.doPZ(Vamp, pardefs='circuit', numeric=True)

Nothing about that file is special: it is readable, editable by hand, and
version-controllable.  It has no side effects of its own, so a design script can
simply import it and use the results:

.. code-block:: python

   import instructions as instr

   f_c   = sl.findServoBandwidth(instr.LG.laplace)["mid"]
   poles = instr.PZ1.poles

That is the point of the whole environment.  The dialogs are a convenience; the
script they write is the deliverable, and it puts the full symbolic and numeric
analysis of your circuit at your disposal — for design automation, for
verification, and for documentation that is generated rather than retyped.

How the pieces fit together
===========================

A **schematic** is drawn once and serves twice: it is the source of the netlist
*and* the publication figure, so the circuit you analyse and the circuit in your
report cannot drift apart.

From a schematic you create a **circuit object** — one explicit line in the
instruction file — and for that object you compose **instructions**.  Running
them produces **results**: symbolic expressions, poles and zeros, noise, time
responses, operating points.

Results become **traces**, traces are placed on **axes**, and axes are arranged
into **figures**, each one statement in the same file.  Results, tables and
figures are then exported as **report snippets** — LaTeX, RST or HTML — that a
document includes directly.  Nothing is copied by hand, so a changed component
value propagates from the drawing to the published figure in one run.

Two analysis backends live in the same project.  **SLiCAP** answers the
symbolic, design-oriented questions: what does this transfer look like in terms
of the component values, where do the poles go, how much noise does this
topology cost.  **NGspice** answers the numeric, verification questions with
device models: does the biasing hold, what does the real transistor do.  The
same schematic types, the same project layout and the same instruction file
serve both.

What you can rely on
====================

* **Files are the truth.**  Schematics, netlists, libraries, instruction files
  and results are ordinary files in your project; the environment never becomes
  the only place your design lives.
* **Projects are self-contained.**  Everything a schematic references lives
  inside the project and is addressed relatively, so a project survives being
  moved, archived or handed over (see :doc:`/GUI/project/project_files`).
* **Nothing is rewritten behind your back.**  Editing is append-only: the
  dialogs add statements, and existing ones are left as they are for you to
  keep or delete.
* **The GUI is optional.**  Netlisting, export and every analysis are available
  from scripts and from the command line.  The environment makes the work
  easier; it never becomes a dependency of your design.

Where to go next
================

* :doc:`getting_started` — install, first project, the parts of the window.
* :doc:`/GUI/schematics/the_canvas`, :doc:`/GUI/schematics/placing_symbols`, :doc:`/GUI/schematics/wiring` — drawing a circuit.
* :doc:`/GUI/schematics/component_properties`, :doc:`/GUI/schematics/labels_ports_parameters` — giving it
  values, names and interfaces.
* :doc:`/GUI/instruction/instructions` — circuit objects, composing analyses, the instruction
  file.
* :doc:`/GUI/schematics/netlist_and_export` — netlists, SVG/PDF figures, the command line.
* :doc:`/GUI/hierarchical_blocks` — subcircuits and descending into them.
* :doc:`/GUI/project/project_files` — the project layout and what is stored where.
