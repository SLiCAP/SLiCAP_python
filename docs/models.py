#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
models.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

###############################################################################
# work with models
###############################################################################

# Create a circuit object
cir = sl.makeCircuit("kicad/ZtoV/ZtoV.kicad_sch")

# Display the expanded netlist
print('"' + cir.title +'"')
for element in cir.elements.keys():
    refdes = cir.elements[element].refDes
    nodes = ""
    for node in cir.elements[element].nodes:
        nodes += node + " "
    refs = ""
    if len(cir.elements[element].refs):
        for ref in cir.elements[element].refs:
            refs += ref + " "
    model = cir.elements[element].model
    pardefs = ""
    for param in cir.elements[element].params.keys():
        pardefs += str(param) + "={" + str(cir.elements[element].params[param]) +"} "
    print(refdes, nodes, refs, model, pardefs)
for param in cir.parDefs.keys():
    print(".param " + str(param) + " ={" + str(cir.parDefs[param]) + "}")
print(".end")

# Generate an RST snippet of the table with expanded elements for the Help file
rst = sl.RSTformatter()

rst.elementData(cir, 
                caption="Expanded netlist element data").save("table-ZtoV_elements")

# Generate a LaTeX snippet of the table with expanded elements for the Help file
ltx = sl.LaTeXformatter()

ltx.elementData(cir, 
                caption="Expanded netlist element data").save("table-ZtoV_elements")