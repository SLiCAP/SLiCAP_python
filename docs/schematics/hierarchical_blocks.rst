====================
Hierarchical Blocks
====================

.. note::

   **Generating** a subcircuit from a schematic and **placing** it as an ``X``
   block with an auto-generated symbol are both implemented.  Refining the
   symbol in a full Symbol Editor and *descending* into a placed block are still
   planned; see :ref:`block-instantiation` at the end of this chapter.

Hierarchical blocks let a schematic instantiate another schematic as a single
**subcircuit** symbol (device prefix ``X``), the way SLiCAP and SPICE handle
``.subckt`` definitions.

Design intent
=============

* A block is referenced, **not flattened**, in the capture tool.  The netlist
  keeps the hierarchy (an ``X`` instance plus a ``.subckt`` definition);
  SLiCAP / SPICE perform the flattening at analysis time.  This keeps netlists
  small and readable and preserves the design hierarchy.
* A subcircuit's **interface parameters** come from its ``.subckt`` definition
  (name and default value), not from the built-in device tables — matching
  standard SPICE practice.
* A block is stored as two artefacts: a **netlist** (``.lib`` / ``.subckt``) and
  a **symbol**, exactly like an ordinary library element, so the same placement
  and Properties workflow applies.
* Because symbols and styles are already frozen into a schematic's sidecar files
  (see :doc:`project_files`), a hierarchical design remains portable.

Saving a schematic as a subcircuit
==================================

Any schematic can be turned into a reusable subcircuit library:

#. Add **port** symbols and name them — the names become the subcircuit's
   external nodes.  A ``ground`` (node 0) stays global and is never a port.
#. In :menuselection:`File --> Document Properties…`, tick **Save this
   schematic as a SLiCAP subcircuit (.lib)** and give the document a *Title*
   (the subcircuit name).
#. :menuselection:`File --> Save` opens the **Create Subcircuit** dialog, where
   you set the **node order** (drag ports up/down — this order *is* the
   ``.subckt`` node list) and declare the **overridable parameters** (name and
   default).
#. Saving writes both artefacts: the editable source to ``sch/<title>.slicap_sch``
   and the compiled library to ``lib/<title>.lib``.

The ``.lib`` holds one ``.subckt`` definition; the ports appear in the chosen
order, and a parameter passed in on the ``.subckt`` line is **not** redefined
internally — the passed value (or its default) supersedes it.  Passed
parameters use SLiCAP's self-referential default idiom, e.g. ``C_in={C_in}``.

.. _block-instantiation:

Placing a block
===============

:menuselection:`Place --> Subcircuit…` instantiates a saved subcircuit as an
``X`` block:

#. Pick the subcircuit's ``.lib``.  The dialog reads its ``.subckt`` header and
   shows the block name, ordered ports and overridable parameters, and whether a
   matching ``sch/<name>.slicap_sch`` is present.
#. A **default box symbol** is generated into ``lib/<name>.svg`` — a rectangle
   with one pin per port, placed clockwise from the top-left in the ``.subckt``
   node order (so pin order always matches node order).
#. The block's ``.lib`` is added to the schematic as a ``.lib`` include
   (de-duplicated), and the block is placed like any other component.

In the netlist the block appears as ``X<n> <nodes…> <name> par=val …``: nodes in
port order, ``<name>`` the subcircuit, and only the parameters you override on
the placement.  Unset parameters fall back to the ``.subckt`` defaults.

Planned
-------

* **Refine the symbol** in a full Symbol Editor (the auto-box is a starting
  point), and choose an existing ``.svg`` symbol instead of generating one.
* **Descend hierarchy** — open a placed block's ``sch/<name>.slicap_sch`` to
  edit it.
* **Loop detection** across the hierarchy.
