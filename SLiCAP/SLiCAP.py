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
from SLiCAP.SLiCAPtraces import *
from SLiCAP.SLiCAPplots import *
from SLiCAP.SLiCAPrst import RSTformatter
from SLiCAP.SLiCAPlatex import LaTeXformatter, sub2rm, exprLatex, symbolLatex
from SLiCAP.SLiCAPtxt import TXTformatter
from SLiCAP.SLiCAPngspice import (MOS, ngspice2traces, selectTraces,
                                   make_netlist,
                                   op, ac, dc, tran, noise, ngspice_control,
                                   NGspiceRaw2dict, RawFile, Analysis,
                                   instr2dataset)
from SLiCAP.SLiCAPshell import *
from SLiCAP.SLiCAPhtml import *
from SLiCAP.SLiCAPhtml import _startHTML
from SLiCAP.SLiCAPkicad import backAnnotateSchematic
from SLiCAP.SLiCAPstateSpace import doStateSpace

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

def startSchematic(config=None, file=None):
    """
    Launch the SLiCAP schematic capture GUI as a separate process.

    The GUI runs independently — this call returns immediately and does not
    block the Python session or Jupyter notebook.

    The editor always opens in schematic-only mode (no Instruction/Log
    panels); analysis is driven from the Python session.

    :param config: Capture mode.  Sets the symbol library **and** restricts
        which schematic type may be created or opened:

        - ``None`` *(default)*: both SLiCAP and NGspice schematics allowed;
          the symbol set is chosen per schematic.
        - ``'basic'``: SLiCAP only, basic symbol library (``Symbols.svg``
          only).  Intended for external callers that embed the editor and
          want only the standard set.  "New NGspice Schematic" is disabled.
        - ``'slicap'``: SLiCAP only, full symbol library (all SVG files in
          the system symbols directory).  "New NGspice Schematic" is disabled.
        - ``'ngspice'``: NGspice only, NGspice symbol library.  "New SLiCAP
          Schematic" is disabled.

        In a restricted mode **File → Open** also lists only files of the
        permitted type.

    :type config: str or None

    :param file: Path to a schematic file to open at startup
                 (``.slicap_sch`` for SLiCAP, ``.spice_sch`` for NGspice).
                 The schematic type is inferred automatically from the
                 extension.  **A canvas is shown only when a file is given;**
                 otherwise the editor opens empty and the user creates or
                 opens a schematic from the File menu (in the ``config`` mode).
    :type file: str or None

    :example:

    >>> import SLiCAP as sl
    >>> sl.initProject("My Design")
    >>> sl.startSchematic()                                  # empty; user picks type via File menu
    >>> sl.startSchematic(config='slicap')                   # SLiCAP mode, full library
    >>> sl.startSchematic(config='ngspice')                  # NGspice mode
    >>> sl.startSchematic(config='basic')                    # SLiCAP mode, basic symbols
    >>> sl.startSchematic(file='sch/mydesign.slicap_sch')    # open SLiCAP file
    >>> sl.startSchematic(file='sch/mydesign.spice_sch')     # open NGspice file
    """
    import subprocess, sys
    # startSchematic is the schematic-capture entry point for a Python session
    # (analysis is done in Python, not in the GUI), so it always opens the
    # schematic-only editor — no Instruction/Log panels. The explicit flag is
    # required because '-m SLiCAP.schematic.main' cannot be detected by launcher
    # name the way the 'slicap-schematics' console script is.
    cmd = f'"{sys.executable}" -m SLiCAP.schematic.main --schematic-only'
    if config is not None:
        cmd += f' --config {config}'
    if file is not None:
        cmd += f' "{file}"'
    subprocess.Popen(cmd, shell=True)

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

def loadProject(notebook=False):
    """
    Opens an EXISTING SLiCAP project: reads its configuration, compiles the
    libraries and creates any missing project directories.

    Unlike :func:`initProject` it changes nothing about the project itself -
    not its name, not its author, and not the state of a report that has
    already been built (the page list, the index and the labels are left as
    they are). Use it to work on a project that exists; use
    :func:`initProject` to create one or to start a fresh project run.

    Missing directories ARE created: a project handed over or cloned from a
    repository arrives without its empty ones (``results``, ``sch``), and the
    first write into them would fail.

    :param notebook: True for a Jupyter notebook session, see
                     :func:`initProject`.
    :type notebook: bool

    :return: None
    :rtype: NoneType

    :example:

    >>> import SLiCAP as sl
    >>> sl.loadProject()          # in the project folder
    """
    project_config = ini._read_project_config()
    ini.notebook = notebook
    if notebook:
        ini.axis_width    = 4
        ini.axis_height   = 3
        ini.plot_fontsize = 9
        ini.line_width    = 1
    # The project keeps its own identity; only the timestamp moves.
    ini.project_title = project_config['project']['title']
    ini.author        = project_config['project']['author']
    ini.last_updated  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_config['project']['last_updated'] = ini.last_updated
    # Create the project directories that are missing, change nothing else.
    for path in (ini.cir_path, ini.img_path, ini.txt_path, ini.csv_path,
                 ini.results_path, ini.schematic_path, ini.html_path,
                 ini.sphinx_path, ini.user_lib_path, ini.tex_path):
        _makeDir(path)
    # Compile the libraries and drop any circuits of a previously opened
    # project. Safe here and nowhere else: at project-open nothing has been
    # parsed yet, so no user library can be lost (Anton, 2026-08-16).
    _initializeParser()


def initProject(name, notebook=False, report_dirs=True, author=None):
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

    :param notebook: True if SLiCAP runs from a Jupyter notebook, defaults to False
    :type notebook: Bool

    :param create_dirs: True will create but not overwrite the SLiCAP directory
                        structure. Defaults to True
    :type create_dirs: Bool

    :param author: Project author, written to the 'SLiCAP.ini' [project]
                   section. None (default) keeps the existing value.
    :type author: str, NoneType

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
    # Define the project title
    ini.project_title                         = name
    project_config['project']['title']        = ini.project_title
    # Define the project author; persisted like the title via
    # ini._update_project_config() on the first html/file write.
    if author is not None:
        ini.author                            = author
        project_config['project']['author']   = ini.author
    ini.last_updated                          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_config['project']['last_updated'] = ini.last_updated
    # Create the project directories if they do not yet exist
    _makeDir(ini.cir_path)
    _makeDir(ini.img_path)
    _makeDir(ini.txt_path)
    _makeDir(ini.csv_path)
    _makeDir(ini.results_path)
    _makeDir(ini.schematic_path)
    if report_dirs:
        # Reset the html pages 
        # Update configuration files; this is done on the first import of SLiCAPconfigure.py
        # ini.main_config, ini.project_config = ini._update_ini_files()
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
        # Create the report directories at the first run of initProject()
        _makeDir(ini.html_path)
        _makeDir(ini.sphinx_path)
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
    else: 
        ini.notebook = True
    if not ini.notebook:
        # Create the HTML project index file
        _startHTML(name)
    # Initialize the parser, this will create the libraries and delete all previously defined circuits
    _initializeParser()
