#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP _tokenizer for netlist files.

"""
import ply.lex as lex
import sys
import sympy as sp
import re

# list of token names

tokens = ('PARDEF', 'EXPR', 'SCALE', 'SCI', 'FLT', 'INT', 'CMD', 'FNAME',
          'PARAMS', 'ID', 'QSTRING', 'PLUS', 'LEFTBR', 'RIGHTBR', 'COMMENT',
          'NEWLINE')

_SCALEFACTORS    =  {'y':'-24','z':'-21','a':'-18','f':'-15','p':'-12','n':'-9',
                    'u':'-6','m':'-3','k':'3','M':'6','G':'9','T':'12','P':'15'} #,
                    #'E':'18','Z':'21','Y':'24'}

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


# NGspice reads scale factors CASE-INSENSITIVELY: 'm' and 'M' are both
# milli, and mega is 'Meg'. SLiCAP suffixes whose meaning differs must be
# translated; suffixes NGspice does not know are expanded numerically.
_NGSPICE_SUFFIX = {'M': 'Meg'}     # SLiCAP mega → NGspice mega
_NGSPICE_EXPAND = set('yzaP')      # unknown to NGspice ('P' would read as pico)

_NUMSUFFIX = re.compile(r'^([+-]?(?:\d+\.?\d*|\.\d+))([yzafpnumkMGTP])$')

def _to_ngspice(value):
    """SLiCAP numeric literal → NGspice-safe text.

    ``'1M'`` → ``'1Meg'`` (NGspice would read '1M' as 1 milli!), ``'1P'`` →
    ``'1e15'``; suffixes with identical meaning ('5p', '2.2k', '1m', '1G')
    pass through. Plain numbers, expressions, and any other text are
    returned unchanged."""
    if not isinstance(value, str):
        return value
    m = _NUMSUFFIX.match(value.strip())
    if m is None:
        return value
    num, suffix = m.groups()
    if suffix in _NGSPICE_SUFFIX:
        return num + _NGSPICE_SUFFIX[suffix]
    if suffix in _NGSPICE_EXPAND:
        return num + 'e' + _SCALEFACTORS[suffix]
    return num + suffix

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
            sym_in = sp.sympify(t.value[1][1:-1]).atoms(sp.Symbol)
        except:
            sym_in = []
        pos = 1
        out = ''
        for m in re.finditer(r'\d+\.?\d*[yzafpnumkMGTP]', t.value[1]):
            out += t.value[1][pos: m.end()-1] + 'e' + _SCALEFACTORS[m.group(0)[-1]]
            pos = m.end()
        out += t.value[1][pos:-1]
        sym_out = sp.sympify(out).atoms(sp.Symbol)
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
        value = sp.sympify(t.value[1], rational=True)
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
        t.value = sp.sympify(out, rational=True)
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
    r'"?/?[^\s]+\.[a-zA-Z]+"?'
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
    notation:

    :param txt: Expression or number with scale factors
    :type txt: str

    :return: out: Text in which scale factors are replaced with their
             corresponding scientific notation.
    :rtype: str

    :Example:

    >>> _replaceScaleFactors('sin(2*pi*1M)')
    'sin(2*pi*1E6)'
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
    fi = '/home/anton/DATA/SLiCAP/SLiCAP_python_tests/ASMPT-11/cir/classABamp.cir'
    print(fi)
    f = open(fi, 'r')
    netlist = f.read()
    f.close()
    lines, errors = _tokenize(netlist)
    for line in lines:
        print(line)
    print('\nnumber of errors =', errors, '\n')
