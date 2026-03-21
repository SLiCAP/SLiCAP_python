#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  2 14:51:28 2025
@author: anton
"""
import SLiCAP as sl
import re
import os
#sl.initProject("RST formatter") # Initialize the SLiCAP project
rst = sl.RSTformatter()
# Create a circuit object
cir = sl.makeCircuit("kicad/myPassiveNetwork/myPassiveNetwork.kicad_sch")

rst.netlist("myPassiveNetwork.cir").save("netlist")

rst.elementData(cir, label="tab-expanded", 
                caption="Expanded netlist").save("expanded")

rst.parDefs(cir, label="tab-pardefs", 
            caption="Circuit parameter definitions").save("pardefs")

rst.params(cir, label="tab-params", 
           caption="Undefined parameters").save("params")

# Obtain the MNA matrix equation of this network
matrixResult = sl.doMatrix(cir)
Iv = matrixResult.Iv
Dv = matrixResult.Dv
M  = matrixResult.M

# Save the matrix equation as LaTeX snippet
rst.matrixEqn(Iv, M, Dv, label="eq-matrices").save("matrices")

# Evaluate the transfer of the network
transfer = sl.doLaplace(cir).laplace

# Save the transfer as a LaTeX displayed equation
rst.eqn("V_out/V_in", transfer, label="eq-H1").save("H1")

# Save the transfer as a LaTeX inline expression
rst.expr(transfer, name="H2").save("substitutions")

# Save the transfer as a LaTeX inline equation
rst.eqnInline("V_out/V_in", transfer, name="H3").save("substitutions")

# Use the dictTable method to display a dictionary as a table
mydct = cir.parDefs
head = ["Name", "Value"]
rst.dictTable(mydct, head, label='tab-mydct', 
              caption='Circuit parameters using the dictTable format').save('mydct')

# Coefficients of the transfer:
# Define a transfer function:
H_s = sl.doLaplace(cir).laplace
# Assign the gain, the normalized numerator coefficients and the 
# normalized denominator coefficients to the variable 'coeffs'
coeffs = sl.coeffsTransfer(H_s)
# Generate a LaTeX snippet of the coefficient table with the 
# LaTeX formatter 'ltx':
rst.coeffsTransfer(coeffs, label="tab-coeffs", 
                   caption="Numerator and denominator coefficients of " +
                   ":math:`H(s)`, :math:`b_i` and :math:`a_i`, " +
                   "respectively").save("coeffs")

# Plot the magnitude plot
result = sl.doLaplace(cir, pardefs="circuit", numeric=True)
sl.plotSweep("dBmag", "dB magnitude plot of the transfer", result, 0.01,
             100, 500, sweepScale="M", funcType="dBmag")

dcVarResults = sl.doDCvar(cir)
rst.dcvarContribs(dcVarResults, label="tab-dcvar", 
                  caption="dcvar analysis results").save("dcvar")

noiseResults = sl.doNoise(cir, pardefs="circuit")
rst.noiseContribs(noiseResults, label="tab-noise", 
                  caption="Noise contributions").save("noise")

polesResult = sl.doPoles(cir, pardefs="circuit")
zerosResult = sl.doZeros(cir, pardefs="circuit")
pzResult    = sl.doPZ(cir, pardefs="circuit")
symZeros    = sl.doZeros(cir)

rst.pz(polesResult, label="tab-poles", caption="Poles of the transfer").save("poles")
rst.pz(zerosResult, label="tab-zeros", caption="Zeros of the transfer").save("zeros")
rst.pz(pzResult, label="tab-pz", caption="Poles and zeros of the transfer").save("pz")
rst.pz(symZeros, label="tab-symzeros", caption="Symbolic zeros of the transfer").save("symzeros")
rst.expr(pzResult.DCvalue, name="dcValue").save("substitutions")

f = rst.file("../../cir/myPassiveNetwork.cir").save("f")

specs = []
specs.append(sl.specItem("f_min", "Lower limit noise bandwidth", 10, units="Hz", specType="performance"))
specs.append(sl.specItem("f_max", "Upper limit noise bandwidth", 1e6, units="Hz", specType="performance"))
specs.append(sl.specItem("v_n", "RMS output noise over noise bandwidth", 1e6, units="Hz", specType="design"))
sl.specs2csv(specs, "specs.csv")
rst.specs(specs, specType="performance", label="tab-performance", 
          caption="Performance specifications").save("performance")
rst.specs(specs, specType="design", label="tab-design", 
          caption="Design specifications").save("design")

step_dict = {}
step_dict["method"] = "array"
step_dict["params"] = ["C_b", "R_ell"]
step_dict["values"] = [["100p", "250p", "500p"], [150, 100, 50]]
# Plot the magnitude plot
result = sl.doLaplace(cir, pardefs="circuit", numeric=True, stepdict=step_dict)
sl.plotSweep("dBmagStepped", "dB magnitude plot of the transfer", result, 0.01,
             100, 500, sweepScale="M", funcType="dBmag")
rst.stepArray(step_dict["params"], step_dict["values"], 
              label="tab-stepdict", caption="Step array").save("stepdict")

# Work-around to change subscripts to mathrm:

def sub2rm(textext):
    """
    Converts LaTeX subscripts in italic fonts into mathrm fonts.
    
    :param textext: LaTeX snippet
    :type textxt: str
    
    :return: Modified LaTeX snippet
    :rtype: str
    
    :example:
        
    >>> textext = "\\frac{V_{out}}{V_{in}}"
    >>> print(sub2rm(textext))
    
    \\frac{V_{\\mathrm{out}}}{V_{\\mathrm{in}}}
    """
    pos = 0
    out = ''
    pattern = re.compile(r'_{([a-zA-Z0-9]+)}')
    for m in re.finditer(pattern, textext):
        out += textext[pos:m.start()+1]+'{\\mathrm'+textext[m.start()+1: m.end()]+'}'
        pos = m.end()
    out += textext[pos:]
    return out

# Convert all the snippets

files = os.listdir(sl.ini.rst_snippets)
for fi in files:
    f = open(sl.ini.rst_snippets + fi, "r")
    textext = f.read()
    f.close()
    f = open(sl.ini.rst_snippets + fi, "w")
    f.write(sub2rm(textext))
    f.close()