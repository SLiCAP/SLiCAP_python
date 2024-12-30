================================
SLiCAP Version 3.2 release notes
================================

.. image:: /img/colorCode.svg

#. SLiCAP Version 3.2 is compatible with previous versions. The use of the *instruction* object for creating instructions, however, is deprecated and no longer described in this documentation.

#. The function *ENG(<number>, scaleFactors=False)* has been added to write numbers in enginering notation. It is used in the following functions:

   - elementData2html
   - params2html
   - expr2html
   - eqn2html
   - pz2html
   - specs2html
          
   If *scalefactors = True*, scale factors from :math:`y=10^{-24}\cdots P=10^{15}` are used. If *scalefactors = False* and *eng_notation = True*, engineering notation will be used (powers of 10 are an integer multiple of 3).
    
   Application of this function is defined in the *SLiCAP.ini* file in the project folder. Default setting are:
   
   .. code::
   
       [display]
       scalefactors = False
       eng_notation = True

#. The *SLiCAP.ini* files in the ~/SliCAP/ folder and in the project folder are automatically updated in case in which they are corrupted or incomplete.

