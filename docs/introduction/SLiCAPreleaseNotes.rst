====================
SLiCAP release notes
====================

.. image:: /img/colorCode.svg

SLiCAP Version 4.0 release notes
================================

#. The netlist syntax and the matrix stamps of ``F``, ``H``, and ``HZ`` element models has been made SPICE-compatible. All SLiCAP symbol libraries, model libraries, and the netlist parser have been updated accordingly and are NO LONGER compatible with earlier versions.
#. Element branch current names have all been set to ``I_<refdes>``, where ``refdes`` is the reference designator of the element. This is NOT compatible with previous versions.
#. Improved output of noise and dcvar analysis for balanced circuits with ``convtype='dd'`` or ``convtype='cc'``. By default, paired noise or dcvar sources are renamed to common-mode or differential-mode sources.
#. Added `checyshev1Poly() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.chebyshev1Poly>`_ returns a normalized Chebyshev type 1 polynomial.
#. Added `filterFunc() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.filterFunc>`__ for creating unity-gain low-pass, high-pass, band-pass, band-reject, and all-pass transfer functions, based on normalized Butterworth, Bessel, and Chebyshev type-1 (pass-band ripple) polynomials.
#. Added `DIN_A() <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.DIN_A>`__, which returns a DIN_A weighting funcion.
#. The code has strongly been simplified: the ``allResults`` object is replaced with a modified ``instruction`` object.
#. The function ``ini.dump()`` has been modified. It displays settings per section. Settings for a specific section are displayed after giving the section name as argument.

   .. code-block:: python

       >>> import SLiCAP as sl
       >>> sl.ini.dump("version")
       
       VERSION
       -------
       ini.install_version        = 4.0
       ini.latest_version         = 4.0
    
#. The execution of the ``reduce_circuit`` and the ``reduce_matrix`` options have been improved. ``reduce_matrix`` now also works for matrices that do not include Laplace expressions and it only performs multiplication and addition on symbolic expressions.
#. ``listPZ`` displays frequencies in rad/s if ``ini.hz=False``
#. Canceling of poles and zeros in `doPZ() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.doPZ>`__ also works for symbolic pole-zero analysis
#. RST and LaTeX snippets for tables are improved
#. RST snippet for equations now supports multiline expressions
#. The documentation has been updated. It automatically generates ``rst`` and ``LaTeX`` snippets by executing `manual.py <https://github.com/SLiCAP/SLiCAP_python/tree/main/docs/manual.py>`_ when running ``make html``.
#. Examples (Python scripts and Jupyter Notebooks) have been added to the `SLiCAP Examples reporitory <https://github.com/SLiCAP/SLiCAPexamples>`_
#. SLiCAP 4.0 has an improved interface with NGspice:

   #. Added a KiCAD SPICE symbol library with NGspice symbols for all standard NGspice devices (no Xspice devices yet)
   #. A simple python instruction for the following analysis types including (non-nested) parameter stepping:
   
      #. .OP
      #. .DC
      #. .AC
      #. .NOISE
      #. .TRAN
      
      These NGspice analyses return a dictionary with traces that can be plotted with the SLiCAP `plot() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.plot>`__ function, or added to an existing plot using `addTraces() <../reference/SLiCAPplots.html#SLiCAP.SLiCAPplots.addTraces>`__.
      
      The results of an operating point information (without parameter stepping) can be displayed on the KiCAD schematic and its ``svg`` and ``pdf`` image files.

#. Library files have been updated; some names of subcircuits modeling the noise behavior of CMOS devices have been modified. See     `Subcircuits with noise <../userguide/noise.html#subcircuits-with-noise>`__.  
#. Clean-up code and minor bug fixes.
      
SLiCAP Version 3.5 release notes
================================

#. SLiCAP version 3.5 has an improved interface to LaTeX and Sphinx:

   - The `LaTeXformatter <../reference/SLiCAPlatex.html#SLiCAP.SLiCAPlatex.LaTeXformatter>`__ creates LaTeX snippets to be imported in `LaTeX <https://www.latex-project.org/>`_ documents.
   - The `RSTformatter <../reference/SLiCAPrst.html#SLiCAP.SLiCAPrst.RSTformatter>`__ creates ReStructuredText snippets to be imported in `Sphinx <https://www.sphinx-doc.org/en/master/>`_ generated websites.

SLiCAP Version 3.4 release notes
================================

#. SLiCAP 3.4 is compatible with KiCad 9

SLiCAP Version 3.3 release notes
================================

#. SLiCAP Version 3.3 is prepared for PyPi pip install:

   - Examples are no longer part of the package, they can be pulled of downloaded from `github <https://github.com/SLiCAP/SLiCAPexamples>`_.
   - Libraries are no longer placed in the ``~/SLiCAP/`` folder. Library locations are found in ``~/SLiCAP.ini`` under the section **[installpaths]**. Settings for symbol library locations in schematic editors (KiCAD, LTspice, etc.) need to be adjusted accordingly.

SLiCAP Version 3.2 release notes
================================

#. SLiCAP Version 3.2 is compatible with previous versions. The use of the *instruction* object for creating instructions, however, is deprecated and no longer described in this documentation.

#. Version 3.2.4 has a KiCAD library symbol, SLiCAP CMOS18 sub circuits, and extra math functions for the design of a feedback amplifiers' MOS input stage based on its noise performance.

   - KiCAD symbol: *XM_noisyNullor*
   - Use with SLiCAP library sub circuits: *MN18_noisyNullor* and *MP18_noisyNullor* for PMOS and NMOS, respectively
   - SLiCAP functions:

     - 'integrate_monomial_coeffs() see `integrate_monomial_coeffs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrate_monomial_coeffs>`__.
     - 'integrated_monomial_coeffs() see `integrated_monomial_coeffs <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.integrated_monomial_coeffs>`__.
     - 'monomial_coeffs2html() see `monomial_coeffs2html <../reference/SLiCAPhtml.html#SLiCAP.SLiCAPhtml.monomial_coeffs2html>`__.

#. From version 3.2.3 the analysis time for large circuits has been considerably reduced. By default, two methods will be applied:

   #. Reduction of the circuit through elimination of all independent voltage sources that are not used as signal source or current detector.
   
      This circuit reduction can be switched off by setting 
      
      .. code::
      
          reduce_circuit = False
          
      in the **[math]** section of the ``SLiCAP.ini`` file in the project directory
      
   #. Reduction of the size of the MNA matrix before calculation of the determinant, for matrices with Laplace expressions.
   
      This matrix reduction can be switched off by setting 
      
      .. code::
      
          reduce_matrix = False
          
      in the **[math]** section of the ``SLiCAP.ini`` file in the project directory

#. KiCAD is the preferred schematic capture program for SLiCAP version 3.2. From version 3.2.3 Inkscape is no longer needed for creating image-size svg and pdf files of KiCAD schematics. SLiCAP uses dedicated Python scrips for this purpose.

#. The function *ENG(<number>, scaleFactors=False)* has been added to write numbers in enginering notation. It is used in the following functions:

   - elementData2html
   - params2html
   - expr2html
   - eqn2html
   - pz2html
   - specs2html
          
   If ``ini.scalefactors=True``, scale factors from :math:`y=10^{-24}\cdots P=10^{15}` are used. If ``ini.scalefactors=False`` and ``ini.eng_notation=True``, engineering notation will be used (powers of 10 are an integer multiple of 3).
    
   Application of this function is defined in the **[display]** section of the ``SLiCAP.ini`` file in the project folder. Default setting are:
   
   .. code::
 
       scalefactors = False
       eng_notation = True

#. The ``SLiCAP.ini`` files in the ``~/SliCAP/`` folder and in the project folder are automatically updated in case in which they are corrupted or incomplete.

.. image:: /img/colorCode.svg
