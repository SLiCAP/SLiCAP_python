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
W      = 2.2e-6
L      = 1.8e-6
M      = 1
f      = 1E6
refDes = 'M1'
Npts   = 90
Vdiff  = 0.01

# Create the device
mn = MOS(refDes, LIB, DEV)

if DEV == "nch":
    VD   = 0.9
    VS   = 0
    VB   = 0
    VG   = 0
    step = [VS, Npts, Vdiff]

elif DEV == "pch":
    VD   = 0.9
    VS   = 1.8
    VB   = 1.8
    VG   = 1.8
    step = [VS, Npts, -Vdiff]

#step=None # Uncomment if you want single-point info

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

    # Get SLiCAP EKV model data

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

    ID = sp.Symbol('I_D')

    IDS = mn.params['i(ids)']

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
