#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 10 17:24:17 2023

@author: anton
"""
from SLiCAP.SLiCAPdesignData import *

# Public functions for generating snippets that can be stored as LaTeX files
# to be included by other LaTeX files.

def netlist2TEX(netlistFile, lineRange=None, firstNumber=None):
    """
    Converts a SLiCAP netlist into a LaTeX string that can be included in
    a LaTeX document and returns this string.

    :param netlistFile: Name of the netlist file that resides in the
                        ini.circuitPath directory
    :type netListFile: str

    :param lineRange: Range of lines to be displayed; e.g. '1-7,10,12'. Defaults
                      to None (display all lines)
    :type lineRange: str

    :param firstNumber: Number of the first line to be displayed
    :type firstNumber: int, float, str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    TEX = '\\textbf{Netlist: ' + netlistFile + '}\n\n'
    TEX += '\\lstinputlisting[language=ltspice, numbers=left'
    if lineRange != None:
        TEX += ', linerange={' + lineRange + '}'
    if firstNumber != None:
        TEX += ', firstnumber=' + str(int(firstNumber))
    TEX += ']{' + ini.circuitPath + netlistFile + '}\n\n'
    return TEX

def elementData2TEX(circuitObject, label='', append2caption=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.
    The table comprises the data of all elements of the expanded nelist of
    <circuitObject>.

    The caption reads 'Expanded netlist of: <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    headerList = ["ID", "Nodes", "Refs", "Model", "Param", "Symbolic", "Numeric"]
    alignstring= '[c]{lllllll}'
    linesList   = []
    for key in circuitObject.elements.keys():
        el = circuitObject.elements[key]
        line = [key]
        lineItem = ''
        nodes = ''
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
    caption = 'Expanded netlist of: ' + circuitObject.title + '. '
    if append2caption != '':
        caption += append2caption
    TEX = TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    return TEX

def parDefs2TEX(circuitObject, label='', append2caption=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.
    The table comprises the parameter definitions of <circuitObject>.

    The caption reads 'Parameter defnitions in: : <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type param: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    if len(circuitObject.parDefs) > 0:
        caption = 'Parameter defnitions in: ' + circuitObject.title + '.'
        if append2caption != '':
            caption += '\\newline\n' + append2caption
        headerList  = ["Name", "Symbolic", "Numeric"]
        linesList   = []
        alignstring = '[c]{llr}'
        TEX = ''
        for parName in circuitObject.parDefs.keys():
            line = [parName,
                circuitObject.parDefs[parName],
                fullSubs(circuitObject.parDefs[parName], circuitObject.parDefs)]
            linesList.append(line)
        TEX += TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    else:
        TEX = "{\\textbf{No parameter definitions in: " +  circuitObject.title + '}}\n\n'
    return TEX

def params2TEX(circuitObject, label='', append2caption = ''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.
    The table comprises a column with names of undefined parameters of <circuitObject>.

    The caption reads 'Undefined parameters in: : <circuitObject.title>. <append2caption>.

    A label can be given as reference.

    :param circuitObject: SLiCAP circuit object.
    :type circuitObject: SLiCAP.SLiCAPprotos.circuit

    :param label: Reference to this table, defaults to ''
    :type param: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    if len(circuitObject.params) > 0:
        caption = 'Undefined parameters in: ' + circuitObject.title + '.'
        if append2caption != '':
            caption += '\\newline\n' + append2caption
        TEX         = '{\\textbf{Undefined parameters in: ' + circuitObject.title + '}}\n\n'
        headerList  = ["Name"]
        alignstring = '[c]{l}'
        linesList   = []
        for parName in circuitObject.params:
            lineList.append([parName])
        TEX += TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    else:
        TEX = '{\\textbf{No undefined parameters in: ' +  circuitObject.title + '}}\n\n'
    return TEX

def pz2TEX(resultObject, label='', append2caption=''):
    """
    Creates and return a LaTeX table with poles, zeros, or poles and zeros that
    can be included in a LaTeX document. If the data type is 'pz' the zero-
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

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str

    """
    if resultObject.errors != 0:
        print("pz2TEX: Errors found in instruction.")
        TEX = ''
    elif resultObject.dataType != 'poles' and resultObject.dataType != 'zeros' and resultObject.dataType != 'pz':
        print("pz2TEX: Error: 'pz2RST()' expected dataType: 'poles', 'zeros', or 'pz', got: '{0}'.".format(instObj.dataType))
        TEX = ''
    elif resultObject.step == True :
        print("pz2TEX: Error: parameter stepping not implemented for 'pz2RST()'.")
        TEX = ''
    else:
        TEX = ''
        if resultObject.simType == 'numeric':
            alignstring = '[c]{lrrrrr}'
            if ini.Hz == True:
                headerList = ['\\#', 'Re [Hz]', 'Im [Hz]', 'f [Hz]', 'Q']
            else:
                headerList = ['\\#', 'Re [rad/s]', 'Im [rad/s]', '$\\omega$ [rad/s]', 'Q']
        else:
            alignstring = '[c]{ll}'
            if ini.Hz == True:
                headerList = ['\\#', 'f [Hz]']
            else:
                headerList = ['\\#', '$\\omega$ [rad/s]']
        linesList = []
        if len(resultObject.poles) != 0:
            name = 'Poles of: ' + resultObject.gainType
            if resultObject.simType == 'numeric':
                linesList += numRoots2TEX(resultObject.poles, ini.Hz, 'p')
            else:
                linesList = symRoots2TEX(resultObject.poles, ini.Hz, 'p')
        if len(resultObject.zeros) != 0:
            if resultObject.dataType == 'pz':
                linesList += [' ']
            if resultObject.simType == 'numeric':
                linesList += numRoots2TEX(resultObject.zeros, ini.Hz, 'z')
            else:
                linesList = symRoots2TEX(resultObject.zeros, ini.Hz, 'z')
        if resultObject.dataType == 'poles':
            caption = 'Poles of: ' + resultObject.gainType + '.'
        elif resultObject.dataType == 'zeros':
            caption = 'Zeros of: ' + resultObject.gainType + '.'
        elif resultObject.dataType == 'pz':
            caption = 'Poles and zeros of: ' + resultObject.gainType + '; DC value = $' + sp.latex(roundN(resultObject.DCvalue)) + '$.\n'
        if append2caption != '':
            caption += ' ' + append2caption
        TEX += TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    return TEX

def noiseContribs2TEX(resultObject, label='', append2caption=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.

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

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    TEX = ''
    if resultObject.dataType == 'noise' and resultObject.step == False:
        detunits = sp.sympify(resultObject.detUnits + '**2/Hz')
        if resultObject.srcUnits != None:
            srcunits = sp.sympify(resultObject.srcUnits + '**2/Hz')
        # Add a table for source contributions
        linesList = []
        alignstring = '[c]{lrl}'
        headerList = ['Name', 'Value' , 'Units']
        linesList = []
        for src in resultObject.onoiseTerms.keys():
            if src[0].upper() == 'I':
                units = 'A**2/Hz'
            elif src[0].upper() == 'V':
                units = 'V**2/Hz'
            units = sp.sympify(units)
            line = [src + ': Value' , resultObject.snoiseTerms[src], units]
            linesList.append(line)
            if resultObject.srcUnits != None:
                line = [src + ': Source-referred', resultObject.inoiseTerms[src], srcunits]
                linesList.append(line)
            line = [src + ': Detector-referred', resultObject.onoiseTerms[src], detunits]
            linesList.append(line)
        TEX += TEXcreateCSVtable(headerList, linesList, alignstring, unitpos=2, caption='Noise contributions. ' + append2caption + '.', label=label)
    else:
        print('noiseContribs2TEX: Error: wrong data type, or stepped analysis.')
    return TEX

def dcvarContribs2TEX(resultObject, append2caption='', label=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.

    The table comprises the values of the dcvar sources and their contributions
    to the detector-referred dc variance and the source-referred dc variance.
    The latter only if a signal source has been specified.

    The caption reads 'DC variance contributions '<append2caption>.

    A label can be given as reference.

    :param resultObject: SLiCAP execution result object.
    :type resultObject: SLiCAP.SLiCAPprotos.allResults

    :param label: Reference to this table, defaults to ''
    :type label: str

    :param append2caption: Test string that will be appended to the caption,
                           Defaults to ''
    :type append2caption: str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    TEX = ''
    if resultObject.dataType == 'dcvar' and resultObject.step == False:
        detunits = sp.sympify(resultObject.detUnits + '**2')
        if resultObject.srcUnits != None:
            srcunits = sp.sympify(resultObject.srcUnits + '**2')
        # Add a table for source contributions
        linesList = []
        alignstring = '[c]{lrl}'
        headerList = ['Name', 'Value' , 'Units']
        linesList = []
        for src in resultObject.ovarTerms.keys():
            if src[0].upper() == 'I':
                units = 'A**2'
            elif src[0].upper() == 'V':
                units = 'V**2'
            units = sp.sympify(units)
            line = [src + ': Value' , resultObject.svarTerms[src], units]
            linesList.append(line)
            if resultObject.srcUnits != None:
                line = [src + ': Source-referred', resultObject.ivarTerms[src], srcunits]
                linesList.append(line)
            line = [src + ': Detector-referred', resultObject.ovarTerms[src], detunits]
            linesList.append(line)
        TEX += TEXcreateCSVtable(headerList, linesList, alignstring, unitpos=2, caption='DC variance contributions ' + append2caption + '.', label=label)
    else:
        print('dcvarContribs2TEX: Error: wrong data type, or stepped analysis.')
    return TEX

def specs2TEX(specs, specType, label='', caption=''):
    """
    Creates and returns a LaTeX table with specifications that can be included
    in a LaTeX document.

    If a list with specification types is provided, it creates tables
    for specified types only. By default, tables for all types will be created.

    :param specs: List with spec items.
    :type specs:  list

    :param specType: Type of specification.
    :type specType: str

    :param label: Reference to this table, defaults to ''.
    :type label: str

    :param caption: Caption of the table, defaults to ''.
    :type caption: str

    :return: LaTeX snippet to be included in a LaTeX document.
    :rtype: str
    """
    linesList   = []
    alignstring = '[c]{llrl}'
    headerList  = ["name", "description", "value", "units"]
    for specItem in specs:
        if specItem.specType.lower()==specType.lower():
            linesList.append(specItem.specLine())
    if len(linesList) > 0:
        TEX = TEXcreateCSVtable(headerList, linesList, alignstring, unitpos=3, caption=caption, label=label) + '\n'
    else:
        TEX =  "\\textbf{Found no specifications of type: " + specType + ".}\n\n"
    return TEX

def eqn2TEX(LHS, RHS, units='', label='', multiline=0):
    """
    Returns a LaTeX snippet of a displayed equation with dimension and reference
    label.

    :param RHS: Right hand side of the equation.
    :type RHS: str, sympy.Expression, or sympy.Symbol

    :param LHS: Left hand side of the equation.
    :type LHS: str, sympy.Expression, or sympy.Symbol

    :param units: Dimension
    :type units: str

    :param label: Reference label
    :type label: str

    :param multiline: Number of sub-expressions per line, defaults to 0 (single-line equation)
    :type label: int

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    try:
        units = sp.latex(sp.sympify(units))
    except:
        units = ''
    if type(LHS) == str:
        LHS = sp.sympify(LHS)
    if type(RHS) == str:
        RHS = sp.sympify(RHS)
    if multiline:
        TEX = '\n' + sp.multiline_latex(roundN(LHS), roundN(RHS), terms_per_line=multiline)
        TEX = TEX.replace('\\\\\n', '\\nonumber \\\\\n')
        TEX = TEX.replace('{align*}', '{align}')
        if units != '':
            units = '\\,\\left[\\mathrm{' + units + '}\\right]'
            TEX = TEX.replace('\\end{align}', '%s\n\\end{align}'%(units))
        if label != '':
            TEX = TEX.replace('\\end{align}', '\\label{%s}\n\\end{align}'%(label))
        TEX += '\n'
    else:
        TEX = '\\begin{equation}'
        TEX += '\n' + sp.latex(roundN(LHS)) + ' = ' + sp.latex(roundN(RHS))
        if units != '':
            TEX += '\\,\\left[\\mathrm{' + units + '}\\right]'
        TEX += '\n'
        if label != '':
            TEX += '\\label{'+ label + '}\n'
        TEX += '\\end{equation}\n\n'
    return TEX

def matrices2TEX(Iv, M, Dv, label=''):
    """
    Returns a LaTeX snippet of the matrix equation Iv = M.Dv,

    A label can be given for reference.

    :param Iv: (n x 1) matrix with independent variables.
    :type Iv: sympy.Matrix

    :param M: (n x n) matrix.
    :type M: sympy.Matrix

    :param Dv: (n x 1) matrix with dependent variables.
    :type Dv: sympy.Matrix

    :return: LaTeX snippet of the matrix equation.
    :rtype: str
    """
    TEX =  '\\begin{equation}\n'
    TEX += sp.latex(roundN(Iv)) + '=' + sp.latex(roundN(M)) + '\\cdot ' + sp.latex(roundN(Dv)) + '\n'
    if label != '':
        TEX += '\\label{'+ label + '}\n'
    TEX += '\\end{equation}\n\n'
    return TEX

def stepArray2TEX(stepVars, stepArray, label='', caption=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.

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

    :return: TEX: LaTeX table snippet.
    :rtype: str
    """
    numVars = len(stepVars)
    numRuns = len(stepArray[0])
    headerList = stepVars
    alignString = '[c]{'
    for i in range(len(stepVars)):
        alignString += 'l'
    alignString += '}'
    linesList = []
    for i in range(numRuns):
        line = ['Run ' + str(i+1) + ':']
        for j in range(numVars):
            line.append(stepArray[j][i])
        linesList.append(line)
    TEX = TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    return TEX

def coeffsTransfer2TEX(transferCoeffs, label = '', append2caption=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX
    document.

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

    :return: RST snippet to be included in a ReStructuredText document.
    :rtype: str
    """
    (gain, numerCoeffs, denomCoeffs) = transferCoeffs
    caption = ' Gain factor: ' + sp.latex(roundN(gain)) + '. '
    alignstring = '[c]{ll}'
    headerList = ['Coeff', 'Value']
    linesList = []
    for i in range(len(numerCoeffs)):
        linesList.append([sp.sympify('n_' + str(i)), numerCoeffs[i]])
    for i in range(len(denomCoeffs)):
        linesList.append([sp.sympify('d_' + str(i)), denomCoeffs[i]])
    caption += '$n_i$ = numerator coefficient of i-th order, $d_i$ = denominator coefficient of i-th order. '
    caption += append2caption
    TEX = TEXcreateCSVtable(headerList, linesList, alignstring, label=label, caption=caption)
    return TEX

def slicap2TEX(scriptFile, firstLine=None, lineRange=None):
    """
    Converts a SLiCAP script file into a LaTeX string that can be included in
    a LaTeX document and returns this string.

    :param scriptFile: Name of the script file that resides in the
                        ini.projectPath directory
    :type scriptFile: str

    :param lineRange: Range of lines to be displayed; e.g. '1-7,10,12'. Defaults
                      to None (display all lines)
    :type lineRange: str

    :param firstNumber: Number of the first line to be displayed
    :type firstNumber: int, float, str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    TEX = '\\textbf{SLiCAP script: ' + scriptFile + '}\n\n'
    TEX += '\\lstinputlisting[style=slicap, numbers=left'
    if lineRange != None:
        TEX += ', linerange={' + lineRange + '}'
    if firstNumber != None:
        TEX += ', firstnumber=' + str(int(firstNumber))
    TEX += ']{' + ini.projectPath + scriptFile + '}\n\n'
    return TEX

# Public functions for generating snippets to be put in a dictionary for inline
# substitutions in a TEX file.

def expr2TEX(expr, units=''):
    """
    Returns a LaTeX snippet for inline subsitution of an expression in a LaTeX document.

    :param expr: sympy expression for inline substitution.
    :type expr: sympy.Expression

    :param units: units or dimension, defaults to ''
    :type units: str

    :return: LaTeX snippet for inline substitution
    :rtype: str
    """
    try:
        units = sp.latex(sp.sympify(units))
    except:
       units = ''
    TEX = '$' + sp.latex(roundN(expr))
    if units == '':
        TEX += '$ '
    else:
        TEX += '\\left[ \\mathrm{' + units + '} \\right] $ '
    return TEX

def eqn2TEXinline(LHS, RHS, units=''):
    """
    Returns a LaTeX snippet for inline subsitution of an equation in a LaTeX document.

    :param LHS: Left hand side of the equation.
    :type LHS: sympy.Expression, str

    :param RHS: Right hand side of the equation.
    :type RHS: sympy.Expression, str

    :param units: units or dimension, defaults to ''
    :type units: str

    :return: LaTeX snippet for inline substitution
    :rtype: str
    """
    try:
        units = sp.latex(sp.sympify(units))
    except:
        units = ''
    if type(LHS) == str:
        LHS = sp.sympify(LHS)
    if type(RHS) == str:
        RHS = sp.sympify(RHS)
    TEX = '$' + sp.latex(roundN(LHS)) + '=' + sp.latex(roundN(RHS))
    if units == '':
        TEX += '$ '
    else:
        TEX += '\\left[ \\mathrm{' + units + '} \\right]$ '
    return TEX

def save2TEXinline(vardict):
    """
    Saves the key-value pairs of 'vardict' in the CSV file:

    <ini.latexPath>SLiCAPdata/TEXsubstitutions.tex

    :param vardict: Dictionary with inline LaTeX subsitutions
    :type vardict: dict

    :return: None
    :rtype: NoneType
    """
    TEX = ''
    for key in vardict.keys():
        TEX += key + ', ' + vardict[key] + '\n'
    saveTEX(TEX, 'TEXsubstitutions')

def saveTEX(TEX, fileName):
    """
    Saves a LaTeX snippet for inclusion in a LaTeX file into:

    <ini.latexPath>SLiCAdata/<fileName>.tex
    :param TEX: LaTeX snippet.
    :type TEX: str

    :param fileName: File name
    :type fileName: str

    :return: None
    :rtype: NoneType
    """
    f = open(ini.latexPath + 'SLiCAPdata/' + fileName + '.tex', 'w')
    f.write(TEX)
    f.close()

# Non-public functions for creating table snippets

def TEXcreateCSVtable(headerList, linesList, alignstring, unitpos=None, caption='', label=''):
    """
    Creates and returns a LaTeX table snippet that can be included in a LaTeX document.

    A label can be given as reference and a caption can be added.

    :param headerList: List with column headers.
    :type headerList: list with strings

    :param linesList: List with lists of table data for each table row
    :type linesList: list

    :param alignstring: LaTeX table align string
    :type alignstring: str

    :param unitpos: Position of column with units (will be typesetted with mathrm)
    :type unitpos: int, str

    :param caption: Table caption, defauls to ''
    :type caption: str

    :param label: Table reference label
    :type label: str

    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    TEX =  '\\begin{table}[h]\n\centering\n'
    TEX += '\\begin{tabular}' + alignstring + '\n'
    for field in headerList:
        if type(field) == str:
            TEX += '\\textbf{' + field + '} & '
        else:
            TEX += '$\\symbf{' + sp.latex(roundN(field)) + '}$ & '
    TEX = TEX[:-2] + '\\\\ \n'
    j = 0
    for line in linesList:
        i = 0
        if not j%2:
            TEX += '\\rowcolor{myyellow}\n'
        for field in line:
            if type(field) == str:
                if field != '':
                    TEX +=  '\\small{' + field.replace('_', '\\_') + '} &'
                else:
                    TEX += ' &'
            elif unitpos != None and i == int(unitpos):
                TEX += '$\\mathrm{' + sp.latex(field) + '}$ &'
            else:
                TEX += '$' + sp.latex(roundN(sp.N(field))) + '$ &'
            i += 1
        TEX = TEX[:-2] + ' \\\\ \n'
        j += 1
    TEX += '\\end{tabular}\n'
    if caption != '':
        TEX += '\\caption{' + caption + '}\n'
    if label != '':
        TEX += '\\label{' + label + '}\n'
    TEX += '\\end{table}\n\n'
    return TEX

def numRoots2TEX(roots, Hz, pz):
    """
    Returns a list of lists with row data for the creation of a LaTeX table
    with numeric poles or zeros.

    :param roots: List with numeric roots
    :type roots: List with (complex) numbers

    :param Hz: True if frequencies must be displayed in Hz, False for rad/s.
    :type Hz: Bool

    :param pz: Identifier prefix: 'p' ofr poles 'z' for zeros.
    :type pz: str

    :return: List of lists with data of poles or zeros
    :rtype: list
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

def symRoots2TEX(roots, Hz, pz):
    """
    Returns a list of lists with row data for the creation of a LaTeX table
    with symbolic poles or zeros.

    :param roots: List with symbolic roots
    :type roots: List with sympy expressions

    :param Hz: True if frequencies must be displayed in Hz, False for rad/s.
    :type Hz: Bool

    :param pz: Identifier prefix: 'p' ofr poles 'z' for zeros.
    :type pz: str

    :return: List of lists with data of poles or zeros
    :rtype: list
    """
    lineList = []
    i = 0
    for root in roots:
        i += 1
        if Hz == True:
            line = [sp.Symbol('$' + pz + '_' + str(i)) + '$', '$' + root/2/sp.pi + '$']
        else:
            line = [sp.Symbol('$' + pz + '_' + str(i)) + '$', '$' + root + '$']
        lineList.append(line)
    return lineList