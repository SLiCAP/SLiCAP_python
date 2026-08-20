#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with math functions.
"""
import numbers
import sys
import subprocess
import sympy as sp
import numpy as np

np.seterr(all = 'ignore')

import SLiCAP.SLiCAPconfigure as ini
from numpy.polynomial import Polynomial
from numpy import trapezoid
from scipy.integrate import quad
from scipy.optimize import fsolve
from SLiCAP.SLiCAPlex import _replaceScaleFactors, _sympify
from pytexit import py2tex
from copy import deepcopy

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
                   - MECPP: Minor expansion by the external C++/GiNaC engine
                     'slicap_det' (see SLiCAP_GiNAC.md). The command is
                     configured in the main configuration file [commands]; if it is not
                     available, det() falls back to 'ME' (same result,
                     computed in Python).
                   - BS: deprecated (removed); redirected to 'ME'
                   - LU: Sympy built-in LU method
                   - bareiss: Sympy built-in Bareis method

    :return: Determinant of 'M'
    :rtype:  sympy.Expr
    """
    M = float2rational(
        sp.Matrix(M))  # Have a Mutable Matrix with rational numbers
    factor = 1
    if M.shape[0] != M.shape[1]:
        print("ERROR: Cannot determine determinant of non-square matrix.")
        D = None
    if method == "BS":
        if not _mecpp_state["warned_bs"]:
            print("Warning: det(method='BS') is deprecated; using 'ME' instead.")
            _mecpp_state["warned_bs"] = True
        method = "ME"
    if method == "MECPP":
        D = _detMECPP(M)
        if D is not None:
            return D
        method = "ME"  # engine unavailable or failed; warning already printed
    if method == "ME" and ini.reduce_matrix and len(M.atoms(sp.Symbol)) > 0:
        M, factor = _eliminateVars(M, method)
    dim = M.shape[0]
    if M.is_zero_matrix:
        D = 0
    elif dim == 1:
        D = M[0, 0] * factor
    elif dim == 2:
        D = sp.expand(M[0, 0]*M[1, 1]-M[1, 0]*M[0, 1]) * factor
    elif method == "ME":
        D = _detME(M) * factor
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

def _eliminateVars(M, method):
    """
    Reduces the size of a matrix through division-free elimination of variables.
    Returns matrix with dim >= 1 and a multiplication factor for the determinant.

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

# State for the external C++/GiNaC determinant engine (method 'MECPP') and
# one-time deprecation warnings; see SLiCAP_GiNAC.md.
_mecpp_state = {"checked": False, "ok": False,
                "warned_missing": False, "warned_bs": False}

def _detMECPP(M):
    """
    Computes the determinant of 'M' with the external C++/GiNaC engine
    'slicap_det' (source: ginac_det/, see SLiCAP_GiNAC.md), using SLiCAP's
    own ME algorithm compiled with exact rational arithmetic.

    Returns the determinant as a sympy expression, or None when the engine
    is not configured, incompatible, or fails — det() then falls back to
    the Python 'ME' implementation, which remains the reference.

    :param M: Square sympy matrix with rational numeric entries
              (float2rational must have been applied).
    :type M: sympy.Matrix
    """
    cmd = ini.slicap_det
    if cmd == "":
        if not _mecpp_state["warned_missing"]:
            print("Warning: no 'slicap_det' command configured in "
                  "the main configuration file [commands]; det(method='MECPP') falls "
                  "back to 'ME'.")
            _mecpp_state["warned_missing"] = True
        return None
    if not _mecpp_state["checked"]:
        _mecpp_state["checked"] = True
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True,
                               text=True)
            _mecpp_state["ok"] = (r.returncode == 0 and
                                  r.stdout.startswith("slicap_det protocol 1"))
        except Exception:
            _mecpp_state["ok"] = False
        if not _mecpp_state["ok"]:
            print("Warning: '{}' is not a compatible slicap_det "
                  "(protocol 1); det(method='MECPP') falls back to "
                  "'ME'.".format(cmd))
    if not _mecpp_state["ok"]:
        return None
    # The wire format carries only alias names (sym0, sym1, ...): sympy
    # symbol names may be unlexable for GiNaC (e.g. the leading underscore
    # of _LGREF_1 in loop-gain analyses), and mapping the aliases back to
    # the ORIGINAL symbol objects preserves assumptions exactly.
    syms = sorted(M.free_symbols, key=lambda x: x.name)
    fwd = {s: sp.Symbol("sym{}".format(k)) for k, s in enumerate(syms)}
    rev = {a: s for s, a in fwd.items()}
    M = M.xreplace(fwd)
    dim = M.shape[0]
    lines = [str(dim)]
    for i in range(dim):
        for j in range(dim):
            lines.append(str(M[i, j]).replace("**", "^"))
    args = [cmd, "--method", "ME"]
    if not ini.reduce_matrix:
        args.append("--no-reduce")
    try:
        r = subprocess.run(args, input="\n".join(lines) + "\n",
                           capture_output=True, text=True)
    except Exception as e:
        print("Warning: slicap_det failed ({}); falling back to 'ME'.".format(e))
        return None
    if r.returncode != 0:
        msg = r.stderr.strip().splitlines()
        msg = msg[0] if msg else "no message"
        print("Warning: slicap_det returned an error ({}); falling back "
              "to 'ME'.".format(msg))
        return None
    try:
        D = _sympify(r.stdout.strip().replace("^", "**"),
                     locals={"Pi": sp.pi, "E": sp.E, "I": sp.I})
    except Exception:
        print("Warning: could not parse slicap_det output; falling back to 'ME'.")
        return None
    return D.xreplace({a: rev[a] for a in D.free_symbols if a in rev})

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

    :return:  Normalized rational function of the variable; input that is
              not a rational function of 'var' (matrices, non-rational
              expressions) is returned unchanged — normalization is a
              presentation step and must pass anything else through.
    :rtype: sympy.Expr
    """
    try:
        gain, numCoeffs, denCoeffs = coeffsTransfer(
            rational, var=var, method=method)
    except (AttributeError, sp.PolynomialError, TypeError):
        return rational
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
    numerValue = numer.xreplace({var: 0})
    denomValue = denom.xreplace({var: 0})
    if numerValue == 0 and denomValue == 0:
        try:
            gain = sp.limit(numer/denom, var, 0)
        except:
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

    :return: Rational number
    :rtype: sympy.rational
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

def str2number(var):
    """
    Returns a number with its value represented by var.

    :param var: Variable that may represent a number.
    :type var: str, sympy object, int, float

    :return: number
    :rtype: float, int
    """
    return eval(_replaceScaleFactors(str(var)))

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
        try:
            complex(item)
        except:
            item = item.evalf()
            params = item.atoms(sp.Symbol)
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
            sym_in = _sympify(expr).atoms(sp.Symbol)
        except sp.SympifyError:
            pass
        out = _replaceScaleFactors(expr)
    else:
        out = str(expr)
    try:
        out = _sympify(out, rational=True)
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
                # Every value takes the string round-trip below (a former
                # sympy-value fast path compared a type against a bool and
                # was dead; removed 2026-07-13, behavior unchanged).
                symval = _sympify(str(parDefs[param]), rational=True)
                if isinstance(symval, sp.Rational) and not isinstance(symval, sp.Integer):
                    # Non-integer rational (e.g. Rational(7293,10000)): use
                    # Float to prevent rational-power lockup in sp.N().
                    # Integers, pi, E, sqrt(2) are all left untouched.
                    substDict[param] = sp.Float(symval, 15)
                else:
                    substDict[param] = symval
        # perform the substitution
        newvalExpr = valExpr
        valExpr = newvalExpr.xreplace(substDict)
        i += 1
    if i == ini.max_rec_subst:
        print("Warning: reached maximum number of substitutions for expression '{0}'".format(
            strValExpr))
    return float2rational(valExpr)

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
            params = sp.N(expr).atoms(sp.Symbol)
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
        #expr = normalizeRational(sp.N(expr))
        expr = sp.N(expr)
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

def _makeNumData(yFunc, xVar, x, normalize=False):
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
            y = [sp.N(yFunc.xreplace({xVar: x[i]})).doit() for i in range(len(x))]
        else:
            func = sp.lambdify(xVar, yFunc, ini.lambdify)
            y = func(x)
    else:
        y = [sp.N(yFunc) for i in range(len(x))]
    return y

def _rational_coeffs_numeric(expr, var):
    """
    Returns (numCoeffs, denCoeffs) as complex lists for a univariate rational
    function of 'var' with numeric coefficients, both scaled by their common
    largest coefficient magnitude so the float conversion cannot overflow
    (the scale cancels in num/den). Returns None when 'expr' is not such a
    function; callers then use their symbolic path.

    :param expr: Function of 'var'.
    :type expr: sympy.Expr

    :param var: Variable of 'expr'
    :type var: sympy.Symbol

    :return: (numCoeffs, denCoeffs) in decreasing order of the exponent of
             'var', or None.
    :rtype: tuple, NoneType
    """
    if not isinstance(expr, sp.Basic):
        return None
    if getattr(expr, "is_Matrix", False):
        return None
    if expr.free_symbols - {var}:
        return None
    num, den = expr.as_numer_denom()
    try:
        npoly = sp.Poly(num, var)
        dpoly = sp.Poly(den, var)
    except sp.PolynomialError:
        return None
    ncoeffs = npoly.all_coeffs()
    dcoeffs = dpoly.all_coeffs()
    try:
        scale = max(sp.Abs(c) for c in ncoeffs + dcoeffs)
        if scale == 0:
            return [0.0], [1.0]
        ncoeffs = [complex(c / scale) for c in ncoeffs]
        dcoeffs = [complex(c / scale) for c in dcoeffs]
    except (TypeError, ValueError):
        return None
    return ncoeffs, dcoeffs

def _freq_response(LaplaceExpr, f):
    """
    Numeric complex frequency response of 'LaplaceExpr': the Laplace
    variable is replaced with 2*pi*1j*f (ini.hz == True) or 1j*f
    (ini.hz == False) and the rational function is evaluated with numpy
    on its scaled float coefficients — no symbolic evaluation.

    Returns None when 'LaplaceExpr' is not a univariate rational function
    of the Laplace variable with numeric coefficients; callers then fall
    back to their symbolic path.

    :param LaplaceExpr: Univariate function of the Laplace variable.
    :type LaplaceExpr: sympy.Expr

    :param f: Frequency value, list or array of frequency values.

    :return: Complex response array (shape of f), or None.
    :rtype: numpy.ndarray, NoneType
    """
    coeffs = _rational_coeffs_numeric(LaplaceExpr, ini.laplace)
    if coeffs is None:
        return None
    ncoeffs, dcoeffs = coeffs
    w = np.asarray(f, dtype=float)
    jw = 2j * np.pi * w if ini.hz else 1j * w
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        return np.polyval(ncoeffs, jw) / np.polyval(dcoeffs, jw)

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
    H = _freq_response(LaplaceExpr, f)
    if H is not None:
        return np.abs(H)
    #LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    LaplaceExpr = sp.N(LaplaceExpr)
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
    H = _freq_response(LaplaceExpr, f)
    if H is not None:
        with np.errstate(divide='ignore', invalid='ignore'):
            return 20 * np.log10(np.abs(H))
    #LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    LaplaceExpr = sp.N(LaplaceExpr)
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
    H = _freq_response(LaplaceExpr, f)
    if H is not None:
        phase = np.asarray(np.angle(H))
        if phase.ndim:            # unwrap needs a sweep; a scalar f
            phase = np.unwrap(phase)  # (phaseMargin) is returned as-is
        if ini.hz:
            phase = phase * 180 / np.pi
        return phase
    #LaplaceExpr = normalizeRational(sp.N(LaplaceExpr))
    LaplaceExpr = sp.N(LaplaceExpr)
    if type(f) == list:
        f = np.array(f)
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    #data = sp.N(normalizeRational(data, ini.frequency))
    data = sp.N(data)
    if ini.frequency in data.atoms(sp.Symbol):
        try:
            func = sp.lambdify(ini.frequency, data, ini.lambdify)
            phase = np.angle(func(f))
        except BaseException:
            phase = []
            for i in range(len(f)):
                try:
                    phase.append(np.angle(data.xreplace({ini.frequency: f[i]})))
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
    # Numeric implementation (2026-07-11): evaluate the complex response and
    # differentiate the unwrapped phase with groupDelay() — the former
    # symbolic two-point delta trick crashed on object-dtype lambdify
    # results (sympy Float coefficients) and was less accurate. The *delta*
    # parameter is kept for call compatibility but no longer used.
    H = _freq_response(LaplaceExpr, f)
    if H is not None:
        f = np.asarray(f, dtype=float)
        return groupDelay(f, np.real(H), np.imag(H), Hz=ini.hz)
    if type(f) == list:
        f = np.array(f)
    if ini.hz == True:
        data = LaplaceExpr.xreplace({ini.laplace: 2*sp.pi*sp.I*ini.frequency})
    else:
        data = LaplaceExpr.xreplace({ini.laplace: sp.I*ini.frequency})
    if ini.frequency in data.atoms(sp.Symbol):
        #data = sp.N(normalizeRational(data, ini.frequency))
        data = sp.N(data)
        try:
            func = sp.lambdify(ini.frequency, data, ini.lambdify)
            H = np.asarray(func(f), dtype=complex)
            if H.shape != np.shape(f):
                H = np.full(np.shape(f), complex(H))   # constant response
        except BaseException:
            H = np.array([complex(data.xreplace({ini.frequency: float(v)}))
                          for v in f])
        return groupDelay(f, np.real(H), np.imag(H), Hz=ini.hz)
    return np.zeros(len(f))

def _doCDSint(noiseResult, tau, fmin, fmax, method, points=0):
    """
    Returns the integral from ini.frequency = f_min to ini.frequency = f_max,
    of a noise spectrum after multiplying it with (2*sin(pi*ini.frequency*tau))^2

    :param noiseResult: sympy expression of a noise density spectrum in V^2/Hz or A^2/Hz
    :type noiseResult: sympy.Expr, sympy.Symbol, int or float

    :param tau: Time between two samples
    :type tau: sympy.Expr, sympy.Symbol, int or float

    :param fmin: Lower limit of the integral
    :type fmin: sympy.Expr, sympy.Symbol, int or float

    :param fmax: Upper limit of the integral
    :type fmax: sympy.Expr, sympy.Symbol, int or float
    
                   - "auto": automatic selection of integration method
                   - "symbolic": forces symbolic integration 
                   - "scipy": numeric integration using scipy.integrate.quad
                   - "log": numeric integration using numpy.trapezoid with a
                            logarithmic frequency sweep from f_min to f_max 
                            and the number of points set by points
                   - "lin": numeric integration using numpy.trapezoid with a
                            linear frequency sweep from fmin to fmax 
                            and dx=(fmax-fmin)/points
                   - "list": numeric integration using numpy.trapezoid with frequency
                             points taken from points.
                     
                   Defaults to 'auto'
                   
    :type method: str
    
    :param points: Number of frequency points for integration for method="lin"
                   and method="log", or a list with points. Defaults to 0.
                   If type(points) == list f_min, and f_max will be ignored.
    :type points: int, list

    :return: integral of the spectrum from f_min to f_max after corelated double sampling
    :rtype: sympy.Expr, sympy.Symbol, int or float
    """
    # method is determined by parent routine
    _phi = sp.Symbol('_phi', positive=True)
    lim_l = sp.simplify(fmin*tau*sp.pi)
    lim_u = sp.simplify(fmax*tau*sp.pi)
    noiseResult *= ((2*sp.sin(sp.pi*ini.frequency*tau)))**2
    noiseResult = noiseResult.xreplace({ini.frequency: _phi/tau/sp.pi})
    if method == "symbolic":  
        try:
            noiseResult = assumePosParams(noiseResult)
            noiseResultCDSint = sp.integrate(
                sp.simplify(noiseResult/sp.pi/tau), (_phi, lim_l, lim_u))
        except:
            print("ERROR: cannot evaluate integral symbolically.")
            noiseResultCDSint = None  
    else:
        # Use numeric integration
        noise_spectrum    = sp.lambdify( _phi,  sp.N(noiseResult/sp.pi/tau))
        noiseResultCDSint = 0
        lim_l             = float(lim_l)
        lim_u             = float(lim_u)
        i                 = 1
        start             = lim_l
        if method == "scipy":
            while i * np.pi < lim_u:
                noiseResultCDSint += quad(noise_spectrum, start, i*np.pi)[0]
                i += 1
                start += np.pi
            noiseResultCDSint += quad(noise_spectrum, start, lim_u)[0]
        elif method == "lin":
            while i * np.pi < lim_u:
                x = np.linspace(start, i*np.pi, points)
                noiseResultCDSint += trapezoid(noise_spectrum(x), x)
                i += 1
                start += np.pi
            x = np.linspace(start, lim_u, points)
            noiseResultCDSint += trapezoid(noise_spectrum(x), x)
        elif method== "log":
            x = np.geomspace(start, i*np.pi, points)
            while i * np.pi < lim_u:
                noiseResultCDSint += trapezoid(noise_spectrum(x), x)
                i += 1
                start += np.pi
                x = np.linspace(start, i*np.pi, points)
            x = np.linspace(start, lim_u, points)
            noiseResultCDSint += trapezoid(noise_spectrum(x), x)
        elif method == "list":
            noiseResultCDSint += trapezoid(noise_spectrum(points), points)
    return noiseResultCDSint

def doCDS(result, tau):
    """
    Returns a copy of the noise execution result with all onoise results in it
    multiplied with (2*sin(pi*ini.frequency*tau))^2, and deleted inoise results.

    :param result: sympy instruction object, or variable
    :type result: sympy.instruction, int, float, sympy.Expr

    :param tau: Time between two samples
    :type tau: sympy.Expr, sympy.Symbol, int or float

    :return: sympy instruction object
    :rtype: sympy.instruction
    """
    cpy_result = deepcopy(result)
    try:
        terms = cpy_result.onoiseTerms.keys()
        if type(cpy_result.onoise) == list:
            for i in range(len(cpy_result.onoise)):
                cpy_result.onoise[i] *= (2*sp.sin(sp.pi*ini.frequency*tau))**2
                for term in terms:
                    cpy_result.onoiseTerms[term][i] *= (2*sp.sin(sp.pi*ini.frequency*tau))**2
            cpy_result.inoise = []
            for term in cpy_result.inoiseTerms.keys():
                cpy_result.inoiseTerms[term] = []
        else:
            cpy_result.onoise *= (2*sp.sin(sp.pi*ini.frequency*tau))**2
            cpy_result.inoise = None
            for term in terms:
                cpy_result.onoiseTerms[term] *= (2*sp.sin(sp.pi*ini.frequency*tau))**2
                cpy_result.inoiseTerms[term] = None
    except AttributeError:
        cpy_result *= (2*sp.sin(sp.pi*ini.frequency*tau))**2
    return cpy_result

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
                ft_out -= ft.xreplace({t: sp.UnevaluatedExpr(t - t_delay)})
            else:
                t_delay += t_period - t_pulse
                ft_out += ft.xreplace({t: sp.UnevaluatedExpr(t - t_delay)})
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
    P_s = sp.simplify(P_s/P_s.xreplace({s: 0}))
    # Normalize 3 dB frequency
    w = sp.Symbol('w', real=True)
    B_w = sp.Abs(P_s.xreplace({s: sp.I*w}))**2
    func = sp.lambdify(w, B_w - 2)
    w3dB = float2rational(fsolve(func, 10)[0])
    P_s = P_s.xreplace({s: s*w3dB})
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
    B_w = sp.Abs(P_s.xreplace({s: sp.I*w}))**2
    func = sp.lambdify(w, B_w - 2)
    w3dB = float2rational(fsolve(func, 10)[0])
    P_s = P_s.xreplace({s: s*w3dB})
    return P_s

def _doVarNoiseData(noiseData, numeric, method, CDS, tau, fmin, fmax, points, wf):
    """
    Calculates and returns total variance of noise spectra.
    
    :param noiseData: 
        
        a. Dictionary with key-value pairs:
        
          - keys (str): names of noise sources
          - value (expr, list): input or output referred noise spectrum or list with spectra
        
        b. Expression of a noise spectrum or a list of expressions
        
    :type param: dict
    
    :param numeric: True if result needs to be numeric
    :type numeric: Bool
    
    :param method: Integration method, implemented methods are:
        
                   - "auto": automatic selection of integration method
                   - "symbolic": forces symbolic integration 
                   - "scipy": numeric integration using scipy.integrate.quad
                              CDS will use integration per section f=1/tau
                   - "log": numeric integration using numpy.trapezoid with a
                            logarithmic frequency sweep from f_min to f_max 
                            and the number of points (CDS: per section) set by points
                   - "lin": numeric integration using numpy.trapezoid with a
                            linear frequency sweep from fmin to fmax 
                            and the number of points (CDS: per section) set by points
                   - "list": numeric integration using numpy.trapezoid with frequency
                             points taken from points (CDS: switches method to 'scipy').
                     
                   Defaults to 'auto'
                   
    :type method: str

    :param CDS: True if correlated double sampling is required, defaults to False
                If True parameter 'tau' must be given a nonzero finite value
                (can be symbolic). 
                If method=="log" a logarithmic frequency seep will be used from 
                the lowest frequency until the frequency of the first notch: 
                f=1/tau. Linear sweeping will be used for all other frequency 
                segments.
                The number of points per segment will be set to points.
                If type(points) == list, the method will be set to 'scipy'.
    :type CDS: Bool

    :param tau: CDS delay time
    :type tau: str, int, float, sp.Symbol

    :param fmin: Lower limit of the frequency range in Hz.
    :type fmin: str, int, float, sp.Symbol

    :param fmax: Upper limit of the frequency range in Hz.
    :type fmax: str, int, float, sp.Symbol
    
    :param points: Number of frequency points for integration for method="lin"
                   and method="log", or a list with points. Defaults to 0.
                   If type(points) == list f_min, and f_max will be ignored.
    :type points: int, list
    
    :param wf: Frequency weighting function (H(s) or H(f))
    :type wf: str, int, float, sympy expr

    :return: RMS noise over the frequency interval.

            - An expression or value if parameter stepping of the instruction is disabled.
            - A list with expressions or values if parameter stepping of the instruction is enabled.
    :rtype: int, float, sympy.Expr

    """
    errors = False
    if type(wf) == int or type(wf) == float or type(wf) == str:
        wf = _sympify(wf)
    if numeric == True:
        wf = sp.N(wf)
    if ini.laplace in wf.atoms(sp.Symbol):
        wf = wf.subs(ini.laplace, 2*sp.pi*sp.I*ini.frequency)
        wf = assumePosParams(wf)  
        sq_mag_wf = clearAssumptions(sp.simplify(sp.re(wf)**2 + sp.im(wf)**2))
        sq_mag_wf = float2rational(sq_mag_wf)
    else:
        sq_mag_wf = wf**2
    if type(noiseData) == dict:
        noiseSources = list(noiseData.keys())
        if type(noiseData[noiseSources[0]]) == list:
            numSteps = len(noiseData[noiseSources[0]])
        else:
            numSteps = 1
    else:
        if type(noiseData) != list:
            noiseData = [noiseData]
        numSteps = len(noiseData)
        noiseDataDict = {}
        noiseDataDict[0] = noiseData
        noiseData = noiseDataDict
        noiseSources = [0]
    if fmin == sp.oo or fmin == -sp.oo:
        print("Error: lower limit of frequency range cannot be infinite.")
        errors = True
    if fmax == -sp.oo:
        print("Error: frequency range must be positive.")
        errors = True
    if fmax == sp.oo:      
        # Use symbolic integration
        numlimits = False
    else:
        try:
            fmin = float(fmin)
            fmax = float(fmax)
            numlimits = True
        except TypeError:
            numlimits = False
    if numlimits and (fmax <= fmin or fmin < 0 or fmax <=0):
        print("Error in frequency range.")
        errors = True
    if method.lower() == 'list':
        if type(points) == list:
            fmin = points[0]
            fmax = points[-1]
        else:
            print("Error: expected a list with frequencies.")
            errors = True
    var = []
    if not errors:
        for i in range(numSteps):
            var_i    = sp.N(0)
            for src in noiseSources:
                if type(noiseData[src]) != list:
                    data = noiseData[src]
                else:
                    data = noiseData[src][i]
                if numeric:
                    data = sp.N(data) 
                if data != 0:
                    data *= sq_mag_wf
                    data = clearAssumptions(float2rational(data))
                    params = data.atoms(sp.Symbol)
                    if ini.frequency not in params and CDS == False:
                        var_i += data * (fmax - fmin)
                    else:
                        # Determine best method for this term if method="auto"
                        if method == "auto":
                            no_params = False
                            if len(params) == 0 or (len(params) == 1 and ini.frequency in params):
                                no_params = True
                            if not no_params or not numlimits:
                                int_method = "symbolic"
                            elif numlimits:
                                if type(points) == list:
                                    if len(points) > 1:
                                        int_method = "list"
                                    else:
                                        int_method = "scipy"
                                elif int(points) <= 2:
                                    int_method = "scipy"
                                elif int(points) > 2:
                                    if fmin > 0 and CDS == False:
                                     int_method = "log"
                                    else:
                                        int_method = "lin"
                                else:
                                    int_method = "symbolic"
                        else:
                            int_method = method
                        if CDS:
                            var_i += _doCDSint(data, tau, fmin, fmax, method=int_method, points=points)
                        elif int_method == "symbolic":
                            func = assumePosParams(data)
                            var_i += sp.integrate(func, [ini.frequency, fmin, fmax])
                        else:
                            noise_spectrum = sp.lambdify(
                                ini.frequency, sp.N(data))
                            if int_method == "scipy":
                                term = quad(noise_spectrum, fmin, fmax)[0]
                                var_i += term
                            elif int_method == "lin":
                                x = np.linspace(fmin, fmax, points)
                                term = trapezoid(noise_spectrum(x), x=x)
                                var_i += term
                            elif int_method == "list":
                                term = trapezoid(noise_spectrum(points), x=points)
                                var_i += term
                            elif int_method == "log":
                                x = np.geomspace(fmin, fmax, points)
                                term = trapezoid(noise_spectrum(x), x=x)
                                var_i += term
            if numeric == True:
                var.append(sp.N(clearAssumptions(sp.expand(var_i))))
            else:
                var.append(clearAssumptions(sp.expand(var_i)))
    return var

def _varNoise(noiseResult, noise, fmin, fmax, source=None, CDS=False, tau=None, 
              method="auto", points=0, wf=1):
    """
    """
    errors = 0
    var = []
    if type(source) != list:
        sources = [source]
    else:
        sources = source
    numlimits = False
    if CDS:
        if tau == None:
            print(
                "Error: rmsNoise() with CDS=True requires a nonzero finite value for 'tau'.")
            errors += 1
        else:
            try:
                tau = _sympify(str(tau))
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
        elif fMi == 0 and method == "log":
            print("Error: method='log' cannot be combined with fmin=0.")
            errors += 1
        elif fMa > fMi:
            # Numeric values for fmin and fmax and fmax >= fmin
            numlimits = True
        if numlimits:
            fmax = float(fmax)
            fmin = float(fmin)
            
    if noiseResult.dataType != 'noise':
        print("Error: expected dataType noise, got: '{0}'.".format(
            noiseResult.dataType))
        errors += 1
    
    if method != "symbolic" and numlimits == True:
        if noise == "onoise": 
            if type(noiseResult.onoise) != list:
                spectra = [noiseResult.onoise]
            else:
                spectra = noiseResult.onoise
        elif noise == "inoise":
            if type(noiseResult.inoise) != list:
                spectra = [noiseResult.inoise]
            else:
                spectra = noiseResult.inoise
        params = []
        for i in range(len(spectra)):
            params += list(sp.N(spectra[i]).atoms(sp.Symbol))
            params = set(params)                
        if len(params) > 1 or (len(params) == 1 and ini.frequency not in params):
            if method != "symbolic" and method !="auto":
                print("Error: found symbolic data, cannot perform numeric integration.")
                errors += 1
        elif method == "list": 
            if type(points) != list and len(points) < 2:
                print("Error: missing or incomplete list with frequencies.")
                errors += 1
            else:
                for i in range(1, len(points)):
                    try:
                        points[i] = float(points[i])
                        if points[i] <= points[i-1]:
                            print("Error: improper list with frequencies.")
                            errors += 1
                            break
                    except:
                        print("Error: improper list with frequencies.")
                        errors += 1
                        break
                    if errors:
                        break
        elif method == "lin" or method == "log" or method == "scipy": 
            if not numlimits:
                print("Error: integration method requires numeric frequeny range with fmax > fmin.")
                errors += 1
            if method == "log" and (fmin == 0 or fmax == 0):
                print("Error: logarithmic integration cannot include zero.")
                errors += 1             
    if errors == 0:
        if noise == 'onoise':
            noiseData = noiseResult.onoiseTerms
        elif noise == 'inoise':
            noiseData = noiseResult.inoiseTerms
        names = noiseResult.snoiseTerms.keys()
        if len(sources) == 1 and sources[0] == None:
            pass
        else:
            # Check sources names and add if correct
            noiseDataNew = {}
            for src in sources:
                if src in names:
                    noiseDataNew[src] = noiseData[src]
                elif src != None:
                    print("Error: unknown noise source: '{0}'.".format(src))
                    errors += 1
            noiseData = noiseDataNew
        # Now the actual calculation starts
        var = _doVarNoiseData(noiseData, noiseResult.numeric, method, CDS, tau, 
                              fmin, fmax, points, wf)
    if len(var) == 1:
        var = var[0]
    return var

def rmsNoise(noiseResult, noise, fmin, fmax, source=None, CDS=False, tau=None, 
             method="auto", points=0, wf=1):
    """
    Calculates the RMS source-referred noise or detector-referred noise,
    or the contribution of a specific noise source or a collection of sources
    to it.

    :param noiseResult: Results of the execution of an instruction with data
                        type 'noise'.
    :type noiseResult: SLiCAPinstruction.instruction

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
                nonzero value for their 'noise' parameter are accepted.
    :type source: str, list

    :param CDS: True if correlated double sampling is required, defaults to False
                If True parameter 'tau' must be given a nonzero finite value
                (can be symbolic). 
                If method=="log" a logarithmic frequency seep will be used from 
                the lowest frequency until the frequency of the first notch: 
                f=1/tau. Linear sweeping will be used for all other frequency 
                segments.
                The number of points per segment will be set to points.
                If type(points) == list, the method will be set to 'scipy'.
    :type CDS: Bool

    :param tau: CDS delay time
    :type tau: str, int, float, sp.Symbol
    
    :param method: Integration method, implemented methods are:
        
                   - "auto": automatic selection of integration method
                   - "symbolic": forces symbolic integration 
                   - "scipy": numeric integration using scipy.integrate.quad.
                              CDS will use integration per section f=1/tau
                   - "log": numeric integration using numpy.trapezoid with a
                            logarithmic frequency sweep from f_min to f_max 
                            and the number of points (CDS: per section  f=1/tau) set by points
                   - "lin": numeric integration using numpy.trapezoid with a
                            linear frequency sweep from fmin to fmax 
                            and the number of points (CDS: per section  f=1/tau) set by points
                   - "list": numeric integration using numpy.trapezoid with frequency
                             points taken from points (CDS: switches method to 'scipy').
                     
                   Defaults to 'auto'
                   
    :type method: str
    
    :param points: Number of frequency points for integration for method="lin"
                   and method="log", or a list with points. Defaults to 0.
                   If type(points) == list f_min, and f_max will be redefined
                   to the first and the last number in the list.
    :type points: int, list
      
    :param wf: Frequency weighting function (H(s) or H(f))
    :type wf: str, int, float, sympy expr

    :return: RMS noise over the frequency interval.

            - An expression or value if parameter stepping of the instruction is disabled.
            - A list with expressions or values if parameter stepping of the instruction is enabled.
    :rtype: int, float, sympy.Expr
    """
    method = method.lower()
    result = _varNoise(noiseResult, noise, fmin, fmax, source=source, CDS=CDS, 
                       tau=tau, method=method, points=points, wf=wf)
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

    A float is read as the DECIMAL number it displays as: 0.1 becomes 1/10,
    not the binary value a double actually holds
    (3602879701896397/36028797018963968).  Only literal floats are converted;
    symbolic constants and exact numbers are left alone, so
    ``sqrt(2)*x + 0.1*pi + 1/3`` becomes ``sqrt(2)*x + pi/10 + 1/3``.

    :param expr: Sympy expression, matrix, or number in which floats need to
                 be converted into rational numbers.
    :type expr: sympy.Expression, sympy.Matrix, int, float

    :return: expression in which floats have been replaced with rational numbers.
    :rtype:  sympy.Expression
    """
    # ONE reading of a float, whichever way it arrives. A bare number used to
    # go through sp.Rational(float) - the exact BINARY value - while floats
    # inside an expression were read from their printed decimal, so the same
    # 0.1 gave two rationals differing by 1/180143985094819840 and did not
    # cancel. Nothing in SLiCAP hit that branch (sympy sympifies every matrix
    # entry), but exact rank decisions - state-space reduction, pole-zero
    # analysis - are only meaningful with a single definition of "exact"
    # (Anton, 2026-08-16).
    if isinstance(expr, bool):          # bool is a subclass of int
        return expr
    if isinstance(expr, numbers.Integral):
        return expr                     # ints are exact already
    if isinstance(expr, numbers.Real) and not isinstance(expr, sp.Basic):
        # Python and numpy floats: sympify FIRST, so a bare float and a sympy
        # Float of the same value read the same text (repr() of a Python float
        # prints one digit more than sympy's Float, which would disagree).
        return sp.Rational(str(sp.Float(expr)))
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
            expr = _sympify(str(expr))
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

def _ilt_numeric_simple(numCoeffs, rootDict, t):
    """
    Returns the inverse Laplace transform for the all-simple-poles numeric
    case as a real sympy expression, assembled directly from the numeric
    residues:

    Re(c*exp((sigma + j*omega)*t)) = exp(sigma*t)*(Re(c)*cos(omega*t) -
    Im(c)*sin(omega*t))

    summed over ALL roots — conjugate pairs add up correctly by
    construction, so no pairing and no symbolic as_real_imag/trigsimp is
    needed. Returns None when a residue is not finite in float arithmetic;
    ilt() then uses the symbolic residue path.

    :param numCoeffs: Numerator coefficients (numeric, decreasing order).
    :type numCoeffs: list

    :param rootDict: Denominator roots (all with multiplicity 1).
    :type rootDict: dict

    :param t: time variable
    :type t: sympy.Symbol

    :return: Inverse Laplace Transform f(t), or None.
    :rtype: sympy.Expr, NoneType
    """
    rts = np.array(list(rootDict.keys()), dtype=complex)
    try:
        nc = np.array([complex(c) for c in numCoeffs], dtype=complex)
    except (TypeError, OverflowError):
        return None
    if not np.all(np.isfinite(nc)):
        return None
    # spurious imaginary parts on real roots (numpy root finding) are
    # chopped relative to the root scale; genuine high-Q pole pairs are
    # far above this threshold
    tol = 1e-10 * max(float(np.max(np.abs(rts))) if len(rts) else 0.0, 1.0)
    terms = []
    for k, rk in enumerate(rts):
        denom = np.prod(rk - np.delete(rts, k))
        if denom == 0:
            return None
        c = np.polyval(nc, rk) / denom
        if not np.isfinite(c):
            return None
        sigma = float(rk.real)
        omega = float(rk.imag)
        if abs(omega) <= tol:
            omega = 0.0
        decay = sp.exp(sigma*t) if sigma != 0.0 else sp.S.One
        if omega == 0.0:
            terms.append(float(c.real) * decay)
        else:
            terms.append(decay * (float(c.real)*sp.cos(omega*t)
                                  - float(c.imag)*sp.sin(omega*t)))
    return sp.Add(*terms)

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
        expr = _sympify(expr)
    variables = sp.N(expr).atoms(sp.Symbol)
    if len(variables) == 0 or s not in variables:
        inv_laplace = sp.DiracDelta(t)*expr
    elif len(variables) == 1 and s in variables:
        num, den = expr.as_numer_denom()
        if num.is_polynomial() and den.is_polynomial():
            # Cancel exact common polynomial factors first: uncancelled
            # factors (e.g. determinant ratios that are no longer
            # normalized at compute time) add spurious pole/zero pairs to
            # the result and can push the coefficient spread past the
            # float64 range below (found via ASMPT-12, 2026-07-13).
            try:
                num, den = sp.cancel(num/den).as_numer_denom()
            except sp.PolynomialError:
                pass
            polyDen = sp.Poly(den, s)
            gainD = sp.Poly.LC(polyDen)
            denCoeffs = polyDen.all_coeffs()
            # Scale for root finding by the largest coefficient magnitude —
            # roots are scale-invariant and LC-relative ratios can overflow
            # float64 (the residue formula below keeps using gainD).
            scaleD = max(sp.Abs(c) for c in denCoeffs)
            denCoeffs = [sp.N(coeff/scaleD) for coeff in denCoeffs]
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
            if len(rootDict) and max(rootDict.values()) <= 1:
                # all poles simple: assemble the real time function directly
                # from numeric residues — no symbolic as_real_imag/trigsimp
                inv_laplace = _ilt_numeric_simple(numCoeffs, rootDict, t)
            if inv_laplace is None:
                # repeated poles, or non-finite numeric residues:
                # symbolic residue path
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
                        inv_laplace += fs.xreplace({s: root})
                    else:
                        inv_laplace += (1/sp.factorial(n-1)) * \
                            sp.diff(fs, (s, n-1)).xreplace({s: root})

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
        absValue = np.abs(number)
        if absValue != 0:
            # Engineering exponent = largest multiple of 3 not exceeding log10.
            # floor() rounds correctly for both signs (int() truncated toward
            # zero, needing a -=3 hack that over-corrected exact powers of 1000,
            # e.g. 1n -> 1000e-12 instead of 1e-9). log10 is first rounded so
            # floating-point noise does not push a boundary value across a
            # power-of-1000 step; the precision tracks the display resolution
            # (ini.disp significant digits) so only values that are anyway
            # indistinguishable from the boundary at the shown precision snap.
            exp = int(np.floor(round(np.log10(absValue), ini.disp + 1)/3))*3
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
    :type pzResult: SLiCAPinstruction.instruction

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

def _integrate_all_coeffs(poly, x, x_lower, x_upper, doit=True, wf=1, 
                          method="auto", CDS=False, tau=None, 
                          points=1000, numeric=True):
    """
    """
    results = {}
    terms = zip(poly.coeffs(), poly.monoms())
    for coeff, (exp_1, exp_2) in terms:
        coeff = sp.factor(coeff)
        if doit and (len(coeff.atoms(sp.Symbol)) == 0 or coeff.atoms(sp.Symbol) == {x}):
            #coeff_func = sp.lambdify(x, coeff)
            #integral, error = quad(coeff_func, x_lower, x_upper)
            integral = _doVarNoiseData(coeff, numeric, method, CDS, tau, x_lower, x_upper, points, wf=wf)[0]
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

def _integrateCoeffs2(func, variables, x, x_lower, x_upper, doit=True, 
                      wf=1, method="auto", CDS=False, tau=None, 
                      points=1000, numeric=True):
    # Find the highest order terms in the denominator
    numer, denom = func.as_numer_denom()
    poly_denom = sp.Poly(denom, variables[0], variables[1])
    max_degree = poly_denom.total_degree()
    for exponents in poly_denom.monoms():
        if sum(exponents) == max_degree:
            var0_order, var1_order = exponents    
    # Change the order to use sp.Poly 
    denom = sp.simplify(sp.expand(denom) /( variables[0]**var0_order * variables[1]**var1_order))  
    func = numer/denom
    poly = sp.Poly(func, variables[0], variables[1])
    # Integrate the polynomial coefficients numerically
    integratedCoeffs = _integrate_all_coeffs(
        poly, x, x_lower, x_upper, doit=doit, wf=wf, 
        method=method,         CDS=CDS, tau=tau, points=points, 
        numeric=numeric)
    return integratedCoeffs, exponents

def integrated_monomial_coeffs(expr, variables, x, x_lower, x_upper, doit=True, 
                               wf=1, method="auto", CDS=False, tau=None, 
                               points=1000, numeric=True):
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
            expr, variables, x, x_lower, x_upper, doit=doit, 
            wf=wf, method=method, CDS=CDS, tau=tau, 
            points=points, numeric=numeric)
    else:
        raise NotImplementedError(
            "Only two-variable monomials are implemented.")
    new_coeffs = {}
    for key in integrated_coeffs.keys():
        newkey = variables[0]**(key[0]-orders[0]) * \
            variables[1]**(key[1]-orders[1])
        new_coeffs[newkey] = integrated_coeffs[key]
    return new_coeffs

def integrate_monomial_coeffs(expr, variables, x, x_lower, x_upper, doit=True, 
                              wf=1, method="auto", CDS=False, tau=None, 
                              points=1000, numeric=True):
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

    :param CDS: True if correlated double sampling is required, defaults to False
                If True parameter 'tau' must be given a nonzero finite value
                (can be symbolic). 
                If method=="log" a logarithmic frequency seep will be used from 
                the lowest frequency until the frequency of the first notch: 
                f=1/tau. Linear sweeping will be used for all other frequency 
                segments.
                The number of points per segment will be set to points.
                If type(points) == list, the method will be set to 'scipy'.
    :type CDS: Bool

    :param tau: CDS delay time
    :type tau: str, int, float, sp.Symbol
    
    :param method: Integration method, implemented methods are:
        
                   - "auto": automatic selection of integration method
                   - "symbolic": forces symbolic integration 
                   - "scipy": numeric integration using scipy.integrate.quad
                              CDS will use integration per section f=1/tau
                   - "log": numeric integration using numpy.trapezoid with a
                            logarithmic frequency sweep from f_min to f_max 
                            and the number of points (CDS: per section) set by points
                   - "lin": numeric integration using numpy.trapezoid with a
                            linear frequency sweep from fmin to fmax 
                            and the number of points (CDS: per section) set by points
                   - "list": numeric integration using numpy.trapezoid with frequency
                             points taken from points (CDS: switches method to 'scipy').
                     
                   Defaults to 'auto'
                   
    :type method: str
    
    :param points: Number of frequency points for integration for method="lin"
                   and method="log", or a list with points. Defaults to 0.
                   If type(points) == list f_min, and f_max will be ignored.
    :type points: int, list
    
    :param numeric: If True the result will be converted to numeric. 
                    Defaults to True
    :type numeric: Bool

    :return: Integration result
    :rtype: sympy.expr, int or float
    """
    integratedCoeffs = integrated_monomial_coeffs(
        expr, variables, x, x_lower, x_upper, doit=doit, 
                                      wf=wf, method=method, CDS=CDS, 
                                      tau=tau, points=points, numeric=True)
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
    tex = " "
    if type(units) == str and units != '':
        replacements = {}
        replacements['Ohm'] = 'Omega'
        for key in replacements.keys():
            units = units.replace(key, replacements[key])
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
            proto = 1/proto.xreplace({ini.laplace: ini.laplace/(2*sp.pi*f_high)})
        else:
            print("Error: missing f_high")
    elif f_type == "hp":
        if f_low != None:
            proto = normalizeRational(sp.simplify(
                1/proto.xreplace({ini.laplace: 2*sp.pi*f_low/ini.laplace})))
        else:
            print("Error: missing f_low")
    elif f_type == "ap":
        if f_high != None:
            proto = proto.xreplace({ini.laplace: - ini.laplace})/proto
            proto = proto.xreplace({ini.laplace: ini.laplace/(2*sp.pi*f_high)})
        else:
            print("Error: missing f_high")
    else:
        if f_low != None and f_high != None:
            B = f_high - f_low
            f_c = sp.sqrt(f_low * f_high)
            Q = f_c/B
            if f_type == "bp" and f_c != None:
                proto = 1/proto.xreplace({ini.laplace: Q *
                                     (ini.laplace + 1/ini.laplace)})
                proto = normalizeRational(sp.simplify(
                    proto.xreplace({ini.laplace: ini.laplace/(2*sp.pi*f_c)})))
            elif f_type == "bs" and f_c != None:
                proto = 1/proto.xreplace({ini.laplace: 1/(Q*(ini.laplace + 1/ini.laplace))})
                proto = normalizeRational(sp.simplify(
                    proto.xreplace({ini.laplace: ini.laplace/(2*sp.pi*f_c)})))
        elif f_low == None:
            print("Error: missing f_low")
        else:
            print("Error: missing f_high")
    return proto

def DIN_A(f_0=1000):
    """
    Returns DIN_A frequency weighting function (audio), normalized at f=f_0

    See WiKi R_A(f): https://en.wikipedia.org/wiki/A-weighting

    :param f_0: Normalization frequency (frequency at which the weight = 1),
                defaults to 1kHz
    :type f_0: float, int, sympy.Symbol

    :return: R_A(f): Weighting function, argument = ini.frequency
    :rtype: sympy.Expr
    """
    f = ini.frequency
    DIN_A = 12194**2*f**4/((f**2+20.6**2)*(f**2+12194**2)
                           * sp.sqrt((f**2+107.7**2)*(f**2+737.9**2)))
    # normalized the weighting function w.r.t. 1kHz
    return float2rational(DIN_A / DIN_A.xreplace({f: f_0}))

# =============================================================================
# Public signal-processing helpers — type-dispatching (numpy or sympy input)
# =============================================================================

def mag(data, f=None):
    """
    Magnitude of data.

    - numpy array (AC result or noise ASD): returns ``np.abs(data)``.
      Works element-wise on 2D stepped results (shape n_steps × n_sweep).
    - sympy Laplace expression: evaluates ``|H(j·2π·f)|`` at the frequencies
      in *f*.

    :param data: Complex numpy array or sympy Laplace expression.
    :type data: numpy.ndarray, sympy.Expr

    :param f: Frequency array [Hz], required when *data* is a sympy expression.
    :type f: list, numpy.ndarray, NoneType

    :return: Magnitude.
    :rtype: numpy.ndarray, list
    """
    if isinstance(data, np.ndarray):
        return np.abs(data)
    return _magFunc_f(data, f)


def dB(data, f=None, power=False):
    """
    Decibel value of data.

    - numpy array:

      - *power* = ``False`` (default): ``20·log₁₀|data|``.
        Use for complex amplitudes (AC voltages/currents) and noise amplitude
        spectral densities (V/√Hz, A/√Hz).
      - *power* = ``True``: ``10·log₁₀|data|``.
        Use for noise **power** spectral densities (V²/Hz, A²/Hz).

      Note: ``dB(np.sqrt(S_psd))`` and ``dB(S_psd, power=True)`` give identical
      results because ``20·log₁₀(√x) = 10·log₁₀(x)``.

      Works element-wise on 2D stepped results (shape n_steps × n_sweep).

    - sympy Laplace expression: always uses ``20·log₁₀|H(j·2π·f)|``
      in *f*; the *power* flag is ignored.

    :param data: Complex numpy array or sympy Laplace expression.
    :type data: numpy.ndarray, sympy.Expr

    :param f: Frequency array [Hz], required when *data* is a sympy expression.
    :type f: list, numpy.ndarray, NoneType

    :param power: Set ``True`` when *data* is a power spectral density (V²/Hz).
                  Defaults to ``False``.
    :type power: bool

    :return: dB values.
    :rtype: numpy.ndarray, list
    """
    if isinstance(data, np.ndarray):
        factor = 10 if power else 20
        return factor * np.log10(np.abs(data))
    return _dB_magFunc_f(data, f)


def phase(data, f=None, deg=True):
    """
    Phase angle of data.

    - numpy array: unwrapped phase along the last axis (``axis=-1``), so 2D
      stepped results (shape n_steps × n_sweep) are handled row-wise.
      Returns degrees when *deg* is ``True`` (default), radians otherwise.
    - sympy Laplace expression: evaluates ``∠H(j·2π·f)`` at *f* via
      in *f* (always returns degrees when ``ini.hz`` is True).

    :param data: Complex numpy array or sympy Laplace expression.
    :type data: numpy.ndarray, sympy.Expr

    :param f: Frequency array [Hz], required when *data* is a sympy expression.
    :type f: list, numpy.ndarray, NoneType

    :param deg: Return degrees (True, default) or radians (False).
                Ignored for sympy input.
    :type deg: bool

    :return: Phase angle.
    :rtype: numpy.ndarray, list
    """
    if isinstance(data, np.ndarray):
        ph = np.unwrap(np.angle(data, deg=False), axis=-1)
        return np.degrees(ph) if deg else ph
    return _phaseFunc_f(data, f)


def delay(data, f):
    """
    Group delay of data.

    - numpy array: ``-d(phase)/d(ω)`` computed via ``np.gradient`` along
      ``axis=-1``. Works on 2D stepped results (shape n_steps × n_sweep).
    - sympy Laplace expression: evaluated numerically in *f*.

    :param data: Complex numpy array or sympy Laplace expression.
    :type data: numpy.ndarray, sympy.Expr

    :param f: Frequency array [Hz].
    :type f: list, numpy.ndarray

    :return: Group delay [s].
    :rtype: numpy.ndarray, list
    """
    if isinstance(data, np.ndarray):
        return groupDelay(f, np.real(data), np.imag(data), Hz=ini.hz)
    return _delayFunc_f(data, f)


# =============================================================================
# Goal functions — pure numpy, no sympy analogue
# =============================================================================

def YatX(y, x, x0):
    """
    Interpolate *y* at *x* = *x0*.

    For 2D arrays (stepped results, shape n_steps × n_sweep) the interpolation
    is applied row-wise along the last axis and a 1D array of length n_steps is
    returned.

    :param y: Data array (1D or 2D).
    :type y: list, numpy.ndarray

    :param x: X-axis values (1D, same length as the last axis of *y*).
    :type x: list, numpy.ndarray

    :param x0: X value at which to interpolate.
    :type x0: float, int

    :return: Interpolated value(s).
    :rtype: float, numpy.ndarray
    """
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    if y.ndim == 1:
        return float(np.interp(x0, x, y))
    return np.array([float(np.interp(x0, x, row)) for row in y])


def XatNthY(x, y, y0, n=1):
    """
    Find the *n*-th x value where *y* crosses *y0* (linear interpolation at
    the crossing point).

    :param x: X-axis values (1D).
    :type x: list, numpy.ndarray

    :param y: Data values (1D, same length as *x*).
    :type y: list, numpy.ndarray

    :param y0: Target y value (crossing level).
    :type y0: float, int

    :param n: Which crossing to return (1 = first, 2 = second, …).
              Defaults to 1.
    :type n: int

    :return: Interpolated x at the *n*-th crossing, or ``None`` if fewer
             than *n* crossings are found.
    :rtype: float, NoneType
    """
    x      = np.asarray(x, dtype=float)
    shifted = np.asarray(y, dtype=float) - y0
    idx    = np.where(np.diff(np.sign(shifted)))[0]
    if len(idx) < n:
        return None
    i = idx[n - 1]
    return float(x[i] - shifted[i] * (x[i + 1] - x[i]) / (shifted[i + 1] - shifted[i]))


def RMS(y, x=None):
    """
    RMS value of *y*.

    - With *x*: ``sqrt(trapezoid(y², x) / (x[-1] - x[0]))`` — proper
      time- or frequency-domain average.
    - Without *x*: ``sqrt(mean(y²))`` — RMS over the available samples.

    The operation is applied along ``axis=-1`` so 2D stepped results
    (shape n_steps × n_sweep) return a 1D array of length n_steps.

    :param y: Data values.
    :type y: list, numpy.ndarray

    :param x: X-axis values (same length as last axis of *y*). Defaults to None.
    :type x: list, numpy.ndarray, NoneType

    :return: RMS value(s).
    :rtype: float, numpy.ndarray
    """
    y = np.asarray(y, dtype=float)
    if x is None:
        return np.sqrt(np.mean(y ** 2, axis=-1))
    x = np.asarray(x, dtype=float)
    return np.sqrt(np.trapezoid(y ** 2, x, axis=-1) / (x[-1] - x[0]))


def SUM(y, x=None):
    """
    Sum or integral of *y*.

    - With *x*: trapezoid integration along ``axis=-1``.
    - Without *x*: plain ``numpy.sum`` along ``axis=-1``.

    :param y: Data values.
    :type y: list, numpy.ndarray

    :param x: X-axis values. Defaults to None.
    :type x: list, numpy.ndarray, NoneType

    :return: Sum or integral.
    :rtype: float, numpy.ndarray
    """
    y = np.asarray(y, dtype=float)
    if x is None:
        return np.sum(y, axis=-1)
    return np.trapezoid(y, np.asarray(x, dtype=float), axis=-1)


class WeightingFilter(object):
    """
    Single noise weighting filter for use with noiseWeighting().

    Supported filter types (f_type):

    - "lp"     : low-pass,  requires char, f_c, order
    - "hp"     : high-pass, requires char, f_c, order
    - "ap"     : all-pass,  requires char, f_c, order
    - "bp"     : band-pass, requires char, f_c, B, order
    - "bs"     : band-stop, requires char, f_c, B, order
    - "custom" : arbitrary, requires expr (sympy expression in ini.laplace)

    Supported filter characteristics (char):

    - "butterworth"
    - "bessel"
    - "chebyshev1"

    :param f_type: Filter type string (see above).
    :type f_type: str

    :param char: Filter characteristic (butterworth / bessel / chebyshev1).
    :type char: str, NoneType

    :param f_c: Corner frequency [Hz].
    :type f_c: float, int, NoneType

    :param B: Bandwidth [Hz] (band-pass / band-stop only).
    :type B: float, int, NoneType

    :param order: Filter order.
    :type order: int, NoneType

    :param ripple: Pass-band ripple [dB] (chebyshev1 only).
    :type ripple: float, NoneType

    :param expr: Custom sympy expression in ini.laplace (custom type only).
    :type expr: sympy.Expr, str, NoneType
    """
    def __init__(self, f_type, char=None, f_c=None, B=None,
                 order=None, ripple=None, expr=None):
        self.f_type  = f_type
        self.char    = char
        self.f_c     = f_c
        self.B       = B
        self.order   = order
        self.ripple  = ripple
        self.expr    = expr
        self.errors  = False

    def create_expr(self):
        """
        Build self.expr as a Laplace-domain transfer function.

        :return: True if successful, False on error.
        :rtype: bool
        """
        CHARS = ["butterworth", "bessel", "chebyshev1"]
        TYPES = ["lp", "hp", "ap", "bp", "bs", "custom"]
        self.errors = False
        try:
            self.f_type = self.f_type.lower()
        except Exception:
            print("WeightingFilter: unknown filter type.")
            self.errors = True
        if self.f_type not in TYPES:
            print("WeightingFilter: unknown filter type '{}'.".format(self.f_type))
            self.errors = True
        elif self.f_type == "custom":
            try:
                self.expr = _sympify(self.expr)
            except sp.SympifyError:
                print("WeightingFilter: error in custom expression.")
                self.errors = True
        else:
            try:
                self.char = self.char.lower()
                if self.char not in CHARS:
                    print("WeightingFilter: unknown filter characteristic '{}'.".format(self.char))
                    self.errors = True
            except Exception:
                print("WeightingFilter: missing or invalid filter characteristic.")
                self.errors = True
            try:
                self.f_c = float(self.f_c)
                if self.f_c <= 0:
                    print("WeightingFilter: f_c must be > 0.")
                    self.errors = True
                if self.f_type in ("lp", "ap"):
                    f_h, f_l = self.f_c, None
                elif self.f_type == "hp":
                    f_l, f_h = self.f_c, None
                else:
                    f_h, f_l = None, None
            except (TypeError, ValueError):
                print("WeightingFilter: missing or invalid f_c.")
                self.errors = True
            try:
                self.order = int(self.order)
                if self.order <= 0:
                    print("WeightingFilter: order must be > 0.")
                    self.errors = True
            except (TypeError, ValueError):
                print("WeightingFilter: missing or invalid order.")
                self.errors = True
            if self.f_type in ("bp", "bs"):
                try:
                    self.B = float(self.B)
                    if self.B <= 0:
                        print("WeightingFilter: bandwidth B must be > 0.")
                        self.errors = True
                    elif self.B > self.f_c:
                        print("WeightingFilter: B must be < f_c. Use cascaded lp/hp instead.")
                        self.errors = True
                    else:
                        _fl = sp.Symbol("f_low", positive=True)
                        f_l = sp.solve(_fl * self.B + _fl**2 - self.f_c**2, _fl)[0]
                        f_h = f_l + self.B
                except (TypeError, ValueError):
                    print("WeightingFilter: missing or invalid bandwidth B.")
                    self.errors = True
            if self.char == "chebyshev1":
                try:
                    self.ripple = float(self.ripple)
                    if self.ripple <= 0:
                        print("WeightingFilter: ripple must be > 0.")
                        self.errors = True
                except (TypeError, ValueError):
                    print("WeightingFilter: missing or invalid ripple.")
                    self.errors = True
            if not self.errors:
                num, den = filterFunc(self.char, self.f_type, self.order,
                                      f_high=f_h, f_low=f_l,
                                      ripple=self.ripple).as_numer_denom()
                self.expr = sp.expand(num) / sp.expand(den)
        return not self.errors


def noiseWeighting(filters_dict):
    r"""
    Build the combined squared-magnitude noise weighting function from a dict
    of cascaded weighting filters.

    The result is a sympy expression in ini.frequency that evaluates to
    \|H_1(f)\|^2 * \|H_2(f)\|^2 * ... for all cascaded filters. Pass this to
    weightedRMS() to integrate a NGspice noise spectrum with weighting.

    Supported filter-dict keys:

    - "din_a"  : DIN A audio weighting, no sub-parameters needed ({})
    - "cds"    : Correlated Double Sampling; requires {"tau": <value>}
    - "lp","hp","ap","bp","bs" : see WeightingFilter; sub-dict is its kwargs
    - "custom" : see WeightingFilter; sub-dict must contain {"expr": <expr>}

    Example::

        wf = noiseWeighting({
            "din_a": {},
            "hp"   : {"char": "Butterworth", "f_c": 20, "order": 2},
        })

    :param filters_dict: Mapping of filter-type key to parameter dict.
    :type filters_dict: dict

    :return: Squared magnitude of cascaded filters as a sympy expression in
             ini.frequency. Returns 1 if filters_dict is empty.
    :rtype: sympy.Expr
    """
    f = ini.frequency
    sq_mag_wf = sp.Integer(1)
    for key, params in filters_dict.items():
        key_lower = key.lower()
        imag_part = sp.Integer(0)
        if key_lower == "cds":
            par = {k.lower(): v for k, v in params.items()}
            tau = par.get("tau")
            if tau is None:
                print("noiseWeighting: CDS filter requires 'tau' parameter.")
                continue
            real_part = 2 * sp.sin(sp.pi * f * tau)
        elif key_lower == "din_a":
            real_part = DIN_A()
        else:
            par = {k.lower(): v for k, v in params.items()}
            fi = WeightingFilter(key_lower,
                                 char=par.get("char"),
                                 f_c=par.get("f_c"),
                                 B=par.get("b"),
                                 order=par.get("order"),
                                 ripple=par.get("ripple"),
                                 expr=par.get("expr"))
            if not fi.create_expr():
                print("noiseWeighting: skipping invalid filter '{}'.".format(key))
                continue
            expr = sp.N(fi.expr.subs(ini.laplace, 2 * sp.I * sp.pi * f))
            real_part, imag_part = expr.as_real_imag()
        sq_mag_wf = sq_mag_wf * (real_part**2 + imag_part**2)
    return sq_mag_wf


def weightedRMS(spectrum, frequencies, sq_mag_wf=1):
    """
    Apply a noise weighting filter to a numpy noise power spectrum and return
    unweighted and weighted RMS values.

    The weighting is applied outside NGspice: NGspice computes the raw noise
    power spectral density; this function multiplies it by the squared
    magnitude of the weighting filter(s) and integrates.

    :param spectrum: 1D numpy array of noise power spectral density (V^2/Hz
                     or A^2/Hz) as returned by a NGspice noise analysis.
    :type spectrum: numpy.ndarray

    :param frequencies: 1D numpy array of frequency points corresponding to
                        spectrum.
    :type frequencies: numpy.ndarray

    :param sq_mag_wf: Squared magnitude of the weighting filter as a sympy
                      expression in ini.frequency, as returned by
                      noiseWeighting(). Pass 1 (default) for unweighted RMS.
    :type sq_mag_wf: sympy.Expr, int, float

    :return: Tuple (rms_unweighted, rms_weighted, weighted_spectrum) where:

             - rms_unweighted   : float — RMS of the unweighted spectrum
             - rms_weighted     : float — RMS of the weighted spectrum
             - weighted_spectrum : numpy.ndarray — weighted noise PSD (same
               units as spectrum)

    :rtype: tuple
    """
    spectrum    = np.array(spectrum, dtype=float)
    frequencies = np.array(frequencies, dtype=float)
    if sq_mag_wf == 1:
        mag_sq = np.ones_like(frequencies)
    else:
        mag_sq = sp.lambdify(ini.frequency, sp.N(sq_mag_wf),
                             modules='numpy')(frequencies)
    w_spectrum = mag_sq * spectrum
    rms_u = float(np.sqrt(np.trapezoid(spectrum,   frequencies)))
    rms_w = float(np.sqrt(np.trapezoid(w_spectrum, frequencies)))
    return rms_u, rms_w, w_spectrum

def groupDelay(frequency, realPart, imagPart, Hz=True):
    """
    Returns the group delay of a sampled complex frequency response:

    .. math::

        \\tau_g = -\\frac{ d \\varphi }{ d \\omega }

    where the phase :math:`\\varphi` (radians) is obtained from the real
    and imaginary parts and unwrapped before differentiation, and
    :math:`\\omega` is the radian frequency. The finite-difference
    derivative shortens the array by one point; the last point is
    duplicated so the returned array has the same length as *frequency*.

    :param frequency: Frequency values, in Hz (Hz=True, default) or in
                      rad/s (Hz=False). Must be monotonic.
    :type frequency: list, numpy.ndarray

    :param realPart: Real part of the response at each frequency.
    :type realPart: list, numpy.ndarray

    :param imagPart: Imaginary part of the response at each frequency.
    :type imagPart: list, numpy.ndarray

    :param Hz: True if *frequency* is in Hz; the values are then multiplied
               with :math:`2 \\pi` before differentiation. Defaults to True.
    :type Hz: bool

    :return: Group delay in seconds at each frequency; same length as
             *frequency*.
    :rtype: numpy.ndarray
    """
    f  = np.asarray(frequency, dtype=float)
    re = np.asarray(realPart, dtype=float)
    im = np.asarray(imagPart, dtype=float)
    if len(f) < 2:
        return np.zeros_like(f)
    w   = 2*np.pi*f if Hz else f
    phi = np.unwrap(np.arctan2(im, re), axis=-1)
    # np.gradient, NOT np.diff (Anton, 2026-08-01): a difference quotient
    # belongs BETWEEN two samples, so np.diff shortens the array and the old
    # code duplicated the last point to hide it. np.gradient returns a value
    # AT every sample - central differences inside, one-sided at the ends -
    # and stays second-order accurate on the NON-UNIFORM grid of a decade
    # sweep, which is what SLiCAP sweeps look like.
    return -np.gradient(phi, w, axis=-1)

def goal_rms(x, y):
    """RMS of *y* integrated over *x*: ``sqrt(trapz(y², x) / (x[-1] - x[0]))``.

    Suitable as a ``goal_fn`` argument to
    :func:`~SLiCAP.SLiCAPngspice.ngspice_instr2traces` (or
    :func:`~SLiCAP.SLiCAPngspice.ngspice_dict2traces`).

    :param x: 1-D sweep-axis array.
    :type x: numpy.ndarray
    :param y: 1-D signal array (already post-processed by *trace_type*).
    :type y: numpy.ndarray
    :return: RMS value.
    :rtype: float
    """
    x = np.asarray(x, dtype=float)
    y = np.real(np.asarray(y, dtype=float))
    return float(np.sqrt(np.trapezoid(y * y, x) / (x[-1] - x[0])))

def goal_mean(x, y):
    """Mean of *y* over *x*: ``trapz(y, x) / (x[-1] - x[0])``.

    :param x: 1-D sweep-axis array.
    :type x: numpy.ndarray
    :param y: 1-D signal array.
    :type y: numpy.ndarray
    :return: Mean value.
    :rtype: float
    """
    x = np.asarray(x, dtype=float)
    y = np.real(np.asarray(y, dtype=float))
    return float(np.trapezoid(y, x) / (x[-1] - x[0]))

def goal_max(x, y):
    """Maximum value of *y*.

    :param x: 1-D sweep-axis array (unused, present for uniform signature).
    :type x: numpy.ndarray
    :param y: 1-D signal array.
    :type y: numpy.ndarray
    :return: max(y).
    :rtype: float
    """
    return float(np.max(np.asarray(y)))
    
def goal_min(x, y):
    """Miniimum value of *y*.

    :param x: 1-D sweep-axis array (unused, present for uniform signature).
    :type x: numpy.ndarray
    :param y: 1-D signal array.
    :type y: numpy.ndarray
    :return: min(y).
    :rtype: float
    """
    return float(np.min(np.asarray(y)))

def goal_x_at_max_y(x, y):
    """*x* value at which ``y`` is maximum

    :param x: 1-D sweep-axis array.
    :type x: numpy.ndarray
    :param y: 1-D signal array.
    :type y: numpy.ndarray
    :return: x at maximum y.
    :rtype: float
    """
    x = np.asarray(x)
    y = np.asarray(y)
    return float(x[np.argmax(y)])

def goal_x_at_min_y(x, y):
    """*x* value at which ``y`` is minimum.

    :param x: 1-D sweep-axis array.
    :type x: numpy.ndarray
    :param y: 1-D signal array.
    :type y: numpy.ndarray
    :return: x at minimum y.
    :rtype: float
    """
    x = np.asarray(x)
    y = np.asarray(y)
    return float(x[np.argmin(y)])

def goal_y_at_x(x0):
    """Return a goal function that interpolates *y* at *x* = *x0*.

    :param x0: Target x value.
    :type x0: float
    :return: ``goal_fn(x, y)`` callable.
    :rtype: callable

    :Example:

    >>> # Value of v(out) at f = 1 kHz across all steps
    >>> traces = sl.ngspice_instr2traces(AC1, goal_fn=sl.goal_y_at_x(1e3))
    """
    def _goal(x, y):
        x = np.asarray(x, dtype=float)
        y = np.real(np.asarray(y, dtype=float))
        return float(np.interp(x0, x, y))
    _goal.__name__ = f"goal_y_at_x({x0!r})"
    return _goal

def goal_x_at_nth_y(y0, n=1):
    """Return a goal function that gives the *x* of the *n*-th crossing of
    *y* = *y0* (linear interpolation between the samples around the
    crossing; *n* counts from 1). Returns ``x[-1]`` (end of sweep) when
    fewer than *n* crossings exist.

    :param y0: The y level whose crossing is sought.
    :type y0: float
    :param n: Which crossing (1 = first).
    :type n: int
    :return: ``goal_fn(x, y)`` callable.
    :rtype: callable
    """
    def _goal(x, y):
        x = np.asarray(x, dtype=float)
        y = np.real(np.asarray(y, dtype=float))
        above = y >= y0
        crossings = np.where(np.diff(above.astype(int)) != 0)[0]
        if len(crossings) < n:
            return float(x[-1])
        i = crossings[int(n) - 1]
        xa, xb = x[i], x[i + 1]
        ya, yb = y[i], y[i + 1]
        if yb == ya:
            return float(xa)
        return float(xa + (y0 - ya) * (xb - xa) / (yb - ya))
    _goal.__name__ = f"goal_x_at_nth_y({y0!r}, {n!r})"
    return _goal


def goal_int(x, y):
    """Integral of *y* over the sweep, :math:`\\int y \\, dx` (trapezoidal).

    :param x: 1-D sweep-axis array.
    :type x: numpy.ndarray

    :param y: 1-D signal array.
    :type y: numpy.ndarray

    :return: the integral.
    :rtype: float
    """
    x = np.asarray(x, dtype=float)
    y = np.real(np.asarray(y, dtype=float))
    return float(np.trapezoid(y, x))


def goal_sum(x, y):
    """Sum of the values of *y* (the sweep axis is not used)."""
    return float(np.sum(np.real(np.asarray(y, dtype=float))))


def goal_rms_noise(x, y):
    """RMS noise from a SQUARED spectral density: :math:`\\sqrt{\\int S\\,df}`.

    The total noise over the simulated band, computed from the spectrum
    itself rather than from NGspice's ``onoise_total``:
    NGspice computes the input-referred total alongside it, which fails when
    the transfer has transmission zeros. NGspice noise runs always set
    ``sqrnoise``, so ``onoise_spectrum`` is in V^2/Hz and this is the RMS
    output noise in V.

    Integration is trapezoidal over the frequency points as simulated, so a
    decade sweep needs enough points per decade to be accurate.

    :param x: 1-D frequency array.
    :type x: numpy.ndarray

    :param y: 1-D SQUARED spectral density (V^2/Hz or A^2/Hz).
    :type y: numpy.ndarray

    :return: RMS value over the band.
    :rtype: float
    """
    return float(np.sqrt(max(goal_int(x, y), 0.0)))


_GOAL_FUNCTIONS = [
    ("rms",            goal_rms,        []),
    ("rms noise",      goal_rms_noise,  []),
    ("int",            goal_int,        []),
    ("sum",            goal_sum,        []),
    ("mean",           goal_mean,       []),
    ("max",            goal_max,        []),
    ("min",            goal_min,        []),
    ("y at x",         goal_y_at_x,     [("x0", 1e3)]),
    ("x at max y",     goal_x_at_max_y, []),
    ("x at min y",     goal_x_at_min_y, []),
    ("x at nth y",     goal_x_at_nth_y, [("y0", 0.0), ("n", 1)]),
]

if __name__ == "__main__":
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
    DBS = det(M, method="MECPP")
    t3= time()
    print("MECPP           :", t3-t2, 's')

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
    D = det(M, method="MECPP")
    t10 = time()
    print("MECPP", t10-t9)

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
        expr, variables, f, f_min, f_max, doit=False, wf=1, method="auto", CDS=False, tau=None, points=1000, numeric=True)
    result = integrate_monomial_coeffs(
        expr, variables, f, f_min, f_max, doit=False, wf=1, method="auto", CDS=False, tau=None, points=1000, numeric=True)
