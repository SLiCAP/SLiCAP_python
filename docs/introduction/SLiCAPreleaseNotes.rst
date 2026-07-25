====================
SLiCAP release notes
====================

.. image:: /img/colorCode.svg

.. IMPLEMENTATION CHECKLIST — before publishing these notes, the following
   v6 item still has to be implemented (spec: SLNG.md "Version 6:
   explicit tool configuration"):
   - File → Configure SLiCAP… dialog + removal of the installed-software
     search (+ drop pywin32/windows_tools from pyproject.toml)
   Everything else listed below is implemented and tested.

SLiCAP Version 6.0 release notes
================================

#. **Schematic capture GUI.** SLiCAP now includes its own schematic editor;
   KiCad, LTspice, gSchem, or Lepton-EDA are no longer required for drawing
   circuits (they remain supported). The GUI is started from the command
   line with ``slicap`` (full environment with instruction editing and
   simulation) or ``slicap-schematics`` (schematic editing only), or from
   Python with ``sl.startSchematic()``. It supports two schematic types:

   - **SLiCAP schematics** (``.slicap_sch``): symbolic analysis netlists
   - **NGspice schematics** (``.spice_sch``): numeric simulation netlists

   Features include netlist generation, drawing-size SVG/PDF export with
   LaTeX-rendered labels, hierarchical subcircuits, an instruction editor
   with analysis dialogs, and a log panel. See
   `Schematic capture <../schematics/index.html>`_.

#. **NGspice simulations from the GUI.** Instruction dialogs generate and
   run OP, DC, AC, TRAN, and NOISE analyses, including parameter stepping
   and per-instruction parameter overrides (``params=``).
   All values use SLiCAP notation (case-sensitive scale factors: ``m`` =
   milli, ``M`` = mega); SLiCAP translates automatically wherever values are
   written into NGspice input (``1M`` → ``1Meg`` — NGspice reads suffixes
   case-insensitively). See
   `Value notation <../schematics/component_properties.html#value-notation-scale-factors>`_.

#. **Plot dialog and instruction editing.**
   :menuselection:`Instruction --> Create / edit plot…` (main window)
   composes a plot from the named analysis results in the instruction file —
   NGspice results via trace conversion, SLiCAP results via ``plotSweep`` /
   ``plotPZ`` — with smart defaults per analysis type. Both the plot dialog
   and the analysis dialogs can **edit existing definitions**: pick a name,
   the fields prefill from the instruction file, and the regenerated call is
   appended — the later definition wins when the file runs; removing the
   superseded line is up to you.

#. **Project management in the GUI.** The main window's File menu creates,
   opens, saves, and closes SLiCAP projects:

   - :menuselection:`File --> New project…` asks for a project name,
     directory, and author, generates the project ``main.py``, and runs it
     once to create the project structure and its ``SLiCAP.ini``.
   - :menuselection:`File --> Select project folder…` shows the project's files in a
     **Project panel** on the left; double-clicking a schematic opens it in
     the editor, any other file opens with its default application. A
     directory without a ``SLiCAP.ini`` offers to create a project there.
   - :menuselection:`File --> Save project` saves every open panel with
     unsaved content; :menuselection:`File --> Close project` returns to the
     welcome screen. One project is open at a time; switching projects
     prompts for unsaved work first.

#. **Explicit configuration of external programs.** SLiCAP no longer
   searches the disk for installed programs (KiCad, LTspice, gEDA/Lepton-EDA,
   NGspice); on MS-Windows this search could take up to two minutes and
   broke whenever a program changed its installation layout. Instead:

   - The GUI menu :menuselection:`File --> Configure SLiCAP…` lets you
     enter, auto-detect, and test the program paths; they are stored in the
     ``[commands]`` section of ``~/SLiCAP.ini``.
   - The same section can be edited manually (script-only use); see
     `Installation <../userguide/install.html>`_.
   - Automatic detection still covers programs on the search PATH and the
     default MS-Windows install locations (e.g. ``C:\Spice64\bin`` for
     NGspice) — it just no longer walks the disk.
   - An unconfigured program now produces a clear message pointing to the
     configuration dialog instead of a failed netlist run.
   - The ``pywin32`` and ``windows_tools`` dependencies have been dropped.

#. **Faster startup.**

   - ``import SLiCAP`` no longer contacts the internet. The check for new
     releases moved to the GUI menu :menuselection:`Help --> Check for
     updates…` (also available as ``sl.ini.check_for_updates()``).
   - The built-in libraries are compiled once and cached
     (``~/SLiCAP_libcache.pkl``); repeated ``initProject()`` calls are
     nearly instant. The cache refreshes automatically when SLiCAP, sympy,
     or a library file changes.

#. `initProject() <../reference/SLiCAP.html#SLiCAP.SLiCAP.initProject>`__
   accepts an optional ``author`` argument that is stored in the project
   configuration file, e.g. ``sl.initProject("My project", author="Me")``.

#. **GUI refinements.**

   - Schematics open as tabs; each keeps the full canvas width.
   - Closing the last schematic returns to the welcome screen;
     :menuselection:`File --> Exit` (:kbd:`Ctrl+Q`) quits the application.
   - The main window and the schematic panel now have separate File menus:
     the main window creates/opens schematics, the schematic panel acts on
     its own schematic only (*Save schematic*, *Schematic properties…*,
     *Export netlist…*, *Print schematic…*, *Schematic drawing
     preferences…*).

#. **Packaging.** Dependencies are declared in ``pyproject.toml`` only;
   ``requirements.txt`` has been removed. Install from source with
   ``python -m pip install .``.

SLiCAP Version 4.0 release notes
================================

#. RMS noise calculations have been improved:

   - Integration methods can be selected
   - Noise weighting (filter) functions can be added
   
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
       ini.install_version        = 4.0.11
       ini.latest_version         = 4.0.11
    
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
#. The function ``_reduce_circuit`` and its associated ini setting ``ini.reduce_circuit`` have been removed. The improved matrix reduction algorithm made it obsolete. 
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
