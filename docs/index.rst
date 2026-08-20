=============
SLiCAP Manual
=============
    
.. image:: /API/img/colorCode.svg

- SLiCAP is a **S** ymbolic **Li** near **C** ircuit **A** nalysis **P** rogram, is designed to set up and solve equations for analog circuit design and automatically update design data in documentation.
- SLiCAP is written in Python.
- SLiCAP is distributed under the `MIT license <https://opensource.org/license/mit>`_
- SLiCAP `statistics <https://pypistats.org/packages/slicap>`_
- SLiCAP `training courses <https://montagne.nl/slicap>`_

.. admonition:: NEW! Structured Electronic Design Environment integrates SLiCAP and NGspice
    :class: note

    - **Analog design is complex.**
    - **Systems engineering tells us how engineers solve complex problems.**
    - **SLiCAP makes it doable.**
    
    .. image:: /API/img/GUI.png
    
    Project manager, Schematic Editor, Variables Explorer, etc. all integrated in the Structured Electronic Design Environment.

    >>> pip install slicap        # then start the environment with:  slicap
    
    Read more about the `Structured Electronic Design Environment <index.html#structured-electronic-design-environment>`_

.. admonition:: Video Presentation SLiCAP KiCON Europe 2025
    :class: note
    
    .. image:: /API/img/SLiCAP_KiCON_2025.jpg
        :target: https://www.youtube.com/watch?v=Ve3a5WGAXAQ>`_
       
    **Download link to the** `source files <https://montagne.nl/downloads/SLiCAP_KiCON.zip>`_
    
What you can find in this manual
================================

Below, you find short descriptions of the main sections of this manual, listed in the side menu.

SLiCAP Version 5
----------------

`SLiCAP Version 5 <API/introduction/SLiCAPintroduction.html>`_ includes:

#. An introduction to SLiCAP
#. Release Notes
#. A short guidance how to use SLiCAP in conjunction with `Structured Electronic Design <https://books.open.tudelft.nl/home/catalog/book/162>`_
#. A list of contributers to SLiCAP.

SLiCAP User Guide
-----------------

The `User Guide <API/userguide/SLiCAPuserguide.html>`_ provides a comprehensive guide to using SLiCAP, covering everything from installation to executing fully documented design projects.

SLiCAP output displayed in this **SLiCAP user guide**, is generated with the script: `manual.py <https://github.com/SLiCAP/SLiCAP_python/tree/main/docs/manual.py>`_. 

.. literalinclude:: API/Manual.py

.. admonition:: Warning: running this script may take a while!
    :class: warning
    
    This is because:
    
    #. ``feedback.py`` Compares symbolic circuit analysis results obtained with the **asymptotic-gain feedback model** with the results obtained from **Modified Nodal Analysis**. The sole purpose of this is to illustrate the correctness of the feedback model for those unacquainted with it. As stated in `How to Use SLiCAP <introduction/SLiCAPhow.html>`_, working with such complex multi-variable expressions is not encouraged.
    #. The script ``plots.py`` shows a plot of a periodic pulse response obtained from a single unit step response. Periodic pulses created in this way use the  **Heaviside** function. The numeric evaluation of expressions with this function may take a while. 

SLiCAP Examples and Tutorials
-----------------------------

`SLiCAP Examples and Tutorials <API/tutorials/SLiCAPtutorials.html>`_ gives descriptive links to `github SLiCAPexamples <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples>`_.

SLiCAP Netlist syntax
---------------------

The SLiCAP netlist syntax slightly deviates from standard SPICE. `SLiCAP Netlist Syntax <API/syntax/SLiCAPnetlistSyntax.html>`_ describes the netlist syntax, including all built-in devices and models.

SLiCAP Reference
----------------

`SLiCAP Reference <API/reference/SLiCAPreference.html>`_ documents all SLiCAP user callable functions and objects.

Structured Electronic Design Environment
========================================

SLiCAP Version 5 adds a graphical environment on top of the analysis
engine. It is documented in its own manual: `Structured Electronic Design
Environment <GUI/index.html>`_.

The GUI for creating SLiCAP instructions
----------------------------------------

Everything SLiCAP can do is driven from Python instructions, and that is where
the friction has always been: a designer who knows exactly which transfer to
evaluate still has to get the syntax right - the analysis function, a circuit
object, a transfer type with the source, detector and loop-gain reference it
requires, parameter substitution, stepping.

The `Structured Electronic Design Environment <GUI/index.html>`_ is the
graphical front end that removes that burden. You draw the circuit and compose
the instructions through dialogs which offer only what the circuit in front of
you actually has - its sources, its detectors, its controlled sources, its
parameters - so an instruction is correct by construction rather than by
proofreading. It does **not** design your circuit: it removes the clerical work
around it.

Its product is an ordinary **instruction file**: a Python script you can read,
edit by hand, run from the command line, or import from a design script, which
puts the full symbolic and numeric analysis of your circuit at your disposal
for design automation, verification and generated documentation. The same
drawing serves as the runnable netlist *and* as the publication figure, and
both SLiCAP and NGspice analyses live in one project.

SLiCAP installs it: ``pip install slicap``, or ``pip install slicap --upgrade``
to update an existing installation (see
`Installation <API/userguide/install.html>`_). Start it with ``slicap`` for the
full environment, or with ``slicap-schematics`` to edit schematics only.

Design with SLiCAP, verify with NGspice
---------------------------------------

Design and verification use the same relation in opposite directions, and
that is why they need different models.

Designing moves **forward**: from a specification, through budgets, to a
circuit structure and the values of its components. What has to be inverted is
not the design process but the **analysis**. Symbolic analysis expresses
performance as a function of the structure and the component values; a
designer has the required performance and needs the values. With the
specification and its budgets, and with methods for generating candidate
structures, those values are *solved from the analysis result* - which is
possible only while the result is symbolic and the model is simple enough to
be solved: a nullor, an ideal amplifier, a first-order transistor model. That
is why SLiCAP is symbolic, why it works on the simplest model that still
answers the design question under study, and why a design can be built up
stepwise, each decision following from the one before it and documented as it
is taken.

Verification uses the same relation in its natural direction: from a given
structure with given component values to the performance that results - now
with the extensive device models the manufacturer or the foundry supplies,
with their non-linearities, their parasitics and their temperature behaviour.
That is what **NGspice** is for, and it is why the environment carries both:
the same editor draws SLiCAP and NGspice schematics, one instruction file
holds the circuits and instructions of both, and both kinds of result arrive
in the same form.

Because they arrive in the same form, they can be **compared directly**. The
transfer of a concept, derived symbolically from a handful of ideal elements,
and the transfer of the completed circuit, simulated with full device models,
can be drawn on the same axes of the same figure - and NGspice's operating
point is annotated on the schematic itself, node by node, down into the
subcircuits. So the closing question of any design - *does the realisation
still do what the concept promised, and where does it start to deviate?* - is
answered by reading one figure, not by reconciling two separate documents.
This is what makes it an integrated design **and** verification environment
rather than a drawing tool with a simulator attached.

.. toctree::
    :hidden:

    API/introduction/SLiCAPintroduction
    API/userguide/SLiCAPuserguide
    API/tutorials/SLiCAPtutorials
    API/syntax/SLiCAPnetlistSyntax
    API/reference/SLiCAPreference
    GUI/index
    
.. image:: /API/img/colorCode.svg
