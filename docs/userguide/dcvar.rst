=============================
SLiCAP DC and dcvar analysis
=============================

.. image:: ../img/colorCode.svg

SLiCAP dc variance analysis `doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__ is intended to set up design equations for offset and bias voltages and currents, and for resistor tolerances. Similar as with noise analysis, SLiCAP can determine the detector-referred and the source-referred variance of a DC voltage or current. To this end, independent sources are assigned a mean DC value and an absolute variance, while resistors can be assigned a relative variance. Resistor temperature tracking and tolerance matching is achieved by assigning resistors to a lot. 

SLiCAP output displayed on this manual page, is generated with the script: ``dcvar.py``, imported by ``Manual.py``.

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

dc and dcvar parameters
=======================

A `doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__ analysis is always preceeded by a `doDC() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDC>`__ analysis. The DC analysis results are used to convert resistor tolerances into resistor error currents. 

SLiCAP uses the ``dc`` parameter of independent sources during `doDC() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDC>`__ analysis and the ``dcvar``, and ``dcvarlot`` parameters during `doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__ analysis.

Voltage source DC variance
--------------------------

The ``dcvar`` parameter of `independent voltage sources <../syntax/devices.html#v-independent-voltage-source>`__ must be specified in :math:`\mathrm{V^2}`. The variance is the square of the standard deviation.

The netlist syntax of a voltage source ``V1`` connected between ``nodeP`` and ``nodeN`` with a mean (DC) value of 1 V and a standard deviation of 10 mV is:

.. code-block:: text

    V1 nodeP nodeN V value=0 dc=1 dcvar=1e-4 noise=0

Current source DC variance
--------------------------

The ``dcvar`` parameter of `independent current sources <../syntax/devices.html#i-independent-current-source>`__ must be specified in :math:`\mathrm{A^2}`

The netlist syntax of a current source ``I1`` flowing from ``nodeP`` to ``nodeN`` with a mean (DC) value of 1 mA and a standard deviation of 1 uA is:

.. code-block:: text

    I1 nodeP nodeN V value=0 dc=1e-3 dcvar=1e-12 noise=0
    
Resistor tolerance and matching tolerance
-----------------------------------------

SLiCAP models resistor tolerances by placing independent error current sources in parallel with the resistor. To this end, it first evaluates the DC current through the resistor and places an independent current source in parallel with this resistor. The ``dcvar`` parameter of this current source is set to the product of the squared DC resistor current and the relative variance of its resistance.

.. admonition:: dcvar analysis
   :class: note
   
   SLiCAP adds dc error current sources in parallel with resistors that have a nonzero ``dcvar`` parameter. These current sources obtain the reference designator ``I_dcvar_<resID>``, where ``resID`` is the reference designator of the resistor. After dcvar analysis, all independent current sources with reference designators starting with ``I_dcvar_`` will be removed from the circuit.
   
If the resistor tolerance partly matches with that of resistors belonging to the same lot, the matching error current is derived from a voltage source of which ``dcvar`` describes the matching part of the variance. The ``dcvar`` parameters of the individual resistors model the mismatch.

.. admonition:: lot specification
    :class: note
    
    For each ``dcvarlot`` specification, SLiCAP adds a grounded independent voltage source that has a nonzero ``dcvar`` parameter. These voltage sources obtain the reference designator ``V_dcvar_<dcvarlot_xx>``, where ``dcvarlot_xx`` is the value of the ``dcvarlot`` parameter. A voltage-controlled current source with reference designator ``G_dcvar_<resID>`` converts the voltage from this voltage source into an error current in parallel with the resistor. The gain of this conversion equals the DC current through the resistor. After dcvar analysis, all independent voltage sources sources with reference designators starting with ``V_dcvar_``, and all voltage-controlled current sources starting with reference designator ``G_dcvar_`` with will be removed from the circuit.

Modeling of temperature dependency
----------------------------------
    
Both the mean value (``dc``) and the variance (``dcvar``) of voltage sources, current sources and resistors can be made temperature dependent. 

Below the syntax of a resistor ``R1`` connected between ``nodeP`` and ``nodeN``, with a temperature coefficient :math:`\mathrm{TC}`, a relative tolerance (1-:math:`\sigma` value) of 0.5% and a temperature coefficient tolerance of 2%.

.. code-block:: text

    R1 nodeP nodeN R value={1+TC*(T-T_0)} dcvar={0.5^2 + TC*(T-T_0)*0.02^2} noisetemp=0 noiseflow=0   
    
Temperature tracking is modeled by using similar temperature dependency expressions for tracking devices.

Subcircuits with dcvar
======================

Built-in subcircuits
--------------------

Below an overview of subcircuits and symbols for dcvar analysis. Subcircuits are defined in the library ``SLiCAP.lib`` in the folder indicated by ``ini.main_lib_path``.

=============== ============================================ ================== ======= ================== =========
subcircuit name description                                  parameters         KiCAD   gschem/Lepton-EDA  LTspice
=============== ============================================ ================== ======= ================== =========
N_dcvar         Nullor with equivalent-input bias and offset sib, sio, svo, iib N_dcvar N_dcvar            SLN_dcvar
O_dcvar         Nullor with equivalent-input bias and offset sib, sio, svo, iib O_dcvar O_dcvar            SLO_dcvar
=============== ============================================ ================== ======= ================== =========

Wide table: slide below the table!

Create dcvar elements
---------------------

The user can create circuits for dcvar analysis using independent dcvar sources, resistors and predefined dcvar subcircuits from above.

DC variance analysis
====================

At the beginning of a `doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__, SLiCAP performs a `doDC() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDC>`__ analysis and adds resistor error current sources to the circuit (see above).

.. admonition:: Important
    :class: note
    
    The function `doDCvar() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDCvar>`__ sets the attributes ``dcSolve``, ``ovar``, ``svarTerms``, and ``ovarTerms`` of the returned instruction object. The attributes ``ivar`` and ``ivarTerms`` are only set if the circuit has a source specification.

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 9-12
    :lineno-start: 9
        
.. image:: /img/dcMatchingTracking.svg
    :width: 800
    
DC solution
-----------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 14-16
    :lineno-start: 14
    
This yields:

.. code-block:: text

    Matrix([[-V_DC_T/(R_a + R_b)], [V_DC_T], [R_b*V_DC_T/(R_a + R_b)]])
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-dcSolve.rst
   
.. admonition:: Important
    :class: note
    
    ``doDCvar()`` returns the matrix equation of the **DC solution**. Hence, dcvar sources of resistors are not shown.
    
    .. include:: ../sphinx/SLiCAPdata/eqn-dcMatrix.rst
    
Detector-referred DC variance
-----------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 18-19
    :lineno-start: 15
    
This yields:

.. code-block:: text

    2*R_a**2*R_b**2*V_DC_T**2*var_m/(R_a + R_b)**4 + R_b**2*V_DC_T**2*sigma_V**2/(R_a + R_b)**2
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-ovar.rst

Source-referred DC variance
---------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 21-22
    :lineno-start: 21
    
This yields:

.. code-block:: text

    2*R_a**2*V_DC_T**2*var_m/(R_a + R_b)**2 + V_DC_T**2*sigma_V**2
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-ivar.rst

Contributions to detector-referred and source-referred DC variance
------------------------------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 24-31
    :lineno-start: 24

This yields:

.. code-block:: text

    = V1 =
    value        : V_DC_T**2*sigma_V**2
    det-referred : R_b**2*V_DC_T**2*sigma_V**2/(R_a + R_b)**2
    src-referred : V_DC_T**2*sigma_V**2

    = I_dcvar_R1 =
    value        : V_DC_T**2*var_m/(R_a + R_b)**2
    det-referred : R_a**2*R_b**2*V_DC_T**2*var_m/(R_a + R_b)**4
    src-referred : R_a**2*V_DC_T**2*var_m/(R_a + R_b)**2

    = V_dcvar_lot_1 =
    value        : T_Delta**2*sigma_TC_R**2 + sigma_R**2
    det-referred : 0
    src-referred : 0

    = I_dcvar_R2 =
    value        : V_DC_T**2*var_m/(R_a + R_b)**2
    det-referred : R_a**2*R_b**2*V_DC_T**2*var_m/(R_a + R_b)**4
    src-referred : R_a**2*V_DC_T**2*var_m/(R_a + R_b)**2
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/table-varContribs.rst

Tolerances, temperature drift, matching and tracking
====================================================

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 11-26
    :lineno-start: 11
    
No tolerances and no temperature coefficients
---------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 49-63
    :lineno-start: 49

This yields:

.. code-block:: text

    V_out     : V_DC/A
    I(V1)     : -V_DC/(A*R)
    var{I(V1)}: 0

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_1.rst

DC voltage soure with standard deviation
----------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 65-79
    :lineno-start: 65

This yields:

.. code-block:: text

    Case 2
    V_out     : V_DC/A
    I(V1)     : -V_DC/(A*R)
    var{I(V1)}: V_DC**2*sigma_V**2/(A**2*R**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_2.rst

DC voltage soure with temperature coefficient
---------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 81-96
    :lineno-start: 81

This yields:

.. code-block:: text

    Case 3
    V_out     : V_DC*(TC_V*T_Delta + 1)/A
    I(V1)     : -V_DC*(TC_V*T_Delta + 1)/(A*R)
    var{I(V1)}: 0
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_3.rst

DC voltage soure with stddev. and tempco.
-----------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 98-112
    :lineno-start: 98

This yields:

.. code-block:: text

    Case 4
    V_out     : V_DC*(TC_V*T_Delta + 1)/A
    I(V1)     : -V_DC*(TC_V*T_Delta + 1)/(A*R)
    var{I(V1)}: V_DC**2*sigma_V**2*(TC_V*T_Delta + 1)**2/(A**2*R**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_4.rst

Rel. stddev of resistor values, perfect matching
------------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 114-130
    :lineno-start: 114

This yields:

.. code-block:: text

    Case 5
    V_out     : V_DC/A
    I(V1)     : -V_DC/(A*R)
    var{I(V1)}: V_DC**2*sigma_R**2/(A**2*R**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_5.rst

Rel. stddev of resistor values, perfect matching and tracking
-------------------------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 132-147
    :lineno-start: 132

This yields:

.. code-block:: text

    Case 6
    V_out     : V_DC/A
    I(V1)     : -V_DC/(A*R*(TC_R*T_Delta + 1))
    var{I(V1)}: V_DC**2*sigma_R**2/(A**2*R**2*(TC_R*T_Delta + 1)**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_6.rst

Rel. stddev of resistor values, imperfect matching and tracking
---------------------------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 149-166
    :lineno-start: 149

This yields:

.. code-block:: text

    Case 7
    V_out     : V_DC/A
    I(V1)     : -V_DC/(A*R*(TC_R*T_Delta + 1))
    var{I(V1)}: V_DC**2*(2*A**2*(T_Delta**2*sigma_TC_R**2 + sigma_R**2) + (T_Delta**2*sigma_TC_tr_R**2 + sigma_m_R**2)*((A - 1)**2 + 1))/(2*A**4*R**2*(TC_R*T_Delta + 1)**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_7.rst

V src stddev and tempco, rel. res. stddev. imperf. matching/tracking
--------------------------------------------------------------------

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 168-186
    :lineno-start: 168

This yields:

.. code-block:: text

    Case 8
    V_out     : V_DC*(TC_V*T_Delta + 1)/A
    I(V1)     : -V_DC*(TC_V*T_Delta + 1)/(A*R*(TC_R*T_Delta + 1))
    var{I(V1)}: V_DC**2*(2*A**2*(T_Delta**2*sigma_TC_R**2 + sigma_R**2 + sigma_V**2) + (T_Delta**2*sigma_TC_tr_R**2 + sigma_m_R**2)*((A - 1)**2 + 1))*(TC_V*T_Delta + 1)**2/(2*A**4*R**2*(TC_R*T_Delta + 1)**2)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-I_ovar_8.rst

.. image:: /img/colorCode.svg

Display equations on HTML pages and in LaTeX documents
======================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../dcvar.py
    :linenos:
    :lines: 188-203
    :lineno-start: 188
    
The typesetted tables and equations are shown on this page.
