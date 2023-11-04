#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with HTML functions.
"""

import sympy as sp
from shutil import copy2
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPmath import roundN, fullSubs
# Initialize HTML globals
ini.htmlIndex    = ''
ini.htmlPrefix   = ''
ini.htmlPage     = ''
ini.htmlLabels   = {}
ini.htmlPages    = []
HTMLINSERT       = '<!-- INSERT -->' # pattern to be replaced in html files
LABELTYPES       = ['headings', 'data', 'fig', 'eqn', 'analysis']

class Label(object):
    """
    Prototype HTML label
    """
    def __init__(self, name, typ, page, text):
        self.name = name
        """
        Label name *(str)*

        Automatically set by HTML functions that have a label as parameter.
        """

        self.type = typ
        """
        Type of label *(str)*

        Automatically set by HTML functions that have a label as parameter.
        Used by **SLiCALhtml.links2html()** for sorting the links. Value can be:
        'headings', 'data', 'fig', 'eqn' or 'analysis'.
        """

        self.page = page
        """
        Name of the page on which the label is placed  *(str)*

        Automatically set by HTML functions that have a label as parameter.
        """

        self.text = text
        """
        Label text  *(str)* to be placed with the label when using links2html.
        If the label is attached to a figure, this text is the figure caption.
        """

        return

def startHTML(projectName):
    """
    Creates main project index page.

    :param: projectName: Name of the project.
    :type projectName: str
    """
    ini.htmlIndex = 'index.html'
    toc = '<h2>Table of contents</h2>'
    html = HTMLhead(projectName) + toc + '<ol>' + HTMLINSERT + '</ol>' + HTMLfoot(ini.htmlIndex)
    f = open(ini.htmlPath + ini.htmlIndex, 'w')
    f.write(html)
    f.close()
    ini.htmlPages.append(ini.htmlIndex)
    return

def HTMLhead(pageTitle):
    """
    Returns the html head for a new html page.

    :param pageTitle: Title of the page
    :type pageTitle: str
    :return: html: Page head for a html page
    :rtype: str
    """
    html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
    html += '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    html += '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n'
    html += '<head><meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>\n'
    html += '<meta name="Language" content="English"/>\n'
    html += '<title>"' + pageTitle + '"</title><link rel="stylesheet" href="css/slicap.css">\n'
    html += '<script>MathJax = {tex:{tags: \'ams\', inlineMath:[[\'$\',\'$\'],]}, svg:{fontCache:\'global\'}};</script>\n'
    html += '<script type="text/javascript" id="MathJax-script" async  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>\n'
    html += '</head><body><div id="top"><h1>' + pageTitle + '</h1></div>\n'
    return(html)

def HTMLfoot(indexFile):
    """
    Returns html page footer with link to 'indexFile'.

    :param indexFile: name of ther hml index file to which a link must be
                      placed in the footer.
    :type indexFile: str
    :return: html: HTML footer with link to 'indexFile'
    :rtype: str
    """
    idx = ini.htmlIndex.split('.')[0]
    html = '\n<div id="footnote">\n'
    html += '<p>Go to <a href="' + ini.htmlIndex + '">' + idx + '</a></p>\n'
    html += '<p>SLiCAP: Symbolic Linear Circuit Analysis Program, Version 2.0.1 &copy 2009-2023 SLiCAP development team</p>\n'
    html += '<p>For documentation, examples, support, updates and courses please visit: <a href="https://analog-electronics.tudelft.nl">analog-electronics.tudelft.nl</a></p>\n'
    html += '<p>Last project update: %s</p>\n'%(ini.lastUpdate.strftime("%Y-%m-%d %H:%M:%S"))
    html += '</div></body></html>'
    return(html)

def insertHTML(fileName, htmlInsert):
    """
    Inserts html in the file specified by 'fileName' at the location of the
    string 'HTMLINSERT'.

    :param fileName: name of the file
    :type fileName: str
    :param htmlInsert: HTML that must be inserted in this file
    :type htmlInsert: str
    """
    html = readFile(fileName)
    html = html.replace(HTMLINSERT, htmlInsert + HTMLINSERT)
    writeFile(fileName, html)
    return

def readFile(fileName):
    """
    Returns the contents of a file as a string.

    :param fileName: Name of the file
    :type fileName: str
    :return: txt: contents of the file.
    :rtype: str
    """
    try:
        f = open(fileName, 'r')
        txt = f.read()
        f.close()
    except:
        print("Error: could note open '{0}'.".format(fileName))
        txt = ''
    return txt

def writeFile(fileName, txt):
    """
    Writes a text string to a file.

    :param fileName: Name of the file
    :type fileName: str
    :param txt: Text to be written to the file.
    :type txt: str
    """
    f = open(fileName, 'w')
    f.write(txt)
    f.close()
    return

### User Functions ###########################################################

def htmlPage(pageTitle, index = False, label = ''):
    """
    Creates an HTML page with the title in the title bar.

    If index==True the page will be used as new index page, else a link to this
    page will be placed on the current index page.

    :param pageTitle:Title of the page.
    :type param: str
    :param index: True or False
    :type index: Bool
    :param label: ID of a labelthat can be assigned to this page.
    :type label: str

    :Example:

    >>> htmlPage('Circuit data')
    """
    if index == True:
        # The page is a  new index page
        fileName = ini.htmlPrefix + 'index.html'
        # Place link on old index page
        href = '<li><a href="' + fileName +'">' + pageTitle + '</a></li>'
        insertHTML(ini.htmlPath + ini.htmlIndex, href)
        # Create the new HTML file
        toc = '<h2>Table of contents</h2>'
        html = HTMLhead(pageTitle) + toc + '<ol>' + HTMLINSERT + '</ol>' + HTMLfoot(ini.htmlIndex)
        writeFile(ini.htmlPath + fileName, html)
        # Make this page the new index page
        ini.htmlIndex = fileName
    else:
        fileName = ini.htmlPrefix + '-'.join(pageTitle.split()) + '.html'
        # Place link on the current index page
        href = '<li><a href="' + fileName +'">' + pageTitle + '</a></li>'
        insertHTML(ini.htmlPath + ini.htmlIndex, href)
        # Create the new HTML page
        if label != None:
            #
            newlabel = Label(label, 'headings', fileName, pageTitle)
            ini.htmlLabels[label] = newlabel
            #
            #ini.htmlLabels[label] = ini.htmlPage
            label = '<a id="' + label + '"></a>'
        html = label + HTMLhead(pageTitle) + HTMLINSERT + HTMLfoot(ini.htmlIndex)
        writeFile(ini.htmlPath + fileName, html)
    # Make this page the active HTML page
    ini.htmlPage = fileName
    ini.htmlPages.append(fileName)
    # Remove double entries in ini.htmlPages
    ini.htmlPages = list(set(ini.htmlPages))
    return

def head2html(headText, label=''):
    """
    Places a level 2 heading on the active HTML page.

    :param headText: header text
    :type headText: str
    :param label: ID of a labelthat can be assigned to this page.
    :type label: str
    :return: HTML string of this header
    :rtype: str


    """
    if label != '':
        #
        newlabel = Label(label, 'headings', ini.htmlPage, headText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    html = '<h2>' + label + headText + '</h2>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def head3html(headText, label=''):
    """
    Places a level 3 heading on the active HTML page.

    :param headText: header text
    :type headText: str
    :param label: ID of a labelthat can be assigned to this page.
    :type label: str
    :return: HTML string of this header
    :rtype: str
    """
    if label != '':
        newlabel = Label(label, 'headings', ini.htmlPage, headText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    html = '<h3>' + label + headText + '</h3>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def text2html(txt):
    """
    Places txt on the active HTML page.
    :param txt: Text to be placed on the HTML page
    :type txt: str
    :return: html: HTML string placed on the page
    :rtype: str
    """
    html = '<p>' + txt + '</p>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def netlist2html(fileName, label=''):
    """
    Places the netlist of the circuit file 'fileName' on the active HTML page.

    :param fileName: Name of the netlist file
    :type fileName: str
    :param label: Label ID for this object.
    :type label: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    try:
        if label != '':
            newlabel = Label(label, 'data', ini.htmlPage, 'Netlist: ' + fileName)
            ini.htmlLabels[label] = newlabel
            label = '<a id="' + label + '"></a>'
        netlist = readFile(ini.circuitPath + fileName)
        html = '<h2>' + label + 'Netlist: ' + fileName + '</h2>\n<pre>' + netlist + '</pre>\n'
        insertHTML(ini.htmlPath + ini.htmlPage, html)
    except:
        print("Error: could not open netlist file: '{0}'.".format(fileName))
        html = ''
    return html


def lib2html(fileName, label=''):
    """
    Places the contents of the library file 'fileName' on the active HTML page.

    :param fileName: Name of the library file
    :type fileName: str
    :param label: Label ID for this object.
    :type label: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    try:
        if label != '':
            newlabel = Label(label, 'data', ini.htmlPage, 'Netlist: ' + fileName)
            ini.htmlLabels[label] = newlabel
            label = '<a id="' + label + '"></a>'
        netlist = readFile(ini.libraryPath + fileName)
        html = '<h2>' + label + 'Library: ' + fileName + '</h2>\n<pre>' + netlist + '</pre>\n'
        insertHTML(ini.htmlPath + ini.htmlPage, html)
    except:
        print("Error: could not open netlist file: '{0}'.".format(fileName))
        html = ''
    return html

def elementData2html(circuitObject, label = '', caption = ''):
    """
    Displays a table with element data on the active html page:

    - refDes
    - nodes
    - referenced elements
    - element parameters with symbolic and numeric values

    :param circuitObject: SLiCAP circuit object of which the element data will
                          be displayed on the HTML page.
    :type circuitObject: *SLiCAPprotos.circuit*
    :param label: Label that will be assigned to this table.
    :type label: str
    :param caption: Caption that will be placed with this table.
    :type caption: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if label != '':
        #
        newlabel = Label(label, 'data', ini.htmlPage, circuitObject.title + ': element data')
        ini.htmlLabels[label] = newlabel
        #
        #ini.htmlLabels[label] = ini.htmlPage
        label = '<a id="' + label + '"></a>'
    caption = "<caption>Table: Element data of expanded netlist '%s'</caption>"%(circuitObject.title)
    html = '%s<table>%s\n'%(label, caption)
    html += '<tr><th class="left">RefDes</th><th class="left">Nodes</th><th class="left">Refs</th><th class="left">Model</th><th class="left">Param</th><th class="left">Symbolic</th><th class="left">Numeric</th></tr>\n'
    elementNames = list(circuitObject.elements.keys())
    elementNames.sort()
    for el in elementNames:
        elmt = circuitObject.elements[el]
        html += '<tr><td class="left">' + elmt.refDes + '</td><td class = "left">'
        for node in elmt.nodes:
            html += node + ' '
        html += '</td><td class = "left">'
        for ref in elmt.refs:
            html += ref + ' '
        html += '</td><td class = "left">' + elmt.model +'</td>\n'
        parNames = list(elmt.params.keys())
        if len(parNames) == 0:
            html += '<td></td><td></td><td></td><tr>'
        else:
            i = 0
            for param in parNames:
                symValue = '$' + sp.latex(roundN(elmt.params[param])) +'$'
                numValue = '$' + sp.latex(roundN(fullSubs(elmt.params[param], circuitObject.parDefs), numeric=True)) + '$'
                if i == 0:
                    html += '<td class="left">' + param + '</td><td class="left">' + symValue + '</td><td class="left">' + numValue + '</td></tr>\n'
                else:
                    html += '<tr><td></td><td></td><td></td><td></td><td class="left">' + param + '</td><td class="left">' + symValue + '</td><td class="left">' + numValue + '</td></tr>\n'
                i += 1
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def params2html(circuitObject, label = '', caption = ''):
    """
    Displays a table with circuit parameters, their definitions and numeric
    values on the actibe htmal page.

    :param circuitObject: SLiCAP circuit object of which the element data will
                          be displayed on the HTML page.
    :type circuitObject: *SLiCAPprotos.circuit*
    :param label: Label that will be assigned to this table.
    :type label: str
    :param caption: Caption that will be placed with this table.
    :type caption: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if label != '':
        newlabel = Label(label, 'data', ini.htmlPage, circuitObject.title + ': circuit parameters')
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    caption = "<caption>Table: Parameter definitions in '%s'.</caption>"%(circuitObject.title)
    html = '%s<table>%s\n'%(label, caption)
    html += '<tr><th class="left">Name</th><th class="left">Symbolic</th><th class="left">Numeric</th></tr>\n'
    parNames = list(circuitObject.parDefs.keys())
    # Sort the list with symbolic keys such that elements are grouped and
    # sorted per sub circuit
    parNames = [str(parNames[i]) for i in range(len(parNames))]
    localPars = []  # list for sub circuit parameters
    globalPars = [] # list for main circuit parameters
    for i in range(len(parNames)):
        par = str(parNames[i]).split('_')
        if par[-1][0].upper() == 'X':
            localPars.append(str(parNames[i]))
        else:
            globalPars.append(str(parNames[i]))
    # Group per sub circuit ignore case
    localPars = sorted(localPars)
    names = sorted(globalPars) + localPars
    parNames = [sp.Symbol(names[i]) for i in range(len(names))]
    for par in parNames:
        parName = '$' + sp.latex(par) + '$'
        try:
            symValue = '$' + sp.latex(roundN(circuitObject.parDefs[par], numeric=False)) + '$'
            numValue = '$' + sp.latex(roundN(fullSubs(circuitObject.parDefs[par], circuitObject.parDefs), numeric=True)) + '$'
            html += '<tr><td class="left">' + parName +'</td><td class="left">' + symValue + '</td><td class="left">' + numValue + '</td></tr>\n'
        except:
            pass
    html += '</table>\n'
    if len(circuitObject.params) > 0:
        caption = "<caption>Table: Parameters without definition in '%s.</caption>\n"%(circuitObject.title)
        html += '<table>%s\n'%(caption)
        html += '<tr><th class="left">Name</th></tr>\n'
        for par in circuitObject.params:
            parName = '$' + sp.latex(par) + '$'
            html += '<tr><td class="left">' + parName +'</td></tr>\n'
        html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def img2html(fileName, width, label = '', caption = ''):
    """
    Places an image from file 'fileName' on the active html page.

    Copies the image file to the 'img.' subdirectory of the 'html/' directory
    and creates a link to this file on the active html page.

    :param fileName: Name of the image file
    :type fileName: str
    :param width: With of the image in pixels
    :type width: int
    :param label: ID of the label to be assigned to this image, defaults to ''.
    :type label: str
    :param caption: Caption for this image; defaults to ''.
    :type caption: str
    :return: file path for this image.
    :rtype: str
    """
    if label != '':
        #
        if caption == '':
            labelText = fileName
        else:
            labelText = caption
        newlabel = Label(label, 'fig', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    try:
        copy2(ini.imgPath + fileName, ini.htmlPath + 'img/' + fileName)
    except:
        print("Error: could not copy: '{0}'.".format(fileName))
    html = '<figure>{0}<img src="img/{1}" alt="{2}" style="width:{3}px">\n'.format(label, fileName, caption, width)
    if caption != '':
        html+='<figcaption>Figure: %s<br>%s</figcaption>\n'%(fileName, caption)
    html += '</figure>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    return '%s'%(ini.htmlPath + 'img/' + fileName)

def csv2html(fileName, label = '', separator = ',', caption = ''):
    """
    Displays the contents of a csv file as a table on the active HTML page.

    :param fileName: Name of the csv file file
    :type fileName: str
    :param label: ID of the label assigned to this table.
    :type label: str
    :param separator: Field separator for this csv file; defaults to ','.
    :type separator: str
    :param caption: Caption for this table.
    :type caption: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if label != '':
        #
        if caption == '':
            labelText = fileName
        else:
            labelText = caption
        newlabel = Label(label, 'data', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    caption = '<caption>Table: %s<br>%s.</caption>'%(fileName, caption)
    html = '%s<table>%s'%(label, caption)
    csvLines = readFile(ini.csvPath + fileName).splitlines()
    for i in range(len(csvLines)):
        cells = csvLines[i].split(separator)
        html += '<tr>'
        if i == 0:
            for cell in cells:
                html += '<th>%s</th>'%(cell)
        else:
            for cell in cells:
                html += '<td>%s</td>'%(cell)
        html += '</tr>\n'
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def expr2html(expr, units = ''):
    """
    Inline display of an expression optional with units.

    :param expr: Expression
    :type expr: sympy.Expr
    :param units: Units for this expression, defaults to ''.
    :type units: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if isinstance(expr, sp.Basic):
        if units != '':
            units = '\\left[\\mathrm{' + sp.latex(sp.sympify(units)) + '}\\right]'
        html = '$' + sp.latex(roundN(expr)) + units + '$'
        insertHTML(ini.htmlPath + ini.htmlPage, html)
    else:
        print("Error: expr2html, expected a Sympy expression.")
        html = ''
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def eqn2html(arg1, arg2, units = '', label = '', labelText = ''):
    """
    Displays an equation on the active HTML page'.

    :param arg1: left hand side of the equation
    :type arg1: str, sympy.Symbol, sympy.Expr
    :param arg2: right hand side of the equation
    :type arg2: str, sympy.Symbol, sympy.Expr
    :param label: ID of the label assigned to this equation; defaults to ''.
    :type label: str
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if arg1 == None or arg2 == None:
        return
    arg1 = sp.sympify(str(arg1))
    arg2 = sp.sympify(str(arg2))
    if units != '':
        units = '\\,\\left[ \\mathrm{' + sp.latex(sp.sympify(units)) + '}\\right]'

    if label != '':
        #
        if labelText == '':
            labelText = label
        newlabel = Label(label, 'eqn', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label   = '<a id="'+ label +'"></a>\n'
    html = label + '\\begin{equation}\n' + sp.latex(roundN(arg1)) + '=' + sp.latex(roundN(arg2)) + units + '\n'
    html += '\\end{equation}\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = ('$$' + html + '$$')
    return html

def matrices2html(instrObj, label = '', labelText = ''):
    """
    Displays the MNA equation on the active HTML page.

    :param instrObj: Results of instruction with data type matrix.
    :type instrObj: SLiCAPprotos.allResults
    :param label: ID of the label assigned to this equation; defaults to ''.
    :type label: str
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    if instrObj.errors != 0:
        print("Errors found during execution.")
        return ''
    html = ''
    try:
        (Iv, M, Dv) = (instrObj.Iv, instrObj.M, instrObj.Dv)
        Iv = sp.latex(roundN(Iv))
        M  = sp.latex(roundN(M))
        Dv = sp.latex(roundN(Dv))
        if label != '':
            #
            if labelText == '':
                labelText = label
            newlabel = Label(label, 'eqn', ini.htmlPage, labelText)
            ini.htmlLabels[label] = newlabel
            label = '<a id="' + label + '"></a>'
        html = '<h3>' + label + 'Matrix equation:</h3>\n'
        html += '\\begin{equation}\n' + Iv + '=' + M + '\\cdot' + Dv + '\n'
        html += '\\end{equation}\n'
        insertHTML(ini.htmlPath + ini.htmlPage, html)
    except:
        print("Error: unexpected input for 'matrices2html()'.")
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def pz2html(instObj, label = '', labelText = ''):
    """
    Displays the DC transfer, and tables with poles and zeros on the active
    HTML page.

    Not (yet) implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'poles', 'zeros' or 'pz'.
    :type instObj: SLiCAP.protos.allResults
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    html = ''
    if instObj.errors != 0:
        print("Errors found in instruction.")
        return html
    elif instObj.dataType != 'poles' and instObj.dataType != 'zeros' and instObj.dataType != 'pz':
        print("Error: 'pz2html()' expected dataType: 'poles', 'zeros', or 'pz', got: '{0}'.".format(instObj.dataType))
        return html
    elif instObj.step == True :
        print("Error: parameter stepping not implemented for 'pz2html()'.")
        return html

    if label != '':
        if labelText == '':
            labelText = label
        newlabel = Label(label, 'analysis', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    (poles, zeros, DCgain) = (instObj.poles, instObj.zeros, instObj.DCvalue)
    if type(DCgain) == list and len(DCgain) != 0:
        DCgain = DCgain[0]
    if instObj.dataType == 'poles':
        headTxt = 'Poles '
    elif instObj.dataType == 'zeros':
        headTxt = 'Zeros '
    elif instObj.dataType == 'pz':
        headTxt = 'PZ '
    html = '<h2>' + label + headTxt + ' analysis results</h2>\n'
    html += '<h3>Gain type: %s</h3>'%(instObj.gainType)
    if DCgain != None and instObj.dataType =='pz':
        if instObj.numeric == True:
            html += '\n' + '<p>DC value = ' + str(sp.N(DCgain, ini.disp)) + '</p>\n'
        else:
            html += '\n<p>DC gain = $' + sp.latex(roundN(DCgain)) + '$</p>\n'
    elif instObj.dataType =='pz':
        html += '<p>DC gain could not be determined.</p>\n'
    if ini.Hz == True and instObj.numeric == True:
        unitsM = 'Mag [Hz]'
        unitsR = 'Re [Hz]'
        unitsI = 'Im [Hz]'
    else:
        unitsM = 'Mag [rad/s]'
        unitsR = 'Re [rad/s]'
        unitsI = 'Im [rad/s]'
    if len(poles) > 0 and instObj.dataType == 'poles' or instObj.dataType == 'pz':
        if instObj.numeric == True:
            html += '<table><tr><th>pole</th><th>' + unitsR + '</th><th>' + unitsI + '</th><th>' + unitsM + '</th><th>Q</th></tr>\n'
            for i in range(len(poles)):
                p = poles[i]
                if ini.Hz == True:
                    p  = p/2/sp.pi
                Re = sp.re(p)
                Im = sp.im(p)
                F  = sp.sqrt(Re**2+Im**2)
                if Im != 0:
                    Q = str(sp.N(F/2/abs(Re), ini.disp))
                else:
                    Q = ''
                F  = str(sp.N(F, ini.disp))
                Re = str(sp.N(Re, ini.disp))
                if Im != 0.:
                    Im = str(sp.N(Im, ini.disp))
                else:
                    Im = ''
                name = 'p<sub>' + str(i + 1) + '</sub>'
                html += '<tr><td>' + name + '</td><td>' + Re + '</td><td>' + Im + '</td><td>' + F + '</td><td>' + Q +'</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<table><tr><th>pole</th><th>value</th></tr>'
            for i in range(len(poles)):
                html += '\n<tr><td> $p_{' +str(i) + '}$</td><td>$' + sp.latex(roundN(poles[i])) + '$</td></tr>\n'
            html += '</table>\n'
    elif instObj.dataType == 'poles' or instObj.dataType == 'pz':
        html += '<p>No poles found.</p>\n'
    if len(zeros) > 0 and instObj.dataType == 'zeros' or instObj.dataType == 'pz':
        if instObj.numeric == True:
            html += '<table><tr><th>zero</th><th>' + unitsR + '</th><th>' + unitsI + '</th><th>' + unitsM + '</th><th>Q</th></tr>\n'
            for i in range(len(zeros)):
                z = zeros[i]
                if ini.Hz == True:
                    z = z/2/sp.pi
                Re = sp.re(z)
                Im = sp.im(z)
                F  = sp.sqrt(Re**2+Im**2)
                if Im != 0:
                    Q = str(sp.N(F/2/abs(Re), ini.disp))
                else:
                    Q = ''
                F  = str(sp.N(F, ini.disp))
                Re = str(sp.N(Re, ini.disp))
                if Im != 0.:
                    Im = str(sp.N(Im, ini.disp))
                else:
                    Im = ''
                name = 'z<sub>' + str(i + 1) + '</sub>'
                html += '<tr><td>' + name + '</td><td>' + Re + '</td><td>' + Im + '</td><td>' + F + '</td><td>' + Q +'</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<table><tr><th>zero</th><th>value</th></tr>'
            for i in range(len(zeros)):
                html += '\n<tr><td> $z_{' +str(i) + '}$</td><td>$' + sp.latex(roundN(zeros[i])) + '$</td></tr>\n'
            html += '</table>\n'
    elif instObj.dataType == 'zeros' or instObj.dataType == 'pz':
        html += '<p>No zeros found.</p>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    return html

def noise2html(instObj, label = '', labelText = ''):
    """
    Displays the reults of a noise analysis on the active html page.

    Not implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'noise'.
    :type instObj: SLiCAP.protos.allResults
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    html = ''
    if instObj.errors != 0:
        print("Errors found in instruction.")
        return html
    elif instObj.dataType != 'noise':
        print("Error: 'noise2html()' expected dataType: 'noise', got: '{0}'.".format(instObj.dataType))
        return html
    elif instObj.step == True :
        print("Error: parameter stepping not implemented for 'noise2html()'.")
        return html
    if label != '':
        if labelText == '':
            labelText = label
        newlabel = Label(label, 'analysis', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    detUnits = '\mathrm{\left[\\frac{%s^2}{Hz}\\right]}'%(instObj.detUnits)
    if instObj.simType == 'symbolic':
        html = '<h2>Symbolic noise analysis results</h2>\n'
        numeric = False
    else:
        html = '<h2>Numeric noise analysis results</h2>\n'
        numeric = True
    html += '<h3>Detector-referred noise spectrum</h3>\n'
    html += '$$S_{out}=%s\, %s$$\n'%(sp.latex(roundN(instObj.onoise, numeric = instObj.numeric)), detUnits)
    if instObj.srcUnits != None:
        srcUnits = '\mathrm{\left[\\frac{%s^2}{Hz}\\right]}'%(instObj.srcUnits)
        html += '<h3>Source-referred noise spectrum</h3>\n'
        html += '$$S_{in}=%s\, %s$$\n'%(sp.latex(roundN(instObj.inoise, numeric = instObj.numeric)), srcUnits)
    html += '<h3>Contributions of individual noise sources</h3><table>\n'
    keys = list(instObj.onoiseTerms.keys())
    keys.sort()
    for key in keys:
        nUnits = key[0].upper()
        if nUnits == 'I':
            nUnits = 'A'
        nUnits = '\mathrm{\left[\\frac{%s^2}{Hz}\\right]}'%(nUnits)
        html += '<th colspan = "3" class="center">Noise source: %s</th>'%(key)
        try:
            srcValue = instObj.snoiseTerms[key]
        except:
            srcValue = 0
        if numeric:
            srcValue = fullSubs(srcValue, instObj.circuit.parDefs)
        html += '<tr><td class="title">Spectral density:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(srcValue, numeric = instObj.numeric)), nUnits)
        html += '<tr><td class="title">Detector-referred:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.onoiseTerms[key], numeric = instObj.numeric)), detUnits)
        if instObj.srcUnits != None:
            html += '<tr><td class="title">Source-referred:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.inoiseTerms[key], numeric = instObj.numeric)), srcUnits)
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
        html = html.replace('$$$$', '$$')
    return html

def dcVar2html(instObj, label = '', labelText = ''):
    """
    Displays the reults of a dcVAr analysis on the active html page.

    Not implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'dcvar'.
    :type instObj: SLiCAP.protos.allResults
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    html = ''
    if instObj.errors != 0:
        print("Errors found in instruction.")
        return html
    elif instObj.dataType != 'dcvar':
        print("Error: 'dcvar2html()' expected dataType: 'dcvar', got: '{0}'.".format(instObj.dataType))
        return html
    elif instObj.step == True :
        print("Error: parameter stepping not implemented for 'dcvar2html()'.")
        return html
    if label != '':
        if labelText == '':
            labelText = label
        newlabel = Label(label, 'dcvar', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    detUnits = '\mathrm{\left[ %s^2 \\right]}'%(instObj.detUnits)
    if instObj.simType == 'symbolic':
        html = '<h2>Symbolic dcvar analysis results</h2>\n'
        numeric = False
    else:
        html = '<h2>Numeric dcvar analysis results</h2>\n'
        numeric = True
    html += '<h3>DC solution of the network</h3>\n'
    html += '$$%s=%s$$\n'%(sp.latex(roundN(instObj.Dv)), sp.latex(roundN(instObj.dcSolve, numeric = instObj.numeric)))
    html += '<h3>Detector-referred variance</h3>\n'
    html += '$$\sigma_{out}^2=%s\, %s$$\n'%(sp.latex(roundN(instObj.ovar, numeric = instObj.numeric)), detUnits)
    if instObj.srcUnits != None:
        srcUnits = '\mathrm{\left[\\frac{%s^2}{Hz}\\right]}'%(instObj.srcUnits)
        html += '<h3>Source-referred variance</h3>\n'
        html += '$$\sigma_{in}^2=%s\, %s$$\n'%(sp.latex(roundN(instObj.ivar, numeric = instObj.numeric)), srcUnits)
    html += '<h3>Contributions of individual component variances</h3><table>\n'
    keys = list(instObj.ovarTerms.keys())
    keys.sort()
    for key in keys:
        nUnits = key[0].upper()
        if nUnits == 'I':
            nUnits = 'A'
        nUnits = '\mathrm{\left[ %s^2 \\right]}'%(nUnits)
        html += '<th colspan = "3" class="center">Variance of source: %s</th>'%(key)
        try:
            srcValue = instObj.svarTerms[key]
        except:
            srcValue = 0
        if numeric:
            srcValue = fullSubs(srcValue, instObj.parDefs)
        html += '<tr><td class="title">Source variance:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(srcValue, numeric = instObj.numeric)), nUnits)
        html += '<tr><td class="title">Detector-referred:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.ovarTerms[key], numeric = instObj.numeric)), detUnits)
        if instObj.srcUnits != None:
            html += '<tr><td class="title">Source-referred:</td><td>$%s$</td><td class="units">$\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.ivarTerms[key], numeric = instObj.numeric)), srcUnits)
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
        html = html.replace('$$$$', '$$')
    return html

def coeffsTransfer2html(transferCoeffs, label = '', labelText = ''):
    """
    Displays the coefficients of the numerator and the denominator of a transfer function on the active html page.
    """
    if label != '':
        if labelText == '':
            labelText = label
        newlabel = Label(label, 'analysis', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    (gain, numerCoeffs, denomCoeffs) = transferCoeffs
    html = '<h3>Gain factor</h3>\n<p>$%s$</p>\n'%(sp.latex(roundN(gain)))
    html += '<h3>Normalized coefficients of the numerator:</h3>\n<table><tr><th class=\"center\">order</th><th class=\"left\">coefficient</th></tr>\n'
    for i in range(len(numerCoeffs)):
        value = sp.latex(roundN(numerCoeffs[i]))
        html += '<tr><td class=\"center\">$' + str(i) + '$</td><td class=\"left\">$' + value + '$</td></tr>\n'
    html += '</table>\n'
    html += '<h3>Normalized coefficients of the denominator:</h3>\n<table><tr><th class=\"center\">order</th><th class=\"left\">coefficient</th></tr>\n'
    for i in range(len(denomCoeffs)):
        value = sp.latex(roundN(denomCoeffs[i]))
        html += '<tr><td class=\"center\">$' + str(i) + '$</td><td class=\"left\">$' + value + '$</td></tr>\n'
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    if ini.notebook:
        html = html.replace('$', '$$')
    return html

def stepArray2html(stepVars, stepArray):
    """
    Displays the step array on the active HTML page.

    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    numVars = len(stepVars)
    numRuns = len(stepArray[0])
    html = '<h3>Step array</h3>\n<table><tr><th>Run</th>'
    for i in range(numVars):
        html += '<th>$%s$</th>'%(sp.latex(stepVars[i]))
    html += '</tr>\n'
    for i in range(numRuns):
        html += '<tr><td>%s</td>'%(i+1)
        for j in range(numVars):
            html += '<td>%8.2e</td>'%(stepArray[j][i])
        html += '</tr>\n'
    html += '</table>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    return html

def fig2html(figureObject, width, label = '', caption = ''):
    """
    Copies the image file to the 'img.' subdirectory of the 'html/' directory
    set by HTMLPATH in SLiCAPini.py and creates a link to this file on the
    active html page.
    """
    if label != '':
        if caption == '':
            labelText = figureObject.fileName
        else:
            labelText = caption
        newlabel = Label(label, 'fig', ini.htmlPage, labelText)
        ini.htmlLabels[label] = newlabel
        label = '<a id="' + label + '"></a>'
    html = '<figure>%s<img src="img/%s" alt="%s" style="width:%spx">\n'%(label, figureObject.fileName, caption, width)
    if caption != '':
        html+='<figcaption>Figure: %s<br>%s</figcaption>\n'%(figureObject.fileName, caption)
    html += '</figure>\n'
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    try:
        copy2(ini.imgPath + figureObject.fileName, ini.htmlPath + 'img/' + figureObject.fileName)
    except:
        print("Error: could not copy: '{0}'.".format(ini.imgPath + figureObject.fileName))
    return ini.htmlPath + 'img/' + figureObject.fileName

def file2html(fileName):
    """
    Writes the contents of a file to the active html page.

    :param fileName: Name of the file (relative to ini.textPath)
    :type fileName: str
    :return: html code
    :rtype: str
    """
    f = open(ini.txtPath + fileName)
    html = f.read()
    f.close()
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    return html

### HTML links and labels

def href(label, fileName = ''):
    """
    Returns the html code for a jump to a label 'labelName'.
    This label can be on any page. If referring backwards 'fileName' can be
    detected automatically. When referring forward 'fileName' must be the
    name of the file that will be created later. Run a project 2 times without
    closing it after the first run, automaitcally detects all labels.
    """
    html = ''
    if fileName == '':
        fileName = ini.htmlLabels[label].page
    if fileName == ini.htmlPage:
        html = '<a href="#' + label + '">' + ini.htmlLabels[label].text + '</a>'
    else:
        html = '<a href="' + fileName + '#' + label + '">' + ini.htmlLabels[label].text + '</a>'
    return html

def links2html():
    """
    Returns the HTML code for placing links to all labeled HTML objects.

    Links will be grouped as follows:

    #. Links to headings
    #. Links to circuit data and imported tables
    #. Links to figures
    #. Links to equations
    #. Links to analysis results (from noise2html, pz2html, etc.)

    :return: html: HTML string that will be placed on the page.
    :rtype: str
    """
    htmlPage('Links')
    labelDict = {}
    html = ''
    for labelType in LABELTYPES:
        labelDict[labelType] = []
    for labelName in list(ini.htmlLabels.keys()):
        labelDict[ini.htmlLabels[labelName].type].append(labelName)
    for labelType in LABELTYPES:
        if len(labelDict[labelType]) != 0:
            labelDict[labelType].sort()
            if labelType == 'headings':
                html += '<h2>Pages and sections</h2>\n'
                for name in labelDict[labelType]:
                    html += '<p>%s</p>'%(href(name))
            elif labelType == 'data':
                html += '<h2>Circuit data and imported tables</h2>\n'
                for name in labelDict[labelType]:
                    html += '<p>%s</p>\n'%(href(name))
            elif labelType == 'fig':
                html += '<h2>Figures</h2>\n'
                for name in labelDict[labelType]:
                    html += '<p>%s</p>\n'%(href(name))
            elif labelType == 'eqn':
                html += '<h2>Equations</h2>\n'
                for name in labelDict[labelType]:
                    html += '<p>%s</p>\n'%(href(name))
            elif labelType == 'analysis':
                html += '<h2>Analysis results</h2>\n'
                for name in labelDict[labelType]:
                    html += '<p>%s</p>\n'%(href(name))
    insertHTML(ini.htmlPath + ini.htmlPage, html)
    return

def htmlLink(address, text):
    """
    Returns the html code for placing a link on an html page with *text2html()*.

    :param address: link address
    :type address: str

    :return: html code
    :rtype: str
    """
    html = '<a href="' + address + '">' + text + '</a>\n'
    return html

def htmlParValue(instr, parName):
    """
    Returns code for inline display of parameter 'parName' from instruction
    'instr'. If instr.simType == 'numeric' it applies a full substitution of
    all other parameter definitions.

    :param instr: Instruction that holds the parameter definition
    :type instr: SLiCAPinstruction.instruction

    :param parName: Name of the parameter
    :type parName: string

    :return: html code for the parameter value
    :rtype: string
    """
    return '$' + str(sp.latex(roundN(instr.getParValue(parName)))) + '$'

def htmlElValue(instr, elName):
    """
    Returns code for inline display of value of element 'elName' from instruction
    'instr'. If instr.simType == 'numeric' it applies a full substitution of
    all other parameter definitions.

    :param instr: Instruction that holds the parameter definition
    :type instr: SLiCAPinstruction.instruction

    :param elName: Element identifier
    :type elName: string

    :return: html code for the element value
    :rtype: string
    """
    return '$' + str(sp.latex(roundN(instr.getElementValue(elName)))) + '$'
