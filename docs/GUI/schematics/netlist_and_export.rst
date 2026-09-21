=====================
Netlist & Export
=====================

A finished schematic produces three things: a **netlist** for analysis, and
**SVG** / **PDF** figures for documents.

From the GUI
============

* :menuselection:`File --> Export netlist…` (:kbd:`Ctrl+E`) writes a SLiCAP
  or NGspice ``.cir`` netlist.
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
:doc:`/GUI/hierarchical_blocks`).

Running it in SLiCAP
====================

``makeCircuit()`` recognises the ``.slicap_sch`` extension and generates the
netlist and figures automatically before parsing:

.. code-block:: python

   import SLiCAP as sl
   sl.initProject("My Design")
   cir = sl.makeCircuit("sch/my_circuit.slicap_sch")   # exports + parses
   result = sl.doNoise(cir, pardefs="circuit", numeric=True)

You can also trigger the export step separately — for example to regenerate
figures without re-running the analysis:

.. code-block:: python

   from SLiCAP.schematic import make_schematic
   make_schematic("sch/my_circuit.slicap_sch")   # writes cir/ and img/

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
