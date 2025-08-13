#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP instruction class definition.
"""
import sympy as sp
import numpy as np
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPyacc import _updateCirData, _checkCircuit
from SLiCAP.SLiCAPexecute import _doInstruction, _addResNoiseSources, _delResNoiseSources
from SLiCAP.SLiCAPprotos import circuit
from SLiCAP.SLiCAPmath import _checkNumber

_GAINTYPES = ['vi', 'gain', 'loopgain', 'servo', 'asymptotic', 'direct']
_CONVTYPES = ['dd', 'dc', 'cd', 'cc', 'all']
_DATATYPES = ['matrix', 'noise', 'solve', 'time', 'dc', 'dcvar', 'dcsolve', 'timesolve',
             'numer', 'denom', 'laplace', 'zeros', 'poles', 'pz', 'impulse',
             'step', 'params']

class instruction(object):
    """
    Prototype Instruction object.
    """
    def __init__(self):
        
        # Attributes holding the results of the execution
        
        self.DCvalue     = []
        """
        Zero-frequency value in case of dataType 'pz'. (sympy.Expr, sympy.Float)
        """
        self.poles       = []
        """
        Complex frequencies in [rad/s] (list)
        """

        self.zeros       = []
        """
        Complex frequencies in [rad/s] (list)
        """
        self.svarTerms   = {}
        """
        Dict with source variances
        
        Key = (str) name of the dcvar source
        Value = (sympy.Expr) dcvar value in V^2 or A^2
        """

        self.ivarTerms   = {}
        """
        Dict with lists with contributions to source-referred variance.

        Key = (str) name of the dcvar source
        Value = (sympy.Expr) contribution to the source-referred variance in 
        V^2 or A^2
        """

        self.ovarTerms   = {}
        """
        Dict with lists with contributions to detector-referred variance.

        Key = (str) name of the dcvar source
        Value = (sympy.Expr) contribution to the detector-referred variance in 
        V^2 or A^2
        """

        self.ivar        = []
        """
        Total source-referred variance in V^2 or A^2 (sympy.Expr)
        """

        self.ovar        = []
        """
        Total detector-referred variance in V^2 or A^2 (sympy.Expr)
        """

        self.solve       = []
        """
        Laplace solution of the network.
        """

        self.dcSolve     = []
        """
        DC solution of the network.
        """

        self.timeSolve   = []
        """
        Time-domain solution of the network.
        """

        self.snoiseTerms = {}
        """
        Dict with source noise spectra.
        
        Key = (str) name of the noise source
        Value = (sympy.Expr) noise spectral density in V^2/Hz or A^2/Hz
        """

        self.inoiseTerms = {}
        """
        Dict with lists with contributions to source-referred noise spectrum
        
        Key = (str) name of the noise source
        Value = (sympy.Expr) contribution of that noise source to the 
        source-referred noise spectrum in V^2/Hz or A^2/Hz
        """
        self.onoiseTerms = {}
        """
        Dict with with contributions to detector-referred noise spectrum
        
        Key = (str) name of the noise source
        Value = (sympy.Expr) contribution of that noise source to the 
        detector-referred noise spectrum in V^2/Hz or A^2/Hz
        """

        self.inoise      = []
        """
        Total source-referred noise spectral density (sympy.Expr) in V^2/Hz or 
        A^2/Hz.
        """

        self.onoise      = []
        """
        Total detector-referred noise spectrum (sympy.Expr) in V^2/Hz or 
        A^2/Hz.
        """

        self.Iv          = None
        """
        Vector with independent variables (sympy.Matrix).
        """

        self.M           = None
        """
        MNA matrix (sympy.Matrix).
        """

        self.A           = None
        """
        Base conversion matrix (sympy.Matrix).
        """

        self.Dv          = None
        """
        Vector with dependent variables (sympy.Matrix).
        """

        self.denom       = []
        """
        Laplace poly of denominator (sympy.Expr).
        """

        self.numer       = []
        """
        Laplace poly of numerator (sympy.Expr).
        """

        self.laplace     = []
        """
        Laplace transfer function, or detector current or voltage (sympy.Expr).
        """

        self.time        = []
        """
        Time-domain response of the circuit (ILT) (sympy.Expr).
        """

        self.impulse     = []
        """
        Unit impulse response (ILT) (sympy.Expr).
        """

        self.stepResp    = []
        """
        Unit step response (ILT) (sympy.Expr).
        """

        self.params      = {}
        """
        Results of parameter sweep (dataType = 'param').
        """
        
        # Attributes holding the instruction settings
        
        self.simType = 'numeric'
        """
        Defines the simulation gain type.

        See **instruction.setSimType(<simType>)** for specification of *instruction.simType*.
        """

        self.gainType = None
        """
        Defines the simulation gain type.

        See **instruction.setGainType(<gainType>)** for specification of *instruction.gainType*.
        """

        self.convType = None
        """
        Defines the conversion type (None, 'dd', 'dc', 'cd', 'cc')

        See **instruction.setConvType(<convType>)** for specification of *instruction.convType*.
        """

        self.dataType = None
        """
        Defines the simulation data type.

        See **instruction.setDataType(<dataType>)** for specification of *instruction.dataType*.
        """

        self.step = False
        """
        Setting for parameter stepping.

        See **instruction.setStepOn()** and **instruction.setStepOff()** for specification of *instruction.step*.
        """

        self.stepVar = None
        """
        Defines the step variable (*str*) for step types 'lin', 'log' and 'list'.

        See **instruction.setStepVar(<stepVar>)** for specification of *instruction.stepVar*.
        """

        self.stepVars = None
        """
        Defines the step variables for 'array' type parameter stepping.

        See **instruction.setStepVars(<stepVars>)** for specification of *instruction.stepVars*.
        """

        self.stepMethod = None
        """
        Step method for parameter stepping.

        See **instruction.setStepMethod(<stepMethod>)** for specification of *instruction.stepMethod*.
        """

        self.stepStart = None
        """
        Start value for stepping methods 'lin' and 'log'.

        See **instruction.setStepStart(<stepStart>)** for specification of *instruction.stepStart*.
        """

        self.stepStop = None
        """
        Stop value for stepping methods 'lin' and 'log'.

        See **instruction.setStepStop(<stepStop>)** for specification of *instruction.stepStop*.
        """

        self.stepNum = None
        """
        Number of steps for step methods 'lin' and 'log'.

        See **instruction.setStepNum(<stepNum>)** for specification of *instruction.stepNum*.
        """

        self.stepList = []
        """
        List with values for step method 'list'.

        See **instruction.setStepList(<stepList>)** for specification of *instruction.stepList*.
        """

        self.stepArray = []
        """
        Array (*list of lists*) with values for step method array.

        See **instruction.setStepArray(<stepArray>)** for specification of *instruction.stepArray*.
        """

        self.stepDict = {}
        """
        Dictionary with key-value pairs:

        key:   name of a step parameter (*sympy.Symbol*)
        value: list with values for this parameter
        """
        
        self.ignoreCircuitParams = False
        """
        For compatibility with version 2. If True a dictionary of parameters 
        will be used for substitutions. Else these parameters will be taken 
        from the circuit definition.
        """

        self.source = [None, None]
        """
        Refdes of the signal source (independent v or i source).

        See **instruction.setSource(<source>)** for specification of the source.
        """

        self.detector = None
        """
        Names of the positive and negative detector.

        See **instruction.setDetector(<detector>)** for specification of the detector.
        """

        self.pairExt = ini.pair_ext
        """
        Extensions used to indicate paired nodes or elements.
        Default is: [None, None].
        """

        self.removePairSubName = ini.remove_param_pair_ext # True
        """
        If True, the subcircuit pair extension will be removed from parameters
        in expressions of paired elements in sub circuits. Defaults to True.

        :note: Warning: this may result in undesired behavior if global parameters
               carry the name of parameters in paired sub circuits.
        """

        self.lgRef = [None, None]
        """
        Refdes of the controlled source(s) that is (are) assigned as loop gain
        reference. A second controlled source is required for decomposition
        of circuits in common-mode and differential-mode equivalents.

        See **instruction.setLGref(<detector>)** for specification of the loop
        gain reference.
        """

        self.lgValue = [None, None]
        """
        Value of the loopgain reference will be stored during execution of the
        instruction.
        """

        self.circuit = None
        """
        Circuit (*SLiCAPprotos.circuit*) used for this instruction. Can be
        assigned by setting this attribute, or will be defined by running:
        instruction.setCircuit(<fileName>).

        :Example:

        >>> # Create an instance of a circuit object by checking a netlist:
        >>> my_circuit = checkCircuit('my_circuit.cir')
        >>> # create an instance of an instruction object:
        >>> my_instruction = instruction()
        >>> Use the circuit 'my_circuit' or the instruction 'my_instruction'.
        >>> my_instruction.circuit = my_circuit

        :Example:

        >>> # create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        """
        
        self.numeric = True
        """
        If True, functions and constants will be evaluated numerically and
        rational numbers will be converted in sympy.Float
        """

        self.substitute = True
        """
        If True: parameters from self.circuit will be substituted recursively
        in element values. 
        
        Else: element values defined in the circuit will be used
        """
        
        self.errors = 0
        """
        Number of errors found in the definition of this instruction.

        :note:

        The instruction.errors attribute should not be modified
        directly by the user. It is determined automatically when executing
        the instruction.
        """

        self.detUnits = None
        """
        Detector units 'V' or 'A' (automatically detected in **instruction.checkDetector()**).
        """

        self.srcUnits = None
        """
        Source units 'V' or 'A' (automatically detected in **instruction.checkSource()**).
        """

        self.detLabel = None
        """
        Name for the detector quantity to be used in expressions or plots
        (automatically determined in **instruction.checkDetector()**).
        """

        self.label = ''
        """
        Label to be used in plots.
        """

        self.parDefs = None
        """
        Parameter definitions for the instruction. Will be updated by executing
        the instruction.
        """        
        self.references = []
        """
        Referenced elements in the circuit AFTER execution of an 
        instruction.

        Will be copied from  instruction.circuit.references at the start of
        the execution of the instruction and possibly modified during the 
        excution of the instruction.
        """
    
    def clear(self):
        
        self.DCvalue     = []
        self.poles       = []
        self.zeros       = []
        self.svarTerms   = {}
        self.ivarTerms   = {}
        self.ovarTerms   = {}
        self.ivar        = []
        self.ovar        = []
        self.solve       = []
        self.dcSolve     = []
        self.timeSolve   = []
        self.snoiseTerms = {}
        self.inoiseTerms = {}
        self.onoiseTerms = {}
        self.inoise      = []
        self.onoise      = []
        self.Iv          = None
        self.M           = None
        self.A           = None
        self.Dv          = None
        self.denom       = []
        self.numer       = []
        self.laplace     = []
        self.time        = []
        self.impulse     = []
        self.stepResp    = []
        self.params      = {}

    def setSimType(self, simType):
        """
        Defines the simulation type for the instruction.

        :param simType: Simulation type: 'symbolic' or 'numeric'
        :type simType: str

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Set the simulation type to numeric:
        >>> my_instr.setSimType('numeric')
        >>> # Set the simulation type to symbolic:
        >>> my_instr.setSimType('symbolic')

        :note:

        SLiCAP always uses symbolic calculation methods. Only in a limited
        number of cases SLiCAP calulates with floats (pole-zero analysis,
        determination of the phase margin, etc.).

        With the simulation type set to 'numeric' SLiCAP recursively
        substitutes all circuit parameter definitions into expressions used for
        element values. Hence, component values can be expressions with
        symbolic parameters.

        The default number of recursive substitutions is 10. It is defined by
        ini.recSubst and can be changed by the user. For using the built-in MOS
        EKV models a value of eight is the minumum for full substitution.

        :Example:

        >>> ini.recSubst = 12 # For deeply nested expressions!

        """
        self.simType    = simType
        self._checkSimType()
        return

    def _checkSimType(self):
        """
        Checks if the simulation type is defined correctly."

        Called by **instruction.check()** and by **setSimType(<simType>)**.
        """
        if type(self.simType) == str:
            if self.simType.lower() == 'symbolic':
                self.simType    = 'symbolic'
                self.numeric    = False
                self.substitute = False
            elif self.simType.lower() == 'numeric':
                self.simType    = 'numeric'
                self.numeric    = True
                self.substitute = True
            else:
                print("Error: unknown simulation type: '{0}'.".format(self.simType))
                self.errors += 1
        else:
            print("Error: argument type must be type 'str'.")
            self.errors += 1

    def setGainType(self, gainType):
        """
        Defines the gain type for the instruction.

        :param gainType: gain type for the instruction: 'gain', 'asymptotic',
                         'loopgain', 'servo', 'direct', or 'vi'.
        :type gainType: str

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Set gain type to 'gain':
        >>> my_instr.setGainType('gain')
        """
        self.gainType = gainType
        self._checkGainType()

    def _checkGainType(self):
        """
        Checks if the gain type is defined correctly."

        Called by **instruction.check()** and by **setGainType(<gainType>)**.
        """
        if type(self.gainType) == str:
            if self.gainType.lower() in _GAINTYPES:
                self.gainType = self.gainType.lower()
            else:
                print("Error: unknown gain type: '{0}'.".format(self.gainType))
                self.errors += 1
        elif self.gainType == None:
            print("Error: missing gain type.")
        else:
            print("Error: argument type must be type 'str'.")
            self.errors += 1
        return

    def setConvType(self, convType):
        """
        Defines the circuit conversion type for the instruction.

        :param convType: gain type for the instruction: None, 'dd',
                         'dc', 'cd', 'cc', or 'all'.
        :type gainType: str, Bool

        """
        self.convType = convType
        self._checkConvType()

    def _checkConvType(self):
        """
        Checks if the circuit conversion type is defined correctly."

        Called by **instruction.check()** and by **setConvType(<convType>)**.
        """
        if type(self.convType) == str:
            if self.convType.lower() in _CONVTYPES:
                self.convType = self.convType.lower()
            else:
                print("Error: unknown conversion type: '{0}'.".format(self.convType))
                self.errors += 1
        else:
            self.convType = None
        return

    def setPairExt(self, pairExt):
        """
        Defines the extension to element or node IDs for DM and CM pairs.

        :param pairExt: list with extensions for paired nodes.

        :type pairExt: list
        """
        if self.checkPairExt(pairExt) == 0:
            self.pairExt = pairExt
        return

    def checkPairExt(self, pairExt):
        """
        Check the list with extensions of paired nodes.

        :param varPairs: list with extensions of paired nodes.

        :type varPairs: list

        :return: number of errors
        :rtype: int
        """
        errors = 0
        if type(pairExt) != list and len(pairExt) != 2:
            print("Error: expected a list with two extensions for nodes or elements.")
            errors += 1
        if type(pairExt[0]) != str or type(pairExt[1]) != str:
            print("Error: pair extensions for nodes and elements should be of type 'str'.")
            errors += 1
        if len(pairExt[0]) != len(pairExt[1]):
            print("Error: pair extensions should have the same length.")
            errors += 1
        if errors == 0:
            self.pairExt =  pairExt
        return errors

    def setPairedCircuits(self, cirPairs):
        """
        Defines the paired subcircuits for matrix conversion.

        :param varPairs: list with tuples of names (str) of subcircuits
                         that must be considered pairs.
        :type varPairs: tuple
        """
        if self.checkPairedCircuits(cirPairs) == 0:
            self.pairedCircuits = cirPairs
        return

    def checkPairedCircuits(self, circuitPairs):
        """
        Check the list with names of with paired subcircuits.

        :param cirPairs: list with refDes of two subcircuits

        :type varPairs: list

        :return: number of errors
        :rtype: int
        """
        errors = 0
        if type(circuitPairs) != list and len(circuitPairs) != 2:
            print("Error: expected a list with two circuit names")
            errors += 1
        else:
            cirNames = []
            for elName in list(self.circuit.elements.keys()):
                elName = elName.split('_')[-1]
                elType = elName[0].upper()
                if elType == 'X':
                    cirNames.append(elName)
            for cirName in circuitPairs:
                if cirName not in cirNames:
                    print("Error: cannot pair unknown circuit: ", cirName)
                    errors += 1
        return errors

    def setDataType(self, dataType):
        """
        Defines the data type for the instruction.

        :param dataType: data type for the instruction: 'dc', 'dcsolve', 'dcvar',
                         'denom', 'impulse', 'laplace', 'matrix', 'noise', 'numer',
                         'params', 'poles', 'pz', 'solve', 'step', 'time' or 'zeros'.
        :type dataType: str

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Set data type to 'laplace':
        >>> my_instr.setDataType('laplace')
        """
        self.dataType = dataType
        self.checkDataType()
        return

    def checkDataType(self):
        """
        Checks if the data type is defined correctly."

        Called by **instruction.check()** and by **setDataType(<dataType>)**.
        """
        if type(self.dataType) == str:
            if self.dataType.lower() in _DATATYPES:
                self.dataType = self.dataType.lower()
            else:
                print("Error: unknown data type: '{0}'.".format(self.dataType))
                self.errors += 1
        elif self.dataType == None:
            self.errors += 1
            print("Error: missing data type specification.")
        else:
            print("Error: data type must be type 'str' or 'None'.")
        return

    def stepOn(self):
        """
        Enables parameter stepping.

        Does not change other settings for parameter stepping.

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Enable parameter stepping
        >>> my_instruction.stepOn()
        """
        self.step = True
        return

    def stepOff(self):
        """
        Disables parameter stepping.

        Does not change other settings for parameter stepping.

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Disable parameter stepping
        >>> my_instruction.stepOff()
        """
        self.step = False
        return

    def setStepVar(self, stepVar):
        """
        Defines the step variable for parameter step types 'lin', 'log' and 'list'.

        :param stepVar: step variable
        :type stepVar: str, sympy.Symbol

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # Define the circuit parameter 'alpha' as step variable:
        >>> my_instr.setStepVar('alpha')
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()

        :note:

        A list with names (*sympy.Symbol*) that can be used as stepping
        parameter is obtained as follows:

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # print the list with names of all parameters that can be stepped:
        >>> print instr.circuit.params + list(instr.circuit.parDefs.keys())
        """
        self.stepVar = stepVar
        self.checkStepVar()
        return

    def checkStepVar(self):
        """
        Checks if the step variable is defined correctly.

        Called by **instruction.checkStep()** and by **setStepVar(<stepVar>)**.
        """
        if self.stepVar == None:
            self.errors += 1
            print("Error: missing step variable.")
        elif isinstance(self.stepVar, sp.Basic):
            pass
        elif type(self.stepVar) == str:
            self.stepVar = sp.Symbol(self.stepVar)
        else:
            self.errors += 1
            print("Error: argument type must be 'str' or 'sympy.Symbol'.")
        if self.stepVar not in list(self.circuit.parDefs.keys()) and self.stepVar not in self.circuit.params:
            print("Warning: unknown step parameter '{0}'.".format(self.stepVar))
        return

    def setStepVars(self, stepVars):
        """
        Defines the step variables for 'array' type stepping.

        :param stepVars: List with names (*str, sympy.Symbol*) of step
                         variables for array type stepping.
        :type stepVars: list

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define 'array' type stepping:
        >>> my_instr.stepMethod = 'array'
        >>> # Define circuit parameters 'R_a' and 'C_a' as step variables:
        >>> my_instr.setStepVars(['R_a', 'C_a'])
        >>> Define the step values for 'R_a and 'C_a':
        >>> my_instr.setStepArray ([['1k', 1200, 1.2e3],['1u', 10e-6, 0.0001]])
        >>> # Enable parameter stepping
        >>> my_instruction.stepOn()

        :note:

        A list with names (*sympy.Symbol*) that can be used as stepping
        parameter is obtained as follows:

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # print the list with names of all parameters that can be stepped:
        >>> print instr.circuit.params + list(instr.circuit.parDefs.keys())
        """
        self.stepVars = stepVars
        self.checkStepVars()
        return

    def checkStepVars(self):
        """
        Checks if the step variables for array stepping are defined correctly.

        Called by **instruction.checkStep** and by **instruction.setStepVars(<stepVars>)**.
        """
        if self.stepVars == None:
            self.errors += 1
            print("Error: missing list stepVars.")
            return
        errors = 0
        if type(self.stepVars) == list:
            if len(self.stepVars) != 0:
                for i in range(len(self.stepVars)):
                    if type(self.stepVars[i]) == str:
                        try:
                            self.stepVars[i] = sp.Symbol(self.stepVars[i])
                        except:
                            errors += 1
                            print("Error: step variable '{0}' is not a parameter.".format(str(self.stepVars[i])))
                    if isinstance(self.stepVars[i], sp.Basic):
                        if self.stepVars[i] not in list(self.circuit.parDefs.keys()) and self.stepVars[i] not in self.circuit.params:
                            print("Warning: unknown step parameter '{0}'.".format(str(self.stepVars[i])))
                    else:
                        errors += 1
                        print("Error: argument type must be 'str' or 'sympy.Symbol'.")
            else:
                errors += 1
                print("Error: empty stepVars.")
        else:
            print("Error: argument should be a list.")
            errors += 1
        self.errors += errors
        return

    def setStepMethod(self, stepMethod):
        """
        Defines the parameter stepping method.

        :param stepMethod: 'lin', 'log', 'list' or 'array'.
        :type stepMethod: str

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define 'linear' type stepping:
        >>> my_instr.setStepMethod('lin')
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepMethod = stepMethod
        self.checkStepMethod()
        return

    def checkStepMethod(self):
        """
        Checks if the step method is defined correctly.

        Called by **instruction.checkStep** and by **instruction.setStepMethod(<stepMethod>)**.
        """
        if self.stepMethod == None:
            self.errors += 1
            print("Error: missing step method definition.")
        elif type(self.stepMethod) != str:
            self.errors += 1
            print("Error: stepMethod should be type 'str'.")
        else:
            stepMethods = ['lin', 'log', 'list', 'array']
            if self.stepMethod.lower() not in stepMethods:
                self.errors += 1
                print("Error: unknown step method '{0}',".format(self.stepMethod))
            else:
                self.stepMethod == self.stepMethod.lower()
        return

    def setStepStart(self, stepStart):
        """
        Start value for parameter stepping methods 'lin' and 'log'.

        :param stepStart: Start value for parameter stepping methods 'lin' and 'log'.
        :type stepStart: str, int, float

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define linear stepping:
        >>> my_instr.stepMethod = 'lin'
        >>> # Define the start value
        >>> my_instr.setStepStart('1k')  # 1E3
        >>> my_instr.setStepStart(1000)  # 1E3
        >>> my_instr.setStepStart(1e3)   # 1E3
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepStart = stepStart
        self.checkStepStart()
        return

    def checkStepStart(self):
        """
        Checks if the start value for parameter stepping is defined correctly.

        Called by **instruction.checkStep()** and by **instruction.stepStart(<stepStart>)**.
        """
        if self.stepStart == None:
            self.errors += 1
            print("Error: missing stepStart value.")
        else:
            value = float(_checkNumber(self.stepStart))
            if value == None:
                self.errors += 1
                print("Error: cannot determine numeric value of stepStart.")
            else:
                self.stepStart = value
        return

    def setStepStop(self, stepStop):
        """
        End value for parameter stepping methods 'lin' and 'log'.

        :param stepStop: End value for parameter stepping methods 'lin' and 'log'.
        :type stepStop: str, int, float

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define linear stepping:
        >>> my_instr.stepMethod = 'lin'
        >>> # Define the start value
        >>> my_instr.setStepStop('1M')  # 1E6
        >>> my_instr.setStepStop(1e6)   # 1E6
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepStop = stepStop
        self.checkStepStop()
        return

    def checkStepStop(self):
        """
        Checks if the end value for parameter steping is defined correctly.

        Called by **instruction.checkStep()** and by **instruction.stepStop(<stepStop>)**.
        """
        if self.stepStop == None:
            self.errors += 1
            print("Error: missing stepStop value.")
        else:
            value = float(_checkNumber(self.stepStop))
            if value == None:
                self.errors += 1
                print("Error: cannot determine numeric value of stepStop.")
            else:
                self.stepStop = value
        return

    def setStepNum(self, stepNum):
        """
        Defines the number of steps for 'lin' and 'log' parameter stepping.

        :param stepNumber: Number of steps for stepping methods 'lin' and 'log'.
        :type stepStop: int

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define linear stepping:
        >>> my_instr.stepMethod = 'lin'
        >>> # Define the start value
        >>> my_instr.setStepStop('1M')  # 1E6
        >>> my_instr.setStepStop(1e6)   # 1E6
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepNum = stepNum
        self.checkStepNum()
        return

    def checkStepNum(self):
        """
        Checks if the number of steps is defined properly.

        Called by :**instruction.checkStep()** and by **instruction.setStepNum(<stepNum>)**.

        Also called by and by **instruction.setStepNum(<stepNum>)**.
        """
        if self.stepNum == None:
            self.errors += 1
            print("Error: missing stepNum value.")
        else:
            if type(self.stepNum) == int:
                if self.stepNum <= 0:
                    self.errors += 1
                    print("Error: step number must be a positive nonzero integer.")
            else:
                self.errors += 1
                print("Error: step number type must be 'int'.")
        return

    def setStepList(self, stepList):
        """
        Defines the list with step values for step method 'list'. This list will
        be overwritten if the instruction is executed with the step method set
        to 'lin' or 'log'.

        :param stepList: List with step values for the step parameter.
        :type stepList: list

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define 'list' type stepping:
        >>> my_instr.setStepMethod('list')
        >>> # Define the circuit parameter 'alpha' as step parameter:
        >>> my_instr.setStepVar('alpha')
        >>> # Define a list of step values for this parameter.
        >>> my_instr.setStepList(['10m', '20m', '50m', 0.1, 0.2, 0.5, 1, 2, 5])
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepList = stepList
        self.checkStepList()
        return

    def checkStepList(self):
        """
        Checks if the list with step values is defined properly.

        Called by **instruction.checkStep()** and by **instruction.setStepList(<stepList>)**.
        """
        if self.stepList == None:
            self.errors += 1
            print("Error: missing stepList.")
        elif type(self.stepList) == list:
            if len(self.stepList) == 0:
                self.errors += 1
                print("Error: empty stepList.")
            for i in range(len(self.stepList)):
                value = _checkNumber(self.stepList[i])
                if value == None:
                    self.errors += 1
                    print("Error: cannot determine numeric value of stepList[{0}].".format(i))
                else:
                    self.stepList[i] = value
        else:
            self.errors += 1
            print("Error: expected a list type for 'stepValues'.")
        return

    def setStepArray(self, stepArray):
        """
        Defines the array with values for step method array.

        :param stepArray: Nested list: list[i] carries the step values for the
                          step variable in instruction.stepVars[i].
                          The lists should have equal lengths.
        :type stepArray: list

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define 'array' type stepping:
        >>> my_instr.setStepMethod('array')
        >>> # Define circuit parameters 'R_a' and 'C_a' as step variables:
        >>> my_instr.setStepVars(['R_a', 'C_a'])
        >>> Define the step values for 'R_a and 'C_a':
        >>> my_instr.setStepArray([['1k', 1200, 1.2e3],['1u', 10e-6, 0.0001]])
        >>> # Enable parameter stepping
        >>> my_instr.stepOn()
        """
        self.stepArray = stepArray
        self.checkStepArray()
        return

    def checkStepArray(self):
        """
        Checks if the array with step values is defined properly.

        Called by **instruction.checkStep()** and by **instruction.setStepArray(<stepArray>)**.

        The step array is a list of lists. The number of lists must equal the
        number of step variables. The numbers in the lists are subsequent
        values of the associated step variable. All lists should have equal
        lengths.
        """
        if self.stepArray == None:
            self.errors += 1
            print("Error: missing stepArray.")
        elif type(self.stepArray) == list:
            numVars = len(self.stepArray)
            if numVars != len(self.stepVars):
                self.errors += 1
                print("Error: mismatch between dimensions of stepArray and stepVars.")
            else:
                numSteps = len(self.stepArray[0])
                for i in range(numVars):
                    if len(self.stepArray[i]) != numSteps:
                        self.errors += 1
                        print("Error: unequal number of steps for step variables.")
                    if self.errors == 0:
                        for j in range(numSteps):
                            value = _checkNumber(self.stepArray[i][j])
                            if value == None:
                                self.errors += 1
                                print("Error: cannot determine numeric value of stepArray[{0}, {1}].".format(i, j))
                            else:
                                self.stepArray[i][j] = value
        return


    def setSource(self, source):
        """
        Defines the signal source.

        :param source: Name of an independent voltage or current source that
                       exists in the circuit.
        :type source: str

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Define the voltage source 'V1' as signal source:
        >>> my_instr.setSource('V1')

        :note:

        A list with names of independent voltage and current sources that can be
        assigned as signal source can be obtained from the method:
        **instruction.indepVars()**:

        :Example:

        >>> # Create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Obtaine a list with names of independent sources:
        >>> my_instr.circuit.indepVars()
        """
        if type(source) == str:
            self.source = [source, None]
            self.checkSource()
        elif type(source) == list and len(source) == 2:
            self.source = source
            self.checkSource()
        else:
            print("Error in loop gain reference specification.")
        self.checkSource(need = False)
        return

    def checkSource(self, need = True):
        """
        Checks if the source has been defined and if it exists in the circuit.

        Called by **instruction.check()** and by **instruction.setSource(<source>)**.


        :param need: If True, a source is required and an error message will be
                     given if it missing. If False, only the presence of the
                     indicated independent source in the circuit will be
                     verified.

        :type need: bool
        """
        if self.convType == "all":
            print("Error: Conversion type 'all' cannot automatically convert the source to 'DM' or 'CM'. " +
                  "Use convtype=None instead.")
            self.errors += 1
        if need:
            if self.source == None:
                self.errors += 1
                print("Error: missing source definition.")
        if self.source != None:
            for i in range(len(self.source)):
                if self.source[i] == None:
                    if need and i == 0:
                        self.errors += 1
                        print("Error: missing source definition.")
                elif self.source[i] != None and self.source[i] not in self.indepVars():
                    self.errors += 1
                    print("Error: unkown source: '{0}'.".format(self.source[i]))
                elif self.source[i] != None:
                    if i == 0:
                        self.srcUnits = self.source[i][0].upper()
                    else:
                        if self.source[i][0].upper() != self.srcUnits:
                            self.errors += 1
                            print("Error: two sources must be of the same type.")
            if self.srcUnits == 'I':
                self.srcUnits = 'A'
        return

    def setDetector(self, detector):
        """
        Defines the signal detector

        :param detector: Name(s) of one or two nodal voltages or of one or two
                         dependent currents.
        :type detector: list, str

        detector can defined as:

        - None: no detector has been defined
        - str:  a single detector, name of a nodal voltage or a branch current
        - list: with names of either two nodal voltages or two branch currents.

        instruction.checkDetector converts the detector definition into a list
        with a positive and a negative detector [<detP>, <detN>], where detP
        and detN are the names (str) of either two nodal voltages or two branch
        currents. One of those can be 'None'.

        A list with names of dependent variables that can be used as signal
        detector is returned by the method: **instruction.depVars()**.

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Display a list with names of nodal voltages and branch currents
        >>> # that can be assigned to the detector.
        >>> my_instr.depVars()
        ['I_V1', 'V_0', 'V_N001', 'V_out']
        >>> # Voltage at node 'out':
        >>> my_instr.setDetector('V_out')
        >>> # Differential voltage between node 'N001' and 'out':
        >>> my_instr.setDetector(['V_N001', 'V_out'])
        >>> # Current through `V1':
        >>> my_instr.setDetector('I_V1')

        :note:

        The voltage 'V_0' at the reference node '0' equals zero.
        """
        self.detector = detector
        self.checkDetector()
        return

    def checkDetector(self):
        """
        Checks if the detector has been defined and if it exists in the circuit.

        Called by **instruction.check()** and by **instruction.setDetector(<detector>)**.
        """
        if self.convType == "all":
            print("Error: Conversion type 'all' cannot automatically convert the detector to 'DM' or 'CM'. " +
                  "Use convtype=None instead.")
            self.errors += 1
        if self.detector != None:
            self.detLabel = ''
            # detector has two nodes or two voltage sources
            if type(self.detector) == str:
                # Change the detector definition
                self.detector = [self.detector, None]
            elif type(self.detector) == list:
                numDets = len(self.detector)
                if numDets == 0:
                    self.errors += 1
                    print("Error: missing detector specification")
                elif numDets == 1:
                    self.detector = [self.detector[0], None]
                elif numDets > 2:
                    self.errors += 1
                    print("Error: to many detectors.")
            if self.errors !=0:
                return
            detP = self.detector[0]
            detN = self.detector[1]
            if detP == None and detN == None:
                self.errors += 1
                print("Error: missing detector specification.")
            elif detP == detN:
                self.errors += 1
                print("Error: equal positive and negative detector.")
            elif detP == detN:
                self.errors += 1
                print("Error: two detectors must be of the same type.")

            if self.errors == 0 and self.convType == None:
                if detP != None and detP not in self.depVars():
                    self.errors += 1
                    print("Error: unkown detector: '{0}'.".format(detP))
                    print("Available detectors:", str(self.depVars()))
                elif detN != None and detN not in self.depVars():
                    self.errors += 1
                    print("Error: unkown detector: '{0}'.".format(detN))
                    print("Available detectors:", str(self.depVars()))

            if self.errors == 0 and self.lgRef != None:
                for lgRef in self.lgRef:
                    if lgRef != None:
                        # Impossible to calculate the asymptotic gain with these values
                        forbidden = 'I_i_' + lgRef
                        if detP == forbidden or detN == forbidden:
                            self.errors += 1
                            print("Error: forbidden combination of lgRef and detector.")
            if self.detector[0] != None:
                self.detUnits = detP[0].upper()
                self.detLabel += detP
            elif self.detector[1] != None:
                self.detUnits = detN[0].upper()
                self.detLabel += '-' + detN
            if self.detUnits == 'I':
                self.detUnits = 'A'
        else:
            self.errors += 1
            print("Error: missing detector definition.")
        return

    def setLGref(self, lgRef):
        """
        Defines the loop gain reference (name of a controlled source).

        A list with names of dependent (controlled) sources is returned by the
        method **instruction.controlled()**.

        :param lgRef: Name of the loop gain reference.
        :type lgRef: str, sympy.Symbol

        :Example:

        >>> # create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        >>> # Display a list with controlled sources of the circuit:
        >>> my_instr.controlled()
        """
        if type(lgRef) == str:
            self.lgRef = [lgRef, None]
            self.checkLGref()
        elif type(lgRef) == list and len(lgRef) == 2:
            self.lgRef = lgRef
            self.checkLGref()
        else:
            print("Error in loop gain reference specification.")
        return

    def checkLGref(self):
        """
        Checks if the loop gain reference has been defined and if it exists in
        the circuit.

        Called by **instruction.check()** and by **instruction.setLGref(<lgRef>)**.
        """
        if self.lgRef == [None, None]:
            self.errors += 1
            print("Error: missing loop gain reference definition.")
        for lgRef in self.lgRef:
            if lgRef != None and lgRef not in self.circuit.controlled:
                self.errors += 1
                print("Error: unkown loop gain reference: '{0}'.".format(self.lgRef))
        return

    def delPar(self, parName):
        """
        Deletes a parameter definition

        After deletion of the parameter from the instruction.circuit.parDefs
        dictionary the list **instruction.circuit.params** with
        names (*sympy.Symbol*) of undefined parameters is updated.

        :param parName: Name of the parameter.
        :type parName: str, sympy.Symbol

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Delete the definition for the parameter 'R':
        >>> my_instr.delPar('R')
        >>> # Or:
        >>> my_instr.circuit.delPar('R')
        """
        self.circuit.delPar(parName)
        return

    def defPar(self, parName, parValue):
        """
        Adds or modifies a parameter definition and updates the list
        **instruction.circuit.params** with names (*sympy.Symbol*) of undefined
        parameters.

        :param parName: Name of the parameter.
        :type parName: str, sympy.Symbol
        :param parValue: Value or expression.
        :type parName: str, sympy.Symbol, sympy.Expr

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Define the value of 'R' as 2000
        >>> my_instr.defPar('R', '2k')
        >>> # Or:
        >>> my_instr.defPar('R', 2e3)

        """
        self.circuit.defPar(str(parName), parValue)
        return

    def defPars(self, parDict):
        """
        Adds or modifies multiple parameter definitions and updates the list
        **instruction.circuit.params** with names (*sympy.Symbol*) of undefined
        parameters.

        :params parDict: Dictionary with key-value pairs:
                         key: parName (*str, sympy.Symbol*): name of the parameter.
                         value: parValue (*str, float, int, sp.Symbol*) : value
                         or expression of the parameter.
        :type parDict:   dict

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Define the value of 'R' as 2000 and 'C' as 5e-12:
        >>> my_instr.defPars({'R': '2k', 'C': '5p'})

        """
        # define multiple parameters.
        self.circuit.defPars(parDict)
        return

    def getParValue(self, parName):
        """
        Returns the value or expression of one or more parameters.

        If instruction.numeric == True it will perform a full recursive
        substitution of all circuit parameter definitions.

        This method calls instruction.circuit.getParValue() with keyword arg
        numeric = True if instruction.simType is set to 'numeric'.

        :param parName: name(s) of the parameter(s)
        :type parName: str, sympy.Symbol, list

        :return: if type(parNames) == list:

                 return value = dict with key-value pairs: key (*sympy.Symbol*):
                 name of the parameter, value (*int, float, sympy expression*):
                 value of the parameter

                 else:
                 value or expression

        :rtype: dict, float, int, sympy.Expr

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Obtain the numeric parameter definitions of of 'R' and 'C':
        >>> my_instr.symType = 'numeric'
        >>> my_instr.getParValue(['R', 'C'])
        """
        if self.simType == 'numeric':
            self.numeric = True
        else:
            self.numeric = False
        return self.circuit.getParValue(parName, self.numeric)

    def getElementValue(self, elementID, param = 'value'):
        """
        Returns the value or expression of one or more circuit elements.

        If instruction.numeric == True it will perform a full recursive
        substitution of all circuit parameter definitions.

        This method calls instruction.circuit.getElementValue() with
        numeric = True if instruction.simType is set to 'numeric'.

        :param elementID: name(s) of the element(s)
        :type elementID: str, list

        :param param: name of the parameter (equal for all elements):

                      - 'value': Laplace value
                      - 'dc': DC value (independent sources only)
                      - 'noise': Noise spectral density (independent sources only)
                      - 'dcvar': DC variance (independent sources only)

                      Defaults to 'value'.

        :type param: str

        :return: if type(param) == list:

                 return value = dict with key-value pairs: key (*sympy.Symbol*):
                 name of the parameter, value (*int, float, sympy expression*):
                 value of the parameter

                 else:
                 value or expression

        :rtype: dict, float, int, sympy.Expr

        :Example:

        >>> # Create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # Create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Obtain the numeric value of 'R1' and 'C1':
        >>> my_instr.symType = 'numeric'
        >>> print my_instr.getElementValue(['R1', 'C1'])
        {'C1': 5.0e-7/pi, 'R1': 1000.00000000000}
        """
        if self.simType == 'numeric':
            self.numeric = True
        else:
            self.numeric = False
        return self.circuit.getElementValue(elementID, param, self.numeric)

    def indepVars(self):
        """
        Returns a list with names of independent sources in **instruction.circuit**

        :return: list with names of independent sources in **instruction.circuit**
        :rtype: list

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Obtain a list with names of independent sources:
        >>> my_instr.indepVars()
        ['V1']
        """
        return self.circuit.indepVars

    def depVars(self):
        """
        Returns a list with names of nodal voltages and branch currents that can
        be used as detector.

        :return: list with names of nodal voltages and branch currents
        :rtype: list

        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Obtain a list with names of dependent variables:
        >>> my_instr.depVars()
        ['I_V1', 'V_N001', 'V_out']
        """
        depvars = []
        for var in self.circuit.dep_vars:
            if var != 'V_0':
                depvars.append(var)
        return depvars

    def controlled(self):
        """
        Returns a list with names of controlled sources in **instruction.circuit**
        that can be used as loop gain reference.

        :return: list with names of controlled sources in **instruction.circuit**
        :rtype: list
        :Example:

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Obtain a list with names of controlled sources:
        >>> my_instr.controlled()
        []
        """
        return self.circuit.controlled

    def setCircuit(self, fileName):
        """
        Defines the circuit for this instruction.

        - Checks the netlist file 'fileName'
        - Creates a circuit object from it
        - Makes it the ciruit object for this instruction.

        :param fileName: Name of the netlist file.
        :type fileName: str

        :Example:

        >>> # create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        """
        self.circuit = _checkCircuit(fileName)
        return

    def checkCircuit(self):
        """
        Checks if the circuit for this instruction is a :class:`SLiCAPprotos.circuit()` object.

        Called by **instruction.execute()**.
        """
        if self.circuit == None:
            self.errors += 1
            print("Error: missing circuit definition.")
        elif type(self.circuit.params) == dict:
            self.errors += 1
            print("Error: empty circuit object for this instruction.")
        elif type(self.circuit) != type(circuit()):
            self.errors += 1
            print("Error: not SLiCAP a circuit object for this instruction.")
        return

    def _checkNumeric(self):
        """
        Checks if the simulation type is set to 'numeric'. This is required for
        pole-zero analysis.

        Called by **instruction.check()** in cases in which a numeric
        simulation is required.
        """
        if not self.numeric:
            self.errors += 1
            print("Error: dataType '{0}' not available for simType: '{1}'.".format(self.dataType, self.simType))
        return

    def checkStep(self):
        """
        This method will check the completeness and the consistency of the
        instruction data for parameter stepping, before executing the
        instruction.

        Called by **instruction.check()** in cases in which
        instruction.step == True
        """
        self.checkStepMethod()
        if self.errors == 0:
            if not self.step:
                self.parDefs = self.circuit.parDefs
            elif self.stepMethod == 'lin':
                self.checkStepVar()
                self.checkStepNum()
                self.checkStepStart()
                self.checkStepStop()
                if self.errors == 0:
                    self.stepList = np.linspace(self.stepStart, self.stepStop, self.stepNum)
                    self.stepList = [sp.Rational(item) for item in self.stepList]
                    self.stepDict[self.stepVar] = self.stepList
            elif self.stepMethod == 'log':
                self.checkStepVar()
                self.checkStepNum()
                self.checkStepStart()
                self.checkStepStop()
                if self.errors == 0 and self.stepStart * self.stepStop > 0:
                    self.stepList = np.geomspace(self.stepStart, self.stepStop, self.stepNum)
                    self.stepList = [sp.Rational(item) for item in self.stepList]
                    self.stepDict[self.stepVar] = self.stepList
                else:
                    self.errors += 1
                    print("Error: logarithmic stepping cannot include zero.")
            elif self.stepMethod == 'list':
                self.checkStepVar()
                self.checkStepList()
                if self.errors == 0:
                    self.stepList = [sp.Rational(item) for item in self.stepList]
                    self.stepDict[self.stepVar] = self.stepList
            elif self.stepMethod == 'array':
                self.checkStepVars()
                # We need a list without errors before we can check the array
                if self.errors == 0:
                    self.checkStepArray()
                if self.errors == 0:
                    for i in range(len(self.stepVars)):
                        tmpLst = self.stepArray[i]
                        tmpLst = [sp.Rational(item) for item in tmpLst]
                        self.stepDict[self.stepVars[i]] = tmpLst
        return

    def check(self):
        """
        Checks the completeness and consistancy of the instruction data.
        Will be called by **instruction.execute()**.

        :Example:

        >>> # create an instance of the instruction object
        >>> my_instr = instruction()
        >>> # check a netlist file and use the circuit from this file for this
        >>> # instruction:
        >>> my_instr.setCircuit('my_circuit.cir')
        """
        self.errors = 0
        self.checkCircuit()
        if self.dataType != "matrix":
            if self.convType not in [None, "dd", "cc"]:
                self.errors += 1
                print("Error: conversion type '%s' can only be combined with doMatrix() (or instruction.dataType='matrix')."%(self.convType))
        if self.dataType == 'noise':
            # Noise sources of resistors add k and T to the circuit parameters
            # These sources should be added before executing the instruction.
            _delResNoiseSources(self)
            self.circuit = _updateCirData(self.circuit)
            self = _addResNoiseSources(self)
            self.circuit = _updateCirData(self.circuit)
        if self.dataType != 'params':
            self._checkGainType()
            self.checkDataType()
            if self.errors == 0:
                if self.gainType == 'vi':
                    if self.dataType == 'laplace':
                        # need detector
                        self.checkDetector()
                    elif self.dataType == 'noise':
                        # need detector
                        self.checkDetector()
                        # only needs a source for input noise analysis
                        self.checkSource(need = False)
                    elif self.dataType == 'matrix':
                        # need nothing
                        pass
                    elif self.dataType == 'solve':
                        # need nothing
                        pass
                    elif self.dataType == 'time':
                        # need detector
                        self.checkDetector()
                    elif self.dataType == 'dc':
                        # need detector
                        self.checkDetector()
                    elif self.dataType == 'dcvar':
                        # need detector
                        self.checkDetector()
                        self.checkSource(need = False)
                    elif self.dataType == 'dcsolve':
                        # need nothing
                        pass
                    elif self.dataType == 'timesolve':
                        # need nothing
                        pass
                    else:
                        self.errors += 1
                        print("Error: dataType '{0}' not available for gainType: '{1}'.".format(self.dataType, self.gainType))
                elif self.gainType != 'loopgain':
                    if self.dataType == 'matrix':
                        # need nothing
                        pass
                    elif self.dataType == 'laplace':
                        # need source and detector
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'dc':
                        # need source and detector
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'numer':
                        # need source and detector
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'denom':
                        # need nothing
                        pass
                    elif self.dataType == 'impulse':
                        # need source and detector
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'step':
                        # need source and detector
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'poles':
                        # need numeric
                        # self._checkNumeric()
                        pass
                    elif self.dataType == 'zeros':
                        # need numeric, source and detector
                        #self._checkNumeric()
                        self.checkDetector()
                        self.checkSource()
                    elif self.dataType == 'pz':
                        # need numeric source and detector
                        #self._checkNumeric()
                        self.checkDetector()
                        self.checkSource()
                    else:
                        self.errors += 1
                        print("Error: dataType '{0}' not available for gainType: '{1}'.".format(self.dataType, self.gainType))
                if self.gainType == 'asymptotic' or self.gainType == 'direct' or self.gainType == 'loopgain' or self.gainType == 'servo':
                    # need loop gain reference
                    self.checkLGref()
                else:
                    pass
        if self.convType != None:
            self._checkConvType()
            if self.pairExt != [None, None]:
                self.checkPairExt(self.pairExt)
        if self.step == True:
            if not self.numeric and self.dataType != 'params':
                self.errors += 1
                print("Error: symbolic stepping has not been implemented, use substitution instead.")
            elif self.dataType == 'matrix':
                self.errors += 1
                print("Error: parameter stepping with dataType 'matrix' has not been implemented.")
            else:
                # Check step parameters
                self.stepDict = {} # Clear the dictionary with step data
                self.checkStep()
        self.references = [ref for ref in self.circuit.references]
        return

    def execute(self):
        """
        Checks the instruction and executes it if no errors are found.

        if no errors are found it returns a :class:`allResults` object with the
        results of the instruction.

        :return: allResults object with results of the execution
        :rtype: SLiCAPprotos.allResults

        >>> # create an instance if a SLiCAP instruction
        >>> my_instr = instruction()
        >>> # create my_instr.circuit from the netlist 'myFirstRCnetwork.cir'
        >>> my_instr.setCircuit('myFirstRCnetwork.cir')
        >>> # Assign 'V1' signal source:
        >>> my_instr.source = 'V1'
        >>> # Assign 'V_out' detector:
        >>> my_instr.detector = 'V_out'
        >>> # Set the gain type to 'gain'
        >>> my_instr.gainType = 'gain'
        >>> # Set the data type to 'laplace'
        >>> my_instr.dataType = 'laplace'
        >>> result = my_instr.execute()
        >>> print result.laplace
        """
        self.check()
        return _doInstruction(self)


