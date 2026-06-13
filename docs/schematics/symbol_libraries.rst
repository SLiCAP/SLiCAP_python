================
Symbol Libraries
================

Where symbols come from
=======================

While you draw, symbols are taken from the application's **system library**
(the shipped set listed in :doc:`placing_symbols`).  Each symbol is an SVG
``<g>`` element that carries its own metadata in ``data-*`` attributes:

.. code-block:: xml

   <g id="R"
      data-prefix="R"
      data-nodes="pos neg"
      data-model="R"
      data-params="value dcvar dcvarlot noisetemp noiseflow"
      data-description="Resistor (nonzero resistance)"
      data-info="https://www.slicap.org/syntax/devices.html#r-resistor">
      ...artwork and pin markers...
   </g>

The editor reads everything it needs from these attributes — there is no
separate table to keep in sync.

* ``data-prefix`` — the device letter / reference-designator prefix.
* ``data-nodes`` — the node names, in the order the netlister expects.  A pin's
  position is given by a ``<circle class="node" data-node="...">`` marker.
* ``data-model`` — the SLiCAP model name.
* ``data-params`` — the parameters the user may set.
* ``data-description`` / ``data-info`` — the text and link shown in the
  Properties dialog.

The symbol's outline extent (used for selection) is computed from its geometry,
so symbols never need a hand-maintained bounding box.

Frozen copies travel with the schematic
=======================================

When you **save**, the symbols the schematic uses are copied into its
``<name>.symbols`` sidecar (see :doc:`project_files`).  When you **open** a
schematic, those frozen copies are loaded *on top of* the system library, so the
drawing always renders with the symbols it was created with — even if the
shipped symbols change later.

Custom and overriding symbols
=============================

Because a frozen symbol overrides the system symbol of the same name, you can
customise how a device looks.  For example, you can draw the nullor ``N`` as an
operational-amplifier triangle, freeze it into a schematic's ``.symbols``, and
that schematic will use your version while everything else keeps the standard
IEC symbol.

.. todo::

   A graphical in-app symbol editor (draw the artwork and fill in the
   ``data-*`` metadata) is planned.  Until then, custom symbols are authored by
   editing the SVG directly.
