#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 11:36:32 2023

@author: anton
"""

from SLiCAP import *

prj = initProject("myFirstVampNGspice")

# Example opamp circuit

# Define the circuit and the simulations
filePath = 'cir/'
cirFile  = 'MyFirstVampOPA211'
TRAN     = 'tran 100n 10u'
AC       = 'AC dec 100 1k 10meg'
DC       = 'DC V1 0 1 10m'
NOISE    = 'Noise v(7) V3 dec 100 1k 10meg 1'
stepCL   = 'CL list [1e-9, 5e-9, 50e-9]' # No postfixes!
#stepCL=None
names    = {'uncomp.': 'v(5)', 'comp.': 'v(7)'}
noiseNames    = {'onoise': 'onoise_spectrum', 'inoise': 'inoise_spectrum'}

# Stepped transient analysis
traceDict, xVar = ngspice2traces(filePath + cirFile, TRAN, names, stepCmd=stepCL)
plot(cirFile + TRAN.replace(' ', '_'), cirFile + ' ' + TRAN, 'lin', traceDict, xName=xVar, xUnits='s', xScale='u', yUnits='V', show=True)

# Stepped DC analysis
traceDict, xVar = ngspice2traces(filePath + cirFile, DC, names, stepCmd=stepCL)
plot(cirFile + DC.replace(' ', '_'), cirFile + ' ' + DC, 'lin', traceDict, xName=xVar, xUnits='V',  yUnits='V', show=True)

# Stepped AC analysis
magTraces, phaseTraces, xVar = ngspice2traces(filePath + cirFile, AC, names, stepCmd=stepCL, traceType='dBmagPhase')
plot(cirFile + AC.replace(' ', '_'), cirFile + ' ' + AC, 'semilogx', magTraces, xName=xVar, xScale='k', xUnits = 'Hz', yUnits='dB', show=True)
plot(cirFile + AC.replace(' ', '_'), cirFile + ' ' + TRAN, 'semilogx', phaseTraces, xName=xVar, xScale='k', xUnits = 'Hz', yUnits='deg', show=True)

# Stepped Noise analysis
noiseTraces, xVar = ngspice2traces(filePath + cirFile, NOISE, noiseNames, stepCmd=stepCL, traceType='noise')
plot(cirFile + NOISE.replace(' ', '_'), cirFile + ' ' + NOISE, 'log', noiseTraces, xName=xVar, xScale='k', xUnits = 'Hz', yUnits='$\\frac{V^2}{Hz}$', show=True)