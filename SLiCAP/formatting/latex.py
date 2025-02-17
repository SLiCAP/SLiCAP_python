"""
LaTeX formatter example to discuss the API.
"""

import SLiCAP.SLiCAPlatex as sl
from functools import wraps


# Autosave decorator
def _autosave(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        LaTeXOutput = method(self, *args, **kwargs)
        if self.autosave:
            print(f"Autosave is set. Saving to {self.outputFilename}...")
            self.save(LaTeXOutput)
        return LaTeXOutput
    return wrapper


# TODO: Decide which should be the basic functionality required for all
# formatters.
class BaseFormatter:
    """
    Formatter base class.
    Does not implement functionality, but it should define a minimum
    interface via NotImplementedError that all formatters should support.
    """

    def __init__(self):
        pass

    def save(self, filename):
        raise NotImplementedError

    def _createCSVTable(self, headerList, linesList):
        raise NotImplementedError

    def netlist(self, netlistFilename):
        raise NotImplementedError


class LaTeXFormatter(BaseFormatter):
    """
    LaTeX Formatter, inherited from the base formatter.
    Implements the LaTeX version of the functionality.
    Extra functionality is always allowed.
    """

    def __init__(self, outputFilename="", autosave=False):
        super().__init__()
        if autosave and not outputFilename:
            raise ValueError("To enable autosave a filename must be given.")
        self.outputFilename = outputFilename
        self.autosave = autosave

    def save(self, LaTeXString, filename=None):
        if filename is None:
            if not self.outputFilename:
                raise ValueError("No filename given.")
            with open(sl.ini.tex_path + 'SLiCAPdata/'
                      + self.outputFilename + '.tex', 'a') as f:
                f.write(LaTeXString)
        else:
            sl.saveTEX(LaTeXString, filename)

    @_autosave
    def netlist(self, netlistFile, lineRange=None, firstNumber=None):
        return sl.netlist2TEX(netlistFile, lineRange=None, firstNumber=None)

    @_autosave
    def specs(self, specs, specType, label='', caption=''):
        return sl.specs2TEX(specs, specType, label='', caption='')

    @_autosave
    def elementData(self, circuitObject, label='', append2caption=''):
        return sl.elementData2TEX(circuitObject, label='', append2caption='')

    @_autosave
    def eqn(self, LHS, RHS, units='', label='', multiline=0):
        return sl.eqn2TEX(LHS, RHS, units='', label='', multiline=0)
