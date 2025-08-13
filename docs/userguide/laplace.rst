=======================
SLiCAP Laplace analysis
=======================

.. image:: ../img/colorCode.svg

Symbolic complex frequency domain analysis provides:

- A Laplace transfer function

  This is the Laplace Transform of the unit impulse response from a circuit having the signal source as input signal, and the detector voltage or current as output signal.
      
- The Laplace Transform of a detector voltage or current with the voltages and currents of the independent sources as input signals.
  
  .. admonition:: Important
      :class: note
      
      The ``value`` parameter of independent sources must be specified in the Laplace domain:
      
      Some examples of time functions and their Laplace Transform:
      
      #. Impulse: :math:`a \delta (t) \Leftrightarrow a`
      #. Step: :math:`a \mu (t) \Leftrightarrow \frac{a}{s}`
      #. Linear ramp: :math:`at \Leftrightarrow \frac{a}{s^2}`
      #. Sine: :math:`a\sin{(\omega t)} \Leftrightarrow \frac{a \omega}{s^2+\omega^2}`
      #. Cosine: :math:`a\cos{(\omega t)} \Leftrightarrow \frac{a s}{s^2+\omega^2}`
      #. Real exponential: :math:`a \exp{(-At)} \Leftrightarrow \frac{a}{s+A}`
      #. Use Laplace output of other circuits as input
      #. Use built-in filter Laplace filter responses as input

SLiCAP can perform mixed symbolic/numeric Laplace analysis and has a number of supporting functions for processing the results.

SLiCAP output displayed below, is generated with the script: ``laplace.py``, imported by ``Manual.py``.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 1-7
    :lineno-start: 1

Perform Laplace analysis
========================

Create a circuit object
-----------------------

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 10
    :lineno-start: 10
    
.. image:: /img/myPassiveNetwork.svg
    :width: 700px
       
Obtain the Laplace Transform of the gain
----------------------------------------

The function `doLaplace() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doLaplace>`__ returns the Laplace Transform of a transfer, or of a detector voltage or current.

Below a script for obtaining the Laplace Transform of the source-detector transfer (gain) of the circuit.
    
.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 12-15
    :lineno-start: 12

.. admonition:: Note
    :class: note
    
    - The default value of the *keyword argument* ``transfer`` is ``gain``, which is the transfer from source to load.
    - By default, the source and the detector as defined in the circuit  will be used.
    - The default value of the *keyword argument* ``pardefs`` is ``None``. Hence, parameter definitions will not be substituted in element expressions.
    - The default value of the *keyword argument* ``numeric`` is ``None``. Hence, no numeric evaluation takes place.
    - The default value of the *keyword argument* ``convtype`` is ``None``. Hence, no differential-mode or common-mode conversion will be applied.
    
The result is shown below.

.. code-block:: text

    R_ell*(C_b*L*s**2 + 1)/((R_ell + R_s)*(C_a*C_b*L*R_ell*R_s*s**3/(R_ell + R_s) + s**2*(C_a*L*R_ell + C_b*L*R_ell + C_b*L*R_s)/(R_ell + R_s) + s*(C_a*R_ell*R_s + L)/(R_ell + R_s) + 1))
    
This can be typesetted using the formatter. The script below shows how to create an RST snippet for the source of this help file.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 70-73
    :lineno-start: 70
    
.. include:: ../sphinx/SLiCAPdata/eqn-laplace-passive.rst

Numeric evaluation after subsititution of all the parameters:

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 24-26
    :lineno-start: 26

Below the result.
    
.. code-block:: text

    (455945326390521*s**2/500000000000000000000000000000 + 9/10)/(455945326390521*s**3/400000000000000000000000000000000000 + 1175660591821169*s**2/50000000000000000000000000000 + 1127*s/1000000000 + 1)

    
SLiCAP uses rational numbers. Typsetting functions convert them into float. The number of digits is set with ``ini.disp``

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.ini.disp
    
    4

Below the typesetted numeric transfer:
       
.. include:: ../sphinx/SLiCAPdata/eqn-laplace-passive-numeric.rst

Obtain the Laplace Transform of a detector voltage or current
-------------------------------------------------------------

With the keyword argument ``transfer=None``, SLiCAP evaluates the response at the detector. The vector with independent variables now contains the values of all independent sources defined in the circuit. In this case we have :math:`V_\mathrm{V1}=\frac{1}{s}`.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 28
    :lineno-start: 28

.. include:: ../sphinx/SLiCAPdata/eqn-laplace-passive-vout.rst

Return attributes
=================

.. admonition:: Important
    :class: note
    
    The evaluation of the Laplace Transform, requires:
    
    #. Creation of the matrix equation
    #. Evaluation of the denominator ``doDenom()``
    #. Evaluation of the numerator ``doNumer()``
    #. Evaluation of numerator/denominator
    
    This returns the following result attributes:
    
    .. literalinclude:: ../laplace.py
        :linenos:
        :lines: 17-22
        :lineno-start: 17
    
    The matrix equation is for ``transfer="gain"``: the value of the signal source has been set to unity:
    
    .. include:: ../sphinx/SLiCAPdata/eqn-matrix-passive.rst
               
Related math functions
======================

Coefficients of a Laplace rational function
--------------------------------------------

The function `coeffsTransfer() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.coeffsTransfer>`__ returns a tupe with:

#. A gain factor = normalization coefficient.
#. A list with normalized numerator coefficients of the Laplace variable ``ini.laplace=s`` in ascending order.

   Normalization: the lowest order nonzero coefficient is normalized to unity.
   
#. A list with normalized denominator coefficients of the Laplace variable ``ini.laplace=s`` in ascending order.

   Normalization: the lowest order nonzero coefficient is normalized to unity.
   
.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 30-37
    :lineno-start: 30

This yields:
    
.. code-block:: text

    Gain factor: R_ell/(R_ell + R_s)

    Numerator coefficients of 's':
    0 1
    1 0
    2 C_b*L

    Denominator coefficients of 's':
    0 1
    1 (C_a*R_ell*R_s + L)/(R_ell + R_s)
    2 L*(C_a*R_ell + C_b*R_ell + C_b*R_s)/(R_ell + R_s)
    3 C_a*C_b*L*R_ell*R_s/(R_ell + R_s)

Typesetted:

.. include:: ../sphinx/SLiCAPdata/table-coeffs-gain.rst

Obtain circuit component values using a prototype function 
----------------------------------------------------------

The function `equateCoeffs() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.equateCoeffs>`__ can be used to determine component values of a circuit, such that its transfer equals that of a prototype transfer (rational) function.

An example that demonstrates the design of a 4-th order Linkwitz-Riley passive loudspeaker cross-over filter can be downloaded from github: `FilterDesign <https://github.com/SLiCAP/SLiCAPexamples/tree/main/Examples/FilterDesign>`_.

Obtain a Butterworth polynomial
-------------------------------

The function `butterworthPoly(n) <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.butterworthPoly>`__ returns a normalized (:math:`\omega=1` rad/s) Butterworth polynomial of the n-th order.

Below the code for obtaining a normalized Butterworth polynomial of the 4-th order.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 39, 40
    :lineno-start: 39

The results are shown below

.. include:: ../sphinx/SLiCAPdata/eqn-BuP.rst

Obtain a Bessel polynomial
--------------------------

The function `besselPoly(n) <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.besselPoly>`__ returns a normalized (:math:`\omega=1` rad/s) Bessel polynomial of the n-th order.

Below the code for obtaining a normalized Bessel polynomial of the 4-th order.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 42, 43
    :lineno-start: 42

This yields:

.. include:: ../sphinx/SLiCAPdata/eqn-BeP.rst

Obtain a Chebyshev type 1 polynomial
------------------------------------

The function `chebyshev1Poly(n, ripple) <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.chebyshev1Poly>`__ returns a normalized (:math:`\omega=1` rad/s) Chebyshev polynomial of the n-th order, with ``ripple`` dB pass-band ripple.

Below the code for obtaining a normalized Chebyshev polynomial of the 4-th order with 1 dB pass-band.

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 45, 47
    :lineno-start: 45

This yields:

.. include:: ../sphinx/SLiCAPdata/eqn-ChP.rst

Obtain a filter prototype function
----------------------------------

The function `filterFunc() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.filterFunc>`__ returns a prototype filter function.

The script below returns *low-pass, high-pass, band-pass, band-stop, * and *all-pass* filter functions of the order 2, based on a *Butterworth* polynomial (maximally-flat magnitude chraracteristic).

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 49-59
    :lineno-start: 49

This yields:

.. include:: ../sphinx/SLiCAPdata/eqn-FLP.rst
.. include:: ../sphinx/SLiCAPdata/eqn-FHP.rst
.. include:: ../sphinx/SLiCAPdata/eqn-FBP.rst
.. include:: ../sphinx/SLiCAPdata/eqn-FBS.rst
.. include:: ../sphinx/SLiCAPdata/eqn-FAP.rst

Example 3-rd order Chebyshev type 1 bandpass 900 Hz-1200 Hz
-----------------------------------------------------------

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 61-74
    :lineno-start: 61
    
.. image:: /img/BP4.svg
    :width: 500

The transfer function of this filter:

.. include:: ../sphinx/SLiCAPdata/eqn-BP_num.rst

Inverse Laplace Transform
-------------------------

SLiCAP has a built-in symbolic and numeric Inverse Laplace Transform function `ilt() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.ilt>`__. However, it is preferred to use time-domain analysis for this purpose.

Symbolic Inverse Laplace Transform is implemented for lower order rational functions and functions that are implemented in Sympy.

Numeric Inverse Laplace Transform is implemented for rational functions of any order.

Display equations on HTML pages and in LaTeX documents
======================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../laplace.py
    :linenos:
    :lines: 76-93
    :lineno-start: 76

Plot frequency characteristics
==============================

SLiCAP plot functions are discussed in `Create plots <plots.html>`_

.. image:: /img/colorCode.svg
