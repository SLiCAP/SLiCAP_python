#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 16:38:36 2021

@author: anton

Test file for networks with a 1x1 matrix
"""

from SLiCAP import *
from SLiCAP.SLiCAPmath import det

fileName = 'smallMatrix'
prj = initProject(fileName)
makeNetlist(fileName + '.asc', 'Small Matrix')
i1 = instruction()
i1.setCircuit(fileName + '.cir')
htmlPage('Circuit data')
head2html('Circuit diagram')
img2html(fileName + '.svg', 500)
netlist2html(fileName + '.cir')
elementData2html(i1.circuit)
params2html(i1.circuit)

head2html('Matrix equation')
i1.setSimType('symbolic')
i1.setGainType('vi')
i1.setDetector('V_1')
i1.setDataType('matrix')
result = i1.execute()
matrices2html(result)
M = result.M
if M == sp.sympify("Matrix([[C*s + 1/R]])"):
    print("\nMatrix equation is correct!")
else:
    print("\nError in matrix equation")

if det(M) == sp.sympify("C*s + 1/R"):
    print("\nDeterminant 1x1 matrix is correct!")
else:
    print("\nError in determinant 1x1 matrix!")

head2html("Time-domain response")
i1.setSimType('symbolic')
i1.setDataType('time')
i1.setSource('I1')
result = i1.execute()
V = result.time
if V == sp.sympify("2*pi*f*exp(-t/(C*R))/(C*(-2*pi*sqrt(-f**2) - 1/(C*R))*(2*pi*sqrt(-f**2) - 1/(C*R))) + f*exp(2*pi*t*sqrt(-f**2))/(2*C*sqrt(-f**2)*(2*pi*sqrt(-f**2) + 1/(C*R))) - f*exp(-2*pi*t*sqrt(-f**2))/(2*C*sqrt(-f**2)*(-2*pi*sqrt(-f**2) + 1/(C*R)))"):
    print("\nTime domain response is correct!")
else:
    print("\nError in time-domain response!")

head2html("Gain laplace")
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
G = result.laplace
if G == sp.sympify("R/(C*R*s + 1)"):
    print("\nGain is correct!")
else:
    print("\nError in gain!")

head2html("Gain poles")

i1.setDataType('poles')
result = i1.execute()
pz2html(result)
