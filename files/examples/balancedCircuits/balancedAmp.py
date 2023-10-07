#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
from SLiCAP import *
prj=initProject('driver')
fileName = "balancedAmp"

#makeNetlist(fileName + ".asc", "Balanced Line Driver")

i1 = instruction()
i1.setCircuit(fileName + ".cir")

htmlPage("Circuit Data")
head2html("Circuit diagram")
img2html(fileName + ".svg", 600)
netlist2html(fileName + ".cir")
elementData2html(i1.circuit)
params2html(i1.circuit)

htmlPage("Stability analysis")
i1.setSimType("numeric")
i1.setGainType("gain")
i1.setDataType("poles")
polesResult = i1.execute()
listPZ(polesResult)
pz2html(polesResult)
text2html("The circuit has two poles with a positive real part. Hence it is instable.")

i1.setSource(["V1P", "V1N"])
i1.setDetector(["V_outP", "V_outN"])
i1.setDataType("zeros")
zerosResult = i1.execute()
listPZ(zerosResult)
pz2html(zerosResult)
text2html("The instability is not observable!")

i1.setDataType("pz")
pzResult = i1.execute()
listPZ(pzResult)
pz2html(pzResult)
text2html("The source-load transfer has five poles. They all have a negative real part.")
text2html("Hence, the instable behavior cannot be observed in the source-load transfer")

i1.setSimType("symbolic")
htmlPage("DM-CM decomposition")
# Define the decomposition
head2html("MNA matrix equation")
i1.setGainType("vi")
i1.setDataType("matrix")
matrices2html(i1.execute())

head2html("DM-CM matrix equation")
i1.setPairExt(['P', 'N'])

i1.setConvType('all') 
matrices2html(i1.execute())

head2html("DM matrix equation")
i1.setConvType('dd') 
matrices2html(i1.execute())

head2html("CM matrix equation")
i1.setConvType('cc') 
matrices2html(i1.execute())
i1.setSimType("numeric")
head2html("poles of the transformed circuit")
i1.setConvType('all') 
i1.setGainType("gain")
i1.setDataType("poles")
result = i1.execute()
listPZ(result)
pz2html(result)

head2html("poles and zeros of the CM transfer")
i1.setDataType("pz")
i1.setConvType('cc') 
i1.setDetector('V_out_C')
result = i1.execute()
listPZ(result)
pz2html(result)

head2html("poles and zeros of the DM transfer")
i1.setConvType('dd') 
i1.setDetector('V_out_D')
result = i1.execute()
listPZ(result)
pz2html(result)
