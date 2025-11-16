#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module for interfacing with KiCAD
"""
import subprocess
import os
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPsvgTools import _crop_svg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from SLiCAP.SLiCAPprotos import _MODELS, _SPICEMODELS
import re

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

def _parseKiCADnetlist(kicad_sch, kicadPath='', language="SLICAP"):
    fileName = '.'.join(kicad_sch.split('.')[0:-1])
    cirTitle = fileName.split('/')[-1].split('.')[0]
    cirName  = cirTitle + ".cir"
    cirFile  = ini.cir_path + cirName
    try:
        subprocess.run([ini.kicad, 'sch', 'export', 'netlist', '-o', ini.cir_path + kicadPath + fileName + ".net", ini.cir_path + kicadPath + fileName + ".kicad_sch"])
        f = open(ini.cir_path + kicadPath + fileName + ".net", "r")
        lines = f.readlines()
        f.close()
        netlist, subckt, subckt_lib = _parseKiCADnetlistlines(lines, cirTitle, language)
        f = open(cirFile, 'w')
        f.write(netlist)
        f.close()
    except FileNotFoundError:
        print("\nError: could not run Kicad using '{}'.".format(ini.kicad))
    return cirName
    
def _parseKiCADnetlistlines(lines, cirTitle, language):
    reserved   = ["Description", "Footprint", "Datasheet"]
    components = {}
    nodes      = {}
    nodelist   = []
    comps      = False
    title      = False
    subckt     = False
    subckt_lib = False
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
            if language == "SLiCAP":
                value = fields[fields.index("value")+1][1:-1]
            elif language == "SPICE":
                value = " ".join(fields[fields.index("value")+1:])[1:-1]
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
                elif fieldName == "Vsource":
                    newComp.refs.append(fieldValue)
                elif fieldName == 'command':
                    newComp.command = ' '.join(fields[3:])[1:-1]
                else:    
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
    netlist = ""
    for refDes in components.keys():
        onoff = None
        if refDes[0] != "A":
            netlist += "\n" + refDes
            pinlist = list(components[refDes].nodes.keys())
            pinlist.sort()
            for pin in pinlist:
                netlist += " " + components[refDes].nodes[pin]
            for ref in components[refDes].refs:
                netlist += " " + ref
            if language == "SLiCAP":
                netlist += " " + components[refDes].model
            for param in components[refDes].params.keys():
                if language == "SLiCAP":
                    if refDes[0] != "X":
                        try:
                            if param in _MODELS[components[refDes].model].params:
                                netlist += " " + param + "=" + components[refDes].params[param]
                        except KeyError:
                            if param not in reserved:
                                    netlist += " " + param + "=" + components[refDes].params[param]
                    elif param not in reserved:
                            netlist += " " + param + "=" + components[refDes].params[param]
                elif language == "SPICE":
                    if param == "onoff":
                        onoff = components[refDes].params["onoff"]
                    elif param == "value":
                        netlist += " " + components[refDes].params["value"]
                    elif refDes[0] != "X" and param in _SPICEMODELS[components[refDes].model]:
                        netlist += " " + param + "=" + components[refDes].params[param]
                    elif param not in reserved:
                        netlist += " " + param + "=" + components[refDes].params[param]
            if language == "SPICE" and onoff != None:
                netlist += " " + onoff  
        else:
            CMD = components[refDes].command.split()
            if CMD[0].upper() == ".SUBCKT":
                subckt = components[refDes].command
            elif CMD[0].upper() == ".FILE":
                if len(CMD) < 2:
                    print("Error: KiCAD netlister: missing library file")
                else:
                    subckt_lib = " ".join(CMD[1:]).replace('\\"', '"').replace('" ', '"')
                    print("LIB", subckt_lib)
            else:
                netlist +='\n' + components[refDes].command
    #if language == "SPICE":
    #    netlist += "\n.INC %sSLiCAP/files/lib/SPICE.lib"%(ini.install_path)
    if not title:
        title = cirTitle
    if subckt:
        netlist = subckt + netlist + "\n.ends"
        subckt = subckt.split()[1]
        if language == "SLiCAP" and not subckt_lib:
            netlist = title + "\n" + netlist
            netlist += "\n.end"
    else:
        netlist = title + netlist
        netlist += "\n.end"
    return netlist, subckt, subckt_lib

def KiCADsch2svg(fileName):
    """
    Creates drawing-size images in .SVG and .PDF format from KiCad schematics.
    The image files will be placed in the img subdirectory in the project fodler.
    The names of the image files equal that of the schematic file, but the 
    file extensions differ (.svg and .pdf).
    
    :param fileName: Name of the KiCad schematic file,  relative to project
                     folder or absolute
    :type fileName: str
    """
    if ini.kicad == "":
        print("Please install KiCad, delete '~/SLiCAP.ini', and run this script again.")
    else:
        cirName = fileName.split('/')[-1].split('.')[0]
        if os.path.isfile(fileName):
            print("Creating drawing-size SVG and PDF images of {}".format(fileName))
            subprocess.run([ini.kicad, 'sch', 'export', 'svg', '-o', ini.img_path, '-e', '-n', fileName])
            _crop_svg(ini.img_path + cirName + ".svg")
            renderPDF.drawToFile(svg2rlg(ini.img_path + cirName + ".svg"), ini.img_path + cirName + ".pdf")
        else:
            print("Error: could not open: '{}'.".format(fileName))
    
def _kicadNetlist(fileName, cirTitle, language="SLiCAP"):
    if ini.kicad == "":
        print("Please install KiCad, delete '~/SLiCAP.ini', and run this script again.")
    elif os.path.isfile(fileName):
        print("Creating netlist of {} using KiCAD".format(fileName))
        kicadnetlist  = fileName.split('.')[0] + '.net'        
        subprocess.run([ini.kicad, 'sch', 'export', 'netlist', '-o', kicadnetlist, fileName])
        f = open(kicadnetlist, "r")
        lines = f.readlines()
        f.close()
        netlist, subckt, subckt_lib = _parseKiCADnetlistlines(lines, cirTitle, language=language)
        if subckt:
            f = open(ini.user_lib_path + subckt + ".lib", "w")
            f.write(netlist)
            f.close()
        else:
            cirName = fileName.split('/')[-1].split('.')[0]+ ".cir"
            cirFile = ini.cir_path + cirName 
            f = open(cirFile, 'w')
            f.write(netlist)
            f.close()
        KiCADsch2svg(fileName)
    else:
        print("Error: could not open: '{}'.".format(fileName))
    return netlist, subckt

def backAnnotateSchematic(sch, opinfo):
    """
    #. Replaces text labels <label> on a KiCAD schematic with <label>:<opinfo[label]>
    #. Creates drawing-size ``svg`` and ``pdf`` images of the annotated schematic
    #. Saves the annotated schematic
    
    :param sch: File of the KiCAD schematic with annotation text labels;
                location relative to project directory
    :type sch: str
    
    :param opinfo: Dictionary with key-value pairs:
         
                   - key: label text
                   - value: text to be appended to the label
    :return: None
    :rtype: NoneType
    """
    f = open(sch, "r")
    schematic = f.read()
    f.close()
    replacements = {}
    for name in opinfo.keys():
        m = re.search(rf'(\(text "{name})(\:\s?[+-]?\d+\.?\d*)?([eE][+-]?\d+)?"', schematic)
        if m != None:
            replacements[m.group(0)] = m.group(1) + ': {:8.2e}"' .format(opinfo[name])
    for replacement in replacements.keys():
        schematic = schematic.replace(replacement, replacements[replacement])
    f = open(sch, "w")
    f.write(schematic)
    f.close()
    KiCADsch2svg(sch)  
    
if __name__=='__main__':
    from SLiCAP import initProject
    prj=initProject('kicad')
    fileName    = "SLiCAP.kicad_sch"
    print(_parseKiCADnetlist(fileName))
    KiCADsch2svg(fileName)
 