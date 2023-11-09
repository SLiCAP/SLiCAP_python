#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 15:05:13 2021

@author: anton

"""
from os     import system, remove
from sympy  import Symbol
from SLiCAP.SLiCAPini import ini
from SLiCAP.SLiCAPplots import plot, trace
from numpy  import array, sqrt, arctan, pi, unwrap, log10, linspace, geomspace
from re     import findall

"""
NGspice is executed by invoking the 'ini.ngspiceCMD'. Under MSWindows the
location of 'ngspice.exe' must be in the searcg path.
"""

class MOS(object):
    def __init__(self, refDes, lib, dev):
        self.refDes = refDes
        self.lib = lib
        self.dev = dev
        self.opInfo = None
        self.modelDef = None
        self.parDefs = None
        self.params = {}
        self.errors = {}
        self.step   = False
    def getOPid(self, W, L, M, ID, VD, VS, VB, f, step=None):
        if type(step) != list or len(step) != 3:
            stepStart = '{ID}'
            stepNum   = '1'
            stepStep  = '0'
        else:
            stepStart = str(float(step[0]))
            stepNum   = str(int(step[1]))
            stepStep  = str(float(step[2]))
            self.step = True
        txt =  'MOS_OP_I\n'
        txt += '.param ID     = %s\n'%(ID)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '.param L      = %s\n'%(L)
        txt += '.param W      = %s\n'%(W)
        txt += '.param M      = %s\n'%(M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '.lib %s\n\n'%(self.lib)
        # MOS with voltage feedback loop for creating the gate-source voltage
        txt += '%s d1 g1 s1 b1 %s W={W} L={L} M={M}\n'%(self.refDes + '_OP', self.dev)
        # LOOP and DC voltages
        txt += 'V5 s1 0 {VS}\nV6 b1 0 {VB}\nV7 d1 1 {VD}\nE1 g1 d1 1 0 1k\nI1 0 1 {ID}\n'
        # MOS for parameter measurement
        txt += '%s d2 g2 s2 b2 %s W={W} L={L} M={M}\n'%(self.refDes, self.dev)
        # VGS copy
        txt += 'E2 g2 2 g1 0 1\n'
        f = open('cir/MOS_OP_I.cir', 'r')
        txt += f.read()
        f.close()
        f = open('MOS_OP.cir', 'w')
        f.write(txt)
        f.close()
        system(ini.ngspiceCMD + ' -b MOS_OP.cir -o MOS_OP.log')
        remove('MOS_OP.cir')
        remove('MOS_OP.log')
        self.getParams()
        self.makeParDefs()
        self.makeModelDef()
        self.determineAccuracy()
    def getOPvg(self, W, L, M, VG, VD, VS, VB, f, step=None):
        if type(step) != list or len(step) != 3:
            stepStart = '{VG}'
            stepNum   = '1'
            stepStep  = '0'
        else:
            stepStart = str(float(step[0]))
            stepNum   = str(int(step[1]))
            stepStep  = str(float(step[2]))
            self.step = True
        txt =  'MOS_OP_V\n'
        txt += '.param VG     = %s\n'%(VG)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '.param L      = %s\n'%(L)
        txt += '.param W      = %s\n'%(W)
        txt += '.param M      = %s\n'%(M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '.lib %s\n\n'%(self.lib)
        txt += '%s d g s b %s W={W} L={L} M={M}\n\n'%(self.refDes, self.dev)
        f = open('cir/MOS_OP_V.cir', 'r')
        txt += f.read()
        f.close()
        f = open('MOS_OP.cir', 'w')
        f.write(txt)
        f.close()
        system(ini.ngspiceCMD + ' -b MOS_OP.cir -o MOS_OP.log')
        remove('MOS_OP.cir')
        remove('MOS_OP.log')
        self.getParams()
        self.makeParDefs()
        self.makeModelDef()
        self.determineAccuracy()
    def getParams(self):
        f = open('MOS_OP.out', 'r')
        lines = f.readlines()
        f.close()
        remove('MOS_OP.out')
        names  = False
        values = False
        parnames = []
        i = 0
        for line in lines:
            fields = line.split()
            if len(fields):
                if names and fields[0] != 'Values:':
                    parnames.append(fields[1])
                if fields[0] == 'Variables:':
                    names = True
                elif fields[0] == 'Values:':
                    names = False
                    values = True
                if values:
                    if len(fields) == 2:
                        i = 0
                    if parnames[i] in self.params.keys():
                        self.params[parnames[i]].append(float(fields[0]))
                        i += 1
                    elif fields[0] != 'Values:':
                        if self.step:
                            self.params[parnames[i]] = [float(fields[0])]
                            i += 1
                        else:
                            self.params[parnames[i]] = float(fields[0])
                            i += 1
        del self.params['yes']
        if self.step:
            for key in self.params.keys():
                self.params[key] = array(self.params[key])
    def makeParDefs(self):
        self.parDefs = {}
        self.parDefs[Symbol('gm_' + self.refDes)] = self.params['ggd']
        self.parDefs[Symbol('gb_' + self.refDes)] = self.params['gbd']
        self.parDefs[Symbol('go_' + self.refDes)] = self.params['gdd']
        self.parDefs[Symbol('cgs_' + self.refDes)] = (self.params['cgs'] + self.params['csg'])/2
        self.parDefs[Symbol('cgb_' + self.refDes)] = (self.params['cgb'] + self.params['cbg'])/2
        self.parDefs[Symbol('cdg_' + self.refDes)] = (self.params['cdg'] + self.params['cgd'])/2
        self.parDefs[Symbol('cdb_' + self.refDes)] = (self.params['cdb'] + self.params['cbd'])/2
        self.parDefs[Symbol('csb_' + self.refDes)] = (self.params['csb'] + self.params['cbs'])/2
    def makeModelDef(self):
        text = '.model %s M'%(self.refDes)
        text += '\n+ gm=%s'%(self.params['ggd'])
        text += '\n+ gb=%s'%(self.params['gbd'])
        text += '\n+ go=%s'%(self.params['gdd'])
        text += '\n+ cgs=%s'%((self.params['cgs'] + self.params['csg'])/2)
        text += '\n+ cgb=%s'%((self.params['cgb'] + self.params['cbg'])/2)
        text += '\n+ cdg=%s'%((self.params['cdg'] + self.params['cgd'])/2)
        text += '\n+ cdb=%s'%((self.params['cdb'] + self.params['cbd'])/2)
        text += '\n+ csb=%s'%((self.params['csb'] + self.params['cbs'])/2)
        self.modelDef = text
    def determineAccuracy(self):
        CGG = self.params['cgs'] + self.params['cgd'] + self.params['cgb']
        CDD = self.params['cds'] + self.params['cdg'] + self.params['cdb']
        CSS = self.params['csd'] + self.params['csg'] + self.params['csb']
        CBB = self.params['cbd'] + self.params['cbg'] + self.params['cbs']
        CGG_error = (CGG-self.params['cgg'])/self.params['cgg']
        self.errors['cgg'] = (CDD-self.params['cdd'])/self.params['cdd']
        self.errors['css'] = (CSS-self.params['css'])/self.params['css']
        self.errors['cbb'] = (CBB-self.params['cbb'])/self.params['cbb']
        self.errors['cgs'] = ((self.params['cgs']-self.params['csg'])/(self.params['cgs']+self.params['csg']))
        self.errors['cgd'] = ((self.params['cgd']-self.params['cdg'])/(self.params['cgd']+self.params['cdg']))
        self.errors['cgb'] = ((self.params['cgb']-self.params['cbg'])/(self.params['cgb']+self.params['cbg']))
        self.errors['cbs'] = ((self.params['cbs']-self.params['csb'])/(self.params['cbs']+self.params['csb']))
        self.errors['cbd'] = ((self.params['cbd']-self.params['cdb'])/(self.params['cbd']+self.params['cdb']))

def ngspice2traces(cirFile, simCmd, namesDict, stepCmd=None, traceType='magPhase'):
    """
    Creates a csv file from an ngspice run.

    :param cirFile: Name of the circuit file withouit '.cir' extension, located
                     in the cir folder.

                     The circuit file should not have a .end command, this will
                     be added at the end of he control section.

    :type cirFile: str

    :param simCmd: ngspice instruction capable of generating plot data, such as,

                 ac dec 20 1 10meg

                 tran 1n 10u

                 dc Source Vstart Vstop Vincr [ Source2 Vstart2 Vstop2 Vincr2 ]

                 etc.

    :type simCmd: str

    :param stepCmd: .stepCmd instruction or None if no stepping is performed:

                 .stepCmd <parname> <stepmethod> <firstvalue> (<lastvalue> <numberofvalues | listwithvalues>)

                 - parname (*str*): name of the parameter (not a RefDes)
                 - stepmethod (*str*): lin, log or list

    :type stepCmd: str, nonetype

    :param namesDict: Dictionary with key-value pairs:

                      key: plot label (*str*)

                      value: nodal voltage or brach current in ngspice notation
    :type namesDict: dict

    :param traceType: Type of traces, can be:

                      - realImag
                      - magPhase
                      - dBmagPhase
    """
    try:
        remove(cirFile + '.csv')
    except:
        pass
    labels = {}
    if stepCmd != None:
        stepFields = stepCmd.split()
        stepPar = stepFields[0]
        stepMethod = stepFields[1].lower()
        if stepMethod == 'list':
            try:
                stepList = eval(findall(r'\[[\s,.+-eE0-9]*\]', stepCmd)[0])
            except:
                print('Error in step list.')
                return
        else:
            try:
                stepStart  = eval(stepFields[2])
            except:
                print('Error: missing or error in stepstart value.')
                return
            try:
                stepStop  = eval(stepFields[3])
            except:
                print('Error: missing or error in stepCmd stop value.')
                return
            try:
                stepNum  = int(stepFields[4])
            except:
                print('Error: missing or error in step number.')
                return
        if stepMethod == 'lin':
            stepList = linspace(stepStart, stepStop, stepNum)
        elif stepMethod == 'log':
            stepList = geomspace(stepStart, stepStop, stepNum)
        for i in range(len(stepList)):
            f = open(cirFile + '.cir', 'r')
            netlist = f.read()
            f.close()
            traceNames = []
            netlist += '\n.param ' + stepPar + ' = ' + str(stepList[i]) + '\n'
            netlist += '\n.control\n'
            netlist += simCmd + '\n'
            netlist += '\nset appendwrite\nset wr_vecnames\nset wr_singlescale\n'

            for key in list(namesDict.keys()):
                traceName = key + '_' + str(i)
                labels[traceName] = key + ':' + stepPar + '=' + '{0: 8.2e}'.format(stepList[i])
                # remove whitespace (compact label)
                labels[traceName] = ''.join(labels[traceName].split())
                netlist += 'let ' + traceName + ' = ' + namesDict[key] + '\n'
                traceNames.append(traceName)
            netlist += 'wrdata ' + cirFile  + '.csv'
            for name in traceNames:
                netlist += ' ' + name
            netlist += '\n.endc\n'

            f = open('simFile.sp', 'w')
            f.write(netlist)
            f.close()
            system(ini.ngspiceCMD + ' -b simFile.sp -o simFile.log')
    else:
        f = open(cirFile + '.cir', 'r')
        netlist = f.read()
        f.close()
        netlist += '\n.control\nset wr_vecnames\nset wr_singlescale\n'
        netlist += simCmd + '\n'

        for key in list(namesDict.keys()):
            netlist += 'let ' + key + ' = ' + namesDict[key] + '\n'
        netlist += 'wrdata ' + cirFile + '.csv'
        for key in list(namesDict.keys()):
            netlist += ' ' + key
        netlist += '\n.endc'
    netlist += '\n.end'
    f = open('simFile.sp' , 'w')
    f.write(netlist)
    f.close()
    analysisType = simCmd.split()[0]
    system('ngspice -b simFile.sp -o simFile.log')
    f = open(cirFile + '.csv', 'r')
    txt = f.read()
    f.close()
    if analysisType == 'DC':
        lines = txt.splitlines()
        xVar = lines[0].split()[0]
        labels[xVar] = simCmd.split()[1]
    if labels != None:
        for key in labels:
            txt = txt.replace(key + ' ', labels[key] + ' ')
    f = open(cirFile + '.csv', 'w')
    f.write(txt)
    f.close()
    remove('simFile.sp')
    remove('simFile.log')
    traceDict = processNGspiceResult(cirFile, analysisType, traceType)
    return traceDict

def processNGspiceResult(cirFile, analysisType, traceType):
    # Read the CSV file
    f = open(cirFile + '.csv', 'r')
    lines = f.readlines()
    f.close()
    analysisType = analysisType.upper()
    if analysisType == 'DC' or analysisType == 'TRAN' or analysisType == 'NOISE':
        traceDict = makeDCTRNStraces(lines)
    elif analysisType.upper() == 'AC':
        traceDict = makeACtraces(lines, traceType)
    return traceDict

def makeDCTRNStraces(lines):
    traceDict = {}
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            xVar = fields[0]
        if fields[0] == xVar:
            # We have a new trace
            labels = [fields[j] for j in range(1, len(fields))]
            for label in labels:
                traceDict[label] = [[],[]] # time, value
        else:
            for j in range(len(labels)):
                traceDict[labels[j]][0].append(eval(fields[0])) # time
                traceDict[labels[j]][1].append(eval(fields[j+1])) # value
    for key in list(traceDict.keys()):
        traceDict[key] = trace((traceDict[key][0], traceDict[key][1]))
        traceDict[key].label = key
    return traceDict, xVar

def makeACtraces(lines, traceType):
    reMagDict = {}
    imPhsDict = {}
    traceDict = {}
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            xVar = fields[0]
        if fields[0] == xVar:
            labels = [fields[j] for j in range(1, len(fields))]
            for label in labels:
                traceDict[label] = [[],[],[]] # frequency, real, imag
        else:
            for j in range(len(labels)):
                if j%2:
                    traceDict[labels[j]][2].append(eval(fields[j+1])) # imag
                else:
                    traceDict[labels[j]][0].append(eval(fields[0])) # frequency
                    traceDict[labels[j]][1].append(eval(fields[j+1])) # real
    for key in list(traceDict.keys()):
        freq = traceDict[key][0]
        real = array(traceDict[key][1])
        imag = array(traceDict[key][2])
        if traceType == 'realImag':
            reMagDict[key] = trace((freq, real))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, imag))
            imPhsDict[key].label = key
        elif traceType == 'magPhase':
            reMagDict[key] = trace((freq, sqrt(real**2+imag**2)))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real)*180/pi, 90)))
            imPhsDict[key].label = key
        elif traceType == 'dBmagPhase':
            reMagDict[key] = trace((freq, 10*log10(real**2+imag**2)))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real)*180/pi, 90)))
            imPhsDict[key].label = key
    return reMagDict, imPhsDict, xVar