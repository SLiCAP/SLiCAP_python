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
import sympy as sp

class _KiCADcomponent(object):
    def __init__(self):
        self.refDes = ""
        self.nodes = {}
        self.refs = []
        self.model = ""
        self.params = {}
        self.cmd = ""
        
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
        text = f.read()
        f.close()
        netlist, subckt, subckt_lib = _parseKiCADnetlisttext(text, cirTitle, language)
        f = open(cirFile, 'w')
        f.write(netlist)
        f.close()
    except FileNotFoundError:
        print("\nError: could not run Kicad using '{}'.".format(ini.kicad))
    return cirName


# ---------------------------------------------------------------------------
# S-expression tokeniser and parser  (KiCad 9.x and 10.x compatible)
#
# KiCad 10 moved from compact single-line layout to fully expanded multi-line
# S-expressions.  Parsing the whole file into a tree once makes the rest of
# the code layout-agnostic and works for both versions.
# ---------------------------------------------------------------------------

def _tokenise(text):
    """
    Yield tokens from a KiCad S-expression string.
    Tokens are: '(' | ')' | bare-word | "quoted string" (with quotes stripped).
    """
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in ' \t\r\n':
            i += 1
        elif c in '()':
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == '\\':   # skip escaped character
                    j += 1
                j += 1
            yield text[i+1:j]         # yield content without surrounding quotes
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            yield text[i:j]
            i = j


def _parse_sexpr(tokens):
    """
    Recursively parse a token stream into a nested list.
    Must be called after the opening '(' has been consumed.
    Each (tag child1 child2 ...) becomes ['tag', child1, child2, ...],
    where children are plain strings or nested lists.
    """
    tag = next(tokens)
    children = []
    for tok in tokens:
        if tok == '(':
            children.append(_parse_sexpr(tokens))
        elif tok == ')':
            return [tag] + children
        else:
            children.append(tok)
    return [tag] + children   # top-level fallback for a well-formed file


def _find_child(node, tag):
    """Return the first child list whose tag matches, or None."""
    for child in node[1:]:
        if isinstance(child, list) and child[0] == tag:
            return child
    return None


def _find_all_children(node, tag):
    """Return all child lists whose tag matches."""
    return [child for child in node[1:] if isinstance(child, list) and child[0] == tag]


def _child_value(node, tag):
    """
    Return the first bare string inside the child with the given tag, or None.
    E.g. for (ref "R1"), _child_value(comp, 'ref') returns 'R1'.
    """
    child = _find_child(node, tag)
    if child is None:
        return None
    return next((i for i in child[1:] if isinstance(i, str)), None)


# ---------------------------------------------------------------------------
# Main parser  –  now tree-based, KiCad 9.x and 10.x compatible
# ---------------------------------------------------------------------------

def _parseKiCADnetlisttext(text, cirTitle, language):
    reserved   = ["Description", "Footprint", "Datasheet"]
    components = {}
    nodes      = {}
    nodelist   = []
    subckt     = False
    subckt_lib = False

    # Collapse whitespace inside {param expressions} before tokenising,
    # so e.g. {1 / (2*pi*R*f_c)} is never split across tokens.
    text = re.sub(r'\{[^}]*\}', lambda m: m.group(0).replace(' ', '').replace('\t', ''), text)
    tokens = iter(_tokenise(text))
    next(tokens)              # consume the outermost '('
    tree = _parse_sexpr(tokens)

    # ---- title ----
    design_node = _find_child(tree, 'design')
    title = False
    if design_node is not None:
        sheet_node = _find_child(design_node, 'sheet')
        if sheet_node is not None:
            tb = _find_child(sheet_node, 'title_block')
            if tb is not None:
                t = _child_value(tb, 'title')
                if t:
                    title = _checkTitle(t)

    # ---- components ----
    comps_node = _find_child(tree, 'components')
    if comps_node is not None:
        for comp_node in _find_all_children(comps_node, 'comp'):
            newComp = _KiCADcomponent()
            newComp.refDes = _child_value(comp_node, 'ref')
            if newComp.refDes is None:
                continue

            # value
            val = _child_value(comp_node, 'value')
            if val and val != '~':
                newComp.params["value"] = val

            # fields
            fields_node = _find_child(comp_node, 'fields')
            if fields_node is not None:
                for field_node in _find_all_children(fields_node, 'field'):
                    field_name = _child_value(field_node, 'name')
                    # field value is a bare string sibling of the (name ...) child
                    field_val = next((i for i in field_node[1:] if isinstance(i, str)), None)
                    if field_name is None or field_val is None:
                        continue
                    if field_name == "model":
                        newComp.model = field_val
                    elif field_name[0:-1] == "ref":
                        newComp.refs.append(field_val)
                    elif field_name == "Vsource":
                        newComp.refs.append(field_val)
                    elif field_name == 'command':
                        newComp.command = field_val
                    else:
                        newComp.params[field_name] = field_val

            components[newComp.refDes] = newComp

    # ---- nets ----
    nets_node = _find_child(tree, 'nets')
    if nets_node is not None:
        for net_node in _find_all_children(nets_node, 'net'):
            net_name = _child_value(net_node, 'name')
            if net_name is None:
                continue
            nodes[net_name] = net_name
            for node_node in _find_all_children(net_node, 'node'):
                refDes = _child_value(node_node, 'ref')
                pinNum = _child_value(node_node, 'pin')
                if refDes and pinNum and refDes in components:
                    components[refDes].nodes[pinNum] = net_name

    # ---- normalise node names ----
    nodenames = list(nodes.keys())
    for node in nodenames:
        i = 1
        if "(" in node:
            while str(i) in nodes.values() or str(i) in nodelist:
                i += 1
            nodes[node] = str(i)
            nodelist.append(str(i))
        elif node[0] == "/":
            nodes[node] = node[1:]
            nodelist.append(node[1:])

    for refDes in components.keys():
        for pin in components[refDes].nodes.keys():
            raw = components[refDes].nodes[pin]
            components[refDes].nodes[pin] = nodes.get(raw, raw)

    # ---- build netlist text ----
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
            if language == "SPICE" and onoff is not None:
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
                netlist += '\n' + components[refDes].command

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
        text = f.read()
        f.close()
        netlist, subckt, subckt_lib = _parseKiCADnetlisttext(text, cirTitle, language=language)
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
