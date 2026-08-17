=================================================
Structured Electronic Design Environment — Manual
=================================================

A design environment for **SLiCAP** (Symbolic Linear Circuit Analysis Program,
https://www.slicap.org) and **NGspice**.  You draw a circuit and compose its
analysis instructions through dialogs; the environment writes a plain Python
instruction file that puts the full symbolic and numeric analysis of your
circuit at your disposal — for design automation, verification and generated
documentation.  The same drawing serves as the runnable netlist *and* as the
publication figure, so design and documentation stay one activity instead of
two that must be kept in sync by hand.

.. figure:: /GUI/img/overview_hearingloop.png
   :alt: A finished schematic in the editor
   :width: 100%

   A finished schematic: components, wires, net labels, a parameter table and a
   hyperlink annotation — exported straight to the figure you are reading.

.. note::

   This manual is a (far from completed) **draft**!

.. toctree::
   :maxdepth: 2
   :caption: Contents

   introduction/introduction
   introduction/getting_started
   project/project
   schematics/schematic
   schematics/placing_symbols
   schematics/component_properties
   schematics/wiring
   schematics/labels_ports_parameters
   schematics/annotations
   schematics/preferences
   schematics/netlist_and_export
   hierarchical_blocks
   instruction/instructions
   reference/symbol_libraries
   reference/design

Indices
=======

* :ref:`genindex`
* :ref:`search`
