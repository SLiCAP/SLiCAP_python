#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 20:05:45 2024

@author: anton

This file requires SLiCAP_V3
"""

import SLiCAP as sl
import sympy as sp

# Define all the paths, create the HTML main index page, reset the parser, and
# compile the SLiCAP libraries.

prj = sl.initProject('My first RC network') 

# Create a circuit object from a schematic file or a SLiCAP netlist:
fileName = "myFirstRCnetwork"

# KiCAD version 8.0 + 
fileName = 'kicad/' + fileName + '/' + fileName + '.kicad_sch'

# LTspice
#fileName = ini.cir_path + fileName + '.asc'

# gSchem or lepton-eda
#fileName = 'lepton-eda/' + fileName + '.sch'

# Use existing netlist that resides in the ini.cir_path directory
#fileName = fileName + '.cir'

cir = sl.makeCircuit(fileName, imgWidth=400)

# Let us define an instruction to display the symbolic MNA matrix equation.
MNA = sl.doMatrix(cir)

# We will put the instruction on a new HTML page and display it in this notebook
sl.htmlPage('Matrix equations')
# Let us put some explaining text in the report:
sl.text2html('The MNA matrix equation for the RC network is:')
sl.matrices2html(MNA, label = 'MNA', labelText = 'MNA equation of the network')
# The variables in this equation are available in the variable that holds
# the result of the execution:
#
# 1. The vector 'Iv' with independent variables:
sl.text2html('The vector with independent variables is:')
sl.eqn2html('I_v', MNA.Iv, label = 'Iv', labelText = 'Vector with independent variables')
# 2. The matrix 'M':
sl.text2html('The MNA matrix is:')
sl.eqn2html('M', MNA.M, label = 'M', labelText = 'MNA matrix')
# 3. The vercor wit dependent variables 'Dv':
sl.text2html('The vector with dependent variables is:')
sl.eqn2html('D_v', MNA.Dv, label = 'Dv', labelText = 'Vector with dependent variables')

# Let us now evaluate the transfer function of this network.
gain = sl.doLaplace(cir)
# The laplace transform can now be found in the attribute 'laplace' of 'gain'.
sl.eqn2html('V_out/V_1', gain.laplace, label = 'gainLaplace', labelText = 'Laplace transfer function')
# The parameters 'R' and 'C' stem from the circuit, while 's' is defined as the Laplace variable:
print(sl.ini.laplace)
# SLiCAP has a lot of predefined plots. The results of an analysis with data type 'laplace' can
# graphically be represented with:
# 1. magnitude plots versus frequency
# 2. dB magnitude plots versus frequency
# 3. phase plots versus frequency
# 4. (group) delay plots versus frequency
# For plotting we need numeric values, this is achieved by recursive 
# substitution of all circuit parameters; use kwarg: pardefs='circuit'
numGain = sl.doLaplace(cir, pardefs='circuit')
# We will create a new HTML page for the plots
sl.htmlPage('Plots')
sl.head2html('Frequency domain plots')
figMag = sl.plotSweep('RCmag', 'Magnitude characteristic', numGain, 10, '100k', 100, yUnits = '-', show = False)
# This will put the figure on the HTML page with a width of 800 pixels, a caption and a label:
sl.fig2html(figMag, 600, caption = 'Magnitude characteristic of the RC network.', label = 'figMag')
figPol = sl.plotSweep('RCpolar', 'Polar plot', numGain, 10, '100k', 100, axisType = 'polar', show = False)
sl.fig2html(figPol, 600, caption = 'Polar plot of the transfer of the RC network.', label = 'figPolar')
figdBmag = sl.plotSweep('RCdBmag', 'dB magnitude characteristic', numGain, 10, '100k', 100, funcType = 'dBmag', show = False)
sl.fig2html(figdBmag, 600, caption = 'dB Magnitude characteristic of the RC network.', label = 'figdBmag')
figPhase = sl.plotSweep('RCphase', 'Phase characteristic', numGain, 10, '100k', 100, funcType = 'phase', show = False)
sl.fig2html(figPhase, 600, caption = 'Phase characteristic of the RC network.', label = 'figPhase')
# We will display the delay in 'us'
figDelay = sl.plotSweep('RCdelay', 'Group delay characteristic', numGain, 10, '100k', 100, yScale = 'u', funcType = 'delay')
sl.fig2html(figDelay, 600, caption = 'Group delay characteristic of the RC network.', label = 'figDelay')
# With data type: 'pz' we can calculate the DC value of the gain and the poles and the zeros.
# Symbolic pole-zero analysis is supported for relatively simple networks.
pzResult = sl.doPZ(cir)
pzGain = sl.doPZ(cir, pardefs = 'circuit')
# We will create a new HTML page for displaying the results and display them also in this notebook.
sl.htmlPage('Poles and zeros')
sl.pz2html(pzResult, label = 'PZlistSym', labelText = 'Symbolic values of the poles and zeros of the network')
sl.pz2html(pzGain, label = 'PZlist', labelText = 'Poles and zeros of the network')
# Let us also add a pole-zero plot of these results:
sl.head2html("Complex frequency domain plots")
figPZ = sl.plotPZ('PZ', 'Poles and zeros of the RC network', pzGain)
# You can also set the range and the units of the axes of this plot:
# We will redefine the figure object 'figPZ'
figPZ = sl.plotPZ('PZ', 'Poles and zeros of the RC network', pzGain, xmin = -1.9, xmax = 0.1, ymin = -1, ymax = 1, xscale = 'k', yscale = 'k')
sl.fig2html(figPZ, 600, caption = 'Poles and zeros of the RC network.', label = 'figPZ');
# The data types 'poles' and 'zeros' can be used to calculate the poles and the zeros separately.
# The difference with data type 'pz' is that the latter one cancels poles and zeros that coincide
# withing the display accuracy (ini.disp) and calculated the zero-frequency value of the transfer.
# Displaying the result of all three data types gives you the DC gain and the non observable poles.
#
# With data types 'impulse' and 'step' you can calculate the impulse response and the step response
# of the network, respectively. These responses are obtained from the inverse Laplace transform of
# the transfer function (impulse response) or the transfer function multiplied with 1/ini.Laplace.
numStep = sl.doStep(cir, pardefs="circuit")
figStep = sl.plotSweep('step', 'Unit step response', numStep, 0, 1, 50, sweepScale='m', show = False)
# Let us put this plot on the page with the plots. You can get a list with page names by typing: 'ini.htmlPages'
sl.ini.htmlPage = 'myFirstRCnetwork_Plots.html'
sl.head2html('Time domain plots')
sl.fig2html(figStep, 600, caption = 'Unit step response of the RC network.', label = 'figStep')
# SLiCAP is developed for setting up and solving circuit design equations
# In the following section we will write the values of the circuit
# components as a function of the setting time to n bit.
# The procedure is as follows:
# 1. Get a symbolic expression of the output voltage as a function of time
# 2. Get a symbolic expression for the settling error delta_t as function of time
# 3. Find the settling tau_s by solving: delta_t = 2^(-n)
# 4. Find the design equations for  the component values:
#    a. Write the resistance 'R_R1' as a function of 'n', 'tau_s' and 'C'
#    b. Write the capacitance 'C_R1' as a function of 'n', 'tau_s' and 'R'
#
# Let us first create a new page for the above:
sl.htmlPage('Design equations for $R$ and $C$', label='desEq')
sl.head2html('The unit step response')

# Step 1:
symStep = sl.doStep(cir)
mu_t = sp.Symbol('mu_t')
sl.eqn2html(mu_t, symStep.stepResp, label = 'mu_t', labelText = 'Symbolic expression of the unit step response')

# Step 2:
sl.head2html("The settling error versus time")
t = sp.Symbol('t', positive = True)
# Redefine all symbols in the expression as positive
stepResp = sl.assumePosParams(symStep.stepResp)
settlingError = sp.limit(stepResp, t, 'oo') - stepResp
epsilon_t     = sp.Symbol('epsilon_t')
sl.eqn2html(epsilon_t, settlingError, label = 'epsilon_t', labelText = 'Symbolic expression of the settling error versus time')

# Step 3:
sl.head2html("The n-bit settling time")
n             = sp.Symbol('n', positive = True)
settlingTime  = sp.solve(settlingError - 2**(-n), t)[0] # In this case there is only one solution
tau_s         = sp.Symbol('tau_s', positive = True)
sl.eqn2html(tau_s, settlingTime, label = 'tau_s', labelText = 'Symbolic expression of the settling time')

# Step 4a:
sl.head2html("The design equation for $R$")
R    = sp.Symbol('R', positive = True)
RR1  = sp.solve(settlingTime - tau_s, R)[0] # In this case there is only one solution
sl.eqn2html(R, RR1, label = 'RR1', labelText = 'Design equation for $R$')

# Step 4b:
sl.head2html("The design equation for $C$")
C    = sp.Symbol('C', positive = True)
CC1  = sp.solve(settlingTime - tau_s, C)[0] # In this case there is only one solution
sl.eqn2html(C, CC1, label = 'CC1', labelText = 'Design equation for $C$')
sl.head2html("Numeric example.")
sl.text2html("We will determine R for the case in which we need 10 bit settling within 100ns with a capacitance C=10pF. We obtain:")
Rvalue = sp.N(RR1.subs([(tau_s, 100e-9), (n, 10), (C, 1e-11)]), sl.ini.disp)
sl.eqn2html(R, Rvalue, label = 'Rvalue', labelText = 'Numeric value of $R$')
#
sl.links2html()