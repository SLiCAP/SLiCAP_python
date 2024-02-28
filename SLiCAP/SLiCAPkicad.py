#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on February 8, 2024

@author: anton
"""
import os
from SLiCAP.SLiCAPini import ini
import subprocess

class KiCADcomponent(object):
    def __init__(self):
        self.refDes = ""
        self.nodes = {}
        self.refs = []
        self.model = ""
        self.params = {}
        self.cmd = ""

def removeParenthesis(field):
    while field[0] == "(":
        field = field[1:]
    while field[-1] == ")":
        field = field[:-1]
    return field

def checkTitle(title):
    title = '"' + title + '"'
    return title.replace('""', '"')

def parseKiCADnetlist(kicad_sch, kicadPath=''):
    fileName = '.'.join(kicad_sch.split('.')[0:-1])
    subprocess.run([ini.kicad, 'sch', 'export', 'netlist', '-o', ini.circuitPath + kicadPath + fileName + ".net", ini.circuitPath + kicadPath + fileName + ".kicad_sch"])
    components = {}
    nodes      = {}
    nodelist   = []
    comps      = False
    title      = False
    f = open(ini.circuitPath + kicadPath + fileName + ".net", "r")
    kicad_netlist_lines = f.readlines()
    f.close()
    for line in kicad_netlist_lines:
        fields = line.split()
        fields = [removeParenthesis(field) for field in fields]
        if fields[0] == "title":
            if len(fields) > 1:
                title = checkTitle(" ".join(fields[1:]))
        elif fields[0] == "comp":
            newComp = KiCADcomponent()
            newComp.refDes = fields[-1][1:-1]
            comps= True
        elif fields[0] == "tstamps":
            components[newComp.refDes] = newComp
            comps = False
        elif fields[0] == "value" and comps:
            if fields[-1][1:-1] != '~':
                newComp.params["value"] = fields[-1][1:-1]
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
                else:
                    newComp.params[fieldName] = fieldValue
            except IndexError:
                # Field has no value!
                pass
        elif fields[0] == 'net':
            lastNode = fields[-1][1:-1]
            nodes[lastNode] = lastNode
        elif fields[0] == "node":
            refDes = fields[2][1:-1]
            pinNum = fields[4][1:-1]
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
        while not title:
            print("Error: missing a valid circuit title")
            title = checkTitle(input("Enter a circuit title: "))
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
    f = open(ini.circuitPath + fileName + ".cir", 'w')
    f.write(netlist)
    f.close()
    return netlist

def KiCADsch2svg(fileName, kicadPath = ''):
    imgFile = fileName.split('.')[0] + ".svg"
    subprocess.run([ini.kicad, 'sch', 'export', 'svg', '-o', ini.imgPath, '-e', '-n', ini.circuitPath + kicadPath + fileName])
    subprocess.run([ini.inkscape, '-o', ini.imgPath + imgFile, '-D', ini.imgPath + imgFile])

if __name__=='__main__':
    from SLiCAP import initProject
    prj=initProject('kicad')
    fileName    = "SLiCAP.kicad_sch"
    print(parseKiCADnetlist(fileName))
    KiCADsch2svg(fileName)
