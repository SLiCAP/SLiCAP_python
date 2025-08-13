#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SLiCAP multi-pass netlist parser:

pass 1: The netlist is converted into a nested circuit object (mainCircuit)
        
- mainCircuit.elements:
  list with element objects from element definition lines
- mainCircuit.modelDefs:
  dictionary with modelDef objects from .model definition lines:
  key   = model name (str)
  value = modelDef object for this model
- mainCircuit.parDefs   parDef objects from .param definition lines:
  dictionary with parameters:
  key   = parameter name (str)
  value = sympy object (Symbol, Expression, Integer, Float)
- mainCircuit.libs:
  list with file names (str) from .include and .lib lines
- (sub)circuit definitions:
  dictionary with circuit objects:
  key   = subcircuit name
  value = circuit object, as the main object, but with nodes and 
  parameters that can be passed.

pass 2: Checks and completes the data of the nested circuits object:
            
- check if referenced elements exist in the circuit
- check if library files exist
- create modelDef objects from the libraries
- create (sub)circuit objects from the libraries

pass 3: Flattens the netlist: the nested circuit is converted into one circuit.

pass 4: Generates/updates the instructions data, such as available sources,
detectors and loop gain references
"""

import os
import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from copy import deepcopy
from SLiCAP.SLiCAPhtml import htmlPage
from SLiCAP.SLiCAPlex import _tokenize, _printError
from SLiCAP.SLiCAPprotos import _MODELS, _DEVICES, circuit, element, modelDef
from SLiCAP.SLiCAPmath import fullSubs

# Composite tokens
_NODES           = ['NODEID', 'ID', 'INT']
_VALEXPR         = ['FLT', 'EXPR', 'SCI', 'INT']
_TITLE           = ['ID', 'QSTRING', 'FNAME']

# Lists with constrolled and independent sources
_CONTROLLED      = ['E', 'F', 'G', 'H']  # Controlled sources
_INDEPSCRCS      = ['I', 'V']            # Independent sources

# list with (sub)circuit names for checking hierarchy
# last name is current circuit during hierarchical checking
_CIRCUITNAMES    = []

# Dictionary with (sub)circuit definitions, keys are from CIRCUITNAMES,
# values are circuit objects.
_CIRCUITS        = {}

# List with SLiCAP device types
_DEVICETYPES     = list(_DEVICES.keys())

# List with default SLiCAP libraries
_SLiCAPLIBS      = ['SLiCAP.lib', 'SLiCAPmodels.lib']

# SLiCAP built-in models
_SLiCAPMODELS    = {}

# SLiCAP global parameters
_SLiCAPPARAMS    = {}

# SLiCAP built-in subcircuits
_SLiCAPCIRCUITS  = {}

# User include files and library files
_USERLIBS        = []

# User defined models from library files
_USERMODELS      = {}

# User defined circuit from library files
_USERCIRCUITS    = {}

# User defined global parameters from library files
_USERPARAMS      = {}

def _initializeParser():
    global _CIRCUITNAMES, _CIRCUITS, _SLiCAPMODELS, _SLiCAPPARAMS
    global _SLiCAPCIRCUITS, _USERLIBS, _USERMODELS, _USERCIRCUITS, _USERPARAMS
    
    _CIRCUITNAMES    = []
    _CIRCUITS        = {}
    _SLiCAPMODELS    = {}
    _SLiCAPPARAMS    = {}
    _SLiCAPCIRCUITS  = {}
    _USERLIBS        = []
    _USERMODELS      = {}
    _USERCIRCUITS    = {}
    _USERPARAMS      = {}
    _makeLibraries()
    
def _resetParser():
    global _CIRCUITNAMES, _CIRCUITS, _USERCIRCUITS, _USERPARAMS, _USERLIBS, _USERMODELS

    _CIRCUITNAMES    = []
    _CIRCUITS        = {}
    _USERLIBS        = []
    _USERMODELS      = {}
    _USERCIRCUITS    = {}
    _USERPARAMS      = {}
    
def _compileSLiCAPLibraries():
    """
    Compiles the SLiCAP bult-in libraries and writes the subcircuit, models,
    and global parameters to SLiCAPCIRCUITS, SLiCAPMODELS, and SLiCAPPARAMS,
    respectively.

    :return: None
    :rtype: NoneType
    """
    global _SLiCAPCIRCUITS, _SLiCAPMODELS, _SLiCAPPARAMS
    for fi in _SLiCAPLIBS:
        print("Compiling library: " + fi + ".")
        f = open(ini.main_lib_path + fi, 'r')
        netlist = f.read()
        f.close()
        cirName  = fi.split('.')[0]
        _parseNetlist(netlist, cirName, 'system')
        for model in _SLiCAPCIRCUITS[cirName].modelDefs.keys():
            _SLiCAPMODELS[model] = _SLiCAPCIRCUITS[cirName].modelDefs[model]
        for param in _SLiCAPCIRCUITS[cirName].parDefs.keys():
            _SLiCAPPARAMS[param] = _SLiCAPCIRCUITS[cirName].parDefs[param]
        del _SLiCAPCIRCUITS[cirName]
    # PASS 2 and 3
    for cir in _SLiCAPCIRCUITS.keys():
        _checkReferences(_SLiCAPCIRCUITS[cir])
        _expandCircuit(_SLiCAPCIRCUITS[cir])
    ini.SLiCAPPARAMS = _SLiCAPPARAMS

def _compileUSERLibrary(fileName):
    """
    Parses a user library file and writes the subcircuit, models,
    and global parameters to USERCIRCUITS, USERPMODELS, and USERPARAMS,
    respectively.

    :param fileName: Path of the library file

    :type fileName: str

    :return: None
    :rtype: NoneType
    """
    global _USERCIRCUITS, _USERPARAMS, _USERMODELS
    print("Compiling library: " + fileName + ".")
    f = open(fileName, 'r')
    netlist = f.read()
    f.close()
    cirName = netlist.splitlines()[0][0:-1].replace(" ", "_")
    _parseNetlist(netlist, cirName, 'user')
    for model in _USERCIRCUITS[cirName].modelDefs.keys():
        _USERMODELS[model] = _USERCIRCUITS[cirName].modelDefs[model]
    for param in _USERCIRCUITS[cirName].parDefs.keys():
        _USERPARAMS[param] = _USERCIRCUITS[cirName].parDefs[param]
    del _USERCIRCUITS[cirName]
    # PASS 2 and 3
    for cir in _USERCIRCUITS.keys():
        _checkReferences(_USERCIRCUITS[cir])

def _parseNetlist(netlist, name, cirType):
    """
    Netlist parser: converts a netlist to the active circuit object.
    The name of the active circuit object is the last name in the global
    _CIRCUITNAMES: _CIRCUITNAMES[-1]. The circuit object itself is stored in a
    dictionary that depends on the variable cirType.

    :param netlist: Netlist of the circuit
    :type netlist: String

    :param name: Name of the (sub)circuit, defaults to 'main'
    :type name: String (no whitespace characters)

    :param cirType: pointer to the dictionary to which the circuit elements 
                    and commands will be written.
    :type cirType: str

    :return: None

    :rtype: Nonetype
    """
    global _CIRCUITNAMES
    _CIRCUITNAMES.append(name)
    _createCircuit(name, cirType)
    lines, errors = _tokenize(netlist)
    if errors == 0:
        if name == 'main' and lines[0][0].type in _TITLE:
            title = lines[0][0].value
            if lines[0][0].type == 'QSTRING':
                # Remove the double quotes, this conflicts with HTML files
                title = title[1:-1]
            _addTitle(name, cirType, title)
        lines = lines[1:]
        for line in lines:
            #print("NAMES:", _CIRCUITNAMES, name, cirType, list(_CIRCUITS.keys()))
            if line[0].type == "ID":
                deviceType = line[0].value[0].upper()
                if deviceType != 'X':
                    _parseElement(line, name, cirType)
                else:
                    _parseSubcircuitElement(line, name, cirType)
            elif line[0].type == "CMD":
                cmdType = line[0].value.upper()
                if cmdType == "SUBCKT":
                    if len(line) > 1:
                        if line[1].type == "ID":
                            cirName = line[1].value
                            if cirName not in _CIRCUITNAMES:
                                _createSubCKT(line, cirName, cirType)
                                _CIRCUITNAMES.append(cirName)
                                name = cirName
                            else:
                                _printError("Error: Hierarchical loop involving '" + line[1].value + "'.", line[1])
                                _addErrors(name, cirType, 1)
                        else:
                           _printError("Error: Expected a circuit title.", line[1])
                           _addErrors(name, cirType, 1)
                    else:
                        _printError("Error: Missing circuit title", line[0])
                        _addErrors(name, cirType)
                elif cmdType == "SOURCE":
                    source = None
                    if len(line) > 2:
                        source = [line[1].value, line[2].value]
                    elif len(line) > 1:
                        source = [line[1].value, None]
                    else:
                        _printError("Error: Missing source definition", line[0])
                        _addErrors(name, cirType)
                    _addSource(name, cirType, source)
                elif cmdType == "DETECTOR":
                    detector = None
                    if len(line) > 2:
                        detector = [line[1].value, line[2].value]
                    elif len(line) > 1:
                        detector = [line[1].value, None]
                    else:
                        _printError("Error: Missing detector definition", line[0])
                        _addErrors(name, cirType)
                    _addDetector(name, cirType, detector)
                elif cmdType == "LGREF":
                    lgRef = None
                    if len(line) > 2:
                        lgRef = [line[1].value, line[2].value]
                    elif len(line) > 1:
                        lgRef = [line[1].value, None]
                    else:
                        _printError("Error: Missing lgRef definition", line[0])
                        _addErrors(name, cirType)
                    _addLGref(name, cirType, lgRef)
                elif cmdType == "DETECTOR":
                    pass
                elif cmdType == "ENDS":
                    del _CIRCUITNAMES[-1]
                    name = _CIRCUITNAMES[-1]
                elif cmdType == "END":
                    del _CIRCUITNAMES[-1]
                else:
                    _parseCommand(line, name, cirType)
    else:
        _addErrors(name, cirType, errors)
        if name != 'main':
            print("Error: something wring with circuit hierachy, probably missing '.ends'. in a subcircuit definition.")
    return

def _createCircuit(name, cirType):
    newCircuit = circuit()
    _saveCircuit(newCircuit, name, cirType)
    
def _addTitle(name, cirType, title):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if cirType == 'system':
        _SLiCAPCIRCUITS[name].title = title
    elif cirType == 'user':
        _USERCIRCUITS[name].title = title
    elif cirType == 'main':
        _CIRCUITS[name].title = title
    
def _createSubCKT(line, name, cirType):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    nodes  = []
    params = {}
    errors = 0
    for i in range(2, len(line)):
        if line[i].type in _NODES:
            nodes.append(line[i].value)
        elif line[i].type == "PARDEF":
            parName, parValue = line[i].value
            params[parName] = parValue
        else:
            _printError("Error: Unexpected input.", line[i])
            errors += 1
    subCKT = circuit()
    subCKT.title  = name
    subCKT.nodes  = nodes
    subCKT.params = params
    subCKT.errors += errors
    _saveCircuit(subCKT, name, cirType)
    
def _addErrors(name, cirType, n):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if cirType == 'system':
        _SLiCAPCIRCUITS[name].errors += n
    elif cirType == 'user':
        _USERCIRCUITS[name].errors += n
    elif cirType == 'main':
        _CIRCUITS[name].errors += n
    
def _saveCircuit(cir, name, cirType):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if cirType == 'system':
        _SLiCAPCIRCUITS[name] = cir
    elif cirType == 'user':
        _USERCIRCUITS[name] = cir
    elif cirType == 'main':
        _CIRCUITS[name] = cir
        
def _addElement(el, name, cirType):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if cirType == 'system':
        _SLiCAPCIRCUITS[name].elements[el.refDes] = el
    elif cirType == 'user':
        _USERCIRCUITS[name].elements[el.refDes] = el
    elif cirType == 'main':
        _CIRCUITS[name].elements[el.refDes] = el
        
def _addModel(name, cirType, model):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if model != None:
        if cirType == 'system':
            _SLiCAPCIRCUITS[name].modelDefs[model.name] = model
        elif cirType == 'user':
            _USERCIRCUITS[name].modelDefs[model.name] = model
        elif cirType == 'main':
            _CIRCUITS[name].modelDefs[model.name] = model
            
def _addParDef(name, cirType, parDefs):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if parDefs != None:
        if cirType == 'system':
            for key in parDefs.keys():
                _SLiCAPCIRCUITS[name].parDefs[key] = parDefs[key]
        elif cirType == 'user':
            for key in parDefs.keys():
                _USERCIRCUITS[name].parDefs[key] = parDefs[key]
        elif cirType == 'main':
            for key in parDefs.keys():
                _CIRCUITS[name].parDefs[key] = parDefs[key]
            
def _addSource(name, cirType, source):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if source != None:
        if cirType == 'system':
            _SLiCAPCIRCUITS[name].source = source
        elif cirType == 'user':
            _USERCIRCUITS[name].source = source
        elif cirType == 'main':
            _CIRCUITS[name].source = source
            
def _addDetector(name, cirType, detector):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if detector != None:
        if cirType == 'system':
            _SLiCAPCIRCUITS[name].detector = detector
        elif cirType == 'user':
            _USERCIRCUITS[name].detector = detector
        elif cirType == 'main':
            _CIRCUITS[name].detector = detector

def _addLGref(name, cirType, lgRef):
    global _CIRCUITS, _USERCIRCUITS, _SLiCAPCIRCUITS
    if lgRef != None:
        if cirType == 'system':
            _SLiCAPCIRCUITS[name].lgRef= lgRef
        elif cirType == 'user':
            _USERCIRCUITS[name].lgRef= lgRef
        elif cirType == 'main':
            _CIRCUITS[name].lgRef= lgRef


def _parseElement(line, name, cirType):
    """
    Parsing of an element line to the active circuit object.
    The name of the active circuit object is the last name in the global
    CIRCUITNAMES: CIRCUITNAMES[-1]. The circuit object itself is stored in the
    dictionary CIRCUITS under this name: circuitDict[CIRCUITNAMES[-1]].

    :param line: list with tokens from a netlist line
    :type line: list with tokens

    :param circuitDict: Dictionary to which the definition will be written
    :type circuitDict: dictionary

    :return: Errors: number of errors found in this line.

    :rtype: Integer
    """
    global _CIRCUITNAMES
    newElement = element()
    deviceType = line[0].value[0].upper()
    errors = 0
    if deviceType in _DEVICETYPES:
        newElement.type = deviceType
        newElement.refDes =  line[0].value
        nNodes = _DEVICES[deviceType].nNodes
        nRefs = _DEVICES[deviceType].nRefs
        nFields = 1 + nNodes + nRefs
        if _DEVICES[deviceType].value == True:
            nFields += 1
        if len(line) < nFields:
            _printError("Error: incomplete element specification.", line[-1])
            errors += 1
        else:
            for i in range(nNodes):
                pos = 1 + i
                if line[pos].type in _NODES:
                    newElement.nodes.append(line[pos].value)
                else:
                    _printError("Error: syntax error in node ID", line[pos])
                    errors += 1
            for i in range(_DEVICES[deviceType].nRefs):
                pos = 1 + nNodes + i
                if line[pos].type == "ID":
                    newElement.refs.append(line[pos].value)
                else:
                    _printError("Error: syntax error in device ID", line[pos])
                    errors += 1
            pos = 1 + nNodes + nRefs
            if _DEVICES[deviceType].value:
                if line[pos].type == "ID":
                    newElement.model = line[pos].value
                elif line[pos].type in _VALEXPR:
                    newElement.model = _DEVICES[deviceType].models[0]
                    if line[pos].type == 'EXPR':
                        newElement.params['value'] = line[pos].value
                        if newElement.model in _MODELS.keys():
                            if not _MODELS[newElement.model].params['value'] and ini.laplace in newElement.params['value'].atoms(sp.Symbol):
                                _printError("Error: Laplace variable not allowed in this expression.", line[pos])
                    else:
                        newElement.params['value'] = sp.Rational(str(line[pos].value))
                elif line[pos].type == "PARDEF":
                    _printError("Error: missing model definition", line[pos])
                    errors += 1
                else:
                    _printError("Error: syntax error in model definition", line[pos])
                    errors += 1
                for i in range(len(line) - nFields):
                    pos = nFields + i
                    if line[pos].type == "PARDEF":
                        key, value = line[pos].value
                        newElement.params[key] = value
                        if newElement.model in _MODELS.keys():
                            if key in _MODELS[newElement.model].params.keys():
                                if not _MODELS[newElement.model].params[key] and ini.laplace in value.atoms(sp.Symbol):
                                    _printError("Error: Laplace variable not allowed in this expression.", line[pos])
                            else:
                                _printError("Error: unknown model parameter", line[pos])
                    else:
                        _printError("Error: expected a parameter definition.", line[pos])
                        errors += 1
    else:
        _printError("Error: unknown element.", line[-1])
        errors += 1
    if errors == 0:
        _addElement(newElement, name, cirType)

def _parseSubcircuitElement(line, name, cirType):
    """
    Parsing of a subcircuit call (an X element) in the netlist in the active
    circuit object.
    The name of the active circuit object is the last name in the global
    CIRCUITNAMES: CIRCUITNAMES[-1]. The circuit object itself is stored in the
    dictionary CIRCUITS under this name: circuitDict[CIRCUITNAMES[-1]].

    :param line: list with tokens from a netlist line
    :type line: list with tokens

    :param circuitDict: Dictionary to which the definition will be written,
                        defaults to CIRCUITS.
    :type circuitDict: dictionary

    :return: Errors: number of errors found in this line.

    :rtype: Integer
    """
    global _CIRCUITNAMES
    errors = 0
    # Check if there are parameter definitions
    for modelPos in range(len(line)):
        if line[modelPos].type == "PARDEF":
            modelPos -= 1
            break
    newElement = element()
    newElement.refDes = line[0].value
    newElement.type = 'X'
    newElement.model = line[modelPos].value
    for i in range(1, modelPos):
        if line[i].type in _NODES:
            newElement.nodes.append(line[i].value)
        else:
            errors += 1
            _printError("Error: Expected a node ID.", line[i])
    if len(line) > modelPos + 1:
        for i in range(modelPos + 1, len(line)):
            if line[i].type == "PARDEF":
                key, value = line[i].value
                newElement.params[key] = value
            else:
                errors += 1
                _printError("Error: Expected a parameter definition.", line[i])
    if errors == 0:
        _addElement(newElement, name, cirType)

def _parseCommand(line, name, cirType):
    """
    Parsing of a command the netlist to the active circuit object.
    The name of the active circuit object is the last name in the global
    CIRCUITNAMES: CIRCUITNAMES[-1]. The circuit object itself is stored in the
    dictionary CIRCUITS under this name: circuitDict[CIRCUITNAMES[-1]].

    :param circuitDict: Dictionary to which the definition will be written,
                        defaults to CIRCUITS.
    :type circuitDict: dictionary

    :param line: list with tokens from a netlist line
    :type line: list with tokens

    :return: Errors: number of errors found in this line.

    :rtype: Integer
    """
    global _CIRCUITNAMES
    parDef = {}
    model  = None
    errors = 0
    cmd = line[0].value.upper()
    if cmd == 'LIB' or (len(cmd) >= 3 and cmd[:3] == 'INC'):
        _parseLibrary(line, name, cirType)
    elif cmd == 'PARAM':
        for i in range(1, len(line)):
            if line[i].type == 'PARDEF':
                parName, parValue = line[i].value
                parDef[parName] = parValue
            else:
                errors += 1
                _printError("Error: Expected a parameter definition.", line[i])
        if errors == 0:
            _addParDef(name, cirType, parDef)
    elif cmd == 'MODEL':
        if len(line) < 3:
            _printError("Error: Incomplete model specification.", line[-1])
        else:
            newModelDef = modelDef()
            if line[1].type == 'ID':
                newModelDef.name = line[1].value
            else:
                errors += 1
                _printError("Error: Expected a model name.", line[1])
            if line[1].type == 'ID':
                modelType = line[2].value
                if modelType not in _MODELS.keys():
                    errors += 1
                    _printError("Error: Unknown model.", line[2])
                    newModelDef.type = False
                else:
                    newModelDef.type = line[2].value
            else:
                errors +=1
                _printError("Error: Expected a model type.", line[1])
        if len(line) > 3:
            validParams = _MODELS[newModelDef.type].params
            for i in range(3, len(line)):
                if line[i].type == "PARDEF":
                    parName, parValue = line[i].value
                    if parName in validParams:
                        if _MODELS[newModelDef.type].params[parName] == False:
                            if ini.laplace in parValue.atoms(sp.Symbol):
                                _printError("Error: Laplace variable not allowed in the expression for this parameter.", line[i])
                                errors += 1
                            else:
                                newModelDef.params[parName] = parValue
                        else:
                            newModelDef.params[parName] = parValue
                    else:
                        errors += 1
                        _printError("Error: unknown model parameter.", line[i])
                else:
                    errors += 1
                    _printError("Error: Expected a parameter definition.", line[i])
        if errors == 0:
            model = newModelDef
            _addModel(name, cirType, model)

def _parseLibrary(line, name, cirType):
    """
    Parsing of a .include or .lib command. If the library exists and has not
    been called earlier, the path of the library will be stured in the list
    USERLIBS, and the library will be compiled (see: _compileUSERLibrary()).

    If the library does not exist the error count of the active circuit will be
    increased with one.

    The name of the active circuit object is the last name in the global
    CIRCUITNAMES: CIRCUITNAMES[-1]. The circuit object itself is stored in the
    dictionary CIRCUITS under this name: circuitDict[CIRCUITNAMES[-1]].

    1. Check of the file exists at the first of the following locations:

       1. In the absolute path or path relative to the project directory
       2. In the circuit directory (ini.circuitPath)
       3. In the project library directory (ini.libraryPath)

    2. Add the definitions of subcircuits, models and parameters to the globals
       USERCIRCUITS, USERMODELS, and USERPARAMS, respectively

    Note: libraries are always global.

    :param line: list with tokens from a netlist line
    :type line: list with tokens

    :param circuitDict: Dictionary to which the definition will be written,
                        defaults to CIRCUITS.
    :type circuitDict: dictionary

    :return: Errors: number of errors found in this line.

    :rtype: Integer
    """
    global _CIRCUITNAMES, _USERLIBS
    for i in range(1, len(line)):
        errors = 0
        if line[i].type == 'FNAME':
            # 1. Check if the file exists:
            #    1. Absolute path
            #    2. In circuit directory      (ini.circuitPath)
            #    3. In project lib directory  (ini.libraryPath)
            # 2. Add definitions of circuits, models and parameters to the
            # 3. USERCIRCUITS, USERMODELS and USERPARAMS (if not yet present)
            # Libraries are always global!
            fileName = line[i].value
            if fileName == 'SLiCAP.lib':
                _printError("Warning: a system library call in the netlist will be ignored.", line[i])
                return
            else:
                if os.path.exists(fileName):
                    pass
                elif os.path.exists(ini.cir_path + fileName):
                    fileName = ini.cir_path + fileName
                elif os.path.exists(ini.user_lib_path + fileName):
                    fileName = ini.user_lib_path + fileName
                else:
                    _printError("Error: cannot find library file: " + fileName + ".", line[i])
                    errors += 1
                    _addErrors(name, cirType, errors)
                if errors == 0 and fileName not in _USERLIBS:
                    _USERLIBS.append(fileName)
                    _compileUSERLibrary(fileName)
        else:
            errors += 1
            _printError("Error: Expected a file path.", line[i])
    return errors

""" PASS 2 FUNCTIONS """

def _checkReferences(circuitObject):
    """
    Second pass of the parser:

    1. Check if the referenced elements exsist in the circuit
    2. Check if the parameters of a model correspond with those of its basic
       model, if so, the model name is replaced with the model definition.
    3. Check if the model definitions of the elements are correct and can be
       found. If so, the model name in a model definition (.model netlist
       entry) is replaced with its definition.
    4. Check if the element parameters correspond with those of the model.

    :param circuitObject: Circuit object to be checked.

    :type circuitObject: SLiCAP circuit object

    :return: None
    :rtype: NoneType
    """
    _checkElementReferences(circuitObject)
    _checkModelDefs(circuitObject)
    _checkElementModel(circuitObject)
    subCircuits = circuitObject.circuits.keys()
    for cir in subCircuits:
        _checkReferences(circuitObject.circuits[cir])

def _checkElementReferences(circuitObject):
    """
    Checks if referenced elements exist in the circuit.

    :param circuitObject: Circuit object to be checked.

    :type circuitObject: SLiCAP circuit object
    """
    elementNames = list(circuitObject.elements.keys())
    for el in elementNames:
        for referencedElement in circuitObject.elements[el].refs:
            if referencedElement not in elementNames:
                circuitObject.errors += 1
                print("Error: unknown referenced element: " + referencedElement)

def _checkModelDefs(circuitObject):
    """
    Checks if the parameters given with a model statement (.model line)
    correspond with those of the model definition.

    :param circuitObject: Circuit object to be checked.

    :type circuitObject: SLiCAP circuit object

    :return: None
    :rtype: NoneType
    """
    for modelName in circuitObject.modelDefs.keys():
        baseModel = circuitObject.modelDefs[modelName].type
        modelParams = _MODELS[baseModel].params.keys()
        referredParams = circuitObject.modelDefs[modelName].params.keys()
        for parName in referredParams:
            if parName not in modelParams:
                print("Error: unknown model parameter: " + parName)
                circuitObject.errors += 1

def _checkElementModel(circuitObject):
    """
    Checks:
        1. If the element has a correct model definition
        2. If the model parameters correspond with those of the prototype model
        3. If the use of the Laplace variable in expressions is allowed.

    If the element model is not a built-in model, and the model definition
    is not included in the circuit, the definition will be taken from a
    library file.

    If the element model is not given the default device model will be used.

    If the element is not a subcircuit, the model attribute will be set to that
    basic model (e.g. 'Q2N3904' will be replaced with 'Q'), and model
    parameters that have not been defined will obtain their default value.

    If the element is a subcircuit model parameters that have not been defined
    with the call will obtain their default value.

    :param circuitObject: Circuit object to be checked.

    :type circuitObject: SLiCAP circuit object

    :return: None
    :rtype: NoneType
    """
    elementNames = list(circuitObject.elements.keys())
    for i in range(len(elementNames)):
        elType  = circuitObject.elements[elementNames[i]].type
        if type(circuitObject.elements[elementNames[i]].model) != circuit and elType != 'X':
            circuitObject = _checkElementModelParams(circuitObject, circuitObject.elements[elementNames[i]])
        else:
            circuitObject = _checkSubCircuitElementModelParams(circuitObject, circuitObject.elements[elementNames[i]])

def _checkElementModelParams(circuitObject, el):
    """
    Checks the model parameters used in elements that are not subcircuits (X).
    If the model parameters correspond with those of the prototype, the values
    will be passed to the instance of the prototype. if no values are given
    with the element, default values of the prototype will be used.

    If the model requires expansion then its model attribute will be replaced
    with its prototype subcircuit.

    :param circuitObject: Circuit object that holds the element.
    :type circuitObject: SLiCAPprotos.circuit

    :param el: Element that needs to be checked
    :type el: SLiCAPprotos.element

    :return: circuit object with updated element el.
    :rtype: SLiCAPprotos.circuit
    """
    modelParams = {}
    elModel = el.model
    if elModel == '':
        basicModel = _DEVICES[el.type].models[0]
    elif elModel in _DEVICES[el.type].models:
        basicModel = elModel
    elif elModel != '' and elModel not in _DEVICES[el.type].models:
        # If not present in the circuit model definitions, find it in the libraries
        # and replace the model name with the base model and parameters
        if elModel in circuitObject.modelDefs.keys():
            modelParams = circuitObject.modelDefs[elModel].params
            basicModel =  circuitObject.modelDefs[elModel].type
        elif elModel in _USERMODELS.keys():
            modelParams = _USERMODELS[elModel].params
            basicModel = _USERMODELS[elModel].type
        elif elModel in _SLiCAPMODELS.keys():
            modelParams = _SLiCAPMODELS[elModel].params
            basicModel = _SLiCAPMODELS[elModel].type
        else:
            print("Error: missing definition of model: " + str(elModel) + ".")
            circuitObject.errors += 1
            basicModel = False
    # Assign basic model to element
    el.model = basicModel
    # Check parameter names and complete the list of parameters with default values
    givenParams = el.params
    allParams   = _MODELS[basicModel].params
    for parName in givenParams:
        if parName not in allParams:
            circuitObject.errors += 1
            print("Error: unknown parameter '%s' for element '%s' in circuit '%s'."%(parName, el.refDes, circuitObject.title))
        elif _MODELS[basicModel].params[parName] == False:
            # Laplace variable not allowed inexpression.
            if ini.laplace in el.params[parName].atoms(sp.Symbol):
                print("Error: Laplace variable not allowed in expression of %s."%(el.refDes))
    for parName in allParams.keys():
        if parName not in givenParams.keys():
            if parName not in modelParams:
                # Assign default values to missing parameters
                if _MODELS[basicModel].stamp:
                    el.params[parName] = sp.N(0)
                else:
                    el.params[parName] = _SLiCAPCIRCUITS[basicModel].params[parName]
            else:
                el.params[parName] = modelParams[parName]
        else:
            el.params[parName] = givenParams[parName]
    if not _MODELS[basicModel].stamp:
        # Assign the expansion circuit to the model attribute
        el.model = _SLiCAPCIRCUITS[basicModel]
    circuitObject.elements[el.refDes] = el
    return circuitObject

def _checkSubCircuitElementModelParams(circuitObject, el):
    """
    Checks the model parameters of subcircuit elements (X).
    If the model parameters correspond with those of the prototype, the values
    will be passed to the instance of the prototype. if no values are given
    with the element, default values of the prototype will be used.

    The model attribute will be replaced with its prototype subcircuit.

    :param circuitObject: Circuit object that holds the element.
    :type circuitObject: SLiCAPprotos.circuit

    :param el: Element that needs to be checked
    :type el: SLiCAPprotos.element

    :return: circuit object with updated element el.
    :rtype: SLiCAPprotos.circuit
    """
    if type(el.model) != circuit:
        if el.model in circuitObject.circuits.keys():
            validParams = circuitObject.circuits[el.model].params
            el.model = circuitObject.circuits[el.model]
        elif el.model in _USERCIRCUITS.keys():
            validParams = _USERCIRCUITS[el.model].params
            el.model = _USERCIRCUITS[el.model]
        elif el.model in _SLiCAPCIRCUITS.keys():
            validParams = _SLiCAPCIRCUITS[el.model].params
            el.model = _SLiCAPCIRCUITS[el.model]
        elif el.model in _CIRCUITS.keys():
            validParams = _CIRCUITS[el.model].params
            el.model = _CIRCUITS[el.model]
        else:
            print("Error: missing definition of subcircuit: " + el.model + ".")
            circuitObject.errors += 1
            el.model = False
            validParams = {}
        for parName in el.params:
            if parName not in validParams.keys():
                print("Error: unknown model parameter: " + parName)
                circuitObject.errors += 1
            elif ini.laplace in el.params[parName].atoms(sp.Symbol):
                print("Error: Laplace variable not allowed in subcircuit calls!\n  Parameter: '%s', element: `%s`, circuit: '%s'."%(parName, el.ID, circuitObject.title))
                circuitObject.errors += 1
    circuitObject.elements[el.refDes] = el
    return circuitObject

""" PASS 3 FUNCTIONS """

def _expandCircuit(circuitObject):
    """
    This functions flattens the hierarchy of circuitObject:

    1. Sub circuits and model expansions will be expanded and connected to
       the main circuit
    2. Parameter definitions will be updated:

    :param circuitObject: SLiCAP circuit object to be expanded

    :return: SLiCAP circuit object of the expanded circuit
    :rtype: SLiCAP circuit object
    """
    #elNames = list(circuitObject.elements.keys())
    for elName in list(circuitObject.elements.keys()):
        el = circuitObject.elements[elName]
        if isinstance(el.model, circuit):
            circuitObject = _doExpand(el, circuitObject)
    return circuitObject
    
def _doExpand(el, circuitObject):
    parentRefDes    = el.refDes
    parentNodes     = el.nodes
    parentParams    = el.params
    prototypeNodes  = el.model.nodes
    prototypeParams = el.model.params
    parentParDefs   = circuitObject.parDefs
    childParDefs  = el.model.parDefs
    circuitObject.parDefs = _updateParDefs(parentParDefs, childParDefs, parentParams, prototypeParams, parentRefDes)
    for subElement in list(el.model.elements.keys()):
        newElement = deepcopy(el.model.elements[subElement])
        # Update the refDes
        newElement.refDes = el.model.elements[subElement].refDes + '_' + el.refDes
        # Update the referenced elements
        for i in range(len(newElement.refs)):
            newElement.refs[i] += '_' + el.refDes
        # Update the nodes
        newElement = _updateNodes(newElement, parentNodes, prototypeNodes, parentRefDes)
        # Update the parameters used in element expressions and in parameter definitions
        newElement, newParDefs = _updateElementParams(newElement, parentParams, prototypeParams, parentRefDes)
        for key in newParDefs.keys():
            if key not in circuitObject.parDefs.keys():
                circuitObject.parDefs[key] = newParDefs[key]
        # Add the new element to the parent circuit
        circuitObject.elements[newElement.refDes] = newElement
        # If the new element is a sub circuit, it needs to be expanded
        if isinstance(newElement.model, circuit): 
            circuitObject = _doExpand(newElement, circuitObject)
    del circuitObject.elements[el.refDes]
    return circuitObject

def _updateNodes(newElement, parentNodes, prototypeNodes, parentRefDes):
    """
    Determines the nodes of a subcircuit element.

    1. If the node is in de node list of the prototype circuit, it is replaced
       with the corresponding (same index) node of the parent element.
    2. If this is not the case, the node is an interbal node and it will
       receive the name of the node of the pprototype circuit with the postfix
       _<refDes of parent element>.

    :param newElement: Element of the subciorcuit that needs to be connected to
                       the parent circuit.
    :type newElement: SLiCAPprotos.element

    :param parentNodes: Node list of the parent element.
    :type parentNodes: list

    :param prototypeNodes: Node list of the prototype expansion (circuit)
    :type prototypeNodes: list

    :param parentRrefDes: Reference designator of the parent element
    :type parentRefDes: str

    :return: newElement with updated node list
    :rtype: SLiCAPprotos.element
    """
    for i in range(len(newElement.nodes)):
        if newElement.nodes[i] != '0':
            try:
                pos = prototypeNodes.index(newElement.nodes[i])
                newElement.nodes[i] = parentNodes[pos]
            except ValueError:
                    newElement.nodes[i] += '_' + parentRefDes
    return newElement

def _updateElementParams(newElement, parentParams, prototypeParams, parentRefDes):
    """
    After expansion of the elements, the element parameters can be:
    'value'
    'noise'
    'dc'
    'dcvar'
    'dcvarlot'
    'noisetemp'
    'noiseflow'

    The values of these parameters are symbolic expressions. The atoms of these
    expressions are parameters. The update procedure is as follows:


    #. If the parameter is a parameter of the parent circuit, then it needs to
       obtain the value given with the parent circuit.
    #. Else if the parameter is a parameter of the prototype circuit, then it
       needs to obtain the value given with the prototype circuit
    #. Else if the parameter is defined in a user library (in USERPARAMS), then
       the definition from this library needs to be added to the parameter
       definitions of the parent circuit.
    #. Else if the parameter is defined in a system library (in SLiCAPPARAMS),
       then the definition from this library needs to be added to the parameter
       definitions of the parent circuit.
    #. Else: the parameter name will receive the postfix: _<parentRefDes)>.


    :param newElement: Element of the subciorcuit that needs to be connected to
                       the parent circuit.
    :type newElement: SLiCAPprotos.element

    :param parentParams: Dictionary with key-value pairs of parameters of the
                         parent element:

                         - key *str*: name of the parameter
                         - value: *SympyExpression*: value or expression of
                           this parameter

    :param prototypeParams: Dictionary with key-value pairs of parameters of
                            the prototype circuit:

                            - key *str*: name of the parameter
                            - value: *SympyExpression*: value or expression of
                              this parameter

    :param parentRrefDes: Reference designator of the parent element
    :type parentRefDes: str

    :return: newElement with updated node list
    :rtype: SLiCAPprotos.element
    """
    parNames  = list(newElement.params.keys())
    params    = []
    substDict = {}
    newParDefs = {}
    for parName in parNames:
        params += list(newElement.params[parName].atoms(sp.Symbol))
    for parName in params:
        if str(parName) in parentParams.keys():
            substDict[parName] = parentParams[str(parName)]
        elif str(parName) in prototypeParams.keys():
            substDict[parName] = prototypeParams[str(parName)]
        elif str(parName) in _USERPARAMS.keys():
            newParDefs[parName] = _USERPARAMS[str(parName)]

            # recursively add parameters from expression in parameter definition
            # from USERPARAMS

        elif str(parName) in _SLiCAPPARAMS.keys():
            newParDefs[parName] = _SLiCAPPARAMS[str(parName)]

            # recursively add parameters from expression in parameter definition
            # from SLiAPPARAMS

        elif parName != ini.laplace and parName != ini.frequency:
            substDict[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
    # Perform the full substitution in the parameter values of the element
    for parName in parNames:
        newElement.params[parName] = fullSubs(newElement.params[parName], substDict)
    return newElement, newParDefs

def _updateParDefs(parentParDefs, childParDefs, parentParams, prototypeParams, parentRefDes):
    """
    The parameter definitions of the parent circuit will be updated:

    Parameters of the child circuit as well as parameters in their expressions
    will be treated as follows:

    #. If the parameter is a parameter of the parent circuit, then the child 
       needs to obtain the value given with the parent circuit.
    #. Else if the parameter is a parameter of the prototype circuit, then the
       child needs to obtain the value given with the prototype circuit
    #. Else if the parameter is defined in a user library (in _USERPARAMS),
       then the definition from this library needs to be added to the parameter
       definitions of the parent circuit.
    #. Else if the parameter is defined in a system library (in SLiCAPPARAMS),
       then the definition from this library needs to be added to the parameter
       definitions of the parent circuit.
    #. Else: the parameter name will receive the postfix: _<parentRefDes)>.

    :param newElement: Element of the subciorcuit that needs to be connected to
                       the parent circuit.
    :type newElement: SLiCAPprotos.element

    :param parentParams: Dictionary with key-value pairs of parameters of the
                         parent element:

                         - key *str*: name of the parameter
                         - value: *SympyExpression*: value or expression of
                           this parameter

    :param prototypeParams: Dictionary with key-value pairs of parameters of
                            the prototype circuit:

                            - key *str*: name of the parameter
                            - value: *SympyExpression*: value or expression of
                              this parameter

    :param parentRrefDes: Reference designator of the parent element
    :type parentRefDes: str

    :return: newElement with updated node list
    :rtype: SLiCAPprotos.element
    """
    # Create a list with all parameters
    allParams = childParDefs.keys()
    allAtoms = []
    for parName in allParams:
        allAtoms += childParDefs[parName].atoms(sp.Symbol)
    allParams = [sp.Symbol(par) for par in allParams]
    allParams += allAtoms
    substDictNames  = {}
    substDictValues = {}
    for parName in allParams:
        if parName != ini.laplace and parName != ini.frequency:
            if str(parName) in parentParams.keys():
                substDictValues[parName] = parentParams[str(parName)]
            elif str(parName) in prototypeParams.keys():
                substDictValues[parName] = prototypeParams[str(parName)]
            elif str(parName) in _USERPARAMS.keys():
                parentParDefs = _addParDefsParam(parName, parentParDefs)
            elif str(parName) in _SLiCAPPARAMS.keys():
                parentParDefs = _addParDefsParam(parName, parentParDefs)
            else :
                substDictNames[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
                substDictValues[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
    for parName in childParDefs.keys():
        """
        Add a child parameter definition to the parent parameter definitions if:
            - the parameter is not the Laplace or Fourier variable
            - the parameter is not in the prototype definition
        """
        if sp.Symbol(parName) != ini.laplace and sp.Symbol(parName) != ini.frequency and parName not in prototypeParams.keys():
            parentParDefs[fullSubs(sp.Symbol(parName), substDictNames)] = fullSubs(childParDefs[parName], substDictValues)
    return parentParDefs

def _addParDefsParam(parName, parDict):
    """
    Adds a the definition of a global parameter (from SLiCAP.lib or from a
    user library) and, recursively, the parameters from its expression to
    the dictionary parDict.

    :param parName: Name of the parameter.
    :type parName: sympy.Symbol, or str.

    :return: parDict
    :rtype: dict
    """
    parName = str(parName)
    if parName not in parDict.keys():
        if parName in _USERPARAMS.keys():
            parDict[parName] = _USERPARAMS[parName]
            newParams = _USERPARAMS[parName].atoms(sp.Symbol)
            for newParam in newParams:
                _addParDefsParam(newParam, parDict)
        elif parName in _SLiCAPPARAMS.keys():
            parDict[parName] = _SLiCAPPARAMS[parName]
            newParams = _SLiCAPPARAMS[parName].atoms(sp.Symbol)
            for newParam in newParams:
                _addParDefsParam(newParam, parDict)
    return parDict

""" PASS 4 FUNCTIONS """

def _updateCirData(circuitObject):
    """
    Updates data of the main expanded circuit required for instructions.

    - Updates the lists with dependent variables (detectors), sources
      (independent variables) and controlled sources (possible loop gain
      references).
    - If global parameters are used in the circuit, their definition is added
      to the '.parDefs' attribute of the circuit.
    - Checks if the global ground node '0' is used in the circuit.
    - Checks if the circuit has at least two nodes.
    - Checks if the referenced elements exist.
    - Converts circuitObject.params into list and puts the undefined parameters
      in it

    :param circuitObject: Circuit object to be updated
    :type circuitObject: SLiCAPprotos.circuit

    :return: Updated circuit object
    :rtype: SLiCAPprotos.circuit
    """
    # Convert *char* keys in the .parDefs attribute into sympy symbols.
    for key in list(circuitObject.parDefs.keys()):
        if type(key) == str:
            circuitObject.parDefs[sp.Symbol(key)] = circuitObject.parDefs[key]
            del(circuitObject.parDefs[key])
    circuitObject.params =[]
    circuitObject.nodes = []
    circuitObject.dep_vars = []
    circuitObject.indepVars = []
    circuitObject.references = []
    for elmt in circuitObject.elements.keys():
        circuitObject.nodes += circuitObject.elements[elmt].nodes
        if circuitObject.elements[elmt].type in _INDEPSCRCS:
            circuitObject.indepVars.append(elmt)
        elif circuitObject.elements[elmt].type in _CONTROLLED:
            circuitObject.controlled.append(elmt)
        circuitObject.references += circuitObject.elements[elmt].refs
        for i in range(len(_MODELS[circuitObject.elements[elmt].model].depVars)):
            depVar = _MODELS[circuitObject.elements[elmt].model].depVars[i]
            circuitObject.dep_vars.append(depVar + '_' + elmt)
        # Add parameters used in element expressions to circuit.params
        for par in circuitObject.elements[elmt].params.keys():
            try:
                circuitObject.params += circuitObject.elements[elmt].params[par].atoms(sp.Symbol)
            except:
                pass
 
    # Add parameters used in parDef expressions to circuit.params
    for par in list(circuitObject.parDefs.keys()):
        circuitObject.params.append(par)
        circuitObject.params += circuitObject.parDefs[par].atoms(sp.Symbol)
    circuitObject.params = list(set(circuitObject.params))
    # Try to find required global parameter definitions for undefined params
    
    for par in circuitObject.params:
        if par != ini.laplace and par != ini.frequency and par not in list(circuitObject.parDefs.keys()):
            circuitObject = _addGlobalParam(par, circuitObject)
            
    # Remove parameters with definitions from the undefined parameters list
    newParams=[]
    circuitObject.params = list(set(circuitObject.params))
    for par in circuitObject.params:
        if par != ini.laplace and par != ini.frequency and par not in list(circuitObject.parDefs.keys()):
            newParams.append(par)
    circuitObject.params = newParams
            
    # check for two connections per node (warning)
    connections = {i:circuitObject.nodes.count(i) for i in circuitObject.nodes}
    
    #for key in connections.keys():
    #    if connections[key] < 2:
    #        print("Warning less than two connections at node: '{0}'.".format(key))
    
    # Remove duplicate entries in the referenced elements list
    circuitObject.references = list(set(circuitObject.references))
    # Remove duplicate entries from node list and sort the list."
    circuitObject.nodes = list(set(circuitObject.nodes))
    circuitObject.nodes.sort()
    if '0' not in circuitObject.nodes:
        circuitObject.errors += 1
        print("Error: could not find ground node '0'.")
    nodeVoltages = ['V_' + circuitObject.nodes[i] for i in range(len(circuitObject.nodes))]
    circuitObject.dep_vars += nodeVoltages
    # Check source
    if circuitObject.source != None:
        for src in circuitObject.source:
            if src != None:
                if src not in circuitObject.indepVars:
                    print("Error: unknown signal source: {}.".format(src))
                    circuitObject.errors += 1
    # Check loop gain reference
    if circuitObject.lgRef!= None:
        for lgRef in circuitObject.lgRef:
            if lgRef != None:
                if lgRef not in circuitObject.controlled:
                    print("Error: unknown loop gain reference: {}.".format(lgRef))
                    circuitObject.errors += 1
    return circuitObject

def _addGlobalParam(par, circuitObject):
    if str(par) in _SLiCAPPARAMS.keys():
        circuitObject.parDefs[par] = _SLiCAPPARAMS[str(par)]
        newParams = _SLiCAPPARAMS[str(par)].atoms(sp.Symbol)
        for newParam in newParams:
            # Parameters in the expression of a global parameter also have a 
            # global definition 
            # circuitObject.parDefs[newParam] = _SLiCAPPARAMS[str(newParam)]
            circuitObject = _addGlobalParam(newParam, circuitObject)
    elif par == ini.laplace or par == ini.frequency:
        circuitObject.params.remove(par)
    return circuitObject

def _checkCircuit(fileName):
    """
    Main function for checking a netlist and converting it into a 'flattened'
    circuit object.

    PASS 1: Tokenize and parse the netlist to a nested circuit object

    PASS 2: Complete all data, include libraries and replace models and
    circuits to be expanded with thei prototype circuit

    PASS 3: Expand subcircuits and models using their prototypes

    PASS 4: Complete data for instructions

    :param fileName: Name of the netlist file, residing in the .cir subdirectory
                     of the product folder.

    :type fileName: str

    :return: Circuit object
    :rtype: SLiCAPprotos.circuit
    """
    _resetParser()
    fileName = ini.cir_path + fileName
    print("Checking netlist:", fileName)
    # Read the netlist
    f = open(fileName, 'r')
    netlist = f.read()
    f.close()
    # Check the circuit
    # PASS 1
    _parseNetlist(netlist, 'main', 'main') # Tokenize and parse the netlist to a nested circuit object
    # PASS 2
      
    if _CIRCUITS['main'].errors == 0:
        for key in _CIRCUITS.keys():
            _checkReferences(_CIRCUITS[key]) # Complete all data, include libraries and replace models and circuits to be expanded with thei prototype circuit
        if _CIRCUITS[key].errors == 0:
            # PASS 3
            _CIRCUITS['main'] = _expandCircuit(_CIRCUITS['main']) # Expand subcircuits and models
            # PASS 4
            _CIRCUITS['main'] = _updateCirData(_CIRCUITS['main']) # Complete data for instructions
        if _CIRCUITS['main'].errors == 0:
            ini.html_prefix = ('-'.join(_CIRCUITS['main'].title.split()) + '_')
            ini.html_index = 'index.html'
            htmlPage(_CIRCUITS['main'].title, index = True)
        else:
            print("Errors found during updating of circuit data from '{0}'. Instructions with this circuit will not be executed.".format(_CIRCUITS['main'].title))
    else:
        print("Found", _CIRCUITS['main'].errors, "error(s).")
    return _CIRCUITS['main']

def _makeLibraries():
    _compileSLiCAPLibraries()