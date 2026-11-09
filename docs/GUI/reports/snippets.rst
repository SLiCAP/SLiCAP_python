========
Snippets
========

A snippet is a small file with a piece of a report: an equation, a table, a
listing, a figure reference. The instruction file writes it when it runs, and
the report includes it, so the report follows the design without copying.
:menuselection:`Instruction --> Create LaTeX snippet…` and
:menuselection:`Instruction --> Create RST snippet…` compose the formatter
call that writes one snippet and append it to the instruction file. The
dialog is the same for both formats; it offers the methods the chosen
formatter has, with the arguments its signature takes.

The **Name** is the file name of the snippet without extension and the
Python variable that holds it. LaTeX snippets are written to the project
``tex/SLiCAPdata/`` folder, RST snippets to ``sphinx/SLiCAPdata/``. A LaTeX
document includes a snippet with ``\input{SLiCAPdata/<name>}``, a Sphinx
document with ``.. include:: SLiCAPdata/<name>.rst``.

The dialog creates four kinds of snippet.

Text output
===========

A listing that SLiCAP prints as text: the poles and zeros of a result, the
servo bandwidth, the phase margin, a state-space listing, or free text. The
dialog emits two lines:

.. code-block:: python

   txt = sl.TXTformatter()
   poles_txt = txt.pz(PZ1).save("poles")
   poles = ltx.file(sl.ini.txt_path + "poles.txt").save("poles")

The first line writes the listing to ``txt/poles.txt`` with the text
formatter, which is the same for every output format. The second line wraps
that text file into a snippet of the chosen format, ``poles.tex`` here, in a
verbatim environment. Include the snippet as any other.

Snippet from a file
===================

Any text file, or a netlist, included verbatim: the file name, and for LaTeX
the listing language, for RST the first line number. A netlist is named by
its file name in the project's cir folder, for example ``amp.slicap_cir``.
The Browse button opens that folder. Any other file takes its full path.

Snippet from an object
======================

A formatter method applied to an object the instruction file defines. The
**Result** list offers the result variables of the file that fit the method:
a pole-zero table takes a result of ``doPoles()``, ``doZeros()`` or
``doPZ()``, a noise table a result of ``doNoise()``. The **Circuit** list
offers the circuit objects the file defines for the methods that describe a
circuit: the element data, the parameter definitions and the undefined
parameters. Both lists are picks, not text fields: a snippet is composed only
for an object that exists in the file. The **Expression** list offers every
expression the last run of the file produced, as shown in the Design data:
``TIME1.laplace``, ``TIME1.time``, ``NOISE1.onoise``, and every variable
that holds an expression. The list is empty until the file has run. The
field is editable, so a derived expression can be typed as well.

Specification table
===================

A table of the specifications of one type in a specification CSV of the
project. The dialog loads the CSV once, into ``SPECS_<file stem>``, and
emits the table call for the chosen type.

Row colour of LaTeX tables
==========================

The LaTeX tables, the specification table among them, colour their rows.
The **Row colour** field offers the colours that ``preambuleSLiCAP.tex``
defines, and ``none`` for a table without row colour. The default,
``myyellow``, emits no argument. Another choice is emitted as
``color="mygray"``, ``none`` as ``color=None``. The field appears only for
the methods that take a colour, so never for RST.

A Beamer document needs ``\documentclass[xcolor=table]{beamer}`` for the
row colour, and the colour definitions of ``preambuleSLiCAP.tex``. That
preamble itself cannot be loaded in Beamer, its page geometry conflicts.
With the ``mathpazo`` font package in Beamer, ``\mathrm{\Omega}`` renders as
a black box, so every unit in ohms is affected. Without it the units render
correctly.
