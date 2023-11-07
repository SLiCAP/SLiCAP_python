#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  7 17:08:41 2021

@author: anton
"""
import sympy as sp
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPyacc import updateCirData, SLiCAPPARAMS
from SLiCAP.SLiCAPprotos import element, allResults
from SLiCAP.SLiCAPmatrices import makeMatrices, makeSrcVector
from SLiCAP.SLiCAPmath import float2rational, normalizeRational, det, Roots, cancelPZ, zeroValue, ilt, assumeRealParams, clearAssumptions, fullSubs

def createResultObject(instr):
    """
    Returns an instance of the *allResults* object with the instruction data copied to it.

    :param instr: SLiCAP instruction object.
    :type instr: SLiCAPinstruction.instruction

    :return: result
    :rtype: SLiCAPprotos.allResults object
    """
    result = allResults()
    result.simType        = instr.simType
    result.gainType       = instr.gainType
    result.convType       = instr.convType
    result.dataType       = instr.dataType
    result.step           = instr.step
    result.stepVar        = instr.stepVar
    result.stepVars       = []
    if type(instr.stepVars) == list:
        # Make a deep copy of the list
        result.stepVars = [var for var in instr.stepVars]
    result.stepMethod     = instr.stepMethod
    result.stepStart      = instr.stepStart
    result.stepStop       = instr.stepStop
    result.stepNum        = instr.stepNum
    result.stepList       = []
    # Make a deep copy of the list
    result.stepList = [num for num in instr.stepList]
    result.stepArray      = []
    # Make a deep copy of the array
    for row in instr.stepArray:
        if type(row) == list:
            rowCopy = [num for num in row]
            result.stepArray.append(rowCopy)
    result.source         = instr.source
    if type(instr.detector) == list:
        # Make a deep copy of the detector list
        result.detector       = [detector for detector in instr.detector]
    else:
        result.detector = instr.detector
    result.lgRef          = instr.lgRef
    result.circuit        = instr.circuit
    result.errors         = instr.errors
    result.detUnits       = instr.detUnits
    result.detLabel       = instr.detLabel
    result.srcUnits       = instr.srcUnits
    result.numeric        = instr.numeric
    result.label          = instr.label
    result.parDefs        = None
    if instr.parDefs != None:
        result.parDefs = {}
        for key in list(instr.parDefs.keys()):
            result.parDefs[key] = instr.parDefs[key]
    return result

def makeMaxDetPos(instr, result):
    """
    Returns the index of the detector colum(s) for calculation of Cramer's rule.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResults()`

    :return: tuple: (detP, detN):

                    - detP (*int, int*): number of the row of the vector with dependent
                      variables that corresponds with the positive detector
                    - detN (*int, int*): number of the row of the vector with dependent
                      variables that corresponds with the negative detector

    :return type: tuple
    """

    detectors = [str(var) for var in list(result.Dv)]
    detP, detN = result.detector
    if detP != None:
        try:
            detP = detectors.index(detP) + 1
        except ValueError:
            print("Error: unknown detector:", detP)
            instr.errors += 1
    else:
        detP = 0
    if detN != None:
        try:
            detN = detectors.index(detN) + 1
        except ValueError:
            print("Error: unknown detector:", detN)
            instr.errors += 1
    else:
        detN = 0
    return detP, detN

def doInstruction(instr):
    """
    Executes the instruction and returns the result.


    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: Result of the execution of the instruction.
    :rtype: SLiCAPprotos.allResults()
    """
    if instr.errors == 0:
        result = createResultObject(instr)
        instr = makeSubsDict(instr)
        oldLGrefElements = []
        for i in range(len(instr.lgRef)):
            if instr.lgRef[i] != None:
                if instr.gainType == 'asymptotic':
                    oldLGrefElements.append(instr.circuit.elements[instr.lgRef[i]])
                    newLGrefElement = element()
                    newLGrefElement.nodes = oldLGrefElements[-1].nodes
                    newLGrefElement.model = 'N'
                    newLGrefElement.type = 'N'
                    newLGrefElement.refDes = oldLGrefElements[-1].refDes
                    instr.circuit.elements[instr.lgRef[i]] = newLGrefElement
                    instr.circuit = updateCirData(instr.circuit)
                elif instr.gainType == 'loopgain' or instr.gainType == 'servo' or instr.gainType == 'direct':
                    instr.lgValue[i] = instr.circuit.elements[instr.lgRef[i]].params['value']
                    if instr.gainType == 'direct':
                        instr.circuit.elements[instr.lgRef[i]].params['value'] = sp.N(0)
                    else:
                        instr.circuit.elements[instr.lgRef[i]].params['value'] = sp.Symbol("_LGREF_" + str(i+1))
        if instr.dataType == 'numer':
            result = doNumer(instr, result)
        elif instr.dataType == 'denom':
            result = doDenom(instr, result)
        elif result.dataType == 'laplace':
            result = doLaplace(instr, result)
        elif instr.dataType == 'poles':
            result = doPoles(instr, result)
        elif instr.dataType == 'zeros':
            result = doZeros(instr, result)
        elif instr.dataType == 'pz':
            result = doPZ(instr, result)
        elif instr.dataType == 'noise':
            result = doNoise(instr, result)
        elif instr.dataType == 'dcvar':
            result = doDCvar(instr, result)
        elif instr.dataType == 'dc':
            result = doDC(instr, result)
        elif instr.dataType == 'impulse':
            result = doImpulse(instr, result)
        elif instr.dataType == 'step':
            result = doStep(instr, result)
        elif instr.dataType == 'time':
            result = doTime(instr, result)
        elif instr.dataType == 'solve':
            result = doSolve(instr, result)
        elif instr.dataType == 'dcsolve':
            result = doDCsolve(instr, result)
        elif instr.dataType == 'timesolve':
            result = doTimeSolve(instr, result)
        elif instr.dataType == 'matrix':
            result = doMatrix(instr, result)
        elif instr.dataType == 'params':
            pass
        else:
            print('Error: unknown dataType:', instr.dataType)
        if instr.gainType == 'asymptotic':
            # Restore the original loop gain reference element
            for i in range(len(instr.lgRef)):
                if instr.lgRef[i] != None:
                    instr.circuit.elements[instr.lgRef[i]] = oldLGrefElements[i]
            instr.circuit = updateCirData(instr.circuit)
        elif instr.gainType == 'direct' or instr.gainType == 'loopgain' or instr.gainType == 'servo':
            for i in range(len(instr.lgRef)):
                if instr.lgRef[i] != None:
                    instr.circuit.elements[instr.lgRef[i]].params['value'] = instr.lgValue[i]
    return result

def doNumer(instr, result):
    """
    Returns the numerator of a transfer function, or of the Laplace Transform
    of a detector voltage or current.

    The result will be stored in the **.numer** attribute of the resturn object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: Result of the execution of the instruction.
    :rtype: SLiCAPprotos.allResults()
    """
    if instr.step:
        if ini.stepFunction:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                result = makeAllMatrices(instr, result)
                result = doPyLoopGainServo(instr, result)
            else:
                result = makeAllMatrices(instr, result)
                result = doPyNumer(instr,result)
            numer  = result.numer[0]
            result.numer = stepFunctions(instr.stepDict, numer)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    result = makeAllMatrices(instr, result)
                    result = doPyLoopGainServo(instr, result)
                else:
                    result = makeAllMatrices(instr, result)
                    result = doPyNumer(instr, result)
                result.numer[-1] = result.numer[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            result = makeAllMatrices(instr, result)
            result = doPyLoopGainServo(instr, result)
        else:
            result = makeAllMatrices(instr, result)
            result = doPyNumer(instr, result)
        result.numer = result.numer[0]
    result = correctDMcurrentResult(instr, result)
    return result

def doDenom(instr, result):
    """
    Returns the denominator of a transfer function, or of the Laplace Transform
    of a detector voltage or current.

    The result will be stored in the **.denom** attribute of the resturn object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: Result of the execution of the instruction.
    :rtype: SLiCAPprotos.allResults()
    """
    if instr.step:
        if ini.stepFunction:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                result = makeAllMatrices(instr, result)
                result = doPyLoopGainServo(instr, result)
            else:
                result = makeAllMatrices(instr, result)
                result = doPyDenom(result)
            denom = result.denom[0]
            result.denom = stepFunctions(instr.stepDict, denom)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.dataType == 'servo':
                    result = makeAllMatrices(instr, result)
                    result = doPyLoopGainServo(instr, result)
                else:
                    result = makeAllMatrices(instr, result)
                    result = doPyDenom(result)
                result.denom[-1] = result.denom[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            result = makeAllMatrices(instr, result)
            result = doPyLoopGainServo(instr, result)
            result.denom[-1] = result.denom[-1]
        else:
            result = makeAllMatrices(instr, result)
            result = doPyDenom(result)
        result.denom = result.denom[0]
    return result

def doLaplace(instr, result):
    """
    Returns a transfer function, or the Laplace Transform of a detector voltage or current.

    The result will be stored in the **.laplace** attribute of the resturn object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: Result of the execution of the instruction.
    :rtype: SLiCAPprotos.allResults()
    """
    if instr.step:
        if ini.stepFunction:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                result = makeAllMatrices(instr, result)
                result = doPyLoopGainServo(instr, result)
            else:
                result = makeAllMatrices(instr, result)
                result = doPyLaplace(instr, result)
            laplaceFunc = result.laplace[0]
            result.laplace = stepFunctions(instr.stepDict, laplaceFunc)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    result = makeAllMatrices(instr, result)
                    result = doPyLoopGainServo(instr, result)
                else:
                    result = makeAllMatrices(instr, result)
                    result = doPyLaplace(instr, result)
                result.laplace[-1] = result.laplace[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            result = makeAllMatrices(instr, result)
            result = doPyLoopGainServo(instr, result)
        else:
            result = makeAllMatrices(instr, result)
            result = doPyLaplace(instr, result)
        result.laplace = result.laplace[0]
        result.numer = result.numer[0]
        result.denom = result.denom[0]
    result = correctDMcurrentResult(instr, result)
    return result

def doPoles(instr, result):
    """
    Adds the result of a poles analysis to result.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    instr.dataType = "denom"
    result.dataType = "denom"
    result = doDenom(instr, result)
    if instr.step:
        for poly in result.denom:
            result.poles.append(Roots(poly, ini.Laplace))
    else:
        result.poles = Roots(result.denom, ini.Laplace)
    instr.dataType = "poles"
    result.dataType = "poles"
    return result

def doZeros(instr, result):
    """
    Adds the result of a zeros analysis to result.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    instr.dataType = "numer"
    result.dataType = "numer"
    result = doNumer(instr, result)
    if instr.step:
        for poly in result.numer:
            result.zeros.append(Roots(poly, ini.Laplace))
    else:
        result.zeros = Roots(result.numer, ini.Laplace)
    instr.dataType = "zeros"
    result.dataType = "zeros"
    return result

def doPZ(instr, result):
    """
    Adds the result of a pole-zero analysis to result.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    instr.dataType = "laplace"
    result.dataType = "laplace"
    result = doLaplace(instr, result)
    if instr.step:
        for poly in result.numer:
            result.zeros.append(Roots(poly, ini.Laplace))
        for poly in result.denom:
            result.poles.append(Roots(poly, ini.Laplace))
        for i in range(len(result.denom)):
            try:
                result.poles[i], result.zeros[i] = cancelPZ(result.poles[i], result.zeros[i])
            except:
                pass
            result.DCvalue.append(zeroValue(result.numer[i], result.denom[i]), ini.Laplace)
    else:
        result.zeros = Roots(result.numer, ini.Laplace)
        result.poles = Roots(result.denom, ini.Laplace)
        try:
            result.poles, result.zeros = cancelPZ(result.poles, result.zeros)
        except:
            pass
        result.DCvalue = zeroValue(result.numer, result.denom, ini.Laplace)
    instr.dataType = 'pz'
    result.dataType = 'pz'
    return result

def doNoise(instr, result):
    """
    Adds the result of a noise analysis to result.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    if instr.step:
        if ini.stepFunction:
            noiseResult = doPyNoise(instr, result)
            result.onoise = stepFunctions(instr.stepDict, noiseResult.onoise[0])
            result.inoise = stepFunctions(instr.stepDict, noiseResult.inoise[0])
            for srcName in list(noiseResult.onoiseTerms.keys()):
                result.onoiseTerms[srcName] = stepFunctions(instr.stepDict, noiseResult.onoiseTerms[srcName][0])
                result.inoiseTerms[srcName] = stepFunctions(instr.stepDict, noiseResult.inoiseTerms[srcName][0])
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                result = doPyNoise(instr, result)
    else:
        result = doPyNoise(instr, result)
        result.onoise = result.onoise[0]
        result.inoise = result.inoise[0]
        for key in list(result.onoiseTerms.keys()):
            if type(result.onoiseTerms[key]) == list and len(result.onoiseTerms[key]) != 0 :
                result.onoiseTerms[key] = result.onoiseTerms[key][0]
                if instr.source != [None, None]:
                    result.inoiseTerms[key] = result.inoiseTerms[key][0]
            else:
                del(result.onoiseTerms[key])
                if instr.source != [None, None]:
                    del(result.inoiseTerms[key])
    result = correctDMcurrentResult(instr, result)
    return result

def doDCvar(instr, result):
    """
    Adds the result of a dcvar analysis to result.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    if instr.step:
        print("Warning: parameter stepping not (yet) tested for 'dcvar' analysis!")
        if ini.stepFunction:
            result = makeAllMatrices(instr, result)
            instr.dataType = 'dcsolve'
            result.dataType = 'dcsolve'
            result = doDCsolve(instr, result)
            instr.dataType = 'dcvar'
            result.dataType = 'dcvar'
            addDCvarSources(instr, result.dcSolve[0])
            result = makeAllMatrices(instr, result)
            varResult = doPyDCvar(instr, result)
            result.ovar = stepFunctions(instr.stepDict, varResult.ovar[0])
            result.ivar = stepFunctions(instr.stepDict, varResult.ivar[0])
            for srcName in list(varResult.ovarTerms.keys()):
                result.ovarTerms[srcName] = stepFunctions(instr.stepDict, varResult.ovarTerms[srcName][0])
                result.ivarTerms[srcName] = stepFunctions(instr.stepDict, varResult.ivarTerms[srcName][0])
            delDCvarSources(instr)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                delDCvarSources(instr)
                instr.dataType = 'dcsolve'
                result.dataType = 'dcsolve'
                result = doDCsolve(instr, result)
                addDCvarSources(instr, result.dcSolve[-1])
                instr.dataType = 'dcvar'
                result.dataType = 'dcvar'
                result = doPyDCvar(instr, result)
                delDCvarSources(instr)
    else:
        result = makeAllMatrices(instr, result)
        result = makeAllMatrices(instr, result)
        instr.dataType = 'dcsolve'
        result.dataType = 'dcsolve'
        result = doDCsolve(instr, result)
        addDCvarSources(instr, result.dcSolve)
        instr.dataType = 'dcvar'
        result.dataType = 'dcvar'
        result = doPyDCvar(instr, result)
        result.ovar = result.ovar[0]
        result.ivar = result.ivar[0]
        for key in list(result.ovarTerms.keys()):
            if len(result.ovarTerms[key]) > 0:
                result.ovarTerms[key] = result.ovarTerms[key][0]
                if instr.source != [None, None]:
                    result.ivarTerms[key] = result.ivarTerms[key][0]
            else:
                del(result.ovarTerms[key])
                if instr.source != [None, None]:
                    del(result.ivarTerms[key])
        delDCvarSources(instr)
    result = correctDMcurrentResult(instr, result)
    delDCvarSources(instr)
    return result

def correctDMcurrentResult(instr, result):
    """
    In cases of a differential-mode current detector the numerator of the
    differential output current, or its associated transfer must be divided by
    two I_diff = (I_P - I_N)/2

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    if instr.convType == None and instr.gainType != 'loopgain' and instr.gainType != 'servo' and instr.detector[0] != None and instr.detector[1] != None:
        if instr.detector[0][0] == 'I':
            if instr.step == False:
                if instr.dataType == 'dcvar':
                    result.ovar = result.ovar/4
                    for term in result.ovarTerms:
                        result.ovarTerms[term] = result.ovarTerms[term]/4
                elif instr.dataType == 'noise':
                    result.onoise = result.onoise/4
                    for term in result.onoiseTerms:
                        result.onoiseTerms[term] = result.onoiseTerms[term]/4
                elif instr.dataType == 'laplace':
                    result.laplace = result.laplace/2
                    result.numer = result.numer/2
                elif instr.dataType == 'numer':
                    result.numer = result.numer/2
                elif instr.dataType == 'dc':
                    result.dc = result.dc/2
            else:
                if instr.dataType == 'dcvar':
                    for i in range(len(result.ovar)):
                        result.ovar[i] = result[i].ovar/4
                        for term in result.ovarTerms:
                            result.ovarTerms[term][i] = result.ovarTerms[term][i]/4
                elif instr.dataType == 'noise':
                    for i in range(len(result.onoise)):
                        result.onoise[i] = result.onoise[i]/4
                        for term in result.onoiseTerms:
                            result.onoiseTerms[term][i] = result.onoiseTerms[term][i]/4
                elif instr.dataType == 'laplace':
                    for i in range(len(result.laplace)):
                        result.laplace[i] = result.laplace[i]/2
                        result.numer[i] = result.numer[i]/2
                elif instr.dataType == 'numer':
                    for i in range(len(result.numer)):
                        result.numer[i] = result.numer[i]/2
                elif instr.dataType == 'dc':
                    for i in range(len(result.dc)):
                        result.dc[i] = result.dc[i]/2
    return result

def addDCvarSources(instr, dcSolution):
    """
    Adds the dcvar sources of resistors to instr.circuit for dataType: 'dcvar'.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param dcSolution: DC solution of the network obtained from execution of
                       this instruction with dataType: 'dcsolve'

    :type dcSolution: sympy.Matrix

    :return: updated instruction object
    :rtype: :class`SLiCAPinstruction.instruction`
    """
    newElements = {}
    for el in instr.circuit.elements.keys():
        if instr.circuit.elements[el].model.upper() == 'R' and instr.circuit.elements[el].params['value'] != 0:
            lotparnames = []
            refDes = instr.circuit.elements[el].refDes
            if 'dcvar' in instr.circuit.elements[el].params.keys():
                DCcurrent = 0
                if instr.circuit.elements[el].model == 'r':
                    pos = instr.depVars().index('I_' + refDes)
                    DCcurrent = dcSolution[pos]
                elif instr.circuit.elements[el].model == 'R':
                    nodeP, nodeN = instr.circuit.elements[el].nodes
                    if nodeP != '0':
                        posP = instr.depVars().index('V_' + nodeP)
                        Vpos = dcSolution[posP]
                    else:
                        Vpos = 0
                    if nodeN != '0':
                        posN = instr.depVars().index('V_' + nodeN)
                        Vneg = dcSolution[posN]
                    else:
                        Vneg = 0
                    DCcurrent = sp.simplify((Vpos - Vneg)/instr.circuit.elements[el].params['value'])
                if DCcurrent != 0:
                    errorCurrentVariance = instr.circuit.elements[el].params['dcvar']/instr.circuit.elements[el].params['value']**2 * DCcurrent**2
                    newCurrentSource = element()
                    newCurrentSource.refDes          = 'I_dcvar_' + refDes
                    newCurrentSource.params['dcvar'] = errorCurrentVariance
                    newCurrentSource.params['noise'] = 0
                    newCurrentSource.params['dc']    = 0
                    newCurrentSource.params['value'] = 0
                    newCurrentSource.model           = 'I'
                    newCurrentSource.type            = 'I'
                    newCurrentSource.nodes           = instr.circuit.elements[refDes].nodes
                    newElements[newCurrentSource.refDes] = newCurrentSource
                    instr.circuit.indepVars.append(newCurrentSource.refDes)
                    if 'dcvarlot' in list(instr.circuit.elements[el].params.keys()):
                        lotparname = instr.circuit.elements[el].params['dcvarlot']
                        if lotparname:
                            if lotparname in instr.circuit.parDefs.keys():
                                if lotparname not in lotparnames:
                                    lotparnames.append(lotparname)
                                    newVoltageSource = element()
                                    newVoltageSource.refDes          = 'V_dcvar_' + str(lotparname)
                                    newVoltageSource.params['dcvar'] = instr.circuit.parDefs[lotparname]
                                    newVoltageSource.params['noise'] = 0
                                    newVoltageSource.params['dc']    = 0
                                    newVoltageSource.params['value'] = 0
                                    newVoltageSource.model           = 'V'
                                    newVoltageSource.type            = 'V'
                                    newVoltageSource.nodes           = [str(lotparname), '0']
                                    newElements[newVoltageSource.refDes] = newVoltageSource
                                    instr.circuit.indepVars.append(newVoltageSource.refDes)
                                newVCCS = element()
                                newVCCS.model = 'g'
                                newVCCS.type  = 'G'
                                newVCCS.refDes = 'G_dcvar_' + refDes
                                newVCCS.nodes = instr.circuit.elements[el].nodes + newVoltageSource.nodes
                                newVCCS.params['value'] = DCcurrent
                                newElements[newVCCS.refDes] = newVCCS
                            else:
                                print("Error: unknown lot parameter:", str(lotparname))
    for el in newElements.keys():
        if el not in instr.circuit.elements.keys():
            instr.circuit.elements[el] = newElements[el]
        else:
            print("Error: name already used:", el)
    instr.circuit = updateCirData(instr.circuit)
    return instr

def delDCvarSources(instr):
    """
    Deletes the dcVar sources from instr.circuit, added by executing this
    instruction with dataType: 'dcvar'.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: updated instruction object
    :rtype: :class`SLiCAPinstruction.instruction`
    """
    names = []
    prefixes = ['I_dcvar_', 'G_dcvar_', 'V_dcvar_']
    for refDes in instr.circuit.elements.keys():
        if len(refDes) > 8:
            prefix = refDes[0:8]
            if prefix in prefixes:
                names.append(refDes)
    for name in names:
        del instr.circuit.elements[name]
    instr.circuit = updateCirData(instr.circuit)
    return instr

def addResNoiseSources(instr):
    """
    Adds the noise sources of resistors to instr.circuit for dataType: 'noise'.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: updated instruction object
    :rtype: :class:`SLiCAPinstruction.instruction`
    """
    for el in list(instr.circuit.elements.keys()):
        if instr.circuit.elements[el].model.upper() == 'R':
            params = list(instr.circuit.elements[el].params.keys())
            if 'noisetemp' in params:
                Temp = instr.circuit.elements[el].params['noisetemp']
                if Temp != False and Temp != 0 and instr.circuit.elements[el].params['value'] != 0:
                    spectrum = sp.sympify('4*k*' + str(Temp), rational=True)/instr.circuit.elements[el].params['value']
                    if 'noiseflow' in params:
                        flow = instr.circuit.elements[el].params['noiseflow']
                        if flow != False and flow != 0:
                            spectrum *= (1 + flow/ini.frequency)
                    noiseCurrent = element()
                    noiseCurrent.refDes = 'I_noise_' + instr.circuit.elements[el].refDes
                    noiseCurrent.params['noise'] = spectrum
                    noiseCurrent.params['value'] = sp.N(0)
                    noiseCurrent.params['dc']    = sp.N(0)
                    noiseCurrent.params['dcvar'] = sp.N(0)
                    noiseCurrent.model           = 'I'
                    noiseCurrent.type            = 'I'
                    noiseCurrent.nodes           = instr.circuit.elements[el].nodes
                    instr.circuit.elements[noiseCurrent.refDes] = noiseCurrent
                    instr.circuit.indepVars.append(noiseCurrent.refDes)
    # Add the global parameters k and T to the circuit parameter definitions
    Boltzmann = sp.Symbol('k')
    Temp      = sp.Symbol('T')
    if Boltzmann not in list(instr.circuit.parDefs.keys()):
        instr.circuit.parDefs[Boltzmann] = SLiCAPPARAMS['k']
    if Temp not in list(instr.circuit.parDefs.keys()):
        instr.circuit.parDefs[Boltzmann] = SLiCAPPARAMS['T']
    return instr

def delResNoiseSources(instr):
    """
    Deletes the noise sources from instr.circuit, added by executing this
    instruction with dataType: 'noise'.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: updated instruction object
    :rtype: :class:`SLiCAPinstruction.instruction`
    """
    names = []
    for i in range(len(instr.circuit.indepVars)):
        refDes = instr.circuit.indepVars[i]
        if len(refDes) > 8:
            prefix = refDes[0:8]
            if prefix == 'I_noise_':
                del instr.circuit.elements[refDes]
                names.append(refDes)
    for name in names:
        instr.circuit.indepVars.remove(name)
    return instr

def doDC(instr, result):
    """
    Calculates the DC response at the detector using the parameter 'dc' of
    independent sources as input.

    The result will be stored in the .dc attribute of the result object.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    if instr.step:
        if ini.stepFunction:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                result = makeAllMatrices(instr, result)
                result.Iv = result.Iv.subs(ini.Laplace, 0)
                result.M = result.M.subs(ini.Laplace, 0)
                result = doPyLoopGainServo(instr, result)
                dcFunc = result.laplace[0]
            else:
                result = makeAllMatrices(instr, result)
                result.Iv = result.Iv.subs(ini.Laplace, 0)
                result.M = result.M.subs(ini.Laplace, 0)
                result = doPyLaplace(instr, result)
                dcFunc = result.laplace[0]
            result.dc = stepFunctions(instr.stepDict, dcFunc)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    result = makeAllMatrices(instr, result)
                    result.Iv = result.Iv.subs(ini.Laplace, 0)
                    result.M = result.M.subs(ini.Laplace, 0)
                    result = doPyLoopGainServo(instr, result)
                else:
                    result = makeAllMatrices(instr, result)
                    result.Iv = result.Iv.subs(ini.Laplace, 0)
                    result.M = result.M.subs(ini.Laplace, 0)
                    result = doPyLaplace(instr, result)
                result.dc.append(result.laplace[-1])
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            result = makeAllMatrices(instr, result)
            result.Iv = result.Iv.subs(ini.Laplace, 0)
            result.M = result.M.subs(ini.Laplace, 0)
            result = doPyLoopGainServo(instr, result)
        else:
            result = makeAllMatrices(instr, result)
            result.Iv = result.Iv.subs(ini.Laplace, 0)
            result.M = result.M.subs(ini.Laplace, 0)
            result = doPyLaplace(instr, result)
        result.dc = result.laplace[0]
    result = correctDMcurrentResult(instr, result)
    return result

def doImpulse(instr, result):
    """
    Calculates the inverse Laplace transform of the source-detector transfer.

    First it calculates the Laplace transform of the sou-detector transfer
    and subsequently the inverse Laplace Transform.

    The Laplace Transform of the source-detector transfer will be stored in the
    .laplace attribute of the result object.

    The result will be stored in the .impulse attribute of the result object.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    instr.dataType = 'laplace'
    result.dataType = 'laplace'
    result = doLaplace(instr, result)
    if instr.step:
        result.impulse = []
        for laplaceResult in result.laplace:
            result.impulse.append(ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True), trig=True))
    else:
        result.impulse = ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True), trig=True)
    instr.dataType = 'impulse'
    result.dataType = 'impulse'
    return result

def doStep(instr, result):
    """
    Calculates the unit step response of the circuit. This is the inverse
    Laplace transform of the source-detector transfer divided by the Laplace
    variable.

    First it calculates the Laplace transform of the source-detector transfer
    and subsequently the inverse Laplace Transform.

    The Laplace Transform of the source-detector transfer will be stored in the
    .laplace attribute of the result object.

    The unit step response will be stored in the .stepResp  attribute of the
    result object.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    instr.dataType = 'laplace'
    result.dataType = 'laplace'
    result = doLaplace(instr, result)
    if instr.step:
        result.stepResp = []
        for laplaceResult in result.laplace:
            result.stepResp.append(ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True), integrate=True))
    else:
        result.stepResp = ilt(result.laplace, ini.Laplace, sp.Symbol('t', real=True), integrate=True)
    instr.dataType = 'step'
    result.dataType = 'step'
    return result

def doTime(instr, result):
    """
    Calculates the inverse Laplace transform of the detector voltage or current.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    instr.dataType = 'laplace'
    result.dataType = 'laplace'
    result = doLaplace(instr, result)
    if instr.step:
        result.time = []
        for laplaceResult in result.laplace:
            laplaceResult = laplaceResult, ini.Laplace
            result.time.append(ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True)))
    else:
        laplaceResult = result.laplace
        result.time = ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True))
    instr.dataType = 'time'
    result.dataType = 'time'
    return result

def doSolve(instr, result):
    """
    Solves the network: calculates the Laplace transform of all dependent
    variables.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    if instr.step:
        if ini.stepFunction:
            result = makeAllMatrices(instr, result)
            sol = doPySolve(instr, result).solve[0]
            result.solve = stepFunctions(instr.stepDict, sol)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                result = makeAllMatrices(instr, result)
                result = doPySolve(instr, result)
    else:
        result = makeAllMatrices(instr, result)
        result.solve = doPySolve(instr, result).solve[0]
    return result

def doDCsolve(instr, result):
    """
    Finds the DC solution of the network using the .dc attribute of independent
    sources as inputs.

    The DC solution will be stored in the .dcSolve attribute of the result
    object.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    if instr.step:
        if ini.stepFunction:
            result = makeAllMatrices(instr, result)
            result.M = result.M.subs(ini.Laplace, 0)
            result.Iv = result.Iv.subs(ini.Laplace, 0)
            result = doPySolve(instr, result)
            sol = result.solve[-1]
            result.dcSolve = stepFunctions(instr.stepDict, sol)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                result = makeAllMatrices(instr, result)
                result.M = result.M.subs(ini.Laplace, 0)
                result.Iv = result.Iv.subs(ini.Laplace, 0)
                result = doPySolve(instr, result)
                result.dcSolve.append(result.solve[-1])
    else:
        result = makeAllMatrices(instr, result)
        result.M = result.M.subs(ini.Laplace, 0)
        result.Iv = result.Iv.subs(ini.Laplace, 0)
        result = doPySolve(instr, result)
        result.dcSolve = result.solve[0]
    return result

def doTimeSolve(instr, result):
    """
    Calculates the time-domain solution of the circuit.

    The result will be stored in the .timeSolve attribute of the result object.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    result = doSolve(instr, result)
    if instr.step:
        for solution in result.solve:
            timeSolution = sp.zeros(len(solution), 1)
            for i in range(len(solution)):
                laplaceResult = solution[i]
                timeSolution[i] = ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True))
            result.timeSolve.append(timeSolution)
    else:
        timeSolution = sp.zeros(len(result.solve), 1)
        for i in range(len(result.solve)):
            laplaceResult = result.solve[i]
            timeSolution[i] = ilt(laplaceResult, ini.Laplace, sp.Symbol('t', real=True))
        result.timeSolve = timeSolution
    return result

def doMatrix(instr, result):
    """
    Calculates the MNA matrix and the vector with dependent and independent
    variables, based on the conversion type:

    - instr.convType == None: The basic MNA equation
    - instr.convType == 'all': The basic equation on a basis of common-mode and
      differential-mode variables
    - instr.convType == 'dd': The differential-mode equivalent representation
    - instr.convType == 'cc': The common-mode equivalent representation
    - instr.convType == 'cd': The differential-mode to common-mode conversion
      reprsentation
    - instr.convType == 'dc': The common-mode to differential-mode conversion
      reprsentation

    The results are stored in the following attributes of the result object:

    - .Iv: Vector with independent variables (independent voltage and current
      sources)
    - .Dv: Vector with dependent variables (nodal voltages and branch currents)
    - .M: Matrix: Iv=M*Dv

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: updated result object
    :rtype: class:`allResult()`
    """
    result = makeAllMatrices(instr, result)
    return result

def makeAllMatrices(instr, result):
    """
    Returns an allResults() object of which the following attributes have been
    updated:

        - M  = MNA matrix
        - Iv = Vector with independent variables (voltages and current of
          independent voltage and current sources, repectively)
        - Dv = Vector with dependent variables (unknown nodal voltages and
          branch currents)

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: result object with updated attributes Iv, M, and Dv:
    :rtype: SLiCAPprotos.allResults
    """
    # Create the MNA matrix
    result.M, result.Dv = makeMatrices(instr)
    # Create vecor with independent variables
    # Iv = [0 for i in range(len(instr.depVars()))]
    Iv = [0 for i in range(result.M.shape[0])]
    result.Iv = sp.Matrix(Iv)
    transferTypes = ['gain', 'asymptotic', 'direct']
    if instr.gainType == 'vi':
        if instr.dataType == "noise" or instr.dataType == "dcvar":
            result.Iv = makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'id', numeric = instr.numeric)
        elif instr.dataType == "dc" or instr.dataType == "dcsolve":
            result.Iv = makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'dc', numeric = instr.numeric)
        else:
            result.Iv = makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'value', numeric = instr.numeric)
    elif instr.gainType in transferTypes:
        if instr.source != [None, None]:
            if instr.source[0] == None or instr.source[1] == None:
                ns = 1
            else:
                ns = 2
        for i in range(len(instr.source)):
            if instr.source[i] != None:
                if instr.source[i][0].upper() == 'I':
                    nodeP, nodeN = instr.circuit.elements[instr.source[i]].nodes
                    if nodeP != '0':
                        pos = instr.depVars().index('V_' + nodeP)

                        if instr.convType == 'cc' or instr.convType == 'cd':
                            result.Iv[pos] -= 1/ns
                        else:
                            # differential input
                            result.Iv[pos] -= (-1)**i
                    if nodeN != '0':
                        pos = instr.depVars().index('V_' + nodeN)

                        if instr.convType == 'cc' or instr.convType == 'cd':
                            result.Iv[pos] += 1/ns
                        else:
                            # differential input
                            result.Iv[pos] += (-1)**i
                elif instr.source[i][0].upper() == 'V':
                    pos = instr.depVars().index('I_' + instr.source[i])

                    if instr.convType == 'cc' or instr.convType == 'cd':
                        result.Iv[pos] = 1
                    else:
                        # differential input
                        result.Iv[pos] = ((-1)**i)/ns
    if instr.convType != None:
        # Adapt instr.ParDefs for balancing
        if instr.removePairSubName:
            instr = pairParDefs(instr)
        # Convert the matrices
        result = convertMatrices(instr, result)
    result.Iv = float2rational(result.Iv)
    return result

def makeSubsDict(instr):
    """
    Creates a substitution dictionary that does not contain the step parameters
    for the instruction.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: Updated instruction object
    :rtype: :class`SLiCAPinstruction.instruction()`
    """
    if instr.numeric and ini.stepFunction and instr.step:
        instr.parDefs = {}
        for key in list(instr.circuit.parDefs.keys()):
            if key not in list(instr.stepDict.keys()):
                instr.parDefs[key] = instr.circuit.parDefs[key]
    else:
        instr.parDefs = instr.circuit.parDefs
    return instr

def stepFunctions(stepDict, function):
    """
    Substitutes values for step parameters in *function* and returns a list
    of functions with these substitutions.

    :param stepDict: Dictionary with key-value pair:
                     key: step parameter name (*sympy.Symbol*)
                     value: list with step values for this parameter.
    :type stepDict:  Dictionary
    :param function: Function in which the parameters need to be substituted
    :type function: sympy.Expr

    :return: List with functions (*sympy.Expr*). The number of
             functions equals the number of steps. Function i equals
             the input function in which the step variable has been
             replaced with its i-th step value.
    :return type: list
    """
    stepVars = list(stepDict.keys())
    numSteps = len(stepDict[stepVars[0]])
    functions = []
    for i in range(numSteps):
        for j in range(len(stepVars)):
            newFunction = function.subs(stepVars[j], stepDict[stepVars[j]][i])
        newFunction = sp.sympify(str(sp.N(newFunction)), rational=True)
        functions.append(newFunction)
    return functions

# Functions for converting the MNA matrix and the vecors with independent and
# dependent variables into equivalent common-mode and differential-mode variables.

def pairParDefs(instr):
    """
    Removes the pair extension from paired parameters in both keys and values in
    instr.parDefs.

    :param instr: instruction with circuit and pairing extensions
    :type instr: SLiCAPinstruction.instruction()

    :return: instr
    :rtupe: SLiCAPinstruction.instruction()
    """
    lenExt  = len(instr.pairExt[0])
    substDict = {}
    newParDefs = {}
    # remove subcircuit extension of paired circuits from parameter names
    for key in list(instr.parDefs.keys()):
        parName = str(key)
        if len(parName) > lenExt and parName[-lenExt:] in instr.pairExt:
            value = instr.parDefs[key]
            params = list(value.atoms(sp.Symbol))
            # remove subcircuit extension of paired circuits from parameters in expressions
            valueSubs = {}
            for param in params:
                newName = str(param)
                if len(newName) > lenExt:
                    if newName[-lenExt:] in instr.pairExt:
                        valueSubs[param] = sp.Symbol(newName[:-lenExt])
            value = value.subs(valueSubs)
            newParDefs[sp.Symbol(parName[:-lenExt])] = value

        else:
            newParDefs[key] = instr.parDefs[key]
    # perform substitutions
    for param in list(newParDefs.keys()):
        # In parameter names
        newParDefs[param] = newParDefs[param].subs(substDict)
    instr.parDefs = newParDefs
    return instr

def convertMatrices(instr, result):
    """
    Converts the result attributes M, Iv and Dv into those of equivalent
    common-mode or differential mode circuits.

    If instruction.removePairSubName == True, it also removes the pair extensions
    from paired parameters.

    The conversion type is defined by the attribute instr.convType it can be:

        - 'dd' Diferential-mode transfer
        - 'cc' Common-mode transfer
        - 'dc' Differential-mode to common-mode conversion
        - 'cd' Common-mode to differential-mode conversion
        - 'all' The complete vectors with redefined and re-arranged common-mode
          and differential-mode quantities.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`
    """
    pairs, unPaired, dmVars, cmVars, A = createConversionMatrices(instr)
    if instr.removePairSubName:
        lenExt  = len(instr.pairExt[0])
        params = list(set(list(result.M.atoms(sp.Symbol)) + list(result.Iv.atoms(sp.Symbol))))
        substDict = {}
        for param in params:
            parName = str(param)
            if len(parName) > lenExt:
                if parName[-lenExt:] in instr.pairExt:# and nameParts[-1][:-lenExt] in baseIDs:
                    substDict[param] = sp.Symbol(parName[:-lenExt])
        result.M = result.M.subs(substDict)
        if instr.dataType != 'noise' and instr.dataType != 'dcvar':
            result.Iv = result.Iv.subs(substDict)
    result.Dv = sp.Matrix(dmVars + cmVars)
    result.M  = A*result.M*A.transpose()
    result.Iv = A*result.Iv
    dimDm = len(pairs)
    dimCm = dimDm + len(unPaired)
    result = getSubMatrices(result, dimDm, dimCm, instr.convType)
    return result

def createConversionMatrices(instr):
    """
    Creates the matrax for a base transformation from nodal voltages and branches
    currents to common-mode and differential-mode equivalents.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: pairs, unPaired, dmVars, cmVars, A

             - pairs: a list with tuples with paired variables
             - unPaired: a list with unpaired variables
             - dmVars: a list with differential-mode variables
             - cmVars: a list with common mode variables
             - A: the base transformation matrix

    :rtype: tuple
    """
    pairs, unPaired, dmVars, cmVars = pairVariables(instr)
    depVars = [var for var in instr.depVars()]
    dim = len(depVars)
    A = sp.zeros(dim)
    n = len(pairs)
    m = len(unPaired)
    # Create conversion matrix: express nodal voltages and branch currents in
    # corresponding differential-mode and common-mode quantities.
    for i in range(n):
        col0 = depVars.index(pairs[i][0]) # nodal voltage or branch current
        col1 = depVars.index(pairs[i][1]) # nodal voltage or branch current
        if pairs[i][0][0] == 'V':
            # transform pair of node voltages into DM and CM node voltage
            A[i, col0] = 1/2
            A[i, col1]  = -1/2
            A[i+n, col0] = 1
            A[i+n, col1] = 1
        elif pairs[i][0][0] == 'I':
            # transform pair of branch currents into DM and CM branch current
            A[i, col0] = 1
            A[i, col1]  = -1
            A[i+n, col0] = 1/2
            A[i+n, col1] = 1/2
    for i in range(m):
        # Unpaired variable, no transformation
        col = depVars.index(unPaired[i])
        row = 2*n  + i
        A[row, col] = 1
    return pairs, unPaired, dmVars, cmVars, A

def pairVariables(instr):
    """
    Combines nodal voltages and branch currents in pairs of variables that
    can be resolved in common-mode, and differential-mode variables.

    Pairing is defined by the instr.pairedVars and instr.pairedCircuits.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :return: pairs, unPaired, dmVars, cmVars

             - pairs: a list with tuples with paired variables
             - unPaired: a list with unpaired variables
             - dmVars: a list with differential-mode variables
             - cmVars: a list with common mode variables

    :rtype: tuple
    """
    depVars = [var for var in instr.circuit.depVars]
    paired = []
    pairs = []
    unPaired = []
    dmVars = []
    cmVars = []
    sub1, sub2 = instr.pairExt
    if sub1 != None and sub2 != None:
        l_sub1 = len(sub1)
        l_sub2 = len(sub2)
        while len(depVars) != 0:
            var = depVars[0]
            if var != 'V_0':
                paired = False
                if var[-l_sub1:] == sub1:
                    pairedVar = var[0:-l_sub1] + sub2
                    if pairedVar in depVars:
                        paired = True
                        pairs.append((var, pairedVar))
                elif var[-l_sub2:] == sub2:
                    pairedVar = var[0:-l_sub2] + sub1
                    if pairedVar in depVars:
                        paired = True
                        pairs.append((pairedVar, var))
                if paired:
                    depVars.remove(var)
                    depVars.remove(pairedVar)
                    if pairs[-1][0][-l_sub1:] == sub1:
                        baseName = pairs[-1][0][0: -l_sub1]
                    if baseName[-1] != '_':
                        baseName += '_'
                    dmVars.append(baseName + 'D')
                    cmVars.append(baseName + 'C')
                else:
                    unPaired.append(var)
                    depVars.remove(var)
            else:
                depVars.remove(var)
        cmVars += unPaired
    return pairs, unPaired, dmVars, cmVars

def getSubMatrices(result, dimDm, dimCm, convType):
    """
    Updates the attributes M, Iv, and Dv of result according to the conversion
    type: convType.

    :param result: instruction results of which the matrix attributes M, Iv,
                   and Dv have been set.

    :param dimDm: Number of differential-mode variables
    :type dimDm: str

    :param dimCm: Number of common-mode variables
    :type dimCm: str

    :param convType: Conversion type, can be 'dd', 'dc', 'cd', 'cc' and 'all'.
    :type convType: str

    :result: updated instruction result
    :rtype: :class: SLiCAP.allResults()
    """
    convType = convType.lower()
    if convType == 'dd':
        result.M  = result.M.extract([i for i in range(0, dimDm)],[i for i in range(0, dimDm)])
        result.Iv = sp.Matrix(result.Iv[0:dimDm])
        result.Dv = sp.Matrix(result.Dv[0:dimDm])
    elif convType == 'dc':
        result.M  = result.M.extract([i for i in range(0,dimDm)],[i for i in range(dimDm, dimDm+dimCm)])
        result.Iv = sp.Matrix(result.Iv[0:dimDm])
        result.Dv = sp.Matrix(result.Dv[dimDm:dimDm+dimCm])
    elif convType == 'cd':
        result.M  = result.M.extract([i for i in range(dimDm, dimDm+dimCm)], [i for i in range(0,dimDm)])
        result.Iv = sp.Matrix(result.Iv[dimDm:dimDm+dimCm])
        result.Dv = sp.Matrix(result.Dv[0:dimDm])
    elif convType == 'cc':
        result.M  = result.M.extract([i for i in range(dimDm, dimDm+dimCm)], [i for i in range(dimDm, dimDm+dimCm)])
        result.Iv = sp.Matrix(result.Iv[dimDm:dimDm+dimCm])
        result.Dv = sp.Matrix(result.Dv[dimDm:dimDm+dimCm])
    elif convType == 'all':
        pass
    else:
        print("Warning: unknown conversion type: %s, assuming: 'all'."%(convType))
    return result

#################################################################################

def makeDetPos(result):
    """
    Returns the index of the detector colum(s) for calculation of Cramer's rule.

    :param instr: **instruction()** object that holds instruction data.
    :type instr: :class:`instruction()`

    :param result: **allResults()** object that holds instruction results
    :type result: :class:`allResult()`

    :return: tuple: (detP, detN):

                    - detP (int or None, int or None): number of the row of the vector with dependent
                      variables that corresponds with the positive detector
                    - detN (int or None, int or None): number of the row of the vector with dependent
                      variables that corresponds with the negative detector

    :return type: tuple
    """

    detectors = [str(var) for var in list(result.Dv)]
    detP, detN = result.detector
    if detP != None:
        try:
            detP = detectors.index(detP)
        except ValueError:
            print("Error: unknown detector:", detP)
    if detN != None:
        try:
            detN = detectors.index(detN)
        except ValueError:
            print("Error: unknown detector:", detN)
    return detP, detN

def doPyDenom(result):
    denom = det(result.M, method=ini.denom)
    result.denom.append(denom)
    return result

def doCramer(M, rowVector, rowNumber):
    newMatrix = sp.zeros(M.rows)
    for i in range(M.rows):
        for j in range(M.cols):
            newMatrix[i,j] = M[i,j]
    newMatrix[:,rowNumber] = rowVector
    num = det(newMatrix, method=ini.numer)
    num = sp.collect(num, ini.Laplace)
    return num

def doPyNumer(instr, result):
    detP, detN = makeDetPos(result)
    num = 0
    if detP != None:
        num += doCramer(result.M, result.Iv, detP)
    if detN != None:
        num -= doCramer(result.M, result.Iv, detN)
    num = sp.collect(num, ini.Laplace)
    result.numer.append(num)
    return result

def doPyLaplace(instr, result):
    result = doPyNumer(instr, result)
    result = doPyDenom(result)
    laplaceRational = result.numer[-1]/result.denom[-1]
    laplaceRational = normalizeRational(laplaceRational, ini.Laplace)
    result.laplace.append(laplaceRational)
    result.numer[-1], result.denom[-1] = laplaceRational.as_numer_denom()
    return result

def doPySolve(instr, result):
    result.solve.append(result.M.LUsolve(result.Iv))
    return result

def doPyLoopGainServo(instr, result):
    result = makeAllMatrices(instr, result)
    if instr.lgValue[0] != None:
        lg1 = instr.lgValue[0]
    else:
        lg1 = sp.N(0)
    if instr.lgValue[1] != None:
        lg2 = instr.lgValue[1]
    else:
        lg2 = sp.N(0)
    if instr.convType !=None and instr.removePairSubName:
        lenExt  = len(instr.pairExt[0])
        params = list(set(list(lg1.atoms(sp.Symbol)) + list(lg2.atoms(sp.Symbol))))
        substDict = {}
        for param in params:
            parName = str(param)
            if len(parName) > lenExt:
                if parName[-lenExt:] in instr.pairExt:
                    substDict[param] = sp.Symbol(parName[:-lenExt])
        lg1 = lg1.subs(substDict)
        lg2 = lg2.subs(substDict)
    if instr.numeric:
        lg1 = fullSubs(lg1, instr.parDefs)
        lg2 = fullSubs(lg2, instr.parDefs)
    _LGREF_1, _LGREF_2 = sp.symbols('_LGREF_1, _LGREF_2')
    MD = result.M
    M0 = result.M.subs({_LGREF_1: 0, _LGREF_2: 0})
    DM = det(MD, method=ini.denom)
    D0 = det(M0, method=ini.denom)
    LG = (D0-DM)/D0
    if instr.numeric:
        LG = fullSubs(LG, instr.parDefs)
    num, den = LG.as_numer_denom()
    LG = normalizeRational(num/den, ini.Laplace).subs({_LGREF_1: lg1, _LGREF_2: lg2})
    num, den = LG.as_numer_denom()
    if instr.gainType == 'loopgain':
        result.laplace.append(LG)
    elif instr.gainType == 'servo':
        num = - num
        den = sp.expand(den - num)
        SV = num/den
        result.laplace.append(SV)
    #num, den = result.laplace[-1].as_numer_denom()
    result.numer.append(num)
    result.denom.append(den)
    return result

def doPyNoise(instr, result):
    """
    Attribute numer rewriten or appended?! Check with stepping.
    """
    s2f = 2*sp.pi*sp.I*ini.frequency
    for name in instr.circuit.indepVars:
        if 'noise' in list(instr.circuit.elements[name].params.keys()):
            value = instr.circuit.elements[name].params['noise']
            if instr.numeric == True:
                value = float2rational(fullSubs(value, instr.parDefs))
            result.snoiseTerms[name] = value
    result = makeAllMatrices(instr, result)
    Iv_noise = result.Iv
    den = doPyDenom(result).denom[0].subs(ini.Laplace, s2f)
    den = assumeRealParams(den)
    re_den, im_den = den.as_real_imag()
    den_sq = re_den**2 + im_den**2
    if instr.source != [None, None]:
        instr.gainType = 'gain'
        result.gainType = 'gain'
        result = makeAllMatrices(instr, result)
        result = doPyNumer(instr, result)
        num = result.numer[-1].subs(ini.Laplace, s2f)
        if num != None:
            num = assumeRealParams(num)
            re_num, im_num = num.as_real_imag()
            sl_num_sq = re_num**2 + im_num**2
        instr.gainType = 'vi'
        result.gainType = 'vi'
    onoise = 0
    inoise = 0
    for src in result.snoiseTerms.keys():
        if src not in result.onoiseTerms.keys():
            result.onoiseTerms[src] = []
            result.inoiseTerms[src] = []
        Iv = Iv_noise
        for el in result.snoiseTerms.keys():
            name = sp.Symbol(el)
            if el == src:
                Iv = Iv.subs(name, 1)
            else:
                Iv = Iv.subs(name, 0)
        result.Iv = Iv
        result = doPyNumer(instr, result)
        num = result.numer[-1].subs(ini.Laplace, s2f)
        if num != None:
            num = assumeRealParams(num)
            re_num, im_num = num.as_real_imag()
            num_sq = re_num**2 + im_num**2
            gain_sq = num_sq/den_sq
            onoiseTerm = result.snoiseTerms[src]*gain_sq
            if ini.factor:
                onoiseTerm = sp.factor(onoiseTerm)
            result.onoiseTerms[src].append(clearAssumptions(onoiseTerm))
            onoise += result.onoiseTerms[src][-1]
            if instr.source != [None, None]:
                inoiseTerm = result.snoiseTerms[src]*num_sq/sl_num_sq
                if ini.factor:
                    inoiseTerm = sp.factor(inoiseTerm)
                result.inoiseTerms[src].append(clearAssumptions(inoiseTerm))
                inoise += result.inoiseTerms[src][-1]
    result.onoise.append(onoise)
    if inoise == 0:
        inoise = None
    result.inoise.append(inoise)
    return result

def doPyDCvar(instr, result):
    """
    Attribute numer rewriten or appended?! Check with stepping.
    """
    instr.dataType='dcvar'
    result.dataType='dcvar'
    for name in instr.circuit.indepVars:
        if 'dcvar' in list(instr.circuit.elements[name].params.keys()):
            value = instr.circuit.elements[name].params['dcvar']
            if instr.numeric == True:
                value = float2rational(fullSubs(value, instr.parDefs))
            result.svarTerms[name] = value
    result = makeAllMatrices(instr, result)
    result.M = result.M.subs(ini.Laplace, 0)
    Iv_var = result.Iv
    den = doPyDenom(result).denom[0]
    den_sq = den**2
    if instr.source != [None, None]:
        instr.gainType = 'gain'
        result.gainType = 'gain'
        result = makeAllMatrices(instr, result)
        Iv_gain = result.Iv
        result.Iv = Iv_gain
        result = doPyNumer(instr, result)
        num = result.numer[-1]
        if num != None:
            sl_num_sq = num**2
        instr.gainType = 'vi'
        result.gainType = 'vi'
    ovar = 0
    ivar = 0
    for src in result.svarTerms.keys():
        if src not in result.ovarTerms.keys():
            result.ovarTerms[src] = []
            result.ivarTerms[src] = []
        Iv = Iv_var
        for el in result.svarTerms.keys():
            name = sp.Symbol(el)
            if el == src:
                Iv = Iv.subs(name, 1)
            else:
                Iv = Iv.subs(name, 0)
        result.Iv = Iv
        result = doPyNumer(instr, result)
        num = result.numer[-1]
        if num != None:
            num_sq = num**2
            gain_sq = num_sq/den_sq
            ovarTerm = result.svarTerms[src]*gain_sq
            if ini.factor:
                ovarTerm = sp.factor(ovarTerm)
            result.ovarTerms[src].append(ovarTerm)
            ovar += result.ovarTerms[src][-1]
            if instr.source != [None, None]:
                ivarTerm = result.svarTerms[src]*num_sq/sl_num_sq
                if ini.factor:
                    ivarTerm = sp.factor(ivarTerm)
                result.ivarTerms[src].append(ivarTerm)
                ivar += result.ivarTerms[src][-1]
    result.ovar.append(ovar)
    if ivar == 0:
        ivar = None
    result.ivar.append(ivar)
    return result
