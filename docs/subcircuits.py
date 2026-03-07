#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
subcircuits.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

###############################################################################
# work with subcircuits
###############################################################################

cir = sl.makeCircuit("hierarchy.cir")

# Create a subcircuit library file: <sl.ini.user_lib_path>smallAmp.lib
smallAmp = sl.makeCircuit("kicad/smallAmp/smallAmp.kicad_sch")

# Create a subcircuit library file: <sl.ini.user_lib_path>bigAmp.lib
bigAmp = sl.makeCircuit("kicad/bigAmp/bigAmp.kicad_sch")

# Create the main circuit
mainAmp = sl.makeCircuit("kicad/mainAmp/mainAmp.kicad_sch")

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.elementData(cir, caption="Expanded netlist data of hierarchy.cir").save(
    "table-hierarchy-expanded")
rst.parDefs(cir, caption="Expanded circuit parameter definitions").save(
    "table-hierarchy-pardefs")
rst.params(cir, caption="Expanded circuit undefined parameters").save(
    "table-hierarchy-params")
rst.elementData(mainAmp, caption="Expanded netlist data of mainAmp.cir").save(
    "table-mainamp-expanded")
rst.parDefs(mainAmp, caption="Expanded circuit parameter definitions").save(
    "table-mainamp-pardefs")
rst.params(mainAmp, caption="Expanded circuit undefined parameters").save(
    "table-mainamp-params")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.elementData(cir, caption="Expanded netlist data of hierarchy.cir").save(
    "table-hierarchy-expanded")
ltx.parDefs(cir, caption="Expanded circuit parameter definitions").save(
    "table-hierarchy-pardefs")
ltx.params(cir, caption="Expanded circuit undefined parameters").save(
    "table-hierarchy-params")
ltx.elementData(mainAmp, caption="Expanded netlist data of mainAmp.cir").save(
    "table-mainamp-expanded")
ltx.parDefs(mainAmp, caption="Expanded circuit parameter definitions").save(
    "table-mainamp-pardefs")
ltx.params(mainAmp, caption="Expanded circuit undefined parameters").save(
    "table-mainamp-params")
