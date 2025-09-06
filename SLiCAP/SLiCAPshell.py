#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module creates a shell around basic SLiCAP instructions.
This yields a strongly simplified and reduced set of SLiCAP user commands.

General instruction format
==========================
    
result = do<Instruction>(cir, transfer=None, source='circuit',
detector='circuit', lgref='circuit', convtype=None, pardefs=None, 
numeric=False, stepdict=None), 

where <Instruction> describes the analysis to be performed. Below an overview 
of instructions that have been implemented in SLiCAP.

#. Network equations:

   - doMatrix()     : matrix equation of the circuit

#. Complex frequency domain (Laplace) analysis:
    
   - doLaplace()    : transfer function (Laplace expression)
   - doNumer()      : numerator of a transfer function
   - doDenom()      : denominator of a transfer function
   - doSolve()      : Laplace Transform of the network solution
   
#. Complex frequency domain analysis: Poles and zeros of transfer functions:

   - doPoles()      : poles of a transfer, including non-controllable and 
     non-observable (complex frequency solutions of Denom)
   - doZeros()      : zeros of a transfer (complex frequency solutions of Numer)
   - doPZ()         : DC value, poles and zeros of a transfer (with pole-zero 
     canceling)
   
#. Noise analysis:

   - doNoise()      : spectral densities of detector and source-referred noise
   
#. Time domain analysis, based on the Inverse Laplace Transform:

   - doTime()       : detector voltage or current
   - doImpulse()    : unit-impulse response of a transfer
   - doStep()       : unit-step response of a transfer
   - doTimeSolve()  : Time-domain solution of a network
   
#. DC (zero-frequency) analysis:

   - doDC()         : Zero-frequency value of a transfer
   - doDCsolve()    : DC network solution
   - doDCvar()      : detector-referred and source-referred DC variance
   
#. Parametric sweep

   - doParams()     : Parametric sweep, used for plots only.

Some analysis types require definitions of a signal source, a signal detector, 
and/or a loop gain reference. Souce, detector and loop gain reference are
specified with the circuit.

- A **detector** specification is **NOT** required for the instructions:
                     
  - doMatrix()
  - doDenom()
  - doPoles()
  - doSolve()
  - doDCsolve()
  - doTimeSolve()
  
  **AND** for transfer types:
      
  - loopgain
  - servo
                   
  In all other cases a definition of a detector is required.

- A **source** specification is required for transfers: 'gain', 'direct', 
  and 'asymptotic'.

  If a source definition is given, instructions 'doNoise()' and 'doDCvar()' 
  also return the source-referred noise and source referred DC variance, 
  respectively.

- A **loop gain reference** specification is required for the transfers: '
  asymptotic', direct', 'loopgain', and 'servo'.

------
                     
:param cir: Circuit object that will be used for the analysis. The signal 
            source, the signal detector, the loop gain reference, and 
            definitions of circuit parameters are attributes the circuit.
                      
:type circuit: SLiCAPprotos.circuit() object

:param source:   - 'circuit': signal source as defined in the netlist
                 - str: name (refDes) of independent source
                 - list: list with two names of independent sources

:param detector: - 'circuit': signal detector as defined in the netlist
                 - str: name a dependent variable
                 - list: list with two names of dependent variables

:param lgref:    - 'circuit': loop gain reference as defined in the netlist
                 - str: name a controlled source
                 - list: list with two names of controlled sources

:param transfer: - None: calculation of detector voltage or current
                 - 'gain': calculation of complex ratio of detector 
                   voltage/current and source voltage/current
                 - 'asymptotic': as gain with loop gain reference replace with 
                   a nullor
                 - 'loopgain': gain enclosed in the loop involving the loop 
                   gain reference
                 - 'servo' :-L/(1-L), where L is the loop gain
                 - 'direct': as gain with the transfer of the loop gain 
                   reference set to zero
    
                 Defaults to 'gain'.
                 
                 In some analysis types the transfer value is ignored and 
                 considered None
                   
:type transfer: - NoneType, str       

:param convType: - None: No matrix conversion takes place
                 - 'all': Dependent variables and independent variables will be 
                   grouped into differential-mode and common-mode variables. 
                   The circuit matrix dimension is not changed. Automatic
                   determination of DM or CM source and detector is not 
                   possible. Only useful for studying the completely converted
                   MNA matrix.
                   
                 - 'dd': After grouping of the vaiables in differential-mode
                   and common-mode variables, only the differential-mode 
                   variables of both dependent and independent variables are 
                   considered. 
                   
                   The matrix equation describes the differential-
                   mode behavior of the circuit.
                   
                   Source, detector and loop gain reference will be converted
                   automatically.
                   
                 - 'cc': After grouping of the vaiables in differential-mode
                   and common-mode variables, only the common-mode variables of 
                   both dependent and independent variables are considered. 
                   
                   The matrix equation describes the common-mode behavior of 
                   the circuit.
                   
                   Source, detector and loop gain reference will be converted
                   automatically.
                   
                 - 'dc': After grouping of the vaiables in differential-mode
                   and common-mode variables, only the differential-mode 
                   dependent variables and the common-mode independent 
                   variables are considered. 
                   
                   The matrix equation describes the common-mode to 
                   differential-mode conversion of the circuit.
                   
                   Source, detector and loop gain reference will be converted
                   automatically.
                   
                 - 'cd': After grouping of the vaiables in differential-mode
                   and common-mode variables, only the common-mode dependent 
                   variables and the differential-mode independent ariables are c
                   onsidered. 
                   
                   The matrix equation describes the differential-mode to 
                   common-mode conversion of the circuit.
                   
                   Source, detector and loop gain reference will be converted
                   automatically.
    
                 Defaults to None
    
:type convType: str           
                   
:param pardefs: #. None: 
    
                   Analysis is performed with circuit element values or 
                   expressions.
                  
                #. 'circuit': 
                  
                   Analysis is performed with circuit element values or 
                   expressions in which parameters defined with the circuit are 
                   recursively substituted.
                  
                #. A dictionary with key-value pairs: 
                    
                   - key = parameter name (sympy.Symbol), 
                   - value = parameter expression (sympy.Expr) or a numeric 
                     value (int, float). 
                    
                   Analysis is performed with circuit element values or 
                   expressions in which parameters defined in the dictionary 
                   are recursively substituted.

                Defaults to None
                             
:type pardefs: NoneType, str or dict

:param numeric: #. True: results will be returned in float format with pi
                   substituted with its numeric value and numerically evaluated
                   functions.
                #. False: results will be returned with rational numbers and
                   without numeric evaluation of functions or constants.
                
                Defaults to False
                
:type numeric: Bool

:param stepdict: Parameter stepping is implemented for plotting.
                 <stepdict> defines if stepping will be applied.
                 
                 #. None: no parameter(s) will be stepped.
                 #. A dictionary with key-value pairs of stepping parameters: 
                    this will invoke parameter stepping. Keys and possible 
                    associated values are given below.
                     
                   - stepmethod (str); 'lin', 'log', 'list', 'array'
                   - params    : (str, sympy.Symbol) for stepmethod: lin', 
                     'log', and 'list' (list of str or sympy.Symbol) for 
                     stepmethod: 'array'
                   - start     : (float, int, str): start value for linear and 
                     log stepping
                   - stop      : (float, int, str): stop value for lin and log 
                     stepping
                   - num       : (int), number of steps for lin and log 
                     stepping
                   - values    : (list of int, float, or str) step values for
                     stepmethod: 'list' (list of lists of int, float, or str)
                     step values for stepmethod: 'array'. Each list applies to 
                     one step variable.
                                 
----
"""
import sympy as sp
from copy import deepcopy
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPhtml import htmlPage, img2html, head2html, elementData2html 
from SLiCAP.SLiCAPhtml import params2html, file2html, netlist2html
from SLiCAP.SLiCAPinstruction import instruction
from SLiCAP.SLiCAPyacc import _checkCircuit
from SLiCAP.SLiCAPkicad import _kicadNetlist, KiCADsch2svg
from SLiCAP.SLiCAPltspice import _LTspiceNetlist
from SLiCAP.SLiCAPgschem import _gNetlist  
from SLiCAP.SLiCAPmath import _checkExpression

def _makeNetlist(fileName, cirTitle=None, language="SLiCAP"):
    """
    Creates a netlist from a schematic file generated with LTspice or gschem.
    """
    fileName  = fileName.replace('\\', '/')   
    fileParts = fileName.split('/')
    netlist   = None
    subckt    = False
    if cirTitle == None:
        nameParts = fileParts[-1].split('.')
        cirTitle = nameParts[0]
        cirType  = nameParts[-1].lower()
    elif " " in cirTitle and (cirTitle[0] != '"' or cirTitle[-1] != '"'):
        cirTitle = '"' + cirTitle + '"'
    if cirType == "asc":
        _LTspiceNetlist(fileName, cirTitle)
    elif cirType == "sch":
        _gNetlist(fileName, cirTitle)
    elif cirType == "kicad_sch":
        netlist, subckt = _kicadNetlist(fileName, cirTitle, language=language)
    elif cirType == "cir":
        pass
    else:
        print("Cannot determine netlister for file extension: {}"
              .format(cirType))
    return netlist, subckt
        
def makeCircuit(fileName, cirTitle=None, imgWidth=500, 
                 expansion=True, description=None, language="SLiCAP"):
    """
    #. Creates and returns a circuit object from:
        
       - A netlist file (".cir" file: always in the cir folder of the project
         folder)
       - A KiCAD schematic file (".kicad_sch" file, full path or relative to 
         project folder)
       - An LTspice schematic file (".asc" file, full path or relative to 
         project folder)
       - A Lepton-eda schematic file (".sch" file, full path or relative to 
         project folder; Linux and macOS only)
       - A gschem schematic file (".sch" file, full path or relative to script; 
         MSWindows only)
    
    #. Creates drawing size PDF and SVG image files of the schematics diagram 
       (KiCAD and Lepton-eda only, KiCAD requires installation of Inkscape) and 
       puts these images in the ini.img_path folder.
    
    #. Creates an HTML page with circuit information.
    
    ----
    
    :param fileName: Circuit file name, netlist files ".cir" are located in the
                     ini.cir directory, which can be altered in the SLiCAP.ini
                     file in the project directory.
                     
                     Schematic files from KiCAD, LTspice, Lepton-eda or gschem
                     should be given with their path relative to the project
                     folder or with their absolute path.
    :type fileName:  str
                    
    :param cirTitle: Title of the circuit if no title is given for netlist generation:
        
                     - KiCAD: uses Title field on schematic or the filename
                       without  ".kicad_sch"
                     - LTspice, gschem, lepton-eda use the filename without 
                       extension ".asc" or ".sch".
                       
                     Defaults to None
                     
    :type cirTitle: str
    
    :param imgWidth: - Width of the circuit image in pixels (for placement on 
                       the HTML page with circuit data)
                     - None: No image file will be placed on the HTML page with
                       circuit data
    
                     Defaults to 500
                     
    :type imgWidth: int, None
                
    :param expansion: - True: expanded netlist and parameter definitions are
                        shown on the "Circuit Data" HTML page
                      - False: only the circuit image and the circuit netlist 
                        are shown on the "Circuit Data" HTML page
                        
    :type expansion: Bool
    
    :param description: Name of the file with a HTML Description of the
                        circuit. It will be included in the HTML page with the 
                        circuit data.
                        
                        SLiCAP will look for this text file in the ini.txt
                        directory (default './txt/')
    :type description: str
    """
    cir, subckt = _makeNetlist(fileName, cirTitle=cirTitle, language=language)
    if not subckt:
        language = language.upper()
        cirName, ext = fileName.replace('\\', '/').split('/')[-1].split('.')
        if language == "SLICAP":
            cir = _checkCircuit(cirName + ".cir")
        elif language == "SPICE":
            ini.html_prefix = ('-'.join(cirName.split()) + '_')
            ini.html_index = 'index.html'
            htmlPage(cirName, index = True)
        htmlPage("Circuit data")
        if description != None:
            head2html('Circuit description')
            file2html(description)
        if imgWidth != None:
            head2html("Schematic diagram of {}".format(cirName + '.' + ext))
            img2html(cirName + ".svg", 
                     imgWidth, caption = 'Circuit diagram of {}.'.format(cirName), 
                     label = 'fig_{}'.format(cirName + '.' + ext))
        netlist2html(cirName + ".cir", label = 'netlist_{}'.format(cirName), 
                     labelText='Netlist of {}.'.format(cirName + ".cir"))
        if language == "SLiCAP":
            elementData2html(cir, label='elementdata_{}'.format(cirName), 
                             caption="Expanded netlist of {}.".format(cirName + ".cir"))
            params2html(cir, label='params_{}'.format(cirName), 
                        caption="Parameter definitions of {}.".format(cirName + ".cir"))
    return cir

def doMatrix(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer=None, convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Returns the MNA matrix, the vector with dependent variables and the vector 
    with independent variables.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doMatrix(<circuit>).M: MNA matrix (sympy.Matrix)
    - doMatrix(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doMatrix(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the matrix equation of the circuit
        matrixResult = sl.doMatrix(cir)
        # Create an HTML page for displaying the results
        sl.htmlPage("Matrix equation")
        sl.matrices2html(matrixResult)
        # assign the MNA matris to the variable M
        M  = matrixResult.M  
        # assign the vector with independent variables to Iv
        Iv = matrixResult.Iv
        # assign the vector with dependent variables to Dv
        Dv = matrixResult.Dv 
        # Print the result of the matrix multiplication to the active HTML page
        sl.eqn2html(Iv, M*Dv))
    """
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='matrix', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result 

def doLaplace(cir, source='circuit', detector='circuit', lgref='circuit', 
              transfer='gain', convtype=None, pardefs=None, numeric=False, 
              stepdict=None):
    """
    Returns a transfer function or a detector voltage or current.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doLaplace(<circuit>).M: MNA matrix (sympy.Matrix)
    - doLaplace(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doLaplace(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doLaplace(<circuit>).numer: Numerator of the voltage transfer from V1 to
      V_out (sympy.Expr)
    - doLaplace(<circuit>).denom: Denominator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doLaplace(<circuit>).laplace: Voltage transfer from V1 to V_out 
      (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the voltage transfer from V1 to V_out:
        V_gain = sl.doLaplace(cir).laplace
    
    """
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='laplace', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doDC(cir, source='circuit', detector='circuit', lgref='circuit', 
         transfer='gain', convtype=None, pardefs=None, numeric=False, 
         stepdict=None):
    """
    Returns the zero-frequency value (DC value) of a transfer or a detector
    voltge or current.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doDC(<circuit>).M: MNA matrix (sympy.Matrix)
    - doDC(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doDC(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doDC(<circuit>).numer: Numerator of the DC voltage transfer from V1 to 
      V_out (sympy.Expr)
    - doDC<circuit>).denom: Denominator of the DC voltage transfer from V1 to 
      V_out (sympy.Expr)
    - doDC(<circuit>).laplace: DC voltage transfer from V1 to V_out 
      (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the DC voltage transfer from V1 to V_out:
        V_DCgain = sl.doDC(cir).laplace
    
    """
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='dc', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doNumer(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer='gain', convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Returns the numerator of a transfer or of a detector voltage or current.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doNumer(<circuit>).M: MNA matrix (sympy.Matrix)
    - doNumer(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doNumer(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doNumer(<circuit>).numer: Numerator of the voltage transfer from V1 to
      V_out (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the numerator od the voltage transfer from V1 to V_out:
        V_gain = sl.doNumer(cir).laplace
    
    """
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='numer', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doDenom(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer='gain', convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Returns the denominator of a transfer or a detector voltage or current.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doDenom(<circuit>).M: MNA matrix (sympy.Matrix)
    - doDenom(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doDenom(<circuit>).denom: Denominator of the voltage transfer from V1 
      to V_out (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the numerator od the voltage transfer from V1 to V_out:
        V_gain = sl.doNumer(cir).laplace
    
    """
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='denom', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doTime(cir, source='circuit', detector='circuit', lgref='circuit', 
           transfer=None, convtype=None, pardefs=None, numeric=False, 
           stepdict=None):
    """
    Returns the detector voltage or current (Inverse Laplace Transform).
    
    The (Laplace) values of all independent sources are taken as input signals.
    Application of initial conditions has not yet ben implemented.
    
    The arguments for source and transfer will be ignored and both considered:
    None).
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doTime<circuit>).M: MNA matrix (sympy.Matrix)
    - doLaplaceVI(<circuit>.Iv: Vector with independent variables 
      (sympy.Matrix)
    - doTime<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doTime(<circuit>).numer: Numerator of the Laplace Transform of the
      detector voltage or current  (sympy.Expr)
    - doTime<circuit>).denom: Denominator of the Laplace Transfor of the
      detector voltage or current  (sympy.Expr)
    - doTime(<circuit>).laplace: Laplace Transform of the detector voltage
      or current (sympy.Expr)
    - doTime(<circuit>).time: Detector voltage or current
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the Lapace transform of the detector voltage V_out:
        V_out = sl.doLaplaceVI(cir).laplace
    
    """
    result = _executeInstruction(cir, transfer=None, source=None, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='time', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doImpulse(cir, source='circuit', detector='circuit', lgref='circuit', 
              transfer='gain', convtype=None, pardefs=None, numeric=False, 
              stepdict=None):
    """
    Returns the unit-impulse response of a transfer (ILT of a transfer 
    function). The argument 'transfer' will be set to gain if None is given.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doImpulse(<circuit>).M: MNA matrix (sympy.Matrix)
    - doImpulse(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doImpulse(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doImpulse(<circuit>).numer: Numerator of the voltage transfer from V1 to
      V_out (sympy.Expr)
    - doImpulse(<circuit>).denom: Denominator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doImpulse(<circuit>).laplace: Voltage transfer from V1 to V_out 
      (sympy.Expr)
    - doImpulse(<circuit>).impulse: Unit-impulse response of the Voltage 
      transfer from V1 to V_out (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the unit impulse response of the transfer from V1 to V_out:
        h_t = sl.doImpulse(cir).impulse
    
    """
    if transfer == None:
        print("Warning: Invalid transfer=None has been changed to 'gain'")
        transfer = 'gain'
        
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='impulse', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doStep(cir, source='circuit', detector='circuit', lgref='circuit', 
           transfer='gain', convtype=None, pardefs=None, numeric=False, 
           stepdict=None):
    """
    Returns the unit-step response of a transfer (based upon the ILT).  The 
    argument 'transfer' will be set to gain if None is given.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doStep(<circuit>).M: MNA matrix (sympy.Matrix)
    - doStep(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doStep(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doStep(<circuit>).numer: Numerator of the voltage transfer from V1 to
      V_out (sympy.Expr)
    - doStep(<circuit>).denom: Denominator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doStep(<circuit>).laplace: Voltage transfer from V1 to V_out (sympy.Expr)
    - doStep(<circuit>).stepResp: Unit-step response of the Voltage transfer 
      from V1 to V_out (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the unit-step response of the transfer from V1 to V_out:
        a_t = sl.doStep(cir).stepResp
    
    """
    if transfer == None:
        print("Warning: Invalid transfer=None has been changed to 'gain'")
        transfer = 'gain'
        
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='step', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doPoles(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer='gain', convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Returns the poles of a transfer function.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doPoles(<circuit>).M: MNA matrix (sympy.Matrix)
    - doPoles(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doPoles(<circuit>).denom: Denominator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doPoles(<circuit>).poles: List with solutions of denom=0 for the Laplace 
      variable (ini.laplace) (list with sympy.Expr or floats)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
    
    Frequencies of poles are always in radians per seconds. The setting of 
    ini.hz only affects the diplay of tables in the console (listPZ()), on HTML
    pages (pz2httml()), or in LaTeX and RST reports.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the poles of the transfer from V1 to V_out:
        Poles = sl.doPoles(cir).poles
    
    """
    if transfer == None:
        print("Warning: Invalid transfer=None has been changed to 'gain'")
        transfer = 'gain'
        
    result = _executeInstruction(cir, transfer=transfer, lgref=lgref, 
                                 convtype=convtype, datatype='poles', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doZeros(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer='gain', convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Returns the zeros of a transfer function.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doZeros(<circuit>).M: MNA matrix (sympy.Matrix)
    - doZeros(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doZeros(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doZeros(<circuit>).numer: Numerator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doZeros(<circuit>).zeros: List with solutions of numer=0 for the Laplace 
      variable (ini.laplace) (list with sympy.Expr or floats)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
    
    Frequencies of zeros are always in radians per seconds. The setting of 
    ini.hz only affects the diplay of tables in the console (listPZ()), on HTML
    pages (pz2httml()), or in LaTeX and RST reports.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the zeros of the transfer from V1 to V_out:
        Zeros = sl.doZeros(cir).zeros
    
    """  
    if transfer == None:
        print("Warning: Invalid transfer=None has been changed to 'gain'")
        transfer = 'gain'
        
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='zeros', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doPZ(cir, source='circuit', detector='circuit', lgref='circuit', 
         transfer='gain', convtype=None, pardefs=None, numeric=False, 
         stepdict=None):
    """
    Returns the DC value, the zeros, and the poles of a transfer function. 
    Poles and zeros that coincide within the diaplay accuracy (ini.disp) are
    canceled.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doPZ(<circuit>).M: MNA matrix (sympy.Matrix)
    - doPZ(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doPZ(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doPZ(<circuit>).numer: Numerator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doPZ(<circuit>).denom: Denominator of the voltage transfer from V1
      to V_out (sympy.Expr)
    - doPZ(<circuit>).zeros: List with solutions of numer=0 for the Laplace 
      variable (ini.laplace) (list with sympy.Expr or floats)
    - doPZ(<circuit>).poles: List with solutions of denom=0 for the Laplace 
      variable (ini.laplace) (list with sympy.Expr or floats)
    - doPZ(<circuit>).DCvalue: Zero frequency value of the  voltage transfer 
      from V1 to V_out (sympy.Expr)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
    
    Frequencies of poles and zeros are always in radians per seconds. The 
    setting of ini.hz only affects the diplay of tables in the console 
    (listPZ()), on HTML pages (pz2httml()), or in LaTeX and RST reports.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the zeros of the transfer from V1 to V_out:
        Zeros = sl.doZeros(cir).zeros
    
    """  
    if transfer == None:
        print("Warning: Invalid transfer=None has been changed to 'gain'")
        transfer = 'gain'
        
    result = _executeInstruction(cir, transfer=transfer, source=source, 
                                 detector=detector, lgref=lgref, 
                                 convtype=convtype, datatype='pz', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doSolve(cir, source=None, detector=None, lgref=None, transfer=None, 
            convtype=None, pardefs=None, numeric=False, stepdict=None):
    """
    Returns the (Laplace) solution of the circuit.
    
    The (Laplace) values of all independent sources are taken as input signals.
    The application of initial conditions has not yet been implemented.
    
    The arguments for source, detector, lgref and transfer will be ignored and
    considered: None.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doSolve(<circuit>).M: MNA matrix (sympy.Matrix)
    - doSolve(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doSolve(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doSolve(<circuit>).solve Vector with solutions of dependent variables
      (sympy.Matrix)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the network solution:
        solution = sl.doSolve(cir).solve
    
    """
    if transfer != None:
        print("Warning: Invalid transfer={} will be changed to None".format(str(transfer)))
        
    result = _executeInstruction(cir, transfer=None, source=None, 
                                 detector=None, lgref=None, 
                                 convtype=convtype, datatype='solve', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result

def doDCsolve(cir, source=None, detector=None, lgref=None, transfer=None, 
              convtype=None, pardefs=None, numeric=False, stepdict=None):
    """
    Returns the DC solution of the circuit.
    
    The dc values of all independent sources are taken as input signals.
    
    The arguments for source, detector, lgref and transfer will be ignored and
    considered: None.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doDCSolve(<circuit>).M: MNA matrix (sympy.Matrix)
    - doDCSolve(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doDCSolve(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doDCSolve(<circuit>).dcSolve: Vector with DC solutions of dependent 
      variables (sympy.Matrix)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the DC network solution:
        DCsolution = sl.doDCsolve(cir).DCsolve
    
    """
    if transfer != None:
        print("Warning: Invalid transfer={} will be changed to None".format(str(transfer)))
        
    result = _executeInstruction(cir, transfer=None, source=None, 
                                 detector=None, lgref=None,  convtype=convtype,
                                 datatype='dcsolve', pardefs=pardefs, 
                                 numeric=numeric, stepdict=stepdict)
    return result

def doTimeSolve(cir, source=None, detector=None, lgref=None, transfer=None, 
                convtype=None, pardefs=None, numeric=False, stepdict=None):
    """
    Returns the time-domain solution of the circuit, using the Inverse Laplace
    Transform.
    
    The (Laplace) values of all independent sources are taken as input signals.
    The application of initial conditions has not yet been implemented.
    
    The arguments for source, detector, lgref and transfer will be ignored and
    considered: None.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doTimeSolve(<circuit>).M: MNA matrix (sympy.Matrix)
    - doTimeSolve(<circuit>.Iv: Vector with independent variables (sympy.Matrix)
    - doTimeSolve(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doTimeSolve<circuit>).timeSolve Vector with Dtime-domain solutions of 
      dependent variables (sympy.Matrix)
      
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    
    **Example**
    
    .. code-block:: python
        
        import SLiCAP as sl
        sl.initProject("My First RC Network")
        # Generate the circuit object from the netlist
        cir = sl.makeCircuit("myFirstRCnetwork.cir")
        # Obtain the DC network solution:
        timeSolution = sl.doTimeSolve(cir).DCsolve
    
    """
    if transfer != None:
        print("Warning: Invalid transfer={} will be changed to None".format(str(transfer)))
        
    result = _executeInstruction(cir, transfer=None, source=None, 
                                 detector=None, lgref=None, 
                                 convtype=convtype, datatype='timesolve', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    
    return result

def doNoise(cir, source='circuit', detector='circuit', lgref=None, 
            transfer=None, convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Evaluates the detector noise spectral density and the individual 
    contributions of all noise sources to it. 
    
    If a signal source is specified, it also calculates the source-referred 
    noise spectral density and the individual contributions of all noise
    sources to it.
    
    The noise of all independent sources, the noise temperatures and the 
    flicker noise corner frequencies of resistors are taken as inputs. All
    noise sources are assumed to be uncorrelated. Correlation can modeled with
    transfer functions (controlled sources).
    
    The arguments for lgref and transfer will be ignored and considered: None.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doNoise(<circuit>).M: MNA matrix (sympy.Matrix)
    - doNoise(<circuit>).Iv: Vector with independent variables (sympy.Matrix)
    - doNoise(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doNoise(<circuit>).onoise: detector-referred noise spectrum in V^2/Hz or 
      A^2/Hz (sympy.Expr)
    - doNoise(<circuit>).onoiseTerms: dictionary with key-value pairs:
        
      - key (str): name of the noise source, the noise source associated with a 
        resistor 'Rx' is referred to as 'I_noise_Rx'
      - value (sympy.Expr): contribution of this source to the detector-
        referred noise in V^2/Hz or A^2/Hz
        
    - doNoise(<circuit>).inoise: source-referred noise spectrum in V^2/Hz or 
      A^2/Hz (sympy.Expr)
      
    - doNoise(<circuit>).inoiseTerms: dictionary with key-value pairs:
        
      - key (str): name of the noise source, the noise source associated with a 
        resistor 'Rx' is referred to as 'I_noise_Rx'
      - value (sympy.Expr): contribution of this source to the source-referred 
        noise in V^2/Hz or A^2/Hz
        
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
        
    """
    if transfer != None:
        print("Warning: Invalid transfer={} will be changed to None".format(str(transfer)))
        
    result = _executeInstruction(cir, transfer=None, source=source, 
                                 detector=detector, lgref=None, 
                                 convtype=convtype, datatype='noise', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)

    return result

def doDCvar(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer=None, convtype=None, pardefs=None, numeric=False, 
            stepdict=None):
    """
    Evaluates the variance of the detector DC voltage or current and the 
    individual contributions of all noise sources to it. 
    
    If a signal source is specified, it also calculates the source-referred 
    DC variance and the individual contributions of all DC sources and 
    resistors to it.
    
    The DC variance of all independent sources and resistors are taken as 
    inputs. Correlation can be accounted for using matching and tracking
    specifications.
    
    The arguments for lgref and transfer will be ignored and considered: None.
    
    :return: SLiCAP results object of which the following attributes with be
             set as a result of this instruction:
    
    :rtype: SLiCAP.SLiCAPinstruction.instruction object
    
    **Return value attributes**
    
    - doDCvar(<circuit>).M: MNA matrix (sympy.Matrix)
    - doDCvar(<circuit>).Iv: Vector with independent variables (sympy.Matrix)
    - doDCvar(<circuit>).Dv: Vector with dependent variables (sympy.Matrix)
    - doDCvar(<circuit>).ovar: detector-referred DC variance in V^2 or A^2 
      (sympy.Expr)
    - doDCvar(<circuit>).ovarTerms: dictionary with key-value pairs:
        
      - key (str): name of the variance source, the variance of the current
        associated with a resistor 'Rx' is referred to as 'I_dcvar_Rx'
      - value (sympy.Expr): contribution of this source to the detector-
        referred variance in V^2 or A^2
        
    - doDCvar(<circuit>).ivar: source-referred DC variance in V^2 or A^2 
      (sympy.Expr)
      
    - doDCvar(<circuit>).inoiseTerms: dictionary with key-value pairs:
        
      - key (str): name of the variance source, the variance of the current
        associated with a resistor 'Rx' is referred to as 'I_dcvar_Rx'
      - value (sympy.Expr): contribution of this source to the source-
        referred variance in V^2 or A^2
        
    If parameter stepping is applied, all above attributes are lists of values
    or expressions for each step.
      
    **Parameters**
    
    See section `General instruction format`_.
    """

    if transfer != None:
        print("Warning: Invalid transfer={} will be changed to None".format(str(transfer)))
        
    result = _executeInstruction(cir, transfer=None, source=source, 
                                 detector=detector, lgref=None, 
                                 convtype=convtype, datatype='dcvar', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)

    return result

def doParams(cir, source='circuit', detector='circuit', lgref='circuit', 
            transfer=None, convtype=None, pardefs='circuit', numeric=True, 
            stepdict=None):
    
    """
    This function is used in combination with plotSweep(funcType='param')
    It only needs the circuit object argument and returns the SLiCAP instruction
    object with the circuit object as attribute. This is used by plotSweep() to
    plot parameters against each other.
    """
    result =  _executeInstruction(cir, transfer=None, source=None, 
                                 detector=None, lgref=None, 
                                 convtype=None, datatype='params', 
                                 pardefs=pardefs, numeric=numeric, 
                                 stepdict=stepdict)
    return result
    
def _executeInstruction(cir, transfer=None, source='circuit', 
                        detector='circuit', lgref='circuit', convtype='circuit', 
                        datatype=None, pardefs='circuit', numeric=False, 
                        stepdict=None):
    """
    Converts the shell instruction into a basic instruction object, executes it
    and returns the result.

    """
    i1         = instruction()
    i1.circuit = deepcopy(cir) # Changes made to the circuit during execution 
                               # of the instruction, will not affect the main 
                               # circuit object
    if detector == 'circuit':
        i1.detector = cir.detector
    elif detector != None:
        i1.setDetector(detector)
    if source == 'circuit':
        i1.source = cir.source
    elif source != None:
        i1.setSource(source)
    if lgref == 'circuit':
        i1.lgRef = cir.lgRef
    elif lgref!= None:
        i1.setLGref(lgref)
    if transfer == None:
        i1.gainType = 'vi'
    else:
        i1.setGainType(transfer)
    i1.dataType    = datatype
    i1.numeric     = numeric
    if convtype != None:
        i1.convType    = convtype.lower()
    else:
        i1.convType = None
    if pardefs == None:
        i1.substitute = False
    else:
        i1.substitute = True
    #oldParDefs     = deepcopy(i1.circuit.parDefs)
    if type(pardefs) == dict:
        i1.parDefs = {}
        for key in pardefs.keys():
            i1.parDefs[sp.Symbol(str(key))] = _checkExpression(pardefs[key])
        i1.ignoreCircuitParams = True
    elif pardefs== "circuit":
        i1.parDefs = deepcopy(cir.parDefs)
        i1.ignoreCircuitParams = False
    else:
        i1.ignoreCircuitParams = False
    if stepdict == None:
        i1.stepOff()
    else:
        stepParams        = _makeStepParams(stepdict)
        try:
            i1.stepMethod = stepParams['stepMethod']
        except KeyError:
            pass
        try:
            i1.stepStart  = stepParams['stepStart']
        except KeyError:
            pass
        try:
            i1.stepStop   = stepParams['stepStop']
        except KeyError:
            pass
        try:
            i1.stepNum    = stepParams['stepNum']
        except KeyError:
            pass
        try:
            i1.stepVar    = stepParams['stepVar']
        except KeyError:
            pass
        try:
            i1.stepVars   = stepParams['stepVars']
        except KeyError:
            pass
        try:
            i1.stepList   = stepParams['stepList']
        except KeyError:
            pass
        try:
            i1.stepArray  = stepParams['Array']
        except KeyError:
            pass
        i1.stepOn()
    #cir.parDefs = deepcopy(oldParDefs)
    return i1.execute()

def _makeStepParams(stepdict):
    """
    Converts the shell step dictionary in to one that contains all the entries
    for the basic instruction.

    """
    outDict = {}
    outDict['stepMethod'] = stepdict['method']
    try:
        outDict['stepStart'] = stepdict['start']
    except KeyError:
        pass
    
    try:
        outDict['stepStop'] = stepdict['stop']
    except KeyError:
        pass
    try:
        outDict['stepNum'] = stepdict['num']
    except KeyError:
        pass
    try:
        if type(stepdict['params']) == str:
            outDict['stepVar'] = stepdict['params']
        elif type(stepdict['params']) == list:
            outDict['stepVars'] = stepdict['params']
    except KeyError:
        pass
    try:
        if type(stepdict['values']) == list:
            if len(stepdict['values']) > 0:
                if type(stepdict['values'][0]) == list:
                    outDict['Array'] = stepdict['values']
                outDict['stepList'] = stepdict['values']
    except KeyError:
        pass
    return outDict