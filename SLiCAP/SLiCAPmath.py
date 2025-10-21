#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with math functions.
"""
import sys
import sympy as sp
import numpy as np
import SLiCAP.SLiCAPconfigure as ini
from numpy.polynomial import Polynomial
from scipy.integrate import quad
from scipy.optimize import fsolve
from SLiCAP.SLiCAPlex import _replaceScaleFactors
from pytexit import py2tex

def det(M, method="ME"):
    """
    Returns the determinant of a square matrix 'M' calculated using recursive
    minor expansion (Laplace expansion).
    For large matrices with symbolic entries, this is faster than the built-in
    sympy.Matrix.det() method.

    :param M: Sympy matrix
    :type M: sympy.Matrix

    :param method: Method used:

                   - ME: SLiCAP Minor expansion
                   - BS: SLiCAP Bareis fraction-free expansion
                   - FC: SLiCAP Frequency Constants method
                   - LU: Sympy built-in LU method
                   - bareis: Sympy built-in Bareis method

    :return: Determinant of 'M'
    :rtype:  sympy.Expr
    """
    M = float2rational(
        sp.Matrix(M))  # Have a Mutable Matrix with rational numbers
    factor = 1
    if M.shape[0] != M.shape[1]:
        print("ERROR: Cannot determine determinant of non-square matrix.")
        D = None
    if method == "ME" and ini.reduce_matrix and len(M.atoms(sp.Symbol)) > 0:
        M, factor = _eliminateVars(M)
    dim = M.shape[0]
    if M.is_zero_matrix:
        D = 0
    elif dim == 1:
        D = M[0, 0] * factor
    elif dim == 2:
        D = sp.expand(M[0, 0]*M[1, 1]-M[1, 0]*M[0, 1]) * factor
    elif method == "ME":
        D = _detME(M) * factor
    elif method == "BS":
        D = _detBS(M)
    elif method == "LU":
        D = M.det(method="LU")
    elif method == "bareiss":
        D = M.det(method="bareiss")
    elif method == "laplace":
        D = M.det(method="laplace")
    else:
        print("ERROR: Unknown method for det(M).")
        D = None
    return D

def _eliminateVars(M):
    """
    Reduces the size of a matrix through division-free elimination of variables.
    Returns matrix with dim >= 1.

    :param M: sympy matrix
    :type M: sympy.Matrix()

    :return: (M, factor)
    
             - The returned matrix M is either a 1x1 matrix, a matrix of which 
               its entries are either zero or contain at least one symbol.
             - The returned factor is a nonzero (numeric) multiplication factor 
               for the determinant of the returned matrix to equal the 
               determinant of the original matrix.
               
    :rtype: tuple

    The returned factor 
    """
    factor = 1  # Scaling factor for determinant
    dim = M.shape[0]
    k, l = _find_numeric_entry(M)
    while k >= 0 and dim > 1:
        factor *= M[k, l]
        if (k+l) % 2:
            factor *= -1
        for i in range(dim):
            if M[i, l] != 0 and i != k:  # Test on zero increases speed
                for j in range(dim):
                    if M[k, j] != 0 and j != l:  # Test on zero increases speed
                        M[i, j] = sp.expand(M[i, j] - M[i, l]*M[k, j]/M[k, l])
        # remove row k and column l
        M = M.minor_submatrix(k, l)
        # reduce dimension
        dim -= 1
        k, l = _find_numeric_entry(M)
    return M, factor

def _find_numeric_entry(M):
    """
    Returns the (row, col) position of the first numeric entry in the matrix.

    :param M: sympy matrix
    :type M: sympy.Matrix()
    
    :return: (row, col)
    
             - row (int): row number of first numeric entry (-1 if not found)
             - col (int): column number of first numeric entry (-1 if not found)
    :rtype: tuple         
    """
    dim = M.shape[0]
    r, c = -1, -1
    for i in range(dim):
        for j in range(dim):
            if M[i, j] != 0 and M[i, j].is_number:
                return i, j
    return r, c

def _detME(M):
    dim = M.shape[0]
    if dim == 2:
        D = M[0, 0]*M[1, 1] - M[1, 0]*M[0, 1]
    else:
        D = 0
        for row in range(dim):
            if M[row, 0] != 0:
                minor = _detME(M.minor_submatrix(row, 0))
                if minor != 0:
                    if row % 2:
                        D += -M[row, 0] * minor
                    else:
                        D += M[row, 0] * minor
    return sp.expand(D)

def _detBS(M):
    newM = M.copy()
    sign = 1
    dim = newM.shape[0]
    for k in range(dim-1):
        if newM[k, k] == 0:
            for m in range(k+1, dim):
                if newM[m, k] != 0:
                    row_m = newM.row(m)
                    newM[m, :] = newM.row(k)
                    newM[k, :] = row_m
                    sign = -sign
            if m == dim:
                return sp.S(0)
        for i in range(k+1, dim):
            for j in range(k+1, dim):
                newM[i, j] = newM[k, k] * newM[i, j] - newM[i, k] * newM[k, j]
                if k:
                    newM[i, j] = sp.factor(newM[i, j] / newM[k-1, k-1])
    D = sign * newM[dim-1, dim-1]
    return sp.simplify(D)

def _Roots(expr, var):
    if isinstance(expr, sp.Basic) and isinstance(var, sp.Symbol):
        params = expr.atoms(sp.Symbol)
        if var in params:
            if len(params) == 1:
                rts = _numRoots(expr, var)
            elif len(params) == 2 and sp.pi in params:
                rts = _numRoots(expr, var)
            else:
                rts = _symRoots(expr, var)
        else:
            rts = []
    else:
        rts = []
    return rts

def _symRoots(expr, var):
    expr = assumeRealParams(expr)
    polyExpr = sp.poly(expr, var)
    rootDict = sp.roots(polyExpr)
    rts = []
    for rt in rootDict.keys():
        for i in range(rootDict[rt]):
            rts.append(clearAssumptions(rt))
    return rts

def _numRoots(expr, var):
    """
    Returns the roots of the polynomial 'expr' with indeterminate 'var'.

    This function uses numpy for calculation of numeric roots.

    :note:

    See: https://docs.scipy.org/doc/numpy/reference/generated/numpy.polynomial.polynomial.polyroots.html

    :param expr: Univariate function.
    :type expr: sympy.Expr

    :param var: Indeterminate of 'expr'.
    :type var: sympy.Symbol
    """
    rts = []
    try:
        pol = sp.Poly(expr, var)
        coeffs = pol.all_coeffs()
        coeffs = [float(sp.N(coeffs[i]/sp.Poly.LC(pol))) for i in range(len(coeffs))]
    except sp.PolynomialError:
        print('ERROR: could not write expression as polynomial:\n\n')
        print('Try different setting for setting: ini.numer and/or ini.denom;')
        print('current settings: ', ini.numer, ini.denom, 'respectively.')
        coeffs = []
    coeffs = np.array(coeffs[::-1], dtype=float) # Reversed list to array
    try:
        p = Polynomial(coeffs)
        rts = np.flip(p.roots())
    except BaseException:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        print("Error: cannot determine the roots of:", str(p))
    return rts

def coeffsTransfer(rational, var=ini.laplace, method='lowest'):
    """
    Returns a nested list with the coefficients of the variable of the
    numerator and of the denominator of 'rational'.

    The coefficients are in ascending order.

    :param rational: Rational function of the variable.
    :type rational: sympy.Expr

    :param variable: Variable of the rational function
    :type variable: sympy.Symbol

    :param method: Normalization method:

                   - "highest": the coefficients of the highest order of
                     <variable> of the denominator will be noramalized to unity.
                   - "lowest": the coefficients of the lowest order of
                     <variable> of the denominator will be noramalized to unity.

    :type method: str

    :return: Tuple with gain and two lists: [gain, numerCoeffs, denomCoeffs]

             #. gain (*sympy.Expr*): ratio of the nonzero coefficient of the
                lowest order of the numerator and the coefficient of the
                nonzero coefficient of the lowest order of the denominator.
             #. numerCoeffs  (*list*): List with all coeffcients of the
                numerator in ascending order.
             #. denomCoeffs  (*list*): List with all coeffcients of the
                denominator in ascending order.

    :rtype: tuple
    """
    if rational != 0:
        num, den = rational.as_numer_denom()
        try:
            numPoly = sp.Poly(num, var)
            denPoly = sp.Poly(den, var)
            if method == 'lowest':
                gainNum = sp.Poly.EC(numPoly)
                gainDen = sp.Poly.EC(denPoly)
            elif method == 'highest':
                gainNum = sp.Poly.LC(numPoly)
                gainDen = sp.Poly.LC(denPoly)
            numCoeffs = numPoly.all_coeffs()
            denCoeffs = denPoly.all_coeffs()
            gain = sp.simplify(gainNum/gainDen)
            numCoeffs = list(
                reversed([sp.simplify(numCoeffs[i]/gainNum) for i in range(len(numCoeffs))]))
            denCoeffs = list(
                reversed([sp.simplify(denCoeffs[i]/gainDen) for i in range(len(denCoeffs))]))
        except sp.PolynomialError:
            gain = sp.simplify(rational)
            numCoeffs = []
            denCoeffs = []
    else:
        gain = 0
        numCoeffs = [0]
        denCoeffs = [1]
    return (gain, numCoeffs, denCoeffs)

def normalizeRational(rational, var=ini.laplace, method='lowest'):
    """
    Normalizes a rational expression to:

    .. math::

        F(s) = gain\\,s^{\\ell}  \\frac{1+b_1s + ... + b_ms^m}{1+a_1s + ... + a_ns^n}

    :param Rational: Rational function of the variable.
    :type Rational: sympy.Expr

    :param var: Variable of the rational function
    :type var: sympy.Symbol

    :param method: Normalization method:

                   - "highest": the coefficients of the highest order of
                     <variable> of the denominator will be noramalized to unity.
                   - "lowest": the coefficients of the lowest order of
                     <variable> of the denominator will be noramalized to unity.

    :type method: str

    :return:  Normalized rational function of the variable.
    :rtype: sympy.Expr
    """
    gain, numCoeffs, denCoeffs = coeffsTransfer(
        rational, var=var, method=method)
    if len(numCoeffs) and len(denCoeffs):
        numCoeffs = list(reversed(numCoeffs))
        denCoeffs = list(reversed(denCoeffs))
        num = sp.Poly(numCoeffs, var).as_expr()
        den = sp.Poly(denCoeffs, var).as_expr()
        rational = gain*num/den
    return rational

def _cancelPZ(poles, zeros):
    """
    Cancels poles and zeros that coincide within the displayed accuracy.

    :note:

    The display accuracy (number of digits) is defined by ini.disp.

    :param poles: List with poles (*float*) of a Laplace rational function.
    :type poles: list

    :param zeros: List with zeros (*float*) of a Laplace rational function.
    :type zeros: list

    :return: Tuple with a list with poles (*float*) and a list with zeros (*float*).
    :rtype: Tuple with two lists,
    """
    newPoles = []
    newZeros = []
    # make a copy of the lists of poles and zeros, this one will be modified
    newPoles = [poles[i] for i in range(len(poles))]
    newZeros = [zeros[i] for i in range(len(zeros))]
    for j in range(len(zeros)):
        for i in range(len(poles)):
            cancel = False
            # Check if zero coincides with pole
            diff = poles[i]-zeros[j]
            if not diff:
                cancel = True
            else:
                try:
                    syms = len(list(diff.atoms(sp.Symbol)))
                except:
                    syms = 0
                if not syms:
                    ssum = poles[i]+zeros[j]
                    erel = abs(0.5*diff/ssum)
                    if erel < 10**(-ini.disp):
                        cancel = True
                    else:
                        cancel = False
                else:
                    cancel = False
            if cancel:
                # if the pole and the zero exist in newPoles and newZeros, respectively
                # then remove the pair
                if poles[i] in newPoles and zeros[j] in newZeros:
                    newPoles.remove(poles[i])
                    newZeros.remove(zeros[j])
    return (newPoles, newZeros)

def _zeroValue(numer, denom, var):
    """
    Returns the zero frequency (s=0) value of numer/denom.

    :param numer: Numerator of a rational function of the Laplace variable
    :type numer:  sympy.Expr

    :param denom: Denominator of a rational function of the Laplace variable
    :type denom:  sympy.Expr

    :return:      zero frequency (s=0) value of numer/denom.
    :rtype:       sympy.Expr
    """
    # numer = sp.simplify(numer)
    # denom = sp.simplify(denom)
    numerValue = numer.subs(var, 0)
    denomValue = denom.subs(var, 0)
    if numerValue == 0 and denomValue == 0:
        gain = sp.sympify("undefined")
    elif numerValue == 0:
        gain = sp.N(0)
    elif denomValue == 0:
        gain = sp.oo
    else:
        gain = sp.simplify(numerValue/denomValue)
    return gain

def findServoBandwidth(loopgainRational):
    """
    Determines the intersection points of the asymptotes of the magnitude of
    the loopgain with unity.

    :param loopgainRational: Rational function of the Laplace variable, that
           represents the loop gain of a circuit.
    :type LoopgainRational: sympy.Expr

    :return: Dictionary with key-value pairs:

             - hpf: frequency of high-pass intersection
             - hpo: order at high-pass intersection
             - lpf: frequency of low-pass intersection
             - lpo: order at low-pass intersection
             - mbv: mid-band value of the loopgain (highest value at order = zero)
             - mbf: lowest freqency of mbv
    :rtype: dict
    """
    numer, denom = loopgainRational.as_numer_denom()
    poles = _numRoots(denom, ini.laplace)
    zeros = _numRoots(numer, ini.laplace)
    poles, zeros = _cancelPZ(poles, zeros)
    numPoles = len(poles)
    numZeros = len(zeros)
    numCornerFreqs = numPoles + numZeros
    gain, coeffsN, coeffsD = coeffsTransfer(loopgainRational)
    freqsOrders = np.zeros((numCornerFreqs, 2), dtype='float64')
    for i in range(numZeros):
        freqsOrders[i, 0] = np.abs(zeros[i])
        freqsOrders[i, 1] = 1
    for i in range(numPoles):
        freqsOrders[numZeros + i, 0] = np.abs(poles[i])
        freqsOrders[numZeros + i, 1] = -1
    # sort the rows with increasing corner frequencies
    freqsOrders = freqsOrders[freqsOrders[:, 0].argsort()]
    for i in range(numCornerFreqs):
        if i == 0:
            # Initialize variables
            value = np.abs(float(gain))
            fcorner = float(freqsOrders[i, 0])
            order = int(freqsOrders[i, 1])
            result = _initServoResults(fcorner, order, value)
        elif freqsOrders[i, 0] == 0:
            # Update corner frequency and order
            fcorner = float(freqsOrders[i, 0])
            order += int(freqsOrders[i, 1])
        else:
            new_fcorner = float(freqsOrders[i, 0])
            new_order = int(order + freqsOrders[i, 1])
            # Determine new value at corner frequency
            if order == 0:
                new_value = value
            elif fcorner == 0:  # first pole or zero in origin
                new_value = value * new_fcorner ** order
            else:
                new_value = value * (new_fcorner / fcorner) ** order
            # Determine unity-gain frequencies
            if new_value > 1 and new_order < 0:
                # low-pass intersection
                result['lpf'] = new_fcorner * new_value ** (-1/new_order)
                result['lpo'] = new_order
            elif new_value < 1 and new_order > 0:
                # high-pass intersection
                result['hpf'] = new_fcorner * new_value ** (-1/new_order)
                result['hpo'] = new_order
            if new_value > 1 and (result['mbv'] == None or new_value > result['mbv']):
                # A new or larger midband value
                result['mbv'] = new_value
                result['mbf'] = new_fcorner
            # Update value, corner frequency, and order
            value = new_value
            order = new_order
            fcorner = new_fcorner
    for key in result.keys():
        try:
            result[key] = float(result[key])
        except TypeError:
            pass
    if ini.hz:
        if result['hpf'] != None:
            result['hpf'] = result['hpf']/np.pi/2
        if result['lpf'] != None:
            result['lpf'] = result['lpf']/np.pi/2
        if result['mbf'] != None:
            result['mbf'] = result['mbf']/np.pi/2
    return result

def _initServoResults(fcorner, order, value):
    result = {}
    result['mbv'] = None
    result['mbf'] = None
    result['lpf'] = None
    result['lpo'] = None
    result['hpf'] = None
    result['hpo'] = None
    if fcorner == 0:
        if order < 0:
            result['mbv'] = sp.oo
            result['mbf'] = 0
            result['lpf'] = value**(-1/order)
            result['lpo'] = order
        elif order > 0:
            result['hpf'] = value**(-1/order)
            result['hpo'] = order
    elif value > 1 and order < 0:
        result['mbv'] = value
        result['mbf'] = 0
        result['lpf'] = fcorner * value**(-1/order)
        result['lpo'] = order
    elif value < 1 and order > 0:
        result['hpf'] = fcorner * value**(-1/order)
        result['hpo'] = order
    return result

def _checkNumber(var):
    """
    Returns a number with its value represented by var.

    :param var: Variable that may represent a number.
    :type var: str, sympy object, int, float

    :return: sympy expression
    :rtype: int, float
    """
    if type(var) == str:
        var = _replaceScaleFactors(var)
    else:
        var = str(var)
    try:
        var = sp.Rational(var)
    except BaseException:
        var = None
    return var

def _checkNumeric(exprList):
    """
    Returns True is all entries in the list 'exprList' are numeric.

    :param exprList; List with numbers and/or expressions
    :type exprList: list

    :return: True is all entries in 'exprList' are numeric.
    :rtype: Bool
    """
    numeric = True
    for item in exprList:
        params = sp.N(item).atoms(sp.Symbol)
        if len(params) > 0:
            numeric = False
            break
    return numeric

def _checkExpression(expr):
    """
    Returns the sympy expression of expr.

    :param expr: argument that may represent a number or an expression.
    :type expr: str, sympy object, int, float

    :return: sympy expression
    :rtype: int, float
    """
    sym_in = []
    if type(expr) == str:
        try:
            sym_in = sp.sympify(expr).atoms(sp.Symbol)
        except sp.SympifyError:
            pass
        out = _replaceScaleFactors(expr)
    else:
        out = str(expr)
    try:
        out = sp.sympify(out, rational=True)
        sym_out = out.atoms(sp.Symbol)
        for item in sym_in:
            if item not in sym_out:
                print("Error in symbol name: %s."%(item))
    except sp.SympifyError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        print("Error in expression:", expr)
        out = None
    return out

def fullSubs(valExpr, parDefs):
    """
    Returns 'valExpr' after all parameters of 'parDefs' have been substituted
    into it recursively until no changes occur, or until the maximum number of
    substitutions is achieved.

    The maximum number opf recursive substitutions is set by ini.maxRexSubst.

    :param valExpr: Eympy expression in which the parameters should be substituted.
    :type valExpr: sympy.Expr, sympy.Symbol, int, float

    :param parDefs: Dictionary with key-value pairs:

                    - key (*sympy.Symbol*): parameter name
                    - value (*sympy object, int, float*): value of the parameter

    :return: Expression or value obtained from recursive substitutions of
             parameter definitions into 'valExpr'.
    :rtype: sympy object, int, float
    """
    strValExpr = str(valExpr)
    i = 0
    newvalExpr = 0
    while valExpr != newvalExpr and i < ini.max_rec_subst and isinstance(valExpr, sp.Basic):
        # create a substitution dictionary with the smallest number of entries (this speeds up the substitution)
        substDict = {}
        params = valExpr.atoms(sp.Symbol)
        for param in params:
            if param in parDefs.keys():
                if type(parDefs[param]) == isinstance(valExpr, sp.Basic):
                    substDict[param] = float2rational(parDefs[param])
                else:
                    # In case of floats, integers or strings:
                    substDict[param] = sp.sympify(
                        str(parDefs[param]), rational=True)
        # perform the substitution
        newvalExpr = valExpr
        valExpr = newvalExpr.xreplace(substDict)
        i += 1
    if i == ini.max_rec_subst:
        print("Warning: reached maximum number of substitutions for expression '{0}'".format(
            strValExpr))
    return valExpr

def assumeRealParams(expr, params='all'):
    """
    Returns the sympy expression 'expr' in which variables, except the
    Laplace variable, have been redefined as real.

    :param expr: Sympy expression
    :type expr: sympy.Expr, sympy.Symbol

    :param params: List with variable names (*str*), or 'all' or a variable name (*str*).
    :type params: list, str

    :return: Expression with redefined variables.
    :rtype: sympy.Expr, sympy.Symbol
    """
    if type(params) == list:
        for i in range(len(params)):
            expr = expr.xreplace(
                {sp.Symbol(params[i]): sp.Symbol(params[i], real=True)})
    elif type(params) == str:
        if params == 'all':
            params = expr.atoms(sp.Symbol)
            for param in params:
                if param != ini.laplace:
                    expr = expr.xreplace(
                        {sp.Symbol(str(param)): sp.Symbol(str(param), real=True)})
        else:
            expr = expr.xreplace(
                {sp.Symbol(params): sp.Symbol(params, real=True)})
    else:
        print("Error: expected type 'str' or 'lst', got '{0}'.".format(
            type(params)))
    return expr

def assumePosParams(expr, params='all'):
    """
    Returns the sympy expression 'expr' in which  variables, except the
    Laplace variable, have been redefined as positive.

    :param expr: Sympy expression
    :type expr: sympy.Expr, sympy.Symbol

    :param params: List with variable names (*str*), or 'all' or a variable name (*str*).
    :type params: list, str

    :return: Expression with redefined variables.
    :rtype: sympy.Expr, sympy.Symbol
    """
    if type(params) == list:
        for i in range(len(params)):
            if params[i] == 't':
                expr = expr.replace(sp.Heaviside(sp.Symbol('t')), 1)
            expr = expr.xreplace(
                {sp.Symbol(params[i]): sp.Symbol(params[i], positive=True)})
    elif type(params) == str:
        if params == 'all':
            params = list(expr.atoms(sp.Symbol))
            for param in params:
                if param != ini.laplace and param != ini.frequency:
                    if param == sp.Symbol('t'):
                        expr = expr.replace(sp.Heaviside(sp.Symbol('t')), 1)
                    expr = expr.xreplace(
                        {param: sp.Symbol(str(param), positive=True)})
        elif params == 't':
                expr = expr.replace(sp.Heaviside(sp.Symbol('t')), 1)
        else:
            expr = expr.xreplace(
                {sp.Symbol(params): sp.Symbol(params, positive=True)})
    else:
        print("Error: expected type 'str' or 'lst', got '{0}'.".format(
            type(params)))
    return expr

def clearAssumptions(expr, params='all'):
    """
    Returns the sympy expression 'expr' in which  the assumtions 'Real' and
    'Positive' have been deleted.

    :param expr: Sympy expression
    :type expr: sympy.Expr, sympy.Symbol

    :param params: List with variable names (*str*), or 'all' or a variable name (*str*).
    :type params: list, str

    :return: Expression with redefined variables.
    :rtype: sympy.Expr, sympy.Symbol
    """
    if type(params) == list:
        for i in range(len(params)):
            expr = expr.xreplace(
                {sp.Symbol(params[i], positive=True): sp.Symbol(params[i])})
            expr = expr.xreplace(
                {sp.Symbol(params[i], real=True): sp.Symbol(params[i])})
    elif type(params) == str:
        if params == 'all':
            params = expr.atoms(sp.Symbol)
            try:
                params.remove(ini.laplace)
            except BaseException:
                pass
            for param in params:
                expr = expr.xreplace(
                    {sp.Symbol(str(param), positive=True): sp.Symbol(str(param))})
                expr = expr.xreplace(
                    {sp.Symbol(str(param), real=True): sp.Symbol(str(param))})
        else:
            expr = expr.xreplace(
                {sp.Symbol(params, positive=True): sp.Symbol(params)})
            expr = expr.xreplace(
                {sp.Symbol(params, real=True): sp.Symbol(params)})
    else:
        print("Error: expected type 'str' or 'lst', got '{0}'.".format(
            type(params)))
    return expr

def phaseMargin(LaplaceExpr):
    """
    Calculates the phase margin assuming a loop gain definition according to
    the asymptotic gain model.

    This function uses **scipy.newton()** for determination of the the
    unity-gain frequency. It uses the function **SLiCAPmath.findServoBandwidth()**
    for the initial guess, and ini.disp for the relative accuracy.

    if ini.hz == True, the units will be degrees and Hz, else radians and
    radians per seconds.

    :param LaplaceExpr: Univariate function (sympy.Expr*) or list with
                        univariate functions (sympy.Expr*) of the Laplace
                        variable.
    :type LaplaceExpr: sympy.Expr, list

    :return: Tuple with phase margin (*float*) and unity-gain frequency
             (*float*), or Tuple with lists with phase margins (*float*) and
             unity-gain frequencies (*float*).

    :rtype: tuple
    """
    freqs = []
    mrgns = []
    if type(LaplaceExpr) != list:
        LaplaceExpr = [LaplaceExpr]
    for expr in LaplaceExpr:
        expr = normalizeRational(sp.N(expr))
        if ini.hz == True:
            data = expr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
        else:
            data = expr.xreplace({ini.laplace: sp.I*ini.frequency})
        func = sp.lambdify(ini.frequency, sp.Abs(data)-1, ini.lambdify)
        guess = findServoBandwidth(expr)['lpf']
        try:
            # freq = newton(func, guess, tol = 10**(-ini.disp), maxiter = 50)
            freq = float(fsolve(func, guess)[0])
            mrgn = float(_phaseFunc_f(expr, freq))
        except BaseException:
            exc_type, value, exc_traceback = sys.exc_info()
            print('\n', value)
            print("Error: could not determine unity-gain frequency for phase margin.")
            freq = None
            mrgn = None
        freqs.append(freq)
        mrgns.append(mrgn)
    if len(freqs) == 1:
        mrgns = mrgns[0]
        freqs = freqs[0]
    return (mrgns, freqs)

def _makeNumData(yFunc, xVar, x, normalize=True):
    """
    Returns a list of values y, where y[i] = yFunc(x[i]).

    :param yFunc: Function
    :type yFunc: sympy.Expr

    :param xVar: Variable that needs to be substituted in *yFunc*
    :type xVar: sympy.Symbol

    :param x: List with values of x
    :type x: list

    :param normalize: True if rational function needs to be normalized. Defaults to True.
    :type normalize: Bool

    :return: list with y values: y[i] = yFunc(x[i]).
    :rtype:  list
    """
    if normalize:
        yFunc = normalizeRational(sp.N(yFunc), xVar)
    else:
        yFunc = sp.N(yFunc)
    if xVar in yFunc.atoms(sp.Symbol):
        # Check for Heaviside functions (not implemented in sp.lambdify)
        if len(yFunc.atoms(sp.Heaviside)) != 0:
            y = [sp.N(yFunc.subs(xVar, x[i])).doit() for i in range(len(x))]
        else:
            func = sp.lambdify(xVar, yFunc, ini.lambdify)
            y = func(x)
    else:
        y = [sp.N(yFunc) for i in range(len(x))]
    return y

def _magFunc_f(LaplaceExpr, f):
    """
    Calculates the magnitude at the real frequency f (Fourier) from the
    univariate function 'LaplaceExpr' of the Laplace variable.

    If ini.hz == true, the Laplace variable will be replaced with
    2*sp.pi*sp.I*ini.frequency.

    If ini.hz == False, the Laplace variable will be replaced with
    sp.I*ini.frequency.

    :param LaplaceExpr: Univariate function of the Laplace variable.
    :type LaplaceExpr: sympy.Expr

    :param f: Frequency value (*float*), or a numpy array with frequency values
              (*float*).

    :return: Magnitude at the specified frequency, or list with magnitudes at
             the specified frequencies.

    :rtype: float, numpy.array
    """
    LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    if type(f) == list:
        # Convert lists into numpy arrays
        f = np.array(f)
    # Obtain the Fourier transform from the Laplace transform
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    result = _makeNumData(sp.Abs(data), ini.frequency, f, normalize=False)
    return result

def _dB_magFunc_f(LaplaceExpr, f):
    """
    Calculates the dB magnitude at the real frequency f (Fourier) from the
    univariate function 'LaplaceExpr' of the Laplace variable.

    If ini.hz == true, the Laplace variable will be replaced with
    2*sp.pi*sp.I*ini.frequency.

    If ini.hz == False, the Laplace variable will be replaced with
    sp.I*ini.frequency.

    :param LaplaceExpr: Univariate function of the Laplace variable.
    :type LaplaceExpr: sympy.Expr

    :param f: Frequency value (*float*), or a numpy array with frequency values
              (*float*).

    :return: dB Magnitude at the specified frequency, or list with dB magnitudes
             at the specified frequencies.

    :rtype: float, numpy.array
    """
    LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    if type(f) == list:
        f = np.array(f)
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    result = _makeNumData(20*sp.log(sp.Abs(sp.N(data)), 10),
                          ini.frequency, f, normalize=False)
    return result

def _phaseFunc_f(LaplaceExpr, f):
    """
    Calculates the phase angle at the real frequency f (Fourier) from the
    univariate function 'LaplaceExpr' of the Laplace variable.

    If ini.hz == true, the Laplace variable will be replaced with
    2*sp.pi*sp.I*ini.frequency.

    If ini.hz == False, the Laplace variable will be replaced with
    sp.I*ini.frequency.

    :param LaplaceExpr: Univariate function of the Laplace variable.
    :type LaplaceExpr: sympy.Expr

    :param f: Frequency value (*float*), or a numpy array with frequency values
              (*float*).

    :return: Angle at the specified frequency, or list with angles at
             the specified frequencies.

    :rtype: float, numpy.array
    """
    LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    if type(f) == list:
        f = np.array(f)
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    data = sp.N(normalizeRational(data, ini.frequency))
    if ini.frequency in data.atoms(sp.Symbol):
        try:
            func = sp.lambdify(ini.frequency, data, ini.lambdify)
            phase = np.angle(func(f))
        except BaseException:
            phase = []
            for i in range(len(f)):
                try:
                    phase.append(np.angle(data.subs(ini.frequency, f[i])))
                except BaseException:
                    phase.append(0)
    elif data >= 0:
        phase = [0 for i in range(len(f))]
    elif data < 0:
        phase = [np.pi for i in range(len(f))]
    try:
        phase = np.unwrap(phase)
    except BaseException:
        pass
    if ini.hz:
        phase = phase * 180/np.pi
    return phase

def _delayFunc_f(LaplaceExpr, f, delta=10**(-ini.disp)):
    """
    Calculates the group delay at the real frequency f (Fourier) from the
    univariate function 'LaplaceExpr' of the Laplace variable.

    If ini.hz == true, the Laplace variable will be replaced with
    2*sp.pi*sp.I*ini.frequency.

    If ini.hz == False, the Laplace variable will be replaced with
    sp.I*ini.frequency.

    :param LaplaceExpr: Univariate function of the Laplace variable.
    :type LaplaceExpr: sympy.Expr

    :param f: Frequency value (*float*), or a numpy array with frequency values
              (*float*).

    :return: Group delay at the specified frequency, or list with group delays
             at the specified frequencies.

    :rtype: float, numpy.array
    """
    if type(f) == list:
        f = np.array(f)
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    if ini.frequency in data.atoms(sp.Symbol):
        data = sp.N(normalizeRational(data, ini.frequency))
        try:
            func = sp.lambdify(ini.frequency, data, ini.lambdify)
            angle1 = np.angle(func(f))
            angle2 = np.angle(func(f*(1+delta)))
        except BaseException:
            angle1 = np.array([np.angle(data.subs(ini.frequency, f[i]))
                              for i in range(len(f))])
            angle2 = np.array(
                [np.angle(data.subs(ini.frequency, f[i]*(1+delta))) for i in range(len(f))])
        try:
            angle1 = np.unwrap(angle1)
            angle2 = np.unwrap(angle2)
        except BaseException:
            pass
        delay = (angle1 - angle2)/delta/f
        if ini.hz == True:
            delay = delay/2/np.pi
    else:
        delay = [0 for i in range(len(f))]
    return delay

def doCDSint(noiseResult, tau, f_min, f_max):
    """
    Returns the integral from ini.frequency = f_min to ini.frequency = f_max,
    of a noise spectrum after multiplying it with (2*sin(pi*ini.frequency*tau))^2

    :param noiseResult: sympy expression of a noise density spectrum in V^2/Hz or A^2/Hz
    :type noiseResult: sympy.Expr, sympy.Symbol, int or float

    :param tau: Time between two samples
    :type tau: sympy.Expr, sympy.Symbol, int or float

    :param f_min: Lower limit of the integral
    :type f_min: sympy.Expr, sympy.Symbol, int or float

    :param f_max: Upper limit of the integral
    :type f_max: sympy.Expr, sympy.Symbol, int or float

    :return: integral of the spectrum from f_min to f_max after corelated double sampling
    :rtype: sympy.Expr, sympy.Symbol, int or float
    """
    _phi = sp.Symbol('_phi', positive=True)
    noiseResult *= ((2*sp.sin(sp.pi*ini.frequency*tau)))**2
    noiseResult = noiseResult.subs(ini.frequency, _phi/tau/sp.pi)
    noiseResultCDSint = sp.integrate(
        noiseResult/sp.pi/tau, (_phi, f_min*tau*sp.pi, f_max*tau*sp.pi))
    return sp.simplify(noiseResultCDSint)

def doCDS(noiseResult, tau):
    """
    Returns noiseResult after multiplying it with (2*sin(pi*ini.frequency*tau))^2

    :param noiseResult: sympy expression of a noise density spectrum in V^2/Hz or A^2/Hz
    :type noiseResult: sympy.Expr, sympy.Symbol, int or float

    :param tau: Time between two samples
    :type tau: sympy.Expr, sympy.Symbol, int or float

    :return: noiseResult*(2*sin(pi*ini.frequency*tau))^2
    :rtype: sympy.Expr, sympy.Symbol, int or float
    """
    return noiseResult*((2*sp.sin(sp.pi*ini.frequency*tau)))**2


def routh(charPoly, eps=sp.Symbol('epsilon')):
    """
    Returns the Routh array of a polynomial of the Laplace variable (ini.laplace).

    :param charPoly: Expression that can be written as a polynomial of the Laplace variable (ini.laplace).
    :type charPoly:  sympy.Expr

    :param eps:      Symbolic variable used to indicate marginal stability. Use a symbol that is not present in *charPoly*.
    :type eps:       sympy.Symbol

    :return: Routh array
    :rtype:  sympy.Matrix

    :Example:

    >>> # ini.laplace = sp.Symbol('s')
    >>> s, eps = sp.symbols('s, epsilon')
    >>> charPoly = s**4+2*s**3+(3+k)*s**2+(1+k)*s+(1+k)
    >>> M = routh(charPoly, eps)
    >>> print(M.col(0)) # Number of roots in the right half plane is equal to
    >>>                 # the number of sign changes in the first column of the
    >>>                 # Routh array
    Matrix([[1], [2], [k/2 + 5/2], [(k**2 + 2*k + 1)/(k + 5)], [k + 1]])
    """
    coeffs = sp.Poly(charPoly, ini.laplace).all_coeffs()
    orders = len(coeffs)
    dim = int(np.ceil(orders/2))
    M = [[0 for i in range(dim)] for i in range(orders)]
    M = sp.Matrix(M)
    # Fill the first two rows of the matrix
    for i in range(dim):
        # First row with even orders
        M[0, i] = coeffs[2*i]
        # Second row with odd orders
        # Zero at the last position if the highest order is even
        if 2*i+1 < orders:
            M[1, i] = coeffs[2*i+1]
        else:
            M[1, i] = 0
    # Calculate all other coefficients of the matrix
    for i in range(2, orders):
        # print(M.row(i-1))
        if M.row(i-1) == sp.Matrix(sp.zeros(1, dim)):
            # Calculate the auxiliary polynomial
            for j in range(dim):
                M[i-1, j] = M[i-2, j]*(orders-i+1-2*j)
        for j in range(dim):
            if M[i-1, 0] == 0:
                M[i-1, 0] = eps
            if j + 1 >= dim:
                subMatrix = sp.Matrix([[M[i-2, 0], 0], [M[i-1, 0], 0]])
            else:
                subMatrix = sp.Matrix(
                    [[M[i-2, 0], M[i-2, j+1]], [M[i-1, 0], M[i-1, j+1]]])
            M[i, j] = sp.simplify(-1/M[i-1, 0]*subMatrix.det())
    return M

def equateCoeffs(protoType, transfer, noSolve=[], numeric=True):
    """
    Returns the solutions of the equation transferFunction = protoTypeFunction.

    Both transfer and prototype should be Laplace rational functions.
    Their numerators should be polynomials of the Laplace variable of equal
    order and their denominators should be polynomials of the Laplace variable
    of equal order.

    :param protoType: Prototype rational expression of the Laplace variable
    :type protoType: sympy.Expr
    :param transfer:

    Transfer fucntion of which the parameters need to be
    solved. The numerator and the denominator of this rational
    expression should be of the same order as those of the
    prototype.

    :type transfer: sympy.Expr

    :param noSolve: List with variables (*str, sympy.core.symbol.Symbol*) that do not need
                    to be solved. These parameters will remain symbolic in the
                    solutions.

    :type noSolve: list

    :param numeric: True will convert numeric results with floats instead of rationals

    :type numeric: bool

    :return: Dictionary with key-value pairs:

             - key: name of the parameter (*sympy.core.symbol.Symbol*)
             - value: solution of this parameter: (*sympy.Expr, int, float*)

    :rtype: dict
    """
    values = {}
    pars = list(set(list(protoType.atoms(sp.Symbol)) +
                list(transfer.atoms(sp.Symbol))))
    for i in range(len(noSolve)):
        noSolve[i] = sp.Symbol(str(noSolve[i]))
    params = []
    for par in pars:
        if par != ini.laplace and par not in noSolve:
            params.append(par)
    gainP, pN, pD = coeffsTransfer(protoType)
    gainT, tN, tD = coeffsTransfer(transfer)
    if len(pN) != len(tN) or len(pD) != len(tD):
        print('Error: unequal orders of prototype and target.')
    equations = []
    for i in range(len(pN)):
        eqn = sp.Eq(pN[i], tN[i])
        if eqn != True:
            equations.append(eqn)
    for i in range(len(pD)):
        eqn = sp.Eq(pD[i], tD[i])
        if eqn != True:
            equations.append(eqn)
    eqn = sp.Eq(gainP, gainT)
    if eqn != True:
        equations.append(eqn)
    try:
        solution = sp.solve(equations, (params))[0]
        if type(solution) == dict:
            values = solution
            if numeric:
                for key in values.keys():
                    values[key] = sp.N(values[key])
        else:
            for i in range(len(params)):
                if numeric:
                    values[params[i]] = sp.N(solution[i])
                else:
                    values[params[i]] = solution[i]
    except BaseException:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        print('Error: equateCoeffs(): could not solve equations.')
    return values

def step2PeriodicPulse(ft, t_pulse, t_period, n_periods):
    """
    Converts a step response in a periodic pulse response. Works with symbolic
    and numeric time functions.

    For evaluation of numeric values, use the SLiCAP function: _makeNumData().

    :param ft: Time function f(t)
    :type ft: sympy.Expr

    :param t_pulse: Pulse width
    :type t_pulse: int, float

    :param t_period: Pulse period
    :type t_period: int, float

    :param n_periods: Number of pulses
    :typen_periods: int, float

    :return: modified time function
    :rtype: sympy.Expr
    """
    t = sp.Symbol('t')
    ft *= sp.Heaviside(t, 1)
    ft_out = ft
    n_edges = 2*n_periods - 1
    t_delay = 0
    if t in ft.atoms(sp.Symbol):
        for i in range(n_edges):
            if i % 2 == 0:
                t_delay += t_pulse
                ft_out -= ft.subs(t, sp.UnevaluatedExpr(t - t_delay))
            else:
                t_delay += t_period - t_pulse
                ft_out += ft.subs(t, sp.UnevaluatedExpr(t - t_delay))
    else:
        print("Error: expected a time function f(t).")
    return ft_out

def butterworthPoly(n):
    """
    Returns a narmalized Butterworth polynomial of the n-th order of the
    Laplace variable.

    Zero-frequency value = 1, -3dB frequency (magnitude = 2) is 1 rad/s.

    :param n: order
    :type n: int

    :return: Butterworth polynomial of the n-th order of the Laplace variable
    :rtype: sympy.Expression
    """
    s = ini.laplace
    if n % 2:
        P_s = (s+1)
        for i in range(int((n-1)/2)):
            k = i + 1
            P_s *= (s**2-2*s*sp.cos((2*k+n-1)*sp.pi/2/n)+1)
    else:
        P_s = 1
        for i in range(int(n/2)):
            k = i + 1
            P_s *= (s**2-2*s*sp.cos((2*k+n-1)*sp.pi/2/n)+1)
    P_s = sp.simplify(P_s)
    return P_s

def besselPoly(n):
    """
    Returns a normalized Bessel polynomial of the n-th order of the Laplace
    variable.

    Zero-frequency value = 1, -3dB frequency (magnitude = 2) is 1 rad/s.

    :param n: order
    :type n: int

    :return: Bessel polynomial of the n-th order of the Laplace variable
    :rtype: sympy.Expression
    """
    s = ini.laplace
    P_s = 0
    for k in range(n+1):
        P_s += (sp.factorial(2*n-k)/((2**(n-k)) *
                sp.factorial(k)*sp.factorial(n-k)))*s**k
    P_s = sp.simplify(P_s/P_s.subs(s, 0))
    # Normalize 3 dB frequency
    w = sp.Symbol('w', real=True)
    B_w = sp.Abs(P_s.subs(s, sp.I*w))**2
    func = sp.lambdify(w, B_w - 2)
    w3dB = float2rational(fsolve(func, 10)[0])
    P_s = P_s.subs(s, s*w3dB)
    return P_s

def chebyshev1Poly(n, ripple):
    """
    Returns a normalized Chebyshev polynomial of the n-th order of the Laplace
    variable, with a ripple of <ripple> dB

    Zero-frequency value = 1, -3dB frequency (magnitude = 2) is 1 rad/s.

    :param n: order
    :type n: int

    :return: Chebyshev polynomial of the n-th order of the Laplace variable
    :rtype: sympy.Expression
    """
    s = ini.laplace
    eps = np.sqrt(10**(ripple/10)-1)
    h = np.tanh((1/n)*np.arcsinh(1/eps))
    def a_i(i, n, h): return np.sqrt(
        1/(1-h**2) - (np.sin((2*i-1)/n*np.pi/2))**2)

    def b_i(i, n, h): return np.sqrt(1 + 1/(h*np.tan((2*i-1)/n*np.pi/2))**2)/2
    if n % 2:
        P_s = s*np.sqrt(1-h**2)/h + 1
        order = int((n-1)/2)
    else:
        P_s = 1
        order = int(n/2)
    for i in range(1, order+1):
        P_s *= (s/a_i(i, n, h))**2 + s/(a_i(i, n, h)*b_i(i, n, h)) + 1
    # Normalize 3 dB frequency
    w = sp.Symbol('w', real=True)
    B_w = sp.Abs(P_s.subs(s, sp.I*w))**2
    func = sp.lambdify(w, B_w - 2)
    w3dB = float2rational(fsolve(func, 10)[0])
    P_s = P_s.subs(s, s*w3dB)
    return P_s

def _varNoise(noiseResult, noise, fmin, fmax, source=None, CDS=False, tau=None):
    """
    """
    errors = 0
    if type(source) != list:
        sources = [source]
    else:
        sources = source
    numlimits = False
    if fmin == None or fmax == None:
        print("Error in frequency range specification.")
        errors += 1
    if CDS:
        if tau == None:
            print(
                "Error: rmsNoise() with CDS=True requires a nonzero finite value for 'tau'.")
            errors += 1
        else:
            try:
                tau = sp.sympify(str(tau))
            except sp.SympifyError:
                print("Error in expression: rmsNoise( ... , tau =", tau, ").")
                errors += 1
    fMi = _checkNumber(fmin)
    fMa = _checkNumber(fmax)
    if fMi != None:
        # Numeric value for fmin
        fmin = fMi
    if fMa != None:
        # Numeric value for fmax
        fmax = fMa
    if fMi != None and fMa != None:
        if fMi >= fMa:
            # Numeric values for fmin and fmax but fmin >= fmax
            print("Error in frequency range specification.")
            errors += 1
        elif fMa > fMi:
            # Numeric values for fmin and fmax and fmax >= fmin
            numlimits = True
    elif noiseResult.dataType != 'noise':
        print("Error: expected dataType noise, got: '{0}'.".format(
            noiseResult.dataType))
        errors += 1
    if errors == 0:
        names = noiseResult.snoiseTerms.keys()
        if len(sources) == 1 and sources[0] == None:
            noiseSources = [name for name in names]
        else:
            # Check sources names and add if correct
            noiseSources = []
            for src in sources:
                if src in names:
                    noiseSources.append(src)
                elif src != None:
                    print("Error: unknown noise source: '{0}'.".format(src))
                    errors += 1
        if noise == 'onoise':
            noiseData = noiseResult.onoiseTerms
        elif noise == 'inoise':
            noiseData = noiseResult.inoiseTerms
    var = []
    if errors == 0:
        numSteps = 1
        if type(noiseResult.onoise) == list:
            numSteps = len(noiseResult.onoise)
        for i in range(numSteps):
            var_i = sp.N(0)
            for src in noiseSources:
                if type(noiseData[src]) != list:
                    data = float2rational(sp.simplify(noiseData[src]))
                else:
                    data = float2rational(sp.simplify(noiseData[src][i]))
                if data != 0:
                    if CDS:
                        var_i += doCDSint(data, tau, fmin, fmax)
                    else:
                        params = sp.N(data).atoms(sp.Symbol)
                        if len(params) == 0 or ini.frequency not in params:
                            # Frequency-independent spectrum, multiply with (fmax-fmin)
                            var_i += data * (fmax - fmin)
                        elif len(params) == 1 and ini.frequency in params and numlimits:
                            # Numeric frequency-dependent spectrum, use numeric integration
                            noise_spectrum = sp.lambdify(
                                ini.frequency, sp.N(data))
                            var_i += quad(noise_spectrum, fmin, fmax)[0]
                        else:
                            # Try sympy integration
                            func = assumePosParams(data)
                            var_i += sp.integrate(func,
                                                  [ini.frequency, fmin, fmax])
            if noiseResult.numeric == True:
                var.append(sp.N(clearAssumptions(sp.expand(var_i))))
            else:
                var.append(clearAssumptions(sp.expand(var_i)))
    if len(var) == 1:
        var = var[0]
    return var

def rmsNoise(noiseResult, noise, fmin, fmax, source=None, CDS=False, tau=None):
    """
    Calculates the RMS source-referred noise or detector-referred noise,
    or the contribution of a specific noise source or a collection of sources
    to it.

    :param noiseResult: Results of the execution of an instruction with data
                        type 'noise'.
    :type noiseResult: SLiCAPprotos.allResults

    :param noise: 'inoise' or 'onoise' for source-referred noise or detector-
                referred noise, respectively.
    :type noise': str

    :param fmin: Lower limit of the frequency range in Hz.
    :type fmin: str, int, float, sp.Symbol

    :param fmax: Upper limit of the frequency range in Hz.
    :type fmax: str, int, float, sp.Symbol

    :param source: refDes (ID) or list with IDs of noise sources
                of which the contribution to the RMS noise needs to be
                evaluated. Only IDs of current of voltage sources with a
                nonzero value for 'noise' are accepted.
    :type source: str, list

    :param CDS: True if correlated double sampling is required, defaults to False
                If True parameter 'tau' must be given a nonzero finite value
                (can be symbolic)
    :type CDS: Bool

    :param tau: CDS delay time
    :type tau: str, int, float, sp.Symbol

    :return: RMS noise over the frequency interval.

            - An expression or value if parameter stepping of the instruction is disabled.
            - A list with expressions or values if parameter stepping of the instruction is enabled.
    :rtype: int, float, sympy.Expr
    """
    result = _varNoise(noiseResult, noise, fmin, fmax,
                       source=source, CDS=CDS, tau=tau)
    if type(result) == list:
        rms = [sp.sqrt(item) for item in result]
    else:
        rms = sp.sqrt(result)
    return rms

def PdBm2V(p, r):
    """
    Returns the RMS value of the voltage that generates *p* dBm power
    in a resistor with resistance *r*.

    :param p: Power in dBm
    :type p:  sympy.Symbol, sympy.Expression, int, or float

    :param r: Resistance
    :type r:  sympy.Symbol, sympy.Expression, int, or float

    :return: voltage
    :rtype: sympy.Expression
    """
    voltage = sp.sqrt(r * 0.001*10**(p/10))
    return voltage

def float2rational(expr):
    """
    Converts floats in expr into rational numbers.

    :param expr: Sympy expression in which floats need to be converterd into
                 rational numbers.
    :type expr: sympy.Expression

    :return: expression in which floats have been replaced with rational numbers.
    :rtype:  sympy.Expression
    """
    if type(expr) == int:
        pass
    elif type(expr) == float:
        expr = sp.Rational(expr)
    else:
        try:
            expr = expr.xreplace({n: sp.Rational(str(n))
                                 for n in expr.atoms(sp.Float)})
        except AttributeError:
            pass
    return expr

def rational2float(expr):
    """
    Converts rational numbers in expr into floats.

    :param expr: Sympy expression in which rational numbers need to be
                 converterd into floats.
    :type expr: sympy.Expression

    :return: expression in which rational numbers have been replaced with floats.
    :rtype:  sympy.Expression
    """
    try:
        for atom in expr.atoms():
            if isinstance(atom, sp.core.numbers.Rational) and not isinstance(atom, sp.core.numbers.Integer):
                expr = expr.xreplace({atom: sp.Float(atom, ini.disp)})
    except AttributeError:
        pass
    return expr

def roundN(expr, numeric=False):
    """
    Rounds all float and rational numbers in an expression to ini.disp digits,
    and converts integers into floats if their number of digits exceeds ini.disp

    :param expr: Input expression
    :type expr: sympy.Expr

    :param numeric: True if numeric evaluation (pi = 3.14...) must be done
    :type numeric: Bool

    :return: modified expression
    :rtype: sympy.Expr
    """
    if not isinstance(expr, sp.core.Basic):
        try:
            expr = sp.sympify(str(expr))
        except sp.SympifyError:
            print("Error in expression:", expr)
            return None
    if numeric:
        expr = sp.N(expr, ini.disp)
    else:
        # Convert rationals into floats
        expr = rational2float(expr)
    # Clean-up the expression
    try:
        # Round floats to display accuracy
        expr = expr.xreplace({n: sp.Float(n, ini.disp)
                             for n in expr.atoms(sp.Float)})
        # Convert floats to int if they can be displayed as such
        maxInt = 10**ini.disp
        floats = expr.atoms(sp.Float)
        for flt in floats:
            intNumber = int(flt)
            if float(intNumber) == float(flt) and sp.Abs(flt) < maxInt:
                expr = expr.xreplace({flt: intNumber})
        # Replace large integers with floats
        ints = expr.atoms(sp.Integer)
        for integer in ints:
            if sp.Abs(integer) >= maxInt:
                expr = expr.xreplace({integer: sp.Float(integer, ini.disp)})
    except AttributeError:
        pass
    return expr

def ilt(expr, s, t, integrate=False):
    """
    Returns the Inverse Laplace Transform f(t) of an expression F(s) for t > 0.

    :param expr: Function of the Laplace variable F(s).
    :type expr: Sympy expression, integer, float, or str.

    :param s: Laplace variable
    :type s: sympy.Symbol

    :param t: time variable
    :type t: sympy.Symbol

    :param integrate: True multiplies expr with 1/s, defaults to False
    :type integrate: Bool

    :return: Inverse Laplace Transform f(t)
    :rtype: sympy.Expr
    """
    inv_laplace = None
    if type(expr) == float or type(expr) == int:
        expr = sp.N(expr)
    elif type(expr) == str:
        expr = sp.sympify(expr)
    variables = sp.N(expr).atoms(sp.Symbol)
    if len(variables) == 0 or s not in variables:
        inv_laplace = sp.DiracDelta(t)*expr
    elif len(variables) == 1:
        num, den = expr.as_numer_denom()
        if num.is_polynomial() and den.is_polynomial():
            polyDen = sp.Poly(den, s)
            gainD = sp.Poly.LC(polyDen)
            denCoeffs = polyDen.all_coeffs()
            denCoeffs = [sp.N(coeff/gainD) for coeff in denCoeffs]
            if integrate:
                denCoeffs.append(0)
            den = Polynomial(np.array(denCoeffs[::-1], dtype=float))
            rts = den.roots()
            rootDict = {}
            for rt in rts:
                if rt not in rootDict.keys():
                    rootDict[rt] = 1
                else:
                    rootDict[rt] += 1
            rts = rootDict.keys()
            polyNum = sp.Poly(num, s)
            numCoeffs = polyNum.all_coeffs()
            numCoeffs = [sp.N(numCoeff/gainD) for numCoeff in numCoeffs]
            num = sp.Poly(numCoeffs, s)
            inv_laplace = 0
            for root in rts:
                # get root multiplicity
                n = rootDict[root]
                # build the function
                fs = num.as_expr()*sp.exp(s*t)
                for rt in rts:
                    if rt != root:
                        fs /= (s-rt)**rootDict[rt]
                # calculate residue
                if n == 1:
                    inv_laplace += fs.subs(s, root)
                else:
                    inv_laplace += (1/sp.factorial(n-1)) * \
                        sp.diff(fs, (s, n-1)).subs(s, root)

            inv_laplace = assumeRealParams(inv_laplace)
            inv_laplace = inv_laplace.as_real_imag()[0]
            if sp.I in inv_laplace.atoms():
                inv_laplace = inv_laplace.rewrite(sp.cos).simplify().trigsimp()
            inv_laplace = clearAssumptions(inv_laplace)
        else:
            # If the numerator or denominator cannot be written as a polynomial in 's':
            # use the sympy inverse_laplace_transform() method
            inv_laplace = _symilt(expr, s, t, integrate=integrate)
    else:
        # If one or more polynomial coefficients are symbolic:
        # use the sympy inverse_laplace_transform() method
        inv_laplace = _symilt(expr, s, t, integrate=integrate)
    return inv_laplace

def _symilt(expr, s, t, integrate=False):
    """
    Returns the Inverse Laplace Transform f(t) of an expression F(s) for t > 0.

    :param expr: Function of the Laplace variable F(s).
    :type expr: Sympy expression.

    :param s: Laplace variable
    :type s: sympy.Symbol

    :param t: time variable
    :type t: sympy.Symbol

    :param integrate: True multiplies expr with 1/s, defaults to False
    :type integrate: Bool

    return: Inverse Laplace Transform f(t)
    :rtype: sympy.Expr
    """
    if integrate:
        expr = expr/s
    inv_laplace = sp.inverse_laplace_transform(expr, s, t)
    # Remove the Heaviside function; positive time only
    return inv_laplace.replace(sp.Heaviside(t), 1)

def nonPolyCoeffs(expr, var):
    """
    Returns a dictionary with coefficients of negative and positive powers
    of var.

    :param var: Variable of which the coefficients will be returned
    :type var: sympy.Symbol

    :return: Dict with key-value pairs:

             - key: order of the variable
             - value: coefficient of that order
    """
    error = True
    i = 0
    while error:
        try:
            p = sp.Poly(expr*var**i, var)
            error = False
        except sp.PolynomialError:
            i += 1
    coeffDict = {}
    coeffs = p.all_coeffs()
    coeffs.reverse()
    for j in range(len(coeffs)):
        coeffDict[j-i] = coeffs[j]
    return (coeffDict)

def ENG(number, scaleFactors=False):
    """
    Converts a number into a tuple with a number and exponent as power of 3 or 
    as scale factor.

    :param number: Anything representing a number
    :type mumber: str, int, float, sympy.Expr, sympy.Float

    :param scaleFactors: if 'True', scale factors 'y', 'z', 'a', 'f', 'p', 'n', 
                         'u', 'm', 'k', 'M', 'G', 'T', and 'P' will be returned
                         instead of exponents -24, -21, -18, -15, -12, -9, -6, 
                         -3, 3, 6, 9, 12, and 15, respectively.
    :type scaleFactors: Bool

    :return: number, exp
    :rtype: tuple:

            - number: int, float, or input type if conversion failed
            - exp: int, str (in case of scaleFactors == True), or None, 
              if conversion failed

    Example:

    >>> import SLiCAP as sl
    >>> import sympy as sp

    >>> sl.ini.disp # number of significant digits to be diplayed
        4

    >>> sl.ENG(sp.sqrt(sp.pi))
        (1.772, 0)

    >>> sl.ENG(1234567890)
        (1.234, 9)

    >>> sl.ENG(1234567890, scaleFactors=True)
        (1.234, 'G')

    >>> sl.ENG(1.234567890E-4)
        (123.4, -6)

    >>> sl.ENG(1.234567890E-4, scaleFactors=True)
        (123.4, 'u')

    """
    SCALEFACTORS = {-24: 'y', -21: 'z', -18: 'a', -15: 'f', -12: 'p', -9: 'n',
                    -6: 'u',  -3: 'm', +3: 'k', +6: 'M', +9: 'G', +12: 'T', +15: 'P'}
    exp = None
    try:
        if type(number) != float:
            number = float(number)
        sgn = np.sign(number)
        absValue = np.abs(number)
        if absValue != 0:
            exp = int(np.log10(absValue)/3)*3
            if sgn == 0:
                sign = "-"
            else:
                sign = "+"
            if exp < 0:
                exp -= 3
            number = number/(10**exp)
        number = str(number)
        if number[-1] == '.':
            number = number[:-1]
        number = eval(number)
        if scaleFactors:
            try:
                exp = SCALEFACTORS[exp]
            except KeyError:
                pass
    except:
        pass
    if exp == 0:
        exp = None
    return number, exp

def listPZ(pzResult):
    """
    Prints lists with numeric poles and zeros.

    :param pzResult: SLiCAP execution results of pole-zero analysis.
    :type pzResult: SLiCAPprotos.allResults

    :return: None
    :rtype: NoneType
    """
    if pzResult.step == False:
        # Parameter stepping is not supported
        try:
            DCvalue = sp.simplify(pzResult.DCvalue)
            print('DC value of {:}: {:8.2e}'.format(
                pzResult.gainType, float(DCvalue)))
        except:
            pass
        if pzResult.dataType == 'poles' or pzResult.dataType == 'pz':
            if len(pzResult.poles) != 0:
                print('\nPoles of ' + pzResult.gainType + ':\n')
                poles = pzResult.poles
                if ini.hz:
                    print(" {:2} {:15} {:15} {:15} {:9}".format(
                        'n', 'Real part [Hz]', 'Imag part [Hz]', 'Frequency [Hz]', '   Q [-]'))
                else:
                    print(" {:2} {:15} {:15} {:15} {:9}".format(
                        'n', 'Real   [rad/s]', 'Imag   [rad/s]', 'Freq.  [rad/s]', '   Q [-]'))
                print("--  --------------  --------------  --------------  --------")
                for i in range(len(poles)):
                    pole = poles[i]
                    if ini.hz:
                        pole = pole/2/np.pi
                    realPart  = np.real(pole)
                    imagPart  = np.imag(pole)
                    frequency = np.abs(pole)
                    if imagPart != 0:
                        Q = np.abs(frequency/2/realPart)
                        print("{:2} {:15.2e} {:15.2e} {:15.2e} {:9.2e}".format(
                            i, float(realPart), float(imagPart), float(frequency), Q))
                    else:
                        print("{:2} {:15.2e} {:15.2e} {:15.2e}".format(
                            i, float(realPart), 0.0, float(frequency)))
            else:
                print('\nFound no poles.')
        if pzResult.dataType == 'zeros' or pzResult.dataType == 'pz':
            if len(pzResult.zeros) != 0:
                print('\nZeros of ' + pzResult.gainType + ':\n')
                zeros = pzResult.zeros
                if ini.hz:
                    print(" {:2} {:15} {:15} {:15} {:9}".format(
                        'n', 'Real part [Hz]', 'Imag part [Hz]', 'Frequency [Hz]', '   Q [-]'))
                else:
                    print(" {:2} {:15} {:15} {:15} {:9}".format(
                        'n', 'Real   [rad/s]', 'Imag   [rad/s]', 'Freq.  [rad/s]', '   Q [-]'))
                print("--  --------------  --------------  --------------  --------")
                for i in range(len(zeros)):
                    zero = zeros[i]
                    if ini.hz:
                        zero = zero/2/np.pi
                    realPart  = np.real(zero)
                    imagPart  = np.imag(zero)
                    frequency = np.abs(zero)
                    if imagPart != 0:
                        Q = np.abs(frequency/2/realPart)
                        print("{:2} {:15.2e} {:15.2e} {:15.2e} {:9.2e}".format(
                            i, float(realPart), float(imagPart), float(frequency), Q))
                    else:
                        print("{:2} {:15.2e} {:15.2e} {:15.2e}".format(
                            i, float(realPart), 0.0, float(frequency)))
            else:
                print('\nFound no zeros.')
    else:
        print('\nlistPZ() does not support parameter stepping.')
    print('\n')
    return

def _integrate_all_coeffs(poly, x, x_lower, x_upper, doit=True):
    results = {}
    terms = zip(poly.coeffs(), poly.monoms())
    for coeff, (exp_1, exp_2) in terms:
        coeff = sp.factor(coeff)
        if doit and (len(coeff.atoms(sp.Symbol)) == 0 or coeff.atoms(sp.Symbol) == {x}):
            coeff_func = sp.lambdify(x, coeff)
            integral, error = quad(coeff_func, x_lower, x_upper)
        else:
            try:
                if doit:
                    integral = sp.integrate(coeff, (x, x_lower, x_upper))
                else:
                    integral = sp.Integral(coeff, (x, x_lower, x_upper))
            except:
                raise NotImplementedError()
        results[(exp_1, exp_2)] = integral
    return results

def _integrateCoeffs2(func, variables, x, x_lower, x_upper, doit=True):
    # Find the highest order terms in the denominator
    numer, denom = func.as_numer_denom()
    poly_denom = sp.Poly(denom, variables[0], variables[1])
    max_degree = poly_denom.total_degree()
    for exponents in poly_denom.monoms():
        if sum(exponents) == max_degree:
            var0_order, var1_order = exponents

    # Change the order to use sp.Poly
    poly = sp.Poly(sp.simplify(
        func * variables[0]**var0_order * variables[1]**var1_order), variables[0], variables[1])

    # Integrate the polynomial coefficients numerically
    integratedCoeffs = _integrate_all_coeffs(
        poly, x, x_lower, x_upper, doit=doit)
    return integratedCoeffs, exponents

def integrated_monomial_coeffs(expr, variables, x, x_lower, x_upper, doit=True):
    """
    Returns a dictionary with key-value pairs:

    - key: monomial of variables
    - coefficient of this monomial with x integrated over the range 
      x_lower ... x_upper. 

    If doit=True the integration will be performed, else integral operators 
    will be returned.

    :param expr: Sympy expression
    :type param: sympy.expr

    :param variables: List or tuple with variables  
                      (currently only two variables accepted)

    :type variables: list with sympy.Symbol objects

    :param x: integration variable
    :type x: sympy.Symbol

    :param x_lower: start value integration
    :type x_lower: sympy.Symbol, int or float

    :param x_upper: end value integration
    :type x_upper: sympy.Symbol, int or float

    :param doit: True/False; If True, the integration will be performed, 
                 else integral operators will be returned.
    :type doit: bool

    :return: Dictionary with key-value pairs:

             - key (sympy.Expr): monomial
             - value (sympy.Expr): integrated monomial coefficient

    :rtype: sympy.expr, int or float
    """

    if len(variables) == 2:
        integrated_coeffs, orders = _integrateCoeffs2(
            expr, variables, x, x_lower, x_upper, doit=doit)
    else:
        raise NotImplementedError(
            "Only two-variable monomials are implemented.")
    new_coeffs = {}
    for key in integrated_coeffs.keys():
        newkey = variables[0]**(key[0]-orders[0]) * \
            variables[1]**(key[1]-orders[1])
        new_coeffs[newkey] = integrated_coeffs[key]
    return new_coeffs

def integrate_monomial_coeffs(expr, variables, x, x_lower, x_upper, doit=True):
    """
    Returns expr in which x in coefficients of monomials of 
    variables are integrated over the range x_lower ... x_upper. If doit=True
    the integration will be performed, else integral operators will be returned.

    :param expr: Sympy expression
    :type param: sympy.expr

    :param variables: List or tuple with variables
                      (currently only two variables accepted)

    :type variables: list with sympy.Symbol objects

    :param x: integration variable
    :type x: sympy.Symbol

    :param x_lower: start value integration
    :type x_lower: sympy.Symbol, int or float

    :param x_upper: end value integration
    :type x_upper: sympy.Symbol, int or float

    :param doit: True/False; If True, the integration will be performed, 
                 else integral operators will be returned.
    :type doit: bool

    :return: Integration result
    :rtype: sympy.expr, int or float
    """
    integratedCoeffs = integrated_monomial_coeffs(
        expr, variables, x, x_lower, x_upper, doit=doit)
    integratedResult = sum(sp.Mul(key, integratedCoeffs[key], evaluate=doit)
                           for key in integratedCoeffs.keys())
    return integratedResult

def units2TeX(units):
    """
    Returns units in LaTeX format, without opening and closing '$'.

    :param units: String representing an expression with units
    :type units: str

    :return: LaTeX code of 'units' without opening or closing tags.
    :rtype: str
    """
    if type(units) == str and units != '':
        replacements = {}
        replacements['Ohm'] = 'Omega'
        for key in replacements.keys():
            units = units.replace(key, replacements[key])
        tex = ""
        for unitpart in units.split():
            tex += py2tex(unitpart, print_latex=False,
                          print_formula=False, simplify_output=False)[2:-2] + " "
    return tex[:-1]

def filterFunc(f_char, f_type, f_order, f_low=None, f_high=None, ripple=1):
    """
    Returns a f_type prototype function based on a f_char polynomial:

    - f_char = butterworth
    - f_char = bessel
    - f_char = chebyshev1 # Chebyshev type 1 (passband ripple)

    - f_type = lp : low-pass,  requires f_high
    - f_type = hp : high-pass, requires f_low
    - f_type = bp : band-pass, requires f_low and f_high
    - f_type = bs : band-stop, requires f_low and f_high
    - f_type = ap : all-pass,  requires f_high

    :param f_char: filter characteristic: Butterworth or Bessel
    :type f_char:  str

    :param f_type: filter type: lp, hp, bp, bs, ap
    :type f_type:  str

    :param f_order: order of the filter
    :type f_order:  str, int

    :param f_low:  low-frequency -3dB corner [Hz]
    :type f_low:   sympy.Symbol, float, int

    :param f_high: high-frequency -3dB corner [Hz]
    :type f_high:  sympy.Symbol, float, int

    :param ripple: pass-band ripple in [dB]
    :type ripple: int, float

    :return: Filter prototype function (Laplace Transform)
    :rtype: sympy.Expr
    """
    f_char = f_char.lower()
    f_type = f_type.lower()
    f_order = int(f_order)
    if f_char == "butterworth":
        proto = butterworthPoly(f_order)
    elif f_char == "bessel":
        proto = besselPoly(f_order)
    elif f_char == "chebyshev1":
        proto = chebyshev1Poly(f_order, ripple)
    if f_type == "lp":
        if f_high != None:
            proto = 1/proto.subs(ini.laplace, ini.laplace/(2*sp.pi*f_high))
        else:
            print("Error: missing f_high")
    elif f_type == "hp":
        if f_low != None:
            proto = normalizeRational(sp.simplify(
                1/proto.subs(ini.laplace, 2*sp.pi*f_low/ini.laplace)))
        else:
            print("Error: missing f_low")
    elif f_type == "ap":
        if f_high != None:
            proto = proto.subs(ini.laplace, -ini.laplace)/proto
            proto = proto.subs(ini.laplace, ini.laplace/(2*sp.pi*f_high))
        else:
            print("Error: missing f_high")
    else:
        if f_low != None and f_high != None:
            B = f_high - f_low
            f_c = sp.sqrt(f_low * f_high)
            Q = f_c/B
            if f_type == "bp" and f_c != None:
                proto = 1/proto.subs(ini.laplace, Q *
                                     (ini.laplace+1/ini.laplace))
                proto = normalizeRational(sp.simplify(
                    proto.subs(ini.laplace, ini.laplace/(2*sp.pi*f_c))))
            elif f_type == "bs" and f_c != None:
                proto = 1/proto.subs(ini.laplace, 1 /
                                     (Q*(ini.laplace+1/ini.laplace)))
                proto = normalizeRational(sp.simplify(
                    proto.subs(ini.laplace, ini.laplace/(2*sp.pi*f_c))))
        elif f_low == None:
            print("Error: missing f_low")
        else:
            print("Error: missing f_high")
    return proto

def DIN_A(f_0=1000):
    """
    Returns DIN_A frequency weighting function (audio), normalized at f=f_0

    See WiKi R_A(f): https://en.wikipedia.org/wiki/A-weighting

    :param f_0: Normalization frequency (frequency at which the weighting = 1),
                defaults to 1kHz
    :type f_0: float, int, sympy.Symbol

    :return: R_A(f): Weighting function, argument = ini.frequency
    :rtype: sympy.Expr
    """
    f = ini.frequency
    DIN_A = 12194**2*f**4/((f**2+20.6**2)*(f**2+12194**2)
                           * sp.sqrt((f**2+107.7**2)*(f**2+737.9**2)))
    # normalized the weighting function w.r.t. 1kHz
    return float2rational(DIN_A / DIN_A.subs(f, f_0))

if __name__ == "__main__":
    from time import time
    ini.hz = True
    """
    t = sp.Symbol('t')
    s = sp.Symbol('s')
    k = sp.Symbol('k')
    eps = sp.Symbol('epsilon')
    loopgain_numer   = sp.sympify('-s*(1 + s/20)*(1 + s/40)/2')
    loopgain_denom   = sp.sympify('(s + 1)^2*(1 + s/4e3)*(1 + s/50e3)*(1 + s/1e6)')
    loopgain         = loopgain_numer/loopgain_denom
    servo_info       = findServoBandwidth(loopgain)
    print(servo_info)

    charPoly = s**4+2*s**3+(3+k)*s**2+(1+k)*s+(1+k)
    #charPoly = 10 + 11*s +4*s**2 + 2*s**3 + 2*s**4 + s**5
    #charPoly = s**4-1
    #charPoly = s**5+s**4+2*s**3+2*s**2+s+1
    #roots = _numRoots(charPoly, ini.laplace)
    print(routh(charPoly, eps))

    numer    = sp.sympify('3*f/4+b*s+c*s^2')
    denom    = sp.sympify('a+b*s+c*s^2+d*s^3')
    rational = normalizeRational(numer/denom)
    print(rational)

    gain     = gainValue(numer, denom)
    print(gain)

    M = sp.sympify('Matrix([[0, 0, 0, 0, 0, 1, 0], [0, -2, 0, 0, g_m1, g_m1, 0], [0, 0, -2, g_m2, -g_m2, 0, 0], [0, 1, 0, 1/2*c_i2*s + 1/2/r_o1, -1/2*c_i2*s + 1/2/r_o1, 0, 0], [0, 1, -1, -1/2*c_i2*s + 1/2/r_o1, 1/2*c_i1*s + 1/2*c_i2*s + 1/2/r_o2 + 1/2/r_o1 + 1/2/R, 1/2*c_i1*s, -1/2/r_o2], [1, 0, 0, 0, 1/2*c_i1*s, 1/2*c_i1*s, 0], [0, 0, 1, 0, -1/2/r_o2, 0, 1/2/r_o2 + 1/R_L]])')
    t1=time()
    DME = det(M, method="ME")
    t2 = time()
    print("Minor expansion :", t2-t1, 's')
    DBS = det(M, method="BS")
    t3= time()
    print("Bareis          :", t3-t2, 's')

    M = sp.sympify('Matrix([[0, 1, -1, 0, 0], [1, 1/R_GND + 1/R_1, 0, 0, -1/R_1], [-1, 0, 1/R_1, -1/R_1, 0], [0, 0, -1/R_1, 1/R_2 + 1/R_1, -1/R_2], [0, -1/R_1, 0, -1/R_2, 1/R_2 + 1/R_1]])')
    D = det(M)
    t3=time()
    DM = M.det()
    t4 = time()
    print(sp.simplify(DLU-D))
    print(sp.simplify(DM-D))
    print(t2-t1)
    print(t3-t2)
    print(t4-t3)

    ft = ilt(1/D,s,t)
    #expr = sp.sympify("1/(9e-9*s**9 + 8e-8*s**8 + 7e-7*s**7 + 6e-6*s**6 + 5e-5*s^5 + 4e-4*s^4 + 3e-3*s^3 + 2e-2*s^2 + 1e-1*s +1)")

    #P = partFrac(1/D, s)
    #gt = ilt(expr, s, t)
    expr = "1/(s*(s*R*C+1))"
    ht = ilt(expr, s, t)
    Mnew = M.echelon_form()

    M = sp.sympify("Matrix([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, -158314349441152630406568791890000000000000000000*s**2 - 119366273633481121623000000000000000000000000000000000000*s - 50000000000000000000000000000000000000000000000000000000000, 0, 0, 0, 750000000000000000000000000000000000000000000000000000000000000 - 994718394324345000000000000000000000000000000000000000*s, 7915717472057631520328439594500000000000000000*s**2 + 5968313681674056081150000000000000000000000000000000000*s + 2500000000000000000000000000000000000000000000000000000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, -158314349441152630406568791890000000000000000000*s**2 - 119366273633481121623000000000000000000000000000000000000*s - 50000000000000000000000000000000000000000000000000000000000, 0, 750000000000000000000000000000000000000000000000000000000000000 - 994718394324345000000000000000000000000000000000000000*s, 0, 0, 0, 0, -7915717472057631520328439594500000000000000000*s**2 - 5968313681674056081150000000000000000000000000000000000*s - 2500000000000000000000000000000000000000000000000000000000, 0, 0, 7915717472057631520328439594500000000000000000*s**2 + 5968313681674056081150000000000000000000000000000000000*s + 2500000000000000000000000000000000000000000000000000000000, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, -158314349441152630406568791890000000000000000000*s**2 - 119366273633481121623000000000000000000000000000000000000*s - 50000000000000000000000000000000000000000000000000000000000, 0, 0, 0, 0, 0, 0, 0, 7915717472057631520328439594500000000000000000*s**2 + 5968313681674056081150000000000000000000000000000000000*s + 2500000000000000000000000000000000000000000000000000000000, 0, 0, 750000000000000000000000000000000000000000000000000000000000000 - 994718394324345000000000000000000000000000000000000000*s, 0, 0, 0], [0, 1/200, 0, 0, 0, 0, 677*s/10000000000000 + 1/51000, 0, 0, 0, 0, -s/250000000000, 0, -1/51000, -47*s/10000000000000, 0, 0, 0, 0, 0], [0, 0, -1/200, 0, 0, 0, 0, 449*s/10000000000000 + 1/51000, 0, 0, 0, 0, 0, 0, 0, -39*s/10000000000000 - 1/51000, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0, 51*s/125000000000, 0, 0, 0, 0, 0, 0, -s/2500000000, 0, 0, -s/125000000000, 0], [0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11*s/50000000000 + 1/1000, 0, 0, 0, 0, 0, 0, 0, -1/1000, 0], [0, 0, 0, 0, -1, 0, -s/250000000000, 0, 0, 0, 0, 11*s/125000000000 + 1/25, -1/25, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, -1/25, 1/25, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, -1/51000, 0, 0, 0, 0, 0, 0, s/100000000000 + 1/51000, 0, 0, -s/100000000000, 0, 0, 0], [0, 0, 0, 0, 1, 0, -47*s/10000000000000, 0, 0, 0, 0, 0, 0, 0, 47*s/10000000000000 + 1/300, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, -39*s/10000000000000 - 1/51000, -191833260932509*sqrt(I_D)/100000000000000 - s/2500000000, 0, 0, 0, 0, 0, 0, 96204380357653263*sqrt(I_D)/50000000000000000 + 4439*s/10000000000000 + 101/51000, 0, 0, -287749891398763*sqrt(I_D)/50000000000000000 - s/25000000000, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -s/100000000000, 0, 0, 639*s/20000000000000 + 10403/806000000, -1/80600, -59*s/20000000000000 - 1/2000000, 0], [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1/80600, 1/80600, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 191833260932509*sqrt(I_D)/100000000000000 - s/125000000000, 0, -1/1000, 0, 0, 0, 0, -96204380357653263*sqrt(I_D)/50000000000000000 - s/25000000000, -59*s/20000000000000 - 1/2000000, 0, 287749891398763*sqrt(I_D)/50000000000000000 + 1019*s/20000000000000 + 46003/6000000, -1/150], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1/150, s/1000000000 + 1/150]])")
    t7 = time()
    D = det(M, method="ME")
    t8 = time()
    print("ME", t8-t7)

    t9 = time()
    D = det(M, method="BS")
    t10 = time()
    print("BS", t10-t9)

    LG = sp.sympify("-0.00647263929159112*(1.42481097731728e-5*s**2 + s)/(6.46865378347277e-16*s**3 + 2.0274790076825e-8*s**2 + 0.0014352663537982*s + 1.0)")
    print(findServoBandwidth(LG))

    loopgain_numer   = sp.sympify('-s*(1 + s/20)*(1 + s/40)/2')
    loopgain_denom   = sp.sympify('(s + 1)^2*(1 + s/4e3)*(1 + s/50e3)*(1 + s/1e6)')
    loopgain         = loopgain_numer/loopgain_denom
    print(findServoBandwidth(loopgain))

    loopgain         = sp.sympify('100/((1+s/10)*(1+s/20))')
    print(findServoBandwidth(loopgain))

    loopgain         = sp.sympify('0.01*s^2*(1+s^2/20^2)/((1+s)*(1+s/5)*(1+s/200)*(1+s/800)*(1+s/2000))')
    print(findServoBandwidth(loopgain))

    loopgain         = sp.sympify('100*(1+s)*(1+s/10)/(s^2*(1+s^2/100^2)*(1+s/1000))')
    print(findServoBandwidth(loopgain))

    loopgain         = sp.sympify('-8000000000000000000*pi**3/(s*(s**2 + 4000000*pi*s + 8000000000000*pi**2))')
    print(findServoBandwidth(sp.N(loopgain)))

    loopgain         = sp.sympify('100*(1+s)*(1+s/10)/((1+s^3/100^3)*(1+s/1000))')
    print(findServoBandwidth(loopgain))

    loopgain         = sp.sympify('100/(1+s/1000/2/pi)')
    print(findServoBandwidth(loopgain))
    """
    expr = sp.sympify(
        "4*Gamma*T*k*n*(C_i + C_s + c_iss)**2/(C_i**2*g_m) + K_F*(C_i + C_s)**2/(C_OX*C_i**2*c_iss*f**A_F)")
    g_m, c_iss = sp.symbols("g_m, c_iss")
    variables = (g_m, c_iss)
    f, f_min, f_max = sp.symbols("f, f_min, f_max")
    integratedCoeffs = integrated_monomial_coeffs(
        expr, variables, f, f_min, f_max, doit=False)
    result = integrate_monomial_coeffs(
        expr, variables, f, f_min, f_max, doit=False)
