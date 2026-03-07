#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
matrix.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

# Create a circuit object
cir    = sl.makeCircuit("kicad/Transimpedance/Transimpedance.kicad_sch", imgWidth=350)
result = sl.doMatrix(cir)

Iv     = result.Iv # Vector with independent variables 
                   # (independent sources)
M      = result.M  # MNA matrix
Dv     = result.Dv # Vector with dependent variables 
                   # (unknown nodal voltages and branch currents)
print(Iv)
print(M)
print(Dv)

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.matrixEqn(Iv, M, Dv).save("eqn-matrix-trimp")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.matrixEqn(Iv, M, Dv).save("eqn-matrix-trimp")