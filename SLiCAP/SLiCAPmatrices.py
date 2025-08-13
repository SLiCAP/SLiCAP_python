#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module for building the MNA matrix and the associated vectors.
"""

import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import fullSubs, float2rational, normalizeRational


def _getValues(elmt, param, numeric, parDefs, substitute):
    """
    Returns the symbolic or numeric value of numerator and the denominator
    of a parameter of an element. This function is called by _makeMatrices().

    :parm elmt: element object
    :type elmt: SLiCAPprotos.element

    :param param: parameter of interest ('value', 'noise', 'dc' or 'dcvar')
    :type param: str

    :param numeric: If True is uses full substitution and sp.N for converting
                    parameters to sympy floats
    :type numeric: bool

    :param parDefs: Dict with key value pairs:

                    - key  : parameter name (sympy.Symbol)
                    - value: numeric value of sympy expression
    :type parDefs: dict

    :return: Tuple with sympy expresssions or numeric values of the numerator
             and the denominator of the element parameter.
    :return type: tuple
    """
    value = _getValue(elmt, param, numeric, parDefs, substitute)
    if ini.laplace in value.atoms(sp.Symbol):
        numer, denom = normalizeRational(value).as_numer_denom()
    else:
        numer = value
        denom = sp.Rational(1)
    return (numer, denom)


def _getValue(elmt, param, numeric, parDefs, substitute):
    """
    Returns the symbolic or numeric value of a parameter of an element.

    This function is called by _makeMatrices().

    :parm elmt: element object
    :type elmt: SLiCAPprotos.element

    :param param: parameter of interest ('value', 'noise', 'dc' or 'dcvar')
    :type param: str

    :param numeric: If True is uses full substitution and sympy.N for converting
                    parameters to sympy floats
    :type numeric: bool

    :param parDefs: Dict with key value pairs:

                    - key  : parameter name (sympy.Symbol)
                    - value: numeric value of sympy expression
    :type parDefs: dict

    :return: value: sympy expresssion or numeric value of the element parameter
    :return type: sympy.Expr, int, float, sympy.Float
    """
    try:
        if param not in list(elmt.params.keys()):
            value = None
    except:
        value = None
    if param in list(elmt.params.keys()):
        value = elmt.params[param]
        if substitute == True:
            value = float2rational(fullSubs(value, parDefs))
        if numeric == True:
            value = float2rational(sp.N(value))
    return value


def _createDepVarIndex(circuitObject):
    """
    Creates an index dict for the dependent variables, this easies the
    construction of the matrix.

    :param circuitObject: Circuit object to be updated
    :type circuitObject: SLiCAPprotos.circuit

    :return: SLiCAP circuit object
    :rtype: SLiCAP circuit object
    """
    varIndex = {}
    for i in range(len(circuitObject.dep_vars)):
        if circuitObject.dep_vars[i][0:2] == 'V_':
            varIndex[circuitObject.dep_vars[i][2:]] = i
        else:
            varIndex[circuitObject.dep_vars[i]] = i
    return varIndex


def _makeMatrices(instr):
    """
    Returns the MNA matrix and the vector with dependent variables of a circuit.
    The entries in the matrix depend on the instruction type.

    :param cir: Circuit of which the matrices need to be returned.
    :type cir: SLiCAPprotos.circuit

    :param instr: SLiCAP instruction object

                    - key  : parameter name (sympy.Symbol)
                    - value: numeric value of sympy expression

    :type instr: SLiCAPinstruction.instruction()

    :return: tuple with two sympy matrices:

             #. MNA matrix M
             #. Vector with dependent variables Dv
    :return type: tuple
    """
    cir = instr.circuit
    parDefs = instr.parDefs
    numeric = instr.numeric
    substitute = instr.substitute
    varIndex = _createDepVarIndex(cir)
    dim = len(list(varIndex.keys()))
    Dv = sp.Matrix([0 for i in range(dim)])
    M = sp.zeros(dim)
    for i in range(len(cir.dep_vars)):
        Dv[i] = sp.Symbol(cir.dep_vars[i])
    for el in list(cir.elements.keys()):
        elmt = cir.elements[el]
        if elmt.model == 'C':
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, pos0] += value * ini.laplace
            M[pos0, pos1] -= value * ini.laplace
            M[pos1, pos0] -= value * ini.laplace
            M[pos1, pos1] += value * ini.laplace
        elif elmt.model == 'L':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos0] += 1
            M[dVarPos, pos1] -= 1
            M[dVarPos, dVarPos] -= value * ini.laplace
        elif elmt.model == 'R':
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            value = float2rational(
                1/_getValue(elmt, 'value', numeric, parDefs, substitute))
            M[pos0, pos0] += value
            M[pos0, pos1] -= value
            M[pos1, pos0] -= value
            M[pos1, pos1] += value
        elif elmt.model == 'r':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos0] += 1
            M[dVarPos, pos1] -= 1
            M[dVarPos, dVarPos] -= value
        elif elmt.model == 'E':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            (numer, denom) = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos0] += denom
            M[dVarPos, pos1] -= denom
            M[dVarPos, pos2] -= numer
            M[dVarPos, pos3] += numer
        elif elmt.model == 'EZ':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            numer, denom = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            zoN, zoD = _getValues(elmt, 'zo', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos0] += denom * zoD
            M[dVarPos, pos1] -= denom * zoD
            M[dVarPos, pos2] -= numer * zoD
            M[dVarPos, pos3] += numer * zoD
            M[dVarPos, dVarPos] -= zoN * denom
        elif elmt.model == 'F':
            dVarPosO = varIndex['I_' + elmt.refDes]
            dVarPosI = varIndex['I_' + elmt.refs[0]]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            M[pos0, dVarPosO] += 1
            M[pos1, dVarPosO] -= 1
            (numer, denom) = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            M[dVarPosO, dVarPosI] -= numer
            M[dVarPosO, dVarPosO] = denom
        elif elmt.model == 'g':
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, pos2] += value
            M[pos0, pos3] -= value
            M[pos1, pos2] -= value
            M[pos1, pos3] += value
        elif elmt.model == 'G':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            (numer, denom) = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos2] += numer
            M[dVarPos, pos3] -= numer
            M[dVarPos, dVarPos] -= denom
        elif elmt.model == 'H':
            dVarPosO = varIndex['I_' + elmt.refDes]
            dVarPosI = varIndex['I_' + elmt.refs[0]]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            M[pos0, dVarPosO] += 1
            M[pos1, dVarPosO] -= 1
            (numer, denom) = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            M[dVarPosO, pos0] += denom
            M[dVarPosO, pos1] -= denom
            M[dVarPosO, dVarPosI] -= numer
        elif elmt.model == 'HZ':
            dVarPosO = varIndex['I_' + elmt.refDes]
            dVarPosI = varIndex['I_' + elmt.refs[0]]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            M[pos0, dVarPosO] += 1
            M[pos1, dVarPosO] -= 1
            (numer, denom) = _getValues(
                elmt, 'value', numeric, parDefs, substitute)
            (zoN, zoD) = _getValues(elmt, 'zo', numeric, parDefs, substitute)
            M[dVarPosO, pos0] += denom * zoD
            M[dVarPosO, pos1] -= denom * zoD
            M[dVarPosO, dVarPosI] -= numer * zoD
            M[dVarPosO, dVarPosO] -= zoN * denom
        elif elmt.model == 'N':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos2] += 1
            M[dVarPos, pos3] -= 1
        elif elmt.model == 'T':
            dVarPos = varIndex['I_' + elmt.refDes]
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[pos2, dVarPos] -= value
            M[pos3, dVarPos] += value
            M[dVarPos, pos0] += 1
            M[dVarPos, pos1] -= 1
            M[dVarPos, pos2] -= value
            M[dVarPos, pos3] += value
        elif elmt.model == 'V':
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            dVarPos = varIndex['I_' + elmt.refDes]
            M[pos0, dVarPos] += 1
            M[pos1, dVarPos] -= 1
            M[dVarPos, pos0] += 1
            M[dVarPos, pos1] -= 1
        elif elmt.model == 'W':
            pos0 = varIndex[elmt.nodes[0]]
            pos1 = varIndex[elmt.nodes[1]]
            pos2 = varIndex[elmt.nodes[2]]
            pos3 = varIndex[elmt.nodes[3]]
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            M[pos0, pos2] += value
            M[pos0, pos3] -= value
            M[pos1, pos2] -= value
            M[pos1, pos3] += value
            M[pos2, pos0] -= value
            M[pos2, pos1] += value
            M[pos3, pos0] += value
            M[pos3, pos1] -= value
        elif elmt.model == 'K':
            refPos1 = varIndex['I_' + elmt.refs[0]]
            refPos0 = varIndex['I_' + elmt.refs[1]]
            ind0 = _getValue(
                cir.elements[elmt.refs[0]], 'value', numeric, parDefs, substitute)
            ind1 = _getValue(
                cir.elements[elmt.refs[1]], 'value', numeric, parDefs, substitute)
            value = _getValue(elmt, 'value', numeric, parDefs, substitute)
            value = value * ini.laplace * sp.sqrt(ind0 * ind1)
            M[refPos0, refPos1] -= value
            M[refPos1, refPos0] -= value
    gndPos = varIndex['0']
    M.row_del(gndPos)
    M.col_del(gndPos)
    Dv = sp.Matrix(Dv)
    Dv.row_del(gndPos)
    return (M, Dv)

def _makeSrcVector(cir, parDefs, elid, value='id', numeric=True, substitute=True):
    """
    Creates the vector with independent variables.
    The vector can be created for a single independent variable or for all.

    This can be used for determination of a transfer using Cramer's rule.

    If a single variable is used, this vector and Cramer's rule can be used as
    an alternative for calculation cofactors:

    The refDes of the independent variable (source) is substituted in the vecor
    with independent variables (value = 'id'). This vector is then substituted
    in the detector col, of the MNA matrix.  After calculation of the
    determinant of this modified matrix, the result is divided by refDes.

    This method is used for determination of gain factors for noise sources
    and for DC variance sources.

    :param cir: Circuit of which the matrices need to be returned.
    :type cir: SLiCAPprotos.circuit

    :param parDefs: Dict with key value pairs:

                    - key  : parameter name (sympy.Symbol)
                    - value: numeric value of sympy expression
    :type parDefs: dict

    :param elid: Refdes (ID) of a source to be included in this vector; 'all'
                 for all sources.
    :type elid: str

    :param numeric: If True is uses full substitution and sympy.N for converting
                    parameters to sympy floats
    :type numeric: bool

    :return: Iv: vector with in dependent variables
    :return type: sympy.Matrix
    """
    # varIndex holds the position of dependent variables in the matrix.
    varIndex = _createDepVarIndex(cir)
    dim = len(list(varIndex.keys()))
    # Define the vector
    Iv = [0 for i in range(dim)]
    # Select the elements of interest
    if elid == 'all':
        elements = [cir.elements[key] for key in list(cir.elements.keys())]
    elif elid in list(cir.elements.keys()):
        elements = [cir.elements[elid]]
    for elmt in elements:
        # subsititute the element parameters of interest in the vecor Iv
        if value == 'id':
            if elid == 'all':
                val = sp.Symbol(elmt.refDes)
            else:
                val = 1
        elif value == 'value':
            val = _getValue(elmt, 'value', numeric, parDefs, substitute)
        elif value == 'noise':
            val = _getValue(elmt, 'noise', numeric, parDefs, substitute)
        elif value == 'dc':
            val = _getValue(elmt, 'dc', numeric, parDefs, substitute)
        elif value == 'dcvar':
            val = _getValue(elmt, 'dcvar', numeric, parDefs)
        if elmt.model == 'I':
            if val != None:
                pos0 = varIndex[elmt.nodes[0]]
                pos1 = varIndex[elmt.nodes[1]]
                Iv[pos0] -= val
                Iv[pos1] += val
        elif elmt.model == 'V':
            if val != None:
                dVarPos = varIndex['I_' + elmt.refDes]
                Iv[dVarPos] += val
    gndPos = varIndex['0']
    Iv = float2rational(sp.Matrix(Iv))
    Iv.row_del(gndPos)
    return Iv

def _reduceCircuit(M, Iv, Dv, source, detector, references, inductors):
    connections, deletions = _defineReductions(M, Iv, Dv, source, detector, references, inductors)
    M, Iv, Dv = _applyReductions(M, Iv, Dv, connections, deletions) 
    return M, Iv, Dv

def _defineReductions(M, Iv, Dv, source, detector, references, inductors):
    if source == None:
        source = [None, None]
    if detector == None:
        detector = [None, None]
    # Create a substitution dictionary with key-value pairs:
    # row[key], col[key] wil be added to row[value], col[value], respectively.
    connections = {}
    # Create a list with numbers of rows and columns to be deleted.
    deletions = []  
    # Create a list with numbers of rows and columns to be grounded.
    grounded  = []
    # Independent voltage sources that are not used as signal source or 
    # detector and inductors not used as current detector will be removed. 
    # Each removed component reduces the matrix size with two.
    for var in Dv:
        name = str(var)
        name_parts = name.split("_")
        vi = name_parts[0]
        elID = "_".join(name_parts[1:])
        # Test for an independent voltage source not used as signal source or 
        # (current) detector, or inductor not used as current detector.
        # Its associated dependent variable is "I_<Vname>", or "I_<Lname>". 
        # "Vname" or L<name>: refdes of voltage source or inductor, respectively.
        if elID not in source and str(name) not in detector and elID not in references:
            pos = list(Dv).index(var)
            col = list(M.col(pos))  
            if (vi == "I" and elID[0] == "V") or (vi == "I" and inductors and elID[0] == "L"):
                # Find the element's node columns
                try:
                    # col position of the positive node of the V source or inductor
                    colP = col.index(1)
                except ValueError:
                    # positive node of the element is connected to ground
                    colP = None
                try:
                    # col position of the negative node of the V source or inductor
                    colN = col.index(-1)
                except ValueError:
                    # negative node of the element is connected to ground
                    colN = None
                if colP != None and colN != None:
                    # Floating voltage source or inductor
                    if str(Dv[colP]) and str(Dv[colN]) in detector:
                        # Both nodes are detector voltage:
                        # leave it in the circuit
                        pass
                    elif str(Dv[colP]) in detector:
                        # Negative node will be replaced with detector node.
                        connections = _connect(connections, colN, colP)
                        deletions.append(colN)
                        deletions.append(pos)
                    else:   
                        # Positive node will be replaced with detector node.
                        connections = _connect(connections, colP, colN)
                        deletions.append(colP)
                        deletions.append(pos)
                if colN != None and colP == None and str(Dv[colN]) not in detector:  
                    # Negative node also needs to be connected to ground.
                    grounded.append(colN)
                    deletions.append(pos)
                elif colP != None and colN == None and str(Dv[colP]) not in detector: 
                    # Positive node also needs to be connected to ground.
                    grounded.append(colP)
                    deletions.append(pos)
    # Append row and column numbers corresponding with grounded nodes to deletions.
    for col in grounded:
        if col in connections.keys():
            deletions.append(connections[col])
            del connections[col]
        else:
            deletions.append(col)
    deletions = list(set(deletions))
    return connections, deletions

def _applyReductions(M, Iv, Dv, connections, deletions):
    # Perform connections:
    # First create a copy of the original matrix
    M   = M.copy()
    Iv  = Iv.copy()
    Dv  = Dv.copy()
    dim = M.shape[0]
    # Then perform row and column additions:
    # The substituted row or column is added to the substituting row or column,
    # respectively.
    # Also perform these additions in the vector with independent variables
    if len(connections):
        for i in range(dim):
            if i in connections.keys():
                M[connections[i], :] += M[i, :]
                M[:, connections[i]] += M[:, i]
                Iv[connections[i]]   += Iv[i]
    # Then, delete rows and columns that have been substituted or grounded
    deletions = sorted(deletions)
    i = 0
    for rc in deletions:
        M = M.minor_submatrix(rc-i, rc-i)
        Iv.row_del(rc-i)
        Dv.row_del(rc-i)
        i += 1
    return M, Iv, Dv

def _connect(connections, key, value):
    if value not in connections.keys():
        connections[key] = value
    else:
        connections[key] = connections[value]
    return connections