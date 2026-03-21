#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
balanced.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp
###############################################################################
# work with feedback circuits
###############################################################################

# Circuit for ideal gain
vamp_ideal = sl.makeCircuit("kicad/VampIdeal/VampIdeal.kicad_sch")

# Implementation of the controller with an operational amplifier
vamp_opamp = sl.makeCircuit("kicad/VampOV/VampOV.kicad_sch")

# Ideal gain
ideal_gain_sym = sl.doLaplace(vamp_ideal).laplace

# Asymptotic_gain OpAmp circuit
asympt_gain_OV =  sl.doLaplace(vamp_opamp, transfer="asymptotic").laplace

# Asymptotic-gain == ideal gain:
c_c = sp.Symbol("c_c")
asympt_gain_OV_mod = asympt_gain_OV .subs(c_c, 0)

# Loop gain OpAmp circuit
loop_gain_OV =  sl.doLaplace(vamp_opamp, transfer="loopgain").laplace

# Servo function OpAmp circuit
servo_OV =  sl.doLaplace(vamp_opamp, transfer="servo").laplace

# Direct transfer OpAmp circuit
direct_OV =  sl.doLaplace(vamp_opamp, transfer="direct").laplace

# Gain OpAmp circuit
gain_OV =  sp.simplify(sl.doLaplace(vamp_opamp).laplace)

# Show that MNA gives the same result as the asymptotic-gain model
# Calculate gain according to the symptotic-gain model
gain_fb = sp.simplify(asympt_gain_OV*servo_OV + direct_OV/(1-loop_gain_OV))
# Take ratio of the two gains (must be unity)
ratio = gain_OV/gain_fb
# Calculate difference between expanded numerator and expanded denominator
# This difference must be zero!
numer, denom = ratio.as_numer_denom()
diff = sp.expand(numer) - sp.expand(denom)

if diff == 0:
    print("PERFECT: The two models give the same source-load transfer!")
else:
    print("ERROR: MNA gain result differs from asymptotic-gain model!")

# Numeric values for plotting
paramsO = {"A_0": 1e5,
          "p_1": -100,
          "R_o": "5k",
          "c_c": "1p",
          "c_d": "8p",
          "R_s": "100k",
          "R_a": "250k",
          "R_b": "50k",
          "R_L": "1k",
          "C_L": "500p"}

IO = sl.doLaplace(vamp_ideal, transfer="gain", pardefs=paramsO, numeric=True)
IO.gainType = "ideal" # This is to change the color and the name of the trace
GO = sl.doLaplace(vamp_opamp, transfer="gain", pardefs=paramsO, numeric=True)
AO = sl.doLaplace(vamp_opamp, transfer="asymptotic", pardefs=paramsO, numeric=True)
LO = sl.doLaplace(vamp_opamp, transfer="loopgain", pardefs=paramsO, numeric=True)
SO = sl.doLaplace(vamp_opamp, transfer="servo", pardefs=paramsO, numeric=True)
DO = sl.doLaplace(vamp_opamp, transfer="direct", pardefs=paramsO, numeric=True)

sl.plotSweep("AvOVfb_mag", "Feedback model dB magnitude transfers", 
             [IO, AO, LO, SO, DO, GO], 50, 50e6, 200, funcType="dBmag")
sl.plotSweep("AvOVfb_phase", "Feedback model phase transfers", 
             [IO, AO, LO, SO, DO, GO], 50, 50e6, 200, funcType="phase")

# Implementation of the controller with bipolar transistors
vamp_bjt   = sl.makeCircuit("kicad/VampQ/VampQ.kicad_sch")

# Asymptotic_gain transistor circuit
asympt_gain_QV =  sl.doLaplace(vamp_bjt, transfer="asymptotic").laplace
# Show the coefficients because the expression is too long!
transferCoeffs = sl.coeffsTransfer(asympt_gain_QV)

# Asymptotic-gain == ideal gain:
c_mu_1, g_o_1, c_mu_2 = sp.symbols('c_mu_1, g_o_1, c_mu_2')
asympt_gain_QV_mod = sp.simplify(asympt_gain_QV.subs({c_mu_1: 0, g_o_1: 0, c_mu_2: 0}))

# Numeric values for plotting
paramsQ = {"g_m_1": "4m",
          "g_m_2": "10m",
          "beta_AC_1": 100,
          "beta_AC_2": 100,
          "g_o_1": "2u",
          "g_o_2": "10u",
          "c_pi_1": "5p",
          "c_pi_2": "10p",
          "c_mu_1": "1p",
          "c_mu_2": "1p",
          "R_s": 100,
          "R_a": 950,
          "R_b": 50,
          "R_L": "1k",
          "C_L": "500p"}

IQ = sl.doLaplace(vamp_ideal, transfer="gain", pardefs=paramsQ, numeric=True)
IQ.gainType = "ideal" # This is to change the color and the name of the trace
GQ = sl.doLaplace(vamp_bjt, transfer="gain", pardefs=paramsQ, numeric=True)
AQ = sl.doLaplace(vamp_bjt, transfer="asymptotic", pardefs=paramsQ, numeric=True)
LQ = sl.doLaplace(vamp_bjt, transfer="loopgain", pardefs=paramsQ, numeric=True)
SQ = sl.doLaplace(vamp_bjt, transfer="servo", pardefs=paramsQ, numeric=True)
DQ = sl.doLaplace(vamp_bjt, transfer="direct", pardefs=paramsQ, numeric=True)

sl.plotSweep("AvQVfb_mag", "Feedback model dB magnitude transfers", 
             [IQ, AQ, LQ, SQ, DQ, GQ], 0.05, 5e3, 200, sweepScale="M",
             funcType="dBmag")
sl.plotSweep("AvQVfb_phase", "Feedback model phase transfers", 
             [IQ, AQ, LQ, SQ, DQ, GQ], 0.05, 5e3, 200, sweepScale="M", 
             funcType="phase")

pzResult = sl.doPZ(vamp_bjt, pardefs=paramsQ, numeric=True)
sl.listPZ(pzResult)

# Influence of output-stage current on poles
paramsQ["g_m_2"] = sp.Symbol("I_C")/26e-3
paramsQ["c_pi_2"] = sp.sympify("2e-12 + g_m_2*tau_F")
paramsQ["tau_F"]  = 1/(2*sp.pi*195e6)
paramsQ["I_C"] = 260e-6
# Define these parameters as "circuit" parameters (required for stepping)
vamp_bjt.defPars(paramsQ)

stparams = {"start": "0.26m",
            "stop" : "10m",
            "method": "lin",
            "params": "I_C",
            "num": 50}

polesIC = sl.doPoles(vamp_bjt, pardefs='circuit', stepdict=stparams, numeric=True)

sl.plotPZ("PZvampbjtIC", "Poles versus $I_C$", polesIC, xmin=-7, 
          xmax=0, ymin=-3.5, ymax=3.5, xscale="M", yscale="M")

num, den    = GQ.laplace.as_numer_denom() # Extract denominator
RA          = sl.routh(den)               # Create Routh Array of denominator
sign        = sp.sign(RA[0,0])            # Record sign of RA[0,0]
sgn_changes = 0                           # Number of sign changes is number of
for r in range(1, RA.rows):               # right half-plane poles
    new_sign = sp.sign(RA[r, 0])
    if  new_sign != sign:
        sgn_changes += 1
        sign = new_sign
print("Number of poles in right half-plane:", sgn_changes)

# Traditional Nyquist Plot: change the sign of the loop gain!
loopGain   = LQ.laplace
LQ.laplace = -loopGain
sl.plotSweep("NyquistQamp", "Nyquist plot loop gain QVamp", LQ, 1, 10, 200, 
             sweepScale="M", funcType="mag", axisType="polar")

# findServoBandwidth
servoInfo = sl.findServoBandwidth(loopGain)
for key in servoInfo.keys():
    print(key, servoInfo[key])
    
# Dominant poles and zeros of the loop gain for low-pass cut-off
pzL = sl.doPZ(vamp_bjt, transfer="loopgain", pardefs=paramsQ, numeric=True)
dom_poles = []
dom_zeros = []
margin    = 2
for pole in pzL.poles:
    freq = sp.Abs(pole)/(2*sp.pi)
    if  freq < margin * servoInfo['lpf'] and freq > servoInfo['mbf']:
        dom_poles.append(pole)
for zero in pzL.zeros:
    freq = sp.Abs(zero)/(2*sp.pi)
    if freq < margin * servoInfo['lpf'] and freq > servoInfo['mbf']:
        dom_zeros.append(zero)
print("Poles [rad/s]:", dom_poles)
print("Zeros [rad/s]:", dom_zeros)

LoopGain_simplified = servoInfo['mbv']
for zero in dom_zeros:
    LoopGain_simplified *= (1-sl.ini.laplace/zero)
for pole in dom_poles:
    LoopGain_simplified /= (1-sl.ini.laplace/pole)

gain, numerCoeffs, denomCoeffs = sl.coeffsTransfer(LoopGain_simplified)   
order = len(numerCoeffs) - len(denomCoeffs) 
MFM   = (1/(2*sp.pi))*((1 + gain)*numerCoeffs[-1]/denomCoeffs[-1])**(-1/order)
print("Achievable MFM bandwidth:", sp.N(MFM, 3), "Hz")

# Generate RST snippets for the Help file
rst = sl.RSTformatter()
rst.eqn("A_v_Ideal", ideal_gain_sym).save("eqn-A_v_Ideal")
rst.eqn("A_v_oo", asympt_gain_OV).save("eqn-OV-A_v_oo")
rst.eqn("A_vi_oo", asympt_gain_OV_mod).save("eqn-OV-A_v_oo-mod")
rst.coeffsTransfer(transferCoeffs).save("table-coeffsQ-A_v_oo")
rst.eqn("A_vi_oo", asympt_gain_QV_mod).save("eqn-QV-A_v_oo-mod")
rst.eqn("RA", RA).save("eqn-M_routh")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()
ltx.eqn("A_v_Ideal", ideal_gain_sym).save("eqn-A_v_Ideal")
ltx.eqn("A_v_oo", asympt_gain_OV).save("eqn-OV-A_v_oo")
ltx.eqn("A_vi_oo", asympt_gain_OV_mod).save("eqn-OV-A_v_oo-mod")
ltx.coeffsTransfer(transferCoeffs).save("table-coeffsQ-A_v_oo")
ltx.eqn("A_vi_oo", asympt_gain_QV_mod).save("eqn-QV-A_v_oo-mod")
ltx.eqn("RA", RA).save("eqn-M_routh")