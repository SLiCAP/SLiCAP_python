#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP functions for generating snippets that can be stored as RST files
and included in other RST files.

IMPORTANT: In future versions of SLiCAP, these functions will be replaced with 
an RST formatter.
"""
import SLiCAP.SLiCAPconfigure as ini
import sympy as sp
from SLiCAP.SLiCAPmath import fullSubs, roundN, _checkNumeric

# Public functions for generating snippets that can be stored as RST files
# to be included by other RST files.

def netlist2RST(netlistFile, lineRange=None, firstNumber=None, position=0):
    """
    Converts a SLiCAP netlist into an RST string that can be included in
    a ReStructuredText document and returns this string.

    :param netlistFile: Name of the netlist file that resides in the
                        ini.cir_path directory
    :type netListFile: str

    :param lineRange: Range of lines to be displayed; e.g. '1-7,10,12'. Defaults
                      to None (display all lines)
    :type lineRange: str

    :param firstNumber: Number of the first line to be displayed
    :type firstNumber: int, float, str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    spaces = _makeSpaces(position)
    RST = spaces + '.. literalinclude:: /' + ini.project_path + ini.cir_path + netlistFile + '\n'
    RST += spaces + '    :linenos:\n'
    if lineRange != None:
        RST += spaces + '    :lines: ' + lineRange + '\n'
        if firstNumber != None:
            RST += spaces + '    :lineno-start: ' + str(firstNumber) + '\n'
    return RST

def elementData2RST(circuitObject, label='', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReStructuredText document.
    The table comprises the data of all elements of the expanded nelist of <circuitObject>.

    The caption reads 'Expanded netlist of: <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    name       = 'Expanded netlist of: ' + circuitObject.title + '. ' + append2caption
    headerList = ["ID", "Nodes", "Refs", "Model", "Param", "Symbolic", "Numeric"]
    linesList   = []
    for key in circuitObject.elements.keys():
        el = circuitObject.elements[key]
        line = [key]

        lineItem = ''
        for node in el.nodes:
            lineItem += node + ' '
        line.append(lineItem)

        lineItem = ''
        for ref in el.refs:
            lineItem += ref + ' '
        line.append(lineItem)
        line.append(el.model)
        if len(el.params.keys()) == 0:
            line += ['','','']
        else:
            keys = list(el.params.keys())
            for i in range(len(keys)):
                if i == 0:
                    line.append(keys[i])
                    line.append(el.params[keys[i]])
                    line.append(fullSubs(el.params[keys[i]], circuitObject.parDefs))
                    linesList.append(line)
                else:
                    line = ['','','','']
                    line.append(keys[i])
                    line.append(el.params[keys[i]])
                    line.append(fullSubs(el.params[keys[i]], circuitObject.parDefs))
        linesList.append(line)
    RST = _RSTcreateCSVtable(name, headerList, linesList, position=position, label=label)
    return RST

def parDefs2RST(circuitObject, label='', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReSturucturedText document.
    The table comprises the parameter definitions of <circuitObject>.

    The caption reads 'Parameter defnitions in: : <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReSturucturedText document
    :rtype: str
    """
    if len(circuitObject.parDefs) > 0:
        name       = 'Parameter defnitions in: ' + circuitObject.title + '. ' + append2caption
        headerList = ["Name", "Symbolic", "Numeric"]
        linesList   = []
        for parName in circuitObject.parDefs.keys():
            line = [parName,
                circuitObject.parDefs[parName],
                fullSubs(circuitObject.parDefs[parName], circuitObject.parDefs)]
            linesList.append(line)
        RST = _RSTcreateCSVtable(name, headerList, linesList, position=position, label=label)
    else:
        RST = "**No parameter definitions in: " +  circuitObject.title + '**\n\n'
    return RST

def dict2RST(dct, head=None, label='', caption='', position=0):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.
    The table comprises a column with the keys of <dct> and a column with dct[<key>].

    A table caption caption and a label can be given.

    :param dct: Dictionary with data to be displayed in a table.
    :type dct: dict

    :param head: List with names for the 'key' and the 'value' columns, respectively.
                 List items will be converted to string.
    :type head: list
    
    :param label: Reference to this table, defaults to ''
    :type param: str

    :param caption: Test string that will be displayed as table caption; defaults to ''.
    :type caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int
    
    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    RST = None
    if len(dct.keys()) > 0:
        if type(head) == list and len(head) == 2:
            headerList = [str(head[0]), str(head[1])]
        else: 
            headerList  = ["", ""]
        linesList   = []
        for key in dct.keys():
            line = [key, dct[key]]
            linesList.append(line)
        RST = _RSTcreateCSVtable(caption, headerList, linesList, position=position, label=label)
    return RST    
    
def params2RST(circuitObject, label='', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReStructuredText document.
    The table comprises a column with names of undefined parameters of <circuitObject>.

    The caption reads 'Undefined parameters in: : <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    if len(circuitObject.params) > 0:
        name       = 'Undefined parameters in: ' + circuitObject.title + '. ' + append2caption
        headerList = ["Name"]
        linesList   = []
        for parName in circuitObject.params:
            linesList.append([parName])
        RST = _RSTcreateCSVtable(name, headerList, linesList, position=position, label=label)
    else:
        RST = '**No undefined parameters in: ' +  circuitObject.title + '**\n\n'
    return RST

def pz2RST(resultObject, label = '', append2caption='', position=0):
    """
    Creates and return an RST table with poles, zeros, or poles and zeros that
    can be included in a ReStructuredText document. If the data type is 'pz' the zero-
    frequency value of the gain will be displayed in the caption of the table.

    The caption reads as follows:

    - data type = 'poles': 'Poles of: <resultObject.gainType>. <append2caption>'
    - data type = 'zeros': 'Zeros of: <resultObject.gainType>. <append2caption>'
    - data type = 'pz': 'Poles and zeros of: <resultObject.gainType>; DC value = <resultObject,DCvalue>. <append2caption>.'

    A label can be given as reference.

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    RST = ''
    if resultObject.errors != 0:
        print("pz2RST: Errors found in instruction.")
    elif resultObject.dataType != 'poles' and resultObject.dataType != 'zeros' and resultObject.dataType != 'pz':
        print("pz2RST: Error: 'pz2RST()' expected dataType: 'poles', 'zeros', or 'pz', got: '{0}'.".format(resultObject.dataType))
    elif resultObject.step == True :
        print("pz2RST: Error: parameter stepping not implemented for 'pz2RST()'.")
    else:
        if resultObject.dataType == 'poles':
            name = 'Poles of: ' + resultObject.gainType + '. ' + append2caption
            numeric = _checkNumeric(resultObject.poles)
        elif resultObject.dataType == 'zeros':
            name = 'Zeros of: ' + resultObject.gainType + '. ' + append2caption
            numeric = _checkNumeric(resultObject.zeros)
        elif resultObject.dataType == 'pz':
            name = 'Poles and zeros of: ' + resultObject.gainType + '. DC gain = :math:`' + sp.latex(roundN(resultObject.DCvalue)) + '`. ' + append2caption
            numeric = _checkNumeric(resultObject.poles) and _checkNumeric(resultObject.zeros)
        if numeric:
            if ini.hz == True:
                headerList = ['#', 'Re [Hz]', 'Im [Hz]', ':math:`f` [Hz]', 'Q']
            else:
                headerList = ['#', 'Re [rad/s]', 'Im [rad/s]', ':math:`\\omega` [rad/s]', 'Q']
        else:
            if ini.hz == True:
                headerList = ['#', ':math:`f` [Hz]']
            else:
                headerList = ['#', ':math:`\\omega` [rad/s]']
        linesList = []
        if resultObject.dataType == 'poles' or resultObject.dataType == 'pz':
            if numeric:
                linesList += _numRoots2RST(resultObject.poles, ini.hz, 'p')
            else:
                linesList += _symRoots2RST(resultObject.poles, ini.hz, 'p')

        if resultObject.dataType == 'zeros' or resultObject.dataType == 'pz':
            if numeric:
                linesList += _numRoots2RST(resultObject.zeros, ini.hz, 'z')
            else:
                linesList += _symRoots2RST(resultObject.zeros, ini.hz, 'z')

        RST += _RSTcreateCSVtable(name, headerList, linesList, position=position, label=label)
    return RST

def noiseContribs2RST(resultObject, label='', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReStructuredText document.

    The table comprises the values of the noise sources and their contributions
    to the detector-referred noise and the source-referred noise. The latter
    only if a signal source has been specified.

    The caption reads 'Noise contributions. '<append2caption>.

    A label can be given as reference.

    :param resultObject: SLiCAP execution result object.
    :type resultObject: SLiCAP.SLiCAPprotos.allResults

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    if resultObject.dataType == 'noise' and resultObject.step == False:
        detunits = sp.sympify(resultObject.detUnits + '**2/Hz')
        if resultObject.srcUnits != None:
            srcunits = sp.sympify(resultObject.srcUnits + '**2/Hz')
        # Add a table with noise contributions
        linesList = []
        headerList = ['', 'Value' , 'Units']
        name = "Source contributions. " + append2caption
        for src in resultObject.onoiseTerms.keys():
            if src[0].upper() == 'I':
                units = 'A**2/Hz'
            elif src[0].upper() == 'V':
                units = 'V**2/Hz'
            units = sp.sympify(units)
            line = [src + ': Source value', resultObject.snoiseTerms[src], units]
            linesList.append(line)
            if resultObject.srcUnits != None:
                line = [src + ': Source-referred', resultObject.inoiseTerms[src], srcunits]
                linesList.append(line)
            line = [src + ': Detector-referred', resultObject.onoiseTerms[src], detunits]
            linesList.append(line)
        RST = _RSTcreateCSVtable(name, headerList, linesList, unitpos=2, label=label)
    else:
        RST = ''
        print('noise2RST: Error: wrong data type, or stepped analysis.')
    return RST

def dcvarContribs2RST(resultObject, label='', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReStructuredText document.

    The table comprises the values of the dcvar sources and their contributions
    to the detector-referred DC variance and the source-referred DC variance. The latter
    only if a signal source has been specified.

    The caption reads 'Source contributions. '<append2caption>.

    A label can be given as reference.

    :param resultObject: SLiCAP execution result object.
    :type resultObject: SLiCAP.SLiCAPprotos.allResults

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    if resultObject.dataType == 'dcvar' and resultObject.step == False:
        detunits = sp.sympify(resultObject.detUnits + '**2')
        if resultObject.srcUnits != None:
            srcunits = sp.sympify(resultObject.srcUnits + '**2')
        # Add a table with dcvar contributions
        linesList = []
        headerList = ['', 'Value' , 'Units']
        name = "Source contributions. " + append2caption
        for src in resultObject.ovarTerms.keys():
            if src[0].upper() == 'I':
                units = 'A**2'
            elif src[0].upper() == 'V':
                units = 'V**2'
            units = sp.sympify(units)
            line = [src + ': Source value', resultObject.svarTerms[src], units]
            linesList.append(line)
            if resultObject.srcUnits != None:
                line = [src + ': Source-referred', resultObject.ivarTerms[src], srcunits]
                linesList.append(line)
            line = [src + ': Detector-referred', resultObject.ovarTerms[src], detunits]
            linesList.append(line)
        RST = _RSTcreateCSVtable(name, headerList, linesList, unitpos=2, label=label)
    else:
        RST = ''
        print('dcvar2RST: Error: wrong data type, or stepped analysis.')
    return RST

def specs2RST(specs, specType='', label='', caption='', position=0):
    """
    Creates and returns an RST table snippet from a list with specItem objects.
    This table snippet can be included in a ReStructuredText document.

    :param specs: List with spec items.
    :type specs:  list

    :param specType: Type of specification.
    :type types: str

    :param label: Reference to this table, defaults to ''.
    :type label: str

    :param caption: Caption of the table, defaults to ''.
    :type caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    linesList  = []
    headerList = ["Name", "Description", "value", "units"]
    for specItem in specs:
        if specItem.specType.lower()==specType.lower():
            linesList.append(specItem._specLine())
    if len(linesList) > 0:
        RST = _RSTcreateCSVtable(caption, headerList, linesList, label=label, position=position) + '\n'
    else:
        RST =  "**Found no specifications of type: " + specType + ".**\n\n"
    return RST

def eqn2RST(LHS, RHS, units='', label='', position=0):
    """
    Returns an RST snippet of a displayed equation with dimension and reference
    label.

    :param RHS: Right hand side of the equation.
    :type RHS: str, sympy.Expression, or sympy.Symbol

    :param LHS: Left hand side of the equation.
    :type LHS: str, sympy.Expression, or sympy.Symbol

    :param units: Dimension
    :type units: str

    :param label: Reference label
    :type label: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    spaces = _makeSpaces(position)
    RST = spaces + '.. math::\n'
    if label != '':
        RST += spaces + '    :label: ' + label + '\n'
    RST += '\n'
    try:
        units = sp.latex(sp.sympify(units))
    except:
        units = ''
    RST += spaces + '    ' + sp.latex(roundN(LHS)) + ' = ' + sp.latex(roundN(RHS))
    if units != '':
        RST += '\\,\\,\\left[\\mathrm{' + units + '}\\right]\n\n'
    return RST

def matrices2RST(Iv, M, Dv, label='', position=0):
    """
    Returns an RST snippet of the matrix equation Iv = M.Dv,

    A label can be given for reference.

    :param Iv: (n x 1) matrix with independent variables.
    :type Iv: sympy.Matrix

    :param M: (n x n) matrix.
    :type M: sympy.Matrix

    :param Dv: (n x 1) matrix with dependent variables.
    :type Dv: sympy.Matrix

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    spaces = _makeSpaces(position)
    RST = spaces + '.. math::\n'
    if label != '':
        RST += spaces + '    :label: ' + label + '\n'
    RST += '\n'
    RST += spaces + '    ' + sp.latex(roundN(Iv)) + '=' + sp.latex(roundN(M)) + '\\cdot ' + sp.latex(roundN(Dv)) + '\n\n'
    return RST

def stepArray2rst(stepVars, stepArray, label='', caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a ReStructuredText document.

    The table shows the step variables and their values as defined for array-type
    stepping of instructions.

    :param stepVars: List with step variables for array type stepping
                     (SLiCAPinstruction.instruction.stepVars)
    :type stepVars: List

    :param stepArray: List of lists: (SLiCAPinstruction.instruction.stepArray)
    :type stepArray: list

    :param label: Reference lable for this table
    :type label: str

    :param caption: Table caption
    :type caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    RST = ''
    numVars = len(stepVars)
    numRuns = len(stepArray[0])
    headerList = [sp.sympify(stepVar) for stepVar in stepVars]
    linesList = []
    for i in range(numRuns):
        line = []
        for j in range(numVars):
            line.append(stepArray[i][j])
        linesList.append(line)
    RST = _RSTcreateCSVtable(caption, headerList, linesList, position=position, label=label) + '\n\n'
    return RST

def coeffsTransfer2RST(transferCoeffs, label = '', append2caption='', position=0):
    """
    Creates and returns an RST table snippet that can be included in a
    ReStuctrutedText document.

    The table comprises the normalized coefficients of the numerator and
    the denominator as listed in transferCoeffs.

    The normalization factor (Gain) is added to the caption.

    A label can be given as reference.

    :param transferCoeffs: List with:

                           #. gain
                           #. list with numerator coefficients
                           #. list with denominator coefficients

                           Can be obtained with coeffsTransfer()

    :type transferCoeffs: list

    :param label: Reference lable for this table
    :type label: str

    :param append2caption: String that will be appended to the caption.
    :type append2caption: str

    :param position: Number of spaces indention from the left margin, defaults to 0
    :type position: int

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    (gain, numerCoeffs, denomCoeffs) = transferCoeffs
    caption = ' Gain factor: ' + sp.latex(roundN(gain)) + '. '
    headerList = ['Coeff', 'Value']
    linesList = []
    for i in range(len(numerCoeffs)):
        linesList.append([sp.sympify('n_' + str(i)), numerCoeffs[i]])
    for i in range(len(denomCoeffs)):
        linesList.append([sp.sympify('d_' + str(i)), denomCoeffs[i]])
    caption += ':math:`n_i` = numerator coefficient of i-th order, :math:`d_i` = denominator coefficient of i-th order. '
    caption += append2caption
    RST = _RSTcreateCSVtable(caption, headerList, linesList, label=label, position=position)
    return RST
    
def monomialCoeffs2RST(monomialCoeffs, label = '', caption='', position=0):
    raise NotImplementedError

def file2RST(fileName, firstNumber=None, lineRange=None, position=0):
    """
    Converts a SLiCAP script file into an RST string that can be included in
    a ReStructuredText document and returns this string.

    :param scriptFile: Name of the script file that resides in the
                       _PROJECTPATH directory
    :type scriptFile: str

    :param lineRange: Range of lines to be displayed; e.g. '1-7,10,12'. Defaults
                      to None (display all lines)
    :type lineRange: str

    :param firstNumber: Number of the first line to be displayed
    :type firstNumber: int, float, str

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    spaces = _makeSpaces(position)
    RST = spaces + '.. literalinclude:: /' + fileName + '\n'
    RST += spaces + '    :linenos:\n'
    if lineRange != None:
        RST += spaces + '    :lines: ' + lineRange + '\n'
        if firstNumber != None:
            RST += spaces + '    :lineno-start: ' + str(firstNumber) + '\n'
    return RST

# Functions for generating nippets to be put in a dictionary for inline
# substitutions in an RST file.

def expr2RST(expr, units='', name=''):
    """
    Places a substitution in "substitutions.rst" in the rst_snippets folder.

    :param name: Name of the variable to be substituted
    :type name: str
    
    :param expr: sympy expression for inline substitution.
    :type expr: sympy.Expression

    :param units: units or dimension, defaults to ''
    :type units: str

    :return: None
    :rtype: str
    """
    if type(name) == str and len(name) > 0:
        try:
            units = sp.latex(sp.sympify(units))
        except:
            pass
        RST = ':math:`' + sp.latex(roundN(expr))
        if units != '':
            RST += '\\, \\left[ \\mathrm{' + units + '} \\right]` '
        else:
            RST += '` '
        f = open(ini.rst_snippets + "substitutions.rst", "a")
        f.write('.. |' + name + '| replace:: ' + RST + '\n')
        f.close()
    else:
        raise NameError
        
def eqn2RSTinline(LHS, RHS, units='', name=None):
    """
    Places a substitution in "substitutions.rst" in the rst_snippets folder.

    :param name: Name of the variable to be substituted
    :type name: str
    
    :param LHS: Left hand side of the equation.
    :type LHS: sympy.Expression, str

    :param RHS: Right hand side of the equation.
    :type RHS: sympy.Expression, str

    :param units: units or dimension, defaults to ''
    :type units: str

    :return: None
    :rtype: str
    """
    if type(name) == str and len(name) > 0:
        try:
            units = sp.latex(sp.sympify(units))
        except:
            pass
        RST = ':math:`' + sp.latex(roundN(LHS)) + '=' + sp.latex(roundN(RHS))
        if units != '':
            RST += '\\, \\left[ \\mathrm{' + units + '} \\right]` '
        else:
            RST += '` '
        
        f = open(ini.rst_snippets + "substitutions.rst", "a")
        f.write('.. |' + name + '| replace:: ' + RST + '\n')
        f.close()
    else:
        raise NameError

# Non-public functions for creating table snippets

def _RSTcreateCSVtable(name, headerList, linesList, position=0, unitpos=None, label=''):
    """
    Creates and returns an RST table snippet that can be included in a
    ReStructuredText document.

    A label can be given as reference. The name is displayed as caption.

    :param name: Table caption
    :type name: str

    :param headerList: List with column headers.
    :type headerList: list with strings

    :param linesList: List with lists of table data for each table row
    :type linesList: list

    :param unitpos: Position of column with units (will be typesetted with mathrm)
    :type unitpos: int, str

    :param label: Table reference label
    :type label: str

    :return: RST snippet to be included in a ReStructuredText document
    :rtype: str
    """
    RST = ''
    spaces = _makeSpaces(position)
    if label != '':
        RST += spaces + '.. _' + label + ':\n'
    RST += spaces + '.. csv-table:: ' + name + '\n'
    RST += spaces + '    :header: '
    for item in headerList:
        if type(item) == str:
            RST += '"' + item + '", '
        else:
            RST += ':math:`' + sp.latex(roundN(item)) + '`, '
    RST = RST[:-2] + '\n'
    RST +=  spaces + '    :widths: auto\n'
    for line in linesList:
        i = 0
        RST += '\n' + spaces + '    '
        for item in line:
            if type(item) == str:
                RST += '"' + item + '", '
            elif i == unitpos:
                RST += ':math:`\\mathrm{' + sp.latex(item) + '}`, '
            else:
                RST += ':math:`' + sp.latex(roundN(sp.N(item))) + '`, '
            i += 1
        RST = RST[:-2]
    RST += '\n\n'
    return RST

def _numRoots2RST(roots, Hz, pz):
    """
    Returns a list of lists with row data for the creation of an RST table
    with numeric poles or zeros.

    :param roots: List with numeric roots
    :type roots: List with (complex) numbers

    :param Hz: True if frequencies must be displayed in Hz, False for rad/s.
    :type Hz: Bool

    :param pz: Identifier prefix: 'p' ofr poles 'z' for zeros.
    :type pz: str

    :return: List of lists with data of poles or zeros
    :rtype: List of lists
    """
    lineList = []
    i = 0
    for root in roots:
        i += 1
        realpart  = sp.re(root)
        imagpart  = sp.im(root)
        frequency = sp.Abs(root)
        Q = roundN(sp.N(frequency/(2*sp.Abs(realpart))))
        if Hz == True:
            realpart = roundN(sp.N(realpart/2/sp.pi))
            imagpart = roundN(sp.N(imagpart/2/sp.pi))
            frequency = roundN(sp.N(frequency/2/sp.pi))
            if Q <= 0.5:
                line = [sp.Symbol(pz + '_' + str(i)), realpart, imagpart, frequency, ]
            else:
                line = [sp.Symbol(pz + '_' + str(i)), realpart, imagpart, frequency, Q]
        lineList.append(line)
    return lineList

def _symRoots2RST(roots, Hz, pz):
    """
    Returns a list of lists with row data for the creation of an RST table
    with symbolic poles or zeros.

    :param roots: List with symbolic roots
    :type roots: List with sympy expressions

    :param Hz: True if frequencies must be displayed in Hz, False for rad/s.
    :type Hz: Bool

    :param pz: Identifier prefix: 'p' ofr poles 'z' for zeros.
    :type pz: str

    :return: List of lists with data of poles or zeros
    :rtype: List of lists
    """
    lineList = []
    i = 0
    for root in roots:
        i += 1
        if Hz == True:
            line = [sp.Symbol(pz + '_' + str(i)), root/2/sp.pi]
        else:
            line = [sp.Symbol(pz + '_' + str(i)), root]
        lineList.append(line)
    return lineList

def _makeSpaces(n):
    """
    Creates and returns a string with <n> spaces.

    :param n: Number of spaces
    :type n: int

    :return: String with <n> spaces
    :rtype: str
    """
    spaces = ''
    if n > 0:
        for i in range(n):
            spaces += ' '
    return spaces
