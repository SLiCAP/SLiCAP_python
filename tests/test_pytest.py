# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 11:28:37 2020

@author: luc_e
"""
from SLiCAP import *
import os

def test_pytest():
    assert 4==4
    
def test_CSresnoise():
    ini.installPath = os.getcwd() + '/'
    ini.projectPath = ini.installPath + 'files/examples/CSstage/'
    ini.circuitPath = ini.projectPath + 'cir/'
    ini.htmlPath    = ini.projectPath + 'html/'
    ini.htmlIndex   = 'index.html'
    makeDir(ini.htmlPath)
    ini.lastUpdate  = datetime.now()
    # prj = initProject('CS stage noise with resistive source', firstRun=False)
    ini.maxima = 'C:\\maxima-5.42.2\\bin\\maxima.bat'
    fileName = 'CSresNoise.cir'
    LIB = makeLibraries()
    i1 = instruction()
    i1.setCircuit(fileName)
    # Set value of 1/f noise to zero and define drain current at critical inversion
    i1.simType = 'numeric'
    i1.defPar('KF_N18', 0)
    I_D     = i1.getParValue('ID')
    IC      = i1.getParValue('IC_X1')
    IC_CRIT = i1.getParValue('IC_CRIT_X1')
    I_D     = I_D*IC_CRIT/IC
    
    i1.circuit.defPar('ID', I_D)
    R_N   = i1.getParValue('R_N_X1')
    R_s   = i1.getParValue('R_s')
    f_T   = i1.getParValue('f_T_X1')
    g_m   = i1.getParValue('g_m_X1')
    Width = i1.getParValue('W')
    
    i1.setSource('V1')
    i1.setDetector('V_out')
    i1.setGainType('vi')
    i1.setDataType('noise')
    i1.setSimType('numeric')
    noise_result = i1.execute()
    # plotSweep('Inoise', 'Source-referred noise spectrum', noise_result, 1e8, 1e11, 100, funcType = 'inoise', show=False)
    
    # Calculate the noise figure at critical inversion and the given width
    tot_inoise      = rmsNoise(noise_result, 'inoise', 1e9, 5e9)
    tot_inoise_src  = rmsNoise(noise_result, 'inoise', 1e9, 5e9, source = noise_result.source)
    
    NF              = 20*sp.log(tot_inoise/tot_inoise_src)/sp.log(10)
    print(NF)
    shifted = int(NF*1000)
    assert shifted == 652

def test_lex():
    fi = 'tests/test_files/myFirstRCnetwork.cir'
    print(fi)
    lexer = tokenize(fi)
    tok = lexer.token()
    while tok:
        print(tok)
        tok = lexer.token()
    print('\nnumber of errors =', lexer.errCount, '\n')
    #Add assert statement

def test_lex2():
    #Alter circuit to cause an error
    fi = 'tests/test_files/myFirstRCnetwork.cir'
    print(fi)
    lexer = tokenize(fi)
    tok = lexer.token()
    while tok:
        print(tok)
        tok = lexer.token()
    print('\nnumber of errors =', lexer.errCount, '\n')
    #Add assert statement

def test_matrix():
        s = ini.Laplace
        MNA = matrix([[5.0e-12*s + 0.01, 0, 0, -5.0e-12*s - 0.01, 0, 0, 0, 0, 1],
                      [0, 1.98e-11*s + 0.0001, -1.2e-11*s, -1.8e-12*s - 1.0e-5, 0, 0, 0, 0, 0],
                      [0, -1.2e-11*s, 2.8e-11*s + 0.001, 0, -1.0e-11*s - 0.001, 0, 0, -1, 0],
                      [-5.0e-12*s - 0.01, -1.8e-12*s - 1.0e-5, 0, 1.0068e-9*s + 0.01101, 0, 0, 1, 0, 0],
                      [0, 0, -1.0e-11*s - 0.001, 0, 1.0e-11*s + 0.001, 1, 0, 1, 0],
                      [0, 0, 0, 0, 1, 0, 0, 0, 0],
                      [0, 0, 0, 1, 0, 0, -1.0e-6*s, -3.1623e-11*s, 0],
                      [0, 0, -1, 0, 1, 0, -3.1623e-11*s, -1.0e-9*s, 0],
                      [2.048e-20*s**3 + 2.688e-11*s**2 + 0.0016*s + 1, 0, 0, 0, 0, 0, 0, 0, 0]])
        print(MNA.determinant())

def test_yacc():
    ini.installPath = os.getcwd() + '/'
    ini.projectPath = ini.installPath + 'files/examples/CSstage/'
    ini.circuitPath = ini.projectPath + 'cir/'
    ini.htmlPath    = ini.projectPath + 'html/'
    ini.htmlIndex   = 'index.html'
    makeDir(ini.htmlPath)
    ini.lastUpdate  = datetime.now()
    LIB = makeLibraries()
    fi = 'CSresNoise.cir'
    print("\nCheking:", fi)
    myCir = checkCircuit(fi)
    keys = list(myCir.elements.keys())

    for key in keys:
        el = myCir.elements[key]
        print('\nElement    :', key)
        print('Nodes      :', el.nodes)
        print('Refs       :', el.refs)
        print('Model      :', el.model)
        print('Params     :')
        for par in list(el.params.keys()):
            print(' ', par, '=', el.params[par])

    print('\nCircuit parameter definitions:')
    for par in list(myCir.parDefs.keys()):
        print(' ', par, '=', myCir.parDefs[par]    )
    for el in list(myCir.elements.keys()):
        for par in list( myCir.elements[el].params.keys()):
            parNum = fullSubs(myCir.elements[el].params[par], myCir.parDefs)
            print(el,'\t', par, sp.N(parNum, ini.disp))

def test_execute():
    s = sp.Symbol('s')
    loopGainNumer = -s*(1 + s/20)*(1 + s/40)/2
    loopGainDenom = (s + 1)**2*(1 + s/4e3)*(1 + s/50e3)*(1 + s/1e6)
    loopGain        = loopGainNumer/loopGainDenom
    r = findServoBandwidth(loopGain)
    print(r)

def test_instruction():
    i = instruction()
    i.circuit = circuit()
    i.gainType = 'loopgain'
    i.dataType = 'zeros'
    i.simType = 'numeric'
    i.detector = 'V_11'
    i.source = 'V1'
    i.lgRef = 'G1'
    i.step = True
    i.stepMethod = 'lin'
    i.stepNum = '5a'
    i.execute()

def test_math():
    s = ini.Laplace

    MNA = matrix([[5.0e-12*s + 0.01, 0, 0, -5.0e-12*s - 0.01, 0, 0, 0, 0, 1],
                  [0, 1.98e-11*s + 0.0001, -1.2e-11*s, -1.8e-12*s - 1.0e-5, 0, 0, 0, 0, 0],
                  [0, -1.2e-11*s, 2.8e-11*s + 0.001, 0, -1.0e-11*s - 0.001, 0, 0, -1, 0],
                  [-5.0e-12*s - 0.01, -1.8e-12*s - 1.0e-5, 0, 1.0068e-9*s + 0.01101, 0, 0, 1, 0, 0],
                  [0, 0, -1.0e-11*s - 0.001, 0, 1.0e-11*s + 0.001, 1, 0, 1, 0],
                  [0, 0, 0, 0, 1, 0, 0, 0, 0],
                  [0, 0, 0, 1, 0, 0, -1.0e-6*s, -3.1623e-11*s, 0],
                  [0, 0, -1, 0, 1, 0, -3.1623e-11*s, -1.0e-9*s, 0],
                  [2.048e-20*s**3 + 2.688e-11*s**2 + 0.0016*s + 1, 0, 0, 0, 0, 0, 0, 0, 0]])

    DET = MNA.determinant()
    t1=time()
    roots1 = numRoots(DET,s)
    t2=time()
    print(roots1, t2-t1)
    MOD = MNA.Cramer([0,0,0,1,0,-1,0,0,0],3)
    DET = MOD.determinant()
    roots2 = numRoots(DET,s)
    print(roots2)
    a = phase_f(DET)
    print(sp.N(a.subs(ini.frequency, 100)))
    loopgain_numer   = sp.sympify('-s*(1 + s/20)*(1 + s/40)/2')
    loopgain_denom   = sp.sympify('(s + 1)^2*(1 + s/4e3)*(1 + s/50e3)*(1 + s/1e6)')
    loopgain         = loopgain_numer/loopgain_denom
    servo_info       = findServoBandwidth(loopgain)
    print(servo_info)

def test_python_maxima():
    ini.maxima = 'C:\\maxima-5.42.2\\bin\\maxima.bat'
    print(maxILT(1, ini.Laplace**2 + sp.Symbol('a')**2, numeric = False))
    proto_transfer = sp.sympify('0.3*(1/(1+s*0.6))')
    circuit_transfer = sp.sympify('R_1/(R_1 + R_2)/(1 + s*R_1*R_2/(R_1 + R_2)*10e-6)')
    circuit_component_values = equateCoeffs(proto_transfer, circuit_transfer)
    print(circuit_component_values)
    proto_transfer = sp.sympify('A/(1+s*tau)')
    circuit_component_values = equateCoeffs(proto_transfer, circuit_transfer, noSolve=['A','tau'], numeric=False)
    print(circuit_component_values)

