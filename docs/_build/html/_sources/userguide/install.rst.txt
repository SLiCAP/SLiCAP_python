============================================
Download, install, configure and test SLiCAP
============================================

.. image:: /img/colorCode.svg

Requirements
============

#. You need to have python 3.12+ installed
#. Under MSWindows it is strongly advised to install Python under `Anaconda <https://www.anaconda.com/download>`_

SLiCAP requires the Python3 packages listed in `https://github.com/SLiCAP/SLiCAP_python/requirements.txt <https://github.com/SLiCAP/SLiCAP_python/blob/master/requirements.txt>`_.

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
- If you have python installed under Windows, open a terminal by running the command *cmd*
- If you have python installed under Linux or mac Open a *terminal*
- Navigate to the folder with the file *setup.py* (usually: *<where_you_downloaded_or_cloned>/SLiCAP_python-master/)* and enter the command:

  .. code-block:: python

     python -m pip install .

  Dont forget the dot '**.**' at the end!

  This wil install:

  - SLiCAP documentation and libraries in the **SLiCAP home directory**: ~/SLiCAP/
  - SLiCAP module scripts in the python environment

Other packages
==============

SLiCAP has symbol libraries for creating circuit diagrams with:

- `KiCAD <https://www.kicad.org/>`_. This is the preferred package fo working with SLiCAP
- `LTspice <https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html>`_
- `gSchem for windows: gEDA-20130122.zip <https://analog-electronics.tudelft.nl/downloads/gEDA-20130122.zip>`_
- `Lepton EDA <https://github.com/lepton-eda/lepton-eda>`_

For these packages, SLiCAP also has build in netlist generation. SLiCAP uses python scripts for scaling of KiCAD images from page format to drawing format. For detaied information see `Schematic capture <schematics.html>`_.

SLiCAP also interacts with `NGspice <https://ngspice.sourceforge.io/>`_ for performing more elaborate numeric simulations.
 
Main configuration
==================

On its first import, SLiCAP searches the above packages and creates commands to start them. To this end it creates a SLiCAP.ini file in the **SLiCAP home directory**: ~/SLiCAP/ and stores the information in it. You can edit this file manually and you can delete it. SLiCAP generates an updated version on the next run. The minimum code to generate this file is:

.. code-block:: python

   # Import the SLiCAP modules in a separate namespace (preferred)
   # Create (but don't overwrite) SLiCAP.ini in the ~/SLiCAP/ folder
   import SLiCAP as sl

Updating of the main configuration file is recommended if:

#. One or more apps listed above are installed or removed
#. During installation under MS-Windows, searching to the apps listed above timed out

In these cases the commands (under MS-Windows the locatation of the executables) need to be set in the *command* section.
    
Below an example of the command section for user "USER" under MS-Windows with default installation of all apps (lepton-eda is not available under MS-Windows). The main configuration file is located at: C:\\Users\\USER\\SLiCAP\\SLiCAP.ini:

.. code-block:: python

    [commands]
    lepton-eda = 
    kicad = C:\Program Files\KiCad\8.0\bin\kicad-cli.exe
    ltspice = C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe
    geda = C:\Program Files (x86)\gEDA\gEDA\bin\gnetlist.exe
    ngspice = C:\Users\anton\ngspice\Spice64\bin\ngspice.exe

Below an example of the command section for user "USER" under Linux with default installation of LTspice under *wine*. The main configuration file is located at: /home/USER/SLiCAP/SLiCAP.ini:

.. code-block:: python

    [commands]
    ltspice = /home/USER/.wine/drive_c/Program Files/ADI/LTspice/LTspice.exe
    kicad = kicad-cli
    geda = lepton-netlist
    lepton-eda = lepton-cli
    ngspice = ngspice

Project configuration
=====================

SLiCAP projects should be placed in separate folders. Don't place them in the **SLiCAP home directory**. This folder will be recreated if you update SLiCAP.

On the first project run, SLiCAP creates the directory structure in the project directory, copies some files into it, and creates a project configuration file SLiCAP.ini in the project directory. This configuration file contains default math settings, color settings, etc. You can edit or delete this file. After deletion it will be recreated at the next project run.

The python script below generates both configuration files, displays their contents and opens the HTML documentation in the default browser:

.. code-block:: python

   # Import the SLiCAP modules in a separate namespace (preferred)
   # Create (but don't overwrite) SLiCAP.ini in the ~/SLiCAP/ folder
   import SLiCAP as sl
   # Create the project folder structure
   # Start an HTML report
   # Compiles the libraries
   # Create but do not overwrite the project configuration file
   my_project = sl.initProject('my_firstSLiCAP_project')
   # Display the configuration settings:
   sl.ini.dump()
   # Open de HTML documentation in the browser:
   sl.Help()

The default execution result of the command sl.ini.dump() after initialization of the example project "My First RC Network" for user "USER" under MS-Windows in the Anaconda environment is shown below:

.. code-block:: python

    >>> import SLiCAP as sl
    >>> sl.initProject("My First RC network")
    
    Compiling library: SLiCAP.lib.
    Compiling library: SLiCAPmodels.lib.
    
    >>> sl.dump()
    
    ini.install_version = 3.2.4
    ini.latest_version  = 3.2.4
    ini.install_path    = C:/Users/USER/anaconda3/lib/site-packages/
    ini.home_path       = C:/Users/USER/SLiCAP/
    ini.main_lib_path   = C:/Users/USER/SLiCAP/lib/
    ini.example_path    = C:/Users/USER/SLiCAP/examples/
    ini.doc_path        = C:/Users/USER/SLiCAP/docs/
    ini.ltspice         = C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe
    ini.gnetlist        = C:\Program Files (x86)\gEDA\gEDA\bin\gnetlist.exe
    ini.kicad           = C:\Program Files\KiCad\8.0\bin\kicad-cli.exe
    ini.ngspice         = C:\Users\USER\ngspice\Spice64\bin\ngspice.exe
    ini.lepton_eda      = 
    ini.project_path    = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/
    ini.html_path       = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/html/
    ini.cir_path        = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/cir/
    ini.img_path        = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/img/
    ini.csv_path        = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/csv/
    ini.txt_path        = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/txt/
    ini.tex_path        = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/tex/
    ini.user_lib_path   = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/lib/
    ini.mathml_path     = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/mathml/
    ini.sphinx_path     = C:/Users/USER/SLiCAP/examples/myFirstRCnetwork/sphinx/
    ini.html_prefix     = 
    ini.html_index      = index.html
    ini.html_page       = index.html
    ini.html_pages      = ['']
    ini.html_labels     = <Section: labels>
    ini.disp            = 4
    ini.last_updated    = 2025-02-03 16:15:03
    ini.project_title   = My first RC network
    ini.created         = 2025-01-31 05:01:58
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
    ini.hz              = True
    ini.gain_colors     = {'asymptotic': 'r', 'gain': 'b', 'loopgain': 'k', 'servo': 'm', 'direct': 'g', 'vi': 'c'}
    ini.plot_fontsize   = 10
    ini.axis_height     = 5
    ini.axis_width      = 7
    ini.legend_loc      = best
    ini.default_colors  = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
    ini.default_markers = ['']
    ini.svg_margin      = 1
    ini.plot_fontsize   = 10
    ini.plot_file_type  = svg
    ini.gain_types      = ['gain', 'asymptotic', 'loopgain', 'servo', 'direct', 'vi']
    ini.data_types      = ['dc', 'dcvar', 'dcsolve', 'laplace', 'numer', 'denom', 'solve', 'noise', 'pz', 'poles', 'zeros', 'time', 'impulse', 'step']
    ini.sim_types       = ['symbolic', ' numeric']
    ini.notebook        = False
    
Changing settings
-----------------

It is strongly advised not to change any settings in the project SLiCAP.ini file. The preferred way of changing settings is to do it in the python scripts:

.. code-block:: python

   >>> import SLiCAP as sl
   >>> sl.ini.disp            = 3     # set the number of significant digits in reports and listings to 3
   >>> sl.ini.hz              = False # set the default frequency units to *rad/s*
   >>> sl.ini.max_rec_subst   = 20    # set the maximum number of recursive substitutions in expressions to 20
   >>> sl.ini.reduce_circuit  = False # Do NOT eliminate unused independent voltage sources from the circuit
   >>> sl.ini.reduce_matrix   = False # Do NOT eliminate variables and reduce the matrix size before calculating the determinant
                                      # If True, the size of MNA matrices comprising Laplace expressions will be reduced through
                                      # elimination of variables, until all matrix enties are either zero or Laplace polynomials
                                      # of the first order or higher
Test the installation
=====================

You can test the installation by running the example 'myFirstRCnetwork.py' in the ~/SLiCAP/examples/myFirstRCnetwork/ folder. It generates an HTML report in the ~/SLiCAP/examples/myFirstRCnetwork/html folder.
    
.. image:: /img/colorCode.svg
   
