#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ngspice.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

# Create SPICE netlist
fileName = "VampQspice"
netlist  = sl.makeCircuit("kicad/" + fileName + "/" + fileName + ".kicad_sch", 
                         language="SPICE")

# DC sweep
simCmd  = "DC V2 6 12 1"
names   = {"V_c2": "V(c2)", "V_e2":"V(e2)"}
DC, x_name, x_units = sl.ngspice2traces("cir/" + fileName, simCmd, names)

# DC plot 
sl.plot("VampQspiceDC", "DC voltages $V_{c2}$, $V_{e2}$ versus power supply", 
        "lin", DC, xName=x_name, xUnits="V", yUnits="V")

# AC simulation, dBmag and phase, stepped
simCmd  = "AC DEC 50 5 10MEG" 
stepCmd = "C_c LIN 2p 20p 10"
names   = {"V_out": "V(out)"}
mag, phase, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, 
                                                 names, stepCmd=stepCmd, 
                                                 traceType='dBmagPhase')

# dB magnitude plot
sl.plot("VampQspiceM", "dBmag($V_{out}$)", "semilogx", mag , xName=x_name, 
        xUnits=x_units, yUnits="dB")

# Phase plot
sl.plot("VampQspiceP", "arg($V_{out}$)", "semilogx", 
        phase, xName=x_name, xUnits=x_units, yUnits="deg")

# TRAN simumlation, stepped
simCmd  = "TRAN 1n 1u"
stepCmd = "C_c LIN 2p 20p 10"
names   = {"V_out": "V(out)"}
tran, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, names, 
                                           stepCmd=stepCmd)
# Time plot
sl.plot("VampQspiceT1", "Pulse $V_{out}$, stepped $C_c$", "lin", 
        tran, xName=x_name, xUnits=x_units, xScale="u", yUnits="V")

# TRAN simumlation, multiple traces
simCmd  = "TRAN 1n 1u"
names   = {"V_out": "V(out)", "V_in": "V(in)", "V_c2": "V(c2)"}
tran, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, names)

# Time plot
sl.plot("VampQspiceT2", "Pulse $V_{out}$, $C_c$=18pF", "lin", tran, 
        xName=x_name, xUnits=x_units, xScale="u", yUnits="V")

# Change the netlist: change pulse to sinewave with parameter V_p amplitude
netlist = netlist.replace("PULSE 0 0.3 0 1n 1n 499n 1u", 
                          "SIN 0 {V_p} 100k\n" +
                          ".param V_p=1")
f = open("cir/VampQspice.cir", "w")
f.write(netlist)
f.close()

# TRAN simumlation, multiple traces and parameter stepping
simCmd  = "TRAN 10n 20u"
stepCmd = "V_p LIN 0.5 1 2"
names   = {"V_out": "V(out)", "V_in": "V(in)", "V_c2": "V(c2)"}
sine, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, 
                                           names, stepCmd=stepCmd)

# Time plot
sl.plot("VampQspiceS", "Sine overdrive $V_{out}$, $C_c$=18pF", "lin", sine, 
        xName=x_name, xUnits=x_units, xScale="u", yUnits="V")

# DC TEMP sweep
simCmd  = "DC TEMP -55 125 5"
names   = {"V_c2": "V(c2)", "V_e2":"V(e2)"}
TMP, x_name, x_units = sl.ngspice2traces("cir/" + fileName, simCmd, names)

# TEMP plot 
sl.plot("VampQspiceTMP", "DC voltages $V_{c2}$, $V_{e2}$ versus temperature", 
        "lin", TMP, xName=x_name, xUnits="Celsius", yUnits="V")

# NOISE analysis
simCmd  = "NOISE V(out) V1 dec 50 5 10MEG"
names   = {"S_vo": "onoise_spectrum", "S_vi": "inoise_spectrum"}
NOISE, x_name, x_units = sl.ngspice2traces("cir/" + fileName, simCmd, names, 
                                           squaredNoise=False)

# NOISE plot 
sl.plot("VampQspiceNOISE", "Noise input and output spectrum", 
        "log", NOISE, xName=x_name, xUnits="Hz", yUnits="$V/\\sqrt{Hz}$")

# Total noise versus temperature
simCmd  = "NOISE V(out) V1 dec 50 5 10MEG"
stepCmd = "TEMP LIN -55 125 50"
names   = {"v_no": "onoise_total"}
NOISETOT, x_name, x_units = sl.ngspice2traces("cir/" + fileName, simCmd, names, 
                                              stepCmd=stepCmd, 
                                              squaredNoise=False)
# TOTAL NOISE plot 
sl.plot("VampQspiceNOISETOT", "Total output noise versus temperature", "lin", 
        NOISETOT, xName=x_name, xUnits="Celsius", yUnits="V", yScale="u")

# Operating point analysis
simCmd  = "OP"
names   = {"V_c1": "V(c1)",
           "V_b1": "V(b1)",
           "V_e1": "V(e1)",
           "V_c2": "V(c2)",
           "V_e2": "V(e2)", 
           "I_V2": "I(V2)"}

OPinfo  = sl.ngspice2traces("cir/" + fileName, simCmd, names, stepCmd=None)

for name in OPinfo.keys():
    print(name, ":", OPinfo[name])
    
rst = sl.RSTformatter()
head = ["Name", "Value"]
rst.dictTable(OPinfo, head=head, caption="Bias voltages").save("table-VampQ-opinfo")

sl.backAnnotateSchematic("kicad/" + fileName + "/" + fileName + ".kicad_sch", 
                         OPinfo)

# TRAN with parameter substitution
simCmd   = "TRAN 0.1u 20u"
params   = [("V_p", 0.5)]
names    = {"V_out": "V(out)"}
tran, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, names, parList=params)
sl.plot("VampQspiceSIN", "$V_{out}$", "lin", tran , xName=x_name, xUnits=x_units,
        yUnits="V")

# FFT
simCmd   = "TRAN 1u 512u 64u 10n"
params   = [("V_p", 0.5)]
# Eliminate DC component from output
names    = {"V_AC_rms": "V(c2)-{}".format(str(OPinfo['V_c2']))}
postProc = """
set specwindow=gaussian
set specwindoworder=8
FFT V_AC_rms
"""
options  = {"RELTOL": 1e-6}
mag, phase, x_name, x_units  = sl.ngspice2traces("cir/" + fileName, simCmd, names, 
                                                 postProc=postProc, saveLog=True, 
                                                 traceType='magPhase', 
                                                 parList=params, optDict=options)
sl.plot("VampQspiceFFT", "$V_{out}$", "log", mag , xName=x_name, xUnits=x_units, 
        yUnits="V", xLim=[10e3, 1e6], yLim=[2e-7, 2])

# FOURIER
simCmd   = "TRAN 1u 512u 64u 10n"
params   = [("V_p", 0.5)]
# Eliminate DC component from output
names    = {"V_AC": "V(c2)-{}".format(str(OPinfo['V_c2']))}
postProc = "FOURIER 100k V_AC"
options  = {"RELTOL": 1e-6}
results  = sl.ngspice2traces("cir/" + fileName, simCmd, names, optDict=options, 
                             postProc=postProc, saveLog=True, parList=params)