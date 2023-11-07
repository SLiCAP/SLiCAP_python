#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 11:41:04 2023

@author: anton
"""

from SLiCAP import *

prj = initProject("MOS_EKV_BSIM")

# Example NMOS operating point info

# Define library, device, geometry and operating point
LIB    = 'lib/log018.l TT'
DEV    = 'pch'
W      = .22e-6
L      = .18e-6
M      = 1
f      = 10E6
refDes = 'M1'

# Define number of points and the absolute value of the gate step voltage
Npts   = 120
Vdiff  = 0.01

# Create the device
mn = MOS(refDes, LIB, DEV)

if DEV == "nch":
    VD   = 1.2
    VS   = 0
    VB   = 0
    VG   = 0
    step = [VS, Npts, Vdiff]

elif DEV == "pch":
    VD   = 0.6
    VS   = 1.8
    VB   = 1.8
    VG   = 1.8
    step = [VS, Npts, -Vdiff]

# Uncomment the following line to obtain single operating point information
#step=None

mn.getOPvg(W, L, M, VG, VD, VS, VB, f, step)

if step == None:
    print('\nParameters found by simulation:\n')
    for key in mn.params.keys():
        print(key, mn.params[key])

    print('\nSLiCAP model definition:\n')
    print(mn.modelDef)

    print('\nSLiCAP parameter definitions:\n')
    for key in mn.parDefs.keys():
        print(key, mn.parDefs[key])

    print('\nRelative errors:\n')
    for key in mn.errors.keys():
        print(key, mn.errors[key])

    print('\nDerived parameters:\n')
    print('fT\t', mn.params['ggd']/(2*np.pi*mn.params['cgg']))
    print('mu\t', mn.params['ggd']/mn.params['gdd'])
    print('gm/Id\t', mn.params['ggd']/mn.params['i(ids)'])


else:
    derivedParams = {}
    derivedParams['fT'] = mn.params['ggd']/(2*np.pi*mn.params['cgg'])
    derivedParams['gm/Id\t'] = mn.params['ggd']/mn.params['i(ids)']

    # Define SLiCAP circuit with current-controlled EKV model devices (only valid in linear region)
    if DEV == "nch":
        cirText = "EKV model\n.lib CMOS18.lib\nX1 D G S 0 CMOS18N W={W} L={L} ID={I_D} \n.param I_D=0 W=%s L=%s\n.end\n"%(W, L)

    elif DEV == "pch":
        cirText = "EKV model\n.lib CMOS18.lib\nX1 D G S 0 CMOS18P W={W} L={L} ID={-I_D} \n.param I_D=0 W=%s L=%s\n.end\n"%(W, L)

    f = open(ini.circuitPath + 'MOS.cir', 'w')
    f.write(cirText)
    f.close()

    i1 = instruction()
    i1.setCircuit('MOS.cir')
    i1.defPar('W', W * M)
    i1.defPar('L', L)
    i1.delPar('I_D')

    # Store and redefine SLiCAP EKV library model data
    if DEV == "nch":
        # Store CMOS18 N channel process data from library:
        TOX    = i1.getParValue('TOX_N18')    # oxide thickness [m]
        Vth    = i1.getParValue('Vth_N18')    # threshold voltage [V]
        N_s    = i1.getParValue('N_s_N18')    # substrate factor [-]
        Theta  = i1.getParValue('Theta_N18')  # vertical field mobility reduction coefficient [1/V]
        E_CRIT = i1.getParValue('E_CRIT_N18') # lateral field strength for velocity saturation [V/m]
        u_0    = i1.getParValue('u_0_N18')    # zero field carrier mobility [m^2/V/s]
        CGBO   = i1.getParValue('CGBO_N18')   # gate-bulk overlap capacitance [F/m]
        CGSO   = i1.getParValue('CGSO_N18')   # gate-source and gate-drain overlap capacitance [F/m]
        CJB0   = i1.getParValue('CJB0_N18')   # source/bulk drain/bulk capacitance [F/m^2]
        LDS    = i1.getParValue('LDS_N18')    # length of drain and source [m]
        VAL    = i1.getParValue('VAL_N18')    # Early voltage per unit of length [V/m]
        # You can redefine these process parameters by overwriting the defaults
        i1.defPar('TOX_N18', TOX)             # oxide thickness [m]
        i1.defPar('Vth_N18', Vth)             # threshold voltage [V]
        i1.defPar('N_s_N18', N_s)             # substrate factor [-]
        i1.defPar('Theta_N18', Theta)         # vertical field mobility reduction coefficient [1/V]
        i1.defPar('E_CRIT_N18', E_CRIT)       # lateral field strength for velocity saturation [V/m]
        i1.defPar('u_0_N18', u_0)             # zero field carrier mobility [m^2/V/s]
        i1.defPar('CGBO_N18', CGBO)           # gate-bulk overlap capacitance [F/m]
        i1.defPar('CGSO_N18', CGSO)           # gate-source and gate-drain overlap capacitance [F/m]
        i1.defPar('CJB0_N18', CJB0)           # source/bulk drain/bulk capacitance [F/m^2]
        i1.defPar('LDS_N18', LDS)             # length of drain and source [m]
        i1.defPar('VAL_N18', VAL)             # Early voltage per unit of length [V/m]
    elif DEV == "pch":
        # Store CMOS18 P channel process data from library:
        TOX    = i1.getParValue('TOX_P18')    # oxide thickness [m]
        Vth    = i1.getParValue('Vth_P18')    # threshold voltage [V]
        N_s    = i1.getParValue('N_s_P18')    # substrate factor [-]
        Theta  = i1.getParValue('Theta_P18')  # vertical field mobility reduction coefficient [1/V]
        E_CRIT = i1.getParValue('E_CRIT_P18') # lateral field strength for velocity saturation [V/m]
        u_0    = i1.getParValue('u_0_P18')    # zero field carrier mobility [m^2/V/s]
        CGBO   = i1.getParValue('CGBO_P18')   # gate-bulk overlap capacitance [F/m]
        CGSO   = i1.getParValue('CGSO_P18')   # gate-source and gate-drain overlap capacitance [F/m]
        CJB0   = i1.getParValue('CJB0_P18')   # source/bulk drain/bulk capacitance [F/m^2]
        LDS    = i1.getParValue('LDS_P18')    # length of drain and source [m]
        VAL    = i1.getParValue('VAL_P18')    # Early voltage per unit of length [V/m]
        # You can redefine these process parameters by overwriting the defaults
        i1.defPar('TOX_P18', TOX)             # oxide thickness [m]
        i1.defPar('Vth_P18', Vth)             # threshold voltage [V]
        i1.defPar('N_s_P18', N_s)             # substrate factor [-]
        i1.defPar('Theta_P18', Theta)         # vertical field mobility reduction coefficient [1/V]
        i1.defPar('E_CRIT_P18', E_CRIT)       # lateral field strength for velocity saturation [V/m]
        i1.defPar('u_0_P18', u_0)             # zero field carrier mobility [m^2/V/s]
        i1.defPar('CGBO_P18', CGBO)           # gate-bulk overlap capacitance [F/m]
        i1.defPar('CGSO_P18', CGSO)           # gate-source and gate-drain overlap capacitance [F/m]
        i1.defPar('CJB0_P18', CJB0)           # source/bulk drain/bulk capacitance [F/m^2]
        i1.defPar('LDS_P18', LDS)             # length of drain and source [m]
        i1.defPar('VAL_P18', VAL)             # Early voltage per unit of length [V/m]

    ID = sp.Symbol('I_D')
    IDS = mn.params['i(ids)']

    if DEV == "nch":
        VGS               = sp.lambdify(ID, i1.getParValue('V_GS_X1'))
        vgsTraceBSIM      = trace([mn.params['v(bias)'], IDS])
    elif DEV == "pch":
        VGS               = sp.lambdify(ID, -i1.getParValue('V_GS_X1'))
        vgsTraceBSIM      = trace([VG - mn.params['v(bias)'], IDS])
    vgsTraceEKV        = trace([VGS(IDS), IDS])
    vgsTraceEKV.label  = 'EKV'
    vgsTraceBSIM.label = 'BSIM'
    plotDict_vgs       = {'EKV': vgsTraceEKV, 'BSIM': vgsTraceBSIM}
    fig_vgs = plot('fig_vgs', '$I_{ds}$ versus $V_{gs}$', 'lin', plotDict_vgs, yScale='u', xName='$V_{gs}$', yName='$I_{ds}$', xUnits='V', yUnits='A', show=True)

    GM                = sp.lambdify(ID, i1.getParValue('g_m_X1'))
    gmTraceEKV        = trace([IDS, GM(IDS)])
    gmTraceEKV.label  = 'EKV'
    gmTraceBSIM       = trace([IDS, mn.params['ggd']])
    gmTraceBSIM.label = 'BSIM'
    plotDict_gm       = {'EKV': gmTraceEKV, 'BSIM': gmTraceBSIM}
    fig_gm = plot('fig_gm', '$g_m$ versus $I_{ds}$', 'lin', plotDict_gm, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_m$', xUnits='A', yUnits='S', show=True)

    FT                = sp.lambdify(ID, i1.getParValue('f_T_X1'))
    fTTraceEKV        = trace([IDS, FT(IDS)])
    fTTraceEKV.label  = 'EKV'
    fTTraceBSIM       = trace([IDS, derivedParams['fT']])
    fTTraceBSIM.label = 'BSIM'
    plotDict_fT       = {'EKV': fTTraceEKV, 'BSIM': fTTraceBSIM}
    fig_fT = plot('fig_fT', '$f_T$ versus $I_{ds}$', 'lin', plotDict_fT, xScale='u', yScale='G', xName='$I_{ds}$', yName='$f_T$', xUnits='A', yUnits='Hz', show=True)

    GB                = sp.lambdify(ID, i1.getParValue('g_b_X1'))
    gbTraceEKV        = trace([IDS, GB(IDS)])
    gbTraceEKV.label  = 'EKV'
    gbTraceBSIM       = trace([IDS, mn.params['gbd']])
    gbTraceBSIM.label = 'BSIM'
    plotDict_gb       = {'EKV': gbTraceEKV, 'BSIM': gbTraceBSIM}
    fig_gb = plot('fig_gb', '$g_b$ versus $I_{ds}$', 'lin', plotDict_gb, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_b$', xUnits='A', yUnits='S', show=True)

    GO                = sp.lambdify(ID, i1.getParValue('g_o_X1'))
    goTraceEKV        = trace([IDS, GO(IDS)])
    goTraceEKV.label  = 'EKV'
    goTraceBSIM       = trace([IDS, mn.params['gdd']])
    goTraceBSIM.label = 'BSIM'
    plotDict_go       = {'EKV': goTraceEKV, 'BSIM': goTraceBSIM}
    fig_go = plot('fig_go', '$g_o$ versus $I_{ds}$', 'lin', plotDict_go, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_o$', xUnits='A', yUnits='S', show=True)
