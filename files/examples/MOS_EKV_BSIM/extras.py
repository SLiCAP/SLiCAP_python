#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 11:41:04 2023

@author: anton
"""
from SLiCAP import *

def createStep(device, biasPar, VS, ID, Npts, Vdiff, Idiff):
    if device.dev == "nch":
        if biasPar == "VGS":
            step = [VS, Npts, Vdiff]
        elif biasPar == "IDS":
            step = [1e-9, Npts, Idiff]
    elif device.dev == "pch":
        if biasPar == "VGS":
            step = [VS, Npts, -Vdiff]
        elif biasPar == "IDS":
            step = [-1e-9, Npts, -Idiff]
    return step

def printOPinfo(device, biasPar, ID, VG, VD, VS, VB, f):
    step = False
    if device.dev == "pch":
        ID = -ID
        VGS = VS-VG
    elif device.dev == 'nch':
        VGS = VG-VS
    if biasPar == "VGS":
        device.getOPvg(VGS, VD, VS, VB, f, step)
    elif biasPar == "IDS":
        device.getOPid(ID, VD, VS, VB, f, step)
    print('\nParameters found by simulation:\n')
    for key in device.params.keys():
        print(key, device.params[key])
    print('\nSLiCAP model definition:\n')
    print(device.modelDef)
    print('\nSLiCAP parameter definitions:\n')
    for key in device.parDefs.keys():
        print(key, device.parDefs[key])
    print('\nRelative errors:\n')
    for key in device.errors.keys():
        print(key,device.errors[key])
    print('\nDerived parameters:\n')
    print('fT\t', sp.N(device.params['ggd']/(2*np.pi*device.params['cgg']),4))
    print('mu\t', sp.N(device.params['ggd']/device.params['gdd'], 4))
    print('gm/Id\t', sp.N(device.params['ggd']/device.params['i(ids)'], 4))

def plotOpinfo(device, biasPar, ID, VG, VD, VS, VB, f, step, EKVlib='SLiCAP.lib'):
    if device.dev == "pch":
        ID = -ID
        VGS = VS-VG
    elif device.dev == 'nch':
        VGS = VG-VS
    if biasPar == "VGS":
        device.getOPvg(VGS, VD, VS, VB, f, step)
    elif biasPar == "IDS":
        device.getOPid(ID, VD, VS, VB, f, step)
    derivedParams = {}
    derivedParams['fT'] = device.params['ggd']/(2*np.pi*device.params['cgg'])
    derivedParams['gm/Id\t'] = device.params['ggd']/device.params['i(ids)']
    # Define SLiCAP circuit with current-controlled EKV model devices (only valid in linear region)
    if device.dev == "nch":
        cirText = "EKV model\n.lib %s\nX1 D G S 0 CMOS18N W={W} L={L} ID={I_D} \n.param I_D=0 W=%s L=%s\n.end\n"%(EKVlib, device.W * device.M, device.L)
    elif device.dev == "pch":
        cirText = "EKV model\n.lib %s\nX1 D G S 0 CMOS18P W={W} L={L} ID={-I_D} \n.param I_D=0 W=%s L=%s\n.end\n"%(EKVlib, device.W * device.M, device.L)
    f = open(ini.circuitPath + 'MOS.cir', 'w')
    f.write(cirText)
    f.close()
    i1 = instruction()
    i1.setCircuit('MOS.cir')
    i1.delPar('I_D')
    I_D = sp.Symbol('I_D')
    IDS = device.params['i(ids)']
    if device.dev == "nch":
        VGS               = sp.lambdify(I_D, i1.getParValue('V_GS_X1'))
        vgsTraceBSIM      = trace([device.params['v(vgs)'], IDS])
    elif device.dev == "pch":
        VGS               = sp.lambdify(I_D, -i1.getParValue('V_GS_X1'))
        if biasPar == "IDS":
            vgsTraceBSIM      = trace([device.params['v(vgs)'], IDS])
        elif biasPar == "VSG":
            vgsTraceBSIM      = trace([VG - device.params['v(vgs)'], IDS])
    vgsTraceEKV        = trace([VGS(IDS), IDS])
    vgsTraceEKV.label  = 'EKV'
    vgsTraceBSIM.label = 'BSIM'
    plotDict_vgs       = {'EKV': vgsTraceEKV, 'BSIM': vgsTraceBSIM}
    fig_vgs = plot('fig_vgs', '$I_{ds}$ versus $V_{gs}$', 'lin', plotDict_vgs, yScale='u', xName='$V_{gs}$', yName='$I_{ds}$', xUnits='V', yUnits='A', show=True)

    GM                = sp.lambdify(I_D, i1.getParValue('g_m_X1'))
    gmTraceEKV        = trace([IDS, GM(IDS)])
    gmTraceEKV.label  = 'EKV'
    gmTraceBSIM       = trace([IDS, device.params['ggd']])
    gmTraceBSIM.label = 'BSIM'
    plotDict_gm       = {'EKV': gmTraceEKV, 'BSIM': gmTraceBSIM}
    fig_gm = plot('fig_gm', '$g_m$ versus $I_{ds}$', 'lin', plotDict_gm, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_m$', xUnits='A', yUnits='S', show=True)

    FT                = sp.lambdify(I_D, i1.getParValue('f_T_X1'))
    fTTraceEKV        = trace([IDS, FT(IDS)])
    fTTraceEKV.label  = 'EKV'
    fTTraceBSIM       = trace([IDS, derivedParams['fT']])
    fTTraceBSIM.label = 'BSIM'
    plotDict_fT       = {'EKV': fTTraceEKV, 'BSIM': fTTraceBSIM}
    fig_fT = plot('fig_fT', '$f_T$ versus $I_{ds}$', 'lin', plotDict_fT, xScale='u', yScale='G', xName='$I_{ds}$', yName='$f_T$', xUnits='A', yUnits='Hz', show=True)

    GB                = sp.lambdify(I_D, i1.getParValue('g_b_X1'))
    gbTraceEKV        = trace([IDS, GB(IDS)])
    gbTraceEKV.label  = 'EKV'
    gbTraceBSIM       = trace([IDS, device.params['gbd']])
    gbTraceBSIM.label = 'BSIM'
    plotDict_gb       = {'EKV': gbTraceEKV, 'BSIM': gbTraceBSIM}
    fig_gb = plot('fig_gb', '$g_b$ versus $I_{ds}$', 'lin', plotDict_gb, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_b$', xUnits='A', yUnits='S', show=True)

    GO                = sp.lambdify(I_D, i1.getParValue('g_o_X1'))
    goTraceEKV        = trace([IDS, GO(IDS)])
    goTraceEKV.label  = 'EKV'
    goTraceBSIM       = trace([IDS, device.params['gdd']])
    goTraceBSIM.label = 'BSIM'
    plotDict_go       = {'EKV': goTraceEKV, 'BSIM': goTraceBSIM}
    fig_go = plot('fig_go', '$g_o$ versus $I_{ds}$', 'lin', plotDict_go, xScale='u', yScale='u', xName='$I_{ds}$', yName='$g_o$', xUnits='A', yUnits='S', show=True)

def plotSvinoise(device, ID, VD, VS, VB, fmin, fmax, numDec, EKVlib='SLiCAP.lib'):
    if device.dev == "pch":
        ID = -ID
    inoiseTraceDict, xVar, xUnits = device.getSv_inoise(ID, VD, VS, VB, fmin, fmax, numDec)
    for key in inoiseTraceDict.keys():
        inoiseTraceDict[key].label += "-BSIM"

    cirText   = "CMOS_noise\n"
    cirText += ".lib %s\n"%(EKVlib)
    if device.dev == "nch":
        cirText += "X1 in 0 out  NM18_noise W={W} L={L} ID={I_D}\n"
    elif device.dev == "pch":
        cirText += "X1 in 0 out  PM18_noise W={W} L={L} ID={I_D}\n"
    cirText += "V1 in 0 1\n"
    cirText += ".end\n"
    f = open("cir/EKVmosNoise.cir", "w")
    f.write(cirText)
    f.close()

    i1 = instruction()
    i1.setCircuit("EKVmosNoise.cir")
    i1.defPar('W', device.W * device.M)
    i1.defPar('L', device.L)
    i1.defPar('I_D', ID)
    i1.setSimType("numeric")
    i1.setGainType('vi')
    i1.setDataType('noise')
    i1.setDetector('V_out')
    i1.setSource('V1')
    result = i1.execute()
    result.detLabel = "-EKV"
    figNoise = plotSweep('EKVnoise', 'Input referred voltage noise', result, fmin, fmax, 200, funcType='inoise', show=False)
    figNoise.show = True
    traces2fig(inoiseTraceDict, figNoise)
    figNoise.plot()
    FT = i1.getParValue("f_T_X1")
    FL = i1.getParValue("f_ell_X1")
    print("f_T=", sp.N(FT,3))
    print("f_L=", sp.N(FL,3))
    print("f_T/f_L=", sp.N(FT/FL,3))
    return figNoise, FT, FL