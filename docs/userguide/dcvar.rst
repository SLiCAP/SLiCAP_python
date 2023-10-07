===========
DC variance
===========

------------
Introduction
------------

SLiCAP can be used to determine:

#. Source-referred and detector-referred variance in :math:`\left[ V^2 \right]` or in :math:`\left[ A^2 \right]`.
#. Individual contributions of DC error sources to the source-referred and detector-reffered variance
#. Design limits (show stopper values) for all kinds of DC error sources

All of the above can be performed symbolically or numerically.

Tolerances of resistors and independent DC sources can be defined by setting their DC variance attribute *'dcvar'* to a nonzero value or expression.

These variances must be defined in :math:`\left[ \Omega^2\right]` for resistors, in :math:`\left[ V^2\right]` for independent voltage sources, and in :math:`\left[ A^2\right]` for independent current sources.

.. code-block:: text

    "DCvar demo circuit"
    R1 N1 N2 R value={R} dcvar={(sigma_R*R)^2}
    I1 N1 N2 I value={I_DC} dcvar = {(sigma_I*I_DC)^2}
    V1 N1 N2 0 value={V_DC} dcvar = {(sigma_V*V_DC)^2}
    .param R=1k I_DC=1m V_DC=1 sigma_R=0.01 sigma_I=0.05 sigma_V=0.02

It is not (yet) possible to define the variance of the gain of dependent (controlled) sources.

SLiCAP uses a simplified algorithm for evaluation of the total variance of the detector qantity (voltage or current):

#. Calculate the nominal (no errors) DC solution of a network
#. Add error current sources in parallel with resistors. The variance of a current source is the variance of the resistor multiplied with the nominal DC current through that resistor
#. Calculate the variance of the detector quantity, by adding the contributions of all error sources.

-----------------------
Define a dcvar analysis
-----------------------

DC variance analysis requires the data type *'dcvar'* and the gain type *'vi'*.

.. code-block:: python

    >>> i1=instruction()
    >>> i1.setGainType('vi') 
    >>> i1.setDataType('dcvar') 

DC variance analysis results
----------------------------

DC variance analysis provides the following results:

#. Detector-referred DC variance (output DC variance) in :math:`\left[ V^2\right]` or in :math:`\left[ A^2\right]`
#. Contributions of all DC error sources to the detector-referred variance in :math:`\left[ V^2\right]` or in :math:`\left[ A^2\right]`
#. If a source has been defined:

   #. Source-referred variance in :math:`\left[ V^2\right]` or in :math:`\left[ A^2\right]`
   #. Contributions of all DC error sources to the source-referred variance in ::math:`\left[ V^2\right]` or in :math:`\left[ A^2\right]`

These results can be displayed on a html page.

.. code-block:: python

    >>> i1=instruction()                           # Define an instruction
    >>> i1.setSimType('symbolic')                  # Set the analysis type to 'symbolic'
    >>> i1.setGainType('vi')                       # Set the gain type to 'vi'
    >>> i1.setDataType('dcvar')                    # Set the data type to 'dcvar'
    >>> i1.setDetector('V_out')                    # DC variance analysis requires a detector
    >>> dcvar_result = i1.execute()                # Execute the instruction
    >>> htmlPage("Symbolic DC variance analysis")  # Create a html page for displaying the results
    >>> dcvar2html(dcvar_result, label='symDCvar') # Display the result on the html page

The result attributes can be used for further analysis:

.. code-block:: python

    >>> ovar        = dcvar_result.ovar      # Detector-referred variance
    >>> ovar_terms  = dcvar_result.ovarTerms # Contributions to detector-referred variance
    >>> ivar        = dcvar_result.ivar      # Source-referred variance;
    >>>                                      # requires a source definition
    >>> ivar_terms  = dcvar_result.ivarTerms # Contributions to source-referred variance
    >>>                                      # requires a source definition
    
    >>> # Print the contributions of the DC error sources to the detector-referred variance
    >>> for source_name in list(ovar_terms.keys()):
    >>>     print(source_name, ovar_terms[source_name])
    >>> # Print the contributions of the DC error sources to the source-referred variance
    >>> for source_name in list(ivar_terms.keys()):
    >>>     print(source_name, ivar_terms[source_name])

---------------------
DC variance tutorials
---------------------

See: `Tutorials section <../tutorials/SLiCAPtutorials.html>`_

