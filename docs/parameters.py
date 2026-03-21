#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
parameters.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

###############################################################################
# work with parameters
###############################################################################

# Define a circuit
RC_cir = sl.makeCircuit("kicad/myFirstRCnetwork/myFirstRCnetwork.kicad_sch")

# Print the contents of the dictionary with circuit parameter definitions:
if len(RC_cir.parDefs.keys()):
    print("\nParameters with definitions:\n")
    for key in RC_cir.parDefs.keys():
        print(key, RC_cir.parDefs[key])
else: 
    print("\nFound no parameter definitions")
    
# Print the contents of the list with parameters that have no definition:
if len(RC_cir.params):
    print("\nParameters that have no definition:\n")
    for param in RC_cir.params:
        print(param)
else:
    print("\nFound no parameters without definition")
    
# Define parameters        
RC_cir.defPar('R', 'tau/C') # Define R = tau/C
RC_cir.defPar('C', '10n')   # Define C = 10 nF
RC_cir.defPar('tau', '1u')  # Define tau = 1 us
print(RC_cir.parDefs)

# Define multiple parameters
RC_cir.defPars({'R': 'tau/C', 'C': '10n', 'tau': '1/f_c'})
print(RC_cir.parDefs)

# Delete a parameter definition
RC_cir.delPar('f_c')           # Delete the definition of f_c

# Print the contents of the dictionary with circuit parameter definitions:
if len(RC_cir.parDefs.keys()):
    print("\nParameters with definitions:\n")
    for key in RC_cir.parDefs.keys():
        print(key, RC_cir.parDefs[key])
else: 
    print("\nFound no parameter definitions")
    
# Print the contents of the list with parameters that have no definition:
if len(RC_cir.params):
    print("\nParameters that have no definition:\n")
    for param in RC_cir.params:
        print(param)
else:   
    print("\nFound no parameters without definition")
    
# Obtain the value of a parameter
RC_cir.defPar('R', '1/2/pi/f_c/C')    # Define the value of R
RC_cir.defPar('C', '10n')             # Define the value of C
RC_cir.defPar('f_c', '1M')            # Define the value of tau

R_defined           = RC_cir.getParValue('R', substitute=False, numeric=False)
R_evaluated         = RC_cir.getParValue('R', substitute=True,  numeric=False)
R_defined_numeric   = RC_cir.getParValue('R', substitute=False, numeric=True)
R_evaluated_numeric = RC_cir.getParValue('R', substitute=True,  numeric=True)

print('\nR_defined            :', R_defined)
print('R_evaluated          :', R_evaluated)
print('R_defined_numeric    :', R_defined_numeric)
print('R_evaluated_numeric  :', R_evaluated_numeric)

# Obtain the values of multiple parameters
print(RC_cir.getParValue(['R','C'], substitute=False, numeric=False))
print(RC_cir.getParValue(['R','C'], substitute=False, numeric=True))
print(RC_cir.getParValue(['R','C'], substitute=True,  numeric=False))
print(RC_cir.getParValue(['R','C'], substitute=True,  numeric=True))

# Generate RST snippets of tables with parameters for the Help file
rst = sl.RSTformatter()

rst.parDefs(RC_cir, 
            caption="RC circuit parameter definitions").save("table-RC_pardefs")
rst.params(RC_cir, 
           caption="RC circuit undefined parameters").save("table-RC_params")

# Generate LaTeXT snippets of tables with parameters for the Help file
ltx = sl.LaTeXformatter()

ltx.parDefs(RC_cir, caption="RC circuit parameter definitions").save("table-RC_pardefs")
ltx.params(RC_cir, caption="RC circuit undefined parameters").save("table-RC_params")