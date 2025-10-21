=====================
SLiCAP noise analysis
=====================

.. image:: ../img/colorCode.svg

SLiCAP noise analysis helps to create design equations for the noise performance of a circuit. 

Noise can be assigned to independent voltage and current sources and to resistors. SLiCAP also has buit-in subcircuits with noise sources.

SLiCAP output displayed on this manual page, is generated with the script: ``noise.py``, imported by ``Manual.py``.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 1-9
    :lineno-start: 1
    
Noise parameters
================

During noise analysis, SLiCAP uses the ``noise`` parameter of independent voltage sources and independent current sources as uncorrelated noise sources. It inserts noise current sources in parallel with resistors with their noise spectrum determined by the parameters ``noisetemp`` and ``noiseflow``.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 10-11
    :lineno-start: 10
    
.. image:: /img/noiseSources.svg
    :width: 350
    
.. literalinclude:: ../cir/noiseSources.cir
    :linenos:

Noise voltage sources
---------------------

The noise parameter of `independent voltage sources <../syntax/devices.html#v-independent-voltage-source>`__ must be specified in :math:`\mathrm{\left[ \frac{V^2}{Hz} \right] }`

In the circuit above, the spectral density of the voltage noise from ``V1`` equals :math:`S_v` :math:`\mathrm{\left[ \frac{V^2}{Hz} \right] }`.

Noise  current sources
----------------------

The noise parameter of `independent current sources <../syntax/devices.html#i-independent-current-source>`__ must be specified in :math:`\mathrm{\left[ \frac{A^2}{Hz} \right] }`

In the circuit above, the spectral density of the curent noise from ``I1`` equals :math:`S_i` :math:`\mathrm{\left[ \frac{A^2}{Hz} \right] }`.

Resistors
---------

The noise contributed by `resistors <../syntax/devices.html#r-resistor>`__ is governed by two parameters:

- ``noisetemp``: The noise temperature of the resistor
- ``noiseflow``: The flicker noise corner frequency
   
.. admonition:: Addition of noise current sources
    :class: note
   
    Before executing a ``doNoise()`` instruction, SLiCAP adds noise current sources in parallel with resistors that have a nonzero positive noise temperature. These current sources obtain the reference designator ``I_noise_<resID>``, where ``resID`` is the reference designator of the resistor. After the noise analysis, all independent current sources with reference designators starting with ``I_noise_`` will be removed from the circuit.

The noise current spectral density :math:`S_\mathrm{I\_noise\_Rxx}` of a resistor ``Rxx`` is set to:

.. math::

    S_\mathrm{I\_noise\_Rxx} = \frac{4kT_{noise_\mathrm{Rxx}}}{R_\mathrm{Rxx}} \left( 1 + \frac{f_{\ell_\mathrm{Rxx}}}{f}\right) \, \mathrm{\left[ \frac{A^2}{Hz}\right]}
    
where: 

- :math:`k` is Boltzmann's constant in [J/K]
- :math:`T_{noise_\mathrm{Rxx}}` is the noise temperature ``noisetemp`` of resistor ``Rxx`` in [K]
- :math:`R_\mathrm{Rxx}` is the resistance ``value`` of ``Rxx`` in [Ohm]
- :math:`f_{\ell_\mathrm{Rxx}}` is the flicker noise corner frequency ``flow`` of ``Rxx`` in [Hz]

In the circuit above:

- the noise temperature of the resistor ``R1`` is set to the gobal parameter :math:`T`
- the flicker noise corner frequency equals :math:`f_{\ell}`

Hence, SLiCAP will insert a noise current source in parallel with ``R1`` with a spectral density:

.. math:: 

    S_\mathrm{I\_noise\_R1} = \frac{4kT}{R_a} \left( 1 + \frac{f_\ell}{f} \right) \, \mathrm{\left[ \frac{A^2}{Hz} \right]}

Global parameters
-----------------

Global parameters are defined in the file ``SLiCAPmodels.lib`` in the folder given by ``ini.main_lib_path``. If global parameters are found in circuit element expressions or in circuit parameter definitions, SLiCAP automatically adds their definition to the circuit parameter definitions.

In the circuit above, the global parameter :math:`T` is found in the ``noisetemp`` parameter of ``R1``. Its definition with a default value of 300 K is added to the circuit parameter definitions:

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 13-14
    :lineno-start: 13

.. code-block:: text

    T 300
    
Noise Analysis
==============

At the beginning of the noise analysis, SLiCAP adds resistor noise current sources to the circuit (see above). This also adds the Boltzmann constant :math:`k` to the circuit parameter definitions:

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 16-19
    :lineno-start: 16
    
This yields:

.. code-block:: text

    T 300
    k 34516213/2500000000000000000000000000000

.. admonition:: Important
    :class: note
    
    The function `doNoise() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doNoise>`__ sets the noise attributes ``onoise``, ``snoiseTerms``, and ``onoiseTerms`` of the returned instruction object. The ``inoise`` and ``inoiseTerms`` attributes are only set if the circuit has a source specification.

Detector-referred noise
-----------------------

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 21-22
    :lineno-start: 21
    
This yields:

.. code-block:: text

    4*T*k*(f + f_ell)*Abs(R_a**2)/(R_a*f*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1)) + S_i*(4*pi**2*L_a**2*f**2 + R_a**2)*Abs(R_a**2)/(R_a**2*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1)) + S_v*Abs(R_a**2)/(R_a**2*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1))
    
Formatted output:

.. include:: ../sphinx/SLiCAPdata/eqn-Svno.rst

Source-referred noise
---------------------

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 24-25
    :lineno-start: 24
    
This yields:

    4*R_a*T*k*(f + f_ell)/f + S_i*(4*pi**2*L_a**2*f**2 + R_a**2) + S_v
    
Formatted output:

.. include:: ../sphinx/SLiCAPdata/eqn-Svni.rst

Contributions to detector-referred and source-referred noise
------------------------------------------------------------

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 27-34
    :lineno-start: 27
    
This yields:

.. code-block:: text

    = I1 =
    value        : S_i
    det-referred : S_i*(4*pi**2*L_a**2*f**2 + R_a**2)*Abs(R_a**2)/(R_a**2*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1))
    src-referred : S_i*(4*pi**2*L_a**2*f**2 + R_a**2)

    = V1 =
    value        : S_v
    det-referred : S_v*Abs(R_a**2)/(R_a**2*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1))
    src-referred : S_v

    = I_noise_R1 =
    value        : 4*T*k*(1 + f_ell/f)/R_a
    det-referred : 4*T*k*(f + f_ell)*Abs(R_a**2)/(R_a*f*(16*pi**4*C_a**2*L_a**2*f**4 + 4*pi**2*C_a**2*R_a**2*f**2 - 8*pi**2*C_a*L_a*f**2 + 1))
    src-referred : 4*R_a*T*k*(f + f_ell)/f
    
Formatted output:

.. include:: ../sphinx/SLiCAPdata/table-noiseContribs.rst

Subcircuits with noise
======================

Built-in subcircuits
--------------------

Below an overview of subcircuits and symbols for noise analysis. Subcircuits are defined in the library ``SLiCAP.lib`` in the folder indicated by ``ini.main_lib_path``.

======================== ======================================================= ============= ============== ================== ===============
subcircuit name          description                                             parameters    KiCAD          gschem/Lepton-EDA  LTspice
======================== ======================================================= ============= ============== ================== ===============
N_noise                  Nullor with equivalent-input noise sources              si, sv        N_noise        N_noise            SLN_noise
O_noise                  Nullor with equivalent-input noise sources              si, sv        O_noise        O_noise            SLO_noise
MN18_noise               NMOS 180nm equivalent-input noise EKV model             ID, IG, W, L  M_noise        M_noise            SLM_noise
MP18_noise               PMOS 180nm equivalent-input noise EKV model             ID, IG, W, L  M_noise        M_noise            SLM_noise
MN18_noisyNullor         Nullor with NMOS 180nm equivalent-input noise EKV model ID, IG, W, L  XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
MP18_noisyNullor         Nullor with PMOS 180nm equivalent-input noise EKV model ID, IG, W, L  XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
MN18_noisyNullor_simple  Nullor with NMOS 180nm equivalent-input noise EKV model ID, IG, W, L  XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
MP18_noisyNullor_simple  Nullor with PMOS 180nm equivalent-input noise EKV model ID, IG, W, L  XM_noisyNullor XM_noisyNullor     SLM_noisyNullor
J_noise                  MOS/JFET equivalent-input noise sources                 ID, IG, W, L  J_noise        M_noise            SLM_noise        
Q_noise                  BJT equivalent-input noise sources, r_b=0               IC, VCE       Q_noise        Q_noise            SLQ_noise
======================== ======================================================= ============= ============== ================== ===============

Wide table: slide below the table!

The subcircuits ``MN18_noisyNullor_simple`` and ``MP18_noisyNullor_simple`` have their noise parameters ``KF`` and ``Gamma``, as well as their input capacitance ``c_iss`` modeled independent of the inversion coefficient.

Create noise elements
---------------------

The user can create noisy circuits or subcircuits using independent noise sources, independend current sources, resistors and predefined noisy subcircuits from above.

Noise post processing functions
===============================

RMS noise
---------

SLiCAP can perform symbolic and numeric integration and calculate the source-referred or detector-referred `rmsNoise <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.rmsNoise>`__ . 

`rmsNoise() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.rmsNoise>`__ calculates the RMS value by integrating each of the noise terms in the ``onoiseTerms`` or the ``inoiseTerms`` attribute of the noise analysis result. For each term it tries to find the best integration method. However, success is not always guaranteed:

- Symbolic integration of functions with many variables, may take very long
- Symbolic integration of functions is not always possible or implemented in Sympy.

The following may help:

- Keep the circuit model as simple as possible and use only one or two symbolic design parameters. 
- Calculate the variance instead of the RMS noise (standard deviation), and try to obtain expressions with symbolic variables as coefficients of numeric integrals (see below).

Below an example how to express the RMS noise in terms of the source spectral densities :math:`S_v` and :math:`S_i`.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 36-49
    :lineno-start: 36
    
This yields:

.. code-block:: text

    711.447029712076*sqrt(S_i + 4.95576373211838e-7*S_v + 7.6162627945633e-24)
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-RMS.rst

Noise Figure
------------

The noise figure of a system is a measure for the deterioration of the signal-to-noise ratio by that system. It can be found as the ratio of the total weighted output noise power (variance) and the contribution of the signal source noise to it. Alternatively, one can take the ratio of the total weighted source-referred noise and the weighted source noise.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 51-55
    :lineno-start: 51
    
This yields:

.. code-block:: text

    2017852.45232533*S_i/S_v + 1.0 + 1.53684945575637e-17/S_v
    
Commonly the noise figure is expressed in [dB]:

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 56-57
    :lineno-start: 56
    
This yields:

.. code-block:: text

    10*log(2017852.45232533*S_i/S_v + 1.0 + 1.53684945575637e-17/S_v)/log(10)
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-F.rst

Noise weighting functions
-------------------------

DIN A
`````

SLiCAP has the frequency weighting function `DIN_A() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.DIN_A>`__, which is often used for spectral weighting of noise and distortion components in audio applications. See `WiKi R_A(f) <https://en.wikipedia.org/wiki/A-weighting>`_.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 59
    :lineno-start: 59

.. code-block:: text
    
    18719114681919*f**4/(100000*sqrt((f**2 + 1159929/100)*(f**2 + 54449641/100))*(f**2 + 10609/25)*(f**2 + 148693636))

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 61-69
    :lineno-start: 61
    
.. image:: /img/DINA.svg
    :width: 500px
    
Correlated Double Sampling
``````````````````````````
Correlated Double Sampling is a technique that suppresses low-frequency noise by periodically taking the difference between two signal samples at a fixed time difference. It is applied in switched integrators used in optical detectors and image sensors.

The function `doCDS() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.doCDS>`__, takes a noise spectrum and a time delay as argument and returns the CDS weighted noise spectrum.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 71-73
    :lineno-start: 71
    
This yields:

.. code-block:: text

    4*S_v*sin(pi*f*tau)**2
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-CDSweighting.rst


.. admonition:: Important
    :class: note
    
    The function `doCDS() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.doCDS>`__ multiplies the input spectrum with the **squared magnitude** of the CDS transfer function. Hence, the input spectrum must be in :math:`\mathrm{\left[ \frac{V^2}{Hz}\right]}`, :math:`\mathrm{\left[ \frac{A^2}{Hz}\right]}` or :math:`\mathrm{\left[ \frac{W}{Hz}\right]}`. Use the ``onoise`` or ``inoise`` attribute of the noise analysis result!
    
.. literalinclude:: ../noise.py
    :linenos:
    :lines: 75-83
    :lineno-start: 75
    
.. image:: /img/CDS.svg
    :width: 500px
    
The function `doCDSint <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.doCDSint>`__ performs both CDS filtering and integration over frequency.

Below the script that calculates the variance of the output voltage of a switched transimpedance integrator with a gain :math:`Z_t=\frac{1}{2\pi f C_i}` and an input noise current with a spectral density :math:`S_i` to which CDS filtering of the output signal with a time delay :math:`\tau` is applied.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 85-87
    :lineno-start: 85

SLiCAP uses :math:`\_\phi=\pi f \tau` rather than :math:`f` as integration variable. Integration is not always possible because the integral may depend on the domain of the variables:

.. code-block:: text

    S_i*tau*Integral(sin(_phi)**2/_phi**2, (_phi, 0, oo*tau))/(pi*C_i**2)
    
As shown above, the integral cannot be evaluated (undefined when :math:`\tau=0`. However, it can be done with the aid of assumptions.

Use assumptions
---------------

Below the script to obtain the integral from above.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 89-91
    :lineno-start: 89

With :math:`\tau>0` the above integral can be evaluated:

.. code-block:: text

    S_i*tau/(2*C_i**2)
    
Typesetted:

.. include:: ../sphinx/SLiCAPdata/eqn-CDSint.rst

The following SLiCAP functions can be used to change the domain of variables:

#. `assumePosParams() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.assumePosParams>`__
#. `assumeRealParams() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.assumeRealParams>`__
#. `clearAssumptions() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.clearAssumptions>`__

Obtain symbolic coefficients of numeric intergals
-------------------------------------------------

Sometimes numeric integration over frequency becomes possible after symbolic design parameters have been elimated from the integral.

The function `integrate_monomial_coeffs() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrate_monomial_coeffs>`__ returns an experssion in which monomials of two selected parameters have been taken out of the integral:

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 93-96
    :lineno-start: 93
    
This yields:

.. code-block:: text

    253078.438043065*S_i + 0.250839388927001*S_v + 3.85502378354722e-18
    
Typesetted:
 
.. include:: ../sphinx/SLiCAPdata/eqn-intCoeffs.rst

The function `integrated_monomial_coeffs() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrated_monomial_coeffs>`__ returns a dictionary of which the keys are monomials consisting of two variables, and the coefficients of these monomials are numeric integrals.

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 99-100
    :lineno-start: 99
    
Typesetted output:

.. include:: ../sphinx/SLiCAPdata/table-coeffsNoise.rst

Display equations on HTML pages and in LaTeX documents
======================================================

The report module `Create reports <reports.html>`_, discusses how HTML snippets and LaTeX snippets can be created for variables, expressions, equations and tables.

As a matter of fact, all equations, tables and figures on this page are created with this module:

.. literalinclude:: ../noise.py
    :linenos:
    :lines: 102-114
    :lineno-start: 102
    
The typesetted tables and equations are shown on this page.

Plot noise spectrum
===================

SLiCAP plot functions are discussed in `Create plots <plots.html>`_.

.. image:: /img/colorCode.svg
