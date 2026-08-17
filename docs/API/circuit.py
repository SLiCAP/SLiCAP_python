#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
circuit.py: SLiCAP script for the HTML help file
"""
import SLiCAP as sl

# Create a SLiCAP circuit object from a kicad schematic file
#############################################################

# 'makeCircuit()`' also creates an HTML page with circuit data
cir = sl.makeCircuit("kicad/Transimpedance/Transimpedance.kicad_sch", imgWidth=350)

# Display information about the expanded netlist elements
for element in cir.elements.keys():
    print("\n==============================================")
    print("refDes    :", cir.elements[element].refDes)
    print("nodes     :" , cir.elements[element].nodes)
    print("refs      :" , cir.elements[element].refs)
    print("model     :" , cir.elements[element].model)
    if len(cir.elements[element].params.keys()):
        print("\nModel parameters:")
        for param in cir.elements[element].params.keys():
            print(param, "=", cir.elements[element].params[param])

# Circuit parameter definitions
for param in cir.parDefs:
    print(param, "=", cir.parDefs[param])
    
rst = sl.RSTformatter()
lxt = sl.LaTeXformatter()
    