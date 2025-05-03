"""Common classes and functions used by the formatters."""

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
    """Text snippets created by the formatters.

    Its basic functionality is to save itself in a given location.
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
        return self._snippet

    @property
    def format(self):
        return self._format

    def __str__(self):
        return self._snippet

    def __repr__(self):
        return f'Snippet("{self.snippet}", format="{self.format}")'

    def save(self, filenameOrPath: str | Path):
        """Saves the snippet.

        If the path is absolute, it saves it in that location.
        Otherwise, the preffix and suffix is added according to format."""
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
        else:
            raise NotImplementedError

class formatter(_BaseFormatter):
    """
    Formatter, inherited from the base formatter.
    Implements the  functionality.
    """

    def __init__(self, format):
        super().__init__(format)
        self.format = format
        self.snippet = None

    def netlist(self, netlistFile, lineRange=None, firstNumber=None, 
                position=0):
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
                    position=0):
        if self.format == 'latex':
            self.snippet = Snippet( 
                elementData2TEX(circuitObject, label, append2caption),
                self.format)
        elif self.format == 'rst':
            self.snippet = Snippet( 
                elementData2RST(circuitObject, label, append2caption, 
                                   position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def parDefs(self, circuitObject, label="", append2caption="", position=0):
        if self.format == 'latex':
            self.snippet = Snippet(parDefs2TEX(circuitObject, label, 
                                                  append2caption), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(parDefs2RST(circuitObject, label, 
                                                  append2caption, position), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def params(self, circuitObject, label="", append2caption="", position=0):
        if self.format == 'latex':
            self.snippet = Snippet(params2TEX(circuitObject, label, 
                                                 append2caption), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(params2RST(circuitObject, label, 
                                                 append2caption, position),
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def pz(self, resultObject, label="", append2caption=""):
        if self.format == 'latex':
            self.snippet = Snippet(pz2TEX(resultObject, label, 
                                             append2caption), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(pz2RST(resultObject, label, 
                                             append2caption), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def noiseContribs(self, resultObject, label="", append2caption="", 
                      position=0):
        if self.format == 'latex':
            self.snippet = Snippet(noiseContribs2TEX(resultObject, label, 
                                                        append2caption),
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(noiseContribs2RST(resultObject, label, 
                                                        append2caption, 
                                                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def dcvarContribs(self, resultObject, label="", append2caption="",
                      position=0):
        if self.format == 'latex':
            self.snippet = Snippet(dcvarContribs2TEX(resultObject, label, 
                                                        append2caption,
                                                        position), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(dcvarContribs2RST(resultObject, label, 
                                                        append2caption,
                                                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def specs(self, specs, specType, label="", caption="", position=0):
        if self.format == 'latex':
            self.snippet = Snippet(specs2TEX(specs, specType, label, 
                                                caption), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(specs2TEX(specs, specType, label, 
                                                caption, position), 
                                   self.format)
        else:
            raise NotImplementedError

    def eqn(self, LHS, RHS, units="", label="", multiline=0, position=0):
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
        if self.format == 'latex':
            self.snippet = Snippet(matrices2TEX(Iv, M, Dv, label),
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(matrices2RST(Iv, M, Dv, label, position),
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def stepArray(self, stepVars, stepArray, label="", caption="", position=0):
        if self.format == 'latex':
            self.snippet = Snippet(stepArray2TEX(stepVars, stepArray, label,
                                                    caption), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(stepArray2RST(stepVars, stepArray, label,
                                                    caption, position), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def coeffsTransfer(self, transferCoeffs, label="", append2caption="", 
                       position=0):
        if self.format == 'latex':
            self.snippet = Snippet(
            coeffsTransfer2TEX(transferCoeffs, label, append2caption), 
            self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
            coeffsTransfer2RST(transferCoeffs, label, append2caption,
                                  position), self.format)
        else:
            raise NotImplementedError
        return self.snippet
    
    def monomialCoeffs(self, monomialCoeffs, label="", caption="", position=0):        
        if self.format == 'latex':
            self.snippet = Snippet(
                monomialCoeffs2TEX(monomialCoeffs, label, caption), 
                self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
                monomialCoeffs2RST(monomialCoeffs, label, caption,
                                      position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def file(
        self, fileName, firstNumber=None, firstLine=None, lineRange=None, 
        language=None, style=None, position=0):
        if self.format == 'latex':
            self.snippet = Snippet(
            file2TEX(fileName, firstNumber, firstLine, lineRange, 
                        language, style), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(
            file2RST(fileName, firstNumber, firstLine, lineRange, 
                        position), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def expr(self, expr, units="", name=None):
        if self.format == 'latex':
            self.snippet = Snippet(expr2TEX(expr, units), self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(expr2RST(expr, units, name), self.format)
        else:
            raise NotImplementedError
        return self.snippet

    def eqnInline(self, LHS, RHS, units="", name=None):
        if self.format == 'latex':
            self.snippet = Snippet(eqn2TEXinline(LHS, RHS, units), 
                                   self.format)
        elif self.format == 'rst':
            self.snippet = Snippet(eqn2RSTinline(LHS, RHS, units, name), 
                                   self.format)
        else:
            raise NotImplementedError
        return self.snippet
