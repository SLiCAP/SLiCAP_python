#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ngspice.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

fileName = "VampQspice"

# Operating point: NGspice writes cir/VampQspice_op.raw, which the schematic
# export reads for the bias annotations on the schematic
OP = sl.op(fileName)

# Netlist, schematic image with the bias annotations, and HTML circuit page
netlist = sl.makeCircuit("sch/" + fileName + ".spice_sch")

# Operating point information: the result holds every saved NGspice vector
# under its NGspice name; pick the ones of interest under names of your own
opNames = {"V_c1": "v(1)", "V_b1": "v(indc)", "V_e1": "v(4)",
           "V_c2": "v(outdc)", "V_e2": "v(2)", "I_V2": "i(v2)"}
OPinfo  = {name: OP.op[vector] for name, vector in opNames.items()}
for name in OPinfo.keys():
    print(name, ":", OPinfo[name])

rst  = sl.RSTformatter()
head = ["Name", "Value"]
rst.dictTable(OPinfo, head=head,
              caption="Bias voltages and currents").save("table-VampQ-opinfo")

# DC sweep of the supply voltage
DC = sl.dc(fileName, "V2", 6, 12, 1)
DCtraces = sl.make_traces(DC, [{"y": "V_c2", "label": "$V_{c2}$"},
                               {"y": "V_e2", "label": "$V_{e2}$"}],
                          variables={"V_c2": "v(outdc)", "V_e2": "v(2)"})
sl.plot("VampQspiceDC", "DC voltages $V_{c2}$, $V_{e2}$ versus power supply",
        "lin", DCtraces, xName="$V_S$", xUnits="V", yUnits="V")

# AC analysis with parameter stepping
AC = sl.ac(fileName, "dec", 50, 5, "10M",
           step={"param": "C_c", "method": "lin",
                 "start": "2p", "stop": "20p", "num": 10})
mag = sl.make_traces(AC, [{"y": "dB(V_out)", "label": "$V_{out}$"}],
                     variables={"V_out": "v(out)"})
sl.plot("VampQspiceM", "dBmag($V_{out}$)", "semilogx", mag,
        xName="frequency", xUnits="Hz", yUnits="dB")
phs = sl.make_traces(AC, [{"y": "phase(V_out)", "label": "$V_{out}$"}],
                     variables={"V_out": "v(out)"})
sl.plot("VampQspiceP", "arg($V_{out}$)", "semilogx", phs,
        xName="frequency", xUnits="Hz", yUnits="deg")

# Transient analysis with parameter stepping
TR = sl.tran(fileName, "1n", "1u",
             step={"param": "C_c", "method": "lin",
                   "start": "2p", "stop": "20p", "num": 10})
tran = sl.make_traces(TR, [{"y": "V_out", "label": "$V_{out}$"}],
                      variables={"V_out": "v(out)"})
sl.plot("VampQspiceT1", "Pulse $V_{out}$, stepped $C_c$", "lin", tran,
        xName="time", xUnits="s", xScale="u", yUnits="V")

# Transient analysis, several signals
TR = sl.tran(fileName, "1n", "1u")
tran = sl.make_traces(TR, [{"y": "V_out", "label": "$V_{out}$"},
                           {"y": "V_in", "label": "$V_{in}$"},
                           {"y": "V_c2", "label": "$V_{c2}$"}],
                      variables={"V_out": "v(out)", "V_in": "v(5)",
                                 "V_c2": "v(outdc)"})
sl.plot("VampQspiceT2", "Pulse $V_{out}$, $C_c$=18pF", "lin", tran,
        xName="time", xUnits="s", xScale="u", yUnits="V")

# Change the stimulus of a source for one run: a sine with a stepped
# amplitude instead of the pulse of the schematic
TR = sl.tran(fileName, "10n", "20u",
             stimuli={"V1": ["SIN", 0, "{V_p}", "100k"]},
             params=[("V_p", 1)],
             step={"param": "V_p", "method": "lin",
                   "start": 0.5, "stop": 1, "num": 2})
sine = sl.make_traces(TR, [{"y": "V_out", "label": "$V_{out}$"},
                           {"y": "V_in", "label": "$V_{in}$"},
                           {"y": "V_c2", "label": "$V_{c2}$"}],
                      variables={"V_out": "v(out)", "V_in": "v(5)",
                                 "V_c2": "v(outdc)"})
sl.plot("VampQspiceS", "Sine overdrive $V_{out}$, $C_c$=18pF", "lin", sine,
        xName="time", xUnits="s", xScale="u", yUnits="V")

# DC temperature sweep
TMP = sl.dc(fileName, "TEMP", -55, 125, 5)
tmp = sl.make_traces(TMP, [{"y": "V_c2", "label": "$V_{c2}$"},
                           {"y": "V_e2", "label": "$V_{e2}$"}],
                     variables={"V_c2": "v(outdc)", "V_e2": "v(2)"})
sl.plot("VampQspiceTMP", "DC voltages $V_{c2}$, $V_{e2}$ versus temperature",
        "lin", tmp, xName="temperature", xUnits="Celsius", yUnits="V")

# Noise analysis: NGspice returns the spectral densities in V^2/Hz
NOISE = sl.noise(fileName, "V(out)", "V1", "dec", 50, 5, "10M")
noise = sl.make_traces(NOISE, [{"y": "sqrt(S_vo)", "label": "$S_{vo}$"},
                               {"y": "sqrt(S_vi)", "label": "$S_{vi}$"}],
                       variables={"S_vo": "onoise_spectrum",
                                  "S_vi": "inoise_spectrum"})
sl.plot("VampQspiceNOISE", "Noise input and output spectrum", "log", noise,
        xName="frequency", xUnits="Hz", yUnits="V/sqrt(Hz)")

# Total output noise: the RMS_NOISE goal function integrates the spectrum
v_no = sl.measure(NOISE, "RMS_NOISE(onoise_spectrum)", units="V")
print("Total output noise:", v_no)

# Total output noise versus temperature: a stepped noise analysis reduced
# to one value per run gives a trace over the step values
NOISE = sl.noise(fileName, "V(out)", "V1", "dec", 50, 5, "10M",
                 step={"param": "TEMP", "method": "lin",
                       "start": -55, "stop": 125, "num": 19})
noisetot = sl.make_traces(NOISE, [{"y": "RMS_NOISE(S_vo)", "label": "$v_{no}$"}],
                          variables={"S_vo": "onoise_spectrum"})
sl.plot("VampQspiceNOISETOT", "Total output noise versus temperature", "lin",
        noisetot, xName="temperature", xUnits="Celsius", yUnits="V", yScale="u")

# Transient analysis with parameter substitution
TR = sl.tran(fileName, "0.1u", "20u",
             stimuli={"V1": ["SIN", 0, "{V_p}", "100k"]},
             params=[("V_p", 0.5)])
tran = sl.make_traces(TR, [{"y": "V_out", "label": "$V_{out}$"}],
                      variables={"V_out": "v(out)"})
sl.plot("VampQspiceSIN", "$V_{out}$", "lin", tran,
        xName="time", xUnits="s", xScale="u", yUnits="V")

# FFT of the collector voltage of Q2 with its operating point removed
FFT = sl.tran(fileName, "0.5u", "512u", tstart="64u", tmax="10n",
              stimuli={"V1": ["SIN", 0, "{V_p}", "100k"]}, params=[("V_p", 0.5)],
              save=["v_ac = v(outdc) - {}".format(OPinfo["V_c2"])],
              fft={"window": "gaussian", "order": 8}, options={"RELTOL": 1e-6})
spectrum = sl.make_traces(FFT, [{"y": "V_c2", "label": "$V_{c2}$"}],
                          variables={"V_c2": "v_ac"})
sl.plot("VampQspiceFFT", "Spectrum of $V_{c2}$", "log", spectrum,
        xName="frequency", xUnits="Hz", yUnits="V",
        xLim=[10e3, 1e6], yLim=[2e-7, 2])

# Fourier analysis of the collector voltage of Q2
FOURIER = sl.tran(fileName, "1u", "512u", tstart="64u", tmax="10n",
                  stimuli={"V1": ["SIN", 0, "{V_p}", "100k"]}, params=[("V_p", 0.5)],
                  save=["v_ac = v(outdc) - {}".format(OPinfo["V_c2"])],
                  fourier="100k", options={"RELTOL": 1e-6})
print(FOURIER.fourier["table"])
