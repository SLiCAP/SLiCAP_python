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

Circuit objects
===============

Every SLiCAP analysis works on a **circuit object**, created from a schematic:

.. code-block:: python

   RC = sl.makeCircuit("sch/myFirstRCnetwork.slicap_sch")

Creating that object is an explicit, separate step:
:menuselection:`Instruction --> Create circuit object…` on the schematic's own
tab.  You choose the variable name (the schematic's name is offered); the line
is **appended** to the instruction file.

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

Editing an existing instruction
===============================

Editing is **append-only**: selecting an instruction under *Edit existing*
loads it back into the form, and pressing **Add instruction** appends the
regenerated call under the same result name.  The earlier line stays in the
file; delete it in the editor if you no longer want it.  Nothing is rewritten
behind your back.

NGspice schematics
==================

NGspice schematics have no circuit object: they reference the exported netlist
by name, so :menuselection:`Instruction --> Create / edit NGspice instruction…`
composes its call directly, and
:menuselection:`Instruction --> Create / edit NGspice control section…`
adds a ``.control`` block.  Everything above about the instruction file, the
append-only editing and running through ``main.py`` applies unchanged.
