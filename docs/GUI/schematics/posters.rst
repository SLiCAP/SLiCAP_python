=======
Posters
=======

A poster is a drawing that shows other drawings of the project: schematics,
other posters, figures and LaTeX snippets of the Design data, with text,
shapes, LaTeX and images around them. It has a border like a schematic, it
is exported to SVG and PDF like a schematic, and everything it shows follows
the runs of the instruction files, so a poster is a design overview, a
hand-out, a clickable presentation for a lecture that is never out of date,
or a figure of several circuits for a book.

A poster is **not a schematic**: it holds no circuit and is never netlisted.
Its file is ``posters/<name>.slicap_poster``, an edited source beside the
schematics in ``sch/``; its export goes to ``img/<name>.svg`` and ``.pdf``
like every other drawing.

Making a poster
===============

:menuselection:`File --> New poster…` on the main window asks for a name, a
title and a border. The border is the export frame: the exported SVG and PDF
have its size. The choice is the same as in the properties dialog of a
schematic (see :ref:`border-formats`): no border, a paper or screen format,
a border format of your own, or a custom size. The border is drawn with the
border look of the drawing preferences. The poster opens in its own tab with
the menus of a drawing: Draw for lines, shapes, curves, text, hyperlinks and
LaTeX, and Place for what the poster shows.

A figure for a book is a poster with the border format of the document
column: a fixed width and a free height. Place the circuits on it at one
scale, so their text matches, and drag the bottom side of the border to the
content. Each placed schematic brings its own border and background.

What a poster shows
===================

* :menuselection:`Place --> Schematic…` places a schematic of the project,
  chosen from the schematic files in ``sch/`` and ``lib/`` by their path,
  the subcircuit packages included. Nothing is preselected. The poster
  shows the schematic's export and keeps it up to date.
* :menuselection:`Place --> Poster…` places another poster the same way.
  The list leaves out this poster and every poster that already shows it,
  directly or through a chain, because a poster cannot contain itself.
* :menuselection:`Place --> Figure…` and :menuselection:`Place --> LaTeX
  snippet…` place a figure or a snippet of the Design data by name, as on a
  schematic (see :doc:`annotations`).
* :menuselection:`Place --> Image…` places a file.

Every placed drawing is a **link**, never a copy: the schematic stays in its
own file and the poster shows its export. Choosing a drawing brings its
export up to date, so it is shown at once, at 100 %: the scale of its
export, at which its grid and its text are those of the poster. A placed
drawing snaps to the grid like a component. Double-click a placed drawing
for its scale. To edit the drawing itself, open it from the project tree.

Updating and exporting
======================

The export of a poster first brings the exports of the drawings it shows up
to date, children before parents, then writes the poster. In a script that
is ``sl.updateImages("<poster name>")``, at the end of the instruction
file, after the figures; in the editor it is :menuselection:`File --> Export
SVG…` or :menuselection:`Export PDF…`. Figures, snippets and placed trace
curves follow every run as they do on a schematic.

In a browser the exported SVG is clickable: a click on a shown schematic or
poster opens that drawing's own export, which lies next to the poster's in
``img/``, so a poster of posters is a nested, clickable presentation. The
links are relative: a poster copied elsewhere on its own still shows
everything, but its clicks no longer lead anywhere.
