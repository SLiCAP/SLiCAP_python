=======
Posters
=======

A poster is a drawing that shows other drawings of the project: schematics,
other posters, figures and LaTeX snippets of the Design data, with text,
shapes, LaTeX and images around them. It has a page format, it is exported
to SVG and PDF like a schematic, and everything it shows follows the runs of
the instruction files, so a poster is a design overview, a hand-out, or a
clickable presentation for a lecture that is never out of date.

A poster is **not a schematic**: it holds no circuit and is never netlisted.
Its file is ``posters/<name>.slicap_poster``, an edited source beside the
schematics in ``sch/``; its export goes to ``img/<name>.svg`` and ``.pdf``
like every other drawing.

Making a poster
===============

:menuselection:`File --> New poster…` on the main window asks for a name, a
title and a page format: the paper sizes A4 to A0, Letter, Legal and
Tabloid, portrait or landscape, and the screen formats 16:9, 16:10 and 4:3.
The page is the poster's border, drawn at that size with the border look of
the drawing preferences, and the export has that size. The poster opens in
its own tab with the menus of a drawing: Draw for lines, shapes, curves,
text, hyperlinks and LaTeX, and Place for what the poster shows.

What a poster shows
===================

* :menuselection:`Place --> Schematic…` places a schematic of the project,
  chosen by name, shown as its exported image.
* :menuselection:`Place --> Poster…` places another poster the same way.
  The list leaves out this poster and every poster that already shows it,
  directly or through a chain, because a poster cannot contain itself.
* :menuselection:`Place --> Figure…` and :menuselection:`Place --> LaTeX
  snippet…` place a figure or a snippet of the Design data by name, as on a
  schematic (see :doc:`annotations`).
* :menuselection:`Place --> Image…` places a file.

Every placed drawing is a **link**, never a copy: the schematic stays in its
own file and the poster shows its export. Double-click a placed drawing for
its scale, and press **Open** in that dialog to open the drawing itself in a
tab.

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
