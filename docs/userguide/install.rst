============================================
Download, install, configure and test SLiCAP
============================================

.. image:: /img/colorCode.svg

Requirements
============

#. You need to have python 3.12+ installed
#. Under MSWindows it is strongly advised to install Python under `Anaconda <https://www.anaconda.com/download>`_

SLiCAP requires the Python3 packages listed in `https://github.com/SLiCAP/SLiCAP_python/requirements.txt <https://github.com/SLiCAP/SLiCAP_python/blob/main/requirements.txt>`_.

Download SLiCAP
===============

- Open a command window or terminal in a folder where you want to store the downloaded files and clone `SLiCAP <https://github.com/SLiCAP/SLiCAP_python <https://github.com/SLiCAP/SLiCAP_python>`_ into that folder:

.. code-block:: bash

   git clone https://github.com/SLiCAP/SLiCAP_python

or 

- Download the zip file from: `SLiCAP <https://github.com/SLiCAP/SLiCAP_python <https://github.com/SLiCAP/SLiCAP_python>`_ and extract it in some folder.

Install SLiCAP
==============

- If you work with Anaconca open the *Anaconda Prompt* 
- If you have Python installed under Windows, open a terminal by running the command *cmd*
- If you have Python installed under Linux or mac Open a *terminal*
- Navigate to the folder with the file *setup.py* (usually: *<where_you_downloaded_or_cloned>/SLiCAP_python-master/)* and enter the command:

  .. code-block:: python

     python -m pip install .

  Dont forget the dot '**.**' at the end!

  This wil install:

  - Required python packages
  - SLiCAP module scripts, documentation and libraries in the active Python environment

Other packages
==============

SLiCAP has symbol libraries for creating circuit diagrams with:

- `KiCAD <https://www.kicad.org/>`_. This is the preferred package fo working with SLiCAP
- `LTspice <https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html>`_
- `gSchem for windows: gEDA-20130122.zip <https://analog-electronics.tudelft.nl/downloads/gEDA-20130122.zip>`_
- `Lepton EDA <https://github.com/lepton-eda/lepton-eda>`_

For these packages, SLiCAP also has build in netlist generation. SLiCAP uses python scripts for scaling of KiCAD images from page format to drawing format. For detaied information see `Schematic capture <schematics.html>`_.

SLiCAP also interacts with `NGspice <https://ngspice.sourceforge.io/>`_ for performing more elaborate numeric simulations.
 
Completing and testing the installation
=======================================

After installing or updating SLiCAP, you can use it as any other Python package. On its first import, however, SLiCAP searches for installed software for schematic capture or SPICE simulation, and stres this information in a SLiCAP.ini file in the **user home directory**: ~/SLiCAP.ini. You can edit this file manually or delete it. SLiCAP generates an updated version on the next run.

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

        Error: cannot convert SVG to PDF using cairosvg. Please convert manually if necessary.

.. admonition:: First import under Linux or MacOS

    .. code-block:: python

        >>> import SLiCAP as sl
        
        Generating main configuration file: ~/SLiCAP/SLiCAP.ini.

        /usr/bin/kicad-cli
        /usr/bin/lepton-cli
        /usr/bin/ngspice
        SLiCAP Version matches with the latest release of SLiCAP on github.
        Generating project configuration file: SLiCAP.ini.

Main configuration
==================

Updating of the main configuration file `~/SLiCAP.ini` is recommended if:

#. One or more apps listed above are installed or removed
#. During installation under MS-Windows, searching to the apps listed above timed out
    
Below an example of the command section for user "USER" under MS-Windows with default installation of all apps (lepton-eda is not available under MS-Windows). The main configuration file is located at: C:\\Users\\USER\\SLiCAP.ini:

.. code-block:: python

    [commands]
    lepton-eda = 
    kicad = C:\Program Files\KiCad\8.0\bin\kicad-cli.exe
    ltspice = C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe
    geda = C:\Program Files (x86)\gEDA\gEDA\bin\gnetlist.exe
    ngspice = C:\Users\USER\ngspice\Spice64\bin\ngspice.exe

Below an example of the command section for user "USER" under **Linux** or **MacOS** with default installation of LTspice under *wine*. The main configuration file is located at: ~/SLiCAP.ini:

.. code-block:: python

    [commands]
    ltspice = /home/USER/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    kicad = kicad-cli
    geda = lepton-netlist
    lepton-eda = lepton-cli
    ngspice = ngspice
    
.. admonition:: Important

    SLiCAP works well without having additional packages installed. The only function that searches for installed apps is `makeCircuit <../reference/SLiCAPshell.html#SLiCAP.SLiCAPshell.makeCircuit>`__. 

Project configuration
=====================

SLiCAP projects should be placed in separate project folders. In this folder you save the Python script(s) or Jupyter Notebook(s) for your project. On the first run of your Python project script:

#. Creates the directory structure in the project folder
#. Copies some library files
#. Creates a project configuration file SLiCAP.ini in the project directory. 

   This configuration file contains default math settings, color settings, etc. You can edit or delete this file. After deletion it will be recreated at the next project run.

The python script below (user=USER, python environment=USER, os=LINUX) generates/updates the configuration files, displays their contents and opens the HTML documentation in the default browser:

.. code-block:: python

    # Import the SLiCAP modules in a separate namespace (preferred)
    # Create (but don't overwrite) SLiCAP.ini in the ~/ folder
    import SLiCAP as sl
    # Create the project folder structure
    # Start an HTML report
    # Compiles the libraries
    # Create but do not overwrite the project configuration file
    sl.initProject('SLiCAP test')
    # Display the configuration settings:
    sl.ini.dump()
    # Open de HTML documentation in the browser:
    sl.Help()

    Generating project configuration file: SLiCAP.ini.

    Compiling library: SLiCAP.lib.
    Compiling library: SLiCAPmodels.lib.
    ini.install_version = 3.2.4
    ini.latest_version  = 3.2.4
    ini.install_path    = /home/USER/USER/lib/python3.12/site-packages/
    ini.home_path       = /home/USER/
    ini.main_lib_path   = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/lib/
    ini.doc_path        = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/docs/html/
    ini.ltspice         = /home/USER/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    ini.gnetlist        = lepton-netlist
    ini.kicad           = kicad-cli
    ini.ngspice         = ngspice
    ini.lepton_eda      = lepton-cli
    ini.ltspice_syms    = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/LTspice/
    ini.gnetlist_syms   = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/gSchem/
    ini.kicad_syms      = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/kicad/SLiCAP.kicad_sym
    ini.lepton_eda_syms = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/lepton-eda/
    ini.latex_files     = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/tex/
    ini.sphinx_files    = /home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/sphinx/
    ini.html_path       = html/
    ini.cir_path        = cir/
    ini.img_path        = img/
    ini.csv_path        = csv/
    ini.txt_path        = txt/
    ini.tex_path        = tex/
    ini.user_lib_path   = lib/
    ini.mathml_path     = mathml/
    ini.sphinx_path     = sphinx/
    ini.html_prefix     = 
    ini.html_index      = index.html
    ini.html_page       = index.html
    ini.html_pages      = ['']
    ini.html_labels     = <Section: labels>
    ini.disp            = 4
    ini.hz              = True
    ini.notebook        = False
    ini.scalefactors    = False
    ini.eng_notation    = True
    ini.last_updated    = 2025-02-27 15:14:01
    ini.project_title   = SLiCAP test
    ini.created         = 2025-02-27 15:14:00
    ini.author          = USER
    ini.laplace         = s
    ini.frequency       = f
    ini.numer           = ME
    ini.denom           = ME
    ini.lambdify        = numpy
    ini.step_function   = True
    ini.factor          = True
    ini.max_rec_subst   = 15
    ini.reduce_matrix   = True
    ini.reduce_circuit  = True
    ini.gain_colors     = {'asymptotic': 'r', 'gain': 'b', 'loopgain': 'k', 'servo': 'm', 'direct': 'g', 'vi': 'c'}
    ini.plot_fontsize   = 12
    ini.axis_height     = 5
    ini.axis_width      = 7
    ini.line_width      = 2
    ini.marker_size     = 7
    ini.line_type       = -
    ini.legend_loc      = best
    ini.default_colors  = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
    ini.default_markers = ['']
    ini.plot_fontsize   = 12
    ini.plot_file_type  = svg
    ini.svg_margin      = 1

Change settings
---------------

It is strongly advised not to change any settings in the project SLiCAP.ini file. The preferred way of changing settings is to do it in the python scripts. Some examples are given below.

.. code-block:: python

   >>> import SLiCAP as sl
   >>> sl.ini.disp            = 3     # set the number of significant digits in reports and listings to 3
   >>> sl.ini.hz              = False # set the default frequency units to *rad/s*
   >>> sl.ini.max_rec_subst   = 20    # set the maximum number of recursive substitutions in expressions to 20
   >>> sl.ini.reduce_circuit  = False # Do NOT eliminate unused independent voltage sources from the circuit
                                      # If True, the size of MNA matrices comprising independent voltage sources will be reduced
                                      # by eliminating these sources if they are not used as signal source or detector.
   >>> sl.ini.reduce_matrix   = False # Do NOT eliminate variables and reduce the matrix size before calculating the determinant
                                      # If True, the size of MNA matrices comprising Laplace expressions will be reduced through
                                      # elimination of variables, until all matrix enties are either zero or Laplace polynomials
                                      # of the first order or higher
   >>> sl.ini.numer           = "BS"  # Use Bareiss division-free determinant calculation method for the numerator
   >>> sl.ini.denom           = "BS"  # Use Bareiss division-free determinant calculation method for the denominator
   
Find SLiCAP schematic symbols libraries
---------------------------------------

Since version 3.3.0 SLiCAP symbol libraries are stored in the package directory.

.. code-block:: python

   >>> import SLiCAP as sl
   >>> sl.ini.kicad_syms
   
   '/home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/kicad/SLiCAP.kicad_sym'
   
   >>> sl.ini.ltspice_syms
   
   '/home/USER/USER/lib/python3.12/site-packages/SLiCAP/files/LTspice/'
   
Jupyter notebooks
=================

Jupyter Notebooks can also run SLiCAP scripts. For proper rendering of all HTML output to your notebook use the keyword argument ``notebook=True`` with initProject(). 

SLiCAP examples
===============

SLiCAP examples can be found on `github <https://github.com/SLiCAP/SLiCAPexamples>`_.
      
.. image:: /img/colorCode.svg
