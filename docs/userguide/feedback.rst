===========================
Work with feedback circuits
===========================

.. image:: ../img/colorCode.svg

Feedback is a powerful design technique. With the aid of negative feedback (also: *corrective feedback*), accurate, approximate linear and wideband amplifiers can be designed with passive feedback networks around a controller (also: *error amplifier*). The controller itself doensn't need to be accurate, linear, nor does it need to have a large bandwidth. Its only task is to provide a sufficiently large loop gain over the operating range of interest.

With the aid of positive feedback (also: *regenerative feedback*) sustainable oscillations can be obtained by compensation losses in resonators. Weak positive feedback is also used for changing impedances or increasing gain.

SLiCAP has the asymptotic-gain model built in for the analysis and design of negative feedback circuits (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

This model requires the selection of a controlled source as `loop gain reference <analysis.html#the-loop-gain-reference>`__.

With the aid of the asymptotic-gain model, the transfer of a feeback circuit is written as:

.. math::

    A_f=A_{f\infty}\frac{-L}{1-L} + \frac{\rho}{1-L}
    
where:

- :math:`A_f` is the **gain**, defined as the transfer from the signal source to the detector.
- :math:`A_{f\infty}` is the **asymptotic-gain**, defined as the gain with the transfer of the loop gain reference appoaching infinity.
- :math:`L` is the **loop gain**, defined as the gain enclosed in the loop around the loop gain reference.
- :math:`\rho` is the **direct transfer**, defined as the gain with the transfer of the loop gain reference set to zero.

.. admonition:: Important
    :class: note
    
    The gain :math:`A_f` found from the asymptotic-gain model always exactly matches the gain found from network analysis; independent of the selected loop gain reference.

    The asymptotic-gain model gives meaningful design information for the loop tarnsfer function (loop gain), if the *asymptotic-gain* equals the **ideal gain**. The **ideal gain** is defined as the gain with of the feedback amplifier of which the controller (also called: *error-amplifier*) is replaced with a **nullor**:
    
    #. The current in both input terminals of the controller equals zero
    #. The voltage across the input port of the controller equals zero
    #. The controller is a natural two-port

SLiCAP has six built-in ``transfer`` types for `do<Instruction>() <../reference/SLiCAPshell.html#general-instruction-format>`__:

- **None**: SLiCAP calulates the detector voltage or current
- **gain**: SLiCAP calulates the transfer from the signal source to the detector.   
- **asymptotic**: the asymptotic gain, defined above. 

  SLiCAP calculates the asymptotic gain by replacing the loop gain reference with a nullor.
  
- **direct**: the direct transfer, defined above. 

  SLiCAP calculates the direct transfer by setting the gain of the loop gain reference to zero.
  
- **loopgain**: the loop gain, defined above. 

  SLiCAP calculates the loop gain from the return difference with the selected loop gain reference.
  
- **servo**: the *servo function*, defined as :math:`\frac{-L}{1-L}`. 

  SLiCAP calculates the servo function from the return difference with the selected loop gain reference.
  
  With a proper selection of the loop gain reference, the *servo function* is a measure for the discrepancy between the *ideal-gain* and the *gain*. As such, it contains important design information.

.. admonition:: Important
    :class: note
    
    In the asymptotic-gain model, **negative feedback** (also: *corrective feedback*) corresponds with a negative loop gain! A positive loop gain indicates **positive feeedback** (also: *regenerative feedback*).
 
SLiCAP output displayed on this manual page, is generated with the script: ``feedback.py``, imported by ``Manual.py``.

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 1-11
    :lineno-start: 1
    
Loop gain reference selection
=============================

Voltage-feedback opamps
-----------------------

The voltage-controlled voltage source in the voltage-feedback operational amplifier (`model OV <../syntax/devices.html#model-ov>`__) is a good loop gain reference candidate. However, with a nonzero common-mode input conductance or a nonzero common-mode input capacitance, the SLiCAP built-in voltage feedback operational amplifier model is **NOT** a natural two-port. Hence, in feedback amplifiers with a floating controller input port, the asymptotic-gain generally not equals the ideal gain. In most cases, the common-mode input elements, however, can be absorbed in the external network around the controller, thereby re-establishing the correspondence between the ideal and the asymptotic-gain (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

Current-feedback opamps
-----------------------

The current-controlled voltage source in the current-feedback operational amplifier (`model OC <../syntax/devices.html#model-oc>`__) is the best candidate for the loop gain reference. This is because the voltage-controlled current source is part of a local feedback loop. However, with a nonzero input conductance or a nonzero input capacitance, the SLiCAP built-in current feedback operational amplifier model is **NOT** a natural two-port. Hence, in feedback amplifiers with a floating controller input port, the asymptotic gain will not equal the ideal gain. In most cases, the elements modeling the positive input impedance can be absorbed in the network around the controller, thereby re-establishing the correspondence between the ideal and the asymptotic-gain (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

Single-transistor stages
------------------------

The CS-stage and the CE-stage suffer from parasitic feedback through the drain-gate and the collector-base capacitance, respecively. Useful design information about the loop gain and the servo function of multi-stage feedback amplifiers is obtained if this local feedback plays no role in the frequency range of interest, or if it is eliminated in the stage of which the transcondactance is the loop gain reference (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

Common-drain, common-emitter, common-gate and common-base stages are considered negative feedback stages themselves. Selecting the transconductance of such stages as loop gain reference provides useful design information in single-stage feedback amplifiers only (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

Differential-pair transistor stages
-----------------------------------

SLiCAP provides small-signal models for differential-pair stages. These models have only one voltage-controlled current source that can be selected as loop gain reference. The model results from transforming the anti-series connection of two equal two-ports into one equivalent two-port. Like the CS-stage and the CE-stage, the differential pair suffers from parasitic feedback. Setting the feedback capacitances to zero may be necesseray as discussed above (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

Multiple-controller circuits
----------------------------

In the case of balanced amplifiers with paired controllers, differential-mode and common-mode loops can be designed and analyzed as discussed in `Work with balanced circuits <balanced.html>`_,  (see also: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).

In other multiple-controller circuits the design of one controller is done using nullors for all other controllers.

Example with operational amplifier
==================================

Amplifier feedback concept
--------------------------

The figure below shows the concept of a non-inverting, passive-feedback voltage amplifier. The nullor models the ideal controller (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_).
    
.. image:: /img/VampIdeal.svg
    :width: 350px

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 13-14
    :lineno-start: 13
    
Implementation with operational amplifier
-----------------------------------------

The figure below shows the above amplifier in which the controller is implemented with an operational amplifier.

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 16-17
    :lineno-start: 16
    
.. image:: /img/VampOV.svg
    :width: 450px

Ideal gain
~~~~~~~~~~

The ideal gain is calculated from the circuit with the nullor:
 
.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 19-20
    :lineno-start: 19   
    
.. include:: ../sphinx/SLiCAPdata/eqn-A_v_Ideal.rst

Asymptotic-gain
~~~~~~~~~~~~~~~

The asymptotic gain is calculated using the circuit with the operational amplifier. The nonzero common-mode input admittance of the operational amplifier destroys the natural two-port character of the controller. Hence, the common-mode input capacitance :math:`c_c` is found in the expression for the asymptotic gain:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 22-23
    :lineno-start: 22
  
.. include:: ../sphinx/SLiCAPdata/eqn-OV-A_v_oo.rst  

Substitution of :math:`c_c=0` in the above expression establishes the correspondence between the ideal gain and the asymptotic-gain.

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 29-30
    :lineno-start: 29

.. include:: ../sphinx/SLiCAPdata/eqn-OV-A_v_oo-mod.rst

Loop gain
~~~~~~~~~

The loop gain is calculated as follows:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 29-30
    :lineno-start: 29

Servo function
~~~~~~~~~~~~~~

The servo function is calculated as follows:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 32-33
    :lineno-start: 32

Direct transfer
~~~~~~~~~~~~~~~

The direct transfer is calculated as follows:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 35-36
    :lineno-start: 35

Gain
~~~~

The gain is calculated as:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 38-39
    :lineno-start: 38

Comparison MNA and asymptotic-gain model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below the script that verifies if the gain calculates as :math:`A_f=A_{f\infty}\frac{-L}{1-L}+\frac{\rho}{1-L}` equals the gain obtained from MNA analysis:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 41-54
    :lineno-start: 41

Thie yields:

.. code-block:: text

    PERFECT: The two models give the same source-load transfer!
    
Bode plots feedback model
~~~~~~~~~~~~~~~~~~~~~~~~~

Below the script for plotting magnitude and phase characteristics of the transfers from the asymptotic-gain model:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 56-79
    :lineno-start: 56
    
.. image:: /img/AvOVfb_mag.svg
    :width: 500px
    
.. image:: /img/AvOVfb_phase.svg
    :width: 500px

.. admonition:: Important
    :class: note
    
    - In the asymptotic-gain model a negative loop gain indicates negative feedback.
    - With a properly selected loop gain reference, the asymptotic-gain equals the ideal gain over the frequency range of interest.
    - If the ideal gain matches the asymptotic-gain, the servo function is a good measure for the discrepancy between the asymptotic-gain and the gain. In such cases, the loop gain is the design parameter for this discrepancy.
    - The influence of the direct transfer over the frequency range of interest can almost always be neglected.
    
Example implementation with transistors
---------------------------------------

The voltage amplifier with a two-stage bipolar transistor controller:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 81-82
    :lineno-start: 81
    
.. image:: /img/VampQ.svg
    :width: 600px
    
Asymptotic-gain
~~~~~~~~~~~~~~~

The two-stage controller doesn't behave as a natural two-port. The nonzero output admittance of the first stage introduces a common-mode to differential-mode conversion. In addition, the collector-base capacitance in the second stage introduces local feedback around the selected loop gain reference. Both effects contribute to a mismatch between the ideal gain and the aymptotic-gain. 

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 84-87
    :lineno-start: 83
  
.. include:: ../sphinx/SLiCAPdata/table-coeffsQ-A_v_oo.rst  

The asymptotic-gain with the output admittance of the first stage and the feedback capacitance of the second stage set to zero:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 89-91
    :lineno-start: 89

This yields:

.. include:: ../sphinx/SLiCAPdata/eqn-QV-A_v_oo-mod.rst    

Bode plots feedback model
~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 93-123
    :lineno-start: 93
    
.. image:: /img/AvQVfb_mag.svg
    :width: 500px
    
.. image:: /img/AvQVfb_phase.svg
    :width: 500px
 
Stability and frequency charactersitics
=======================================

.. admonition:: Definition
    :class: note
    
    A (linear) system is stable if the response to a bounded input is bounded.
    
The ultimate test for stability is to excite all states and check if the response is bounded. In systems that do not comprise delay lines, all poles should have negative real parts.

Pole-zero analysis
------------------

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 125-126
    :lineno-start: 125

This yields:

.. code-block:: text

    DC value of gain: 1.78e+01

    Poles of gain:

     n  Real part [Hz]  Imag part [Hz]  Frequency [Hz]     Q [-] 
    --  --------------  --------------  --------------  --------
     0       -1.09e+06        2.55e+06        2.77e+06   1.27e+0
     1       -1.09e+06       -2.55e+06        2.77e+06   1.27e+0
     2       -2.40e+08        0.00e+00        2.40e+08
     3       -5.95e+09        0.00e+00        5.95e+09

    Zeros of gain:

     n  Real part [Hz]  Imag part [Hz]  Frequency [Hz]     Q [-] 
    --  --------------  --------------  --------------  --------
     0        6.78e+07        6.09e+07        9.12e+07   6.72e-1
     1        6.78e+07       -6.09e+07        9.12e+07   6.72e-1
     2       -3.30e+08        0.00e+00        3.30e+08
     
Poles versus circuit parameter
------------------------------

Parameter stepping can be applied to *circuit* parameters.

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 128-145
    :lineno-start: 128
    
.. image:: /img/PZvampbjtIC.svg
    :width: 350px
     
Routh array
-----------

The number of sign changes in the first column of the Routh Array of a polynomial, equals the number of its solutions in the right-half of the complex plane.
 
.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 147-156
    :lineno-start: 147

This yields:

.. code-block:: text

    Number of poles in right half-plane: 0
    
Typesetted Routh array:

.. include:: ../sphinx/SLiCAPdata/eqn-M_routh.rst

Nyquist plot
------------

.. admonition:: Important
    :class: note
    
    A negative value of the loop gain in the asymptotic-gain model, indicates negative feedback. For plotting a traditional "Nyquist Plot", plot :math:`-L` on a polar plot.
    
    Nyquist plots only give meaningful information about the stability with a meaningful loop gain!
    
    A ``Pole-Zero Plot``, the ``Unit Impulse Response``, and the ``Unit Step Response`` always provide useful information about stability!

    .. literalinclude:: ../feedback.py
        :linenos:
        :lines: 158-162
        :lineno-start: 158
        
    .. image:: /img/NyquistQamp.svg
        :width: 500

Related math functions
======================

Servo bandwidth
---------------

`findServoBandwidth() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.findServoBandwidth>`__ takes the (numeric) Laplace transform of the loop gain as input and returns a dictionary with information about the asymptotic approximation of the servo function.
It evaluates the asymptotes of the magnitude characteristic of the loop gain and accepts maximally one region in which this magnitude exceeds unity.

The function can be used to separate dominant poles from non-dominant poles thereby simplifying frequency compensation algorithms.

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 164-167
    :lineno-start: 164

This yields:

.. code-block:: text

    mbv 8.152406382061248
    mbf 0.0
    lpf 2618650.8800096293
    lpo -2.0
    hpf None
    hpo None

- **lpf**: Low-pass cut-off frequency, this is the frequency at which the asymptotic approach of the loop gain magnitude crosses unity with a negative slope.
- **lpo**: Low-pass order, the order of the slope of the asymptote of the loop gain magnitude at f=lpf
- **hpf**: High-pass cut-off frequency, this is the frequency at which the asymptotic approach of the loop gain magnitude crosses unity with a positive slope.
- **hpo**: High-pass order, the order of the slope of the asymptote of the loop gain magnitude at f=hpf
- **mbv**: Largest absolute value of midband loop gain. In this case there is no high-pass and the midband loop gain is the DC value
- **mbf**: Frequency at which this value occurs

The unit of ``lpf`` and ``hpf`` is set by ``ini.hz``; default: "Hz".

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.ini.hz
    
    True

Remove non-dominant poles and zeros
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following script extracts the dominant poles and zeros from all loop gain poles and zeros:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 169-183
    :lineno-start: 169
    
.. code-block:: text

    Poles [rad/s]: [np.float64(-4054666.832864887), np.float64(-8083810.307636836)]
    Zeros [rad/s]: []

Coefficients of a Laplace transfer function
-------------------------------------------

`coeffsTransfer() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.coeffsTransfer>`__ take a Laplace rational function as argument and returns a gain factor, and the normalized coefficients of the numerator and the denominator polynomials.
    
Estimate MFM bandwidth
~~~~~~~~~~~~~~~~~~~~~~

The MFM bandwidth (after frequency compensation) is found as (see: `Structured Electronics Design <https://books.open.tudelft.nl/home/catalog/book/162>`_):

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 185-194
    :lineno-start: 185
    
This yields:

.. code-block:: text

    Achievable MFM bandwidth: 2.76e+6 Hz

Display equations and tables on HTML pages and in LaTeX documents
=================================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../feedback.py
    :linenos:
    :lines: 196-203
    :lineno-start: 196

.. image:: /img/colorCode.svg
