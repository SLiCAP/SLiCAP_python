#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SLiCAP three-pass netlist parser:

pass 1: parseNetlist(<netlist>)
        Converts the netlist into a nested circuit object mainCircuit = circuit()
        - mainCircuit.elements:
            list with element objects from element definition lines
        - mainCircuit.modelDefs:
            dictionary with modelDef objects from .model definition lines:
                key   = model name (str)
                value = modelDef object for this model
        - mainCircuit.parDefs   parDef objects from .param definition lines :
            dictionary with parameters:
                key   = parameter name (str)
                value = sympy object (Symbol, Expression, Integer, Float)
        - mainCircuit.libs:
            list with file names (str) from .include and .lib lines
        - (sub)circuit definitions:
            dictionary with circuit objects:
                key   = subcircuit name
                value = circuit object, as the main object, but with nodes
                        and parameters that can be passed.

pass 2: checkData(<circuit>)
        Checks and completes the data of the nested circuits object:
        - check if referenced elements exist in the circuit
        - check if library files exist
        - create modelDef objects from the libraries
        - create (sub)circuit objects from the libraries

pass 3: Flattens the netlist: the nested circuit is converted into one circuit.

You can include .include or .lib commands in library files but library files
will always be global.
"""

import os
import sympy as sp
from copy import deepcopy
from SLiCAP.SLiCAPhtml import htmlPage
from SLiCAP.SLiCAPlex import tokenize, printError
from SLiCAP.SLiCAPprotos import MODELS, DEVICES, circuit, element, modelDef
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPmath import fullSubs

# Composite tokens
NODES           = ['NODEID', 'ID', 'INT']
VALEXPR         = ['FLT', 'EXPR', 'SCI', 'INT']
TITLE           = ['ID', 'QSTRING', 'FNAME']

# Lists with constrolled and independent sources
CONTROLLED      = ['E', 'F', 'G', 'H']  # Controlled sources
INDEPSCRCS      = ['I', 'V']            # Independent sources

# list with (sub)circuit names for checking hierarchy
# last name is current circuit during hierarchical checking
CIRCUITNAMES    = []

# Dictionary with (sub)circuit definitions, keys are from CIRCUITNAMES,
# values are circuit objects.
CIRCUITS        = {}

# List with SLiCAP device types
DEVICETYPES     = list(DEVICES.keys())

# List with default SLiCAP libraries
SLiCAPLIBS      = ['SLiCAP.lib', 'SLiCAPmodels.lib']

# SLiCAP built-in models
SLiCAPMODELS    = {}

# SLiCAP global parameters
SLiCAPPARAMS    = {}

# SLiCAP built-in subcircuits
SLiCAPCIRCUITS  = {}

# User include files and library files
USERLIBS        = []

# User defined models from library files
USERMODELS      = {}

# User defined circuit from library files
USERCIRCUITS    = {}

# User defined global parameters from library files
USERPARAMS      = {}

def compileSLiCAPLibraries():
    """
    Compiles the SLiCAP bult-in libraries and writes the subcircuit, models,
    and global parameters to SLiCAPCIRCUITS, SLiCAPMODELS, and SLiCAPPARAMS,
    respectively.

    :return: None
    :rtype: NoneType
    """
    global SLiCAPCIRCUITS, SLiCAPMODELS, SLiCAPPARAMS
    for fi in SLiCAPLIBS:
        print("Compiling library: " + fi + ".")
        f = open(ini.defaultLib + '/' + fi, 'r')
        netlist = f.read()
        f.close()
        cirName  = fi.split('.')[0]
        parseNetlist(netlist, cirName, SLiCAPCIRCUITS)
        for model in list(SLiCAPCIRCUITS[cirName].modelDefs.keys()):
            SLiCAPMODELS[model] = SLiCAPCIRCUITS[cirName].modelDefs[model]
        for param in list(SLiCAPCIRCUITS[cirName].parDefs.keys()):
            SLiCAPPARAMS[param] = SLiCAPCIRCUITS[cirName].parDefs[param]
        del SLiCAPCIRCUITS[cirName]
    # PASS 2 and 3
    for cir in list(SLiCAPCIRCUITS.keys()):
        checkReferences(SLiCAPCIRCUITS[cir])
        #expandCircuit(SLiCAPCIRCUITS[cir])

def compileUSERLibrary(fileName):
    """
    Parses a user library file and writes the subcircuit, models,
    and global parameters to USERCIRCUITS, USERPMODELS, and USERPARAMS,
    respectively.

    :param fileName: Path of the library file

    :type fileName: str

    :return: None
    :rtype: NoneType
    """
    global CIRCUITNAMES, USERCIRCUITS, USERPARAMS, USERMODELS
    print("Compiling library: " + fileName + ".")
    f = open(fileName, 'r')
    netlist = f.read()
    f.close()
    cirName  = '__library__'
    parseNetlist(netlist, cirName, USERCIRCUITS)
    for model in list(USERCIRCUITS[cirName].modelDefs.keys()):
        USERMODELS[model] = USERCIRCUITS[cirName].modelDefs[model]
    for param in list(USERCIRCUITS[cirName].parDefs.keys()):
        USERPARAMS[param] = USERCIRCUITS[cirName].parDefs[param]
    del USERCIRCUITS[cirName]
    # PASS 2 and 3
    for cir in list(USERCIRCUITS.keys()):
        checkReferences(USERCIRCUITS[cir])

def parseNetlist(netlist, cirName = 'main', circuitDict = CIRCUITS):
    """
    Netlist parser: converts a netlist to the active circuit object.
    The name of the active circuit object is the last name in the global
    CIRCUITNAMES: CIRCUITNAMES[-1]. The circuit object itself is stored in the
    dictionary CIRCUITS under this name: circuitDict[CIRCUITNAMES[-1]].

    :param netlist: Netlist of the circuit
    :type netlist: String

    :param cirName: Name of the (sub)circuit, defaults to 'main'
    :type cirName: String (no whitespace characters)

    :param circuitDict: Dictionary to which the definition will be written
    :type circuitDict: dictionary

    :return: None

    :rtype: Nonetype
    """
    global CIRCUITNAMES
    CIRCUITNAMES.append(cirName)
    circuitDict[cirName] = circuit()
    lines, errors = tokenize(netlist)
    if errors == 0:
        if cirName == 'main' and lines[0][0].type in TITLE:
            circuitDict[cirName].title = lines[0][0].value
            if lines[0][0].type == 'QSTRING':
                # Remove the double quotes, this conflicts with HTML files
                circuitDict[cirName].title = circuitDict[cirName].title[1:-1]
        lines = lines[1:]
        for line in lines:
            if line[0].type == "ID":
                deviceType = line[0].value[0].upper()
                if deviceType != 'X':
                    circuitDict[cirName].errors = parseElement(line, circuitDict)
                else:
                    circuitDict[cirName].errors = parseSubcircuitElement(line, circuitDict)
            elif line[0].type == "CMD":
                cmdType = line[0].value.upper()
                if cmdType == "SUBCKT":
                    if len(line) > 1:
                        if line[1].type == "ID":
                            cirName = line[1].value
                            if cirName not in CIRCUITNAMES:
                                CIRCUITNAMES.append(cirName)
                                if cirName not in list(CIRCUITS.keys()):
                                    circuitDict[cirName] = circuit()
                                    circuitDict[cirName].title = line[1].value
                                    # Change the type of params of the subcircuit
                                    # Better: create a subcircuitParams attribute
                                    circuitDict[cirName].params = {}
                            else:
                                circuitDict[cirName].errors += 1
                                printError("Error: Hierarchical loop involving '" + line[1].value + "'.", line[1])
                        else:
                           printError("Error: Expected a circuit title.", line[1])
                           circuitDict[cirName].errors += 1
                    else:
                        printError("Error: Missing circuit title", line[0])
                        circuitDict[cirName].errors += 1
                    if len(line) > 2:
                        for i in range(2, len(line)):
                            if line[i].type in NODES:
                                circuitDict[cirName].nodes.append(line[i].value)
                            elif line[i].type == "PARDEF":
                                parName, parValue = line[i].value
                                circuitDict[cirName].params[parName] = parValue
                            else:
                                printError("Error: Unexpected input.", line[i])
                                circuitDict[cirName].errors += 1
                elif cmdType == "ENDS":
                    subcktErrors =  circuitDict[CIRCUITNAMES[-1]].errors
                    del CIRCUITNAMES[-1]
                    circuitDict[CIRCUITNAMES[-1]].circuits[cirName] = circuitDict[cirName]
                    circuitDict[CIRCUITNAMES[-1]].errors += subcktErrors
                    cirName = CIRCUITNAMES[-1]
                elif cmdType == "END":
                    del CIRCUITNAMES[-1]
                else:
                    circuitDict[cirName].errors += parseCommand(line, circuitDict)
    else:
        circuitDict[cirName].errors += errors
        if cirName != 'main':
            print("Error: something wring with circuit hierachy, probably missing '.ends'. in a subcircuit definition.")
    return

def parseElement(line, circuitDict = CIRCUITS):
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
    global CIRCUITNAMES
    newElement = element()
    deviceType = line[0].value[0].upper()
    errors = 0
    if deviceType in DEVICETYPES:
        newElement.type = deviceType
        newElement.refDes =  line[0].value
        nNodes = DEVICES[deviceType].nNodes
        nRefs = DEVICES[deviceType].nRefs
        nFields = 1 + nNodes + nRefs
        if DEVICES[deviceType].value == True:
            nFields += 1
        if len(line) < nFields:
            printError("Error: incomplete element specification.", line[-1])
            errors += 1
        else:
            for i in range(nNodes):
                pos = 1 + i
                if line[pos].type in NODES:
                    newElement.nodes.append(line[pos].value)
                else:
                    printError("Error: syntax error in node ID", line[pos])
                    errrors += 1
            for i in range(DEVICES[deviceType].nRefs):
                pos = 1 + nNodes + i
                if line[pos].type == "ID":
                    newElement.refs.append(line[pos].value)
                else:
                    printError("Error: syntax error in device ID", line[pos])
                    errrors += 1
            pos = 1 + nNodes + nRefs
            if DEVICES[deviceType].value:
                if line[pos].type == "ID":
                    newElement.model = line[pos].value
                elif line[pos].type in VALEXPR:
                    newElement.model = DEVICES[deviceType].models[0]
                    if line[pos].type == 'EXPR':
                        newElement.params['value'] = line[pos].value
                        if newElement.model in list(MODELS.keys()):
                            if not MODELS[newElement.model].params['value'] and ini.Laplace in list(newElement.params['value'].atoms(sp.Symbol)):
                                printError("Error: Laplace variable not allowed in this expression.", line[pos])
                    else:
                        newElement.params['value'] = sp.Rational(line[pos].value)
                elif line[pos].type == "PARDEF":
                    printError("Error: missing model definition", line[pos])
                    errrors += 1
                else:
                    printError("Error: syntax error in model definition", line[pos])
                    errrors += 1
                for i in range(len(line) - nFields):
                    pos = nFields + i
                    if line[pos].type == "PARDEF":
                        key, value = line[pos].value
                        newElement.params[key] = value
                        if newElement.model in list(MODELS.keys()):
                            if key in list(MODELS[newElement.model].params.keys()):
                                if not MODELS[newElement.model].params[key] and ini.Laplace in list(value.atoms(sp.Symbol)):
                                    printError("Error: Laplace variable not allowed in this expression.", line[pos])
                            else:
                                printError("Error: unknown model parameter", line[pos])
                    else:
                        printError("Error: expected a parameter definition.", line[pos])
                        errors += 1
    else:
        printError("Error: unknown element.", line[-1])
        errors += 1
    if errors == 0:
        circuitDict[CIRCUITNAMES[-1]].elements[newElement.refDes] = newElement
    return errors

def parseSubcircuitElement(line, circuitDict = CIRCUITS):
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
    global CIRCUITNAMES
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
        if line[i].type in NODES:
            newElement.nodes.append(line[i].value)
        else:
            errors += 1
            printError("Error: Expected a node ID.", line[i])
    if len(line) > modelPos + 1:
        for i in range(modelPos + 1, len(line)):
            if line[i].type == "PARDEF":
                key, value = line[i].value
                newElement.params[key] = value
            else:
                errors += 1
                printError("Error: Expected a parameter definition.", line[i])
    if errors == 0:
        circuitDict[CIRCUITNAMES[-1]].elements[newElement.refDes] = newElement
    return errors

def parseCommand(line, circuitDict = CIRCUITS):
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
    global CIRCUITNAMES
    errors = 0
    cmd = line[0].value.upper()
    if cmd == 'LIB' or (len(cmd) >= 3 and cmd[:3] == 'INC'):
        parseLibrary(line, circuitDict = CIRCUITS)
    elif cmd == 'PARAM':
        for i in range(1, len(line)):
            if line[i].type == 'PARDEF':
                parName, parValue = line[i].value
                circuitDict[CIRCUITNAMES[-1]].parDefs[parName] = parValue
            else:
                errors += 1
                printError("Error: Expected a parameter definition.", line[i])
    elif cmd == 'MODEL':
        if len(line) < 3:
            printError("Error: Incomplete model specification.", line[-1])
        else:
            newModelDef = modelDef()
            if line[1].type == 'ID':
                newModelDef.name = line[1].value
            else:
                errors += 1
                printError("Error: Expected a model name.", line[1])
            if line[1].type == 'ID':
                modelType = line[2].value
                if modelType not in list(MODELS.keys()):
                    errors += 1
                    printError("Error: Unknown model.", line[2])
                    newModelDef.type = False
                else:
                    newModelDef.type = line[2].value
            else:
                errors +=1
                printError("Error: Expected a model type.", line[1])
        if len(line) > 3:
            validParams = MODELS[newModelDef.type].params
            for i in range(3, len(line)):
                if line[i].type == "PARDEF":
                    parName, parValue = line[i].value
                    if parName in validParams:
                        if MODELS[newModelDef.type].params[parName] == False:
                            if ini.Laplace in list(parValue.atoms(sp.Symbol)):
                                printError("Error: Laplace variable not allowed in the expression for this parameter.", line[i])
                                errors += 1
                            else:
                                newModelDef.params[parName] = parValue
                        else:
                            newModelDef.params[parName] = parValue
                    else:
                        errors += 1
                        printError("Error: unknown model parameter.", line[i])
                else:
                    errors += 1
                    printError("Error: Expected a parameter definition.", line[i])
        if errors == 0:
            circuitDict[CIRCUITNAMES[-1]].modelDefs[newModelDef.name] = newModelDef
    return errors

def parseLibrary(line, circuitDict = CIRCUITS):
    """
    Parsing of a .include or .lib command. If the library exists and has not
    been called earlier, the path of the library will be stured in the list
    USERLIBS, and the library will be compiled (see: compileUSERLibrary()).

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
    global CIRCUITNAMES
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
                printError("Warning: a system library call in the netlist will be ignored.", line[i])
                errors += 1
            else:
                if os.path.exists(fileName):
                    pass
                elif os.path.exists(ini.circuitPath + fileName):
                    fileName = ini.circuitPath + fileName
                elif os.path.exists(ini.libraryPath + fileName):
                    fileName = ini.libraryPath + fileName
                else:
                    printError("Error: cannot find library file: " + fileName + ".", line[i])
                    circuitDict[CIRCUITNAMES[-1]].errors += 1
                    fileName = False
                if fileName != False:
                    if fileName not in USERLIBS:
                        USERLIBS.append(fileName)
                        compileUSERLibrary(fileName)
        else:
            errors += 1
            printError("Error: Expected a file path.", line[i])
    return errors

""" PASS 2 FUNCTIONS """

def checkReferences(circuitObject):
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
    checkElementReferences(circuitObject)
    checkModelDefs(circuitObject)
    checkElementModel(circuitObject)
    subCircuits = list(circuitObject.circuits.keys())
    for cir in subCircuits:
        checkReferences(circuitObject.circuits[cir])

def checkElementReferences(circuitObject):
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

def checkModelDefs(circuitObject):
    """
    Checks if the parameters given with a model statement (.model line)
    correspond with those of the model definition.

    :param circuitObject: Circuit object to be checked.

    :type circuitObject: SLiCAP circuit object

    :return: None
    :rtype: NoneType
    """
    for modelName in list(circuitObject.modelDefs.keys()):
        baseModel = circuitObject.modelDefs[modelName].type
        modelParams = list(MODELS[baseModel].params.keys())
        referredParams = list(circuitObject.modelDefs[modelName].params.keys())
        for parName in referredParams:
            if parName not in modelParams:
                print("Error: unknown model parameter: " + parName)
                circuitObject.errors += 1

def checkElementModel(circuitObject):
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
        if elType != 'X':
            circuitObject = checkElementModelParams(circuitObject, circuitObject.elements[elementNames[i]])
        else:
            circuitObject = checkSubCircuitElementModelParams(circuitObject, circuitObject.elements[elementNames[i]])

def checkElementModelParams(circuitObject, el):
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
        basicModel = DEVICES[el.type].models[0]
    elif elModel in DEVICES[el.type].models:
        basicModel = elModel
    elif elModel != '' and elModel not in DEVICES[el.type].models:
        # If not present in the circuit model definitions, find it in the libraries
        # and replace the model name with the base model and parameters
        if elModel in list(circuitObject.modelDefs.keys()):
            modelParams = circuitObject.modelDefs[elModel].params
            basicModel =  circuitObject.modelDefs[elModel].type
        elif elModel in list(USERMODELS.keys()):
            modelParams = USERMODELS[elModel].params
            basicModel = USERMODELS[elModel].type
        elif elModel in list(SLiCAPMODELS.keys()):
            modelParams = SLiCAPMODELS[elModel].params
            basicModel = SLiCAPMODELS[elModel].type
        else:
            print("Error: missing definition of model: " + str(elModel) + ".")
            circuitObject.errors += 1
            basicModel = False
    # Assign basic model to element
    el.model = basicModel
    # Check parameter names and complete the list of parameters with default values
    givenParams = el.params
    allParams   = MODELS[basicModel].params
    for parName in givenParams:
        if parName not in allParams:
            circuitObject.errors += 1
            print("Error: unknown parameter '%s' for element '%s' in circuit '%s'."%(parName, el.refDes, circuitObject.title))
        elif MODELS[basicModel].params[parName] == False:
            # Laplace variable not allowed inexpression.
            if ini.Laplace in el.params[parName].atoms(sp.Symbol):
                print("Error: Laplace variable not allowed in expression of %s."%(elementNames[i]))
    for parName in list(allParams.keys()):
        if parName not in list(givenParams.keys()):
            if parName not in modelParams:
                # Assign default values to missing parameters
                if MODELS[basicModel].stamp:
                    el.params[parName] = sp.N(0)
                else:
                    el.params[parName] = SLiCAPCIRCUITS[basicModel].params[parName]
            else:
                el.params[parName] = modelParams[parName]
        else:
            el.params[parName] = givenParams[parName]
    if not MODELS[basicModel].stamp:
        # Assign the expansion circuit to the model attribute
        el.model = SLiCAPCIRCUITS[basicModel]
    circuitObject.elements[el.refDes] = el
    return circuitObject

def checkSubCircuitElementModelParams(circuitObject, el):
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
        if el.model in list(circuitObject.circuits.keys()):
            validParams = circuitObject.circuits[el.model].params
            el.model = circuitObject.circuits[el.model]
        elif el.model in list(USERCIRCUITS.keys()):
            validParams = USERCIRCUITS[el.model].params
            el.model = USERCIRCUITS[el.model]
        elif el.model in list(SLiCAPCIRCUITS.keys()):
            validParams = SLiCAPCIRCUITS[el.model].params
            el.model = SLiCAPCIRCUITS[el.model]
        else:
            print("Error: missing definition of subcircuit: " + el.model + ".")
            circuitObject.errors += 1
            el.model = False
            validParams = {}
        for parName in el.params:
            if parName not in list(validParams.keys()):
                print("Error: unknown model parameter: " + parName)
                circuitObject.errors += 1
            elif ini.Laplace in el.params[parName].atoms(sp.Symbol):
                print("Error: Laplace variable not allowed in subcircuit calls!\n  Parameter: '%s', element: `%s`, circuit: '%s'."%(parName, elementNames[i], circuitObject.title))
                circuitObject.errors += 1
    circuitObject.elements[el.refDes] = el
    return circuitObject

""" PASS 3 FUNCTIONS """

def expandCircuit(circuitObject):
    """
    This functions flattens the hierarchy of circuitObject:

    1. Sub circuits and model expansions will be expanded and connected to
       the main circuit
    2. Parameter definitions will be updated:

    :param circuitObject: SLiCAP circuit object to be expanded

    :return: SLiCAP circuit object of the expanded circuit
    :rtype: SLiCAP circuit object
    """
    elNames = list(circuitObject.elements.keys())
    for elName in elNames:
        el = circuitObject.elements[elName]
        if type(el.model) == circuit:
            parentRefDes    = el.refDes
            parentNodes     = el.nodes
            prototypeNodes  = el.model.nodes
            parentParams    = el.params
            prototypeParams = el.model.params
            parentParDefs   = circuitObject.parDefs
            # Update the parameter definitions of the parent circuit
            childParDefs  = el.model.parDefs
            circuitObject.parDefs = updateParDefs(parentParDefs, childParDefs, parentParams, prototypeParams, parentRefDes)
            for subElement in list(el.model.elements.keys()):
                newElement = deepcopy(el.model.elements[subElement])
                # Update the refDes
                newElement.refDes = el.model.elements[subElement].refDes + '_' + el.refDes
                # Update the nodes
                newElement = updateNodes(newElement, parentNodes, prototypeNodes, parentRefDes)
                # Update the parameters used in element expressions and in parameter definitions
                newElement, newParDefs = updateElementParams(newElement, parentParams, prototypeParams, parentRefDes)
                for key in list(newParDefs.keys()):
                    if key not in list(circuitObject.parDefs.keys()):
                        circuitObject.parDefs[key] = newParDefs[key]
                # Apply hierarchy
                if el.model.elements[subElement].model == circuit:
                    circuitObject = expandCircuit(el.model.elements[subElement])
                # Add the new element to the parent circuit
                circuitObject.elements[newElement.refDes] = newElement
            # Remove the parent element
            del circuitObject.elements[elName]
    return circuitObject

def updateNodes(newElement, parentNodes, prototypeNodes, parentRefDes):
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

def updateElementParams(newElement, parentParams, prototypeParams, parentRefDes):
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
        if str(parName) in list(parentParams.keys()):
            substDict[parName] = parentParams[str(parName)]
        elif str(parName) in list(prototypeParams.keys()):
            substDict[parName] = prototypeParams[str(parName)]
        elif str(parName) in list(USERPARAMS.keys()):
            newParDefs[parName] = USERPARAMS[str(parName)]

            # recursively add parameters from expression in parameter definition
            # from USERPARAMS

        elif str(parName) in list(SLiCAPPARAMS.keys()):
            newParDefs[parName] = SLiCAPPARAMS[str(parName)]

            # recursively add parameters from expression in parameter definition
            # from SLiAPPARAMS

        elif parName != ini.Laplace and parName != ini.frequency:
            substDict[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
    # Perform the full substitution in the parameter values of the element
    for parName in parNames:
        newElement.params[parName] = fullSubs(newElement.params[parName], substDict)
    return newElement, newParDefs

def updateParDefs(parentParDefs, childParDefs, parentParams, prototypeParams, parentRefDes):
    """
    The parameter definitions of the parent circuit will be updated:

    Parameters of the child circuit as well as parameters in their expressions
    will be treated as follows:

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
    # Create a list with all parameters
    allParams = list(childParDefs.keys())
    allAtoms = []
    for parName in allParams:
        allAtoms += childParDefs[parName].atoms(sp.Symbol)
    allParams = [sp.Symbol(par) for par in allParams]
    allParams += allAtoms
    substDictNames  = {}
    substDictValues = {}
    for parName in allParams:
        if parName != ini.Laplace and parName != ini.frequency:
            if str(parName) in list(parentParams.keys()):
                substDictValues[parName] = parentParams[str(parName)]
            elif str(parName) in list(prototypeParams.keys()):
                substDictValues[parName] = prototypeParams[str(parName)]
            elif str(parName) in list(USERPARAMS.keys()):
                parentParDefs = addParDefsParam(parName, parentParDefs)
            elif str(parName) in list(SLiCAPPARAMS.keys()):
                parentParDefs = addParDefsParam(parName, parentParDefs)
            else :
                substDictNames[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
                substDictValues[parName] = sp.Symbol(str(parName) + '_' + parentRefDes)
    for parName in list(childParDefs.keys()):
        """
        Add a child parameter definition to the parent parameter definitions if:
            - the parameter is not the Laplace or Fourier variable
            - the parameter is not in the prototype definition
        """
        if sp.Symbol(parName) != ini.Laplace and sp.Symbol(parName) != ini.frequency and parName not in list(prototypeParams.keys()):
            parentParDefs[fullSubs(sp.Symbol(parName), substDictNames)] = fullSubs(childParDefs[parName], substDictValues)
    return parentParDefs

def addParDefsParam(parName, parDict):
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
    if parName not in list(parDict.keys()):
        if parName in list(USERPARAMS.keys()):
            parDict[parName] = USERPARAMS[parName]
            newParams = list(USERPARAMS[parName].atoms(sp.Symbol))
            for newParam in newParams:
                addParDefsParam(newParam, parDict)
        elif parName in list(SLiCAPPARAMS.keys()):
            parDict[parName] = SLiCAPPARAMS[parName]
            newParams = list(SLiCAPPARAMS[parName].atoms(sp.Symbol))
            for newParam in newParams:
                addParDefsParam(newParam, parDict)
    return parDict

""" PASS 4 FUNCTIONS """
def sortDepVars(mainCircuit):
    """
    Sort the dependent variables. This controls the construction of the matrix
    such that the number of zero entries per column decreases from left to right.

    :param mainCircuit: Main (fully expanded) circuit object.
    :type mainCircuit: SLiCAP.protos.circuit

    :return: mainCircuit: Main circuit with updated attributes *depVars* and *varIndex*.
    :rtype: SLiCAPprotos.circuit
    """
    vGnd = []
    nGnd = []
    rGnd = []
    lGnd = []
    eGnd = []
    ezGnd = []
    gGnd = []
    tGnd = []
    hGnd = []
    hzGnd = []
    fGnd = []
    v = []
    n = []
    r = []
    l = []
    e = []
    ez = []
    f = []
    g = []
    t = []
    h = []
    hz = []
    depVars = mainCircuit.depVars
    for var in depVars:
        varType = var[0]
        if varType == 'I':
            if var[1] == '_':
                varElement = var[2:]
                model = mainCircuit.elements[varElement].model
                nodes = mainCircuit.elements[varElement].nodes
                if nodes[0] == '0' or nodes[1] == '0':
                    if model == 'V':
                        vGnd.append(var)
                    elif model == 'r':
                        rGnd.append(var)
                    elif model == 'L':
                        lGnd.append(var)
                else:
                    if model == 'V':
                        v.append(var)
                    elif model == 'r':
                        r.append(var)
                    elif model == 'L':
                        l.append(var)
            if var[2] == '_':
                varElement = var[3:]
                model = mainCircuit.elements[varElement].model
                nodes = mainCircuit.elements[varElement].nodes
                if nodes[0] == '0' or nodes[1] == '0':
                    if model == 'N':
                        nGnd.append(var)
                    elif model == 'E':
                        eGnd.append(var)
                    elif model == 'G':
                        gGnd.append(var)
                    elif model == 'T':
                        tGnd.append(var)
                    elif model == 'H':
                        hGnd.append(var)
                    elif model == 'EZ':
                        ezGnd.append(var)
                    elif model == 'HZ':
                        hzGnd.append(var)
                    elif model == 'F':
                        fGnd.append(var)
                else:
                    if model == 'N':
                        n.append(var)
                    elif model == 'E':
                        e.append(var)
                    elif model == 'G':
                        g.append(var)
                    elif model == 'T':
                        t.append(var)
                    elif model == 'H':
                        h.append(var)
                    elif model == 'EZ':
                        ez.append(var)
                    elif model == 'HZ':
                        hz.append(var)
                    elif model == 'F':
                        f.append(var)
    mainCircuit.depVars = vGnd + nGnd + rGnd + lGnd + eGnd + fGnd + gGnd + hGnd + ezGnd + hzGnd + tGnd + v + n + r + l + e + f + g + h + ez + hz + t
    mainCircuit.varIndex = {}
    varIndexPos = 0
    for i in range(len(mainCircuit.depVars)):
        mainCircuit.varIndex[mainCircuit.depVars[i]] = varIndexPos
        varIndexPos += 1
    for i in range(len(mainCircuit.nodes)):
        mainCircuit.depVars.append('V_' + mainCircuit.nodes[i])
        mainCircuit.varIndex[mainCircuit.nodes[i]] = varIndexPos
        varIndexPos += 1
    return mainCircuit

def updateCirData(circuitObject):
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
    circuitObject.depVars = []
    circuitObject.indepVars = []
    for elmt in list(circuitObject.elements.keys()):
        circuitObject.nodes += circuitObject.elements[elmt].nodes
        if circuitObject.elements[elmt].type in INDEPSCRCS:
            circuitObject.indepVars.append(elmt)
        elif circuitObject.elements[elmt].type in CONTROLLED:
            circuitObject.controlled.append(elmt)
        for i in range(len(MODELS[circuitObject.elements[elmt].model].depVars)):
            depVar = MODELS[circuitObject.elements[elmt].model].depVars[i]
            circuitObject.depVars.append(depVar + '_' + elmt)
        # Add parameters used in element expressions to circuit.params
        for par in list(circuitObject.elements[elmt].params.keys()):
            try:
                circuitObject.params += list(circuitObject.elements[elmt].params[par].atoms(sp.Symbol))
            except:
                pass
    # Add parameters used in parDef expressions to circuit.params
    for par in list(circuitObject.parDefs.keys()):
        circuitObject.params.append(par)
        circuitObject.params += list(circuitObject.parDefs[par].atoms(sp.Symbol))
    circuitObject.params = list(set(circuitObject.params))
    # Try to find required global parameter definitions for undefined params
    for par in circuitObject.params:
        if par != ini.Laplace and par != ini.frequency and par not in list(circuitObject.parDefs.keys()):
            if str(par) in list(SLiCAPPARAMS.keys()):
                circuitObject.parDefs[par] = SLiCAPPARAMS[str(par)]
                newParams = list(SLiCAPPARAMS[str(par)].atoms(sp.Symbol))
                for newParam in newParams:
                    # Parameters in the expression of a global parameter also have a global definition
                    circuitObject.parDefs[newParam] = SLiCAPPARAMS[str(newParam)]
        elif par == ini.Laplace or par == ini.frequency:
            circuitObject.params.remove(par)
    for par in circuitObject.parDefs.keys():
        if par in circuitObject.params:
            circuitObject.params.remove(par)
    # check for two connections per node (warning)
    connections = {i:circuitObject.nodes.count(i) for i in circuitObject.nodes}
    for key in list(connections.keys()):
        if connections[key] < 2:
            print("Warning less than two connections at node: '{0}'.".format(key))
    # Remove duplicate entries from node list and sort the list."
    circuitObject.nodes = list(set(circuitObject.nodes))
    circuitObject.nodes.sort()
    if '0' not in circuitObject.nodes:
        circuitObject.errors += 1
        print("Error: could not find ground node '0'.")
    nodeVoltages = ['V_' + circuitObject.nodes[i] for i in range(len(circuitObject.nodes))]
    #circuitObject.depVars = nodeVoltages + circuitObject.depVars
    circuitObject.depVars += nodeVoltages
    circuitObject = createDepVarIndex(circuitObject)
    #circuitObject = sortDepVars(circuitObject)
    return circuitObject

def createDepVarIndex(circuitObject):
    """
    Creates an index dict for the dependent variables, this easies the
    construction of the matrix.

    :param circuitObject: Circuit object to be updated
    :type circuitObject: SLiCAPprotos.circuit

    :return: SLiCAP circuit object
    :rtype: SLiCAP circuit object
    """
    circuitObject.varIndex = {}
    #varIndexPos = 0
    for i in range(len(circuitObject.depVars)):
        if circuitObject.depVars[i][0:2] == 'V_':
            circuitObject.varIndex[circuitObject.depVars[i][2:]] = i
        else:
            circuitObject.varIndex[circuitObject.depVars[i]] = i
    return circuitObject

def checkCircuit(fileName):
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
    fileName = ini.circuitPath + fileName
    print("Checking netlist:", fileName)
    # Read the netlist
    f = open(fileName, 'r')
    netlist = f.read()
    f.close()
    # Check the circuit
    # PASS 1
    parseNetlist(netlist) # Tokenize and parse the netlist to a nested circuit object
    # PASS 2

    if CIRCUITS['main'].errors == 0:
        checkReferences(CIRCUITS['main']) # Complete all data, include libraries and replace models and circuits to be expanded with thei prototype circuit
        if CIRCUITS['main'].errors == 0:
            # PASS 3
            CIRCUITS['main'] = expandCircuit(CIRCUITS['main']) # Expand subcircuits and models
            CIRCUITS['main'] = expandCircuit(CIRCUITS['main']) # Expand subcircuits and models
            # PASS 4
            CIRCUITS['main'] = updateCirData(CIRCUITS['main']) # Complete data for instructions
        if CIRCUITS['main'].errors == 0:
            ini.htmlPrefix = ('-'.join(CIRCUITS['main'].title.split()) + '_')
            ini.htmlIndex = 'index.html'
            htmlPage(CIRCUITS['main'].title, index = True)
        else:
            print("Errors found during updating of circuit data from '{0}'. Instructions with this circuit will not be executed.".format(CIRCUITS['main'].title))
    else:
        print("Found", CIRCUITS['main'].errors, "error(s).")

    return CIRCUITS['main']


def makeLibraries():
    compileSLiCAPLibraries()

if __name__ == '__main__':
    """
    Since we are not running a project, we need to define project data.
    The paths are OK with Linux
    """
    t0=time()
    compileSLiCAPLibraries()
    t1=time()

    fi = 'hierarchy.cir'
    ini.circuitPath = '/mnt/DATA/SLiCAP/SLiCAP_python_tests/basicTests/cir/'
    ini.libraryPath = '/mnt/DATA/SLiCAP/SLiCAP_python_tests/basicTests/lib/'
    ini.htmlPath    = '/mnt/DATA/SLiCAP/SLiCAP_python_tests/basicTests/html/'
    ini.htmlIndex   = 'index.html'
    ini.lastUpdate  = datetime.now()

    print("Checking:", fi)

    checkCircuit(fi)

    # Print the circuit data
    if CIRCUITS['main'].errors == 0:
        #for cirName in list(CIRCUITS.keys()):
        myCir = CIRCUITS['main']
        print("\nCircuit:", myCir.title)

        print("\nSubcircuit nodes:", myCir.nodes)

        print("\nSubcircuit parameters:")
        for param in myCir.params:
            print(param)

        print("\n Circuit elements:")
        keys = list(myCir.elements.keys())

        for key in keys:
            el = myCir.elements[key]
            print('\nElement    :', key)
            print('Nodes      :', el.nodes)
            print('Refs       :', el.refs)
            print('Model      :', el.model)
            print('Params     :')
            for par in list(el.params.keys()):
                print(' ', par, '=', el.params[par])

        print('\nCircuit parameter definitions:')
        for param in list(myCir.parDefs.keys()):
            print(' ', param, '=', myCir.parDefs[param])

        print('\nCircuit model definitions:')
        for model in list(myCir.modelDefs.keys()):
            print('\n Model name: ', myCir.modelDefs[model].name)
            print(" Model type: ", myCir.modelDefs[model].type)
            for key in myCir.modelDefs[model].params.keys():
                print("   ", key, '=', myCir.modelDefs[model].params[key])

        print('\nLibraries and include files:')
        for lib in myCir.libs:
            print(lib)

        print('\nSub circuit definitions:')
        for cir in list(myCir.circuits.keys()):
            print(cir)