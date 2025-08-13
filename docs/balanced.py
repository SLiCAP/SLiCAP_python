#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
balanced.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp
sl.initProject("balanced")
###############################################################################
# work with balanced circuits
###############################################################################

balancedNetwork = sl.makeCircuit("kicad/balancedNetwork/balancedNetwork.kicad_sch")
noneM = sl.doMatrix(balancedNetwork)
allM  = sl.doMatrix(balancedNetwork, convtype="all")
ddM   = sl.doMatrix(balancedNetwork, convtype="dd")
dcM   = sl.doMatrix(balancedNetwork, convtype="dc")
cdM   = sl.doMatrix(balancedNetwork, convtype="cd")
ccM   = sl.doMatrix(balancedNetwork, convtype="cc")

if cdM.M.is_zero_matrix and dcM.M.is_zero_matrix:
    print("The CM-DM decomposition is orthogonal!")
else:
    print("Warning: the CM-DM decomposition is NOT orthogonal!")

# Conversion matrix:
print(allM.A)

# Use models
# OpAmp circuit
Vamp = sl.makeCircuit("kicad/balancedAmp/balancedAmp.kicad_sch")
print(Vamp.elements['E_O1N'].params)
print(Vamp.elements['E_O1P'].params)
# Matrix equation
VampAll = sl.doMatrix(Vamp, pardefs="circuit", numeric=True, convtype="all")

# Use sub circuits
subckt = sl.makeCircuit("kicad/myBJTamp/myBJTamp.kicad_sch")
BJTdiffAmp = sl.makeCircuit("kicad/BJTdiffAmp/BJTdiffAmp.kicad_sch")

# Disable parameter pairing
sl.ini.remove_param_pair_ext = False
BJTampAllF = sl.doMatrix(BJTdiffAmp, pardefs="circuit", numeric=True, convtype="all")
# The circuit parameters are not altered
print(BJTdiffAmp.params)
print(BJTdiffAmp.parDefs)
# The instruction parameters are not altered
print(BJTampAllF.circuit.params)
print(BJTampAllF.circuit.parDefs)
# Enable parameter pairing (default setting)
sl.ini.remove_param_pair_ext = True
BJTampAllT = sl.doMatrix(BJTdiffAmp, pardefs="circuit", numeric=True, convtype="all")
# The circuit parameters are not altered
print(BJTdiffAmp.params)
print(BJTdiffAmp.parDefs)
# The instruction parameters are altered
print(BJTampAllT.circuit.params)
print(BJTampAllT.circuit.parDefs)

# Adapt detector
BJTampDD = sl.doLaplace(BJTdiffAmp, source=["V1P", "V1N"], detector=["V_outP", "V_outN"], convtype='dd').laplace
numer, denom = BJTampDD.as_numer_denom()
BJTampDD = 8*numer/(8*denom)
BJTampCC = sl.doLaplace(BJTdiffAmp, source=["V1P", "V1N"], detector=["V_outP", "V_outN"], convtype='cc').laplace

# Balanced Feedback
# Define parameters
par_dict = {"A_0": 1e6, "f_p1": 100}
Vamp.defPars(par_dict)

# Poles and zeros
poles = sl.doPoles(Vamp, pardefs="circuit", numeric=True)
zeros = sl.doZeros(Vamp, pardefs="circuit", numeric=True)
pz    = sl.doPZ(Vamp, pardefs="circuit", numeric=True)

# Differential-mode poles and zeros
pzdd  = sl.doPZ(Vamp, pardefs="circuit", numeric=True, convtype="dd")
sl.listPZ(pzdd)
# Differential-mode aysmptotic-gain model Bode plots
Add = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="dd", 
                   transfer="asymptotic")
Ldd = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="dd", 
                   transfer="loopgain")
Sdd = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="dd", 
                   transfer="servo")
Ddd = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="dd", 
                   transfer="direct")
Gdd = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="dd", 
                   transfer="gain")
# dB magnitude plots
sl.plotSweep("Vamp_dd_fb_dB", "Balanced voltage amplifier, differential-mode", 
             [Add, Ldd, Sdd, Ddd, Gdd], 0.1, 1e5, 200, sweepScale="k", 
             funcType="dBmag")
# Phase plots
sl.plotSweep("Vamp_dd_fb_phs", "Balanced voltage amplifier, differential-mode", 
             [Add, Ldd, Sdd, Ddd, Gdd], 0.1, 1e5, 200, sweepScale="k", 
             funcType="phase")

# Common-mode poles and zeros
pzcc  = sl.doPZ(Vamp, pardefs="circuit", numeric=True, convtype="cc")

# Common-mode aysmptotic-gain model Bode plots
Acc = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="cc", 
                   transfer="asymptotic")
Lcc = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="cc", 
                   transfer="loopgain")
Scc = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="cc", 
                   transfer="servo")
Dcc = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="cc", 
                   transfer="direct")
Gcc = sl.doLaplace(Vamp, pardefs="circuit", numeric=True, convtype="cc", 
                   transfer="gain")
# dB magnitude plots
sl.plotSweep("Vamp_cc_fb_dB", "Balanced voltage amplifier, common-mode", 
             [Acc, Lcc, Scc, Dcc, Gcc], 0.1, 1e5, 200, sweepScale="k", 
             funcType="dBmag")
# Phase plots
sl.plotSweep("Vamp_cc_fb_phs", "Balanced voltage amplifier, common-mode", 
             [Acc, Lcc, Scc, Dcc, Gcc], 0.1, 1e5, 200, sweepScale="k", 
             funcType="phase")

# Balanced noise
noisyCircuit = sl.makeCircuit("kicad/balancedNoisyNetwork/balancedNoisyNetwork.kicad_sch")

# Differential-mode output noise (complete circuit)
noiseResultD = sl.doNoise(noisyCircuit)

# Common-mode output noise (complete circuit)
noiseResultC = sl.doNoise(noisyCircuit, detector="V_CM")

# DM equivalent circuit
DnoiseResult = sl.doNoise(noisyCircuit, convtype="dd")

# Show difference (should be zero!)
diffD = sp.simplify(sl.assumePosParams(noiseResultD.onoise - DnoiseResult.onoise))
print("Difference onoise full circuit and DM equivalent network:", diffD)
# Display the noise source names
print("Noise sources:")
for src in noiseResultD.onoiseTerms:
    print(src, ":", noiseResultD.snoiseTerms[src])
print("Differential-mode noise sources contribution to DM onoise:")
for src in DnoiseResult.onoiseTerms:
    print(src, ":", DnoiseResult.snoiseTerms[src])

# CM equivalent circuit   
CnoiseResult = sl.doNoise(noisyCircuit, detector="circuit", convtype="cc")

# Show difference (should be zero!)
diffC = sp.simplify(sl.assumePosParams(noiseResultC.onoise - CnoiseResult.onoise))
print("Difference onoise full circuit and CM equivalent network:", diffC)
# Display the noise source names
print("Noise sources:")
for src in noiseResultC.onoiseTerms:
    print(src, ":", noiseResultC.snoiseTerms[src])
print("Common-mode noise sources contribution to CM onoise:")
for src in CnoiseResult.onoiseTerms:
    print(src, ":", CnoiseResult.snoiseTerms[src])

# Balanced dc variance analysis
dcvarAmp  = sl.makeCircuit("kicad/balancedAmpDCvar/balancedAmpDCvar.kicad_sch")

# Differential-mode output dc variance (complete circuit)
dcvarD    = sl.doDCvar(dcvarAmp)

# Common-mode output dc variance (complete circuit)
dcvarC    = sl.doDCvar(dcvarAmp, detector="V_comm")

# DM equivalent circuit
Ddcvar    = sl.doDCvar(dcvarAmp, convtype="dd")

# Show difference (should be zero!)
diffOvarD = sp.simplify(dcvarD.ovar - Ddcvar.ovar)
print("Difference ovar full circuit and DM equivalent network:", diffOvarD)
# Display the dc variance source names
print("DC variance sources:")
for src in dcvarD.ovarTerms:
    print(src, ":", dcvarD.ovarTerms[src])
print("Differential-mode dc variance sources contribution to DM dc variance:")
for src in Ddcvar.ovarTerms:
    print(src, ":", Ddcvar.ovarTerms[src])

# CM equivalent circuit
Cdcvar    = sl.doDCvar(dcvarAmp, convtype="cc")

# Show difference (should be zero!)
diffOvarC = sp.simplify(dcvarC.ovar - Cdcvar.ovar)
print("Difference ovar full circuit and CM equivalent network:", diffOvarC)
# Display the dcvariance source names
print("DC variance sources:")
for src in dcvarC.ovarTerms:
    print(src, ":", dcvarC.ovarTerms[src])
print("Common-mode dc variance sources contribution to CM dc variance:")
for src in Cdcvar.ovarTerms:
    print(src, ":", Cdcvar.ovarTerms[src])

# Generate RST snippets for the Help file
rst = sl.RSTformatter()
rst.matrixEqn(noneM.Iv, sp.simplify(sl.assumePosParams(noneM.M)), noneM.Dv).save("eqn-noneM")
rst.matrixEqn(allM.Iv, sp.simplify(sl.assumePosParams(allM.M)), allM.Dv).save("eqn-allM")
rst.matrixEqn(ddM.Iv, sp.simplify(sl.assumePosParams(ddM.M)), ddM.Dv).save("eqn-ddM")
rst.matrixEqn(dcM.Iv, sp.simplify(sl.assumePosParams(dcM.M)), dcM.Dv).save("eqn-dcM")
rst.matrixEqn(cdM.Iv, sp.simplify(sl.assumePosParams(cdM.M)), cdM.Dv).save("eqn-cdM")
rst.matrixEqn(ccM.Iv, sp.simplify(sl.assumePosParams(ccM.M)), ccM.Dv).save("eqn-ccM")
rst.eqn("A", allM.A).save("eqn-matA")
rst.matrixEqn(VampAll.Iv, VampAll.M, VampAll.Dv).save("eqn-VampAll")
rst.matrixEqn(BJTampAllF.Iv, BJTampAllF.M, BJTampAllF.Dv).save("eqn-BJTampAllMF")
rst.matrixEqn(BJTampAllT.Iv, BJTampAllT.M, BJTampAllT.Dv).save("eqn-BJTampAllMT")
rst.eqn("A_vdd", BJTampDD).save("eqn-AvddBJT")
rst.eqn("A_vcc", BJTampCC).save("eqn-AvccBJT")
rst.pz(poles).save("table-polesVamp")
rst.pz(zeros).save("table-zerosVamp")
rst.pz(pz).save("table-poleszerosVamp")
rst.pz(pzdd).save("table-poleszerosVampdd")
rst.pz(pzcc).save("table-poleszerosVampcc")
rst.eqn("S_vD", noiseResultD.onoise, multiline=1, units="V**2/Hz").save("eqn-DMnoise")
rst.eqn("S_vC", noiseResultC.onoise, multiline=1, units="V**2/Hz").save("eqn-CMnoise")
rst.eqn("var_vD", dcvarD.ovar, multiline=1, units="V**2").save("eqn-DMvar")
rst.eqn("var_vC", dcvarC.ovar, units="V**2").save("eqn-CMvar")
# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()