The symbol editor
=================

:menuselection:`File --> New symbol` and :menuselection:`File --> Edit
symbol...` on the main window open a canvas in **symbol mode**: the
schematic editor with reduced menus, editing one symbol of a
``.slicap_sym`` or ``.spice_sym`` file. Like the schematic entries they
need an open project: symbols are opened from and saved into the project's
``lib`` folder by default. A double click on a ``.slicap_sym`` or
``.spice_sym`` file in the Project panel opens the symbol editor on that
file as well. Draw, undo, selection and the shape properties work as in a
schematic.

A symbol is one group in a symbol file: its drawing in SVG primitives, one
pin marker per terminal, and the attributes that make it an element (prefix,
model, parameters, description). The file is the input and the output:

* :menuselection:`File --> Open symbol...` reads one symbol out of a file;
  the dialect (SLiCAP or NGspice) follows the file extension.
* :menuselection:`File --> Save symbol` writes the symbol back as one group,
  replacing the group of the same name and leaving the other symbols of the
  file untouched. A file in the project's ``lib`` folder is offered in
  :menuselection:`Place --> Symbol` of every schematic of the project.
* :menuselection:`File --> Symbol properties...` sets the name (the id in the
  file), the prefix (the SLiCAP element type; ``X`` for a subcircuit), the
  model, the parameters with their defaults and label flags, the reference
  designators, the description and the info link, and whether the pin names
  are drawn on the schematic.

Drawing
-------

Use :menuselection:`Draw` for lines, rectangles, ellipses and polygons,
:menuselection:`Place --> Pin...` for a terminal,
:menuselection:`Place --> Symbol text...` for decoration such as the plus and
minus of a source, :menuselection:`Place --> LaTeX...` for a typeset label
and :menuselection:`Place --> Image...` for a picture. Every placed item
follows the cursor and is put down with a click, like on a schematic;
**Escape** drops it. Copy and paste (**Ctrl+C**, **Ctrl+V**) work on pins,
texts, shapes, LaTeX labels and images; a pasted pin gets the next pin
number and, when its name is taken, the number appended to its name. The
clipboard is shared by every open canvas: a drawing copied in one symbol
editor pastes in another, also one of the other dialect, and shapes and
labels travel between symbols and schematics. Pins and symbol texts stay
out of a schematic, components and wires out of a symbol. Pins always snap to the grid; shapes snap to the
grid, or to the fine grid of one unit while **Shift** is held, which the
fine work of symbol artwork needs (an arrow head at 8, 8). Select a shape
and drag one of its handles to reshape it.

* Pin names are free. The pin ORDER is the netlist order of the element
  (for a controlled source: output pair, then input pair); on save the pin
  count is checked against the element type of the prefix, ``X`` excepted.
* The origin (the anchor of the placed component) is the circle with a
  cross. Where the marker is, is the origin: the symbol is saved with every
  coordinate relative to it. Drag it alone to set the origin, or select it
  with the drawing to move everything together. It always snaps to the grid
  and is not part of the symbol.
* Colours: the schematic style restyles a symbol by replacing the colours
  ``black`` (strokes and filled heads) and by colouring the text; ``white``
  fills mask wires behind a body. A shape with another colour is written as
  it is and reported on save, because it will not follow the style.
* A primitive the editor cannot edit (a path, a nested group, a transformed
  element) is shown, can be moved or deleted, and is written back verbatim.
* A LaTeX label is compiled with pdflatex and dvisvgm when it is placed
  and saved into the symbol as plain paths, together with its source, so the
  symbol renders without LaTeX on any machine and the label reopens for
  editing (double click) where LaTeX is installed. Like the symbol texts
  the label is recoloured by the schematic style.
* An image is embedded in the symbol (PNG and JPEG files as they are,
  other formats rasterised); the save reports the size of a large one,
  because every schematic that uses the symbol carries a copy. The hyperlink
  of a symbol is its info link in :menuselection:`File --> Symbol
  properties...`; it is not drawn.

Orientation of labels
---------------------

A placed component may be rotated and mirrored; its symbol texts and LaTeX
labels are not. They follow the drawing-school rule that lettering is read
from the bottom or from the right of the sheet: a component rotated by 0 or
180 degrees shows them upright, a component rotated by +90 or -90 degrees
turns them to read bottom-to-top, and a mirrored component never mirrors
them. Each label turns about its own centre, so it stays where it was
drawn. The same rule is applied by the SVG and PDF export.

A schematic that already uses the symbol keeps its frozen copy until
:menuselection:`Tools --> Load symbols from library`.
