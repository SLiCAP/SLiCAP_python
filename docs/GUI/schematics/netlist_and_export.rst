=====================
Netlist & Export
=====================

A finished schematic produces three things: a **netlist** for analysis, and
**SVG** / **PDF** figures for documents.

From the GUI
============

* :menuselection:`File --> Export netlist…` (:kbd:`Ctrl+E`) writes the
  netlist to ``cir/``: ``.cir`` for a SLiCAP circuit, ``.sp`` for an NGspice
  circuit. For a subcircuit schematic it writes the subcircuit library to
  ``lib/`` instead, ``<title>.slicap_lib`` or ``<title>.spice_lib``, the
  same file as the headless export and as saving the subcircuit.
* :menuselection:`File --> Export SVG…` writes a vector figure.
* :menuselection:`File --> Export PDF…` writes a PDF figure.
* :menuselection:`File --> Print schematic…` (:kbd:`Ctrl+P`) prints the drawing.

.. figure:: /GUI/img/export_netlist.png
   :alt: An exported netlist
   :width: 70%

   The schematic and the netlist it produced, side by side.

From the command line
=====================

The same outputs can be generated without opening the window — useful for build
scripts and Makefiles:

.. code-block:: console

   $ python -m SLiCAP.schematic.cli netlist  sch/my_circuit.slicap_sch
   $ python -m SLiCAP.schematic.cli svg      sch/my_circuit.slicap_sch
   $ python -m SLiCAP.schematic.cli pdf      sch/my_circuit.slicap_sch

If ``-o <file>`` is omitted, the output takes the schematic's name with the
appropriate extension and lands in the project's ``cir/`` (netlist) or
``img/`` (SVG / PDF) directory automatically.  For a schematic saved as a
subcircuit the ``netlist`` command writes the library
``lib/<name>.slicap_lib`` instead of a ``.cir`` file (see
:doc:`/GUI/schematics/hierarchical_blocks`).

Running it in SLiCAP
====================

``makeCircuit()`` recognises the ``.slicap_sch`` extension and generates the
netlist and figures automatically before parsing:

.. code-block:: python

   import SLiCAP as sl
   sl.initProject("My Design")
   cir = sl.makeCircuit("sch/my_circuit.slicap_sch")   # exports + parses
   result = sl.doNoise(cir, pardefs="circuit", numeric=True)

The export can also be run on its own with ``sl.updateImages()``, which
rewrites the schematic's images (and its netlist) without creating a
circuit object. It takes the circuit object of a SLiCAP schematic, or the
name of the circuit, which is how an NGspice schematic is addressed. Its
place is the end of the instruction file. A schematic that links plots
(:menuselection:`Place --> Image…` with a file in ``img/``) inlines them at
export time, and ``makeCircuit()`` at the top of the file exports before
the analyses have written them. An export after the figures shows the
plots of this run:

.. code-block:: python

   cir = sl.makeCircuit("sch/my_circuit.spice_sch")   # exports + parses
   TR1 = sl.tran("my_circuit", "1n", "1u")
   FIG1 = sl.makeFigure([[AX1]], "tran")               # writes img/tran.svg
   sl.updateImages("my_circuit")                       # exports with the new plot

:menuselection:`Instruction --> Update schematic images…` on the schematic's tab
appends that last line. Both calls skip the export when the netlist and
the images are newer than everything they depend on: the schematic, its
sidecars, the symbol libraries, the operating-point results and the linked
images. On the canvas the linked images are reloaded after every run.

For a subcircuit schematic both calls write the library in ``lib/`` and the
figures, and ``makeCircuit()`` returns ``None``: a subcircuit dos not require
a ground node ``0`` and is not parsed as a circuit.

.. code-block:: python

   sl.makeCircuit("lib/smallAmp.slicap_sch")   # writes lib/smallAmp.slicap_lib and img/smallAmp.svg, .pdf

What the netlist looks like
===========================

The first line is the title.

Each element becomes one line — reference designator, nodes (in the symbol's
node order), any references, the model and the parameters:

.. code-block:: text

   "My Circuit"

   .param R_s = 825
   .param C_L = 10e-12

   .source V1
   .detector V_out

   R1 in 3 R value={R_s}
   N1 out 0 in 1 N
   C3 out 0 C value={C_L}
   ...
   .end
