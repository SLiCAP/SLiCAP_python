#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 10:48:40 2020

@author: anton
"""

from SLiCAP import *
t1 = time()

prj = initProject('4-th order Linkwitz-Riley Filter') 
                             # Creates the SLiCAP libraries and the
                             # project HTML index page
fileName = 'LowPassLR.cir'
i1 = instruction()           # Creates an instance of an instruction object
i1.setCircuit(fileName)      # Checks and defines the local circuit object and
                             # resets the index page to the project index page
# Calculate the symbolic transfer of the filter circuit                             
i1.setSource('V1')
i1.setDetector('V_out')
i1.setSimType('symbolic')
i1.setGainType('gain')
i1.setDataType('laplace')
resultLapl  = i1.execute()
transfer    = resultLapl.laplace
# Define the prototype filter
f_o         = sp.Symbol('f_o')
protoType   = sp.sympify('1/(1 + sqrt(2)*s/2/pi/f_o + (s/2/pi/f_o)^2)^2')
# Define the cross-over frequency of the filter
protoType   = protoType.subs(f_o, 2000)
# Calculate the circuit prameters
paramValues  = equateCoeffs(protoType, transfer, noSolve = [f_o])
# Obtain the numeric element values
# Define the circuit parameters
i1.defPars(paramValues)
i1.setSimType('numeric')
elementValues = i1.getElementValue(['C1', 'C2', 'L1', 'L2'])
print(elementValues)
# Check the transfer 
i1.gainType = 'gain'
i1.dataType = 'laplace'
result      = i1.execute()
 
figdBmag    = plotSweep('LR4dBmag', 'dB magnitude characteristic', result, 0.02, 20, 100, sweepScale='k', show=True)
figPgase    = plotSweep('LR4phase', 'phase characteristic', result, 0.02, 20, 100, funcType = 'phase', sweepScale='k', show=True)

htmlPage('Report')

head2html('Prototype function')
eqn2html('P_s', protoType)

head2html('Circuit implementation')
img2html('LowPassLR.svg', 400)

head2html('Transfer of the network')
eqn2html('T_s', transfer)

head2html('Parameter values')
for key in paramValues.keys():
    eqn2html(key, paramValues[key])
elementData2html(i1.circuit)  
params2html(i1.circuit)

head2html('Plots')
fig2html(figdBmag, 600, caption='dB magnitude of the LR4 filter transfer.')  
fig2html(figPgase, 600, caption='phase plot of the LR4 filter transfer.')    
t2 = time()
print(t2-t1, 's')