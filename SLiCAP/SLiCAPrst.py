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
from SLiCAP.SLiCAPmath import fullSubs, roundN, _checkNumeric, units2TeX
from SLiCAP.SLiCAPprotos import _BaseFormatter, Snippet
import os

class RSTformatter(_BaseFormatter):
    """
    Formatter. The methods return ReStructuredText snippets.
        
    :example:
    
    >>> import SLiCAP as sl
    >>> sl.initProject("formatter")
    >>> rst = sl.RSTformatter()   # Creates an instance of a ReStructuredText formatter
    """

    def __init__(self):
        super().__init__()
        self.format = "rst"
        self.snippet = None
        try:
            os.remove(ini.rst_snippets + "substitutions.rst")
        except FileNotFoundError :
            pass

    def netlist(self, netlistFile, lineRange=None, firstNumber=None, 
                position=0):
        """
        Creates a LaTeX `\\input{}` or an RST '.. literalinclude:: '
        command for including a netlist file.
        
        :param netlistFile: Name of the netlist file relative to the project 
                            circuit directory
        :type netlistFile: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
        
        >>> import SLiCAP as sl
        >>> rst = sl.RSTformatter() # Creates a ReStructuredText formatter
        >>> rst.netlist("myFirstRCnetwork.cir").save("netlist")
        
        This will save a file `netlist.rst` in the `sl.ini.rst_snippets` folder 
        with the following contents:
        
        .. code::
        
            .. literalinclude:: <full path to myFirstRCnetwork.cir>
                :linenos:
        """
        spaces = _makeSpaces(position)
        RST = spaces + '.. literalinclude:: /' + ini.project_path 
        RST += ini.cir_path + netlistFile + '\n'
        RST += spaces + '    :linenos:\n'
        if lineRange != None:
            RST += spaces + '    :lines: ' + lineRange + '\n'
            if firstNumber != None:
                RST += spaces + '    :lineno-start: ' + str(firstNumber) + '\n'
        return Snippet(RST, self.format)
                
    def elementData(self, circuitObject, label="", caption="", position=0):
        """
        Creates a table with data of expanded netlist elements of *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        headerList = ["ID", "Nodes", "Refs", "Model", "Param", "Symbolic", 
                      "Numeric"]
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
                        line.append(fullSubs(el.params[keys[i]], 
                                             circuitObject.parDefs))
                        linesList.append(line)
                    else:
                        line = ['','','','']
                        line.append(keys[i])
                        line.append(el.params[keys[i]])
                        line.append(fullSubs(el.params[keys[i]], 
                                             circuitObject.parDefs))
                        linesList.append(line)
        RST = _RSTcreateCSVtable(caption, headerList, linesList, 
                                 position=position, label=label)
        return Snippet(RST, self.format)

    def parDefs(self, circuitObject, label="", caption="", position=0):
        """
        Creates a table with parameter definitions of *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if len(circuitObject.parDefs) > 0:
            headerList = ["Name", "Symbolic", "Numeric"]
            linesList   = []
            for parName in circuitObject.parDefs.keys():
                line = [parName,
                    circuitObject.parDefs[parName],
                    fullSubs(circuitObject.parDefs[parName], 
                             circuitObject.parDefs)]
                linesList.append(line)
            RST = _RSTcreateCSVtable(caption, headerList, linesList,
                                     position=position, label=label)
        else:
            RST = "**No parameter definitions in: " 
            RST +=  circuitObject.title + '**\n\n'
        return Snippet(RST, self.format)

    def dictTable(self, dct, head=None, label="", caption="", position=0):
        """
        Creates a table from a dictionary; optionally with a header.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param dct: Dictionary with key-value pairs.
        :type circuitObject: dict
        
        :param head: List with names for the key column and the value column, respectively.
                     List items will be converted to string.
        :type head: list
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> 
        >>> sl.initProject("Documentation")
        >>> rst = sl.RSTformatter()
        >>> header = ["name", "age"]
        >>> data   = {"John": 89, Mary: 104}
        >>> rst.dictTable(data, head=header, caption="Some of my friends").save("friends")
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
            RST = _RSTcreateCSVtable(caption, headerList, linesList, 
                                     position=position, label=label)
        return Snippet(RST, self.format)
    
    def params(self, circuitObject, label="", caption="", position=0):
        """
        Creates a table with undefined parameters of *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if len(circuitObject.params) > 0:
            headerList = ["Name"]
            linesList   = []
            for parName in circuitObject.params:
                linesList.append([parName])
            RST = _RSTcreateCSVtable(caption, headerList, linesList, 
                                     position=position, label=label)
        else:
            RST = '**No undefined parameters in: ' +  circuitObject.title + '**\n\n'
        return Snippet(RST, self.format)

    def pz(self, resultObject, label="", caption="", position=0):
        """
        Creates a table or tables with results of pole/zero analysis stored in *resultObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption(s).
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
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
                numeric = _checkNumeric(resultObject.poles)
            elif resultObject.dataType == 'zeros':
                numeric = _checkNumeric(resultObject.zeros)
            elif resultObject.dataType == 'pz':
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

            RST += _RSTcreateCSVtable(caption, headerList, linesList, 
                                      position=position, label=label)
        return Snippet(RST, self.format)

    def noiseContribs(self, resultObject, label="", caption="", position=0):
        """
        Creates a table with results of noise analysis stored in *resultObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption(s).
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if resultObject.dataType == 'noise' and resultObject.step == False:
            detunits = resultObject.detUnits + '**2/Hz'
            if resultObject.srcUnits != None:
                srcunits = resultObject.srcUnits + '**2/Hz'
            # Add a table with noise contributions
            linesList = []
            headerList = ['', 'Value' , 'Units']
            for src in resultObject.onoiseTerms.keys():
                if src[0].upper() == 'I':
                    units = 'A**2/Hz'
                elif src[0].upper() == 'V':
                    units = 'V**2/Hz'
                #units = sp.sympify(units)
                line = [src + ': Source value', resultObject.snoiseTerms[src],
                        units]
                linesList.append(line)
                if resultObject.srcUnits != None:
                    line = [src + ': Source-referred', 
                            resultObject.inoiseTerms[src], srcunits]
                    linesList.append(line)
                line = [src + ': Detector-referred', 
                        resultObject.onoiseTerms[src], detunits]
                linesList.append(line)
            RST = _RSTcreateCSVtable(caption, headerList, linesList, unitpos=2, 
                                     label=label)
        else:
            RST = ''
            print('noise2RST: Error: wrong data type, or stepped analysis.')
        return Snippet(RST, self.format)

    def dcvarContribs(self, resultObject, label="", caption="", position=0):
        """
        Creates a table with results of dcvar analysis stored in *resultObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will used as table caption(s).
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if resultObject.dataType == 'dcvar' and resultObject.step == False:
            detunits = resultObject.detUnits + '**2'
            if resultObject.srcUnits != None:
                srcunits = resultObject.srcUnits + '**2'
            # Add a table with dcvar contributions
            linesList = []
            headerList = ['', 'Value' , 'Units']
            for src in resultObject.ovarTerms.keys():
                if src[0].upper() == 'I':
                    units = 'A**2'
                elif src[0].upper() == 'V':
                    units = 'V**2'
                #units = sp.sympify(units)
                line = [src + ': Source value', resultObject.svarTerms[src], units]
                linesList.append(line)
                if resultObject.srcUnits != None:
                    line = [src + ': Source-referred', resultObject.ivarTerms[src], 
                            srcunits]
                    linesList.append(line)
                line = [src + ': Detector-referred', resultObject.ovarTerms[src], 
                        detunits]
                linesList.append(line)
            RST = _RSTcreateCSVtable(caption, headerList, linesList, unitpos=2, 
                                     label=label)
        else:
            RST = ''
            print('dcvar2RST: Error: wrong data type, or stepped analysis.')
        return Snippet(RST, self.format)

    def specs(self, specs, specType, label="", caption="", position=0):
        """
        Creates a table with specifications of type *specType*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param specs: List with SLiCAP.SLiCAPdesignData.specItem objects.
        :type specs: list
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        linesList  = []
        headerList = ["Name", "Description", "value", "units"]
        for specItem in specs:
            if specItem.specType.lower()==specType.lower():
                linesList.append(specItem._specLine())
        if len(linesList) > 0:
            RST = _RSTcreateCSVtable(caption, headerList, linesList, label=label, 
                                     position=position) + '\n'
        else:
            RST =  "**Found no specifications of type: " + specType + ".**\n\n"
        return Snippet(RST, self.format)

    def eqn(self, LHS, RHS, units="", label="", multiline=False, position=0):
        """
        Creates a displayed (numbered) equation.

        :param LHS: Left hand side of the equation.
        :type LHS: str, sympy.Symbol, sympy.Expr

        :param RHS: Right hand side of the equation.
        :type RHS: sympy.Symbol, sympy.Expr

        :param units: Units
        :type units: str
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param multiline: True breaks the equation over multiple lines
        :type multiline: Bool
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> rst = sl.RSTformatter()
        >>> lhs = sp.sympify("e^(1j*pi)")
        >>> rhs = sp.N(-1)
        >>> rst.eqn(lhs, rhs, label="nice_eqn").save("nice_eqn")
        """
        spaces = _makeSpaces(position)
        RST = spaces + '.. math::\n'
        if label != '':
            RST += spaces + '    :label: ' + label + '\n'
        RST += '\n'
        try:
            units = units2TeX(units)
        except:
            units = ''
        RST += spaces + '    ' + sp.latex(roundN(LHS)) + ' = ' + sp.latex(roundN(RHS))
        if units != '':
            RST += '\\,\\,\\left[\\mathrm{' + units + '}\\right]\n\n'
        return Snippet(RST, self.format)

    def matrixEqn(self, Iv, M, Dv, label="", position=0):
        """
        Creates a displayed matrix equation without evaluating it.

        :param Iv: Left hand side of the equation: vector with independent variables
        :type Iv: sympy.Matrix

        :param M: Right hand side of the equation: matrix
        :type M: sympy.Matrix

        :param Dv: Righthand side of the equation: vector with dependent variables
        :type Dv: sympy.Matrix
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
 
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        spaces = _makeSpaces(position)
        RST = spaces + '.. math::\n'
        if label != '':
            RST += spaces + '    :label: ' + label + '\n'
        RST += '\n'
        RST += spaces + '    ' + sp.latex(roundN(Iv)) + '='
        RST += sp.latex(roundN(M)) + '\\cdot ' + sp.latex(roundN(Dv)) + '\n\n'
        return Snippet(RST, self.format)

    def stepArray(self, stepVars, stepArray, label="", caption="", position=0):
        """
        Creates a table with step array values. 
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param stepVars: List with step variables (*str, sympy.Symbol*).
        :type stepVars: list
        
        :param stepArray: List with lists with step values for each step variable
        :type stepArray: List
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        RST = ''
        numVars = len(stepVars)
        numRuns = len(stepArray[0])
        headerList = [sp.sympify(stepVar) for stepVar in stepVars]
        linesList = []
        for i in range(numRuns):
            line = []
            for j in range(numVars):
                line.append(stepArray[j][i])
            linesList.append(line)
        RST = _RSTcreateCSVtable(caption, headerList, linesList, position=position, 
                                 label=label) + '\n\n'
        return Snippet(RST, self.format)

    def coeffsTransfer(self, transferCoeffs, label="", caption="", position=0):
        """
        Creates a tablestable that displays the numerator and denominator 
        coefficients of a rational expression. 
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.
        
        :param stepVars: List with step variables (*str, sympy.Symbol*).
        :type stepVars: list
        
        :param stepArray: List with lists with step values for each step variable
        :type stepArray: List
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> rst  = sl.RSTformatter()
        >>> expr = sp.sympify("A_0*(1+s*b_1)/(((1+s*a_1))*((1+s*a_2)))")
        >>> tr_coeffs = sl.coeffsTransfer(expr)
        >>> rst.coeffsTransfer(tr_coeffs, 
                               label="tab-coeffs",
                               caption = "numerator and denominator " +
                               "coefficients").save("coeffs")
        
        """
        (gain, numerCoeffs, denomCoeffs) = transferCoeffs
        headerList = ['Coeff', 'Value']
        linesList = []
        for i in range(len(numerCoeffs)):
            linesList.append([sp.sympify('b_' + str(i)), numerCoeffs[i]])
        for i in range(len(denomCoeffs)):
            linesList.append([sp.sympify('a_' + str(i)), denomCoeffs[i]])
        RST = _RSTcreateCSVtable(caption, headerList, linesList, label=label, 
                                 position=position)
        return Snippet(RST, self.format)

    def file(
        self, fileName, lineRange=None, firstNumber=None, position=0):
        """
        Creates a LaTeX `\\input{}` command for literally displaying a file.
        
        :param fileName: Name of the file. Path is absolute or relative to the 
                         project directory
        :type fileName: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :param position: Number of spaces to indent
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        spaces = _makeSpaces(position)
        RST = spaces + '.. literalinclude:: /' + fileName + '\n'
        RST += spaces + '    :linenos:\n'
        if lineRange != None:
            RST += spaces + '    :lines: ' + lineRange + '\n'
            if firstNumber != None:
                RST += spaces + '    :lineno-start: ' + str(firstNumber) + '\n'
        return Snippet(RST, self.format)

    def expr(self, expr, units="", name=None):
        """
        Creates in inline expression. 
        
        :param expr: Expression
        :type expression: sympy.Expr
        
        :param units: Units
        :type units: str
        
        :param name: Name of the variable for RST substitution.
        :type name: str:
            
        :return: SLiCAP Snippet object with save variable append mode
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if type(name) == str and len(name) > 0:
            try:
                units = units2TeX(units)
            except:
                pass
            RST = ':math:`' + sp.latex(roundN(expr))
            if units != '':
                RST += '\\, \\left[ \\mathrm{' + units + '} \\right]` '
            else:
                RST += '` '
            RST = '.. |' + name + '| replace:: ' + RST + '\n'
        else:
            raise NameError
        return Snippet(RST, self.format, mode="a")

    def eqnInline(self, LHS, RHS, units="", name=None):
        """
        Creates in inline equation. 
        
        :param LHS: Left hand side of the equation
        :type LHS: sympy.Expr, str
                
        :param RHS: Right hand side of the equation
        :type RHS: sympy.Expr
        
        :param units: Units
        :type units: str
        
        :param name: Name of the variable for RST substitution.
        :type name: str:
            
        :return: SLiCAP Snippet object with save variable append mode
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if type(name) == str and len(name) > 0:
            try:
                units = units2TeX(units)
            except:
                pass
            RST = ':math:`' + sp.latex(roundN(LHS)) + '=' + sp.latex(roundN(RHS))
            if units != '':
                RST += '\\, \\left[ \\mathrm{' + units + '} \\right]` '
            else:
                RST += '` '
            RST = '.. |' + name + '| replace:: ' + RST + '\n'
        else:
            raise NameError
        return Snippet(RST, self.format, mode="a")

# Non-public functions for creating table snippets

def _RSTcreateCSVtable(name, headerList, linesList, position=0, unitpos=None, 
                       label=''):
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
            if i == unitpos:
                RST += ':math:`\\mathrm{' + units2TeX(item) + '}`, '
            elif type(item) == str:
                RST += '"' + item + '", '
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
            if imagpart == 0:
                line = [sp.Symbol(pz + '_' + str(i)), realpart, imagpart, frequency ]
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
            line = [sp.Symbol(pz + '_' + str(i)), ':math:`' + sp.latex(roundN(sp.simplify(root/2/sp.pi))) + '`']
        else:
            line = [sp.Symbol(pz + '_' + str(i)), ':math:`' + sp.latex(roundN(root)) + '`']
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
