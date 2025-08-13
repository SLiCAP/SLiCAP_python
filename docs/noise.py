#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
noise.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp
import numpy as np
# Create a circuit object
cir = sl.makeCircuit("kicad/noiseSources/noiseSources.kicad_sch")

for par in cir.parDefs:
    print(par, cir.parDefs[par])
    
noiseResult = sl.doNoise(cir, detector="V_out", source="V1")

for par in cir.parDefs:
    print(par, cir.parDefs[par])
    
onoise      = noiseResult.onoise
print(onoise)

inoise      = noiseResult.inoise
print(inoise)

snoiseTerms = noiseResult.snoiseTerms
onoiseTerms = noiseResult.onoiseTerms
inoiseTerms = noiseResult.inoiseTerms
for term in snoiseTerms:
    print("\n= " + term + " =")
    print("value        :", snoiseTerms[term])
    print("det-referred :", onoiseTerms[term])
    print("src-referred :", inoiseTerms[term])

params = {"R_a"  : "1k",
          "C_a"  : "10u",
          "L_a"  : "1m",
          "f_ell": 100}

cir.defPars(params)

numNoise = sl.doNoise(cir, detector="V_out", pardefs="circuit", numeric=True)

f_min = 1e3
f_max = 1e6

RMS = sl.rmsNoise(numNoise, 'onoise', f_min, f_max)
print(RMS)

# noise figure; V1 is signal source, with associated noise spectrum S_v
o_var   = RMS**2
src_var = sl.rmsNoise(numNoise, 'onoise', f_min, f_max, source="V1")**2
noiseF  = sp.expand(o_var/src_var)
print(noiseF)
F       = 10*sp.log(noiseF)/sp.log(10)
print(F)

print(sl.DIN_A())

# Plot the DIN A weighting curve
frequencies = np.geomspace(10, 20e3, 200, endpoint=True)
din_A_func  = sp.lambdify(sl.ini.frequency, 20*sp.log(sl.DIN_A())/sp.log(10))
din_A_num   = din_A_func(frequencies)
din_A_trace = sl.trace([frequencies, din_A_num])
din_A_trace.label = "DIN A"
traceDict   = {"DINA": din_A_trace}
sl.plot("DINA", "DIN A weighting curve", "semilogx", traceDict, 
        xName="Frequency", xUnits="Hz", yUnits="dB", show=False)

S_v, tau     = sp.symbols("S_v, tau")
cds_weighted = sl.doCDS(S_v, tau)
print(cds_weighted)

# Plot the CDS weighting curve for tau = 1 us
freqs       = np.geomspace(5e3, 4.5e6, 1000)
cds_func  = sp.lambdify(sl.ini.frequency, 10*sp.log(sl.doCDS(sp.N(1), 1e-6))/sp.log(10))
cds_num   = cds_func(freqs)
cds_trace = sl.trace([freqs, cds_num])
cds_trace.label = "CDS"
traceDict   = {"CDS": cds_trace}
sl.plot("CDS", "CDS weighting curve", "semilogx", traceDict, 
        xName="Frequency", xUnits="Hz", yUnits="dB", show=False)

S_v = sp.sympify("S_i/(2*pi*f*C_i)^2")
var = sl.doCDSint(S_v, tau, 0, sp.oo)
print(var)

var = sl.assumePosParams(var).doit()
var = sl.clearAssumptions(var)
print(var)

Si, Sv = sp.symbols("S_i, S_v")
integrated_noise   = sl.integrate_monomial_coeffs(numNoise.onoise, [Si, Sv], 
                                                  sl.ini.frequency, f_min, f_max, 
                                                  doit=True)
print(integrated_noise)

integrated_noise_coeffs = sl.integrated_monomial_coeffs(numNoise.onoise, [Si, Sv], 
                                       sl.ini.frequency, f_min, f_max, doit=False)

# Create an RST formatter
rst = sl.RSTformatter()
# Save expressions in the sphinx/SLiCAPdata folder of the project directory
rst.eqn("S_vno", onoise, multiline=1, label="eqn-Svno", units="V**2/Hz").save("eqn-Svno")
rst.eqn("S_vni", inoise, label="eqn-Svni", units="V**2/Hz").save("eqn-Svni")
rst.noiseContribs(noiseResult, "Noise contributions").save("table-noiseContribs")
rst.eqn("V_nRMS", RMS, units="V").save("eqn-RMS")
rst.eqn("F", F, units="dB").save("eqn-F")
rst.eqn("S_vCDS", cds_weighted, units="V**2/Hz").save("eqn-CDSweighting")
rst.eqn("sigma^2", var, units="V**2").save("eqn-CDSint")
rst.eqn("v_n^2", integrated_noise, units="V**2").save("eqn-intCoeffs")
rst.dictTable(integrated_noise_coeffs, 
              caption="Numeric integrals as coeffs of :math:`S_v` and :math:`S_i`").save("table-coeffsNoise")

ltx = sl.LaTeXformatter()