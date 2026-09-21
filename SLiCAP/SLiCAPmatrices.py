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
    names = list(cir.dep_vars)
    # method 'state': controlled sources with a Laplace rational transfer are
    # expanded into an integrator chain (book: "Matrix stamps of expanded
    # transfer functions"), so that M is first order in s. The chain is sized
    # HERE, after parameter substitution: a time constant that is zero drops
    # the order, and an integrator kept for a vanished coefficient would be a
    # state without a pole (Anton/Claude, 2026-09-09, PZ.md addendum E).
    chains = {}          # chain key -> (a, b, columns)
    expanded = {}        # refDes -> {"av": key|None, "zo": (kind, key|value)}
    if getattr(instr, "method", "det") == "state":

        def _coeffs(numer, denom):
            a = sp.Poly(denom, ini.laplace).all_coeffs()          # highest first
            b = sp.Poly(numer, ini.laplace).all_coeffs()
            return a, [0]*(len(a) - len(b)) + b

        def _newChain(key, a, b, tag):
            cols = []
            for i in range(len(a)):
                cols.append(len(names))
                names.append("V_%d_%s" % (i, tag))
            chains[key] = (a, b, cols)
            return key

        for el in list(cir.elements.keys()):
            elmt = cir.elements[el]
            # Model 'g' is not expanded: its value may not contain the
            # Laplace variable (SLiCAPprotos: {'value': False}), the parser
            # rejects it. A 'g' branch here was dead code and was REMOVED
            # (Anton, 2026-09-15).
            if elmt.model not in ('E', 'F', 'G', 'H', 'EZ', 'HZ'):
                continue
            numer, denom = _getValues(elmt, 'value', numeric, parDefs, substitute)
            info = {"av": None, "zo": None}
            if ini.laplace in (numer + denom).atoms(sp.Symbol):
                a, b = _coeffs(numer, denom)
                if len(sp.Poly(numer, ini.laplace).all_coeffs()) > len(a):
                    # A differentiator has no state; its polynomial stamp is
                    # first order in s but index 2 (Anton, 2026-09-09).
                    print("Warning: %s: transfer is not proper (numerator "
                          "order > denominator order); polynomial stamp "
                          "used, no state-space form." % elmt.refDes)
                    continue
                if len(a) > 1:
                    info["av"] = _newChain(elmt.refDes, a, b, elmt.refDes)
            if elmt.model in ('EZ', 'HZ'):
                # Output impedance: its own states, independent of those of
                # the transfer (OPA209: two chains). Z proper -> Z realised
                # from the branch current; Z improper (inductive) -> 1/Z is
                # proper and is realised from the voltage across it
                # (Anton, 2026-09-09: "determine the order, then decide
                # which model"). A constant zo needs no chain.
                zoN, zoD = _getValues(elmt, 'zo', numeric, parDefs, substitute)
                if ini.laplace in (zoN + zoD).atoms(sp.Symbol):
                    if len(sp.Poly(zoN, ini.laplace).all_coeffs()) <= \
                       len(sp.Poly(zoD, ini.laplace).all_coeffs()):
                        a, b = _coeffs(zoN, zoD)
                        kind = "Z"
                    else:
                        a, b = _coeffs(zoD, zoN)
                        kind = "Y"
                    key = _newChain(elmt.refDes + "_zo", a, b, "zo_" + elmt.refDes)
                    names.append("V_zo_" + elmt.refDes)      # voltage across zo
                    info["zo"] = (kind, key, len(names) - 1)
                else:
                    info["zo"] = ("const", zoN/zoD, None)
            if info["av"] is not None or info["zo"] is not None:
                expanded[elmt.refDes] = info
    dim = len(names)
    Dv = sp.Matrix([sp.Symbol(name) for name in names])
    M = sp.zeros(dim)
    s = ini.laplace

    def _chain(refDes, vin, vout_row=None):
        """Stamp the integrator chain of refDes: input row (sum a_j V_j =
        controlling quantity), integrator rows (s V_i = V_{i-1}); returns the
        list of (column, b_j) pairs for the output sum."""
        a, b, cols = chains[refDes]
        row0 = cols[0]                                # input row = row of V_0
        for j, col in enumerate(cols):
            M[row0, col] += a[j]
        for (pos, sign) in vin:                       # controlling quantity
            if pos is not None:
                M[row0, pos] -= sign
        for i in range(1, len(cols)):
            M[cols[i], cols[i-1]] -= 1
            M[cols[i], cols[i]]   += s
        return list(zip(cols, b))

    for el in list(cir.elements.keys()):
        elmt = cir.elements[el]
        if elmt.refDes in expanded:
            refDes = elmt.refDes
            info   = expanded[refDes]
            model  = {'EZ': 'E', 'HZ': 'H'}.get(elmt.model, elmt.model)
            numer, denom = _getValues(elmt, 'value', numeric, parDefs, substitute)

            def _outputSum(vin):
                """(column, coefficient) pairs of the transfer's output; a
                constant gain has no chain and returns the gain itself."""
                if info["av"] is not None:
                    return _chain(refDes, vin), None
                return [], numer/denom

            def _zoTerm(dVarPos, row):
                """Add the output-impedance voltage to the output row."""
                kind, key, vz = info["zo"]
                if kind == "const":
                    M[row, dVarPos] -= key                 # (V0-V1) - av*Vin - zo*I = 0
                    return
                M[row, vz] -= 1                            # ... - V_zo = 0
                if kind == "Z":                            # V_zo = Z(I): chain in = I
                    for col, bj in _chain(key, [(dVarPos, 1)]):
                        M[vz, col] -= bj
                    M[vz, vz] += 1
                else:                                      # I = Y(V_zo): chain in = V_zo
                    for col, bj in _chain(key, [(vz, 1)]):
                        M[vz, col] += bj
                    M[vz, dVarPos] -= 1

            if model == 'E':
                dVarPos = varIndex['I_' + refDes]
                pos0, pos1, pos2, pos3 = [varIndex[n] for n in elmt.nodes]
                M[pos0, dVarPos] += 1
                M[pos1, dVarPos] -= 1
                M[dVarPos, pos0] += 1                 # (V0 - V1) - sum b_j V_j = 0
                M[dVarPos, pos1] -= 1
                pairs, gain = _outputSum([(pos2, 1), (pos3, -1)])
                for col, bj in pairs:
                    M[dVarPos, col] -= bj
                if gain is not None:
                    M[dVarPos, pos2] -= gain
                    M[dVarPos, pos3] += gain
                if info["zo"] is not None:
                    _zoTerm(dVarPos, dVarPos)
            elif model == 'G':
                dVarPos = varIndex['I_' + refDes]
                pos0, pos1, pos2, pos3 = [varIndex[n] for n in elmt.nodes]
                M[pos0, dVarPos] += 1
                M[pos1, dVarPos] -= 1
                M[dVarPos, dVarPos] -= 1              # -I + sum b_j V_j = 0
                for col, bj in _chain(refDes, [(pos2, 1), (pos3, -1)]):
                    M[dVarPos, col] += bj
            elif model == 'F':
                dVarPosO = varIndex['I_' + refDes]
                dVarPosI = varIndex['I_' + elmt.refs[0]]
                pos0, pos1 = [varIndex[n] for n in elmt.nodes]
                M[pos0, dVarPosO] += 1
                M[pos1, dVarPosO] -= 1
                M[dVarPosO, dVarPosO] -= 1            # -I_F + sum b_j V_j = 0
                for col, bj in _chain(refDes, [(dVarPosI, 1)]):
                    M[dVarPosO, col] += bj
            elif model == 'H':
                dVarPosO = varIndex['I_' + refDes]
                dVarPosI = varIndex['I_' + elmt.refs[0]]
                pos0, pos1 = [varIndex[n] for n in elmt.nodes]
                M[pos0, dVarPosO] += 1
                M[pos1, dVarPosO] -= 1
                M[dVarPosO, pos0] += 1                # (V0 - V1) - sum b_j V_j = 0
                M[dVarPosO, pos1] -= 1
                pairs, gain = _outputSum([(dVarPosI, 1)])
                for col, bj in pairs:
                    M[dVarPosO, col] -= bj
                if gain is not None:
                    M[dVarPosO, dVarPosI] -= gain
                if info["zo"] is not None:
                    _zoTerm(dVarPosO, dVarPosO)
        elif elmt.model == 'C':
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

def _singleDetector(M, detP, detN):
    """
    Returns the MNA matrix in which a differential detector quantity is a
    single variable, the column of that variable, and its sign.

    :param M: MNA matrix
    :type M: sympy.Matrix

    :param detP: column of the positive detector variable, or None
    :type detP: int, None

    :param detN: column of the negative detector variable, or None
    :type detN: int, None

    :return: tuple (M, column, sign):

             #. M (*sympy.Matrix*): the matrix in which the variable of
                'column' is the detector quantity
             #. column (*int*): column of the detector quantity
             #. sign (*int*): 1, or -1 for a negative detector alone
    :rtype: tuple
    """
    # A differential detector x_P - x_N used to cost TWO determinants,
    # det(M_P) - det(M_N). A difference of determinants is not the determinant
    # of any matrix, which blocked the single-matrix (eigenvalue) form of the
    # numerator. Substituting x_P = x_D + x_N turns the difference into ONE
    # variable by a column operation: col_N += col_P, after which slot P holds
    # x_D. The operation is unimodular, so det(M) and every other variable are
    # unchanged; verified symbolically on pzNetwork and balancedAmp
    # (Anton/Claude, 2026-09-09; see PZ.md). The bordered-matrix and the E/H
    # network-augmentation forms considered in July 2026 are SUPERSEDED by
    # this: same dimension, no extra variables.
    if detP is not None and detN is not None:
        Ms = M.copy()
        Ms[:, detN] = Ms[:, detN] + Ms[:, detP]
        return Ms, detP, 1
    if detP is not None:
        return M, detP, 1
    return M, detN, -1

"""
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
"""