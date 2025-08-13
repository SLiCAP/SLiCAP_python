#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plots.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
from copy import deepcopy
import numpy as np

cir = sl.makeCircuit("kicad/myPassiveNetwork/myPassiveNetwork.kicad_sch")

# Swept variable plots
# Laplace analysis
laplaceResult = sl.doLaplace(cir, pardefs="circuit", numeric=True)

# Magnitude
f_mag = sl.plotSweep("f_mag", "Magnitude plot", laplaceResult, 0.01, 100, 500, 
                     sweepScale="M", yUnits="V")

# dB Magnitude
f_dBm = sl.plotSweep("f_dBm", "dB magnitude plot", laplaceResult, 0.01, 100, 
                     500, sweepScale="M", yUnits="V", funcType="dBmag")

# Phase
f_phs = sl.plotSweep("f_phs", "Phase plot", laplaceResult, 0.01, 100, 500, 
                     sweepScale="M", yUnits="V", funcType="phase")

# Group delay
f_del = sl.plotSweep("f_del", "Group delay plot", laplaceResult, 0.01, 100, 
                     500, sweepScale="M", yUnits="V", yScale="u", 
                     funcType="delay")

# Magnitude-polar
p_mag = sl.plotSweep("p_mag", "Magnitude-phase plot", laplaceResult, 0.01, 100,
                     500, axisType="polar", sweepScale="M", yUnits="V")

# dB magnitude-polar
p_dBm = sl.plotSweep("p_dBm", "dB magnitude-phase plot", laplaceResult, 0.01,
                     100, 500, axisType="polar", sweepScale="M", yUnits="V", 
                     funcType="dBmag")

# Time-domain analysis

# Impulse
impulseResp = sl.doImpulse(cir, pardefs="circuit", numeric=True)
delta_t = sl.plotSweep("delta_t", "Unit-impulse response", impulseResp, 
                       0, 5, 500, sweepScale="u", yScale="M")

# Step
stepResp = sl.doStep(cir, pardefs="circuit", numeric=True)
mu_t = sl.plotSweep("mu_t", "Unit-step response", stepResp, 0, 5, 500,
                     sweepScale="u")

# Time
timeResp = sl.doTime(cir, pardefs="circuit", numeric=True)
v_time = sl.plotSweep("v_time", "Time-domain response", timeResp, 0, 5, 500, 
                      sweepScale="u")

# Periodic pulse
stepResp.stepResp = sl.step2PeriodicPulse(stepResp.stepResp, 20e-9, 1e-6, 3)
stepResp.label    = "3 Pulses response"
pp_time = sl.plotSweep("pp_time", "Periodic pulse response", stepResp, 0, 5, 
                       1000, sweepScale="u")

# Noise spectrum
noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
onoise_f     = sl.plotSweep("onoise_f", "Detector-referred noise spectrum", 
                            noiseResult, 0.01, 100, 500, funcType="onoise", 
                            sweepScale="M", yUnits="$V^2/Hz$")

all_onoise_f = sl.plotSweep("all_onoise_f", "Contributions to detector-referred noise", 
                            noiseResult, 0.01, 100, 500, funcType="onoise", 
                            sweepScale="M", yUnits="$V^2/Hz$", 
                            noiseSources="all")

inoise_f     = sl.plotSweep("inoise_f", "Source-referred noise spectrum", 
                            noiseResult, 0.01, 100, 500, funcType="inoise", 
                            sweepScale="M", yUnits="$V^2/Hz$")

# Swept parameter plots
# Create an instruction result object for plotting
parResult = sl.doParams(cir) 
# Create the swept-parameter plot
Cb_fs = sl.plotSweep("Cb_fs", "$C_b$ versus $f_s$", parResult, 1, 5, 100, 
                     axisType="semilogy", funcType="param", sweepVar="f_s", 
                     sweepScale="M", xUnits="Hz", yVar="C_b", yScale="n", 
                     yUnits="F")

# Pole-zero plots
# Plot the poles
polesResult = sl.doPoles(cir, pardefs="circuit", numeric=True)
p_plot = sl.plotPZ("p_plot", "Poles", polesResult, xscale="M", yscale="M")

# Plot the zeros
zerosResult = sl.doZeros(cir, pardefs="circuit", numeric=True)
z_plot = sl.plotPZ("z_plot", "Zeros", zerosResult, xscale="M", yscale="M")

# Only observable and controllable
pzResult = sl.doPZ(cir, pardefs="circuit", numeric=True)
pz_plot = sl.plotPZ("pz_plot", "Observable and controllable poles and zeros", 
                    pzResult, xscale="M", yscale="M", xmin=-11, xmax=1,
                    ymin=-6, ymax=6)

# Multiple results in one plot
all_pz = sl.plotPZ("ppzz_plot", "All poles and zeros", 
                    [polesResult, zerosResult], xscale="M", yscale="M", 
                    xmin=-11, xmax=1, ymin=-6, ymax=6)

# Parameter stepping
# Define the step parameters
step_dict = {"params": "f_s",
             "method": "lin",
             "start":  "1M",
             "stop":   "5M",
             "num": 5}

# dB Magnitude stepped
laplaceStepped = sl.doLaplace(cir, pardefs="circuit", stepdict=step_dict, 
                              numeric=True)
f_dBmStepped = sl.plotSweep("f_dBmStepped", "dB magnitude plot", laplaceStepped,
                            0.01, 100, 500, sweepScale="M", yUnits="V", 
                            funcType="dBmag")

# Root-locus plots
pzStepped  = sl.doPZ(cir, pardefs="circuit", stepdict=step_dict, 
                              numeric=True)
pz_stepped = sl.plotPZ("pzStepped", "Stepped PZ plot", pzStepped, xscale="M", 
                      yscale="M", xmin=-11, xmax=1, ymin=-6, ymax=6)

# Stepped parameter sweep
# Define the step parameters
step_dict = {"params": "L",
             "method": "lin",
             "start":  "1u",
             "stop":   "5u",
             "num": 5}
# Create an instruction result object for plotting with parameter stepping
parResult = sl.doParams(cir, stepdict=step_dict) 
Cb_fs_L = sl.plotSweep("Cb_fs_L", "$C_b$ versus $f_s$", parResult, 1, 5, 100, 
                       axisType="semilogy", funcType="param", sweepVar="f_s", 
                       sweepScale="M", xUnits="Hz", yVar="C_b", yScale="n", 
                       yUnits="F")

# Extract traces from plots
onoise_trace = onoise_f.traceDict

# Add onoise_trace to a copy of all_onoise_f
# Create a deepcopy of the figure
all_oonoise_f = deepcopy(all_onoise_f)
# Change the file name so we don't overwrite the original
all_oonoise_f.fileName = "all_onoise"
# Add the onoise trace to the new figure
sl.traces2fig(onoise_trace, all_oonoise_f)
# Don't show it, just save the figure
all_oonoise_f.show = False
# Generate and save the figure
all_oonoise_f.plot()

# Create traces
x        = np.linspace(-1, 1, 100)

y1       = sl.trace([x, x])
y1.label = "$y=x$"

y2       = sl.trace([x, x**2])
y2.label = "$y=x^2$"

y3       = sl.trace([x, x**3])
y3.label = "$y=x^3$"

y4       = sl.trace([x, x**4])
y4.label = "$y=x^4$"

trc_dict = {"y1": y1, "y2": y2, "y3": y3, "y4": y4}

# Plot a dictionary with traces

pwrs_x   = sl.plot("powers_x", "Powers of $x$", "lin", trc_dict, 
                   xName = "x", yName="y")