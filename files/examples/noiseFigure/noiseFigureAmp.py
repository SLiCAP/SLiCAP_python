#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 18 14:28:17 2021

@author: anton
"""
from SLiCAP import *

fileName = 'ExNoiseFigureAmp'
#makeNetlist(fileName + '.asc', 'Amplifier noise figure')
i1 = instruction()
i1.setCircuit(fileName + '.cir')

# Create an HTML page will the circuit information
htmlPage('Circuit data')
head2html('Circuit diagram')
img2html(fileName + '.svg', 500)
netlist2html(fileName + '.cir')
elementData2html(i1.circuit)
params2html(i1.circuit)

# Define symbolic noise simulation
i1.setSimType('symbolic')
i1.setGainType('vi')
i1.setDataType('noise')

# Define source and detector
i1.setSource('V1')
i1.setDetector('V_out')

# Define the frequency range
f_min = sp.Symbol('f_min')
f_max = sp.Symbol('f_max')

# Execute the instruction
result = i1.execute()

# Calculate the squared RMS noise at the detector
var_onoise     = rmsNoise(result, 'onoise', f_min, f_max)**2
# Calculate the contribution of the source to the squared RMS detector noise
var_onoise_src = rmsNoise(result, 'onoise', f_min, f_max, 'V1')**2
# Calculated the noise figure
F_o = 10*sp.log(sp.simplify(var_onoise/var_onoise_src))/sp.log(10)

# Create an HTML page with the results of the noise analysis
htmlPage('Symbolic noise analysis')
noise2html(result)
head2html('Detector referred noise spectrum')
text2html('The spectral density of the total output noise can be written as:')
eqn2html('S_out', sp.together(result.onoise), units=i1.detUnits+'^2/Hz')
head2html('Noise figure')
text2html('The noise figure is obtained as:')
eqn2html('F', F_o, units='dB')