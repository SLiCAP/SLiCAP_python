#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 16:38:36 2021

@author: anton

Test file for networks with a 1x1 matrix
"""

from SLiCAP import *
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
matrices2html(i1.execute())

head2html("Time-domain response using Cramer's rule")
i1.setSimType('numeric')
i1.setDataType('time')
i1.setSource('I1')
result = i1.execute()
V = result.time
eqn2html('V_1(t)', V)
figTime = plotSweep('V_time', 'Output voltage', result, 0, 10, 500, sweepScale = 'm', show = True)
fig2html(figTime, 600)
head2html('Gain using cofactors')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
G = result.laplace
eqn2html('V_1/I_I1', G)
print(G)
i1.setDataType('pz')
result = i1.execute()
pz2html(result)
listPZ(result)