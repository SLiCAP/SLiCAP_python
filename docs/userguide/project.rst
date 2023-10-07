===========================
Initialize a SLiCAP project
===========================

You start SLiCAP by importing of the scripts and initialization of a python project:

.. code-block:: python

    >>> from SLiCAP import * # This imports the SLiCAP scripts
    >>> prj = initProject('My SLiCAP project') # default PORT for socket communication with maxima CAS.

    >>> prj = initProject('My SLiCAP project', port=8099) # project-defined port for socket communication with maxima CAS is set to 8099.

The function `initProlect() <../reference/SLiCAP.html#SLiCAP.SLiCAP.SLiCAPinitProject>` creates / updates the directory structure in the working directory. Directories once created will not be overwritten. 

The settings are stored in ``ini``: a `settings <../reference/SLiCAPini.html#SLiCAP.SLiCAPini.SLiCAPini.settings>`_ object. You can view these settings ny evoking the function ``ini.dump()``:

.. code-block :: python

    >>> ini.dump()

Below the output generated after executing ``myFisrtRCnetwork.py`` in the folder ``~/SLiCAP/examples/myFirstRCnetwork/`` under Linux:

    HOST.............. : 127.0.0.1
    Hz................ : True
    Laplace........... : s
    MaximaMatrixDim... : 25
    MaximaTimeOut..... : 60
    PORT.............. : 53118
    assumePosMaxVars.. : True
    circuitPath....... : ~/SLiCAP/examples/myFirstRCnetwork/cir/
    csvPath........... : ~/SLiCAP/examples/myFirstRCnetwork/csv/
    defaultColors..... : ['r', 'b', 'g', 'c', 'm', 'y', 'k']
    defaultLib........ : ~/SLiCAP/lib
    defaultMarkers.... : ['']
    disp.............. : 4
    docPath........... : ~/SLiCAP/docs
    figureAxisHeight.. : 5
    figureAxisWidth... : 7
    figureFileType.... : svg
    frequency......... : f
    gainColors........ : {'gain': 'b', 'asymptotic': 'r', 'loopgain': 'k', 'direct': 'g', 'servo': 'm', 'vi': 'c'}
    htmlIndex......... : index.html
    htmlLabels.keys(). : ['']
    htmlPage.......... : 
    htmlPages......... : ['index.html']
    htmlPath.......... : ~/SLiCAP/examples/myFirstRCnetwork/html/
    htmlPrefix........ : 
    imgPath........... : ~/SLiCAP/examples/myFirstRCnetwork/img/
    installPath....... : ~/.local/lib/python3.8/site-packages/SLiCAP/
    lambdifyTool...... : numpy
    lastUpdate........ : 2022-06-28 09:17:57.580901
    latexPath......... : ~/SLiCAP/examples/myFirstRCnetwork/tex/
    legendLoc......... : best
    libraryPath....... : ~/SLiCAP/examples/myFirstRCnetwork/lib/
    ltspice........... : ~/.wine/drive_c/Program Files/LTC/LTspiceXVII/XVIIx64.exe
    mathmlPath........ : ~/SLiCAP/examples/myFirstRCnetwork/mathml/
    maxRecSubst....... : 12
    maxima............ : maxima
    maximaHandler..... : <SLiCAP.SLiCAPpythonMaxima.SLiCAPpythonMaxima.maximaHandler object at 0x7ff834057820>
    netlist........... : lepton-netlist -g spice-noqsi
    notebook.......... : True
    plotFontSize...... : 12
    projectPath....... : ~/SLiCAP/examples/myFirstRCnetwork/
    socket............ : True
    sphinxPath........ : ~/SLiCAP/examples/myFirstRCnetwork/sphinx/
    stepFunction...... : True
    tableFileType..... : csv
    txtPath........... : ~/SLiCAP/examples/myFirstRCnetwork/txt/
    userPath.......... : ~/SLiCAP

Below the meaning of the variables.

HOST
----

Loop back IP address for socket operation of Maxima CAS.

**Default value** is '127.0.0.1'

Hz
--

#. True:

   - The functions: findServoBandwidth(), listPZ and pz2html will return/display poles and zeros in [Hz]. 
   - Frequency domain plots will have the frequency scale in [Hz].
   - Pole-zero plots will have the frequency scale in [Hz].

#. False: the functions: findServoBandwidth(), listPZ and pz2html will return/display poles and zeros in [rad/s]. 

**Default value** is *True*

Execution results of poles and zeros analysis are always in [rad/s].

Noise spectra always have the frequency scale in [Hz].


Laplace
-------

Sympy symbol that will be used as Laplace variable.

**Default value** is *sympy.Symbol('s')*

MaximaMatrixDim
---------------

Maximum number of rows or columns of the MNA matrix for which *maxima CAS* will use the *Gentleman-Johnson* method for determination of the determinant. Above this number *maxima CAS* is forced to use *recursive expansion of minors*.

**Default value** is 25

MaximaTimeOut
-------------

Many symbolic and numeric math functions are performed by *maxima CAS*. Currently the python subprocess module is used for this purpose. If for some reason *maxima CAS* required input that cannot be passed to this subprocess, the execution of this subprocess is times out after ``MaximaTimeOut`` seconds. 

**Default value** is 5 seconds

PORT
----

Port number for socket communication with maxima. Can be set at the initialization of a project (> 8000).

**Default value** is 81153

assumePosMaxVars
----------------

If true, symbols (except the Laplace variable) passed to maxima are assumed to be positive real numbers. If false, maxima may return questions during evaluation of integrals, limits and/or powers.

**Default value** is *True*

circuitPath
-----------

Search path for schematic files and netlist files. 

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

It will be used by:

#. SLiCAPinstruction.instruction.checkCircuit(<netlist file name>)
#. SLiCAPinstruction.instruction.setCircuit(<netlist file name>)
#. SLiCAPprotos.circuit.checkCircuit(<netlist file name>)
#. SLiCAP.makeNetlist(<schematics file name>, <circuit title>)
#. SLiCAPhtml.netlist2html(<netlist file name>)

csvPath
-------

Search path for csv files.

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

It will be used by:

#. SLiCAP_html.csv2html(<csv file name>)
#. SLiCAP_plots.csv2traces(<csv file name>)

defaultColors
-------------

List with matplotlib color names that will be used for plotting multiple graphs on one axis.

**Default value** is ['r', 'b', 'g', 'c', 'm', 'y', 'k'].

defaultLib
----------

Search path for system library files with SPICE definitions of sub circuits and models.

**Default value** is determined during installation.

defaultMarkers
--------------

List with matplotlib marker names to be used in plots.

**Default value** is: ['']

disp
----

Number of digits for displaying floats on html pages.

**Default value** is: 4

docPath
-------

Path to the SLiCAP html documentation

**Default value** is determined during installation.

figureAxisHeight
----------------

Height of a figure object (depends on DPI).

**Default value** is 5

figureAxisWidth
---------------

Width of a figure object (depends on DPI).

**Default value** is 7

figureFileType
--------------

File type for saving matplotlib figures (graphs).

**Default value** is *svg* (scalable vector graphics).

frequency
---------

Sympy symbol used for frequency.

**Default value** is *sympy.Symbol('f')*.

gainColors
----------

Dictionary with gain types and associated colors for plotting.

**Default value** is *{'gain': 'b', 'asymptotic': 'r', 'loopgain': 'k', 'direct': 'g', 'servo': 'm', 'vi': 'c'}*.

htmlIndex
---------

Active html index page. Links to new pages created with *htmlPage()* will be placed on this page.

**Default value** directly after initialization of a project is *index.html*.

htmlLabels.keys()
-----------------

Keys of the dictionary with html labels that have been defined in this project.

**Default value** is [].

htmlPage
--------

Active html page to which html output will be written.

**Default value** is ''.

htmlPages
---------

List with html pages created in this project.

**Default value** directly after initialization of a project is ['index.html'].

htmlPath
--------

Path to the html output generated by this project.

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

htmlPrefix
----------

Prefix that will be added to the html page file names. This string consists of the netlist file name + '_'.

**Default value** directly after initialization of a project is ''.

imgPath
-------

Search path for img2html().

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

installPath
-----------

SLiCAP install path.

**Default value** is determined during installation.


lambdifyTool
------------

Tool for conversion of multivariate symbolic expressions to multivariate numeric functions. 

**Default value** "numpy"

lastUpdate
----------

Last date/time of execution of the project.

**Default value** is the date time directly after initialization of the project.

latexPath
---------

Path for exporting LaTeX output (not used in current version).

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

legendLoc
---------

Location of legend on plots.

**Default value** is *best*.


libraryPath
-----------

Path to user libraries with definitions of sub circuits and models.

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

ltspice
-------

Path to LTspice executable (required for makeNetlist().

**Default value** is automatically determined during installation.

mathml
------

Setting for math output in html pages (not yet implemented)

**Default value** is *False*.

mathmlPath
----------

Path for exporting mathml output (not used in current version).

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

maxRecSubst
-----------

Setting for maximum number of recursisve substitutions.

**Default value** is 12.

maxima
------

Command for running maxima CAS.

**Default value** is determined during installation.

netlist
-------

Command for generating a netlist from a *'.sch'* schematic file.

**Default value** is determined during installation.

normalize
---------

Setting for normalization of rational functions. If *True*, the coefficient of the lowest order of the denominator will be normalized to unity.

**Default value** True

notebook
--------

Will be set to *True* if SLiCAP runs from an ipython environment (some additional scripts will be loaded).

**Default value** is *False*.

plotFontSize
------------

Font size used in plots.

**Default value** is 12.

projectPath
-----------

Path to the project files for the current project.

**Default value** is determined during the initialization of a project.

socket
------

True for Maxima CAS socket communication. False for Maxima CAS subprocess communication.

**Default value** is *True*.

stepFunction
------------

Setting for parameter stepping.

#. True

   The determinant of a matrix is calculated using symbolic step variable(s). 

#. False

   Numeric values of step variable(s) are substituted in the matrices before calculation of the determinant. This can be faster if many step variables are used.


**Default value** is *True*.


tableFileType
-------------

File extension for *comma seperated value* table files.

**Default value** is *csv*.

txtPath
-------

Search path for importing text files with *text2html()*.

**Default value** is defined in *SLiCAPconfig.py* in the project directory.

userPath
--------

Install path for libraries and documentation.

**Default value** is *~/SLiCAP*.

