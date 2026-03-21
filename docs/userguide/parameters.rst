====================
Work with parameters
====================

.. image:: /img/colorCode.svg

*Parameters* are symbolic variables used in circuit element expressions. There are five ways of assigning values or expressions to these parameters:

#. Using built-in parameter definitions
#. In the netlist using the SPICE '.PARAM' directive
#. In python using the ``circuit.defPar()`` method
#. In python using the ``pardefs`` argument in an instruction
#. In python using the ``specs2circuit()`` function

.. admonition:: Important
    :class: warning
    
    Do NOT use parameter names of which parts can be interpreted as expressions or numbers!
    
    - ``"C_100p"``
    - ``"R_sin(x)"``

SLiCAP built-in parameters
==========================

.. admonition:: Global Parameters
    :class: note
    
    Global parameters are defined in the file ``SLiCAPmodels.lib`` in the folder given by ``ini.main_lib_path``. If global parameters are found in circuit element expressions or in circuit parameter definitions, SLiCAP automatically adds their global definition to the circuit parameter definitions.

.. literalinclude:: ../../SLiCAP/files/lib/SLiCAPmodels.lib
    :linenos:
    :lines: 1-19

.. admonition:: CMOS18 EKV model parameters
    :class: note
        
    Built-in CMOS18 EKV model parameter definitions are included in ``SLiCAP.lib`` in the folder given by ``ini.main_lib_path``.
    
.. literalinclude:: ../../SLiCAP/files/lib/SLiCAP.lib
    :linenos:
    :lines: 135-185
    
.. admonition:: SLiCAP Library files    
    :class: warning
    
    Notice, a SLiCAP library is like a SLiCAP circuit file:
    
    #. The first line after any line starting with ``*`` is considered the title of the library. 
    #. The last line must read ``.end``

Circuit parameters
==================

SLiCAP output displayed on this manual page, is generated with the script: ``parameters.py``, imported by ``Manual.py``.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 1-11
    :lineno-start: 1
    
We will use a simple RC network to demonstrate how to use parameters.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 13-14
    :lineno-start: 13

.. image:: ../img/myFirstRCnetwork.svg
    :width: 350px
    
Get all circuit parameters
--------------------------

A listing of all circuit parameters can be obtained as follows:

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 16-30
    :lineno-start: 16
        
This yields:

.. code-block:: text

    Parameters with definitions:

    R 1000
    C 1/(2*pi*R*f_c)
    f_c 1000

    Parameters that have no definition:

    V_s

Assign a value or an expression to a parameter
==============================================

The method `circuit.defPar() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.defPar>`__ can be used to assign a value or an expression to a parameter.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 32-36
    :lineno-start: 32
    
This yields:

.. code-block:: text

    {R: tau/C, C: 1/100000000, f_c: 1000, tau: 1/1000000}

Assign values or expressions to multiple parameters
===================================================

The method `circuit.defPars() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.defPars>`__ can be used to assign definitions to multiple parameters.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 38-40
    :lineno-start: 38
    
This yields:

.. code-block:: python

    {R: tau/C, C: 1/100000000, f_c: 1000, tau: 1/f_c}

Delete a parameter definition
=============================

You can delete a **parameter definition** using the method `circuit.delPar() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.delPar>`__ . This method does not delete the circuit parameter itself, it only clears its definition so that it can be used as a symbolic variable.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 42-59
    :lineno-start: 42

This yields:

.. code-block:: text

    Parameters with definitions:

    R tau/C
    C 1/100000000
    tau 1/f_c

    Parameters that have no definition:

    f_c
    V_s

Obtain the value of a parameter
===============================

The method `circuit.getParValue() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.getParValue>`__  returns the definition or the evaluated value of a parameter.

If the keyword argument ``substitute`` is True (default), all circuit parameter definitions are recursively substituted until a final value or expression is obtained (see `fullSubs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.fullSubs>`__)

If the keyword argument ``numeric`` is True (default is False), functions and constants are numerically evaluated in floating point numbers.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 61-74
    :lineno-start: 61

This yields:

.. code-block:: text

    R_defined            : 1/(2*pi*C*f_c)
    R_evaluated          : 50/pi
    R_defined_numeric    : 0.159154943091895/(C*f_c)
    R_evaluated_numeric  : 15.9154943091895

Obtain the values of multiple parameters
========================================

With a list of parameter names as argument, the method `circuit.getParValue() <../reference/SLiCAPprotos.html#SLiCAP.SLiCAPprotos.circuit.getParValue>`__  returns a dictionary with key-value pairs. The keys are the names of the parameters and the values their defenition or evaluation of it. 

If the keyword argument ``substitute`` is True (default), for each parameter, all circuit parameter definitions are recursively substituted until a final value or expression is obtained (see `fullSubs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.fullSubs>`__)

If the keyword argument ``numeric`` is True (default is False), functions and constants are numerically evaluated in floating point numbers.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 76-80
    :lineno-start: 76

This yields: 

.. code-block:: text

    {R: 1/(2*pi*C*f_c), C: 1/100000000}
    {R: 0.159154943091895/(C*f_c), C: 1.00000000000000e-8}
    {R: 50/pi, C: 1/100000000}
    {R: 15.9154943091895, C: 1.00000000000000e-8}  
    
.. image:: /img/colorCode.svg

Display tables with parameters on HTML pages or in LaTeX documents
==================================================================

With the aid of the report module `Create reports <reports.html>`_, tables with circuit parameter definitions and tables with undefined circuit parameters can be displayed on HTML pages or in LaTeX documents.

Below the script for generating table rst snippets for this help file.

.. literalinclude:: ../parameters.py
    :linenos:
    :lines: 82-88
    :lineno-start: 82
    
Below, both tables for the RC circuit.

.. include:: ../sphinx/SLiCAPdata/table-RC_pardefs.rst

.. include:: ../sphinx/SLiCAPdata/table-RC_params.rst

.. image:: /img/colorCode.svg
