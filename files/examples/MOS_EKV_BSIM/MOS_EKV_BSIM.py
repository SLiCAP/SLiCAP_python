#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 11:41:04 2023

@author: anton
"""
from SLiCAP import *
from extras import *

prj = initProject("MOS_EKV_BSIM")

# MS Windows: define the location of the ngspice.exe"
# ini.ngspiceCMD = '<path to ngspice.exe>'
# Example NMOS operating point info

# Define library and device
refDes   = 'M1'                     # Reference designator of MOS device
DEV      = 'nch'                    # MOS device name
LIB      = '.lib lib/log018.l TT'   # use this CMOS BSIM library with EKV CMOS-1.lib
#LIB      = '.inc lib/CMOS18TT.lib' # use this CMOS BSIM library with EKV CMOS-2.lib
W        = .22e-6                   # Channel width
L        = .18e-6                   # Channel length
M        = 1                        # Number of devices in parallel

# Define test frequency for determination of small-signal operating point parameters
f        = 10E6

# Define frequency range for noise analysis
fmin     = 10                  # Start frequency
fmax     = 10e9                # Stop frequency
numDec   = 20                  # Number of points per decade

# Define the N_Channel operating point
VD       = 1.2                 # Drain voltage w.r.t. GND
VG       = 0.5                 # Gate voltage w.r.t. GND
VP       = 1.8                 # Supply voltage w.r.t. GND
ID       = 100E-6               # Drain current

# Define the biasing step variable 'VGS' or "IDS". IDS > 1E-9 (convergence)
biasPar  = "IDS"               # Choose biasing with "VGS" or with "IDS"

# Define the number of steps (only linear step method implemented)
Npts     = 100                 # Number of points

# Define the absolute value of the step size Vdiff and Idiff for VGS od IDS stepping respectively.
Vdiff    = 0.01                # Gate voltage step size
Idiff    = 1e-6                # Drain current step size

####################################################################################################
# Create the device
device = MOS(refDes, LIB, DEV, W, L, M)

#calculate terminal voltages

if DEV == "pch":
    VS = VP
    VB = VP
    VG = VP - VG
    VD = VP - VD
else:
    VS = 0
    VB = 0
# print operating point information
printOPinfo(device, biasPar, ID, VG, VD, VS, VB, f)

# determine the step values
stepVals = createStep(device, biasPar, VS, ID, Npts, Vdiff, Idiff)

# plot the operating point information
plotOpinfo(device, biasPar, ID, VG, VD, VS, VB, f, stepVals, EKVlib = 'CMOS18-1.lib')

# plot the voltage noise
plotSvinoise(device, ID, VD, VS, VB, fmin, fmax, numDec, EKVlib = 'CMOS18-1.lib')