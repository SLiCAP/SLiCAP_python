==============================
SLiCAP circuit matrix equation
==============================

.. image:: /img/colorCode.svg

One of the first steps in the execution of each instruction is the construction of the MNA matrix equation (MNA: Modified Nodal Analysis). The matrix equation depends on the transfer type and the conversion type. 

Every instruction returns the MNA matrix equation. The instruction ``doMatrix()`` returns the matrix equation without evaluating anything. It is the fastest way to obtain this equation.

The default settings of the transfer type and the conversion type in the ``doMatrix()`` are both ``None``.

Settings for transfer types will be discussed in `Work with feedback circuits <feedback.html>`_.

Settings for conversion types will be discussed in `Work with balanced circuits <balanced.html>`_.

.. image:: /img/colorCode.svg
   
SLiCAP output dispalyed on this manual page, is generated with the script: ``matrix.py``, imported by ``Manual.py``.

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

Obtain the matrix equation of the circuit
=========================================

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 9-20
    :lineno-start: 9

The result is shown below:

.. image:: /img/Transimpedance.svg
    :width: 450 px
    
.. code-block:: text

    Matrix([[0], [I_s], [0]])
    Matrix([[0, 1, 0], [0, C_s*s + 1/R_t, -1/R_t], [1, -1/R_t, 1/R_t]])
    Matrix([[I_N1], [V_in], [V_out]])
    
Naming of the dependent variables
=================================

Nodal voltages are named as ``V_<node_name>``, where ``node_name`` is the name of the node.

Branch currents are named as ``I_<ref_des>``, where ``ref_des`` is the reference designator of the branch element. 
    
Display the matrix equation on HTML pages and in LaTeX documents
================================================================

With the aid of the report module `Creating reports <reports.html>`_, the matrix equation can be displayed on HTML pages or in LaTeX documents. 

Below the script for generating the rst snippet for this help file.

.. literalinclude:: ../matrix.py
    :linenos:
    :lines: 22-25
    :lineno-start: 22
    
The result is shown below.

.. include:: ../sphinx/SLiCAPdata/eqn-matrix-trimp.rst

.. image:: /img/colorCode.svg
