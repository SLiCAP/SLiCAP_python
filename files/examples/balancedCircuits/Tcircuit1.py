#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
from SLiCAP import *

fileName = "Tcircuit1"

#makeNetlist(fileName + ".asc", "T circuit -1-")

i1 = instruction()
i1.setCircuit(fileName + ".cir")

htmlPage("Circuit Data")
head2html("Circuit diagram")
img2html(fileName + ".svg", 600)
netlist2html(fileName + ".cir")
elementData2html(i1.circuit)
params2html(i1.circuit)

i1.setSimType('symbolic')
i1.setSource(['I1P', 'I1N'])

htmlPage("DM-CM decomposition")
# Define the decomposition
head2html("MNA matrix equation")
head3html("Gain type: vi")
i1.setGainType("vi")
i1.setDataType("matrix")
result = i1.execute()
matrices2html(result)
i1.setDetector('V_C')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
head3html("Gain type: gain")
matrices2html(result)

head2html("DM-CM matrix equation")
head3html("Gain type: vi")
i1.setPairExt(['P', 'N'])
i1.setConvType('all')
i1.setGainType("vi")
i1.setDataType("matrix")
result = i1.execute()
matrices2html(result)
i1.setDetector('V_C')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
head3html("Gain type: gain")
matrices2html(result)

head2html("DM matrix equation")
head3html("Gain type: vi")
i1.setConvType('dd')
i1.setGainType("vi")
i1.setDataType("matrix")
result = i1.execute()
matrices2html(result)
i1.setDetector('V_in_D')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
head3html("Gain type: gain")
matrices2html(result)
eqn2html("Z_dm", result.laplace)

head2html("CM matrix equation")
head3html("Gain type: vi")
i1.setConvType('cc')
i1.setGainType("vi")
i1.setDataType("matrix")
result = i1.execute()
matrices2html(result)
i1.setDetector('V_in_C')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
head3html("Gain type: gain")
matrices2html(result)
eqn2html("Z_cm", result.laplace)

htmlPage("Noise Analysis")
head2html("Differential detector")
i1.setConvType(None)
i1.setGainType("vi")
i1.setDataType("noise")
i1.setDetector(['V_inP', 'V_inN'])
noiseResult = i1.execute()
noise2html(noiseResult)
DMonoise = noiseResult.onoise
DMinoise = noiseResult.inoise

htmlPage("DM Noise analysis")
i1.setConvType('dd')
i1.setDetector('V_in_D')
i1.setGainType("vi")
i1.setDataType("noise")
noiseResult = i1.execute()
matrices2html(noiseResult)
noise2html(noiseResult)
if sp.N(noiseResult.onoise - DMonoise) == sp.N(0):
    print('DMonoise OK!')
else:
    print('DMonoise NOT OK!')
if sp.N(noiseResult.onoise - DMonoise) == sp.N(0):
    print('DMinoise OK!')
else:
    print('DMinoise NOT OK!')

htmlPage("CM Noise analysis")
i1.setDetector('V_in_C')
i1.setGainType("vi")
i1.setDataType("noise")
i1.setConvType('cc')
noiseResult = i1.execute()
matrices2html(noiseResult)
noise2html(noiseResult)