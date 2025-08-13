============================================
Download, install, configure and test SLiCAP
============================================

.. image:: /img/colorCode.svg

Requirements
============

#. You need to have python 3.12+ installed
#. Under MSWindows it is strongly advised to install Python under `Anaconda <https://www.anaconda.com/download>`_

Install SLiCAP
==============

- If you work with Anaconca open the *Anaconda Prompt* 
- If you have Python installed under Windows, open a terminal by running the command *cmd*
- If you have Python installed under Linux or mac Open a *terminal*
- Enter:

  .. code-block:: python

     pip install slicap

Upgrade SLiCAP
==============

If you have SLiCAP installed and you want to upgrade to the latest version:

- If you work with Anaconca open the *Anaconda Prompt* 
- If you have Python installed under Windows, open a terminal by running the command *cmd*
- If you have Python installed under Linux or mac Open a *terminal*
- Enter:

  .. code-block:: python

     pip install slicap --upgrade

Other packages
==============

.. admonition:: Important
    :class: note

    SLiCAP works well without having additional packages installed. Functions that search for installed apps are:
    
    - SLiCAP netlist generation with `makeCircuit() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.makeCircuit>`__
    - All functions from the `NGspice module <../reference/SLiCAPngspice.html>`__
    
#. SLiCAP uses schematic capture programs for creating SLiCAP netlists from schematics:

   - KiCAD
   - LTspice
   - Lepton-EDA
   - gSchem

#. SLiCAP uses NGspice for:

   - obtaining operating-point information and creating model definitions for active devices
   - integrating numeric simulation 
   
#. SLiCAP uses Sphinx for generating html reports (websites)

#. SLiCAP uses LaTeX for generating typesetted pdf documents

Schematic capture programs
--------------------------
    
SLiCAP has symbol libraries for creating circuit diagrams with:

- `KiCAD <https://www.kicad.org/>`_. This is the preferred package for working with SLiCAP
- `LTspice <https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html>`_
- `gSchem for windows: gEDA-20130122.zip <https://analog-electronics.tudelft.nl/downloads/gEDA-20130122.zip>`_
- `Lepton EDA <https://github.com/lepton-eda/lepton-eda>`_

For these packages, SLiCAP also has built-in netlist generation with `makeCircuit() <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.makeCircuit>`__. SLiCAP also has built-in scripts for scaling of KiCAD ``.SVG`` images from page format to drawing format, and for converting them into ``.PDF`` images. For detaited information see `Schematic capture <schematics.html>`_.

Integration with SPICE
----------------------

`NGspice <https://ngspice.sourceforge.io/>`_ is used for numeric SPICE simulations with more elaborate models.

SLiCAP comes with a KiCAD SPICE symbol library for all standard NGspice devices (not XSPICE) and a netlister option to produce NGspice netlists from KiCAD SPICE schematics. A simple SLiCAP command generates the NGspice control section, runs NGspice, and returns the simulation data. See `Interfacing with NGspice <ngspice.html>`_.
 
Completing and testing the installation
=======================================

After installing or updating SLiCAP, you can use it as any other Python package. On its first import, however, SLiCAP searches for installed software for schematic capture and NGspicen. It stores install information information in a SLiCAP.ini file in the **user home directory**: ``~/SLiCAP.ini``. You can edit this file manually or delete it. If deleted or corrupted, SLiCAP generates an **updated version** on the next import.

.. admonition:: First import under MSWindows

    .. code-block:: python

        >>> import SLiCAP as sl
        
        Updating main configuration file; this may take a while.

        Do you have NGspice installed? [y/n] >>> y

        Searching installed software, this will time-out after 120 seconds!

        KiCad command set as: C:\Program Files\KiCad\kicad-cli.exe
        LTSpice command set as: C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe
        gnetlist command set as: C:\Program Files (x86)\gEDA\gnetlist.exe
        NGspice command set as: C:\Users\<USER>\ngspice\Spice64\ngspice.exe
        SLiCAP found all installed apps!
        SLiCAP Version matches with the latest release of SLiCAP on github.
        Generating project configuration file: SLiCAP.ini.

.. admonition:: First import under Linux or MacOS

    .. code-block:: python

        >>> import SLiCAP as sl
        
        Generating main configuration file: ~/SLiCAP.ini.

        /usr/bin/kicad-cli
        /usr/bin/lepton-cli
        /usr/bin/ngspice
        SLiCAP Version matches with the latest release of SLiCAP on github.
        Generating project configuration file: SLiCAP.ini.

Main configuration
==================

Updating of the main configuration file ``~/SLiCAP.ini`` is recommended if:

#. One or more apps listed above are installed or removed
#. During installation under MS-Windows, searching to the apps listed above timed out
    
Below an **example** of the command section for user "USR" under MS-Windows with default installation of all apps (lepton-eda is not available under MS-Windows). The main configuration file is located at: C:\\Users\\USR\\SLiCAP.ini

.. code-block:: python

    [commands]
    lepton-eda = 
    kicad = C:\Program Files\KiCad\9.0\bin\kicad-cli.exe
    ltspice = C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe
    geda = C:\Program Files (x86)\gEDA\gEDA\bin\gnetlist.exe
    ngspice = C:\Users\USR\ngspice\Spice64\bin\ngspice.exe

Below an **example** of the command section for user "USR" under **Linux** or **MacOS** with default installation of LTspice under *wine*. The main configuration file is located at: ~/SLiCAP.ini:

.. code-block:: python

    [commands]
    ltspice = /home/USR/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    kicad = kicad-cli
    geda = lepton-netlist
    lepton-eda = lepton-cli
    ngspice = ngspice
    
Display the main configuration settings
---------------------------------------

The SLiCAP main configuration comprises the following sections:

#. Version: version information
#. Install: install paths of program files, libraries and documentation
#. Commands: commands for starting programs such as KiCAD and NGspice

Below an example of showing some main configuration settings under Linux:

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.ini.dump('version')
    
    VERSION
    -------
    ini.install_version        = 4.0
    ini.latest_version         = 4.0
    
    >>> sl.ini.dump('commands')
    
    COMMANDS
    --------
    ini.kicad                  = kicad-cli
    ini.ltspice                = /home/user/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    ini.gnetlist               = lepton-netlist
    ini.lepton_eda             = lepton-cli
    ini.ngspice                = ngspice

Project configuration
=====================

SLiCAP projects must be placed in separate project folders. In this folder you save your project Python script(s) and/or Jupyter Notebook(s). 

Create a SLiCAP project
-----------------------

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.initProject("my project")

    Generating project configuration file: SLiCAP.ini.

    Compiling library: SLiCAP.lib.
    Compiling library: SLiCAPmodels.lib.

#. ``initProject()`` creates the following directory structure in the project folder: ::

     + project folder          # Project root directory for python scripts and jupyter notebooks
     | - SLiCAP.ini            # SLiCAP settings for the project
     +-- cir                   # Default directory for netlists ('.cir' files)
     +-- lib                   # Default directory for project-specific libraries
     +-- img                   # Default direcory for image files generated by SLiCAP
     +-+ html                  # Default directory of standard SLiCAP html project report
     | | - index.html          # Main html report page
     | +-- css                 # Default directory for standard SLiCAP html report CSS
     | |   - Grid.png          # Background for standard SLiCAP html report
     | |   - SLiCAP.css        # CSS file for standard SLiCAP html report
     | +-- img                 # Default directory for standard SLiCAP html report images
     +-- csv                   # Default directory for csv files generated or imported by SLiCAP
     +-+ sphinx                # Root directory for Sphinx project report
     | | - make.bat            # MSWindows batch file for compiling Sphinx project report
     | | - Makefile            # Linux (MacOS) make file for compiling Sphinx project report
     | +-- SLiCAPdata          # Directory for storing SLiCAP generated rst snippets
     | +-+ source              # Directory for storing rst project report files
     |   | - conf.py           # Sphinx configuration file based on ``Sphinx book style``
     |   | - index.rst         # Root rst project report file
     |   +-- img               # Directory for storing rst project report images
     |   |   - colorCode.svg   # svg image with color-coded resistors
     |   +-- _static           # Sphinx directory for style information
     |   |   - custom.css      # Sphinx custom css files
     |   |   - html_logo.png   # Sphinx report html logo
     |   +-- _templates        # Sphinx user templates
     |       - layout.html     # Example of a user template
     +-- tex                   # Root directory for LaTeX project report
     |   - preambuleSLiCAP.tex # Preambule with default SLiCAP LaTeX formatting dfinitions
     |   +-- SLiCAPdata        # Directory for storing SLiCAP generated LaTeX snippets
     +-- txt                   # Directory for text files to be included in standard html output
        
#. A project configuration file ``SLiCAP.ini`` is created in the project folder. 

   This configuration file contains default math settings, color settings, etc. You can edit or delete this file. After deletion it will be recreated at the next project run.
   
#. An HTML index page is generated in the html folder in the project directory. This is the home page of the SLiCAP project HTML report.

The python script below (user=USR, python environment=ENV, os=LINUX) generates/updates the configuration files and displays their contents.

.. code-block:: python

    import SLiCAP as sl
    >>> # Create (but don't override) the project folder structure 
    >>> # and the projectconfiguration file ``SLiCAP.ini``
    >>> sl.initProject('SLiCAP test')

    Generating project configuration file: SLiCAP.ini.

    Compiling library: SLiCAP.lib.
    Compiling library: SLiCAPmodels.lib.
    
    >>> # Display the configuration settings:
    >>> sl.ini.dump()
    
    VERSION
    -------
    ini.install_version        = 4.0
    ini.latest_version         = 4.0

    INSTALL
    -------
    ini.install_path           = /home/USR/ENV/lib/python3.12/site-packages/
    ini.home_path              = /home/USR/
    ini.main_lib_path          = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/lib/
    ini.doc_path               = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/docs/html/
    ini.kicad_syms             = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/kicad/SLiCAP.kicad_sym
    ini.ngspice_syms           = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/kicad/SPICE.kicad_sym
    ini.ltspice_syms           = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/LTspice/
    ini.gnetlist_syms          = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/gSchem/
    ini.lepton_eda_syms        = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/lepton-eda/
    ini.latex_files            = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/tex/
    ini.sphinx_files           = /home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/sphinx/

    COMMANDS
    --------
    ini.kicad                  = kicad-cli
    ini.ltspice                = /home/USR/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    ini.gnetlist               = lepton-netlist
    ini.lepton_eda             = lepton-cli
    ini.ngspice                = ngspice

    PROJECT
    -------
    ini.project_title          = myProject
    ini.author                 = user
    ini.created                = 2025-06-30 23:10:04
    ini.last_updated           = 2025-06-30 23:10:59

    PATHS
    -----
    ini.project_path           = /home/USR/myProject/
    ini.html_path              = html/
    ini.cir_path               = cir/
    ini.img_path               = img/
    ini.csv_path               = csv/
    ini.txt_path               = txt/
    ini.tex_path               = tex/
    ini.user_lib_path          = lib/
    ini.sphinx_path            = sphinx/
    ini.tex_snippets           = tex/SLiCAPdata/
    ini.html_snippets          = sphinx/SLiCAPdata/
    ini.rst_snippets           = sphinx/SLiCAPdata/
    ini.myst_snippets          = sphinx/SLiCAPdata/
    ini.md_snippets            = sphinx/SLiCAPdata/

    HTML
    ----
    ini.html_prefix            = 
    ini.html_index             = 
    ini.html_page              = 
    ini.html_pages
	     index.html
    ini.html_labels
    
    DISPLAY
    -------
    ini.hz                     = True
    ini.disp                   = 4
    ini.scalefactors           = False
    ini.eng_notation           = True

    MATH
    ----
    ini.laplace                = s
    ini.frequency              = f
    ini.numer                  = ME
    ini.denom                  = ME
    ini.lambdify               = numpy
    ini.step_function          = True
    ini.factor                 = True
    ini.max_rec_subst          = 15
    ini.reduce_matrix          = True
    ini.reduce_circuit         = True

    PLOT
    ----
    ini.gain_colors_gain       = b
    ini.gain_colors_loopgain   = k
    ini.gain_colors_asymptotic = r
    ini.gain_colors_servo      = m
    ini.gain_colors_direct     = g
    ini.gain_colors_vi         = c
    ini.axis_height            = 5
    ini.axis_width             = 7
    ini.line_width             = 2
    ini.line_type              = -
    ini.plot_fontsize          = 12
    ini.marker_size            = 7
    ini.legend_loc             = best
    ini.default_colors         = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
    ini.default_markers        = ['']
    ini.plot_file_type         = svg
    ini.svg_margin             = 1

    BALANCING
    ---------
    ini.pair_ext               = ['P', 'N']
    ini.update_srcnames        = True
    ini.remove_param_pair_ext  = True
    
We will discuss these settings later.

Change configuration settings
-----------------------------

.. admonition:: Important
    :class: warning
    
    It is strongly advised not to change any settings in the project SLiCAP.ini file. 
    
    The preferred way of changing settings is to do it in the Python scripts.

.. code-block::

   import SLiCAP as sl
   sl.ini.disp            = 3     # set the number of significant digits in reports and listings to 3
   sl.ini.hz              = False # set the default frequency units to *rad/s*
   sl.ini.max_rec_subst   = 20    # set the maximum number of recursive substitutions in expressions to 20
   sl.ini.reduce_circuit  = False # Do NOT eliminate unused independent voltage sources from the circuit
                                  # If True, the size of MNA matrices comprising independent voltage sources will be reduced
                                  # by eliminating these sources if they are not used as signal source, 
                                  # detector, or reference for CCCS and CCVS elements
   sl.ini.reduce_matrix   = False # Do NOT eliminate variables and reduce the matrix size before calculating the determinant
                                  # If True, the size of MNA matrices comprising will be reduced through division-free
                                  # elimination of variables, before calculation of the determinant. 
                                  # The elimination method is division-free in the Laplace variable
   sl.ini.numer           = "BS"  # Use Bareiss division-free determinant calculation method for the numerator
                                  # Default is ``ME``: recursive expansion of minors
   sl.ini.denom           = "BS"  # Use Bareiss division-free determinant calculation method for the denominator
                                  # Default is ``ME``: recursive expansion of minors
   
Find SLiCAP schematic symbol libraries
--------------------------------------

From version 3.3.0, SLiCAP symbol libraries are stored in the package directory. You need these locations for configuring your schematic capture program:

.. code-block:: python

   >>> import SLiCAP as sl
   >>> sl.ini.kicad_syms
   '/home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/kicad/SLiCAP.kicad_sym'
   >>> sl.ini.ltspice_syms
   '/home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/LTspice/'
   >>> sl.ini.lepton-eda_syms
   '/home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/lepton-eda/'
   >>> sl.ini.gnetlist_syms
   '/home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/gSchem/'
   >>> sl.ini.ngspice_syms
   '/home/USR/ENV/lib/python3.12/site-packages/SLiCAP/files/kicad/SPICE.kicad_sym'
   
Run SLiCAP from within Jupyter notebooks
----------------------------------------

Jupyter Notebooks can also run SLiCAP scripts. For proper rendering of all HTML output to your notebook set the keyword argument ``notebook=True`` with initProject(). With this setting, no html pages are generated and all html output is rendered in the notebook.

.. code-block:: python

    import SLiCAP as sl
    sl.initProject('SLiCAP test', notebook=True) # renders all html output in the notebook
    
Sympy Computer Algebra System
=============================

SLiCAP uses `Sympy <https://www.sympy.org/en/index.html>`_ as Computer Algebra System (**CAS**). Users are encouraged to study the `sympy documentation <https://docs.sympy.org/latest/>`_ to use SLiCAP to its full extent.

Internal number format
----------------------

SLiCAP uses Rational Numbers as internal number format. SLiCAP calculates with floats only if required by numeric math algorithms (e.g. numeric pole-zero analysis and numeric integration). 

Display of numeric values on HTML pages and in LaTeX reports will be done in integers or floats. The number of significant digits for display only, is set by ``ini.disp``.

.. code-block::

    >>> import SLiCAP as sl
    >>> sl.ini.disp
    4

Reserved variables and functions
--------------------------------

SLiCAP inherits Sympy limitations. Please read: `Reserved (Sympy) symbols and SLiCAP built-in variables <../syntax/netlist.html#reserved-sympy-symbols-and-slicap-built-in-variables>`__.

.. code-block::

    >>> import sympy as sp
    >>> sp.N(sp.sympify("pi*I*1E3")).as_real_imag()

    (0, 3141.59265358979)
    
    >>> sp.N(sp.E)
    ￼￼  
    2.718281828459045
    
Assumptions
-----------

All SLiCAP built-in variables as well as circuit parameters are free of `Assumptions <https://docs.sympy.org/latest/guides/assumptions.html>`_. 

Sometimes calculations are strongly siplified using assumptions. SLiCAP has two functions that assign assumptions to variables and one to clear the assumptions:

- `assumePosParams <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.assumePosParams>`__
- `assumeRealParams <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.assumeRealParams>`__
- `clearAssumptions <../reference/SLiCAPmath.html#SLiCAP.SLiCAPmath.clearAssumptions>`__
    
SLiCAP html documentation
=========================

``Help()`` with capital **"H"** opens this html documentation in your default browser.

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.Help()

.. image:: /img/colorCode.svg
