#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module for interfacing with KiCAD
"""
import subprocess
import os
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPsvgTools import _crop_svg
#try:
#    import cairosvg
#except:
#    print("Error: cannot convert SVG to PDF using cairosvg. Please convert manually if necessary.")
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

class _KiCADcomponent(object):
    def __init__(self):
        self.refDes = ""
        self.nodes = {}
        self.refs = []
        self.model = ""
        self.params = {}
        self.cmd = ""
        
def _removeParenthesis(field):
    while field[0] == "(":
        field = field[1:]
    while field[-1] == ")":
        field = field[:-1]
    return field

def _checkTitle(title):
    title = '"' + title + '"'
    return title.replace('""', '"')

def _parseKiCADnetlist(kicad_sch, kicadPath=''):
    fileName   = '.'.join(kicad_sch.split('.')[0:-1])
    try:
        subprocess.run([ini.kicad, 'sch', 'export', 'netlist', '-o', ini.cir_path + kicadPath + fileName + ".net", ini.cir_path + kicadPath + fileName + ".kicad_sch"])
        f = open(ini.cir_path + kicadPath + fileName + ".net", "r")
        lines = f.readlines()
        f.close()
        netlist = _parseKiCADnetlistlines(lines)
        cirName = fileName.split('/')[-1].split('.')[0] + ".cir"
        cirFile = ini.cir_path + cirName
        f = open(cirFile, 'w')
        f.write(netlist)
        f.close()
    except FileNotFoundError:
        print("\nError: could not run Kicad using '{}'.".format(ini.kicad))
    return cirName
    
def _parseKiCADnetlistlines(lines, cirTitle):
    reserved   = ["Description", "Footprint", "Datasheet"]
    components = {}
    nodes      = {}
    nodelist   = []
    comps      = False
    title      = False
    for line in lines:
        # remove spaces in expression
        try:
            startExpr = line.index("{")
            stopExpr = line.index("}", startExpr)
            line = line[0:startExpr] + line[startExpr:stopExpr].replace(" ", "").replace("\t", "") + line[stopExpr:]
        except ValueError:
            pass
        fields = line.split()
        fields = [_removeParenthesis(field) for field in fields]
        if fields[0] == "title":
            if len(fields) > 1:
                title = _checkTitle(" ".join(fields[1:]))
        elif fields[0] == "comp":
            newComp = _KiCADcomponent()
            newComp.refDes = fields[fields.index('ref')+1][1:-1]
            comps= True
        elif fields[0] == "tstamps":
            components[newComp.refDes] = newComp
            comps = False
        elif fields[0] == "value" and comps:
            value = fields[fields.index("value")+1][1:-1]
            if value != '~':
                newComp.params["value"] = value
        elif fields[0] == "field" and comps:
            try:
                fieldName = fields[2][1:-1]
                fieldValue = fields[3][1:-1]
                if fieldName == "model":
                    newComp.model = fieldValue
                elif fieldName[0:-1] == "ref":
                    newComp.refs.append(fieldValue)
                elif fieldName == 'command':
                    newComp.command = ' '.join(fields[3:])[1:-1]
                elif fieldName not in reserved:
                    newComp.params[fieldName] = fieldValue
            except IndexError:
                # Field has no value!
                pass
        elif fields[0] == 'net':
            lastNode = fields[fields.index('name')+1][1:-1]
            #lastNode = fields[4][1:-1]
            nodes[lastNode] = lastNode
        elif fields[0] == "node":
            refDes = fields[fields.index('ref')+1][1:-1]
            pinNum = fields[fields.index("pin")+1][1:-1]
            components[refDes].nodes[pinNum] = lastNode
    nodenames = nodes.keys()
    for node in nodenames:
        i = 1
        if "(" in node:
            while str(i) in nodenames or str(i) in nodelist:
                i += 1
            nodes[node] = str(i)
            nodelist.append(str(i))
        elif node[0] == "/":
            nodes[node] = node[1:]
            nodelist.append(node[1:])
    for refDes in components.keys():
        for node in components[refDes].nodes.keys():
            components[refDes].nodes[node] = nodes[components[refDes].nodes[node]]
    if not title:
        title = cirTitle
    netlist = title
    for refDes in components.keys():
        if refDes[0] != "A":
            netlist += "\n" + refDes
            pinlist = list(components[refDes].nodes.keys())
            pinlist.sort()
            for pin in pinlist:
                netlist += " " + components[refDes].nodes[pin]
            for ref in components[refDes].refs:
                netlist += " " + ref
            netlist += " " + components[refDes].model
            for param in components[refDes].params.keys():
                netlist += " " + param + "=" + components[refDes].params[param]
        else:
            netlist +='\n' + components[refDes].command
    netlist += "\n.end"
    return netlist

def KiCADsch2svg(fileName):
    """
    Creates drawing-size images in .SVG and .PDF format from Kicad schematics.
    The image files will be placed in the img subdirectory in the project fodler.
    The names of the image files equal that of the schematic file, but the 
    file extensions differ (.svg and .pdf).
    
    :param fileName: Name of the Kicad schematic file,  relative to project
                     folder or absolute
    :type fileName: str
    """
    if ini.kicad == "":
        print("Please install Kicad, delete '~/SLiCAP.ini', and run this script again.")
    else:
        cirName = fileName.split('/')[-1].split('.')[0]
        if os.path.isfile(fileName):
            print("Creating drawing-size SVG and PDF images of {}".format(fileName))
            subprocess.run([ini.kicad, 'sch', 'export', 'svg', '-o', ini.img_path, '-e', '-n', fileName])
            _crop_svg(ini.img_path + cirName + ".svg")
            renderPDF.drawToFile(svg2rlg(ini.img_path + cirName + ".svg"), ini.img_path + cirName + ".pdf")
            """
            try:
                cairosvg.svg2pdf(url=ini.img_path + cirName + ".svg", write_to=ini.img_path + cirName + ".pdf")
            except:
                print("Error: cannot convert SVG to PDF using cairosvg. Please convert manually if necessary.")
            """
        else:
            print("Error: could not open: '{}'.".format(fileName))
    
def _kicadNetlist(fileName, cirTitle):
    Kicad = False
    Inkscape = False
    if ini.kicad == "":
        print("Please install Kicad, delete '~/SLiCAP.ini', and run this script again.")
    elif os.path.isfile(fileName):
        print("Creating netlist of {} using KiCAD".format(fileName))
        kicadnetlist  = fileName.split('.')[0] + '.net'        
        subprocess.run([ini.kicad, 'sch', 'export', 'netlist', '-o', kicadnetlist, fileName])
        f = open(kicadnetlist, "r")
        lines = f.readlines()
        f.close()
        netlist = _parseKiCADnetlistlines(lines, cirTitle)
        cirName = fileName.split('/')[-1].split('.')[0]+ ".cir"
        cirFile = ini.cir_path + cirName 
        f = open(cirFile, 'w')
        f.write(netlist)
        f.close()
        KiCADsch2svg(fileName)
    else:
        print("Error: could not open: '{}'.".format(fileName))
    return cirName

if __name__=='__main__':
    from SLiCAP import initProject
    prj=initProject('kicad')
    fileName    = "SLiCAP.kicad_sch"
    print(_parseKiCADnetlist(fileName))
    KiCADsch2svg(fileName)
