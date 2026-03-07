=========================
SLiCAP pole-zero analysis
=========================

.. image:: ../img/colorCode.svg

Accurate pole-zero analysis is indispensible for investigating the stability of dynamic systems. SLiCAP supports both numeric and symbolic pole-zero analysis. Symbolic pole-zero analysis is supported for lower-order rational functions of the Laplace variable and for functions implemented in sympy. Numeric pole-zero analysis is implemented for Laplace rational functions of any order. SLiCAP uses numeric analysis if no other symbolic variables than the Laplace variable ``ini.laplace=s`` are found in the expression.

SLiCAP has three instructions related to pole-zero analysis:

#. `doPoles() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPoles>`__ returns the solutions of the Laplace variable of the denominator of a transfer function.
   
#. `doZeros() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doZeros>`__ returns the solutions of the Laplace variable of the numerator of a transfer function.

#. `doPZ() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPZ>`__ returns the zero frequecy gain, the poles, and the zeros of a transfer function. Poles and zeros that coincide withing the display accurary ``ini.disp`` are canceled out. 

   .. admonition:: Important
       :class: note
       
       ``doPZ()`` does not return non-observable and non-controllable poles. Use ``doPoles()`` and ``doZeros()`` to obtain information about non-observable and non-controllable states.
       
       - Non-controllable state: the input signal(s) cannot change the state.
       - Non-observable state: the state cannot be observed at the output(s)

SLiCAP output displayed on this manual page, is generated with the script: ``laplace.py``, imported by ``Manual.py``.

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1
    
The following circuit is used for this manual page:

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 9
    :lineno-start: 9
    
.. image:: /img/pzNetwork.svg
    :width: 600px
    
With a differential voltage detector between nodes (1) and (2), and the signal source set to ``V1``, the transfer has four poles and three zeros. Two zeros coincide with two poles:

- The pole introduced by C2 is not controllable and thus canceled by a zero.
- The pole introduced by :math:`\tau` is not observable and thus canceled by a zero.
    
Obtain all the poles of a transfer
==================================

Symbolic poles analysis
-----------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 11-12
    :lineno-start: 11

This yields:

.. code-block:: text

    [-1/(C_b*R_b), -1/tau, (-C_a*R_a - C_a*R_d - sqrt(C_a**2*R_a**2 + 2*C_a**2*R_a*R_d + C_a**2*R_d**2 - 4*C_a*L))/(2*C_a*L), (-C_a*R_a - C_a*R_d + sqrt(C_a**2*R_a**2 + 2*C_a**2*R_a*R_d + C_a**2*R_d**2 - 4*C_a*L))/(2*C_a*L)]
    
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-P.rst

.. admonition:: Important
    :class: note
    
    Poles and zeros returned by the instruction are always in [rad/s]. The units of poles and zeros displayed in tables HTML are governed by ``ini.hz=True`` (default).

Numeric poles analysis
----------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 14-15
    :lineno-start: 14

This yields:

.. code-block:: text

    [-30000.+10000.j, -30000.-10000.j, -100000.+0.j, -10000000.+0.j]
    
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-Pnum.rst
    
Obtain all the zeros of a transfer
==================================

Symbolic zero analysis
----------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 17-18
    :lineno-start: 17

This yields:

.. code-block:: text

    [-1/(C_b*R_b), -1/tau, -1/(C_a*R_d)]
    
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-Z.rst

Numeric zero analysis
---------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 20-21
    :lineno-start: 20

This yields:

.. code-block:: text

    [-2.0000e+04, -1.0000e+05, -1.0000e+07]
    
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-Znum.rst
    
Obtain the observable and controllable poles and zeros of a transfer
====================================================================

Symbolic pole-zero analysis
---------------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 23-26
    :lineno-start: 23

This yields:

.. code-block:: text

    1
    [(-C_a*R_a - C_a*R_d - sqrt(C_a**2*R_a**2 + 2*C_a**2*R_a*R_d + C_a**2*R_d**2 - 4*C_a*L))/(2*C_a*L), (-C_a*R_a - C_a*R_d + sqrt(C_a**2*R_a**2 + 2*C_a**2*R_a*R_d + C_a**2*R_d**2 - 4*C_a*L))/(2*C_a*L)]
    [-1/(C_a*R_d)]
    
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-PZ.rst

Numeric pole-zero analysis
--------------------------

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 28-29
    :lineno-start: 28

The ``listPZ()`` function displays a table in the console output:

.. code-block:: text

    DC value of gain: 1.00e+00

    Poles of gain:

     n  Real part [Hz]  Imag part [Hz]  Frequency [Hz]     Q [-] 
    --  --------------  --------------  --------------  --------
     0       -4.77e+03        1.59e+03        5.03e+03   5.27e-1
     1       -4.77e+03       -1.59e+03        5.03e+03   5.27e-1

    Zeros of gain:

     n  Real part [Hz]  Imag part [Hz]  Frequency [Hz]     Q [-] 
    --  --------------  --------------  --------------  --------
     0       -5.07e+02        0.00e+00        5.07e+02
     
Rendered with the formatter:

.. include:: ../sphinx/SLiCAPdata/table-PZnum.rst

Return attributes
=================

.. admonition:: Important
    :class: note
    
    Calculation of the poles requires calculation of the denominator of a transfer. Hence, SLiCAP also executes the instruction ``doDenom()`` and returns the Laplace poly of the denominator (= determinant of the MNA matrix = 'characteristic equation') in the ``.denom`` attribute of the result. It also places the MNA matrix in the ``.M`` attribute of the returned instruction object.
    
    Calculation of the zeros requires calculation of the numerator of a transfer. Hence, SLiCAP also executes the instruction ``doNumer()`` and returns the Laplace poly of the numerator in the ``.numer`` attribute of the result. It also places the MNA matrix in the ``.M`` in the returned instruction object.
    
    Calculation of the poles and the zeros requires all of the above, and the following attributes are available in the returned object:
    
    .. literalinclude:: ../pz.py
        :linenos:
        :lines: 31-36
        :lineno-start: 31
        
Display equations on HTML pages and in LaTeX documents
======================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../pz.py
    :linenos:
    :lines: 38-46
    :lineno-start: 38

Plot pole-zero patterns and root-locus
======================================

SLiCAP plot functions are discussed in `Create plots <plots.html>`_

.. image:: /img/colorCode.svg
