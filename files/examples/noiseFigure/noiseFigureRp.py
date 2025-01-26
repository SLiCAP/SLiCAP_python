#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import SLiCAP as sl
import sympy as sp

fileName = 'ExNoiseFigureRp'

cir = sl.makeCircuit(sl.ini.cir_path + 'ExNoiseFigureRp.cir')


# Define the frequency range
f_min = sp.Symbol('f_min')
f_max = sp.Symbol('f_max')

# Execute the instruction (numeric)
result = sl.doNoise(cir, numeric=True)

# Calculate the squared RMS noise at the detector
var_onoise     = sl.rmsNoise(result, 'onoise', f_min, f_max)**2
# Calculate the contribution of the source to the squared RMS detector noise
var_onoise_src = sl.rmsNoise(result, 'onoise', f_min, f_max, 'V1')**2
# Calculated the noise figure in dB
F_o = 10*sp.log(sp.simplify(var_onoise/var_onoise_src))/sp.log(10)

# Create an HTML page with the results of the noise analysis

sl.htmlPage('Symbolic noise analysis')
sl.noise2html(result)
sl.head2html('Noise figure')
sl.text2html('The noise figure of a circuit is defined as the ratio of the signal-to-noise at the output of the circuit and the signal-to-noise ratio of its input signal.')
sl.text2html('Alternatively, the noise figure can be defined as the as the ratio of the total source referred noise power and the noise power of the signal source, ' +
          'or the ratio of the total detector-referred noise power and the contribution of the noise of the signal source to the detector-referred noise power.')
sl.text2html('The variance $P_{onoise}\\,\\left[ V^2 \\right]$ of the total detector referred noise is:')
sl.eqn2html('P_onoise', var_onoise, units='V^2/Hz')
sl.text2html('The contribution $P_{onoise,source}\\,\\left[ V^2 \\right]$ of the source to $P_{onoise}\\,\\left[ V^2 \\right]$ is:')
sl.eqn2html('P_onoise', var_onoise_src, units='V^2/Hz')
sl.text2html('Hence, the noise figure is obtained as')
sl.eqn2html('F', F_o)
sl.head2html('Detector referred noise spectrum')
sl.text2html('The spectral density of the total output noise can be written as')
sl.eqn2html('S_out', sp.together(result.onoise))
