#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ttime.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp
# Circuit definition
ACcoupling = sl.makeCircuit("kicad/ACcoupling/ACcoupling.kicad_sch")

# Define parameter values
params = {"R_a": "1k",
          "R_b": "1k",
          "R_s": "50",
          "C_c": "1n",
          "f_s": "10M",
          "V_p": 2,
          "V_B": 5}

# Obtain the symbolic unit-impulse response of the power supply transfer
power_impulse_sym = sl.doImpulse(ACcoupling, source="V1").impulse

# Numeric unit-step response of the signal transfer
signal_impulse_num = sl.doImpulse(ACcoupling, pardefs=params, source="V2").impulse
print(signal_impulse_num)

# Obtain the symbolic unit-step response of the signal transfer
signal_step_sym = sl.doStep(ACcoupling, source="V2").stepResp

# Numeric unit-step response of the power supply transfer
power_step_num  = sl.doStep(ACcoupling, pardefs=params, source="V1").stepResp
print(power_step_num)

# Obtain the symbolic time-domain response
timeResult_sym = timeResult_num = sl.doTime(ACcoupling).time

# Numeric time-domain response
timeResult_num  = sl.doTime(ACcoupling, pardefs=params)

# Plot the numeric response
sl.plotSweep("AC_time", "Time-domain response", timeResult_num, 0, 2, 500, sweepScale="u") 

power_impulse = sl.doImpulse(ACcoupling, source="V1")
M             = power_impulse.M
Iv            = power_impulse.Iv
Dv            = power_impulse.Dv
denom         = power_impulse.denom
numer         = power_impulse.numer
transfer      = power_impulse.laplace

# Convert a step response into a periodic pulse response
# Example step response
step_resp  = sp.sympify("A*(1-exp(-t/tau_s))")
# Define pulse time 'tau_p' and pulse period 'T_p'
tau_p, T_p = sp.symbols("tau_p, T_p")
# Generate the response to 3 pulses
three_pulse_resp = sl.step2PeriodicPulse(step_resp, tau_p, T_p, 3)

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.eqn("h_p(t)", power_impulse_sym).save("eqn-ACcoupling-power-impulse")
rst.eqn("a_s(t)", signal_step_sym).save("eqn-ACcoupling-signal-step")
rst.eqn("V_out", timeResult_sym).save("eqn-ACcoupling-time")
rst.eqn("H_3p", three_pulse_resp, multiline=2).save("eqn-H_3p-time")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.eqn("h_p(t)", power_impulse_sym).save("eqn-ACcoupling-power-impulse")
ltx.eqn("a_s(t)", signal_step_sym).save("eqn-ACcoupling-signal-step")
ltx.eqn("V_out", timeResult_sym).save("eqn-ACcoupling-time")
ltx.eqn("H_3p", three_pulse_resp, multiline=1).save("eqn-H_3p-time")