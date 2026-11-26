#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP _tokenizer for netlist files.

"""
import ply.lex as lex
import sys
import builtins
import types
import sympy as sp
from sympy.core.parameters import global_parameters
from sympy.parsing.sympy_parser import (null as _null, parse_expr,
                                        standard_transformations, convert_xor,
                                        rationalize, TokenError)
import re

# list of token names

tokens = ('PARDEF', 'EXPR', 'SCALE', 'SCI', 'FLT', 'INT', 'CMD', 'FNAME',
          'PARAMS', 'ID', 'QSTRING', 'PLUS', 'LEFTBR', 'RIGHTBR', 'COMMENT',
          'NEWLINE')

_SCALEFACTORS    =  {'y':'-24','z':'-21','a':'-18','f':'-15','p':'-12','n':'-9',
                    'u':'-6','m':'-3','k':'3','M':'6','G':'9','T':'12','P':'15'} #,
                    #'E':'18','Z':'21','Y':'24'}

# Names that sympy claims in its own namespace, but that a circuit designer
# needs as ordinary parameters: Q (quality factor), beta and gamma (device
# parameters), N, O, S, zeta, Lambda. Listing them here gives them back to the
# user: inside a SLiCAP expression such a name is a circuit variable, or - if
# it is written with brackets - a function of the user's own. sympy's own
# implementations stay reachable from Python code (sp.gamma(5) -> 24, sp.N()),
# they are simply no longer claimed inside expression text.
#
# Within ONE expression a name is either a variable or a function: the first
# occurrence decides, and 'beta*R + beta(2,3)' raises rather than mis-reading
# either. Nothing leaks into the next expression - sympy restores the markers
# (parse_expr does 'local_dict[i] = null' on both the success and error path),
# so one shared dict per call is safe.
#
# NOT in this list, by decision (Anton, 2026-08-19): E, I and pi keep their
# mathematical meaning (Euler, imaginary unit, 3.14...); a current is named
# I_xx. 'lambda' is a Python keyword and cannot be rescued at all: the
# tokenizer refuses it before sympy sees the name. Those four remain the
# reserved symbols documented in the manual.
#
# Forcing plain Symbols (locals={name: sp.Symbol(name)}) was considered and
# REJECTED (2026-08-19): it also removes beta(x), gamma(x) and the other
# sympy functions from expressions. The _null marker below is sympy's own
# mechanism for "this name is not yours to claim" and keeps both meanings.
_SYMPY_NAMES = ("N", "O", "Q", "S", "beta", "gamma", "zeta", "Lambda")


# The names of 'from sympy import *', as parse_expr imports them
# (sympy/parsing/sympy_parser.py). This import is the costly part of the
# namespace of a parse: 0.1 to 0.2 ms. It runs once, at import.
#
# Up to 6.4.8 a string went through sp.sympify. That path cannot pass a
# global_dict, so every parse ran this import again. REPLACED (2026-11-22):
# it took more than half of makeCircuit for a netlist of 401 elements.
_SYMPY_EXPORTS = {}
exec('from sympy import *', _SYMPY_EXPORTS)


def _sympy_namespace():
    """
    Returns the global namespace in which sympy's parse_expr evaluates an
    expression when it is given no global_dict.

    The statements are those of parse_expr (sympy/parsing/sympy_parser.py).
    The names therefore come from sympy itself. tests/test_sympify_namespace.py
    compares the result with the namespace that sympy builds.

    The sympy names come from _SYMPY_EXPORTS. A sympy name that is rebound
    after import is not seen. The builtin functions are read on each call
    (10 to 20 us). Each call returns a new dict.

    :return: name-to-object mapping
    :rtype: dict
    """
    # Building the whole namespace once was tried and REVERTED (2026-11-22).
    # PySide6 replaces builtins.__import__ after SLiCAP is imported. A
    # snapshot then differs from the namespace that sympify builds.
    #
    # Sharing one namespace between parses was considered and REJECTED
    # (2026-11-22). A parse can write into its namespace:
    # '[(pi := 3) for E in [1]]' binds pi there for every later parse.
    namespace = _SYMPY_EXPORTS.copy()
    for name, obj in vars(builtins).items():
        if isinstance(obj, types.BuiltinFunctionType):
            namespace[name] = obj
    namespace['max'] = sp.Max
    namespace['min'] = sp.Min
    return namespace


# The transformations that sp.sympify passes to parse_expr for a string
# (sympy/core/sympify.py), with its default convert_xor=True.
_TRANSFORMATIONS = standard_transformations + (convert_xor,)
_TRANSFORMATIONS_RATIONAL = standard_transformations + (rationalize,
                                                        convert_xor)


def _sympify(expr, rational=False, locals=None):
    """
    Returns the sympy expression of expr, with the names of _SYMPY_NAMES
    read as circuit parameters instead of as sympy objects.

    A str is parsed as sp.sympify parses it, but without its import of all
    sympy names on every call. Any other input goes through sp.sympify.

    Rule: every str parse of SLiCAP goes through this function. Then Q and
    the other names of _SYMPY_NAMES are circuit parameters in every text
    that SLiCAP reads. A fixed symbol name needs no parse: use sp.Symbol.

    Up to 6.4.8 four functions parsed a user text with sp.sympify:
    createIIR/createFIR, laplace2z, z2fourier and the parameter-table
    display. There Q meant sympy's assumptions object, and Q*R raised
    TypeError. That was REPLACED (2026-11-22) by this function. Six more
    calls parsed a fixed name, such as 'b_1' or 'V_in_d'. They now use
    sp.Symbol.

    :param expr: expression to be converted
    :type expr: str, sympy object, int, float

    :param rational: if True, floats are converted into rational numbers
    :type rational: bool

    :param locals: extra name-to-object mapping passed to sympy
    :type locals: dict, None

    :return: sympy expression
    :rtype: sympy object

    :raises sympy.SympifyError: if a str cannot be parsed, as sp.sympify
    """
    names = {name: _null for name in _SYMPY_NAMES}
    if locals is not None:
        names.update(locals)
    # A str subclass (numpy.str_) may have its own sympify conversion.
    if type(expr) is not str:
        return sp.sympify(expr, locals=names, rational=rational)
    if rational:
        transformations = _TRANSFORMATIONS_RATIONAL
    else:
        transformations = _TRANSFORMATIONS
    expr = expr.replace('\n', '')
    try:
        return parse_expr(expr, local_dict=names,
                          transformations=transformations,
                          global_dict=_sympy_namespace(),
                          evaluate=global_parameters.evaluate)
    except (TokenError, SyntaxError) as exc:
        raise sp.SympifyError('could not parse %r' % expr, exc)

def _scale_float(value):
    """Float value of a SLiCAP numeric literal with an optional scale factor
    (``'5p'`` → 5e-12, ``'2.2k'`` → 2200.0). Plain numbers pass through;
    anything else raises ValueError. Scale factors are case-sensitive, as in
    SLiCAP netlists ('m' = milli, 'M' = mega)."""
    if isinstance(value, str):
        txt = value.strip()
        if len(txt) > 1 and txt[-1] in _SCALEFACTORS:
            return float(txt[:-1] + 'e' + _SCALEFACTORS[txt[-1]])
        return float(txt)
    return float(value)

def _eng_notation(value, digits=4):
    """Float -> SLiCAP numeric literal with a scale factor (the inverse of
    ``_scale_float``): ``0.00123`` -> ``'1.23m'``, ``2.0e-3`` -> ``'2m'``.
    *digits* is the number of significant digits.  Exponents outside the
    scale-factor table (or 0) give plain notation."""
    v = float(value)
    if v == 0.0:
        return "0"
    exp3 = 0
    a = abs(v)
    while a >= 1000.0 and exp3 < 15:
        a /= 1000.0
        exp3 += 3
    while a < 1.0 and exp3 > -24:
        a *= 1000.0
        exp3 -= 3
    suffix = {int(e): s for s, e in _SCALEFACTORS.items()}.get(exp3)
    if suffix is None and exp3 != 0:
        return f"{v:.{digits}g}"
    mantissa = f"{a if v > 0 else -a:.{digits}g}"
    return mantissa + (suffix or "")


def t_PARDEF(t):
    r"""[a-zA-Z]\w*\s*\=\s*({[\w\(\)\/*+-\^ .]*}
    |([+-]?\d+\.?\d*[eE][+-]?\d+)
    |([+-]?\d+\.?\d*[yzafpnumkMGTP])
    |([+-]?\d+\.\d*)
    |([+-]?\d+))"""
    # remove whitespace characters
    t.value = "".join(t.value.split())
    # split name and value/expression
    t.value = t.value.split('=')
    # replace scale factors in t.value[1]
    if t.value[1][0] == '{' and t.value[1][-1] == '}':
        # Do this for an expression
        try:
            sym_in = _sympify(t.value[1][1:-1]).atoms(sp.Symbol)
        except:
            sym_in = []
        pos = 1
        out = ''
        for m in re.finditer(r'\d+\.?\d*[yzafpnumkMGTP]', t.value[1]):
            out += t.value[1][pos: m.end()-1] + 'e' + _SCALEFACTORS[m.group(0)[-1]]
            pos = m.end()
        out += t.value[1][pos:-1]
        sym_out = _sympify(out).atoms(sp.Symbol)
        for item in sym_in:
            if item not in sym_out:
                _printError("Error in parameter name %s"%(str(item)), t)
        t.value[1] = out
    else:
        # Do this for a numeric value: last character is scale factor
        try:
            scaleFactor = _SCALEFACTORS[t.value[1][-1]]
            t.value[1] = t.value[1][0:-1] + 'e' + scaleFactor
        except KeyError:
            pass
    try:
        value = _sympify(t.value[1], rational=True)
        t.value[1] = value
    except TypeError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError("Error in expression.", t)
        lexer.errCount += 1
    except sp.SympifyError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError("Error in expression.", t)
        lexer.errCount += 1
    return t

def t_CMD(t):
    r'\.[a-zA-Z]+'
    """
    Returns a caplitalized command.
    """
    t.value = t.value[1:].upper()
    return t

def t_COMMENT(t):
    r'\*.*|(\;.*)'
    """
    Comment is ignored.
    """

def t_LEFTBR(t):
    r'\('
    """
    Start of model parameters will be ignored. The SLiCAP parser finds
    parameter definitions with the PARDEF token.
    """
    pass

def t_t_RIGHTBR(t):
    r'\)'
    """
    End of model parameters will be ignored.
    """
    pass

def t_PARAMS(t):
    r'params:/i'
    """
    Start of sub circuit parameters will be ignored
    """
    pass

def t_RETURN(t):
    r'\r'
    """
    Skip return character.
    """
    pass

def t_EXPR(t):
    r'{[\w\(\)\/*+-\^ .]*}'
    """
    Replaces scale factors in expressions and converts the expression into
    a sympy object.
    """
    pos = 1
    out = ''
    for m in re.finditer(r'\d+\.?\d*([yzafpnumkMGTP])', t.value):
        out += t.value[pos: m.end()-1] + 'e' + _SCALEFACTORS[m.group(0)[-1]]
        pos = m.end()
    out += t.value[pos:-1]
    t.value = out
    try:
        t.value = _sympify(out, rational=True)
    except TypeError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError("Error in expression.", t)
        lexer.errCount += 1
    except sp.SympifyError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError("Error in expression.", t)
        lexer.errCount += 1
    return t

def t_SCI(t):
    r'[+-]?\d+\.?\d*[eE][+-]?\d+'
    """
    Converts a string representing a number in scientific notation into a
    float.
    """
    try:
        t.value = sp.Rational(t.value)
        t.type = 'FLT'
    except TypeError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError('Cannot convert number to float.', t)
    return t

# Define a rule so we can track line numbers
def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'


# Define a rule for numbers with scale factors (postfixes)
def t_SCALE(t):
    r'[+-]?\d+\.?\d*[yzafpnumkMGTP]'
    """
    Replaces scale factors in numbers and converts numbers into floats
    """
    try:
        t.value = sp.Rational(t.value[0:-1] + 'e' + _SCALEFACTORS[t.value[-1]])
    except TypeError:
        exc_type, value, exc_traceback = sys.exc_info()
        print('\n', value)
        _printError('Cannot convert number to float.', t)
        lexer.errCount += 1
    t.type = 'FLT'
    return t

def t_FLT(t):
    r'[+-]?\d+\.\d*'
    return t

def t_INT(t):
    r'[+-]?\d+'
    return t

def t_FNAME(t):
    # the extension may hold underscores and digits: the type-tagged
    # subcircuit libraries are .slicap_lib / .spice_lib, and
    # ".lib lib/ACcoupler.slicap_lib" died on the underscore with
    # "illegal character" (Anton, 2026-08-04)
    r'"?/?[^\s]+\.[a-zA-Z][a-zA-Z0-9_]*"?'
    if t.value[0] == '"' and t.value[-1] == '"':
        t.value = t.value[1: -1]
    return t

def t_ID(t):
    r'[a-zA-Z](\w*)'
    t.value = t.value.strip()
    return t

def t_QSTRING(t):
    r'"(.*)"'
    return t

def t_PLUS(t):
    r'\+'
    return t

# Error handling rule
def t_error(t):
    t.lexer.errCount += 1
    _printError("Error: illegal character.", t)
    t.lexer.skip(1)

def _replaceScaleFactors(txt):
    """
    Replaces scale factors in expressions with their value in scientific
    notation.

    A SLiCAP scale factor is exactly ONE case-sensitive character from
    ``_SCALEFACTORS`` (Anton, 2026-07-31). SPICE spellings - 'MEG', 'mil',
    'K', or a trailing unit as in '1kohm' - are NOT read here: they are
    refused before a value reaches NGspice, because '1M', '1K' and '1F' mean
    different numbers in the two notations and a tolerant reader would have
    to guess.

    :param txt: Expression or number with scale factors
    :type txt: str

    :return: out: Text in which scale factors are replaced with their
             corresponding scientific notation.
    :rtype: str

    :Example:

    >>> _replaceScaleFactors('sin(2*pi*1M)')
    'sin(2*pi*1e6)'
    """
    pos = 0
    out = ''
    for m in re.finditer(r'\d+\.?\d*([yzafpnumkMGTP])', txt):
        out += txt[pos: m.end()-1] + 'e' + _SCALEFACTORS[m.group(0)[-1]]
        pos = m.end()
    out += txt[pos:]
    return out

def _tokenize(netlist):
    """
    Reset the lexer, and create the tokens from the file: 'cirFileName'.

    :param cirFileName: Name of the netlist file to be tokenized.
    :type cirFileName: str

    :return: list with title line, command liness, or element definition lines.

             Each line consists of a list of tokens

    :rtype: list
    """
    # Initialize the lexer
    lexer.errCount = 0
    lexer.lineno = 0
    lexer.input(netlist)
    lines = []
    lastLine = []
    tok = lexer.token()
    while  tok:
        if tok.type != 'NEWLINE' and tok.type != 'PLUS':
            lastLine.append(tok)
        elif tok.type == 'NEWLINE':
            if len(lastLine) != 0:
                lines.append(lastLine)
                lastLine = []
        elif tok.type == 'PLUS':
            lastLine = lines[-1]
            del lines[-1]
        tok = lexer.token()
    return lines, lexer.errCount

def _printError(msg, tok):
    """
    Prints the line with the error and an error message, and shows the position
    of the error.

    :param msg: Error message.
    :type msg: str

    :param line: Input line with the error.
    :param line: str

    :param pos: Position of therror in the input line.
    :type pos: int

    :return: out: Input line with error message.
    :rtype: str
    """
    pos = _find_column(tok)
    txt = _get_input_line(tok)
    out = '\n' + txt + '\n'
    for i in range(pos-1):
        out += '.'
    out += '|\n' + msg
    print(out)

def _find_column(token):
    """
    Computes and returns the column number of 'token'.

    :param token: Token of which the column number has to be calculated.
    :type token: ply.lex.token

    :return: Column position of this token.
    :rtype: int
    """
    line_start = lexer.lexdata.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

def _get_input_line(token):
    """
    Returns the input text line of the token.

    :param token: Token of which the column number has to be calculated.
    :type token: ply.lex.token

    :return: Text of the input line.
    :rtype: str
    """
    return lexer.lexdata.splitlines()[token.lineno]

lexer = lex.lex()

if __name__ == '__main__':
    fi = 'cir/myFirstRCnetwork.cir'   # any netlist of the current project
    print(fi)
    f = open(fi, 'r')
    netlist = f.read()
    f.close()
    lines, errors = _tokenize(netlist)
    for line in lines:
        print(line)
    print('\nnumber of errors =', errors, '\n')
