===========================
SLiCAP time-domain analysis
===========================

.. image:: ../img/colorCode.svg

The following time-domain analysis functions are implemented in SLiCAP:

- `doImpulse() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doImpulse>`__ returns an expression for the unit-impulse response of a transfer. It is obtained as the Inverse Laplace Transform of the Laplace transfer function.
   
- `doStep() <..//reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doStep>`__ returns an expression for the unit-step response of a transfer. It is obtained as the Inverse Laplace Transform of the product of :math:`\frac{1}{s}` and Laplace transfer function.
   
- `doTime() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doTime>`__ returns an expression for the time domain response, considering the Laplace values of all independent sources in the circuit.
   
.. admonition:: Important
    :class: note
    
    SliCAP calculates all time-domain responses using the Inverse Laplace Transform. If it fails to do so, it returns a non-evaluated expression.

SLiCAP output displayed on this manual page, is generated with the script: ``ttime.py``, imported by ``Manual.py``.

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 1-18
    :lineno-start: 1

The circuit diagram of the circuit ``ACcoupling``:
    
.. image:: /img/ACcoupling.svg
    :width: 400
    
The source signal signal is a sinusoidal voltage with an amplitude of :math:`V_p` V and a frequency of :math:`f_s` Hz. It is specified with its Laplace Transform:

.. math::

    V_\mathrm{V2} = V_p\frac{2 \pi f_s}{s^2 + \left( 2 \pi f_s \right)^2}
    
The power supply voltage steps from zero to :math:`V_B`:

.. math::

    V_\mathrm{V1} = V_B\frac{1}{s}
      
Unit-impulse response
=====================

Symbolic unit-impulse response
------------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 20-21
    :lineno-start: 20
    
This yields (rendered output from formatter):

.. include:: ../sphinx/SLiCAPdata/eqn-ACcoupling-power-impulse.rst

Numeric unit-impulse response
-----------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 23-25
    :lineno-start: 23

This yields:

.. code-block:: text

    -1652892.56198347*exp(-1818181.81818182*t)
    
Unit-step response
==================

Symbolic unit-step response
---------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 27-28
    :lineno-start: 27
    
This yields (rendered output from formatter):

.. include:: ../sphinx/SLiCAPdata/eqn-ACcoupling-signal-step.rst

Numeric unit-step response
--------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 31-33
    :lineno-start: 31

This yields:

.. code-block:: text

    0.5 - 0.454545454545455*exp(-1818181.81818182*t)
    
Time-domain response
====================

Symbolic time-domain response
-----------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 34-35
    :lineno-start: 34
    
This yields (rendered output from formatter):

.. include:: ../sphinx/SLiCAPdata/eqn-ACcoupling-time.rst

.. admonition:: Note
    :class: note
    
    SLiCAP can handle very large equations!
    
    However: In order to provide useful design information:
    
    "Models should be as simple as possible, but not simpler"

Numeric time-domain response
----------------------------

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 37-49
    :lineno-start: 37
    
The plot is hown below.

.. image:: /img/AC_time.svg
    :width: 500px

Return attributes
=================
    
.. admonition:: Important
    :class: note
    
    Calculation of the unit impulse response requires execution of:
    
    - `doNumer() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNumer>`__
    - `doDenom() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doDenom>`__
    - `doLaplace() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doLaplace>`__
    
    This returns the following result attributes:
    
    .. literalinclude:: ../ttime.py
        :linenos:
        :lines: 43-49
        :lineno-start: 43

Related math functions
======================

Convert a step response into a periodic pulse response
------------------------------------------------------

The function `step2PeriodicPulse <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.step2PeriodicPulse>`__ converts a step response into a periodic pulse response.

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 51-57
    :lineno-start: 51
    
Formatted result:

.. include:: ../sphinx/SLiCAPdata/eqn-H_3p-time.rst

where :math:`\theta(t)` is *Sympy's Heaviside Function*, occuring at :math:`t=0` (see below).

.. admonition:: Warning
    :class: warning
    
    Numeric evaluation of periodic periodic pulse responses created in this way, may take a while!
    
Sympy's Heaviside function
--------------------------

`sympy.Heaviside(t, 1) <https://docs.sympy.org/latest/modules/functions/special.html#sympy.functions.special.delta_functions.Heaviside>`_: :math:`\theta(t,1)=0` for :math:`t<0` and :math:`\theta(t,1)=1` for :math:`t \ge 0`.

.. code-block::

    >>> import sympy as sp
    >>> sp.Heaviside(-1,1)
    0
    >>> sp.Heaviside(0,1)
    1
    >>> sp.Heaviside(1,1)
    1
    
Display equations on HTML pages and in LaTeX documents
======================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../ttime.py
    :linenos:
    :lines: 59-73
    :lineno-start: 59

Plot frequency characteristics
==============================

SLiCAP plot functions are discussed in `Create plots <plots.html>`_

.. image:: /img/colorCode.svg
