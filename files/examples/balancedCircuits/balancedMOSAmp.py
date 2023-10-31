#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
from SLiCAP import *
fileName = "balancedMOSAmp"

#makeNetlist(fileName + ".asc", "Balanced Line Driver")

i1 = instruction()
i1.setCircuit(fileName + ".cir")

htmlPage("Circuit Data")
head2html("Circuit diagram")
img2html(fileName + ".svg", 600)
netlist2html(fileName + ".cir")
elementData2html(i1.circuit)
params2html(i1.circuit)

i1.setSimType("symbolic")
htmlPage("DM-CM decomposition")
# Define the decomposition
head2html("MNA matrix equation")
i1.setGainType("vi")
i1.setDataType("matrix")
matrices2html(i1.execute())

head2html("DM-CM matrix equation")
i1.setPairExt(['P', 'N'])
i1.setLGref(["Gm_M1_XU1P","Gm_M1_XU1N"])
i1.setConvType('all') 
matrices2html(i1.execute())

head2html("DM matrix equation")
i1.setConvType('dd') 
matrices2html(i1.execute())

head2html("CM matrix equation")
i1.setConvType('cc') 
matrices2html(i1.execute())
i1.setSimType("numeric")



htmlPage("Loop Gain")
head2html("Loop Gain of the DM transfer")
i1.setConvType('dd') 
i1.setDataType('laplace')
i1.setGainType('loopgain')
i1.setSimType("numeric")
result = i1.execute()
eqn2html("L_G",result.laplace)

