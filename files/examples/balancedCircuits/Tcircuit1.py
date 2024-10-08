#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
import SLiCAP as sl
import sympy as sp

fileName = "Tcircuit1.asc"

cir = sl.makeCircuit(sl.ini.cir_path + fileName, imgWidth=600)

sl.htmlPage("DM-CM decomposition")

sl.head2html("MNA matrix equation")
result = sl.doMatrix(cir)
sl.matrices2html(result)

sl.head2html("DM-CM matrix equation")
result = sl.doMatrix(cir, convtype='all')
sl.matrices2html(result)

sl.head2html("DM matrix equation")
result = sl.doMatrix(cir, convtype='dd')
sl.matrices2html(result)

sl.head2html("DM transfer")
result = sl.doLaplace(cir, convtype='dd')
sl.eqn2html("Z_dm", result.laplace)

sl.head2html("CM matrix equation")
result = sl.doMatrix(cir, convtype='cc', detector="V_C")
sl.matrices2html(result)

sl.head2html("CM transfer to V_C")
result = sl.doLaplace(cir, convtype='cc', detector="V_C")
sl.eqn2html("Z_cm", result.laplace)

sl.head2html("CM transfer to V_in_C")
result = sl.doLaplace(cir, convtype='cc')
sl.eqn2html("Z_cm", result.laplace)

sl.htmlPage("Noise Analysis")
sl.head2html("Differential detector")
noiseResult = sl.doNoise(cir)
sl.noise2html(noiseResult)
DMonoise = noiseResult.onoise
DMinoise = noiseResult.inoise

sl.htmlPage("DM Noise analysis")

noiseResult = sl.doNoise(cir, convtype = 'dd')
sl.noise2html(noiseResult)

if sp.N(noiseResult.onoise - DMonoise) == sp.N(0):
    print('DMonoise OK!')
else:
    print('DMonoise NOT OK!')
if sp.N(noiseResult.onoise - DMonoise) == sp.N(0):
    print('DMinoise OK!')
else:
    print('DMinoise NOT OK!')
sl.htmlPage("CM Noise analysis")
noiseResult = sl.doNoise(cir, convtype='cc')
sl.noise2html(noiseResult)
