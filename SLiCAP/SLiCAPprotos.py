#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with basic SLiCAP classes and functions.
"""

from sympy import N
import sys
import SLiCAP.SLiCAPconfigure as ini
from sympy import Symbol
from collections import namedtuple
from SLiCAP.SLiCAPmath import _checkExpression, fullSubs

class circuit(object):
    """
    Prototype (sub)circuit object.
    """
    def __init__(self):
        """
        Initialization of the circuit object, see description above.
        """
        self.title      = None
        """
        Title (*str*) of the circuit. Defautls to None.
        """

        self.file       = None
        """
        Name (*str*) of the netlist file. Defaults to None.
        """

        self.subCKT     = False
        """
        (*bool*) True if the circuit is a sub circuit. Defaults to False.
        """

        self.elements   = {}
        """
        (*dict*) with key-value pairs:

        - key: Reference designator (*str*) of the element.
        - value: Element object (*SLiCAPprotos.element*)
        """

        self.nodes      = []
        """
        (*list*) with names (*str*) of circuit nodes.
        """

        self.params     = {}
        """
        - If SLiCAPcircuit.subCKT == True:

          (*dict*) with key-value pairs:

          - key: Name (*sympy.core.symbol.Symbol*) of a parameter that can be passed to the
            sub circuit.
          - value: Default value (*sympy object*, float, int) of the parameter.

        - Else:

          - (*list*) with names (*sympy.core.symbol.Symbol*) of undefined parameters.
        """

        self.parDefs    = {}
        """
        (*dict*) with key-value pairs:

        - key: Name (*sympy.core.symbol.Symbol*) of a circuit parameter.
        - value: Value (*sympy object*, float, int) of the parameter.
        """

        self.parUnits   = {}
        """
        (*dict*) with key-value pairs:

        - key: Name (*sympy.core.symbol.Symbol*) of a circuit parameter.
        - value: Units (*str*) of the parameter.
        """

        self.modelDefs  = {}
        """
        (*dict*) with key-value pairs:

        - key: Name (*sympy.core.symbol.Symbol*) of a model.
        - value: Associated model object (*SLiCAPprotos.model*).
        """
        self.circuits   = {}
        """
        (*dict*) with key-value pairs:

        - key: Name (*str*) of a subcircuit.
        - value: Associated circuit object (*SLiCAPprotos.circuit*).
        """

        self.errors     = 0
        """
        Number (*int*) of errors found during checking of the circuit.
        Defaults to 0.
        """

        self.libs       = []
        """
        (*list*) with names (*str*) of library files found in netlist lines
        starting with ',lib' or '.inc'.
        """

        self.indepVars  = []
        """
        (*list*) with reference designators (*str*) of independent variables:

        - independent voltage sources
        - independent current sources.
        """

        self.dep_vars    = []
        """
        (*list*) with names (*str*) of independent variables:

        - nodal voltages:

          A nodal voltage will be named as: 'V_<node name>'. The reference node
          'V_0' is also listed, but it cannot be used as detector.
          use circuit.dep_vars() to obtain the list of valid detectors.

        - branch currents. Branch current will be named ad follows:

          - Current through a two-terminal element:

            - Vxxx: 'I_Vxxx'
            - Rxxx with model 'r': 'I_Rxxx'
            - Lxxx: 'I_Lxxx'

          - Currents through the input port or the output port of controlled
            sources:

            - Exxx output port: 'Io_Exxx'
            - Fxxx input port: 'Ii_Fxxx'
            - Gxxx, model = 'G', output port: 'Io_Gxxx'
            - Hxxx, input port: 'Ii_Hxxx', output port: 'Io_xxx'
        """

        self.controlled = []
        """
        (*list*) with reference designators (*str*) of controlled sources.
        """
        
        self.source = None
        """
        Signal source: None if not defined, or a list with two identifies of
        independent sources or one idenfifier and 'None'.
        """
        
        self.detector = None
        """
        Signal detector None if not defined, or a list with two names of
        dependent variales or one name and 'None'.
        """
        
        self.lgRef = None
        """
        Loopgain reference: None if not defined ,or a list with two identifies
        controlled sources or one idenfifier and 'None'.
        """     
    def depVars(self):
        """
        Returns the list with valid detectors.
        
        :return: list with valid detectors
        :rtype: list
        """
        depvars = []
        for name in self.dep_vars:
            if name != "V_0":
                depvars.append(name)
        return depvars
    
    def delPar(self, parName):
        """
        Deletes a parameter definition and updates the list
        **SLiCAPprotos.circuit.params** with names (*sympy.core.symbol.Symbol*) of
        undefined parameters.

        :param parName: Name of the parameter.
        :type parName: str, sympy.core.symbol.Symbol

        :return: None
        :rtype: NoneType
        """
        parName = Symbol(str(parName))
        if parName in self.parDefs.keys():
            self.parDefs.pop(Symbol(str(parName)), None)
        if parName in self.parUnits.keys():
            self.parUnits.pop(Symbol(str(parName)), None)
        self.updateParams()
        return

    def defPar(self, parName, parValue, units = None):
        """
        Updates or adds a parameter definition and updates the list
        **SLiCAPprotos.circuit.params** with names (*sympy.Symbol*) of
        undefined parameters.

        :param parName: Name of the parameter.
        :type parName: str, sympy.Symbol

        :param parValue: Value of the parameter.
        :type parValue: str, sympy.Symbol, sympy.Expr, int, float

        :param units: Value of the parameter, defaults to None
        :type units: str, sympy.Symbol
        
        :return: None
        :rtype: NoneType
        """
        errors = 0
        try:
            eval(parName)
            errors += 1
            print("Error: Parameter name cannot be a number.")
        except BaseException:
            pass
        if errors == 0:
            parName = Symbol(str(parName))
            self.parDefs[parName] = _checkExpression(parValue)
            if parName in self.params:
                self.params.remove(parName)
            if type(units) == str:
                # ToDo: checkUnits() calculate wir SI units.
                self.parUnits[parName] = units
            else:
                self.parUnits[parName] = ''
            self.updateParams()
        return

    def defPars(self, parDict):
        """
        Adds or modifies multiple parameter definitions and updates the list
        **circuit.params** with names (*sympy.Symbol*) of undefined parameters.

        :params parDict: Dictionary with key-value pairs:

                         - key: parName (*str, sympy.Symbol*): name of the
                           parameter.
                         - value: parValue (*str, float, int, sympy object*):
                           value or expression of the parameter.
                           
        :type parDict:   dict
        
        :return: None
        :rtype: None

        """
        errors = 0
        if type(parDict) == dict:
            for key in list(parDict.keys()):
                try:
                    eval(key)
                    print("Error: parameter name cannot be a number.")
                    errors += 1
                except BaseException:
                    pass
                if errors == 0:
                    parName = Symbol(str(key))
                    parValue = str(parDict[key])
                    self.parDefs[parName] = _checkExpression(parValue)
                    if parName in self.params:
                        self.params.remove(parName)
                else:
                    print("Error: cannot define a number as parameter.")
        else:
            print("Error: expected a dict type argument.")
        self.updateParams()
        return

    def getParValue(self, parNames, substitute=True, numeric=False):
        """
        Returns the value or expression of one or more parameters.

        If substitute == True, recursive substitution of all circuit parameters
        will be applied.
        
        If numeric == True, numeric values of functions wand constants will be 
        evaluated and converted to sympy.Floats
        
        :param parNames: name(s) of the parameter(s)
        :type parNames: str, sympy.Symbol, list
        
        :param substitute: - True: circuit parameters will be recursively 
                             substituted
                           - False: Parameter values or expressions will be 
                             returned as defined
                             
                           Defaults to True
                             
        :type substitute: Bool
                             
        :param numeric: - True: Numeric values of functions and constants will
                          be evaluated and rational numbers will be converted 
                          to sympy.Float
                        - False: No numeric evaluation of functions and 
                          constants
                          
                        Defaults to False
                        
        :type numeric: Bool
            
        :return: - If type(parNames) == list: a dict with key-value pairs:

                   - key (sympy.Symbol): name of the parameter
                   - value (sympy.Float, sympy.Expr): value of the parameter

                 - Else: value or expression (sympy.Float or sympy.Expr).

        :rtype: dict, sympy.Float, sympy.Expr

        """
        if type(parNames) == list:
            parValues = {}
            for par in parNames:
                par = Symbol(str(par))
                for key in list(self.parDefs.keys()):
                    if par == key:
                        if substitute == True:
                            parValues[par] = fullSubs(self.parDefs[key], self.parDefs)
                        else:
                           parValues[par] = self.parDefs[key]
                        if numeric:
                            parValues[par] = N(parValues[par])
        else:
            parName = Symbol(str(parNames))
            parValues = None
            try:
                if substitute:
                    parValues = fullSubs(self.parDefs[parName], self.parDefs)
                else:
                    parValues = self.parDefs[parName]
                if numeric:
                    parValues = N(parValues)
            except BaseException:
                exc_type, value, exc_traceback = sys.exc_info()
                print('\n', value)
                print("Error: parameter '{0}' has not been defined.".format(str(parName)))
        return parValues

    def updateParams(self):
        """
        Updates self.params (list with undefined parameters) after modification
        of parameter definitions in self.parDefs.
        """
        self.params =[]
        # Get all the parameters used in element values
        for elmt in list(self.elements.keys()):
            for par in list(self.elements[elmt].params.keys()):
                try:
                    self.params += list(self.elements[elmt].params[par].atoms(Symbol))
                except BaseException:
                    pass
        # Get all the parameters used in parameter definitions
        for par in list(self.parDefs.keys()):
            try:
                self.params += list(self.parDefs[par].atoms(Symbol))
            except BaseException:
                pass
        # Remove duplicates
        self.params = list(set(self.params))
        undefined = []
        # If these parameters are not found in parDefs.keys, they are undefined.
        for par in self.params:
            if par != ini.laplace and par != ini.hz and par not in list(self.parDefs.keys()):
                undefined.append(par)
        self.params = undefined
        return

    def getElementValue(self, elementID, param='value', substitute=True, numeric=False):
        """
        Returns the value or expression of one or more circuit elements.

        If instruction.numeric == True it will perform a full recursive
        substitution of all circuit parameter definitions.

        This method is called by instruction.circuit.getElementValue() with
        keyword arg numeric = True if instruction.simType is set to 'numeric'.

        :param elementID: name(s) of the element(s)
        :type elementID: str, list

        :param param: name of the parameter (equal for all elements):

                      - 'value': Laplace value
                      - 'dc': DC value (independent sources only)
                      - 'noise': Noise spectral density (independent sources only)
                      - 'dcvar': DC variance (independent sources only)
                      
                      Defaults to 'value'

        :type param: str

        :param substitute: - True: circuit parameters will be recursively 
                             substituted
                           - False: Element values or expressions will be 
                             returned as defined
                             
                           Defaults to True
                             
        :type substitute: Bool
                             
        :param numeric: - True: Numeric values of functions and constants will
                          be evaluated and rational numbers will be converted 
                          to sympy.Float.
                        - False: No numeric evaluation of functions and 
                          constants
                          
                        Defaults to False
                        
        :type numeric: Bool
        
        :return: if type(parNames) == list:

                 return value = dict with key-value pairs: key (*sympy.core.symbol.Symbol*):
                 name of the parameter, value (*int, float, sympy expression*):
                 value of the parameter

                 else:
                 value or expression

        :rtype: dict, sympy.Float, sympy.Expr

        """
        if type(elementID) == list:
            elementValues = {}
            for elID in elementID:
                if elID in list(self.elements.keys()):
                    if param in list(self.elements[elID].params.keys()):
                        value = self.elements[elID].params[param]
                        if substitute:
                            value = fullSubs(value, self.parDefs)
                        if numeric:
                            value = N(value)
                        elementValues[elID] = value
                    else:
                        print("Error: Parameter '{0}' undefined for element '{1}'.".format(param, elID))
                else:
                    print("Error: Unknown circuit element '{0}'.".format(elID))
        else:
            elementValues = None
            if elementID in list(self.elements.keys()):
                if param in list(self.elements[elementID].params.keys()):
                    value = self.elements[elementID].params[param]
                    if substitute:
                        value = fullSubs(value, self.parDefs)
                    if numeric:
                        value = N(value)
                    elementValues = value
                else:
                    print("Error: Parameter '{0}' undefined for element '{1}'.".format(param, elementID))
            else:
                print("Error: Unknown circuit element '{0}'.".format(elementID))
        return elementValues

class element(object):
    """
    Prototype circuit element object.
    """
    def __init__(self):
        self.refDes     = ''
        """
        Element reference designator (*str*), defaults to ''.
        """

        self.type       = ''
        """
        Element type: First letter of refdes (*str*).
        """

        self.nodes      = []
        """
        (*list*) with names (*str*) of the nodes to which the element is
        connected.
        """

        self.refs       = []
        """
        (*list*) with reference designators of elements (*str*) that are
        referenced to by the element.
        """

        self.params     = {}
        """
        (*dict*) with key-value pairs:

        - key (*sympy.core.symbol.Symbol*): Name of an element parameter.
        - value (*sympy object*, float, int): Value of the parameter.
        """
        self.model      = ''
        """
        Name (*str*) of the model of the element.
        """

class modelDef(object):
    """
    Protpotype for model definitions that can be added to SLiCAP.
    """
    def __init__(self):
        
        self.name       = ''
        """
        Name (*str*) of the model.
        """
        self.type       = ''
        """
        Name (*str*) of the built-in model type that should be used for this
        model.
        """

        self.params     = {}
        """
        (*dict*) with key-value pairs:

        - key (*str*): Model parameter name
        - value (*sympy object*, float, int): Value or expression
        """
    
def _initAll():
    """
    Creates the SLiCAP built-in models and devices.
    """
    MODELS      = {}                # Dictionary with SLiCAP built-in models
                                    #   key   : model name
                                    #   value : associated model object
    DEVICES     = {}                # Dictionary with SLiCAP built-in devices
                                    #   key   : device name
                                    #   value : associated device object
    # Generate the dictionary with SLiCAP models
    model    = namedtuple('model', ['name', 'stamp', 'depVars', 'params'])
    
    MODELS['C']  = model('C', True, [], {'value': False, 'vinit': False})
    MODELS['D']  = model('D', False, [], {'rs': False, 'cd': False, 'gd': False})
    MODELS['E']  = model('E', True, ['Io'], {'value': True})
    MODELS['EZ'] = model('EZ', True, ['Io'], {'value': True, 'zo': True})
    MODELS['F']  = model('F', True, ['Ii'], {'value': True})
    MODELS['G']  = model('G', True, ['Io'], {'value': True})
    MODELS['g']  = model('g', True, [], {'value': False})
    MODELS['H']  = model('H', True, ['Io', 'Ii'], {'value': True})
    MODELS['HZ'] = model('HZ', True, ['Io', 'Ii'], {'value': True, 'zo': True})
    MODELS['I']  = model('I', True, [], {'value': True, 'dc': False, 'dcvar': False, 'noise': False})
    MODELS['J']  = model('J', False, [], {'cgs': False, 'cdg': False, 'gm': False, 'go': False})
    MODELS['K']  = model('K', True, [], {'value': False})
    MODELS['L']  = model('L', True, ['I'], {'value': False, 'iinit': False})
    MODELS['M']  = model('M', False, [], {'cgs': False, 'cdg': False, 'cdb': False, 'csb': False, 'cgb': False, 'gm': False, 'gb': False, 'go': False})
    MODELS['MD'] = model('MD', False, [], {'cgg': False, 'cdg': False, 'cdd': False, 'gm': False, 'go': False})
    MODELS['N']  = model('N', True, ['Io'], {})
    MODELS['OC'] = model('OC', False, [], {'cp': False, 'gp': False, 'cpn': False, 'gpn': False, 'gm': False, 'zt': True, 'zo': True})
    MODELS['OV'] = model('OV', False, [], {'cd': False, 'cc': False, 'gd': False, 'gc': False, 'av': True, 'zo': True})
    MODELS['QL'] = model('QL', False, [], {'cpi': False, 'cbc': False, 'cbx': False, 'cs': False, 'gpi': False, 'gm': False, 'gbc': False, 'go': False, 'rb': False})
    MODELS['QV'] = model('QV', False, [], {'cpi': False, 'cbc': False, 'cbx': False, 'cs': False, 'gpi': False, 'gm': False, 'gbc': False, 'go': False, 'rb': False})
    MODELS['QD'] = model('QD', False, [], {'cbb': False, 'cbc': False, 'gbb': False, 'gm': False, 'gcc': False, 'gbc': False, 'rb': False})
    MODELS['R']  = model('R', True, [], {'value': False, 'dcvar': False, 'noisetemp': False, 'noiseflow' :False, 'dcvarlot': False})
    MODELS['r']  = model('r', True, ['I'], {'value': False, 'dcvar': False, 'noisetemp': False, 'noiseflow' :False, 'dcvarlot': False})
    MODELS['T']  = model('T', True, ['Io'], {'value': False})
    MODELS['V']  = model('V', True, ['I'], {'value': True, 'dc': False, 'dcvar': False, 'noise': False})
    MODELS['W']  = model('W', True, [], {'value': False})

    # Generate the dictionary with SLiCAP devices
    device   = namedtuple('device', ['ID', 'nNodes', 'nRefs', 'value', 'models'])
    
    DEVICES['C'] = device('C', 2, 0, True, ['C'])
    DEVICES['D'] = device('D', 2, 0, True, ['D'])
    DEVICES['E'] = device('E', 4, 0, True, ['E', 'EZ'])
    DEVICES['F'] = device('F', 4, 0, True, ['F'])
    DEVICES['G'] = device('G', 4, 0, True, ['G', 'g'])
    DEVICES['H'] = device('H', 4, 0, True, ['H', 'HZ'])
    DEVICES['I'] = device('I', 2, 0, True, ['I'])
    DEVICES['J'] = device('J', 3, 0, True, ['J'])
    DEVICES['K'] = device('K', 0, 2, True, ['K'])
    DEVICES['L'] = device('L', 2, 0, True, ['L'])
    DEVICES['M'] = device('M', 4, 0, True, ['M', 'MD'])
    DEVICES['N'] = device('N', 4, 0, None, ['N'])
    DEVICES['O'] = device('O', 4, 0, True, ['OC', 'OV'])
    DEVICES['Q'] = device('Q', 4, 0, True, ['QV', 'QD', 'QL'])
    DEVICES['R'] = device('R', 2, 0, True, ['R', 'r'])
    DEVICES['T'] = device('T', 4, 0, True, ['T'])
    DEVICES['V'] = device('V', 2, 0, True, ['V'])
    DEVICES['W'] = device('W', 4, 0, True, ['W'])
    DEVICES['X'] = device('X', -1, 0, None, ['F'])   
    return MODELS, DEVICES

class allResults(object):
    """
    Return  structure for results, has attributes with
    instruction data and execution results.
    """
    def __init__(self):
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

        # Instruction settings

        self.gainType = None
        """
        Defines the simulation gain type.

        Will be copied from the instruction at the start of its execution.
        """

        self.convType = None
        """
        Defines the circuit conversion type.

        Will be copied from the instruction at the start of ts execution.
        """

        self.dataType = None
        """
        Defines the simulation data type.

        Will be copied from the instruction at the start of its execution.
        """

        self.step = None
        """
        Setting for parameter stepping.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepVar = None
        """
        Defines the step variable (*str*) for step types 'lin', 'log' and 'list'.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepVars = None
        """
        Defines the step variables for 'array' type parameter stepping.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepMethod = None
        """
        Step method for parameter stepping.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepStart = None
        """
        Start value for stepping methods 'lin' and 'log'.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepStop = None
        """
        Stop value for stepping methods 'lin' and 'log'.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepNum = None
        """
        Number of steps for step methods 'lin' and 'log'.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepList = []
        """
        List with values for step method 'list'.

        Will be copied from the instruction at the start of its execution.
        """

        self.stepArray = []
        """
        Array (*list of lists*) with values for step method array.

        Will be copied from the instruction at the start of its execution.
        """

        self.source = None
        """
        Refdes of the signal source (independent v or i source).

        Will be copied from the instruction at the start of its execution.
        """

        self.detector = None
        """
        Names of the positive and negative detector.

        Will be copied from the instruction at the start of its execution.
        """

        self.lgRef = None
        """
        Refdes of the controlled source that is assigned as loop gain reference.

        Will be copied from the instruction at the start of its execution.
        """

        self.numeric = None
        """
        If True, functions and constants will be evaluated numerically and
        rational numbers will be converted in sympy.Float 
        """

        self.substitute = None
        """
        If True: parameters from self.circuit will be substituted recursively
        in element values. 
        
        Else: element values defined in the circuit will be used
        """
        
        self.errors = 0
        """
        Number of errors found in the definition of this instruction.

        Will be copied from the instruction at the start of its execution.
        """

        self.detUnits = None
        """
        Detector units 'V' or 'A'.

        Will be copied from the instruction at the start of its execution.
        """

        self.srcUnits = None
        """
        Source units 'V' or 'A'.

        Will be copied from the instruction at the start of its execution.
        """

        self.detLabel = None
        """
        Name for the detector quantity to be used in expressions or plots.

        Will be generated by the instruction at the start of its execution.
        """

        self.label = ''
        """
        Label to be used in plots.
        """

        self.parDefs = None
        """
        Parameter definitions for the instruction.

        Will be copied from  the instruction at the start of its execution. 
        """
        self.pairedVars   = None
        """
        Extension of paired nodes and branches for base transformation of the 
        circuit.

        Will be copied from the instruction at the start of its execution.
        """
        self.pairedCircuits = None
        """
        Identifiers of paired subcircuits for base transformation of the 
        circuit.

        Will be copied from the instruction at the start of its execution.
        """
        self.removePairSubName = False
        """
        Setting for changing the parameter names of paired subcircuits.

        Will be copied from the instruction at the start of its execution.
        """

    def depVars(self):
        """
        Returns the list of detecors available AFTER execution of an 
        instruction.
        """
        return [str(var) for var in self.Dv]
    
_MODELS, _DEVICES = _initAll()