#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main module for running SLiCAP from a console or from within a Python IDE.

When working with Jupyter notebooks the main imort module is SLiCAPnotebook.py.
It will import SLiCAP.py and some extra modules for displaying LaTeX, SVG and
RST in the Jupyter notebooks.
"""
from datetime import datetime
import getpass
import platform
import os
import subprocess
from shutil import copy2
from SLiCAP.SLiCAPyacc import makeLibraries, CIRCUITNAMES, CIRCUITS, DEVICES, DEVICETYPES, SLiCAPLIBS, SLiCAPMODELS, SLiCAPPARAMS, SLiCAPCIRCUITS, USERLIBS, USERMODELS, USERCIRCUITS, USERPARAMS
from time import time
import sympy as sp
import numpy as np
from scipy.optimize import newton, fsolve
from scipy.integrate import quad
from SLiCAP.SLiCAPini import ini, Help
from SLiCAP.SLiCAPdesignData import specItem, specs2csv, specs2circuit, csv2specs, specs2html
from SLiCAP.SLiCAPinstruction import instruction, listPZ
from SLiCAP.SLiCAPmath import coeffsTransfer, normalizeRational, findServoBandwidth, fullSubs, assumeRealParams, assumePosParams, clearAssumptions, phaseMargin, doCDS, doCDSint, routh, equateCoeffs, step2PeriodicPulse, butterworthPoly, besselPoly, rmsNoise, PdBm2V, float2rational, rational2float, roundN, nonPolyCoeffs, ilt
from SLiCAP.SLiCAPhtml import startHTML, htmlPage, text2html, eqn2html, expr2html, head2html, head3html, netlist2html, lib2html, elementData2html, params2html, img2html, csv2html, matrices2html, pz2html, noise2html, dcVar2html, coeffsTransfer2html, stepArray2html, fig2html, file2html, href, htmlLink, links2html
from SLiCAP.SLiCAPplots import trace, axis, figure, plotSweep, plotPZ, plot, traces2fig, LTspiceData2Traces, LTspiceAC2SLiCAPtraces, csv2traces, Cadence2traces, addTraces
from SLiCAP.SLiCAPlatex import *
from SLiCAP.SLiCAPrst import *
from SLiCAP.SLiCAPfc import computeFC
from SLiCAP.SLiCAPstatespace import getStateSpace
from SLiCAP.SLiCAPngspice import MOS, ngspice2traces
from SLiCAP.SLiCAPkicad import *

try:
    __IPYTHON__
    print("Running from an Ipython environment, importing SLiCAPnotebook.")
    from SLiCAP.SLiCAPnotebook import *
    ini.notebook = True
except NameError:
    ini.notebook = False

class SLiCAPproject(object):
    """
    Prototype of a SLiCAPproject.
    """
    def __init__(self, name):

        self.name = name
        """
        SLiCAPproject.name (str) is the name of the project. It will appear
        on the main html index page
        """

        self.lastUpdate = datetime.now()
        """
        SLiCAPproject.lastUpdate (datetime.datetime) will be updated by
        running: SLiCAPproject.initProject(<name>)
        """

        self.author = getpass.getuser()
        """
        SLiCAPproject.author (str) Will be updated by running:
        SLiCAPproject.initProject(<name>)
        """

def copyNotOverwrite(src, dest):
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

def makeDir(dirName):
    """
    Creates the directory 'dirName' if it does not yet exist.

    :param dirName: Name of the ditectory.
    :type dirName: str
    """

    if not os.path.exists(dirName):
        os.makedirs(dirName)
    return

def initProject(name, port=""):
    """
    Initializes a SLiCAP project.

    - Copies the directory structure from the templates subdirectory to the
      project directory in the case it has not yet been created.
    - Creates index.html in the html directory with the project name in the
      title bar
    - Compiles the system libraries
    - Creates or updates 'SLiCAPconfig.py' in the project directory
    - Creates instance of SLiCAPproject object

    :param name: Name of the project will be passed to an instance of the
                 SLiCAPproject object.
    :type name: str

    :param port: Port number for communication with maxima CAS (> 8000).
    :type port: int

    :return:     SLiCAPproject
    :rtype:      SLiCAP.SLiCAPproject


    :Example:

    >>> prj = initProject('my first SLiCAP project')
    >>> print prj.author
    anton

    """
    prj = SLiCAPproject(name)
    ini.lastUpdate = prj.lastUpdate
    ini.projectPath = os.path.abspath('.') + '/'
    if not os.path.exists(ini.projectPath + 'SLiCAPconfig.py'):
        lines = ['#!/usr/bin/env python3\n',
                 '# -*- coding: utf-8 -*-\n',
                 '"""\n',
                 'SLiCAP module with user-defined path settings.\n',
                 'Default values:\n',
                 '>>> # PATHS: relative to the project path\n',
                 '>>> HTMLPATH    = "html/"   # path for html output\n',
                 '>>> CIRCUITPATH = "cir/"    # path for .asc, .net, .cir, .sch files\n',
                 '>>> LIBRARYPATH = "lib/"    # path for include and library files\n',
                 '>>> TXTPATH     = "txt/"    # path for text files\n',
                 '>>> CSVPATH     = "csv/"    # path for CSV files\n',
                 '>>> LATEXPATH   = "tex/"    # path for LaTeX output\n',
                 '>>> MATHMLPATH  = "mathml/" # path for mathML output\n',
                 '>>> IMGPATH     = "img/"    # path for image files\n',
                 '>>> SPHINXPATH  = "sphinx/" # path for Sphinx output\n',
                 '"""\n',
                 '# PATHS: relative to the project path\n',
                 'HTMLPATH    = "html/"   # path for html output\n',
                 'CIRCUITPATH = "cir/"    # path for .asc, .net, .cir, .sch files\n',
                 'LIBRARYPATH = "lib/"    # path for include and library files\n',
                 'TXTPATH     = "txt/"    # path for text files\n',
                 'CSVPATH     = "csv/"    # path for CSV files\n',
                 'LATEXPATH   = "tex/"    # path for LaTeX output\n',
                 'MATHMLPATH  = "mathml/" # path for mathML output\n',
                 'IMGPATH     = "img/"    # path for image files\n',
                 'SPHINXPATH  = "sphinx/" # path for Sphinx output\n',
                 '# Project information\n',
                 'PROJECT    = ' + '\'' + prj.name + '\'\n',
                 'AUTHOR     = ' + '\'' + prj.author + '\'\n',
                 'CREATED    = ' + '\'' + str(prj.lastUpdate) + '\'\n',
                 'LASTUPDATE = ' + '\'' + str(prj.lastUpdate) + '\'\n',
                ]
        f = open(ini.projectPath + 'SLiCAPconfig.py', 'w')
        f.writelines(lines)
        f.close()
    else:
        f = open(ini.projectPath + 'SLiCAPconfig.py', 'r')
        lines = f.readlines()[0:-1]
        f.close()
        lines.append('LASTUPDATE = ' + '\'' + str(prj.lastUpdate) + '\'')
        f = open(ini.projectPath + 'SLiCAPconfig.py', 'w')
        f.writelines(lines)
        f.close()
    # Define the paths:
    from SLiCAPconfig import HTMLPATH, CIRCUITPATH, LIBRARYPATH, TXTPATH, CSVPATH, LATEXPATH, MATHMLPATH, IMGPATH, SPHINXPATH
    ini.htmlPath         = ini.projectPath + HTMLPATH
    ini.mathmlPath       = ini.projectPath + MATHMLPATH
    ini.circuitPath      = ini.projectPath + CIRCUITPATH
    ini.libraryPath      = ini.projectPath + LIBRARYPATH
    ini.txtPath          = ini.projectPath + TXTPATH
    ini.csvPath          = ini.projectPath + CSVPATH
    ini.latexPath        = ini.projectPath + LATEXPATH
    ini.sphinxPath       = ini.projectPath + SPHINXPATH
    ini.imgPath          = ini.projectPath + IMGPATH
    ini.htmlIndex        = ''
    ini.htmlPrefix       = ''
    ini.htmlPage         = ''
    ini.htmlLabels       = {}
    ini.htmlPages        = []
    if platform.system() == 'Windows':
        ini.kicadPath = 'C:\\Program Files\\KiCad\\7.0\\bin\\'
        ini.inkscapePath = 'C:\\Program Files\\Inkscape\\bin\\'
    elif platform.system() == 'Linux':
        ini.kicadPath = ''
        ini.inkscapePath = ''
    else:
        ini.kicadPath = '/Applications/KiCad/KiCad.app/Contents/MacOS/'
        ini.inkscapePath = ''
    makeDir(ini.circuitPath)
    makeDir(ini.imgPath)
    makeDir(ini.libraryPath)
    makeDir(ini.csvPath)
    makeDir(ini.txtPath)
    makeDir(ini.htmlPath)
    makeDir(ini.htmlPath + 'img/')
    makeDir(ini.htmlPath + 'css/')
    copyNotOverwrite(ini.userPath + '/html/css/slicap.css', ini.htmlPath + 'css/slicap.css')
    copyNotOverwrite(ini.userPath + '/html/img/Grid.png', ini.htmlPath + 'css/Grid.png')
    makeDir(ini.sphinxPath)
    copyNotOverwrite(ini.userPath + '/sphinx/make.bat', ini.sphinxPath + 'make.bat')
    copyNotOverwrite(ini.userPath + '/sphinx/Makefile', ini.sphinxPath + 'Makefile')
    makeDir(ini.sphinxPath + 'SLiCAPdata/')
    makeDir(ini.sphinxPath + 'source/')
    copyNotOverwrite(ini.userPath + '/sphinx/source/conf.py', ini.sphinxPath + 'source/conf.py')
    copyNotOverwrite(ini.userPath + '/sphinx/source/index.rst', ini.sphinxPath + 'source/index.rst')
    makeDir(ini.sphinxPath + 'source/img/')
    copyNotOverwrite(ini.userPath + '/sphinx/source/img' + '/colorCode.svg', ini.sphinxPath + 'source/img/colorCode.svg')
    copyNotOverwrite(ini.userPath + '/sphinx/source/img' + '/SLiCAP.svg', ini.sphinxPath + 'source/img/SLiCAP.svg')
    copyNotOverwrite(ini.userPath + '/sphinx/source/img' + '/SLiCAP-h1.svg', ini.sphinxPath + 'source/img/SLiCAP-h1.svg')
    makeDir(ini.sphinxPath + 'source/_static/')
    copyNotOverwrite(ini.userPath + '/sphinx/source/_static/html_logo.png', ini.sphinxPath + 'source/_static/html_logo.png')
    copyNotOverwrite(ini.userPath + '/sphinx/source/_static/custom.css', ini.sphinxPath + 'source/_static/custom.css')
    copyNotOverwrite(ini.userPath + '/sphinx/source/_static/handsontable.full.min.css', ini.sphinxPath + 'source/_static/handsontable.full.min.css')
    copyNotOverwrite(ini.userPath + '/sphinx/source/_static/handsontable.full.min.js', ini.sphinxPath + 'source/_static/handsontable.full.min.js')
    makeDir(ini.sphinxPath + 'source/_templates/')
    copyNotOverwrite(ini.userPath + '/sphinx/source/_templates/layout.html', ini.sphinxPath + 'source/_templates/layout.html')
    makeDir(ini.mathmlPath)
    makeDir(ini.latexPath)
    makeDir(ini.latexPath + 'SLiCAPdata/')
    copyNotOverwrite(ini.userPath + '/tex/preambuleSLiCAP.tex', ini.latexPath + 'preambuleSLiCAP.tex')
    # Create the HTML project index file
    startHTML(name)
    # Initialize the parser
    CIRCUITNAMES    = []
    CIRCUITS        = {}
    DEVICETYPES     = list(DEVICES.keys())
    SLiCAPLIBS      = ['SLiCAP.lib', 'SLiCAPmodels.lib']
    SLiCAPMODELS    = {}
    SLiCAPPARAMS    = {}
    SLiCAPCIRCUITS  = {}
    USERLIBS        = []
    USERMODELS      = {}
    USERCIRCUITS    = {}
    USERPARAMS      = {}
    makeLibraries()
    return prj

def makeNetlist(fileName, cirTitle):
    """
    Creates a netlist from a schematic file generated with LTspice or gschem.

    - LTspice: '.asc' file
    - gschem: '.sch' file

    :param fileName: Name of the file, relative to **ini.circuitPath**
    :type fileName: str

    :param cirTitle: Title of the schematic.
    :type cirTitle: str
    """
    if not os.path.isfile(ini.circuitPath + fileName):
        print("Error: could not open: '%s'."%(ini.circuitPath + fileName))
        return
    else:
        fileNameParts = fileName.split('.')
        fileType = fileNameParts[-1].lower()
        baseFileName = ini.circuitPath + '.'.join(fileNameParts[0:-1])
        if fileType == 'asc':
            file = os.path.abspath(baseFileName + '.asc')
            print(file)
            if platform.system() == 'Windows':
                file = file.replace('\\','\\\\')
                subprocess.run([ini.ltspice, '-netlist', file])
            else:
                subprocess.run(['wine', ini.ltspice, '-wine', '-netlist', file], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            try:
                f = open(baseFileName + '.net', 'r')
                netlistLines = ['"' + cirTitle + '"\n'] + f.readlines()
                f.close()
                f = open(baseFileName + '.cir', 'w')
                f.writelines(netlistLines)
                f.close()
            except:
                print("Error: could not open: '%s'."%(baseFileName + '.net'))
        elif fileType == 'sch':
            outputfile = os.path.abspath(baseFileName + '.net')
            inputfile = os.path.abspath(baseFileName + '.sch')
            print('input: ',inputfile, ' output: ', outputfile)
            if platform.system() != 'Windows':
                try:
                    subprocess.run(['lepton-netlist', '-g', 'spice-noqsi', '-o', outputfile, inputfile])
                except:
                    print("Could not generate netlist using Lepton-eda")
            try:
                if platform.system() == 'Windows':
                    outputfile = outputfile.replace('\\','\\\\')
                    inputfile = inputfile.replace('\\','\\\\')
                subprocess.run(['gnetlist', '-q', '-g', 'spice-noqsi', '-o', outputfile, inputfile])
            except:
                print("Could not generate netlist using gschem")
            try:
                f = open(baseFileName + '.net', 'r')
                netlistLines = ['"' + cirTitle + '"\n'] + f.readlines()[1:] + ['.end\n']
                f.close()
                f = open(baseFileName + '.cir', 'w')
                f.writelines(netlistLines)
                f.close()
            except:
                print("Error: could not open: '{0}'.".format(baseFileName + '.net'))
    return

def runLTspice(fileName):
    """
    Runs LTspice netlist (.cir) file.

    :param fileName: Name of the circuit (.cir) file, relative to the
                     project directory (cir/<myCircuit>.cir)
    :type fileName: str

    :return: None
    :rtype: Nonetype
    """
    if not os.path.isfile(fileName):
        print("Error: could not open: '%s'."%(fileName))
        return
    else:
        fileNameParts = fileName.split('.')
        fileType = fileNameParts[-1].lower()
        if fileType == 'cir':
            if platform.system() == 'Windows':
                fileName = fileName.replace('\\','\\\\')
                subprocess.run([ini.ltspice, '-b', fileName])
            else:
                subprocess.run(['wine', ini.ltspice, '-b', '-wine', fileName], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
