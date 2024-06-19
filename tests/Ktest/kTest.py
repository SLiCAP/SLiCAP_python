#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  9 19:31:38 2021

@author: anton
"""

from SLiCAP import *
prj = initProject('kTest')
i1 = instruction()
makeNetlist('k.asc', 'kTest')
i1.setCircuit('k.cir')
#
htmlPage('Circuit data')
head2html('Circuit diagram')
img2html('k.svg', 300)
netlist2html('k.cir')
head2html('MNA equation')
i1.setSimType('symbolic')
i1.setGainType('vi')
i1.setDataType('matrix')
result = i1.execute()
matrices2html(result)

if result.M == sp.sympify("Matrix([[0, 0, 0, 1, 0], [0, -L_a*s, -k*s*sqrt(L_a*L_b), 1, 0], [0, -k*s*sqrt(L_a*L_b), -L_b*s, 0, 1], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0]])"):
    print("\nMatrix stamp K ok!")
else:
    print("\nError in matrix stamp K!")