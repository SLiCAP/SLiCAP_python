================================
SLiCAP Version 3.5 release notes
================================

.. image:: /img/colorCode.svg

#. SLiCAP version 3.5.1 has an improved interface to LaTeX and Sphinx:

   - SLiCAPformatter.py is a multi-format formatter that generates snippets in various formats:
   
     Current support is limited to *ReStucturedText* (Sphinx basic format) and *LaTeX*. Future support wil be extended to *HTML*, *myST*, and *markdown*. See: `formatter <../reference/SLiCAPformatter.html#SLiCAP.SLiCAPformatter.formatter>`__.

SLiCAP Version 3.4 release notes
================================

#. SLiCAP 3.4 is compatible with KiCad 9

SLiCAP Version 3.3 release notes
================================

#. SLiCAP Version 3.3 is prepared for PyPi pip install:

   - Examples are no longer part of the package, they can be puleed of downloaded from `github <https://github.com/SLiCAP/SLiCAPexamples>`_.
   - Libraries are no longer placed in the ~/SLiCAP/ folder. Library locations are found in ~/SLiCAP.ini under the section `[installpaths]`. Settings for symbol library locations in schematic editors (KiCAD, LTspice, etc.) need to be adjusted accordingly.

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
          
      in the **[math]** section of the SLiCAP.ini* file in the project directory
      
   #. Reduction of the size of the MNA matrix before calculation of the determinant, for matrices comprising Laplace expressions.
   
      This matrix reduction can be switched off by setting 
      
      .. code::
      
          reduce_matrix = False
          
      in the **[math]** section of the SLiCAP.ini* file in the project directory

#. KiCAD is the preferred schematic capture program for SLiCAP version 3.2. From version 3.2.3 Inkscape is no longer needed for creating image-size svg and pdf files of KiCAD schematics. SLiCAP uses dedicated Python scrips for this purpose.

#. The function *ENG(<number>, scaleFactors=False)* has been added to write numbers in enginering notation. It is used in the following functions:

   - elementData2html
   - params2html
   - expr2html
   - eqn2html
   - pz2html
   - specs2html
          
   If *scalefactors = True*, scale factors from :math:`y=10^{-24}\cdots P=10^{15}` are used. If *scalefactors = False* and *eng_notation = True*, engineering notation will be used (powers of 10 are an integer multiple of 3).
    
   Application of this function is defined in the **[display]** section of the *SLiCAP.ini* file in the project folder. Default setting are:
   
   .. code::
 
       scalefactors = False
       eng_notation = True

#. The *SLiCAP.ini* files in the ~/SliCAP/ folder and in the project folder are automatically updated in case in which they are corrupted or incomplete.

