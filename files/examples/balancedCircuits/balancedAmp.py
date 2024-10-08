#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
import SLiCAP as sl

cir = sl.makeCircuit(sl.ini.cir_path + 'balancedAmp.asc')

sl.htmlPage("Stability analysis")
polesResult = sl.doPoles(cir, pardefs='circuit', numeric=True)
sl.listPZ(polesResult)
sl.pz2html(polesResult)
sl.text2html("The circuit has two poles with a positive real part. Hence it is instable.")

zerosResult = sl.doZeros(cir, pardefs='circuit', numeric=True)
sl.listPZ(zerosResult)
sl.pz2html(zerosResult)
sl.text2html("The instability is not observable!")

pzResult = sl.doPZ(cir, pardefs='circuit', numeric=True)
sl.listPZ(pzResult)
sl.pz2html(pzResult)
sl.text2html("The source-load transfer has five poles. They all have a negative real part.")
sl.text2html("Hence, the instable behavior cannot be observed in the source-load transfer")

sl.htmlPage("DM-CM decomposition")
# No decomp, MNA matrix
sl.head2html("MNA matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None))
# Decomposition with cmplete matrix
sl.head2html("DM-CM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='all'))
# DM transfer
sl.head2html("DM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='dd'))
# CM transfer
sl.head2html("CM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='cc'))
# Complete desomposition poles
sl.head2html("poles of the transformed circuit")
result = sl.doPoles(cir, pardefs='circuit', convtype='all', numeric=True)
sl.listPZ(result)
# Poles common-mode transfer
sl.head2html("poles and zeros of the CM transfer")
sl.result = sl.doPoles(cir, pardefs='circuit', convtype='cc', numeric=True)
sl.listPZ(result)
sl.pz2html(result)
# Poles and zeros differential-mode transfer
sl.head2html("poles and zeros of the DM transfer")
result = sl.doPoles(cir, pardefs='circuit', convtype='dd', numeric=True)
sl.listPZ(result)
sl.pz2html(result)
# Differential-mode loop gain
sl.head2html("Loop Gain of the DM transfer")
sl.result = sl.doLaplace(cir, transfer='loopgain', convtype='dd', pardefs=None)
sl.eqn2html("L_G",result.laplace)
