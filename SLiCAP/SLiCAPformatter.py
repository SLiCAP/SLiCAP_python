"""
Classes and functions used by the formatters.
"""

import os
from pathlib import Path
from collections import namedtuple
from functools import wraps
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPlatex import *
from SLiCAP.SLiCAPrst import *

# Prefix and suffix for files depending on format
_Entry = namedtuple("_Entry", ["prefix", "suffix"])
_FORMATS: dict[str, tuple[str, str]] = {
    "raw"   : _Entry("", ""),
    "latex" : _Entry(ini.tex_snippets,  ".tex"),
    "rst"   : _Entry(ini.rst_snippets,  ".rst"),
    "myst"  : _Entry(ini.myst_snippets, ".md"),
    "md"    : _Entry(ini.md_snippets,   ".md"),
    "html"  : _Entry(ini.html_snippets, ".html"),
}

class Snippet:
    """
    Text snippet created by the formatters.
    """
    def __init__(self, snippet: str = "", format: None | str = None) -> None:
        self._snippet = snippet
        if format is None:
            self._format = "raw"
            self._prefix, self._suffix = _FORMATS[self._format]
        else:
            try:
                self._prefix, self._suffix = _FORMATS[format]
                self._format = format
            except KeyError:
                raise KeyError(f"Unknown formatting: {format}.")

    @property
    def snippet(self):
        """
        Will be set by the formatter method.
        """
        return self._snippet

    @property
    def format(self):
        """
        Will be set by the formatter method.
        """
        return self._format

    def __str__(self):
        return self._snippet

    def __repr__(self):
        return f'Snippet("{self.snippet}", format="{self.format}")'

    def save(self, filenameOrPath: str | Path):
        """
        Saves the snippet.

        If the path is absolute, it saves it in that location.
        Otherwise, the preffix and suffix are added according to format:
            
            - latex
            
              - prefix: project folder -> SLiCAP.ini -> [projectpaths] -> tex_snippets
              - suffix: '.tex'
                  
            - rst
            
              - prefix: project folder -> SLiCAP.ini -> [projectpaths] -> rst_snippets
              - suffix: '.rst'    
              
            - myst
            
              - prefix: project folder -> SLiCAP.ini -> [projectpaths] -> myst_snippets
              - suffix: '.md'
                  
            - html
            
              - prefix: project folder -> SLiCAP.ini -> [projectpaths] -> html_snippets
              - suffix: '.html

            - md
            
              - prefix: project folder -> SLiCAP.ini -> [projectpaths] -> md_snippets
              - suffix: '.md'
        """
        if self.snippet != None:
            if not filenameOrPath:
                raise ValueError("No filename given to save snippet.")
            if isinstance(filenameOrPath, Path):
                filenameOrPath = str(filenameOrPath)
            if os.path.isabs(filenameOrPath):
                filePath = filenameOrPath
            else:
                filePath = self._prefix + filenameOrPath + self._suffix
            with open(filePath, "w") as f:
                f.write(self.snippet)
        
class _BaseFormatter:
    """
    Formatter base class.
    Does not implement functionality, but it should define a minimum
    interface via NotImplementedError that all formatters should support.
    """

    def __init__(self, format):
        if format in _FORMATS.keys():
            self.format = format
            try:
                os.remove(ini.rst_snippets + "substitutions.rst")
            except FileNotFoundError :
                pass
        else:
            raise NotImplementedError

class formatter(_BaseFormatter):
    """
    Formatter with of which the type can be set with the parameter *format* and
    snippets can be created with formatter methods.
    
    :param format: formatter type; can be one of the following:
        
                   - latex: provides LaTeX formatting
                   - rst: provides ReStructuredText formatting
                   - myst: not (yet) implemented
                   - md: not (yet) implemented
                   - html: not (yet) implemented
    :type format: str
        
    :example:
    
    >>> import SLiCAP as sl
    >>> ltx = sl.formatter("latex") # Creates a LaTeX formatter
    >>> rst = sl.formatter("rst")   # Creates a ReStructuredText formatter
    """

    def __init__(self, format):
        super().__init__(format)
        self.format = format
        self.snippet = None

    def netlist(self, netlistFile, lineRange=None, firstNumber=None, 
                position=0):
        """
        Creates a LaTeX `\\input{}` or an RST '.. literalinclude:: '
        command for including a netlist file.
        
        :param netlistFile: Name of the netlist file relative to the project circuit directory
        :type netlistFile: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        
        :example: latex
        
        >>> import SLiCAP as sl
        >>> ltx = sl.formatter("latex") # Creates a LaTeX formatter
        >>> latex_netlist = ltx.netlist("myFirstRCnetwork.cir")
        >>> latex_netlist.save("netlist")
        
        This will save a file `netlist.tex` in the `sl.ini.tex_snippets` folder 
        with the following contents:
        
        .. code::
        
            \\textbf{Netlist: myFirstRCnetwork.cir}
            \\lstinputlisting[language=ltspice, numbers=left]{<full path to myFirstRCnetwork.cir>}
        
        The netlist file is assumed to reside in the folder given by `sl.ini.cir_path`.
        If you want to include a file from any other location, use: 
        
        >>> ltx.file() # See below.
        
        :example: ReStructuredText
        
        >>> import SLiCAP as sl
        >>> rst = sl.formatter("rst") # Creates a ReStructuredText formatter
        >>> rst.netlist("myFirstRCnetwork.cir").save("netlist")
        
        This will save a file `netlist.rst` in the `sl.ini.rst_snippets` folder 
        with the following contents:
        
        .. code::
        
            .. literalinclude:: <full path to myFirstRCnetwork.cir>
                :linenos:
        """
        if self.format == 'latex':
            self.snippet = Snippet(netlist2TEX(netlistFile, lineRange, 
                                              firstNumber), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(netlist2RST(netlistFile, lineRange, 
                                              firstNumber, position), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet
                
    def elementData(self, circuitObject, label="", append2caption="",
                    position=0, color="myyellow"):
        """
        Creates a table with data of expanded netlist elements of *circuitObject*.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption.
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet( 
                elementData2TEX(circuitObject, label, append2caption, 
                                color=color),
                self.format)
        elif self.format == 'rst':
            self.snippet = Snippet( 
                elementData2RST(circuitObject, label, append2caption, 
                                   position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def parDefs(self, circuitObject, label="", append2caption="", position=0, 
                color="myyellow"):
        """
        Creates a table with parameter definitions of *circuitObject*.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption.
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(parDefs2TEX(circuitObject, label, 
                                                  append2caption, color=color), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(parDefs2RST(circuitObject, label, 
                                                  append2caption, position), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def dictTable(self, dct, head=None, label="", caption="", position=0, 
                  color="myyellow"):
        """
        Creates a table from a dictionary; optionally with a header.

        :param dct: Dictionary with key-value pairs.
        :type circuitObject: dict
        
        :param head: List with names for the key column and the value column, respectively.
                     List items will be converted to string.
        :type head: list
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Text that will be appended to the default table caption.
        :type caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> 
        >>> sl.initProject("Documentation")
        >>> ltx = sl.formatter("latex")
        >>> header = ["name", "age"]
        >>> data   = {"John": 89, Mary: 104}
        >>> ltx.dictTable(data, head=header, caption="Some of my friends").save("friends")
        """
        if self.format == 'latex':
            self.snippet = Snippet(dict2TEX(dct, head, label, caption, 
                                            color=color), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(dict2RST(dct, head, label, caption, 
                                            position), self.format)
        else:
            raise NotImplementedError
        return self.snippet
    
    def params(self, circuitObject, label="", append2caption="", position=0, color="myyellow"):
        """
        Creates a table with undefined parameters of *circuitObject*.

        :param circuitObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type circuitObject: SLiCAP.SLiCAPprotos.circuit
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption.
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(params2TEX(circuitObject, label, 
                                                 append2caption, color=color), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(params2RST(circuitObject, label, 
                                                 append2caption, position),
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def pz(self, resultObject, label="", append2caption="", color="myyellow"):
        """
        Creates a table or tables with results of pole/zero analysis stored in *resultObject*.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption(s).
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(pz2TEX(resultObject, label, 
                                             append2caption, color=color), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(pz2RST(resultObject, label, 
                                             append2caption), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def noiseContribs(self, resultObject, label="", append2caption="", 
                      position=0, color="myyellow"):
        """
        Creates a table with results of noise analysis stored in *resultObject*.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption(s).
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(noiseContribs2TEX(resultObject, label, 
                                                        append2caption, 
                                                        color=color),
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(noiseContribs2RST(resultObject, label, 
                                                        append2caption, 
                                                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def dcvarContribs(self, resultObject, label="", append2caption="",
                      position=0, color="myyellow"):
        """
        Creates a table with results of dcvar analysis stored in *resultObject*.

        :param resultObject: SLiCAP circuit object that comprises the circuit data to be listed.
        :type resultObject: SLiCAP.SLiCAPprotos.allResults
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param append2caption: Text that will be appended to the default table caption(s).
        :type append2caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(dcvarContribs2TEX(resultObject, label, 
                                                        append2caption,
                                                        position, 
                                                        color=color), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(dcvarContribs2RST(resultObject, label, 
                                                        append2caption,
                                                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def specs(self, specs, specType, label="", caption="", position=0, 
              color="myyellow"):
        """
        Creates a table with specifications of type *specType*.

        :param specs: List with SLiCAP.SLiCAPdesignData.specItem objects.
        :type specs: list
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 'preambuleSLiCAP.tex'
        :type color: str
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(specs2TEX(specs, specType, label, 
                                                caption, color=color), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(specs2TEX(specs, specType, label, 
                                                caption, position), 
                                   self.format)
        else:
            raise NotImplementedError

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
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> ltx = sl.formatter("latex")
        >>> lhs = sp.sympify("e^(1j*pi)")
        >>> rhs = sp.N(-1)
        >>> ltx.eqn(lhs, rhs, label="nice_eqn").save("nice_eqn")
        
        """
        if self.format == 'latex':
            self.snippet = Snippet(eqn2TEX(LHS, RHS, units, label, 
                                              multiline), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(eqn2RST(LHS, RHS, units, label, 
                                              position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

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
 
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(matrices2TEX(Iv, M, Dv, label),
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(matrices2RST(Iv, M, Dv, label, position),
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def stepArray(self, stepVars, stepArray, label="", caption="", position=0, 
                  color="myyellow"):
        """
        Creates a table with step array values. 

        :param stepVars: List with step variables (*str, sympy.Symbol*).
        :type stepVars: list
        
        :param stepArray: List with lists with step values for each step variable
        :type stepArray: List
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(stepArray2TEX(stepVars, stepArray, label,
                                                    caption, color=color), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(stepArray2RST(stepVars, stepArray, label,
                                                    caption, position), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def coeffsTransfer(self, transferCoeffs, label="", append2caption="", 
                       position=0, color="myyellow"):
        """
        Creates tables with coefficients of the numerator and the denominator 
        of a rational expression. 
        

        :param stepVars: List with step variables (*str, sympy.Symbol*).
        :type stepVars: list
        
        :param stepArray: List with lists with step values for each step variable
        :type stepArray: List
        
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        
        :example:
            
        >>> import SLiCAP as sl
        >>> import sympy as sp
        >>>
        >>> ltx  = sl.formatter("latex")
        >>> expr = sp.sympify("A_0*(1+s*b_1)/(((1+s*a_1))*((1+s*a_2)))")
        >>> tr_coeffs = sl.coeffsTransfer(expr)
        >>> ltx.coeffsTransfer(tr_coeffs, label="tab-coeffs").save("coeffs")
        
        """
        if self.format == 'latex':
            self.snippet = Snippet(
            coeffsTransfer2TEX(transferCoeffs, label, append2caption, 
                               color=color), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
            coeffsTransfer2RST(transferCoeffs, label, append2caption,
                                  position), self.format)
        else:
            raise NotImplementedError
        return self.snippet
    
    def monomialCoeffs(self, monomialCoeffs, label="", caption="", position=0, 
                       color="myyellow"):   
        """
        Creates and returns a table table with monomials and their coefficients.
                
        :param monomialCoeffs: Dictionary with key-value pairs:
            
                               - key: monomial (*sympy.Expr*, *sympy.Symbol*)
                               - value: coefficient of this monomial (*sympy.Expr*, *sympy.Symbol*)
                               
        :param label: Reference label for the table. Defaults to an empty string.
        :type label: str
        
        :param caption: Table caption.
        :type caption: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param color: Alternate row color name, should be defined in 
                     'preambuleSLiCAP.tex' defaults to 'myyellow'
        :type color: str
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        
        """
        if self.format == 'latex':
            self.snippet = Snippet(
                monomialCoeffs2TEX(monomialCoeffs, label, caption, color=color), 
                self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
                monomialCoeffs2RST(monomialCoeffs, label, caption,
                                      position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def file(
        self, fileName, lineRange=None, firstNumber=None, firstLine=None, 
        language=None, style=None, position=0):
        """
        Creates a LaTeX `\\input{}` or an RST '.. literalinclude:: '
        command for literally displaying a file.
        
        :param fileName: Name of the file. Path is absolute or relative to the 
                         project directory
        :type fileName: str
        
        :param lineRange: range of lines to be included
        :type lineRange: str
        
        :param firstNumber: start number of the displayed line numbers
        :type firstNumber: str
        
        :param language: (LaTeX only) SLiCAP built-in languages:
                         
                         - ltspice
                         
        :type language: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :param style: (LaTeX only) SLiCAP built-in styles:
                         
                         - slicap
                         - latex
                         
        :type style: str
        
        :param position: Number of spaces to indent (RST only)
        :type position: int
        
        :return: SLiCAP Snippet object
        :rtype: SLiCAP.SLiCAPformatter.Snippet
        """
        if self.format == 'latex':
            self.snippet = Snippet(
            file2TEX(fileName, firstNumber, lineRange, 
                        language, style), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
            file2RST(fileName, firstNumber, lineRange, 
                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def expr(self, expr, units="", name=None):
        """
        Creates in inline expression. If format='rst', this expression is 
        stored (name = expr) in the file 'substitutions.rst'. 
        The location of this file is given in the file:
            
        SLiCAP.ini -> [projectpaths] -> rst_snippets
        
        :param expr: Expression
        :type expression: sympy.Expr
        
        :param units: Units
        :type units: str
        
        :param name: Name of the variable for RST substitution.
        :type name: str:
        """
        if self.format == 'latex':
            self.snippet = Snippet(expr2TEX(expr, units), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(expr2RST(expr, units, name), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def eqnInline(self, LHS, RHS, units="", name=None):
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
        
        :param name: Name of the variable for RST substitution.
        :type name: str:
        """
        if self.format == 'latex':
            self.snippet = Snippet(eqn2TEXinline(LHS, RHS, units), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(eqn2RSTinline(LHS, RHS, units, name), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet
