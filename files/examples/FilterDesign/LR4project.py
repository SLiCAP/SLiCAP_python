#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import SLiCAP as sl
import sympy as sp

# Creates the SLiCAP libraries and the project HTML index page
prj = sl.initProject('4-th order Linkwitz-Riley Filter') 

cir = sl.makeCircuit(sl.ini.cir_path + "FilterDesign/FilterDesign.kicad_sch", imgWidth=400)
# Find the Laplace transfer of the network
resultLapl  = sl.doLaplace(cir, pardefs=None)
transfer    = resultLapl.laplace
# Define the prototype filter
f_o         = sp.Symbol('f_o')
protoType   = sp.sympify('1/(1 + sqrt(2)*s/2/pi/f_o + (s/2/pi/f_o)^2)^2')
# Define the cross-over frequency of the filter
protoType   = protoType.subs(f_o, 2000)
# Calculate the circuit prameters
paramValues = sl.equateCoeffs(protoType, transfer, noSolve = [f_o])

# Make Bode Plots
# Assign the numeric element values to the circuit
cir.defPars(paramValues)
result      = sl.doLaplace(cir, pardefs='circuit', numeric=True)
figdBmag    = sl.plotSweep('LR4dBmag', 'dB magnitude characteristic', result, 
                           0.02, 20, 100, sweepScale='k', show=False)
figPgase    = sl.plotSweep('LR4phase', 'phase characteristic', result, 0.02, 
                           20, 100, funcType = 'phase', sweepScale='k', 
                           show=False)

###############################################################################
sl.htmlPage('Report')

sl.head2html('Prototype function')
sl.eqn2html('P_s', protoType)

sl.head2html('Circuit implementation')
sl.img2html('FilterDesign.svg', 400)

sl.head2html('Transfer of the network')
sl.eqn2html('T_s', transfer)

sl.head2html('Parameter values')
for key in paramValues.keys():
    sl.eqn2html(key, paramValues[key])
    
sl.elementData2html(cir)  
sl.params2html(cir)

sl.head2html('Plots')
sl.fig2html(figdBmag, 600, caption='dB magnitude of the LR4 filter transfer.')  
sl.fig2html(figPgase, 600, caption='phase plot of the LR4 filter transfer.')    
