====================
Hierarchical Blocks
====================

Hierarchical blocks let a schematic instantiate another schematic as a single
**subcircuit** symbol (device prefix ``X``), the way SLiCAP and SPICE handle
``.subckt`` definitions.  Subcircuits work for both schematic types; only the
file extensions and the library file format differ per dialect
(``.slicap_sch`` / ``.slicap_lib`` versus ``.spice_sch`` / ``.spice_lib``).

Design intent
=============

* A block is referenced, **not flattened**, in the capture tool.  The netlist
  keeps the hierarchy (an ``X`` instance plus a ``.subckt`` definition);
  SLiCAP / NGspice perform the flattening at analysis time.  This keeps
  netlists small and readable and preserves the design hierarchy.
* Subcircuit's **interface parameters** come from its ``.subckt`` definition
  (name and default value), not from the built-in device tables — matching
  standard SPICE practice.
* A subcircuit is stored as a **package** in the project ``lib/`` folder: the
  compiled library (``.subckt`` definition), the block symbol, and the
  subcircuit's own editable schematic.  One folder holds everything the block
  needs — see *Self-contained projects* in :doc:`/GUI/project/project`.

Saving a schematic as a subcircuit
==================================

Any schematic can be turned into a reusable subcircuit:

#. Add **port** symbols and name them — the names become the subcircuit's
   external nodes.  A ``ground`` (node 0) stays global and is never a port.
#. In :menuselection:`File --> Schematic properties…`, tick **Save this
   schematic as a SLiCAP subcircuit (.lib)** and give the document a
   *Title*: the subcircuit name, and the name of its files.

   .. TODO screenshot: the Schematic Properties dialog with the subcircuit box ticked and a title

#. :menuselection:`File --> Save schematic` opens the **Create Subcircuit**
   dialog. Its *Nodes* list holds the named ports; move them with **Up** and
   **Down**, top to bottom is the left-to-right node order of the ``.subckt``
   line, the order in which a parent connects the block. Under *Parameters*
   declare the **overridable parameters** with their defaults; a parent may
   pass a value for each of them. The dialog is a fixed part of saving a
   subcircuit: it opens on every save, showing the previous choices.

   .. TODO screenshot: the Create Subcircuit dialog for smallAmp (nodes inP, inN, outP, outN; parameters A_v, r_o)

#. **Create Subcircuit** writes the package to ``lib/``: the editable source
   (``lib/<title>.slicap_sch`` or ``.spice_sch``) and the compiled library
   (``lib/<title>.slicap_lib`` or ``.spice_lib``). The schematic is saved in
   ``lib/`` from then on, not in ``sch/``.

The library file holds one ``.subckt`` definition; the ports appear in the
chosen order, and a parameter passed in on the ``.subckt`` line is **not**
redefined internally — the passed value (or its default) supersedes it.
Library lines placed on the schematic (device models such as ``inc
BC847.lib``) are carried into the generated library, so the definition is
complete on its own.

Regenerating the library from a script
======================================

The library is also written **without the GUI**. ``makeCircuit()`` and
``make_schematic()`` recognise a subcircuit schematic by the box ticked in
its properties and write the library instead of a circuit netlist:

.. code-block:: python

   import SLiCAP as sl
   sl.initProject("My Design")
   sl.makeCircuit("lib/smallAmp.slicap_sch")   # writes lib/smallAmp.slicap_lib, img/smallAmp.svg, img/smallAmp.pdf

The call returns ``None``: a subcircuit is not a circuit, it does not need a ground
node, and it cannot have source, detector, or loop gain reference. 
No circuit object check is performed and no circuit object is created by ``makeCircuit()``. 
The port order and the parameters come from the schematic
properties, as saved from the Create Subcircuit dialog. A script that builds
a project's documentation can therefore regenerate every subcircuit library
and figure from the schematics, in the same way it regenerates the circuits.
Unchanged schematics are not re-exported.

.. note::

   **Libraries are always global** in SLiCAP: the contents of a ``.lib`` /
   ``.inc`` line go to one global namespace, wherever the line appears —
   also inside a subcircuit definition. Two libraries defining the *same*
   model name therefore conflict.  (Inline ``.model`` / ``.param``
   definitions inside a ``.subckt`` *are* local to it.)  The NGspice library
   is generated to behave the same way.

Placing a block
===============

:menuselection:`Place --> New subcircuit symbol…` creates (or re-assigns) a
subcircuit's block symbol and places its first instance:

#. Pick the subcircuit's library file.  The dialog reads its ``.subckt``
   header and shows the block name, ordered ports and overridable
   parameters, and whether the subcircuit's schematic is present.
#. Choose the symbol: the **generated box** — a rectangle with one named pin
   per port — or **any loaded symbol** with a matching pin count, re-skinned
   as this subcircuit (an opamp macromodel gets the opamp artwork).
#. With the generated box, each pin is placed on the side its **port symbol
   suggests** in the subcircuit schematic: a port pointing top→bottom sits on
   top of the symbol, one pointing left→right on the left, and so on —
   read from the port's rotation and mirror settings.  Without a schematic
   the pins are spread clockwise from the top-left in node order.  Pin
   *sides* are visual only; the netlist node order never changes.
#. The symbol is written to ``lib/<name>.slicap_sym`` (or
   ``lib/<name>.spice_sym``) and becomes a **palette citizen** of the project:
   a second instance is placed from the palette like any other component,
   no dialog involved.
#. The block's library is added to the schematic as an include
   (de-duplicated), and the block is placed like any other component.

When the chosen library file lives in **another project**, its complete
package — library, symbol and schematic — is *copied* into this project's
``lib/`` first.  The import is a snapshot: later edits stay local, the
originating project is never touched.

In the netlist the block appears as ``X<n> <nodes…> <name> par=val …``: nodes
in port order, ``<name>`` the subcircuit, and only the parameters you
override on the placement.  Unset parameters fall back to the ``.subckt``
defaults.

Descending into the hierarchy
=============================

Double-click a placed block and choose **Descend into subcircuit**: the
subcircuit's schematic opens in its own tab for inspection and editing.  If
it is already open, its tab is activated instead of opening a second copy.
Saving the subcircuit re-runs the Create Subcircuit dialog and regenerates
the library, keeping schematic, symbol and ``.subckt`` definition in step.

**Operating-point annotations (NGspice) follow the descent.**  When the parent
schematic holds the results of an op run, descending hands the subcircuit
view the values of *that instance*: internal nets show their bias voltages,
port nets show the parent nets they connect to, and the tab title names the
instance (e.g. ``BJTamp.spice_sch (X1)``).  The schematic file is the
*definition* and the instance is *view state*: there is only ever one
editable view of a subcircuit, and descending from another instance
retargets its annotations — the last descent wins.  Comparing instances
side by side is parent-level information: the parent shows every instance's
port voltages, and the Design data panel lists all internal vectors
(``v(x1.…)``, ``v(x2.…)``).  A subcircuit opened directly (not via descend)
shows no borrowed values.

The order of run and descend does not matter: an open subcircuit view is
**live-updated** whenever a new run installs fresh results in the parent —
including nested descents.  If the instance it was showing no longer exists
in the netlist the run used, its annotations are cleared rather than left
showing another situation's values.

Planned
-------

* **Loop detection** across the hierarchy.
* A full **Symbol Editor** for refining generated symbols.
