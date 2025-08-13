=============
SLiCAP Manual
=============
    
.. image:: /img/colorCode.svg

Welcome to the version 4 manual of SLiCAP. This edition surpasses all previous versions and has been completely rewritten.

SLiCAP is a **S** ymbolic **Li** near **C** ircuit **A** nalysis **P** rogram, is designed to set up and solve equations for analog circuit design and automatically update design data in documentation.

SLiCAP is written in Python.

SLiCAP is distributed under the `MIT license <https://opensource.org/license/mit>`_

What you can find in this manual
================================

Below, you find short descriptions of the main sections of this manual, listed in the side menu.

SLiCAP Version 4
----------------

`SLiCAP Version 4 <introduction/SLiCAPintroduction.html>`_ includes:

#. An introduction to SLiCAP
#. Version 4 Release Notes
#. A short guidance how to use SLiCAP in conjunction with `Structured Electronic Design <https://books.open.tudelft.nl/home/catalog/book/162>`_
#. A list of contributers to SLiCAP.

SLiCAP User Guide
-----------------

The `User Guide <userguide/SLiCAPuserguide.html>`_ provides a comprehensive guide to using SLiCAP, covering everything from installation to executing fully documented design projects.

SLiCAP output displayed in this **SLiCAP user guide**, is generated with the script: `manual.py <https://github.com/SLiCAP/SLiCAP_python/tree/main/docs/manual.py>`_. 

.. literalinclude:: Manual.py

.. admonition:: Warning: running this script may take a while!
    :class: warning
    
    This is because:
    
    #. ``feedback.py`` Compares symbolic circuit analysis results obtained with the **asymptotic-gain feedback model** with the results obtained from **Modified Nodal Analysis**. The sole purpose of this is to illustrate the correctness of the feedback model for those unacquainted with it. As stated in `How to Use SLiCAP <introduction/SLiCAPhow.html>`_, working with such complex multi-variable expressions is not encouraged.
    #. The script ``plots.py`` shows a plot of a periodic pulse response obtained from a single unit step response. Periodic pulses created in this way use the  **Heaviside** function. The numeric evaluation of expressions with this function may take a while. 

SLiCAP Examples and Tutorials
-----------------------------

`SLiCAP Examples and Tutorials <tutorials/SLiCAPtutorials.html>`_ gives descriptive links to `github SLiCAPexamples <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples>`_.

SLiCAP Netlist syntax
---------------------

The SLiCAP netlist syntax slightly deviates from standard SPICE. `SLiCAP Netlist Syntax <syntax/SLiCAPnetlistSyntax.html>`_ describes the netlist syntax, including all built-in devices and models.

SLiCAP Reference
----------------

`SLiCAP Reference <reference/SLiCAPreference.html>`_ documents all SLiCAP user callable functions and objects.
    
.. toctree::
    :hidden:

    introduction/SLiCAPintroduction
    userguide/SLiCAPuserguide
    tutorials/SLiCAPtutorials
    syntax/SLiCAPnetlistSyntax
    reference/SLiCAPreference
    
.. image:: /img/colorCode.svg
