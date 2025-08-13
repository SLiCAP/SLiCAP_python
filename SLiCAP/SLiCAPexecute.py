#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP scripts for execution of an instruction.
"""
import sympy as sp
from copy import deepcopy
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPyacc import _updateCirData
from SLiCAP.SLiCAPprotos import element
from SLiCAP.SLiCAPmatrices import _makeMatrices, _makeSrcVector, _reduceCircuit
from SLiCAP.SLiCAPmath import float2rational, normalizeRational, det, _Roots 
from SLiCAP.SLiCAPmath import _cancelPZ, _zeroValue, ilt, assumeRealParams
from SLiCAP.SLiCAPmath import  clearAssumptions, fullSubs

def _doInstruction(instr):
    """
    Executes the instruction and returns the instr.
    
    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr = deepcopy(instr) # For compatibility with SLiCAP V3
    if instr.errors == 0:
        instr = _makeInstrParDict(instr)
        instr.clear()
        if instr.lgRef != None:
            oldLGrefElements = []
            oldVsources      = []
            inNodes          = []
            for i in range(len(instr.lgRef)):
                if instr.lgRef[i] != None:
                    if instr.gainType == 'asymptotic':
                        refType = instr.lgRef[i][0].upper()
                        if refType == "F" or refType == "H":
                            srcName = instr.circuit.elements[instr.lgRef[i]].refs[0]
                            # Check if the current through this source is used as reference in other F or H elements
                            # If so: delete "F" source, or replace "H" source with independent voltage source
                            deletions = []
                            for el in instr.circuit.elements.keys():
                                if el != instr.lgRef[i] and srcName in instr.circuit.elements[el].refs:
                                    oldLGrefElements.append(instr.circuit.elements[el])
                                    deletions.append(instr.circuit.elements[el].refDes)
                                    if instr.circuit.elements[el].type.upper() == "H":
                                        newElement = element()
                                        newElement.refDes = instr.circuit.elements[el].refDes
                                        newElement.nodes = instr.circuit.elements[el].nodes
                                        newElement.params["value"] = 0
                                        newElement.model = 'V'
                                        newElement.type = 'V'
                                        instr.circuit.elements[instr.circuit.elements[el].refDes] = newElement
                                    elif instr.circuit.elements[el].type.upper() != "F":
                                        print("ERROR: unexpected error when modifying the circuit for asymptotic-gain calculations.")
                                        instr.error += 1
                            oldVsources.append(instr.circuit.elements[srcName])
                            inNodes = instr.circuit.elements[srcName].nodes
                            deletions.append(srcName)
                            for el in deletions:
                                del instr.circuit.elements[el]
                        oldLGrefElements.append(instr.circuit.elements[instr.lgRef[i]])
                        newLGrefElement = element()
                        newLGrefElement.nodes = instr.circuit.elements[instr.lgRef[i]].nodes + inNodes
                        newLGrefElement.model = 'N'
                        newLGrefElement.type = 'N'
                        newLGrefElement.refDes = instr.circuit.elements[instr.lgRef[i]].refDes
                        instr.circuit.elements[instr.lgRef[i]] = newLGrefElement
                    elif instr.gainType == 'loopgain' or instr.gainType == 'servo' or instr.gainType == 'direct':
                        # Store the value of the loop gain reference
                        instr.lgValue[i] = instr.circuit.elements[instr.lgRef[i]].params['value']
                        if instr.gainType == 'direct':
                            instr.circuit.elements[instr.lgRef[i]].params['value'] = sp.N(0)
                        else:
                            instr.circuit.elements[instr.lgRef[i]].params['value'] = sp.Symbol("_LGREF_" + str(i+1))
                    instr.circuit = _updateCirData(instr.circuit)
        if instr.errors == 0:
            if instr.dataType == 'numer':
                instr = _doNumer(instr)
            elif instr.dataType == 'denom':
                instr = _doDenom(instr)
            elif instr.dataType == 'laplace':
                instr = _doLaplace(instr)            
            elif instr.dataType == 'poles':
                instr = _doPoles(instr)
            elif instr.dataType == 'zeros':
                instr = _doZeros(instr)
            elif instr.dataType == 'pz':
                instr = _doPZ(instr)
            elif instr.dataType == 'noise':
                instr = _doNoise(instr)
            elif instr.dataType == 'dcvar':
                instr = _doDCvar(instr)
            elif instr.dataType == 'dc':
                instr = _doDC(instr)
            elif instr.dataType == 'impulse':
                instr = _doImpulse(instr)
            elif instr.dataType == 'step':
                instr = _doStep(instr)
            elif instr.dataType == 'time':
                instr = _doTime(instr)
            elif instr.dataType == 'solve':
                instr = _doSolve(instr)
            elif instr.dataType == 'dcsolve':
                instr = _doDCsolve(instr)
            elif instr.dataType == 'timesolve':
                instr = _doTimeSolve(instr)
            elif instr.dataType == 'matrix':
                instr = _doMatrix(instr)
            elif instr.dataType == 'params':
                pass
            else:
                print('Error: unknown dataType:', instr.dataType)
        # Restore the circuit data for compatibility with SLiCAP V3
        if instr.gainType == 'asymptotic' and instr.lgRef != None:
            # Restore the original loop gain reference
            for i in range(len(oldLGrefElements)):
                instr.circuit.elements[oldLGrefElements[i].refDes] = oldLGrefElements[i]
            for vsrc in oldVsources:
                instr.circuit.elements[vsrc.refDes] = vsrc
            instr.circuit = _updateCirData(instr.circuit)
        elif instr.gainType == 'direct' or instr.gainType == 'loopgain' or instr.gainType == 'servo':
            # Restore the value of the loop gain reference
            for i in range(len(instr.lgRef)):
                if instr.lgRef[i] != None:
                    instr.circuit.elements[instr.lgRef[i]].params['value'] = instr.lgValue[i]           
    return instr

def _doNumer(instr):
    """
    Returns the numerator of a transfer function, or of the Laplace Transform
    of a detector voltage or current.

    The instr will be stored in the **.numer** attribute of the return object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                instr = _makeAllMatrices(instr)
                instr = _doPyLoopGainServo(instr)
            else:
                instr = _makeAllMatrices(instr)
                instr = _doPyNumer(instr,instr)
            numer  = instr.numer[0]
            instr.numer = _stepFunctions(instr.stepDict, numer)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    instr = _makeAllMatrices(instr)
                    instr = _doPyLoopGainServo(instr)
                else:
                    instr = _makeAllMatrices(instr)
                    instr = _doPyNumer(instr)
                instr.numer[-1] = instr.numer[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            instr = _makeAllMatrices(instr)
            instr = _doPyLoopGainServo(instr)
        else:
            instr = _makeAllMatrices(instr)
            instr = _doPyNumer(instr)
        instr.numer = instr.numer[0]
    instr = _correctDMcurrentinstr(instr)
    return instr

def _doDenom(instr):
    """
    Returns the denominator of a transfer function, or of the Laplace Transform
    of a detector voltage or current.

    The instr will be stored in the **.denom** attribute of the resturn object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                instr = _makeAllMatrices(instr)
                instr = _doPyLoopGainServo(instr)
            else:
                instr = _makeAllMatrices(instr)
                instr = _doPyDenom(instr)
            denom = instr.denom[0]
            instr.denom = _stepFunctions(instr.stepDict, denom)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.dataType == 'servo':
                    instr = _makeAllMatrices(instr)
                    instr = _doPyLoopGainServo(instr)
                else:
                    instr = _makeAllMatrices(instr)
                    instr = _doPyDenom(instr)
                instr.denom[-1] = instr.denom[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            instr = _makeAllMatrices(instr)
            instr = _doPyLoopGainServo(instr)
            instr.denom[-1] = instr.denom[-1]
        else:
            instr = _makeAllMatrices(instr)
            instr = _doPyDenom(instr)
        instr.denom = instr.denom[0]
    return instr

def _doLaplace(instr):
    """
    Returns a transfer function, or the Laplace Transform of a detector voltage or current.

    The instr will be stored in the **.laplace** attribute of the resturn object. In
    cases of parameter stepping, this attribute is a list with numerators.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                instr = _makeAllMatrices(instr)
                instr = _doPyLoopGainServo(instr)
            else:
                instr = _makeAllMatrices(instr)
                instr = _doPyLaplace(instr)
            laplaceFunc = instr.laplace[0]
            instr.laplace = _stepFunctions(instr.stepDict, laplaceFunc)
            numerFunc = instr.numer[0]
            instr.numer = _stepFunctions(instr.stepDict, numerFunc)
            denomFunc = instr.denom[0]
            instr.denom = _stepFunctions(instr.stepDict, denomFunc)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    instr = _makeAllMatrices(instr)
                    instr = _doPyLoopGainServo(instr)
                else:
                    instr = _makeAllMatrices(instr)
                    instr = _doPyLaplace(instr)
                instr.laplace[-1] = instr.laplace[-1]
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            instr = _makeAllMatrices(instr)
            instr = _doPyLoopGainServo(instr)
        else:
            instr = _makeAllMatrices(instr)
            instr = _doPyLaplace(instr)
        instr.laplace = instr.laplace[0]
        instr.numer = instr.numer[0]
        instr.denom = instr.denom[0]
    instr = _correctDMcurrentinstr(instr)
    return instr

def _doPoles(instr):
    """
    Adds the instr of a poles analysis to instr.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = "denom"
    instr.dataType = "denom"
    instr = _doDenom(instr)
    if instr.step:
        for poly in instr.denom:
            instr.poles.append(_Roots(poly, ini.laplace))
    else:
        instr.poles = _Roots(instr.denom, ini.laplace)
    instr.dataType = "poles"
    instr.dataType = "poles"
    return instr

def _doZeros(instr):
    """
    Adds the instr of a zeros analysis to instr.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = "numer"
    instr.dataType = "numer"
    instr = _doNumer(instr)
    if instr.step:
        for poly in instr.numer:
            instr.zeros.append(_Roots(poly, ini.laplace))
    else:
        instr.zeros = _Roots(instr.numer, ini.laplace)
    instr.dataType = "zeros"
    instr.dataType = "zeros"
    return instr

def _doPZ(instr):
    """
    Adds the instr of a pole-zero analysis to instr.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = "laplace"
    instr.dataType = "laplace"
    instr = _doLaplace(instr)
    if instr.step:
        for poly in instr.numer:
            instr.zeros.append(_Roots(poly, ini.laplace))
        for poly in instr.denom:
            instr.poles.append(_Roots(poly, ini.laplace))        
        for i in range(len(instr.denom)):
            try:
                instr.poles[i], instr.zeros[i] = _cancelPZ(instr.poles[i], instr.zeros[i])
            except:
                pass
            instr.DCvalue.append(_zeroValue(instr.numer[i], instr.denom[i], ini.laplace))
    else:
        instr.zeros = _Roots(instr.numer, ini.laplace)
        instr.poles = _Roots(instr.denom, ini.laplace)
        try:
            instr.poles, instr.zeros = _cancelPZ(instr.poles, instr.zeros)
        except:
            pass
        instr.DCvalue = _zeroValue(instr.numer, instr.denom, ini.laplace)
    instr.dataType = 'pz'
    instr.dataType = 'pz'
    return instr

def _doNoise(instr):
    """
    Adds the instr of a noise analysis to instr.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            noiseinstr = _doPyNoise(instr)
            instr.onoise = _stepFunctions(instr.stepDict, noiseinstr.onoise[0])
            instr.inoise = _stepFunctions(instr.stepDict, noiseinstr.inoise[0])
            for srcName in list(noiseinstr.onoiseTerms.keys()):
                instr.onoiseTerms[srcName] = _stepFunctions(instr.stepDict, noiseinstr.onoiseTerms[srcName][0])
                instr.inoiseTerms[srcName] = _stepFunctions(instr.stepDict, noiseinstr.inoiseTerms[srcName][0])
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                instr = _doPyNoise(instr)
    else:
        instr = _doPyNoise(instr)
        instr.onoise = instr.onoise[0]
        instr.inoise = instr.inoise[0]
        for key in list(instr.onoiseTerms.keys()):
            if type(instr.onoiseTerms[key]) == list and len(instr.onoiseTerms[key]) != 0 :
                instr.onoiseTerms[key] = instr.onoiseTerms[key][0]
                if instr.source != [None, None] and instr.source != None:
                    instr.inoiseTerms[key] = instr.inoiseTerms[key][0]
            else:
                del(instr.onoiseTerms[key])
                if instr.source != [None, None] and instr.source != None:
                    del(instr.inoiseTerms[key])
    instr = _correctDMcurrentinstr(instr)
    instr = _updateSRCnames(instr)
    return instr

def _doDCvar(instr):
    """
    Adds the instr of a dcvar analysis to instr.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    conv_type = instr.convType
    if instr.step:
        print("Warning: parameter stepping not (yet) tested for 'dcvar' analysis!")
        if ini.step_function:
            instr.convType = None
            instr = _makeAllMatrices(instr, reduce=False)
            instr.dataType = 'dcsolve'
            instr = _doDCsolve(instr)
            M, Iv, Dv = instr.M, instr.Iv, instr.Dv
            instr.dataType = 'dcvar'
            _addDCvarSources(instr, instr.dcSolve[0])
            instr.convType = conv_type
            varinstr = _doPyDCvar(instr)
            instr.ovar = _stepFunctions(instr.stepDict, varinstr.ovar[0])
            instr.ivar = _stepFunctions(instr.stepDict, varinstr.ivar[0])
            for srcName in list(varinstr.ovarTerms.keys()):
                instr.ovarTerms[srcName] = _stepFunctions(instr.stepDict, varinstr.ovarTerms[srcName][0])
                instr.ivarTerms[srcName] = _stepFunctions(instr.stepDict, varinstr.ivarTerms[srcName][0])
            _delDCvarSources(instr)
            if instr.convType != None:
                # Restore DC solution matrices
                instr.M  = M
                instr.Iv = Iv
                instr.Dv = Dv
                instr = _convertDCsolve(instr)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            M  = []
            Iv = []
            Dv = []
            for i in range(numSteps):
                instr.convType = None
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                instr.dataType = 'dcsolve'
                instr = _doDCsolve(instr)
                M.append(instr.M)
                Iv.append(instr.Iv)
                Dv.append(instr.Dv)
                _addDCvarSources(instr, instr.dcSolve[-1])
                instr.convType = conv_type
                instr.dataType = 'dcvar'
                instr = _doPyDCvar(instr)
                _delDCvarSources(instr)
                if instr.convType != None:
                    raise NotImplementedError("DC solution not converted to CM and DM variables with ini.stepFunction=False.")
    else:
        instr.convType = None
        #instr = _makeAllMatrices(instr, reduce=False)
        instr.dataType = 'dcsolve'
        instr = _doDCsolve(instr)
        M, Iv, Dv = instr.M, instr.Iv, instr.Dv
        _addDCvarSources(instr, instr.dcSolve)
        instr.dataType = 'dcvar'
        instr.convType = conv_type
        instr = _doPyDCvar(instr)
        instr.ovar = instr.ovar[0]
        instr.ivar = instr.ivar[0]
        for key in list(instr.ovarTerms.keys()):
            if len(instr.ovarTerms[key]) > 0:
                instr.ovarTerms[key] = instr.ovarTerms[key][0]
                if instr.source != [None, None] and instr.source != None:
                    instr.ivarTerms[key] = instr.ivarTerms[key][0]
            else:
                del(instr.ovarTerms[key])
                if instr.source != [None, None] and instr.source != None:
                    del(instr.ivarTerms[key])
        _delDCvarSources(instr)
        if instr.convType != None:
            # Restore DC solution matrices
            instr.M  = M
            instr.Iv = Iv
            instr.Dv = Dv
            instr = _convertDCsolve(instr)
    instr = _correctDMcurrentinstr(instr)
    instr = _updateSRCnames(instr)
    return instr

def _convertDCsolve(instr):
    """
    At the start of a dc variance analysis, the DC solution is calculated from 
    the original (unconverted) network. This function coverts the results of
    this dc solve instruction to the desired conversion type.
    """
    if instr.convType != None: 
        if isinstance(instr.dcSolve, sp.Basic):
            instr = _convertMatrices(instr)
            instr.dcSolve = instr.A**(-1)*instr.dcSolve
            if instr.convType == "dd" or instr.convType=="cd":
                instr.dcSolve = sp.Matrix([instr.dcSolve[i] for i in range(len(instr.Dv))])
            elif instr.convType == "dc" or instr.convType=="cc":
                instr.dcSolve = sp.Matrix([instr.dcSolve[i - len(instr.Dv)] for i in range(len(instr.Dv))])
        else:
            print("The DC solution is not converted into CM or DM variables!")
    return instr

def _correctDMcurrentinstr(instr):
    """
    In cases of a differential-mode current detector (conversion type=None), 
    the numerator of the differential output current, or its associated
    transfer must be divided by two: I_diff = (I_P - I_N)/2

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.convType == None and instr.gainType != 'loopgain' and instr.gainType != 'servo' and instr.detector != None and instr.detector[0] != None and instr.detector[1] != None:
        if instr.detector[0][0] == 'I':
            if instr.step == False:
                if instr.dataType == 'dcvar':
                    instr.ovar = instr.ovar/4
                    for term in instr.ovarTerms:
                        instr.ovarTerms[term] = instr.ovarTerms[term]/4
                elif instr.dataType == 'noise':
                    instr.onoise = instr.onoise/4
                    for term in instr.onoiseTerms:
                        instr.onoiseTerms[term] = instr.onoiseTerms[term]/4
                elif instr.dataType == 'laplace' or instr.dataType == 'dc':
                    instr.laplace = instr.laplace/2
                    instr.numer = instr.numer/2
                elif instr.dataType == 'numer':
                    instr.numer = instr.numer/2
            else:
                if instr.dataType == 'dcvar':
                    for i in range(len(instr.ovar)):
                        instr.ovar[i] = instr[i].ovar/4
                        for term in instr.ovarTerms:
                            instr.ovarTerms[term][i] = instr.ovarTerms[term][i]/4
                elif instr.dataType == 'noise':
                    for i in range(len(instr.onoise)):
                        instr.onoise[i] = instr.onoise[i]/4
                        for term in instr.onoiseTerms:
                            instr.onoiseTerms[term][i] = instr.onoiseTerms[term][i]/4
                elif instr.dataType == 'laplace' or instr.dataType == 'dc':
                    for i in range(len(instr.laplace)):
                        instr.laplace[i] = instr.laplace[i]/2
                        instr.numer[i] = instr.numer[i]/2
                elif instr.dataType == 'numer':
                    for i in range(len(instr.numer)):
                        instr.numer[i] = instr.numer[i]/2
    return instr

def _updateSRCnames(instr):
    """
    If instr.convType == "dd" or "cc" and ini.update_srcnames == True, this 
    function updates the names and values of noise and dcvar sources after a 
    doNoise() or doDcvar() instruction, respectively.
    It replaces the pair extensions with "_D", or "_C" for conversion types "dd"
    and "cc", respectively.
    These source names are the keys of the dictionaries:
    - instr.snoiseTerms
    - instr.inoiseTerms
    - instr.onoiseTerms
    - instr.svarTerms
    - instr.ivarTerms
    - instr.ovarTerms
    
    The values are the summ of the paired sources.
    
    :param instr: SLiCAP.SLiCAP.intruction object that hold the instruction
                  data and its results
    :type instr: SLiCAP.SLiCAP.intruction object
    
    :return: instruction with updated names in the above result dictionaries
    :rtype: SLiCAP.SLiCAP.intruction object
    """
    if ini.update_srcnames and (instr.convType == 'dd' or instr.convType == 'cc') and (instr.dataType == "noise" or instr.dataType == "dcvar"):
        if instr.dataType == 'noise':
            sTerms = instr.snoiseTerms
            iTerms = instr.inoiseTerms
            oTerms = instr.onoiseTerms
        elif instr.dataType=="dcvar":
            sTerms = instr.svarTerms
            iTerms = instr.ivarTerms
            oTerms = instr.ovarTerms
        srcNames = sTerms.keys()
        newSterms = {}
        newOterms = {}
        newIterms = {}
        for srcName in srcNames:
            baseName = srcName[:-1]
            if (srcName[-1] == instr.pairExt[0] and baseName + instr.pairExt[1] in srcNames) or (srcName[-1] == instr.pairExt[1] and baseName + instr.pairExt[0] in srcNames):
                if type(sTerms[srcName]) == list:
                    nsteps = len(sTerms[srcName])
                else:
                    nsteps = 0
                if instr.convType == "dd":
                    ext = "D"
                elif instr.convType == "cc":
                    ext = "C"
                vi = srcName[0].upper()
                if baseName[-1] == "_":
                    newName = baseName + ext
                else:
                    newName = baseName + "_" + ext
                if newName not in newSterms.keys():
                    if vi == "V":
                        if ext == "D":
                            if nsteps:
                                newSterms[newName] = [sTerms[baseName + instr.pairExt[0]][i] + sTerms[baseName + instr.pairExt[1]][i] for i in range(nsteps)]
                            else:
                                newSterms[newName] = sTerms[baseName + instr.pairExt[0]] + sTerms[baseName + instr.pairExt[1]]
                        elif ext == "C":
                            if nsteps:
                                newSterms[newName] = [sTerms[baseName + instr.pairExt[0]][i]/4 + sTerms[baseName + instr.pairExt[1]][i]/4 for i in range(nsteps)]
                            else:
                                newSterms[newName] = sTerms[baseName + instr.pairExt[0]]/4 + sTerms[baseName + instr.pairExt[1]]/4
                    elif vi == "I":
                        if ext == "D":
                            if nsteps:
                                newSterms[newName] = [sTerms[baseName + instr.pairExt[0]][i]/4 + sTerms[baseName + instr.pairExt[1]][i]/4 for i in range(nsteps)]
                            else:
                                newSterms[newName] = sTerms[baseName + instr.pairExt[0]]/4 + sTerms[baseName + instr.pairExt[1]]/4
                        elif ext == "C":
                            if nsteps:
                                newSterms[newName] = [sTerms[baseName + instr.pairExt[0]][i] + sTerms[baseName + instr.pairExt[1]][i] for i in range(nsteps)]
                            else:
                                newSterms[newName] = sTerms[baseName + instr.pairExt[0]] + sTerms[baseName + instr.pairExt[1]]
                    if nsteps:
                        newIterms[newName] = [iTerms[baseName + instr.pairExt[0]][i] + iTerms[baseName + instr.pairExt[1]][i] for i in range(nsteps)]
                        newOterms[newName] = [oTerms[baseName + instr.pairExt[0]][i] + oTerms[baseName + instr.pairExt[1]][i] for i in range(nsteps)]
                    else:
                        newIterms[newName] = iTerms[baseName + instr.pairExt[0]] + iTerms[baseName + instr.pairExt[1]]
                        newOterms[newName] = oTerms[baseName + instr.pairExt[0]] + oTerms[baseName + instr.pairExt[1]]
            elif instr.convType == "cc":
                # Add unpaired sources as common-mode sources
                newSterms[srcName] = sTerms[srcName]
                newIterms[srcName] = iTerms[srcName]
                newOterms[srcName] = oTerms[srcName]
        if instr.dataType == "noise":
            instr.snoiseTerms = newSterms
            instr.inoiseTerms = newIterms
            instr.onoiseTerms = newOterms
        else:
            instr.svarTerms = newSterms
            instr.ivarTerms = newIterms
            instr.ovarTerms = newOterms
    return instr

def _addDCvarSources(instr, dcSolution):
    """
    Adds the dcvar sources of resistors to instr.circuit for dataType: 'dcvar'.

    :param dcSolution: DC solution of the network obtained from execution of
                       this instruction with dataType: 'dcsolve'

    :type dcSolution: sympy.Matrix

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
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
                    errorCurrentVariance = instr.circuit.elements[el].params['dcvar'] * DCcurrent**2
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
    instr.circuit = _updateCirData(instr.circuit)
    return instr

def _delDCvarSources(instr):
    """
    Deletes the dcVar sources from instr.circuit, added by executing this
    instruction with dataType: 'dcvar'.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
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
    instr.circuit = _updateCirData(instr.circuit)
    return instr

def _addResNoiseSources(instr):
    """
    Adds the noise sources of resistors to instr.circuit for dataType: 'noise'.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
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
    # Add the global parameter k to the circuit parameter definitions
    Boltzmann = sp.Symbol('k')
    if Boltzmann not in list(instr.circuit.parDefs.keys()):
        instr.circuit.parDefs[Boltzmann] = ini.SLiCAPPARAMS['k']
    return instr

def _delResNoiseSources(instr):
    """
    Deletes the noise sources from instr.circuit, added by executing this
    instruction with dataType: 'noise'.
    
    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
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

def _doDC(instr):
    """
    Calculates the DC response at the detector using the parameter 'dc' of
    independent sources as input.

    The instr will be stored in the .dc attribute of the instr object.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                instr = _makeAllMatrices(instr, inductors=True)
                instr.Iv = instr.Iv.subs(ini.laplace, 0)
                instr.M = instr.M.subs(ini.laplace, 0)
                instr = _doPyLoopGainServo(instr)
                dcFunc = instr.laplace[0]
            else:
                instr = _makeAllMatrices(instr, inductors=True)
                instr.Iv = instr.Iv.subs(ini.laplace, 0)
                instr.M = instr.M.subs(ini.laplace, 0)
                instr = _doPyLaplace(instr)
                dcFunc = instr.laplace[0]
            instr.laplace = _stepFunctions(instr.stepDict, dcFunc)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]] = instr.stepDict[stepVars[j]][i]
                if instr.gainType == 'loopgain' or instr.gainType == 'servo':
                    instr = _makeAllMatrices(instr, inductors=True)
                    instr.Iv = instr.Iv.subs(ini.laplace, 0)
                    instr.M = instr.M.subs(ini.laplace, 0)
                    instr = _doPyLoopGainServo(instr)
                else:
                    instr = _makeAllMatrices(instr, inductors=True)
                    instr.Iv = instr.Iv.subs(ini.laplace, 0)
                    instr.M = instr.M.subs(ini.laplace, 0)
                    instr = _doPyLaplace(instr)
    else:
        if instr.gainType == 'loopgain' or instr.gainType == 'servo':
            instr = _makeAllMatrices(instr, inductors=True)
            instr.Iv = instr.Iv.subs(ini.laplace, 0)
            instr.M = instr.M.subs(ini.laplace, 0)
            instr = _doPyLoopGainServo(instr)
        else:
            instr = _makeAllMatrices(instr, inductors=True)
            instr.Iv = instr.Iv.subs(ini.laplace, 0)
            instr.M = instr.M.subs(ini.laplace, 0)
            instr = _doPyLaplace(instr)
        instr.laplace = instr.laplace[0]
        instr.numer = instr.numer[0]
        instr.denom = instr.denom[0]
    instr = _correctDMcurrentinstr(instr)
    return instr

def _doImpulse(instr):
    """
    Calculates the inverse Laplace transform of the source-detector transfer.

    First it calculates the Laplace transform of the sou-detector transfer
    and subsequently the inverse Laplace Transform.

    The Laplace Transform of the source-detector transfer will be stored in the
    .laplace attribute of the instr object.

    The instr will be stored in the .impulse attribute of the instr object.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = 'laplace'
    instr = _doLaplace(instr)
    if instr.step:
        instr.impulse = []
        for laplaceinstr in instr.laplace:
            instr.impulse.append(ilt(laplaceinstr, ini.laplace, sp.Symbol('t')))
    else:
        instr.impulse = ilt(instr.laplace, ini.laplace, sp.Symbol('t'))
    instr.dataType = 'impulse'
    return instr

def _doStep(instr):
    """
    Calculates the unit step response of the circuit. This is the inverse
    Laplace transform of the source-detector transfer divided by the Laplace
    variable.

    First it calculates the Laplace transform of the source-detector transfer
    and subsequently the inverse Laplace Transform.

    The Laplace Transform of the source-detector transfer will be stored in the
    .laplace attribute of the instr object.

    The unit step response will be stored in the .stepResp  attribute of the
    instr object.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = 'laplace'
    instr = _doLaplace(instr)
    if instr.step:
        instr.stepResp = []
        for laplaceinstr in instr.laplace:
            instr.stepResp.append(ilt(laplaceinstr, ini.laplace, sp.Symbol('t'), integrate=True))
    else:
        instr.stepResp = ilt(instr.laplace, ini.laplace, sp.Symbol('t'), integrate=True)
    instr.dataType = 'step'
    return instr

def _doTime(instr):
    """
    Calculates the inverse Laplace transform of the detector voltage or current.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr.dataType = 'laplace'
    instr = _doLaplace(instr)
    if instr.step:
        instr.time = []
        for laplaceinstr in instr.laplace:
            laplaceinstr = laplaceinstr, ini.laplace
            instr.time.append(ilt(laplaceinstr, ini.laplace, sp.Symbol('t')))
    else:
        laplaceinstr = instr.laplace
        instr.time = ilt(laplaceinstr, ini.laplace, sp.Symbol('t'))
    instr.dataType = 'time'
    instr.dataType = 'time'
    return instr

def _doSolve(instr):
    """
    Solves the network: calculates the Laplace transform of all dependent
    variables.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            instr = _makeAllMatrices(instr, reduce=False)
            sol = _doPySolve(instr).solve[0]
            instr.solve = _stepFunctions(instr.stepDict, sol)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                instr = _makeAllMatrices(instr, reduce=False)
                instr = _doPySolve(instr)
    else:
        instr = _makeAllMatrices(instr, reduce=False)
        instr.solve = _doPySolve(instr).solve[0]
    return instr

def _doDCsolve(instr):
    """
    Finds the DC solution of the network using the .dc attribute of independent
    sources as inputs.

    The DC solution will be stored in the .dcSolve attribute of the instr
    object.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    if instr.step:
        if ini.step_function:
            instr = _makeAllMatrices(instr, reduce=False)
            instr.M = instr.M.subs(ini.laplace, 0)
            instr.Iv = instr.Iv.subs(ini.laplace, 0)
            instr = _doPySolve(instr)
            sol = sp.simplify(instr.solve[-1])
            instr.dcSolve = _stepFunctions(instr.stepDict, sol)
        else:
            stepVars = list(instr.stepDict.keys())
            numSteps = len(instr.stepDict[stepVars[0]])
            for i in range(numSteps):
                for j in range(len(stepVars)):
                    instr.parDefs[stepVars[j]]=instr.stepDict[stepVars[j]][i]
                instr = _makeAllMatrices(instr, reduce=False)
                instr.M = instr.M.subs(ini.laplace, 0)
                instr.Iv = instr.Iv.subs(ini.laplace, 0)
                instr = _doPySolve(instr)
                instr.dcSolve.append(sp.simplify(instr.solve[-1]))
    else:
        instr = _makeAllMatrices(instr, reduce=False)
        instr.M = instr.M.subs(ini.laplace, 0)
        instr.Iv = instr.Iv.subs(ini.laplace, 0)
        instr = _doPySolve(instr)
        instr.dcSolve = sp.simplify(instr.solve[0])
    return instr

def _doTimeSolve(instr):
    """
    Calculates the time-domain solution of the circuit.

    The instr will be stored in the .timeSolve attribute of the instr object.

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr = _doSolve(instr)
    if instr.step:
        for solution in instr.solve:
            timeSolution = sp.zeros(len(solution), 1)
            for i in range(len(solution)):
                laplaceinstr = solution[i]
                timeSolution[i] = ilt(laplaceinstr, ini.laplace, sp.Symbol('t'))
            instr.timeSolve.append(timeSolution)
    else:
        timeSolution = sp.zeros(len(instr.solve), 1)
        for i in range(len(instr.solve)):
            laplaceinstr = instr.solve[i]
            timeSolution[i] = ilt(laplaceinstr, ini.laplace, sp.Symbol('t'))
        instr.timeSolve = timeSolution
    return instr

def _doMatrix(instr):
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

    The instrs are stored in the following attributes of the instr object:

    - .Iv: Vector with independent variables (independent voltage and current
      sources)
    - .Dv: Vector with dependent variables (nodal voltages and branch currents)
    - .M: Matrix: Iv=M*Dv

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    instr = _makeAllMatrices(instr)
    return instr

def _makeAllMatrices(instr, reduce=True, inductors=False):
    """
    Returns the instrs() object of which the following attributes have been
    updated:

        - M  = MNA matrix
        - Iv = Vector with independent variables (voltages and current of
          independent voltage and current sources, repectively)
        - Dv = Vector with dependent variables (unknown nodal voltages and
          branch currents)

    :param instr: SLiCAP instruction object that holds instruction data.
    :type instr: SLiCAPinstruction.instruction

    :return: instr of the execution of the instruction.
    :rtype: SLiCAPinstruction.instruction
    """
    # Create the MNA matrix
    instr.M, instr.Dv = _makeMatrices(instr)
    # Create vecor with independent variables
    # Iv = [0 for i in range(len(instr.depVars()))]
    Iv = [0 for i in range(instr.M.shape[0])]
    instr.Iv = sp.Matrix(Iv)
    transferTypes = ['gain', 'asymptotic', 'direct']
    
    # Create the source vector for the instruction
    if instr.gainType == 'vi':
        if instr.dataType == "noise" or instr.dataType == "dcvar":
            instr.Iv = _makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'id', numeric = instr.numeric, substitute=instr.substitute)
        elif instr.dataType == "dc" or instr.dataType == "dcsolve":
            instr.Iv = _makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'dc', numeric = instr.numeric, substitute=instr.substitute)
        else:
            instr.Iv = _makeSrcVector(instr.circuit, instr.parDefs, 'all', value = 'value', numeric = instr.numeric, substitute=instr.substitute)
    elif instr.gainType in transferTypes and instr.source != None:
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
                            instr.Iv[pos] -= 1/ns
                        else:
                            # differential input
                            instr.Iv[pos] -= (-1)**i
                    if nodeN != '0':
                        pos = instr.depVars().index('V_' + nodeN)

                        if instr.convType == 'cc' or instr.convType == 'cd':
                            instr.Iv[pos] += 1/ns
                        else:
                            # differential input
                            instr.Iv[pos] += (-1)**i
                elif instr.source[i][0].upper() == 'V':
                    pos = instr.depVars().index('I_' + instr.source[i])

                    if instr.convType == 'cc' or instr.convType == 'cd':
                        instr.Iv[pos] = 1
                    else:
                        # differential input
                        instr.Iv[pos] = ((-1)**i)/ns
    # Apply conversion type
    if instr.convType != None:
        # Adapt instr.ParDefs for balancing
        if instr.removePairSubName:
            instr = _pairParDefs(instr)
            instr = _pairParams(instr)
        # Convert the matrices
        instr = _convertMatrices(instr)
    instr.Iv = float2rational(instr.Iv)
    # If a detector is required, check it
    nodetGainTypes = ['loopgain', 'servo']
    nodetDataTypes = ['poles', 'denom', 'solve', 'dcsolve', 'timesolve']
    if instr.gainType not in nodetGainTypes or instr.dataType not in nodetDataTypes:
        detector, errors = _checkDetector(instr.detector, list(instr.Dv.transpose()))
        instr.detector = detector
        instr.circuit.errors += errors
    # Reduce the circuit
    if ini.reduce_circuit and reduce and instr.gainType != 'vi':
        instr.M, instr.Iv, instr.Dv = _reduceCircuit(instr.M, instr.Iv, instr.Dv, instr.source, instr.detector, instr.references, inductors=inductors)
    return instr
    
def _checkDetector(detector, detectors):
    """
    Check if the detector exists, this must be done after matrix conversion
    """
    errors = 0
    if type(detector) != list:
        detector = [detector, None]
    for detr in detector:
        if detr != None and sp.Symbol(detr) not in detectors:
            errors +=1
    return detector, errors
    
def _makeInstrParDict(instr):
    """
    Creates a substitution dictionary that does not contain the step parameters
    for the instruction.
    """
    if instr.substitute and ini.step_function and instr.step:
        parDefs = {}
        if not instr.ignoreCircuitParams:
            for key in list(instr.circuit.parDefs.keys()):
                if key not in list(instr.stepDict.keys()):
                    parDefs[key] = instr.circuit.parDefs[key]
        else:
            for key in list(instr.parDefs.keys()):
                if key not in list(instr.stepDict.keys()):
                    parDefs[key] = instr.circuit.parDefs[key]
        instr.parDefs = parDefs
    elif not instr.ignoreCircuitParams:
        instr.parDefs = deepcopy(instr.circuit.parDefs)
    return instr

def _stepFunctions(stepDict, function):
    """
    Substitutes values for step parameters in *function* and returns a list
    of functions with these substitutions.
    """
    stepVars = list(stepDict.keys())
    numSteps = len(stepDict[stepVars[0]])
    functions = []
    for i in range(numSteps):
        newFunction = function
        for j in range(len(stepVars)):
            newFunction = newFunction.subs(stepVars[j], stepDict[stepVars[j]][i])
        newFunction = sp.sympify(str(sp.N(newFunction)), rational=True)
        functions.append(newFunction)
    return functions

# Functions for converting the MNA matrix and the vecors with independent and
# dependent variables into equivalent common-mode and differential-mode variables.

def _pairParDefs(instr):
    """
    Removes the pair extension from paired parameters in both keys and values in
    instr.parDefs.
    """
    lenExt  = len(instr.pairExt[0])
    substDict = {}
    newParDefs = {}
    # remove pair extension of paired circuits from parameter names
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
    instr.circuit.parDefs = newParDefs
    return instr

def _pairParams(instr):
    """
    Removes the pair extension from paired parameters in instr.circuit.params.
    """
    lenExt  = len(instr.pairExt[0])
    newParams = []
    # remove pair extension of paired circuits from parameter names
    for param in instr.circuit.params:
        parName = str(param)
        if len(parName) > lenExt and parName[-lenExt:] in instr.pairExt:
            newParams.append(sp.Symbol(parName[:-lenExt]))
        else:
            newParams.append(param)
    instr.circuit.params = list(set(newParams))
    return instr

def _pairReferences(refs, pairExt, convType):
    """
    Removes the pair extension from the list with referenced circuit elements.
    """
    lenExt  = len(pairExt[0])
    for i in range(len(refs)):
        if len(refs[i]) > lenExt and refs[i][-lenExt:] in pairExt:
            ref = refs[i][:-lenExt]
            if convType == 'dd' or convType == 'dc':
                ref += '_D'
            elif convType == 'cc'or convType == 'cd':
                ref += '_C'
            refs[i] = ref
    refs = list(set(refs))
    return refs
    
def _convertMatrices(instr):
    """
    Converts the instr attributes M, Iv and Dv into those of equivalent
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

    """
    pairs, unPaired, dmVars, cmVars, A = _createConversionMatrices(instr)
    if instr.removePairSubName:
        lenExt  = len(instr.pairExt[0])
        params = list(set(list(instr.M.atoms(sp.Symbol)) + list(instr.Iv.atoms(sp.Symbol))))
        substDict = {}
        for param in params:
            parName = str(param)
            if len(parName) > lenExt:
                if parName[-lenExt:] in instr.pairExt:# and nameParts[-1][:-lenExt] in baseIDs:
                    substDict[param] = sp.Symbol(parName[:-lenExt])
        instr.M = instr.M.subs(substDict)
        
        if instr.dataType != 'noise' and instr.dataType != 'dcvar':
            instr.Iv = instr.Iv.subs(substDict)
        
    instr.Dv = sp.Matrix(dmVars + cmVars)
    instr.M  = A.transpose() * instr.M * A
    instr.Iv = A.transpose() * instr.Iv
    instr.A  = A
    dimDm = len(pairs)
    dimCm = dimDm + len(unPaired)
    instr = _getSubMatrices(instr, dimDm, dimCm, instr.convType)
    #instr.detector = instr.detector
    instr.detector = _makeNewDetector(instr, pairs, dmVars, cmVars)
    instr.references = _pairReferences(instr.circuit.references, instr.pairExt, instr.convType)
    return instr

def _createConversionMatrices(instr):
    """
    Creates the matrax for a base transformation from nodal voltages and branches
    currents to common-mode and differential-mode equivalents.
    """
    pairs, unPaired, dmVars, cmVars = _pairVariables(instr)
    depVars = [var for var in instr.depVars()]
    dim = len(depVars)
    A = sp.zeros(dim)
    n = len(pairs)
    m = len(unPaired)
    # Create conversion matrix: express nodal voltages and branch currents in
    # corresponding differential-mode and common-mode quantities.
    for i in range(n):
        row0 = depVars.index(pairs[i][0]) # nodal voltage or branch current
        row1 = depVars.index(pairs[i][1]) # nodal voltage or branch current
        if pairs[i][0][0] == 'V':
            # transform pair DM and CM voltages into node voltages
            A[row0, i] = 1/2
            A[row1, i]  = -1/2
            A[row0, i+n] = 1
            A[row1, i+n] = 1
        elif pairs[i][0][0] == 'I':
            # transform pair of DM and CM currents into branch currents
            A[row0, i] = 1
            A[row1, i]  = -1
            A[row0, i+n] = 1/2
            A[row1, i+n] = 1/2
    for i in range(m):
        # Unpaired variable, no transformation
        row = depVars.index(unPaired[i])
        col = 2*n  + i
        A[row, col] = 1
    return pairs, unPaired, dmVars, cmVars, A

def _pairVariables(instr):
    """
    Combines nodal voltages and branch currents in pairs of variables that
    can be resolved in common-mode, and differential-mode variables.

    Pairing is defined by the instr.pairedVars and instr.pairedCircuits.
    """
    depVars = [var for var in instr.circuit.dep_vars]
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
                    #_makeNewDetector(instr, [pairedVar, var], baseName)
                else:
                    unPaired.append(var)
                    depVars.remove(var)
            else:
                depVars.remove(var)
        cmVars += unPaired
    return pairs, unPaired, dmVars, cmVars

def _makeNewDetector(instr, pairs, dmVars, cmVars):
    old_detector = instr.detector
    new_detector = False
    if type(old_detector) == list:
        if len(old_detector) == 2:
            if old_detector[0] != None and old_detector[1] != None:
                extLen = len(instr.pairExt[0])
                base_P = old_detector[0][0:-extLen]
                base_N = old_detector[0][0:-extLen]
                if base_P == base_N:
                    baseName = base_P + "_"
                    if instr.convType == 'dd' or instr.convType=='cd':
                        if baseName + "D" in dmVars:
                            instr.detector = baseName + "D"
                            print("Detector changed to:", instr.detector)
                            new_detector = True
                    elif instr.convType == 'cc' or instr.convType=='dc':
                        if baseName + "C" in cmVars:
                            instr.detector = baseName + "C"
                            print("Detector changed to:", instr.detector)
                            new_detector = True
            elif old_detector[1] == None:
                # Check if detector was already modified
                if instr.convType == 'dd' or instr.convType=='cd' and old_detector[0] in dmVars:
                        new_detector = True
                elif instr.convType == 'dc' or instr.convType=='cc' and old_detector[0] in cmVars:
                        new_detector = True
    if not new_detector and instr.convType != "all" and old_detector != None:
        print("Warning: cannot create a new detector for conversion type: %s."%(instr.convType))
    return instr.detector
        
def _getSubMatrices(instr, dimDm, dimCm, convType):
    """
    Updates the attributes M, Iv, and Dv of instr according to the conversion
    type: convType.
    """
    convType = convType.lower()
    if convType == 'dd':
        instr.M  = instr.M.extract([i for i in range(0, dimDm)],[i for i in range(0, dimDm)])
        instr.Iv = sp.Matrix(instr.Iv[0: dimDm])
        instr.Dv = sp.Matrix(instr.Dv[0: dimDm])
    elif convType == 'dc':
        instr.M  = instr.M.extract([i for i in range(0, dimDm)],[i for i in range(dimDm, dimDm + dimCm)])
        instr.Iv = sp.Matrix(instr.Iv[0: dimDm])
        instr.Dv = sp.Matrix(instr.Dv[dimDm: dimDm + dimCm])
    elif convType == 'cd':
        instr.M  = instr.M.extract([i for i in range(dimDm, dimDm+dimCm)], [i for i in range(0, dimDm)])
        instr.Iv = sp.Matrix(instr.Iv[dimDm: dimDm + dimCm])
        instr.Dv = sp.Matrix(instr.Dv[0: dimDm])
    elif convType == 'cc':
        instr.M  = instr.M.extract([i for i in range(dimDm, dimDm+dimCm)], [i for i in range(dimDm, dimDm + dimCm)])
        instr.Iv = sp.Matrix(instr.Iv[dimDm: dimDm + dimCm])
        instr.Dv = sp.Matrix(instr.Dv[dimDm: dimDm + dimCm])
    elif convType == 'all':
        pass
    else:
        print("Warning: unknown conversion type: %s, assuming: 'all'."%(convType))
    return instr

#################################################################################

def _makeDetPos(instr):
    """
    Returns the index of the detector colum(s) for application of Cramer's rule.
    """
    detectors = [str(var) for var in list(instr.Dv)]
    detP, detN = instr.detector
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

def _doPyDenom(instr):
    denom = det(instr.M, method=ini.denom)
    instr.denom.append(denom)
    return instr

def _doCramer(M, rowVector, rowNumber):
    newMatrix = sp.zeros(M.rows)
    for i in range(M.rows):
        for j in range(M.cols):
            newMatrix[i,j] = M[i,j]
    newMatrix[:,rowNumber] = rowVector
    num = det(newMatrix, method=ini.numer)
    num = sp.collect(num, ini.laplace)
    return num

def _doPyNumer(instr):
    if instr.Iv.is_zero_matrix:
        instr.numer.append(sp.N(0))
    else:
        detP, detN = _makeDetPos(instr)
        num = 0
        if detP != None:
            num += _doCramer(instr.M, instr.Iv, detP)
        if detN != None:
            num -= _doCramer(instr.M, instr.Iv, detN)
        num = sp.collect(num, ini.laplace)
        instr.numer.append(num)
    return instr

def _doPyLaplace(instr):
    instr = _doPyNumer(instr)
    instr = _doPyDenom(instr)
    laplaceRational = instr.numer[-1]/instr.denom[-1]
    laplaceRational = normalizeRational(laplaceRational, ini.laplace)
    instr.laplace.append(laplaceRational)
    instr.numer[-1], instr.denom[-1] = laplaceRational.as_numer_denom()
    return instr

def _doPySolve(instr):
    instr.solve.append(instr.M.LUsolve(instr.Iv))
    return instr

def _doPyLoopGainServo(instr):
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
    if instr.substitute:
        lg1 = fullSubs(lg1, instr.parDefs)
        lg2 = fullSubs(lg2, instr.parDefs)
    if instr.numeric:
        lg1 = float2rational(sp.N(lg1))
        lg2 = float2rational(sp.N(lg2))
    _LGREF_1, _LGREF_2 = sp.symbols('_LGREF_1, _LGREF_2')
    MD = instr.M
    M0 = instr.M.subs({_LGREF_1: 0, _LGREF_2: 0})
    DM = det(MD, method=ini.denom)
    D0 = det(M0, method=ini.denom)
    LG = (D0-DM)/D0
    if instr.substitute:
        LG = fullSubs(LG, instr.parDefs)
    if instr.numeric:
        LG = float2rational(sp.N(LG))
    num, den = LG.as_numer_denom()
    LG = sp.simplify(num/den).subs({_LGREF_1: lg1, _LGREF_2: lg2})
    num, den = LG.as_numer_denom()
    if instr.gainType == 'loopgain':
        instr.laplace.append(LG)
    elif instr.gainType == 'servo':
        SVnum = - num
        SVden = sp.expand(den - num)
        num, den = SVnum, SVden
        SV = num/den
        instr.laplace.append(SV)
    instr.numer.append(num)
    instr.denom.append(den)
    return instr

def _doPyNoise(instr):
    s2f = 2*sp.pi*sp.I*sp.Symbol('f', positive=True)
    if instr.numeric == True:
        s2f = float2rational(sp.N(s2f))
    for name in instr.circuit.indepVars:
        if 'noise' in list(instr.circuit.elements[name].params.keys()):
            value = instr.circuit.elements[name].params['noise']
            if instr.substitute == True:
                value = fullSubs(value, instr.parDefs)
            if instr.numeric == True:
                value = float2rational(sp.N(value))
            instr.snoiseTerms[name] = value
    instr.gainType = 'gain'
    instr = _makeAllMatrices(instr, reduce=True, inductors=False)
    den = _doPyDenom(instr)
    den = assumeRealParams(den.denom[0].subs(ini.laplace, s2f))
    den_sq = sp.Abs(den * sp.conjugate(den))
    if instr.source != [None, None] and instr.source != None:   
        instr = _doPyNumer(instr)
        num = assumeRealParams(instr.numer[-1].subs(ini.laplace, s2f))
        if num != None:
            sl_num_sq = sp.Abs(num * sp.conjugate(num))
    instr.gainType = 'vi'
    instr.dataType = 'noise'
    instr = _makeAllMatrices(instr, reduce=False, inductors=False)
    # Save full matrices
    M_noise = instr.M
    Iv_noise = instr.Iv
    Dv_noise = instr.Dv
    onoise = 0
    inoise = 0   
    for src in instr.snoiseTerms.keys():
        if src not in instr.onoiseTerms.keys():
            instr.onoiseTerms[src] = []
            instr.inoiseTerms[src] = []
        Iv = Iv_noise
        for el in instr.snoiseTerms.keys():
            name = sp.Symbol(el)
            if el == src:
                Iv = Iv.subs(name, 1)
            else:
                Iv = Iv.subs(name, 0)
        # Modify source and source vector (reduce to single input)
        instr.Iv = Iv
        # Remove unused independent voltage sources
        if ini.reduce_circuit:
            instr.M, instr.Iv, instr.Dv = _reduceCircuit(instr.M, instr.Iv, instr.Dv, [src], instr.detector, instr.references, inductors=False)
        instr = _doPyNumer(instr)
        num = assumeRealParams(instr.numer[-1].subs(ini.laplace, s2f))
        if num != None:
            num_sq = sp.Abs(num * sp.conjugate(num))
            gain_sq = num_sq/den_sq
            onoiseTerm = instr.snoiseTerms[src]*gain_sq
            if ini.factor:
                onoiseTerm = sp.factor(onoiseTerm)
            instr.onoiseTerms[src].append(clearAssumptions(onoiseTerm))
            onoise += instr.onoiseTerms[src][-1]
            if instr.source != [None, None] and instr.source != None:
                inoiseTerm = clearAssumptions(instr.snoiseTerms[src]*num_sq/sl_num_sq)
                if ini.factor:
                    inoiseTerm = sp.factor(inoiseTerm)
                instr.inoiseTerms[src].append(inoiseTerm)
                inoise += instr.inoiseTerms[src][-1]
        # Restore full matrices
        instr.M  = M_noise
        instr.Iv = Iv_noise
        instr.Dv = Dv_noise
    instr.onoise.append(onoise)
    if inoise == 0:
        inoise = None
    instr.inoise.append(inoise)
    return instr

def _doPyDCvar(instr):
    for name in instr.circuit.indepVars:
        if 'dcvar' in list(instr.circuit.elements[name].params.keys()):
            value = instr.circuit.elements[name].params['dcvar']
            if instr.substitute == True:
                value = fullSubs(value, instr.parDefs)
            if instr.numeric == True:
                value = float2rational(sp.N(value))
            instr.svarTerms[name] = value 
    instr.gainType = 'gain'
    instr = _makeAllMatrices(instr, inductors=True)
    instr.M = instr.M.subs(ini.laplace, 0)
    den = _doPyDenom(instr).denom[0]
    den_sq = den**2
    if instr.source != [None, None] and instr.source != None:
        instr = _doPyNumer(instr)
        num = instr.numer[-1].subs(ini.laplace, 0)
        if num != None:
            sl_num_sq = num**2
    instr.gainType  = 'vi'
    instr = _makeAllMatrices(instr, reduce=False)
    M_var = instr.M.subs(ini.laplace, 0)
    Iv_var = instr.Iv.subs(ini.laplace, 0)
    Dv_var = instr.Dv
    ovar = 0
    ivar = 0
    for src in instr.svarTerms.keys():
        if src not in instr.ovarTerms.keys():
            instr.ovarTerms[src] = []
            instr.ivarTerms[src] = []
        Iv = Iv_var
        for el in instr.svarTerms.keys():
            name = sp.Symbol(el)
            if el == src:
                Iv = Iv.subs(name, 1)
            else:
                Iv = Iv.subs(name, 0)
        # Modify source and source vector (reduce to single input)
        instr.Iv = Iv
        # Remove unused independent voltage sources
        instr.M, instr.Iv, instr.Dv = _reduceCircuit(instr.M, instr.Iv, instr.Dv, [src], instr.detector, instr.references, inductors=True)
        instr = _doPyNumer(instr)
        num = instr.numer[-1]
        if num != None:
            num_sq = num**2
            gain_sq = num_sq/den_sq
            ovarTerm = instr.svarTerms[src]*gain_sq
            if ini.factor:
                ovarTerm = sp.factor(ovarTerm)
            instr.ovarTerms[src].append(ovarTerm)
            ovar += instr.ovarTerms[src][-1]
            if instr.source != [None, None] and instr.source != None:
                ivarTerm = instr.svarTerms[src]*num_sq/sl_num_sq
                if ini.factor:
                    ivarTerm = sp.factor(ivarTerm)
                instr.ivarTerms[src].append(ivarTerm)
                ivar += instr.ivarTerms[src][-1]
        # Restore full matrices
        instr.M = M_var
        instr.Iv = Iv_var
        instr.Dv = Dv_var
    instr.ovar.append(ovar)
    if ivar == 0:
        ivar = None
    instr.ivar.append(ivar)
    return instr