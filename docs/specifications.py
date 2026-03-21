#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
specifications.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp

###############################################################################
# Work with specifications
###############################################################################

# Tip: Define parameter values at the top of the file, this makes it easy to 
#      modify them later.

Cs = 10e-12
Ip = 20e-6
Vp = 4
Bf = 5e4
Vn = 10e-6

specs = []
specs.append(sl.specItem("C_s",
                         description = "Typical value of the source capacitance",
                         value       = Cs,
                         units       = "F",
                         specType    = "Interface"))
specs.append(sl.specItem("I_p",
                         description = "Peak-peak input current",
                         value       = Ip,
                         units       = "A",
                         specType    = "Interface"))
specs.append(sl.specItem("V_p",
                         description = "Peak-peak output voltage",
                         value       = Vp,
                         units       = "V",
                         specType    = "Interface"))
specs.append(sl.specItem("B_f",
                         description = "Target value -3dB bandwidth in Hz",
                         value       = Bf,
                         units       = "Hz",
                         specType    = "Performance"))
specs.append(sl.specItem("V_n",
                         description = "Maximum unweighted RMS output noise voltage",
                         value       = Vn,
                         units       = "V",
                         specType    = "Performance"))

# Save specs to 'csv/specs.csv'
sl.specs2csv(specs, "specs.csv")

# Importing a list with specItems from 'csv/specs.csv'
specs = sl.csv2specs("specs.csv")

# Convert the speccification list to a dictionary for easy addressing
spec_dict = sl.specs2dict(specs)

# Print name, value and units of 'interface specifications'
for name in spec_dict.keys():
    if spec_dict[name].specType.lower() == "interface":
        value = spec_dict[name].value
        units = spec_dict[name].units
        print(name, sp.N(value, 3), units)
    
# Assigning specifications to circuit parameters

# Create a circuit object
cir = sl.makeCircuit("kicad/Transimpedance/Transimpedance.kicad_sch", imgWidth=350)

# Assign the specifications to circuit parameters
sl.specs2circuit(specs, cir)

# Print name and value of circuit parameters
print("\nCircuit parameter definitions")
for name in cir.parDefs.keys():
    print(name, sp.N(cir.parDefs[name], 3))
# Print the contents of the list with parameters that have no definition:
if len(cir.params):
    print("\nParameters that have no definition:\n")
    for param in cir.params:
        print(param)
else:
    print("\nFound no parameters without definition")
    
# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.specs(specs, specType="Performance", 
          caption="Performance specification").save("table-specs-performance")
rst.specs(specs, specType="Interface", 
          caption="Interface specification").save("table-specs-interface")

# Create LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.specs(specs, specType="Performance", 
          caption="Performance specification").save("table-specs-performance")
ltx.specs(specs, specType="Interface", 
          caption="Interface specification").save("table-specs-interface")