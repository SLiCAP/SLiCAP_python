======================================
Download, install and configure SLiCAP
======================================

---------------------------
Download and Install SLiCAP
---------------------------

SLiCAP is available under the following license:

.. image:: https://i.creativecommons.org/l/by-nc-nd/4.0/88x31.png
    :target: http://creativecommons.org/licenses/by-nc-nd/4.0/
    :width: 88
    :alt: Creative Commons License

SLiCAP is licensed under a `Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License <http://creativecommons.org/licenses/by-nc-nd/4.0/>`_. Based on a work at: `http://www.analog-electronics.eu/slicap/slicap.html <http://www.analog-electronics.eu/slicap/slicap.html>`_

Requirements
------------

Before installing SLiCAP you need to install `maxima CAS <http://maxima.sourceforge.net/download.html>`_ and Python 3 packages listed in `https://github.com/Lenty/SLiCAP_python/requirements.txt <https://github.com/Lenty/SLiCAP_python/blob/master/requirements.txt>`_.

MSWindows installation of maxima
````````````````````````````````
The preferred install path for maxima under MSWindows is on the system drive. If the program is installed on another drive, SLiCAP will only work after the *MAXIMA* command in the *SLiCAPsettings.py* has been set to the correct value. The file *SLiCAPsettings.py* is located in the SLiCAP installation directory (use file search).

MSWindows installation of LTspice
`````````````````````````````````
The preferred install path for LTspice under MSWindows is on the system drive. If the program is installed on another drive, *makeNetlist(<netlistFile>.asc)* will only work after the *LTspice* command in the *SLiCAPsettings.py* has been set to the correct value. The file *SLiCAPsettings.py* is located in the SLiCAP installation directory (use file search).

MacOS installation of maxima
````````````````````````````
#. Install maxima on macOs using the *homebrew* package manager (see `brew.sh <https://brew.sh/>`_ for installation instructions)
#. Install maxima with homebrew: open a terminal and enter: *brew install maxima*. 

Download SLiCAP
---------------

- Open a command window or terminal in a folder where you want to store the downloaded files and clone `https://github.com/Lenty/SLiCAP_python <https://github.com/Lenty/SLiCAP_python>`_ into that folder:

.. code-block:: bash

   git clone https://github.com/Lenty/SLiCAP_python

or 

- Download the zip file from: `https://github.com/Lenty/SLiCAP_python <https://github.com/Lenty/SLiCAP_python>`_ and extract it in some folder.

Install SLiCAP
--------------

- If you work with Anaconca open the *Anaconda Prompt* 
- If you have python installed under Windows, open a terminal by running the command *cmd*
- If you have python installed under Linux or mac Open a *terminal*

Go to the folder with the file *setup.py* (usually: *<where_you_downloaded_or_cloned>/SLiCAP_python-master/)* and enter the command:

.. code-block:: python

   python setup.py install --user

- If you install SLiCAP under MSWindows (Anaconda), the installation searches for the maxima command and the LTspice command.

- In cases in which maxima cannot be found, SLiCAP will only work after maxima has been installed and the *MAXIMA* command in the *SLiCAPsettings.py* has been set to the correct value. The file *SLiCAPsettings.py* is located in the SLiCAP installation directory (use file search).

- In cases in which the LTspice command is not found, the instruction *makeNetlist(<cirFileName>.asc)* will only run after LTspice has been installed and the *LTSPICE* command in the *SLiCAPsettings.py* has been set to the correct value. The file *SLiCAPsettings.py* is located in the SLiCAP installation directory (use file search).

------------------------
Configure SLiCAP options
------------------------

You can configure SLiCAP options after you have created a project. To this end you create a python file 
in some project directory. The minimum content of this (python) file is:

.. code-block:: python

   # import the SLiCAP modules
   from SLiCAP import *
   # Create a SLiCAP project, this creates the folder structure
   # and compiles the libraries.
   my_project = initProject('my_firstSLiCAP_project')

You can modify the directory structure and update the paths for circuit files, library files, etc in the
``SLiCAPconfig.py`` file, which is created in the project directory.

MathJax
-------

SLiCAP uses MathJax to render LaTeX embedded in html. LaTeX is used for expressions. MathJax rendering of equations requires an Internet connection. The scripts of the `MathJax CDN`_ will then be used for this purpose. For proper rendering of equations you need to be connected to the Internet and have JavaScript enabled in your browser.

.. _MathJax CDN: https://www.mathjax.org/

Global parameters
-----------------

Global parameters are parameters that are defined in a library outside a subcircuit environment. SLiCAP has a number of built-in global parameters. These parameters are defined in the ``SLiCAPmodels.lib`` library file in the ``lib/`` folder
You can define other global parameters by adding SPICE .param declarations in this file.

.. literalinclude:: ../../files/lib/SLiCAPmodels.lib
    :language: text
    :linenos: 
    :lines: 1-56
    :lineno-start: 1

Path settings
-------------

The project path settings are defined in **SLiCAPconflig.py**. This file is created in the project directory the by **initProject()**. Once created, it can be edited to modify the path settings. **initProject()** will not overwrite the existing **SLiCAPconflig.py**. If you want it to be regenerated, simply delete it before running **initProject()**. 

The default values are:

.. literalinclude:: ../../SLiCAP/SLiCAPconfig/SLiCAPconfig.py
    :language: python
    :linenos:
    
SLiCAP configuration parameters
-------------------------------

The configuration parameters for SLiCAP are defined in `SLiCAP.SLiCAPini.py <../reference/SLiCAPini.html#module-SLiCAPini>`_.

To list the values of the SLiCAP configuration parameters enter:

.. code:: python

   >>> ini.dump()

------------
Getting Help
------------

For help open the ``index.html`` in the ``doc/`` folder in the SLiCAP main library path that you have selected during installation. 

If you are working in a python IDE or in a jupyter notebook, use the *Help()* function (with capital **H**).

.. code:: python

   >>> Help() # This will open the HTML documentation in your default web browser.
