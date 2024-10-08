============================================
Download, install, configure and test SLiCAP
============================================

.. image:: /img/colorCode.svg

Requirements
============

#. You need to have python3 installed
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

For these packages, SLiCAP also has build in netlist generation. SLiCAP uses `Inkscape <https://inkscape.org/>`_ for scaling of KiCAD images from page format to drawing format. For detaied information see `Schematic capture <schematics.html>`_.

SLiCAP also interacts with `NGspice <https://ngspice.sourceforge.io/>`_ for performing more elaborate numeric simulations.
 
Main configuration
==================

On its first import, SLiCAP searches the above packages and creates commands to start them. To this end it creates a SLiCAP.ini file in the **SLiCAP home directory**: ~/SLiCAP/ and stores the information in it. You can edit this file manually and you can delete it. SLiCAP generates an updated version on the next run. The minimum code to generate this file is:

.. code-block:: python

   # Import the SLiCAP modules in a separate namespace (preferred)
   # Create (but don't overwrite) SLiCAP.ini in the ~/SLiCAP/ folder
   import SLiCAP as sl

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
   
Test the installation
=====================

You can test the installation by running the example 'myFirstRCnetwork.py' in the ~/SLiCAP/examples/myFirstRCnetwork/ folder. It generates an HTML report in the ~/SLiCAP/examples/myFirstRCnetwork/html folder.
    
.. image:: /img/colorCode.svg
   
