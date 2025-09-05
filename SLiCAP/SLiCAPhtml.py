#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with functions for creating a basic HTML report.
"""

import sympy as sp
import SLiCAP.SLiCAPconfigure as ini
from shutil import copy2
from SLiCAP.SLiCAPmath import roundN, fullSubs, _checkNumeric, ENG, units2TeX
from IPython.core.display import HTML

_HTMLINSERT = '<!-- INSERT -->' # pattern to be replaced in html files
_LABELTYPES = ['heading', 'data', 'fig', 'eqn', 'analysis']

def _Label(name, typ, page, text):
    return [typ, page, '"' + text + '"']

def _addLabel(label, fileName='', caption='', labelType=''):
    if label != '':
        #
        if caption == '':
            labelText = fileName
        else:
            labelText = caption
        ini.html_labels[label] = _Label(label, labelType, ini.html_page, labelText)
        label = '<a id="' + label + '"></a>'
    return label

def _latex_ENG(num):
    if ini.scalefactors or ini.eng_notation:
        num, exp = ENG(num, scaleFactors=ini.scalefactors)
        num = roundN(num)
        if exp != None:
            if ini.scalefactors:
                num = str(num) + '\\, \\mathrm{' + str(exp) + '}'
            else:
                num = str(num) + '\\cdot 10^{' + str(exp) + '}'
        else:
            num = sp.latex(num)
    else:
        num = sp.latex(roundN(num))
    return num

def printHTMLinfo():
    """
    Prints current HTML pages and labels to stdout
    
    :return: None
    :rtype: NoneType
    """
    print("Current page       :", ini.html_page)
    print("Current index page :", ini.html_index)
    print("Available pages    :")
    for page in ini.html_pages:
        print("  ", page)
    print("Labels             :")
    for key in ini.html_labels.keys():
        print("  " + key +";")
        print("    type:", ini.html_labels[key][0])
        print("    page:", ini.html_labels[key][1])
        print("    text:", ini.html_labels[key][2])

def _startHTML(projectName):
    """
    Creates main project index page.

    :param: projectName: Name of the project.
    :type projectName: str
    
    :return: None
    :rtype: NoneType
    """
    toc = '<h2>Table of contents</h2>'
    html = _HTMLhead(projectName) + toc + '<ol>' + _HTMLINSERT + '</ol>' + _HTMLfoot(ini.html_index)
    _writeFile(ini.html_path + ini.html_index, html)
    ini.html_page = ini.html_index
    ini.html_pages.append(ini.html_page)
    return

def _HTMLhead(pageTitle):
    """
    Returns the html head for a new html page.

    :param pageTitle: Title of the page
    :type pageTitle: str
    
    :return: Page head for a html page
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
    return html

def _HTMLfoot(indexFile):
    """
    Returns html page footer with link to 'indexFile'.

    :param indexFile: name of ther hml index file to which a link must be
                      placed in the footer.
    :type indexFile: str
    
    :return: html: HTML footer with link to 'indexFile'
    :rtype: str
    """
    idx = ini.html_index.split('.')[0]
    html = '\n<div id="footnote">\n'
    html += '<p>Go to <a href="' +  ini.html_index + '">' + idx + '</a></p>\n'
    html += '<p>SLiCAP: Symbolic Linear Circuit Analysis Program, Version %s &copy 2009-2025 SLiCAP development team</p>\n'%(ini.INSTALLVERSION)
    html += '<p>For documentation, examples, support, updates and courses please visit: <a href="https://analog-electronics.tudelft.nl">analog-electronics.tudelft.nl</a></p>\n'
    html += '<p>Last project update: %s</p>\n'%(ini.last_updated)
    html += '</div></body></html>'
    return html

def _insertHTML(fileName, htmlInsert):
    """
    Inserts html in the file specified by 'fileName' at the location of the
    string 'htmlInsert'.

    :param fileName: name of the file
    :type fileName: str
    
    :param htmlInsert: HTML that must be inserted in this file
    :type htmlInsert: str
    """
    if ini.notebook:
        htmlInsert = HTML(htmlInsert)
    else:
        html = _readFile(fileName)
        html = html.replace(_HTMLINSERT, htmlInsert + _HTMLINSERT)
        _writeFile(fileName, html)
    return htmlInsert

def _readFile(fileName):
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

def _writeFile(fileName, txt):
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
    # Update project configuration file. In this way the HTML info is preserved
    # with next import of SLiCAP in the same project; it is only reset with
    # initProject()
    ini._update_project_config()
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
    
    :param label: ID of a label to be assigned to this page.
    :type label: str

    :return: None
    :rtype: NoneType
    
    """   
    if not ini.notebook:
        if index == True:
            # The page is a  new index page
            fileName = ini.html_prefix + 'index.html'
            # Place link on old index page
            href = '<li><a href="' + fileName +'">' + pageTitle + '</a></li>'
            _insertHTML(ini.html_path + ini.html_index, href)
            # Create the new HTML file
            toc = '<h2>Table of contents</h2>'
            html = _HTMLhead(pageTitle) + toc + '<ol>' + _HTMLINSERT + '</ol>' + _HTMLfoot(ini.html_index)
            _writeFile(ini.html_path + fileName, html)
            # Make this page the new index page
            ini.html_index = fileName
        else:
            fileName = ini.html_prefix + '-'.join(pageTitle.split()) + '.html'
            # Place link on the current index page
            href = '<li><a href="' + fileName +'">' + pageTitle + '</a></li>'
            _insertHTML(ini.html_path + ini.html_index, href)
            # Create the new HTML page
            if label != "":
                ini.html_labels[label] = _Label(label, 'heading', fileName, pageTitle)
                label = '<a id="' + label + '"></a>'
            html = label + _HTMLhead(pageTitle) + _HTMLINSERT + _HTMLfoot(ini.html_index)
            _writeFile(ini.html_path + fileName, html)
        # Make this page the active HTML page
        ini.html_page = fileName
        ini.html_pages.append(fileName)
    return

def head2html(headText, label=''):
    """
    Places a level 2 header on the active HTML page.

    :param headText: header text
    :type headText: str
    
    :param label: ID of a labelt to be assigned to this header.
    :type label: str
    
    :return: HTML string of this header
    :rtype: str

    """
    label = _addLabel(label, labelType="heading")
    html = '<h2>' + label + headText + '</h2>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def head3html(headText, label=''):
    """
    Places a level 3 header on the active HTML page.

    :param headText: header text
    :type headText: str
    
    :param label: ID of a labelt to be assigned to this header.
    :type label: str
    
    :return: HTML string of this header
    :rtype: str
    """
    label = _addLabel(label, labelType="heading")
    html = '<h3>' + label + headText + '</h3>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def text2html(txt):
    """
    Places txt on the active HTML page.
    
    :param txt: Text to be placed on the HTML page
    :type txt: str
    
    :return: HTML string placed on the page: "<p>" + txt + "</p>\\n""
    :rtype: str
    """
    html = '<p>' + txt + '</p>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def netlist2html(fileName, label='', labelText =''):
    """
    Places the netlist of the circuit file 'fileName' on the active HTML page.
    The file must be located in the ini.cir_path folder.
    
    :param fileName: Name of the netlist file
    :type fileName: str
    
    :param label: Label ID for this object.
    :type label: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    try:
        label = _addLabel(label, fileName=fileName, caption=labelText, labelType="data")
        netlist = _readFile(ini.cir_path + fileName)
        html = '<h2>' + label + 'Netlist: ' + fileName + '</h2>\n<pre>' + netlist + '</pre>\n'
        html = _insertHTML(ini.html_path + ini.html_page, html)
    except:
        print("Error: could not open netlist file: '{0}'.".format(fileName))
        html = ''
    return html


def lib2html(fileName, label='', lib='user'):
    """
    Places the contents of the library file 'fileName' on the active HTML page.
    
    The library is assumed to be located in the user library path.

    :param fileName: Name of the library file
    :type fileName: str
    
    :param label: Label ID for this object.
    :type label: str
    
    :param lib: Library path, can either be "user", or "system".
    :type lib: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    lib = lib.lower()
    try:
        label = _addLabel(label, fileName=fileName, labelType="data")
        if lib == 'user':
            netlist = _readFile(ini.user_lib_path + fileName)
        elif lib == 'system':
            netlist = _readFile(ini.main_lib_path + fileName)
        else:
            print("ERROR: unknown library type (lib='user' or 'system').")
        html = '<h2>' + label + 'Library: ' + fileName + '</h2>\n<pre>' + netlist + '</pre>\n'
        html = _insertHTML(ini.html_path + ini.html_page, html)
    except:
        print("Error: could not open netlist file: '{0}'.".format(fileName))
        html = ''
    return html

def elementData2html(circuitObject, label='', caption=''):
    """
    Displays a table with element data on the active html page:

    - refDes
    - nodes
    - referenced elements
    - element parameters with symbolic and numeric values

    :param circuitObject: SLiCAP circuit object of which the element data will
                          be displayed on the HTML page.
                          
    :type circuitObject: SLiCAPprotos.circuit
    
    :param label: Label that will be assigned to this table.
    :type label: str
    
    :param caption: Caption that will be placed with this table.
    :type caption: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    label = _addLabel(label, fileName='', caption=caption, labelType="data")
    if caption == '':
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
                symValue = '$' + _latex_ENG(elmt.params[param]) + '$'
                #symValue ='$' + sp.latex(roundN(elmt.params[param])) +'$'
                numValue = '$' + _latex_ENG(sp.N(fullSubs(elmt.params[param], circuitObject.parDefs))) + '$'
                #numValue = '$' + sp.latex(roundN(fullSubs(elmt.params[param], circuitObject.parDefs), numeric=True)) + '$'
                if i == 0:
                    html += '<td class="left">' + param + '</td><td class="left">' + symValue + '</td><td class="left">' + numValue + '</td></tr>\n'
                else:
                    html += '<tr><td></td><td></td><td></td><td></td><td class="left">' + param + '</td><td class="left">' + symValue + '</td><td class="left">' + numValue + '</td></tr>\n'
                i += 1
    html += '</table>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def params2html(circuitObject, label='', caption=''):
    """
    Displays a table with circuit parameters, their definitions and numeric
    values on the actibe htmal page.

    :param circuitObject: SLiCAP circuit object of which the element data will
                          be displayed on the HTML page.
                          
    :type circuitObject: SLiCAPprotos.circuit
    :param label: Label that will be assigned to this table.
    :type label: str
    
    :param caption: Caption that will be placed with this table.
    :type caption: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    label = _addLabel(label, fileName='', caption=caption, labelType='data')
    if caption == '':
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
            symValue = '$' + _latex_ENG(circuitObject.parDefs[par]) + '$'
            #ymValue = '$' + sp.latex(roundN(circuitObject.parDefs[par], numeric=False)) + '$'
            numValue = '$' + _latex_ENG(sp.N(fullSubs(circuitObject.parDefs[par], circuitObject.parDefs))) + '$'
            #numValue = '$' + sp.latex(roundN(fullSubs(circuitObject.parDefs[par], circuitObject.parDefs), numeric=True)) + '$'
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
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def img2html(fileName, width, label='', caption=''):
    """
    Places an image from file 'fileName' on the active html page.

    Copies the image file to the 'img.' subdirectory of the 'html/' directory
    and creates a link to this file on the active html page.

    :param fileName: Name of the image file, must be located in the 
                     ini.img_path folder.
                     
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
    label = _addLabel(label, fileName=fileName, caption=caption, labelType="fig")
    try:
        copy2(ini.img_path + fileName, ini.html_path + 'img/' + fileName)
    except:
        print("Warning: could not copy: '{0}'.".format(fileName))
    html = '<figure>{0}<img src="img/{1}" alt="{2}" style="width:{3}px">\n'.format(label, fileName, caption, width)
    if caption != '':
        html+='<figcaption>Figure: %s<br>%s</figcaption>\n'%(fileName, caption)
    html += '</figure>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def csv2html(fileName, label='', separator=',', caption=''):
    """
    Displays the contents of a csv file as a table on the active HTML page.
    The file must be located in the ini.csv_path folder.

    :param fileName: Name of the csv file file
    :type fileName: str
    
    :param label: ID of the label assigned to this table.
    :type label: str
    
    :param separator: Field separator for this csv file; defaults to ','.
    :type separator: str
    
    :param caption: Caption for this table.
    :type caption: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    label = _addLabel(label, fileName=fileName, caption=caption, labelType="data")
    caption = '<caption>Table: %s<br>%s.</caption>'%(fileName, caption)
    html = '%s<table>%s'%(label, caption)
    csvLines = _readFile(ini.csv_path + fileName).splitlines()
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
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def expr2html(expr, units=''):
    """
    Inline display of an expression optional with units.

    :param expr: Expression
    :type expr: sympy.Expr
    
    :param units: Units for this expression, defaults to ''.
    :type units: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    if isinstance(expr, sp.Basic):
        if units != '':
            units = '\\left[\\mathrm{' + units2TeX(units) + '}\\right]'
        html = '$' + _latex_ENG(expr) + units + '$'
        #html = '$' + sp.latex(roundN(expr)) + units + '$'
        html = _insertHTML(ini.html_path + ini.html_page, html)
    else:
        print("Error: expr2html, expected a Sympy expression.")
        html = ''
    return html

def eqn2html(arg1, arg2, units='', label='', labelText=''):
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
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    if arg1 == None or arg2 == None:
        return
    arg1 = sp.sympify(str(arg1))
    arg2 = sp.sympify(str(arg2))
    if units != '':
        units = '\\,\\left[ \\mathrm{' + units2TeX(units) + '}\\right]'
    label = _addLabel(label, caption=labelText, labelType='eqn')
    value = _latex_ENG(arg2)
    #value =  sp.latex(roundN(arg2))    
    html = label + '\\begin{equation}\n' + sp.latex(roundN(arg1)) + '=' + value + units + '\n'
    html += '\\end{equation}\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def matrices2html(results, label='', labelText=''):
    """
    Displays the MNA equation on the active HTML page.

    :param instrObj: Results of instruction with data type matrix.
    :type instrObj: SLiCAPprotos.allResults
    
    :param label: ID of the label assigned to this equation; defaults to ''.
    :type label: str
    
    :param labelText: Label text displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    if results.errors != 0:
        print("Errors found during execution.")
        return ''
    html = ''
    try:
        (Iv, M, Dv) = (results.Iv, results.M, results.Dv)
        Iv = sp.latex(roundN(Iv))
        M  = sp.latex(roundN(M))
        Dv = sp.latex(roundN(Dv))
        label = _addLabel(label, caption=labelText, labelType='eqn')
        html = '<h3>' + label + 'Matrix equation:</h3>\n'
        html += '\\begin{equation}\n' + Iv + '=' + M + '\\cdot' + Dv + '\n'
        html += '\\end{equation}\n'
        html = _insertHTML(ini.html_path + ini.html_page, html)
    except:
        print("Error: unexpected input for 'matrices2html()'.")
    return html

def pz2html(instObj, label = '', labelText = ''):
    """
    Displays the DC transfer, and tables with poles and zeros on the active
    HTML page.

    Not implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'poles', 'zeros' or 'pz'.
    :type instObj: SLiCAP.protos.allResults
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
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
    label = _addLabel(label, caption=labelText, labelType="data")
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
            html += '\n' + '<p>DC value = $' + sp.latex(roundN(sp.N(DCgain))) + '$</p>\n'
        else:
            html += '\n<p>DC gain = $' + sp.latex(roundN(DCgain)) + '$</p>\n'
    elif instObj.dataType =='pz':
        html += '<p>DC gain could not be determined.</p>\n'
    if ini.hz == True:
        unitsM = 'Mag [Hz]'
        unitsR = 'Re [Hz]'
        unitsI = 'Im [Hz]'
        unitsS = '[Hz]'
    else:
        unitsM = 'Mag [rad/s]'
        unitsR = 'Re [rad/s]'
        unitsI = 'Im [rad/s]'
        unitsS = '[rad/s]'
    if len(poles) > 0 and instObj.dataType == 'poles' or instObj.dataType == 'pz':
        if _checkNumeric(poles):
            html += '<table><tr><th>pole</th><th>' + unitsR + '</th><th>' + unitsI + '</th><th>' + unitsM + '</th><th>Q</th></tr>\n'
            for i in range(len(poles)):
                if ini.hz:
                    root  = sp.N(poles[i]/2/sp.pi)
                else:
                    root  = sp.N(poles[i])
                realpart  = sp.re(root)
                imagpart  = sp.im(root)
                frequency = sp.Abs(root)
                Q         = frequency/(2*sp.Abs(realpart))
                if imagpart != 0:
                    Q        = "$" + _latex_ENG(sp.N(frequency/2/abs(realpart), ini.disp)) + "$"
                    imagpart = "$" + _latex_ENG(sp.N(imagpart, ini.disp)) + "$"
                else:
                    Q        = ''
                    imagpart = ''
                frequency  = "$" + _latex_ENG(sp.N(frequency, ini.disp)) + "$"
                realpart   = "$" + _latex_ENG(sp.N(realpart, ini.disp)) + "$"
                name = 'p<sub>' + str(i + 1) + '</sub>'
                html += '<tr><td>' + name + '</td><td>' + realpart + '</td><td>' + imagpart + '</td><td>' + frequency + '</td><td>' + Q +'</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<table><tr><th>pole</th><th>value ' + unitsS + '</th></tr>'
            for i in range(len(poles)):
                p = poles[i]
                if ini.hz == True:
                    p  = p/2/sp.pi
                html += '\n<tr><td> $p_{' +str(i) + '}$</td><td>$' + sp.latex(roundN(p)) + '$</td></tr>\n'
            html += '</table>\n'
    elif instObj.dataType == 'poles' or instObj.dataType == 'pz':
        html += '<p>No poles found.</p>\n'
    if len(zeros) > 0 and instObj.dataType == 'zeros' or instObj.dataType == 'pz':
        if _checkNumeric(zeros):
            html += '<table><tr><th>zero</th><th>' + unitsR + '</th><th>' + unitsI + '</th><th>' + unitsM + '</th><th>Q</th></tr>\n'
            for i in range(len(zeros)):
                if ini.hz:
                    root  = sp.N(zeros[i]/2/sp.pi)
                else:
                    root  = sp.N(zeros[i])
                realpart  = sp.re(root)
                imagpart  = sp.im(root)
                frequency = sp.Abs(root)
                Q         = frequency/(2*sp.Abs(realpart))
                if imagpart != 0:
                    Q        = "$" + _latex_ENG(sp.N(frequency/2/abs(realpart), ini.disp)) + "$"
                    imagpart = "$" + _latex_ENG(sp.N(imagpart, ini.disp)) + "$"
                else:
                    Q        = ''
                    imagpart = ''
                frequency  = "$" + _latex_ENG(sp.N(frequency, ini.disp)) + "$"
                realpart   = "$" + _latex_ENG(sp.N(realpart, ini.disp)) + "$"
                name = 'p<sub>' + str(i + 1) + '</sub>'
                html += '<tr><td>' + name + '</td><td>' + realpart + '</td><td>' + imagpart + '</td><td>' + frequency + '</td><td>' + Q +'</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<table><tr><th>zero</th><th>value ' + unitsS + '</th></tr>'
            for i in range(len(zeros)):
                z = zeros[i]
                if ini.hz == True:
                    z = sp.simplify(z/2/sp.pi)
                html += '\n<tr><td> $z_{' +str(i) + '}$</td><td>$' + sp.latex(roundN(z)) + '$</td></tr>\n'
            html += '</table>\n'
    elif instObj.dataType == 'zeros' or instObj.dataType == 'pz':
        html += '<p>No zeros found.</p>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def noise2html(instObj, label='', labelText=''):
    """
    Displays the reults of a noise analysis on the active html page.

    Not implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'noise'.
    :type instObj: SLiCAP.protos.allResults
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
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
        label = _addLabel(label, caption=labelText, labeType="data")
    detUnits = '\\mathrm{\\left[\\frac{%s^2}{Hz}\\right]}'%(instObj.detUnits)
    html = '<h2>Noise analysis results</h2>\n'
    html += '<h3>Detector-referred noise spectrum</h3>\n'
    html += '$$S_{out}=%s\\, %s$$\n'%(sp.latex(roundN(instObj.onoise, numeric = instObj.numeric)), detUnits)
    if instObj.srcUnits != None:
        srcUnits = '\\mathrm{\\left[\\frac{%s^2}{Hz}\\right]}'%(instObj.srcUnits)
        html += '<h3>Source-referred noise spectrum</h3>\n'
        html += '$$S_{in}=%s\\, %s$$\n'%(sp.latex(roundN(instObj.inoise, numeric = instObj.numeric)), srcUnits)
    html += '<h3>Contributions of individual noise sources</h3><table>\n'
    keys = list(instObj.onoiseTerms.keys())
    keys.sort()
    for key in keys:
        nUnits = key[0].upper()
        if nUnits == 'I':
            nUnits = 'A'
        nUnits = '\\mathrm{\\left[\\frac{%s^2}{Hz}\\right]}'%(nUnits)
        html += '<th colspan = "3" class="center">Noise source: %s</th>'%(key)
        try:
            srcValue = instObj.snoiseTerms[key]
        except:
            srcValue = 0
        if instObj.substitute:
            srcValue = fullSubs(srcValue, instObj.circuit.parDefs)
        if instObj.numeric:
            srcValue = sp.N(srcValue, ini.disp)
        html += '<tr><td class="title">Spectral density:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(srcValue, numeric = instObj.numeric)), nUnits)
        html += '<tr><td class="title">Detector-referred:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.onoiseTerms[key], numeric = instObj.numeric)), detUnits)
        if instObj.srcUnits != None:
            html += '<tr><td class="title">Source-referred:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.inoiseTerms[key], numeric = instObj.numeric)), srcUnits)
    html += '</table>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def dcVar2html(instObj, label = '', labelText = ''):
    """
    Displays the reults of a dc variance analysis on the active html page.

    Not implemented with parameter stepping.

    :param instObj: Results of an instruction with data type 'dcvar'.
    :type instObj: SLiCAP.protos.allResults
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
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
    if label != "":
        label = _addLabel(label, caption=labelText, labelType="data")
    detUnits = '\\mathrm{\\left[ %s^2 \\right]}'%(instObj.detUnits)
    html = '<h2>Dcvar analysis results</h2>\n'
    html += '<h3>DC solution of the network</h3>\n'
    html += '$$%s=%s$$\n'%(sp.latex(roundN(instObj.Dv)), sp.latex(roundN(instObj.dcSolve, numeric = instObj.numeric)))
    html += '<h3>Detector-referred variance</h3>\n'
    html += '$$\\sigma_{out}^2=%s\\, %s$$\n'%(sp.latex(roundN(instObj.ovar, numeric = instObj.numeric)), detUnits)
    if instObj.srcUnits != None:
        srcUnits = '\\mathrm{\\left[ %s^2 \\right]}'%(instObj.srcUnits)
        html += '<h3>Source-referred variance</h3>\n'
        html += '$$\\sigma_{in}^2=%s\\, %s$$\n'%(sp.latex(roundN(instObj.ivar, numeric = instObj.numeric)), srcUnits)
    html += '<h3>Contributions of individual component variances</h3><table>\n'
    keys = list(instObj.ovarTerms.keys())
    keys.sort()
    for key in keys:
        nUnits = key[0].upper()
        if nUnits == 'I':
            nUnits = 'A'
        nUnits = '\\mathrm{\\left[ %s^2 \\right]}'%(nUnits)
        html += '<th colspan = "3" class="center">Variance of source: %s</th>'%(key)
        try:
            srcValue = instObj.svarTerms[key]
        except:
            srcValue = 0
        if instObj.substitute:
            srcValue = fullSubs(srcValue, instObj.circuit.parDefs)
        if instObj.numeric:
            srcValue=sp.N(srcValue, ini.disp)
        html += '<tr><td class="title">Source variance:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(srcValue, numeric = instObj.numeric)), nUnits)
        html += '<tr><td class="title">Detector-referred:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.ovarTerms[key], numeric = instObj.numeric)), detUnits)
        if instObj.srcUnits != None:
            html += '<tr><td class="title">Source-referred:</td><td>$%s$</td><td class="units">$\\,%s$</td></tr>\n'%(sp.latex(roundN(instObj.ivarTerms[key], numeric = instObj.numeric)), srcUnits)
    html += '</table>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def coeffsTransfer2html(transferCoeffs, label='', labelText=''):
    """
    Displays the gain factor and the coefficients of the numerator and the 
    denominator of a transfer function on the active html page.
    
    :param transferCoeffs: Result of coeffsTransfer() function
    :type transferCoeffs: list
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    
    """
    label = _addLabel(label, caption=labelText, labelType="data")    
    (gain, numerCoeffs, denomCoeffs) = transferCoeffs
    html = '<h3>' + label +  'Gain factor</h3>\n<p>$%s$</p>\n'%(sp.latex(roundN(gain)))
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
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def monomial_coeffs2html(coeff_dict, label='', labelText=''):
    label = _addLabel(label, caption=labelText, labelType="data")
    html = '<h3>' + label + 'Monomial coefficients</h3>\n<table><tr><th class=\"left\">Monomial</th><th class=\"left\">Coefficient</th></tr>\n'
    for key in coeff_dict:
        html += '<tr><td class=\"left\">$' + sp.latex(key) + '$</td><td class=\"left\">$' + sp.latex(roundN(coeff_dict[key])) + '$</td></tr>\n'
    html += '</table>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html
        
def stepArray2html(stepVars, stepArray, label="", labelText=""):
    """
    Displays the step array on the active HTML page.

    :param stepVars: List with step variables
    :type tepVars: list
    
    :param stepArray: List with lists for step data
    :type stepArray: list
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    numVars = len(stepVars)
    numRuns = len(stepArray[0])
    if label != "":
        label = _addLabel(label, caption=labelText, labelType="data")
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
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def fig2html(figureObject, width, label='', caption=''):
    """
    Copies the image file to the 'img.' subdirectory of the 'html/' directory
    set by HTMLPATH in SLiCAPini.py and creates a link to this file on the
    active html page.
    
    :param figureObject: SLiCAP figure object generated with a plot function.
    :type figureObject: SLiCAPplots.figure
    
    :param width: Width of the figure in pixels
    :type width: int
    
    :param label: ID of the label assigned to these tables; defaults to ''.
    :type label: str
    
    :param labelText: Label text to be displayed by **links2html()**; defaults to ''
    :type labelText: str
    
    :return: HTML string that will be placed on the page.
    :rtype: str
    """
    label = _addLabel(label, caption=caption, labelType="fig")
    html = '<figure>%s<img src="img/%s" alt="%s" style="width:%spx">\n'%(label, figureObject.fileName + '.' + figureObject.fileType, caption, width)
    if caption != '':
        html+='<figcaption>Figure: %s<br>%s</figcaption>\n'%(figureObject.fileName, caption)
    html += '</figure>\n'
    html = _insertHTML(ini.html_path + ini.html_page, html)
    try:
        copy2(ini.img_path + figureObject.fileName + '.' + figureObject.fileType, 
              ini.html_path + 'img/' + figureObject.fileName + '.' + figureObject.fileType)
    except:
        print("Error: could not copy: '{0}'.".format(ini.img_path + figureObject.fileName + '.' + figureObject.fileType))
    return html

def file2html(fileName):
    """
    Writes the contents of a file to the active html page. The file must be
    located in the ini.txt_path.

    :param fileName: Name of the file
    :type fileName: str
    
    :return: html code that will be inserted in the HTML file
    :rtype: str
    """
    f = open(ini.txt_path + fileName)
    html = f.read()
    f.close()
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

### HTML links and labels

def href(label, fileName=''):
    """
    Returns the html code for a jump to a label 'labelName'.
    This label can be on any page. If referring backwards 'fileName' can be
    detected automatically. When referring forward 'fileName' must be the
    name of the file that will be created later. Run a project 2 times without
    closing it after the first run, automaitcally detects all labels.
    
    :param label: ID of the label.
    :type label: str
    
    :param fileName: Name of the HTML page for inserting the link.
    :type fileName: str
    
    :return: HTML code that will be inserted
    :rtype: str
    """
    html = ''
    if fileName == '':
        fileName = ini.html_labels[label][1]
    if fileName == ini.html_page:
        html = '<a href="#' + label + '">' + ini.html_labels[label][2] + '</a>'
    else:
        html = '<a href="' + fileName + '#' + label + '">' + ini.html_labels[label][2] + '</a>'
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
    
    # [typ, page, '"' + text + '"']
    
    htmlPage('Links')
    labelDict = {}
    html = ''
    
    # Create a dictionary with key = label type and value is labes of that type
    for labelType in _LABELTYPES:
        labelDict[labelType] = []
        for labelName in ini.html_labels.keys():
            if ini.html_labels[labelName][0] == labelType:
                labelDict[labelType].append(labelName)        
    # Print the labels with a heading fot each group
    for labelType in _LABELTYPES:
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
    html = _insertHTML(ini.html_path + ini.html_page, html)
    return html

def htmlLink(address, text):
    """
    Returns the html code for placing a link on an html page with *text2html()*.

    :param address: link address
    :type address: str

    :return: HTML code
    :rtype: str
    """
    html = '<a href="' + address + '">' + text + '</a>\n'
    return html

def htmlParValue(cir, parName):
    """
    Returns code for inline display of parameter 'parName' from instruction
    'instr'. 
    :param cir: Circuit object that holds the parameter definition
    :type instr: SLiCAPprotos.circuit

    :param parName: Name of the parameter
    :type parName: string

    :return: HTML code for the parameter value
    :rtype: string
    """
    return '$' + str(sp.latex(roundN(cir.getParValue(parName)))) + '$'

def htmlElValue(cir, elName, param='value', numeric=False):
    """
    Returns code for inline display of value of element 'elName' from instruction
    'instr'.

    :param instr: Instruction that holds the parameter definition
    :type instr: SLiCAPinstruction.instruction

    :param elName: Element identifier
    :type elName: string

    :param param: Element parameter name
    :type param: string
    
    :param numeric: - True: full recursive substitution of circuit parameters.
                    - False: value or expression of the parameter given with 
                      the element.
                      
                    Defaults to False

    :return: HTML code for the element value
    :rtype: string
    """
    return '$' + str(sp.latex(roundN(cir.getElementValue(elName, param=param, 
                                                         numeric=numeric)))) + '$'
