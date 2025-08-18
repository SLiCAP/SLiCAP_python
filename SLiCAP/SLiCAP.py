#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main module for running SLiCAP from a console or from within a Python IDE.

When working with Jupyter notebooks the main imort module is SLiCAPnotebook.py.
It will import SLiCAP.py and some extra modules for displaying LaTeX, SVG and
RST in the Jupyter notebooks.
"""
import os
import webbrowser
import numpy as np
import SLiCAP.SLiCAPconfigure as ini
from datetime import datetime
from shutil import copy2
from SLiCAP.SLiCAPyacc import _initializeParser
from scipy.optimize import newton, fsolve
from scipy.integrate import quad
from SLiCAP.SLiCAPdesignData import *
from SLiCAP.SLiCAPinstruction import instruction
from SLiCAP.SLiCAPmath import *
from SLiCAP.SLiCAPplots import *
from SLiCAP.SLiCAPrst import RSTformatter
from SLiCAP.SLiCAPlatex import LaTeXformatter, sub2rm
from SLiCAP.SLiCAPngspice import MOS, ngspice2traces, selectTraces
from SLiCAP.SLiCAPshell import *
from SLiCAP.SLiCAPhtml import *
from SLiCAP.SLiCAPhtml import _startHTML
from SLiCAP.SLiCAPkicad import backAnnotateSchematic

# Increase width for display of numpy arrays:
np.set_printoptions(edgeitems=30, linewidth=1000,
    formatter=dict(float=lambda x: "%11.4e" % x))

def Help():
    """
    Opens the SLiCAP HTML documentation in the default browser.
    
    :example:
    
    >>> import SLiCAP as sl
    >>> # Display the SLiCAP HTML help in your default browser:
    >>> sl.Help()
    """
    webbrowser.open_new(ini.doc_path + 'index.html')
    return

def _copyNotOverwrite(src, dest):
    """
    Copies the file 'src' to 'dest' if the latter one does not exist.

    :param src: Name of the source file.
    :type src: str

    :param dest: Name of the desitination file.
    :type dest: str
    """
    if not os.path.exists(dest):
        copy2(src, dest)
    return

def _makeDir(dirName):
    """
    Creates the directory 'dirName' if it does not yet exist.

    :param dirName: Name of the ditectory.
    :type dirName: str
    """

    if not os.path.exists(dirName):
        os.makedirs(dirName)
    return

def initProject(name, notebook=False):
    """
    Initializes a SLiCAP project.

    - Copies the directory structure from the templates subdirectory to the
      project directory in cases it has not yet been created.
    - Creates index.html in the html directory with the project name in the
      title bar
    - Compiles the system libraries
    - Creates or updates 'SLiCAPconfigure.py' in the project directory

    :param name: Name of the project: appears on the main html index page.
    :type name: str

    :return:     None
    :rtype:      NoneType

    :Example:

    >>> import SLiCAP as sl 
    >>> # At the first run it will create a 'SLiCAP.ini' file in the SLiCAP 
    >>> # home folder:  '~/SLiCAP/'. 
    >>> # To this end it searches for installed applications. 
    >>> # Under MSwindows this may take a while.
    >>> sl.initProject('my first SLiCAP project')
    >>> # At the first run this will create a 'SLiCAP.ini' file in the SLiCAP 
    >>> # project folder:  './'. Once created it will only reset some values.
    >>> # This function also resets the netlist parser and (re)creates the 
    >>> # system library objects.
    >>> sl.ini.dump() 
    >>> # Prints the SLiCAP global settings obtained from both ini files.

    """
    # Read the project data from the project configuration file
    project_config = ini._read_project_config()
    # Adjust image sizes for notebooks (image font size equals notebook font size)
    ini.notebook        = notebook
    if notebook:
        # These values will not be stored
        ini.axis_width    = 4
        ini.axis_height   = 3
        ini.plot_fontsize = 9
        ini.line_width    = 1
    # Define the project title and reset the html pages 
    ini.project_title                         = name
    ini.html_page                             = 'index.html'
    project_config['html']['current_page']    = ini.html_page
    ini.html_index                            = 'index.html'
    project_config['html']['current_index']   = ini.html_index
    ini.html_pages                            = []
    project_config['html']['pages']           = (',').join(ini.html_pages)
    ini.html_labels                           = {}
    project_config['labels']                  = ini.html_labels
    ini.html_prefix                           = ''
    project_config['html']['prefix']          = ini.html_prefix
    ini.project_title                         = name
    project_config['project']['title']        = ini.project_title
    ini.last_updated                          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_config['project']['last_updated'] = ini.last_updated
    
    # Update configuration files
    ini.main_config, ini.project_config = ini._update_ini_files()
    # Create the project directory structure, at the first run of initProject()
    _makeDir(ini.html_path)
    _makeDir(ini.txt_path)
    _makeDir(ini.csv_path)
    _makeDir(ini.img_path)
    _makeDir(ini.sphinx_path)
    _makeDir(ini.cir_path)
    _makeDir(ini.user_lib_path)
    _makeDir(ini.tex_path)
    _makeDir(ini.html_path + 'img/')
    _makeDir(ini.html_path + 'css/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/html/css/slicap.css', ini.html_path + 'css/slicap.css')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/html/img/Grid.png', ini.html_path + 'css/Grid.png')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/make.bat', ini.sphinx_path + 'make.bat')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/Makefile', ini.sphinx_path + 'Makefile')
    _makeDir(ini.sphinx_path + 'SLiCAPdata/')
    _makeDir(ini.sphinx_path + 'source/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/conf.py', ini.sphinx_path + 'source/conf.py')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/index.rst', ini.sphinx_path + 'source/index.rst')
    _makeDir(ini.sphinx_path + 'source/img/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/img' + '/colorCode.svg', ini.sphinx_path + 'source/img/colorCode.svg')
    _makeDir(ini.sphinx_path + 'source/_static/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/_static/html_logo.png', ini.sphinx_path + 'source/_static/html_logo.png')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/_static/custom.css', ini.sphinx_path + 'source/_static/custom.css')
    _makeDir(ini.sphinx_path + 'source/_templates/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/sphinx/_templates/layout.html', ini.sphinx_path + 'source/_templates/layout.html')
    _makeDir(ini.tex_path + 'SLiCAPdata/')
    _copyNotOverwrite(ini.install_path + 'SLiCAP/files/tex/preambuleSLiCAP.tex', ini.tex_path + 'preambuleSLiCAP.tex')
    #
    if not ini.notebook:
        # Create the HTML project index file
        _startHTML(name)
    # Initialize the parser, this will create the libraries and delete all previously defined circuits
    _initializeParser()
