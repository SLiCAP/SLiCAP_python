#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import SLiCAP as sl
import sympy as sp

fileName = 'ExNoiseFigureAmp'

cir = sl.makeCircuit(sl.ini.cir_path + 'ExNoiseFigureAmp.asc', imgWidth=600)

# Define the frequency range
f_min = sp.Symbol('f_min')
f_max = sp.Symbol('f_max')

# Perorm a noise analysis
result = sl.doNoise(cir)
# Calculate the squared RMS noise at the detector
var_onoise     = sl.rmsNoise(result, 'onoise', f_min, f_max)**2
# Calculate the contribution of the source to the squared RMS detector noise
var_onoise_src = sl.rmsNoise(result, 'onoise', f_min, f_max, 'V1')**2
# Calculated the noise figure
F_o = 10*sp.log(sp.simplify(var_onoise/var_onoise_src))/sp.log(10)

# Create an HTML page with the results of the noise analysis
sl.htmlPage('Symbolic noise analysis')
sl.noise2html(result)
sl.head2html('Detector referred noise spectrum')
sl.text2html('The spectral density of the total output noise can be written as:')
sl.eqn2html('S_out', sp.together(result.onoise), units=result.detUnits+'^2/Hz')
sl.head2html('Noise figure')
sl.text2html('The noise figure is obtained as:')
sl.eqn2html('F', F_o, units='dB')