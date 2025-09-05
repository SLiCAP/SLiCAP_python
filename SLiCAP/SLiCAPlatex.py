#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

SLiCAP formatterfor generating snippets that can be stored as LaTeX files
and included in other LaTeX files.
"""
import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import fullSubs, roundN, _checkNumeric, units2TeX
from pathlib import PureWindowsPath
from SLiCAP.SLiCAPprotos import _BaseFormatter, Snippet
import re

class LaTeXformatter(_BaseFormatter):
    """
    Latex formatter. The methods return LaTeX snippets.
        
    :example:
    
    >>> import SLiCAP as sl
    >>> sl.initProject("formatter")
    >>> ltx = sl.LaTeXformatter()   # Creates an instance of a LaTeX formatter
    """
    def __init__(self):
        super().__init__()
        self.format = "latex"
        self.snippet = None

    def netlist(self, netlistFile, lineRange=None, firstNumber=None):
        """
        Creates a LaTeX `\\input{}` or an RST '.. literalinclude:: '
        command for including a netlist file.
        
        :param netlistFile: Name of the netlist file relative to the project circuit directory
        :type netlistFile: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example: latex
        
        >>> import SLiCAP as sl
        >>> ltx = sl.LaTeXformatter() # Creates a LaTeX formatter
        >>> latex_netlist = ltx.netlist("myFirstRCnetwork.cir")
        >>> latex_netlist.save("netlist")
        
        This will save a file `netlist.tex` in the `sl.ini.tex_snippets` folder 
        with the following contents:
        
        .. code::
        
            \\textbf{Netlist: myFirstRCnetwork.cir}
            \\lstinputlisting[language=ltspice, numbers=left]{<full path to myFirstRCnetwork.cir>}
        
        The netlist file is assumed to reside in the folder given by `sl.ini.cir_path`.
        If you want to include a file from any other location, use: 
        
        >>> ltx.file()
        """
        netlistFile  = netlistFile.replace("_", "\\_")
        TEX = '\\textbf{Netlist: ' + netlistFile + '}\n\n'
        TEX += '\\lstinputlisting[language=ltspice, numbers=left'
        if lineRange != None:
            TEX += ', linerange={' + lineRange + '}'
        if firstNumber != None:
            TEX += ', firstnumber=' + str(int(firstNumber))
        TEX += ']{' + ini.project_path + ini.cir_path + netlistFile + '}\n\n'
        
        return Snippet(TEX, self.format)
                
    def elementData(self, circuitObject, label="", caption="", 
                    color="myyellow"):
        """
        Creates a table with data of expanded netlist elements of 
        *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit 
                              data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty 
                      string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        headerList = ["ID", "Nodes", "Refs", "Model", "Param", "Symbolic", 
                      "Numeric"]
        alignstring= '[c]{lllllll}'
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
        TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                 label=label, caption=caption, color=color)
        return Snippet(TEX, self.format)

    def parDefs(self, circuitObject, label="", caption="", color="myyellow"):
        """
        Creates a table with parameter definitions of *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit
                              data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty 
                      string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        
        headerList = ["ID", "Nodes", "Refs", "Model", "Param", "Symbolic",
                      "Numeric"]
        alignstring= '[c]{lllllll}'
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
        TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                 label=label, caption=caption, color=color)
        return Snippet(TEX, self.format)

    def dictTable(self, dct, head=None, label="", caption="", 
                  color="myyellow"):
        """
        Creates a table from a dictionary; optionally with a header.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param dct: Dictionary with key-value pairs.
        :type circuitObject: dict
        
        :param head: List with names for the key column and the value column, 
                     respectively. List items will be converted to string.
        :type head: list
        
        :param label: Reference label for the table. Defaults to an empty 
                      string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
                
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> 
        >>> sl.initProject("Documentation")
        >>> ltx = sl.LaTeXformatter()
        >>> header = ["name", "age"]
        >>> data   = {"John": 89, Mary: 104}
        >>> ltx.dictTable(data, head=header, caption="Some of my friends").save("friends")
        """
        TEX = None
        if len(dct.keys()) > 0:
            if type(head) == list and len(head) == 2:
                headerList = [str(head[0]), str(head[1])]
            else: 
                headerList  = ["", ""]
            linesList   = []
            alignstring = '[c]{ll}'
            for key in dct.keys():
                line = [key, dct[key]]
                linesList.append(line)
            TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                     label=label, caption=caption, 
                                     color=color)
        return Snippet(TEX, self.format)
    
    def params(self, circuitObject, label="", caption="", color="myyellow"):
        """
        Creates a table with undefined parameters of *circuitObject*.
        If no label AND no caption are given this method returns a LaTeX
        tabular snippet. Else it returns a table snippet.

        :param circuitObject: SLiCAP circuit object that comprises the circuit 
                              data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty 
                      string.
        :type label: str
        
        :param caption: Text that will used as table caption.
        :type caption: str
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if len(circuitObject.params) > 0:
            TEX         = '{\\textbf{Undefined parameters in: ' 
            TEX        += circuitObject.title + '}}\n\n'
            headerList  = ["Name"]
            alignstring = '[c]{l}'
            linesList   = []
            for parName in circuitObject.params:
                linesList.append([parName])
            TEX += _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                      label=label, caption=caption, 
                                      color=color)
        else:
            TEX = '{\\textbf{No undefined parameters in: ' 
            TEX +=  circuitObject.title + '}}\n\n'
        return Snippet(TEX, self.format)

    def pz(self, resultObject, label="", caption="", color="myyellow"):
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
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        if resultObject.errors != 0:
            print("pz2TEX: Errors found in instruction.")
            TEX = ''
        elif resultObject.dataType != 'poles' and resultObject.dataType != 'zeros' and resultObject.dataType != 'pz':
            print("pz2TEX: Error: 'pz2RST()' expected dataType: 'poles', 'zeros', or 'pz', got: '{0}'.".format(resultObject.dataType))
            TEX = ''
        elif resultObject.step == True :
            print("pz2TEX: Error: parameter stepping not implemented for 'pz2RST()'.")
            TEX = ''
        else:
            TEX = ''
            if len(resultObject.poles) != 0:
                numericPoles = _checkNumeric(resultObject.poles)
            else:
                numericPoles = True
            if len(resultObject.zeros) != 0:
                numericZeros = _checkNumeric(resultObject.zeros)
            else:
                numericZeros = True
            if numericPoles and numericZeros:
                numeric = True
            else:
                numeric = False
            if numeric:
                alignstring = '[c]{lrrrrr}'
                if ini.hz == True:
                    headerList = ['\\#', 'Re [Hz]', 'Im [Hz]', 'f [Hz]', 'Q']
                else:
                    headerList = ['\\#', 'Re [rad/s]', 'Im [rad/s]', '$\\omega$ [rad/s]', 'Q']
            else:
                alignstring = '[c]{ll}'
                if ini.hz == True:
                    headerList = ['\\#', 'f [Hz]']
                else:
                    headerList = ['\\#', '$\\omega$ [rad/s]']
            linesList = []
            if len(resultObject.poles) != 0:
                if numeric:
                    linesList += _numRoots2TEX(resultObject.poles, ini.hz, 'p')
                else:
                    linesList = _symRoots2TEX(resultObject.poles, ini.hz, 'p')
            if len(resultObject.zeros) != 0:
                if resultObject.dataType == 'pz':
                    linesList += [' ']
                if numeric:
                    linesList += _numRoots2TEX(resultObject.zeros, ini.hz, 'z')
                else:
                    linesList = _symRoots2TEX(resultObject.zeros, ini.hz, 'z')
            TEX += _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                      label=label, caption=caption, 
                                      color=color)
        return Snippet(TEX, self.format)

    def noiseContribs(self, resultObject, label="", caption="", color="myyellow"):
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
                
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        TEX = ''
        if resultObject.dataType == 'noise' and resultObject.step == False:
            detunits = resultObject.detUnits + '**2/Hz'
            if resultObject.srcUnits != None:
                srcunits = resultObject.srcUnits + '**2/Hz'
            # Add a table for source contributions
            linesList = []
            alignstring = '[c]{lll}'
            headerList = ['Name', 'Value' , 'Units']
            linesList = []
            for src in resultObject.onoiseTerms.keys():
                if src[0].upper() == 'I':
                    units = 'A**2/Hz'
                elif src[0].upper() == 'V':
                    units = 'V**2/Hz'
                #units = sp.sympify(units)
                line = [src + ': Value' , resultObject.snoiseTerms[src], units]
                linesList.append(line)
                if resultObject.srcUnits != None:
                    line = [src + ': Source-referred', 
                            resultObject.inoiseTerms[src], srcunits]
                    linesList.append(line)
                line = [src + ': Detector-referred', 
                        resultObject.onoiseTerms[src], detunits]
                linesList.append(line)
            TEX += _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                      unitpos=2, caption=caption, 
                                      label=label, color=color)
        else:
            print('noiseContribs2TEX: Error: wrong data type, or stepped analysis.')
        return Snippet(TEX, self.format)

    def dcvarContribs(self, resultObject, label="", caption="", color="myyellow"):
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
                
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        TEX = ''
        if resultObject.dataType == 'dcvar' and resultObject.step == False:
            detUnits = resultObject.detUnits + '**2'
            if resultObject.srcUnits != None:
                srcUnits = resultObject.srcUnits + '**2'
            else:
                srcUnits = ""
            # Add a table for source contributions
            linesList = []
            alignstring = '[c]{lll}'
            headerList = ['Name', 'Value' , 'Units']
            linesList = []
            for src in resultObject.ovarTerms.keys():
                if src[0].upper() == 'I':
                    units = 'A**2'
                elif src[0].upper() == 'V':
                    units = 'V**2'
                #units = sp.sympify(units)
                line = [src + ': Value' , resultObject.svarTerms[src], units]
                linesList.append(line)
                if resultObject.srcUnits != None:
                    line = [src + ': Source-referred', 
                            resultObject.ivarTerms[src], srcUnits]
                    linesList.append(line)
                line = [src + ': Detector-referred', 
                        resultObject.ovarTerms[src], detUnits]
                linesList.append(line)
            TEX += _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                      unitpos=2, caption=caption, label=label, 
                                      color=color)
        else:
            print('dcvarContribs2TEX: Error: wrong data type, or stepped analysis.')
        return Snippet(TEX, self.format)

    def specs(self, specs, specType, label="", caption="", color="myyellow"):
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
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        linesList   = []
        alignstring = '[c]{llrl}'
        headerList  = ["name", "description", "value", "units"]
        for specItem in specs:
            if specItem.specType.lower() == specType.lower():
                linesList.append(specItem._specLine())
        if len(linesList) > 0:
            TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                     unitpos=3, caption=caption, label=label, 
                                     color=color) + '\n'
        else:
            TEX =  "\\textbf{Found no specifications of type: " 
            TEX += specType + ".}\n\n"
        return Snippet(TEX, self.format)

    def eqn(self, LHS, RHS, units="", label="", multiline=False):
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
        
        :param multiline: n breaks the equation over multiple lines with n sums
                          or products per line
        :type multiline: int, Bool
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> ltx = sl.LaTeXformatter()
        >>> lhs = sp.sympify("e^(1j*pi)")
        >>> rhs = sp.N(-1)
        >>> ltx.eqn(lhs, rhs, label="nice_eqn").save("nice_eqn")
        """
        try:
            units = units2TeX(units)
        except:
            units = ''
        if type(LHS) == str:
            LHS = sp.sympify(LHS)
        if type(RHS) == str:
            RHS = sp.sympify(RHS)
        if multiline:
            TEX = '\n' + sp.multiline_latex(roundN(LHS), roundN(RHS), 
                                            terms_per_line=multiline)
            TEX = TEX.replace('\\\\\n', '\\nonumber \\\\\n')
            TEX = TEX.replace('{align*}', '{align}')
            if label != '':
                TEX = TEX.replace('\\end{align}', '\\label{%s}\n\\end{align}'%(label))
            TEX += '\\,\\left[\\mathrm{' + units + '}\\right]\n'
        else:
            TEX = '\\begin{equation}'
            TEX += '\n' + sp.latex(roundN(LHS)) + ' = ' + sp.latex(roundN(RHS))
            if units != '':
                TEX += '\\,\\left[\\mathrm{' + units + '}\\right]'
            TEX += '\n'
            if label != '':
                TEX += '\\label{'+ label + '}\n'
            TEX += '\\end{equation}\n\n'
        return Snippet(TEX, self.format)

    def matrixEqn(self, Iv, M, Dv, label=""):
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
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        TEX =  '\\begin{equation}\n'
        TEX += sp.latex(roundN(Iv)) + '=' + sp.latex(roundN(M)) + '\\cdot ' 
        TEX += sp.latex(roundN(Dv)) + '\n'
        if label != '':
            TEX += '\\label{'+ label + '}\n'
        TEX += '\\end{equation}\n\n'
        return Snippet(TEX, self.format)

    def stepArray(self, stepVars, stepArray, label="", caption="",
                  color="myyellow"):
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
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        numVars = len(stepVars)
        numRuns = len(stepArray[0])
        headerList = [' '] + stepVars
        alignString = '[c]{l'
        for i in range(len(stepVars)):
            alignString += 'l'
        alignString += '}'
        linesList = []
        for i in range(numRuns):
            line = ['Run ' + str(i+1) + ':']
            for j in range(numVars):
                line.append(stepArray[j][i])
            linesList.append(line)
        TEX = _TEXcreateCSVtable(headerList, linesList, alignString, 
                                 label=label, caption=caption, color=color)
        return Snippet(TEX, self.format)

    def coeffsTransfer(self, transferCoeffs, label="", caption="", 
                       color="myyellow"):
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
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> ltx  = sl.LaTeXformatter()
        >>> expr = sp.sympify("A_0*(1+s*b_1)/(((1+s*a_1))*((1+s*a_2)))")
        >>> tr_coeffs = sl.coeffsTransfer(expr)
        >>> ltx.coeffsTransfer(tr_coeffs, 
                               label="tab-coeffs",
                               caption = "numerator and denominator " +
                               "coefficients").save("coeffs")
        """
        (gain, numerCoeffs, denomCoeffs) = transferCoeffs
        num, den = gain.as_numer_denom()
        for i in range(len(numerCoeffs)):
            numerCoeffs[i] *= num
        for i in range(len(denomCoeffs)):
            denomCoeffs[i] *= den
        alignstring = '[c]{ll}'
        headerList = ['Coeff', 'Value']
        linesList = []
        for i in range(len(numerCoeffs)):
            linesList.append([sp.sympify('b_' + str(i)), numerCoeffs[i]])
        for i in range(len(denomCoeffs)):
            linesList.append([sp.sympify('a_' + str(i)), denomCoeffs[i]])
        TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                 label=label, caption=caption, color=color)
        return Snippet(TEX, self.format)

    def file(
        self, fileName, lineRange=None, firstNumber=None, language=None, 
        style=None):
        """
        Creates a LaTeX `\\input{}` command for literally displaying a file.
        
        :param fileName: Name of the file. Path is absolute or relative to the 
                         project directory
        :type fileName: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :param language: SLiCAP built-in languages:
                         
                         - ltspice
                         
        :type language: str
        
        :param style: SLiCAP built-in styles:
                         
                         - slicap
                         - latex
                         
        :type style: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPprotos.Snippet
        """
        short_name = PureWindowsPath(fileName).parts[-1]
        fileName   = fileName.replace("_", "\\_")
        short_name = short_name.replace("_", "\\_")
        TEX = '{\\textbf{File:} ' + short_name + '}\n\n'
        
        if type(language) == str and len(language) > 0:
            TEX += '\\lstinputlisting[language=%s, numbers=left'%(language)
        elif type(style) == str and len(style) > 0:
            TEX += '\\lstinputlisting[style=%s, numbers=left'%(style)
        else:
            TEX += '\\lstinputlisting[numbers=left'
        if lineRange != None:
            TEX += ', linerange={' + lineRange + '}'
        if firstNumber != None:
            TEX += ', firstnumber=' + str(int(firstNumber))
        TEX += ']{' + fileName + '}\n\n'
        return Snippet(TEX, self.format)

    def expr(self, expr, units=""):
        """
        Creates in inline expression. If format='rst', this expression is 
        stored (name = expr) in the file 'substitutions.rst'. 
        The location of this file is given in the file:
            
        SLiCAP.ini -> [projectpaths] -> rst_snippets
        
        :param expr: Expression
        :type expression: sympy.Expr
        
        :param units: Units
        :type units: str
        """
        try:
            units = units2TeX(units)
        except:
           units = ''
        TEX = '$' + sp.latex(roundN(expr))
        if units == '':
            TEX += '$ '
        else:
            TEX += '\\left[ \\mathrm{' + units + '} \\right] $ '
        return Snippet(TEX, self.format)

    def eqnInline(self, LHS, RHS, units=""):
        """
        Creates in inline equation. If format='rst', this equation is 
        stored (name = equation) in the file 'substitutions.rst'. 
        The location of this file is given in the file:
            
        SLiCAP.ini -> [projectpaths] -> rst_snippets
        
        :param LHS: Left hand side of the equation
        :type LHS: sympy.Expr, str
                
        :param RHS: Right hand side of the equation
        :type RHS: sympy.Expr
        
        :param units: Units
        :type units: str
        """
        try:
            units = units2TeX(units)
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
        return Snippet(TEX, self.format)

    def nestedLists(self, headerList, linesList, unitpos=None, caption='', 
                    label='', color="myyellow"):
        """
        Creates and returns a LaTeX table snippet that can be included in a 
        LaTeX document. Each list is converted into a table row and
        must have equal lengths. There can be one column with units. 

        A label can be given as reference and a caption can be added.

        :param headerList: List with column headers.
        :type headerList: list with strings

        :param linesList: List with lists of table data for each table row
        :type linesList: list

        :param unitpos: Position of column with units (will be typesetted with mathrm)
        :type unitpos: int, str

        :param caption: Table caption, defauls to ''
        :type caption: str

        :param label: Table reference label
        :type label: str

        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                     no background color.
        :type color: str
        
        :return: LaTeX snippet to be included in a LaTeX document
        :rtype: str
        """
        alignstring = "[c]{"
        for item in headerList:
            alignstring += "l"
        alignstring += "}"
        TEX = _TEXcreateCSVtable(headerList, linesList, alignstring, 
                                 unitpos, caption, label, color)
        return Snippet(TEX, self.format)

def sub2rm(textext):
    """
    Converts italic fonts LaTeX subscripts into mathrm fonts.
    
    :param textext: LaTeX snippet
    :type textxt: str
    
    :return: Modified LaTeX snippet
    :rtype: str
    
    :example:
        
    >>> textext = "\\frac{V_{out}}{V_{in}}"
    >>> print(sub2rm(textext))
    \\frac{V_{\\mathrm{out}}}{V_{\\mathrm{in}}}
    """
    pos = 0
    out = ''
    pattern = re.compile(r'_{([a-zA-Z0-9]+)}')
    for m in re.finditer(pattern, textext):
        out += textext[pos:m.start()+1]+'{\\mathrm'+textext[m.start()+1: m.end()]+'}'
        pos = m.end()
    out += textext[pos:]
    return out
        
# Non-public functions for creating table snippets

def _TEXcreateCSVtable(headerList, linesList, alignstring, unitpos=None, caption='', label='', color="myyellow"):
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

    :param color: Alternate row color name, should be defined in 
                 'preambuleSLiCAP.tex' defaults to 'myyellow'. Use None for
                 no background color.
    :type color: str
        
    :return: LaTeX snippet to be included in a LaTeX document
    :rtype: str
    """
    if caption != '' or label != '':
        TEX =  '\\begin{table}[H]\n\\centering\n'
    else:
        TEX = ''
    TEX += '\\begin{tabular}' + alignstring + '\n'
    for field in headerList:
        if type(field) == str:
            TEX += '\\textbf{' + field + '} & '
        else:
            TEX += '$\\mathbf{' + sp.latex(roundN(field)) + '}$ & '
    TEX = TEX[:-2] + '\\\\ \n'
    j = 0
    for line in linesList:
        i = 0
        if not j%2 and color != None:
            TEX += '\\rowcolor{%s}\n'%(color)
        for field in line:
            if unitpos != None and i == int(unitpos):
                TEX += '$\\mathrm{' + units2TeX(field) + '}$ &'
            elif type(field) == str:
                if field != '':
                    TEX +=  '\\small{' + field.replace('_', '\\_') + '} &'
                else:
                    TEX += ' &'
            else:
                TEX += '$' + sp.latex(roundN(sp.N(field))) + '$ &'
            i += 1
        TEX = TEX[:-2] + ' \\\\ \n'
        j += 1
    TEX += '\\end{tabular}\n'
    if caption != '' or label != '':
        TEX += '\\caption{' + caption + '}\n'
        if label != '':
            TEX += '\\label{' + label + '}\n'
        TEX += '\\end{table}\n\n'
    return TEX

def _numRoots2TEX(roots, Hz, pz):
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
        if Hz:
            root  = sp.N(root/2/sp.pi)
        else:
            root  = sp.N(root)
        realpart  = roundN(sp.re(root))
        imagpart  = roundN(sp.im(root))
        frequency = roundN(sp.Abs(root))
        Q = roundN(frequency/(2*sp.Abs(realpart)))
        if imagpart == 0:
            line = [sp.Symbol(pz + '_' + str(i)), realpart, imagpart, frequency]
        else:
            line = [sp.Symbol(pz + '_' + str(i)), realpart, imagpart, frequency, Q]
        lineList.append(line)
    return lineList

def _symRoots2TEX(roots, Hz, pz):
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
            line = [sp.Symbol(pz + '_' + str(i)), 
                    '$' + sp.latex(roundN(root/2/sp.pi)) + '$']
        else:
            line = [sp.Symbol(pz + '_' + str(i)), '$' + sp.latex(roundN(root)) + '$']
        lineList.append(line)
    return lineList
