=====
Noise
=====

------------
Introduction
------------

SLiCAP can be used to determine:

#. Source-referred and detector-referred noise spectral densities in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`.
#. Individual contributions of noise sources to the source-referred and detector-reffered noise spectra
#. Detector-referred noise spectrum after correlated double sampling
#. Source-referred and detector-referred RMS noise
#. Design limits (show stopper values) for all kinds of noise sources

All of the above can be performed symbolically or numerically.

Noise of resistors is modelled by setting their noise temperature attribute *'noisetemp'* to a nonzero value or expression. Flicker noise in resistors can be modeled by setting both the noise temperature attribute *'noisetemp'*, and the corner frequency of the :math:`\frac{1}{f}` noise *'noiseflow'* to a nonzero value or expression.

Noise spectra are defined in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`, temperature in degrees Kelvin :math:`\left[ K \right]`, and frequency in :math:`\left[ Hz \right]`.

The netlist entry for a noisy resistor R1 connected between nodes N1 and N2, with resistance :math:`R`, and with flicker noise corner frequency :math:`f_{\ell}`, operating at a temperature :math:`T` is:

.. code-block:: text

   R1 N1 N2 R value={R} noisetemp={T} noiseflow={f_ell}

The spectral density :math:`S_vR` in :math:`\left[ \frac{V^2}{Hz}\right]` of the voltage noise of this resistor equals:

.. math::

    S_{vR}=4kTR\left(1+\frac{f_{\ell}}{f}\right)


Alternatively, the spectral density :math:`S_iR` in :math:`\left[ \frac{A^2}{Hz}\right]` of the current noise of this resistor can be written as:

.. math::

    S_{iR}=\frac{4kT}{R}\left(1+\frac{f_{\ell}}{f}\right)



The SLiCAP library has a number of built-in noise models for active devices such as operational amplifiers, MOS transistors, BJTs, and JFETs. 

Other noise sources can be added with independent voltage or current sources, of which the *'noise'* attribute has been set to a nonzero value or expression.

Hence, a noisy resistor can alternatively be modeled as a noise-free resistor in parallel with a noise current source:

.. code-block:: text

    R1 N1 N2 {R}                                   ; Noise-free resistor with resistance
                                                   ; R between nodes N1 and N2
    INR1 N1 N2 value=0 noise={4*k*T*R*(1*f_ell/f)} ; Noise current associated with R1


.. admonition:: Built-in variables
    :class: note

    k = 1.38E-23 J/K and T=300 K are built-in variables
    
    >>> ini.frequency = sp.Symbol('f') # is by default used for the frequency in [Hz].

-----------------------
Define a noise analysis
-----------------------

Noise analysis requires the data type *'noise'* and the gain type *'vi'*.

.. code-block:: python

    >>> i1=instruction()
    >>> i1.setGainType('vi') 
    >>> i1.setDataType('noise') 

----------------------
Noise analysis results
----------------------

Noise analysis provides the following results:

#. Detector-referred noise spectrum (output noise) in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`

#. Contributions of all noise sources to the detector-referred noise spectrum in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`
#. If a source has been defined:

   #. Source-referred noise spectrum in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`
   #. Contributions of all noise sources to the source-referred noise spectrum in :math:`\left[ \frac{V^2}{Hz}\right]` or in :math:`\left[ \frac{A^2}{Hz}\right]`

These results can be displayed on a html page.

.. code-block:: python

    >>> i1=instruction()                           # Define an instruction
    >>> i1.setSimType('symbolic')                  # Set the analysis type to 'symbolic'
    >>> i1.setGainType('vi')                       # Set the gain type to 'vi'
    >>> i1.setDataType('noise')                    # Set the data type to 'noise'
    >>> i1.setDetector('V_out')                    # Noise analysis requires a detector
    >>> noise_result = i1.execute()                # Execute the instruction
    >>> htmlPage("Symbolic noise analysis")        # Create a html page for displaying the results
    >>> noise2html(noise_result, label='symNoise') # Display the noise result on the html page

The result attributes can be used for further analysis:

.. code-block:: python

    >>> onoise_spectrum = noise_result.onoise      # Detector-referred noise spectrum
    >>> onoise_terms    = noise_result.onoiseTerms # Contributions to detector-referred noise
    >>> inoise_spectrum = noise_result.inoise      # Source-referred noise spectrum;
    >>>                                            # requires a source definition
    >>> inoise_terms    = noise_result.inoiseTerms # Contributions to source-referred noise;
    >>>                                            # requires a source definition
    
    >>> # Print the contributions of the noise sources to the detector-referred noise
    >>> for source_name in list(onoise_terms.keys()):
    >>>     print(source_name, onoise_terms[source_name])
    >>> # Print the contributions of the noise sources to the source-referred noise
    >>> for source_name in list(inoise_terms.keys()):
    >>>     print(source_name, inoise_terms[source_name])

---------
RMS noise
---------

SLiCAP has a buil-in function for determination of the RMS noise, for a given noise spectrum and frequency range:

.. code-block:: python

    >>> f_min = sp.Symbol('f_min')
    >>> f_max = sp.Symbol('f_max')

    >>> RMS_detector_noise = rmsNoise(onoise_spectrum, f_min, f_max)


.. admonition:: Warning
    :class: warning

    Symbolic integration may fail if the frequency dependency of the spectra becomes too complex.

---------------
Noise tutorials
---------------

See: `Tutorials section <../tutorials/SLiCAPtutorials.html>`_

