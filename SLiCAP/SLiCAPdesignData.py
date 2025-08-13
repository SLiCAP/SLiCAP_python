#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 13:24:17 2022

@author: anton
"""

import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import _checkExpression, roundN
from SLiCAP.SLiCAPhtml import _insertHTML, _latex_ENG, units2TeX

class specItem(object):
    """
    Class for specification items. These are parameter definitions with
    descriptions that can be assigned to the circuit.
    Specification items must have:

    - A unique symbol (their parameter name)
    - A spectype defintion, such as 'functional', 'environment', 'design', etc.
    - A value

    """
    def __init__(self, symbol, description='', value='', units='', specType=''):
        """
        Initializes the instance of this class and checks the syntax.

        :param symbol: Parameter name of this specification item
                       (must be unique)
        :type symbol: sympy.Symbol, str

        :param description: Description of this specification item. 
                            Defaults to ''.
        :type description: str

        :param value: Value of this specification item. Defaults to ''.
        :type value: str, int, float, sympy.Expr, sympy.Symbol

        :param units: Units of this specification item
        :type units: str
        
        :param specType: Name of the specification type; free to choose.
                         In reports, specification tables will be displayed for
                         each type.
                         
        """
        self.symbol      = symbol
        self.description = description
        self.value       = value
        self.units       = units
        self.spectype    = specType
        self._update()

    def _update(self):
        """
        Checks the syntax and updates the attributes of this specitem.

        :return: None
        :rtype: NoneType
        """
        self.specType    = str(self.spectype)
        self.symbol      = sp.Symbol(str(self.symbol))
        if self.value != '':
            self.value = _checkExpression(self.value)

    def _csvLine(self):
        """
        Creates a comma separated output line for this spec item. Commas in the
        description are replaced with their html code '&#44;'.

        :return: csv code of this specitem
        :rtype: str
        """
        # symbol
        csv      = str(self.symbol) + ','
        # description
        description = self.description.replace(',', '&#44;')
        csv      += description + ','
        # value
        if self.value != None:
            csv  += str(self.value) + ','
        else:
            csv  += ','
        # units
        if self.units != None:
            csv  += str(self.units) + ','
        else:
            csv  += ','
        # spectype
        csv      += self.specType + '\n'
        return csv

    def _htmlLine(self):
        """
        Creates an html output line for this spec item.

        :return: html code of this specitem
        :rtype: str
        """
        if self.value != '':
            value = _latex_ENG(roundN(self.value))
        else:
            self.value = ''
        # symbol
        html     = '<td class="left">$' + sp.latex(self.symbol) + '$</td>'
        # description
        html     += '<td class="left">' + self.description + '</td>'
        # value
        html += '<td class="left">$' + value + '$</td>' # value
        # units
        if self.units == '':
            html += '<td></td></tr>\n'
        else:
            html += '<td class="left">$\\mathrm{' + units2TeX(self.units) + '}$</td></tr>\n'
        return html

    def _specLine(self):
        """
        Creates an output line for this spec item (used with latex and rst reports)

        :return: list with: symbol, description, value, units
        :rtype: list
        """
        # symbol
        line     = [self.symbol]
        # description
        line.append(self.description)

        # value
        if type(self.value) == str:
            line.append('')
        else:
            line.append(self.value)

        # units
        if self.units== '':
            line.append('')
        else: 
            line.append(self.units)
        return line

def specs2dict(specList):
    """
    Creates a dictionary with spec items. the parameter name is used as key.
    Also checks for unique parameter names.

    :param specList: List with spec items
    :type specList: List

    :return: dictionary with specification items
    :rtype: dict
    """
    specDict = {}
    # Assign ID and update the spec
    for i in range(len(specList)):
        item = specList[i]
        if str(item.symbol) in list(specDict.keys()):
            print("Warning: symbol %s already used, its definition will be overwritten!"%(str(item.symbol)))
        item._update()
        specDict[str(item.symbol)] = item
    return specDict

def specs2csv(specList, fileName):
    """
    Saves the list with spec items as a CSV file.
    
    The file will be stored in the ini.csv_folder, which defaults to the 'csv'
    folder in the project diretory.

    :param specList: List with spec items
    :type specList: list

    :return: None
    :rtype: NoneType

    """
    dictWithSpecs = specs2dict(specList)
    f = open(ini.csv_path + fileName, 'w')
    f.write("symbol, description, value, units, type\n")
    for spec in list(dictWithSpecs.keys()):
        item = dictWithSpecs[spec]
        f.write(item._csvLine())
    f.close()

def csv2specs(csvFile):
    """
    Reads the CSV file with specifications and converts it into a list with
    specitems.
    
    The file will be read from the ini.csv_folder, which defaults to the 'csv'
    folder in the project diretory.

    :param csvFile: name of the CSV file in the directory 'ini.csv_path'
    :type csvFile: str

    :return: Lit with specification items
    :rtype: list
    """
    f = open(ini.csv_path + csvFile)
    lines = f.readlines()
    f.close()
    specList = []
    for i in range(1, len(lines)):
        args = lines[i].strip().split(',')
        newSpecItem = specItem(args[0], args[1], args[2], args[3], args[4])
        newSpecItem.description = newSpecItem.description.replace('&#44;',',')
        specList.append(newSpecItem)
    return specList

def specs2circuit(specList, cir):
    """
    Adds all prameter definitions from the specList to the circuit 'cir'.

    :param specList: List with spec items
    :type specList: list

    :param cir: circuit to which the parameters definitions will be added
    :type cir: SLiCAPprotos.circuit

    :return: None
    :rtype: NoneType
    """
    for item in specList:
        if item.value != '':
            cir.defPar(item.symbol, item.value)

def createSubstDict(specs):
    """
    Returns a subsitutution dictionary from a list with specifications.
    substDict[<parname>] = <parValue>
    
    :param specs: list with specItem objects
    :type specs: list
    
    :return: dictionary with key-value pairs; for each specitem:
             
             - key: parameter name (sympy.Symbol)
             - value: parameter value (sympy.expression)
             
    :rtype: dict
    """
    substDict = {}
    for spec in specs:
        substDict[spec.symbol] = spec.value
    return substDict

def specs2html(specs, types=[]):
    """
    Displays specification items for the list 'specs' on the active HTML
    page. Specifications of the same type are placed in one table.
    
    If a list of specification types is provided, it creates tables
    for specified types only. By default, tables for all types will be created.

    :param specs: List with spec items.
    :type specs:  list

    :param types: List with specification types to be placed on the html page,
                  defaults to [].
    :type types: str

    :return: HTML code that will be placed on the page
    :rtype: str
    """
    dictWithSpecs = specs2dict(specs)
    keys = sorted(list(dictWithSpecs.keys()))
    # Create an HTML dict with a key for each spec type
    html = {}
    for key in keys:
        if dictWithSpecs[key].specType not in list(html.keys()):
            html[dictWithSpecs[key].specType] =  '<h3>' + dictWithSpecs[key].specType + ' specification</h3>\n'
            html[dictWithSpecs[key].specType] += '<table><a id="table_' + dictWithSpecs[key].specType + '"></a><caption>Table ' + dictWithSpecs[key].specType + ' specification </caption>'
            html[dictWithSpecs[key].specType] += '<tr><th class="left">symbol</th><th class="left">description</th><th class="left">value</th><th class="left">units</th></tr>\n'
            html[dictWithSpecs[key].specType] += dictWithSpecs[key]._htmlLine()
        else:
            html[dictWithSpecs[key].specType] += dictWithSpecs[key]._htmlLine()
    txt = ''
    # Copy html code for desired type to output txt
    if len(types):
        for spectype in types:
            try:
                txt += html[spectype] + '</table>\n'
            except BaseException:
                pass
    else:
        # Copy htl code for each type to output txt
        for key in list(html.keys()):
            txt += html[key] + '</table>\n'
    txt = _insertHTML(ini.html_path + ini.html_page, txt)
    return txt