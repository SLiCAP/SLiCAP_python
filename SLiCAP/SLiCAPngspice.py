#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module for interfacing with NGspice.

"""
import SLiCAP.SLiCAPconfigure as ini
from SLiCAP.SLiCAPmath import _checkExpression
from os     import system, remove
from sympy  import Symbol
from SLiCAP.SLiCAPplots import trace
from numpy  import array, sqrt, arctan, pi, unwrap, log10, linspace, geomspace
import re
from shutil import copy2

class MOS(object):
    """
    MOS Transistor.

    :param refDes: Reference designator used in SLiCAP circuit file
    :type refDes: str

    :param lib: path to library file, absolute or relative to python script.
    :type lib: str

    :param dev: Device name (as in library)
    :type dev: str


    MOS attributes:

    - *self*.refDes = refDes
    - *self*.lib = lib
    - *self*.dev = dev
    - *self*.modelDef = Text string with SLiCAP model definition for this device
    - *self*.parDefs = Dictionary with SLiCAP parameter definitions for this device
    - *self*.params = Dictionary with names and values of parameters provided by ngspice
    - *self*.errors = Relative difference between forward and reverse parameter measurement
    - *self*.step   = Step data for VG or ID, defaults to False

    """
    def __init__(self,refDes, lib, dev, W, L, M):
        self.refDes   = refDes
        self.lib      = lib
        self.dev      = dev
        self.W        = W
        self.L        = L
        self.M        = M
        self.modelDef = None
        self.parDefs  = None
        self.params   = {}
        self.errors   = {}
        self.step     = False

    def getOPid(self, ID, VD, VS, VB, f, step=None):
        """
        Returns operating point information of the device with the drain
        current as (swept) independent variable.

        :param W: Width of the device in [m]
        :type W: float

        :param L: Length of the device in [m]
        :type L: float

        :param M: Number of devices in parallel
        :type M: int

        :param ID: Drain current [A]
        :type ID: float

        :param VD: Drain voltage with respect to ground in [V]
        :type VD: float

        :param VS: Source voltage with respect to ground in [V]
        :type VS: float

        :param VB: Bulk voltage with respect to ground in [V]
        :type VB: float

        :param step: Step data for ID; list with start value, number of values
                     and stop value. Defaults to None
        """
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
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '%s\n\n'%(self.lib)
        # MOS with voltage feedback loop for creating the gate-source voltage
        txt += 'M1_OP d1 g1 s1 b1 %s W={W} L={L} M={M}\n'%(self.dev)
        # LOOP and DC voltages
        txt += 'V5 s1 0 {VS}\nV6 b1 0 {VB}\nV7 d1 1 {VD}\nE1 g1 d1 1 0 100\nI1 0 1 {ID}\n'
        # MOS for parameter measurement
        txt += 'M1 d2 g2 s2 b2 %s W={W} L={L} M={M}\n'%(self.dev)
        # VGS copy
        txt += 'E2 g2 2 g1 0 1\n'
        f = open('cir/MOS_OP_I.cir', 'r')
        txt += f.read()
        f.close()
        f = open('MOS_OP.cir', 'w')
        f.write(txt)
        f.close()
        system(ini.ngspice + ' -b MOS_OP.cir -o MOS_OP.log')
        #remove('MOS_OP.cir')
        #remove('MOS_OP.log')
        self._getParams()
        self._makeParDefs()
        self._makeModelDef()
        self._determineAccuracy()

    def getOPvg(self, VG, VD, VS, VB, f, step=None):
        """
        Returns operating point information of the device with the gate
        voltage as (swept) independent variable.

        :param W: Width of the device in [m]
        :type W: float

        :param L: Length of the device in [m]
        :type L: float

        :param M: Number of devices in parallel
        :type M: int

        :param VG: Gate voltage with respect to ground in [V]
        :type VG: float

        :param VD: Drain voltage with respect to ground in [V]
        :type VD: float

        :param VS: Source voltage with respect to ground in [V]
        :type VS: float

        :param VB: Bulk voltage with respect to ground in [V]
        :type VB: float

        :param step: Step data for VG; list with start value, number of values
                     and stop value. Defaults to None
        """
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
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param freq   = %s\n'%(f)
        txt += '.param num    = %s\n'%(stepNum)
        txt += '.param start  = %s\n'%(stepStart)
        txt += '.param delta  = %s\n'%(stepStep)
        txt += '.param select = 0\n\n'
        txt += '%s\n\n'%(self.lib)
        txt += '%s d g s b %s W={W} L={L} M={M}\n\n'%(self.refDes, self.dev)
        f = open('cir/MOS_OP_V.cir', 'r')
        txt += f.read()
        f.close()
        f = open('MOS_OP.cir', 'w')
        f.write(txt)
        f.close()
        system(ini.ngspice + ' -b MOS_OP.cir -o MOS_OP.log')
        remove('MOS_OP.cir')
        remove('MOS_OP.log')
        self._getParams()
        self._makeParDefs()
        self._makeModelDef()
        self._determineAccuracy()

    def _getParams(self):
        f = open('MOS_OP.out', 'r')
        lines = f.readlines()
        f.close()
        #remove('MOS_OP.out')
        names  = False
        values = False
        self.params = {}
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

    def _makeParDefs(self):
        self.parDefs = {}
        self.parDefs[Symbol('gm_' + self.refDes)] = self.params['ggs']
        self.parDefs[Symbol('gb_' + self.refDes)] = self.params['gbs']
        self.parDefs[Symbol('go_' + self.refDes)] = self.params['gdd']
        self.parDefs[Symbol('cgs_' + self.refDes)] = (self.params['cgs'] + self.params['csg'])/2
        self.parDefs[Symbol('cgb_' + self.refDes)] = (self.params['cgb'] + self.params['cbg'])/2
        self.parDefs[Symbol('cdg_' + self.refDes)] = (self.params['cdg'] + self.params['cgd'])/2
        self.parDefs[Symbol('cdb_' + self.refDes)] = (self.params['cdb'] + self.params['cbd'])/2
        self.parDefs[Symbol('csb_' + self.refDes)] = (self.params['csb'] + self.params['cbs'])/2

    def _makeModelDef(self):
        txt = '.model %s M'%(self.refDes)
        txt += '\n+ gm=%s'%(self.params['ggs'])
        txt += '\n+ gb=%s'%(self.params['gbs'])
        txt += '\n+ go=%s'%(self.params['gdd'])
        txt += '\n+ cgs=%s'%((self.params['cgs'] + self.params['csg'])/2)
        txt += '\n+ cgb=%s'%((self.params['cgb'] + self.params['cbg'])/2)
        txt += '\n+ cdg=%s'%((self.params['cdg'] + self.params['cgd'])/2)
        txt += '\n+ cdb=%s'%((self.params['cdb'] + self.params['cbd'])/2)
        txt += '\n+ csb=%s'%((self.params['csb'] + self.params['cbs'])/2)
        self.modelDef = txt

    def _determineAccuracy(self):
        CGG = self.params['cgs'] + self.params['cgd'] + self.params['cgb']
        CDD = self.params['cds'] + self.params['cdg'] + self.params['cdb']
        CSS = self.params['csd'] + self.params['csg'] + self.params['csb']
        CBB = self.params['cbd'] + self.params['cbg'] + self.params['cbs']
        self.errors['cgg'] = (CGG-self.params['cgg'])/self.params['cgg']
        self.errors['cdd'] = (CDD-self.params['cdd'])/self.params['cdd']
        self.errors['css'] = (CSS-self.params['css'])/self.params['css']
        self.errors['cbb'] = (CBB-self.params['cbb'])/self.params['cbb']
        self.errors['cgs'] = ((self.params['cgs']-self.params['csg'])/(self.params['cgs']+self.params['csg']))
        self.errors['cgd'] = ((self.params['cgd']-self.params['cdg'])/(self.params['cgd']+self.params['cdg']))
        self.errors['cgb'] = ((self.params['cgb']-self.params['cbg'])/(self.params['cgb']+self.params['cbg']))
        self.errors['cbs'] = ((self.params['cbs']-self.params['csb'])/(self.params['cbs']+self.params['csb']))
        self.errors['cbd'] = ((self.params['cbd']-self.params['cdb'])/(self.params['cbd']+self.params['cdb']))

    def getSv_inoise(self, ID, VD, VS, VB, fmin, fmax, numDec):
        self.params = {}
        self.step   = None
        self.getOPid(ID, VD, VS, VB, sqrt(fmin*fmax))
        VGS = self.params['v(vgs)']
        if self.dev[0].lower() == 'p':
            VGS = -VGS
        IDS = self.params['i(ids)']
        print("Ids target  :", ID)
        print("Ids realized:", IDS, "\n")
        print("Vgs realized:", VGS, "\n")
        txt = "MOS_noise\n"
        txt += '%s\n\n'%(self.lib)
        txt += '.param L      = %s\n'%(self.L)
        txt += '.param W      = %s\n'%(self.W)
        txt += '.param M      = %s\n'%(self.M)
        txt += '.param VG     = %s\n'%(VGS + VS)
        txt += '.param VD     = %s\n'%(VD)
        txt += '.param VS     = %s\n'%(VS)
        txt += '.param VB     = %s\n'%(VB)
        txt += '%s d g s b %s W={W} L={L} M={M}\n\n'%(self.refDes, self.dev)
        txt += 'V1 dd 0  dc {VD}\n'
        txt += 'V2 g  0  dc {VG} ac 1\n'
        txt += 'V3 s  0  dc {VS}\n'
        txt += 'V4 b  0  dc {VB}\n'
        txt += 'L1 d  dd 1G\n'
        txt += '.end'
        f = open('MOS_noise.cir', 'w')
        f.write(txt)
        f.close()
        simCmd = 'noise V(d) V2 dec %s %s %s'%( str(numDec), str(fmin), str(fmax))
        namesDict = {'inoise': 'inoise_spectrum'}
        output = ngspice2traces('MOS_noise', simCmd, namesDict, stepCmd=None, traceType='onoise', squaredNoise=True)
        remove('MOS_noise.cir')
        remove('MOS_noise.csv')
        return output

def ngspice2traces(cirFile, simCmd, namesDict, stepCmd=None, parList=None, 
                   traceType='magPhase', squaredNoise=False):
    """
    Creates a dictionary with values or traces from an ngspice run.

    :param cirFile: Name of the circuit file withouit '.cir' extension, located
                    in the cir folder.

    :type cirFile: str

    :param simCmd: ngspice instruction,

                   - ac dec 20 1 10meg
                   - tran 1n 10u
                   - dc Source Vstart Vstop Vincr [ Source2 Vstart2 Vstop2 Vincr2 ]
                   - noise V(out) Vs dec 10 1 10meg 1
                   - op

    :type simCmd: str

    :param stepCmd: Step instruction or None if no parameter stepping is performed:

                    Syntax: *<parname> <stepmethod> <firstvalue> (<lastvalue> <numberofvalues | listwithvalues>)*
                    
                    - parname (*str*): name of the parameter (not a RefDes)
                    - stepmethod (*str*): lin, log or list

    :type stepCmd: str, nonetype

    :param namesDict: Dictionary with key-value pairs:

                      key: plot label (*str*)

                      value: nodal voltage, branch current or device parameter in ngspice notation
                      
    :type namesDict: dict

    :param traceType: Type of traces for AC analysis or noise analysis:

                      - realImag
                      - magPhase
                      - dBmagPhase
                      - onoise
                      - inoise
                      
    :type traceType: str
    
    :param parList: List with parameter definitions, each item in the list must 
                    be a tuple with the name and the value of a parameter. The
                    name must be a string, and the value a string, an integer, 
                    a float, or a SPICE expression (between curly brackets). 
                    The order of parameter definitions should be such that 
                    SPICE can evaluate a numeric value for each parameter in a
                    non-recursive way.
                    
                    :Example:
                        
                    >>> params = [('R', '1k'), ('C', '1n'), ('tau', '{1/(R*C)}')]
                    
    :type parList: list
    
    :param squaredNoise: - True: output in V^2/Hz, A^2/Hz, V^2 or A^2
                         - False: output in V/rt(Hz), A/rt(Hz), V or A
                         
                         Defaults to True
                         
    :type squaredNoise: Bool
    
    :return: - In case of an "OP" instruction without parameter stepping: 
             
               A dictionary with key-value pairs:
                   
               - key: *str* Name of the variable
               - value: *float* Value of the parameter, voltage or current
               
             - In all other cases: a tuple (*dict*, *str1*, *str2*)
             
               - dict
               
                 - key: *str* Name of the variable
                 - value: SLiCAP.SLiCAPplots.trace object or single value
                 
               - str1: name of the x-variable
               - str2: units if the x-variable
             
    :rtype: tuple: dict, (dict, str, str)
    """
    try:
        remove(cirFile + '.csv')
    except:
        pass
    labels = {}
    simType = simCmd.split()[0].lower()
    f = open(cirFile + '.cir', 'r')
    netlistlines = f.readlines()
    f.close()
    title = netlistlines[0].strip()
    netlist = ""
    for line in netlistlines:
        if line.strip().upper() != ".END":
            netlist += line   
    netlist += "** Python input section **"
    if parList != None:
        for pardef in parList:
            if pardef != None and len(pardef) == 2:
                netlist += "\n.param " + str(pardef[0]) + "=" + str(pardef[1])
    if stepCmd != None:
        stepFields = stepCmd.split()
        stepPar = stepFields[0]
        stepMethod = stepFields[1].lower()
        if stepMethod == 'list':
            try:
                stepList = eval(re.findall(r'\[[\s,.+-eE0-9]*\]', stepCmd)[0])
            except:
                print('Error in step list.')
                return
        else:
            try:
                stepStart  = float(_checkExpression(stepFields[2]))
            except:
                print('Error: missing or error in stepstart value.')
                return
            try:
                stepStop  = float(_checkExpression(stepFields[3]))
            except:
                print('Error: missing or error in stepCmd stop value.')
                return
            try:
                stepNum  = int(_checkExpression(stepFields[4]))
            except:
                print('Error: missing or error in step number.')
                return
        if stepMethod == 'lin':
            stepList = linspace(stepStart, stepStop, stepNum)
        elif stepMethod == 'log':
            stepList = geomspace(stepStart, stepStop, stepNum)
        for i in range(len(stepList)):
            cmdsection = ""
            traceNames = []
            if stepPar.lower() == "temp":
                cmdsection += '\n.option ' + stepPar + ' = ' + str(stepList[i])
            else:
                cmdsection += '\n.param ' + stepPar + ' = ' + str(stepList[i])
            cmdsection += '\n.control\n'
            if simType == 'noise' and squaredNoise:
                cmdsection += '\nset sqrnoise\n'
            cmdsection += simCmd + '\n'
            cmdsection += '\nset wr_vecnames\nset wr_singlescale\n'
            if simType == 'noise':
                totalNoise = False
                cmdsection += '\nsetplot noise1\n'
            for key in list(namesDict.keys()):
                if namesDict[key].lower().split("_")[-1] != "total":
                    traceName = key + '_' + str(i)
                    labels[traceName] = key + ':' + stepPar + '=' + '{0: 8.2e}'.format(stepList[i])
                    # remove whitespace (compact label)
                    labels[traceName] = ''.join(labels[traceName].split())
                    cmdsection += 'let ' + traceName + ' = ' + namesDict[key] + '\n'
                    traceNames.append(traceName)
                else:
                    totalNoise = True
            if simType == 'noise' and totalNoise:
                cmdsection += '\nsetplot noise2\n'
                for key in list(namesDict.keys()):
                    if namesDict[key].lower().split("_")[-1] == "total":
                        traceName = key + '_' + str(i)
                        labels[traceName] = key + ':' + stepPar + '=' + '{0: 8.2e}'.format(stepList[i])
                        # remove whitespace (compact label)
                        labels[traceName] = ''.join(labels[traceName].split())
                        cmdsection += 'let ' + traceName + ' = ' + namesDict[key] + '\n'
                        traceNames.append(traceName)
            if i > 0:
                cmdsection += "\nset appendwrite"
            cmdsection += '\nwrdata ' + cirFile  + '.csv'
            for name in traceNames:
                cmdsection += ' ' + name
            cmdsection += '\n.endc\n'
            if i == 0: 
                netlist += '\n.end'
            f = open('simFile.sp', 'w')
            f.write(netlist + cmdsection)
            f.close()
            system(ini.ngspice + ' -b simFile.sp -o simFile.log > temp.txt')
    else:
        netlist += '\n.control\nset wr_vecnames\nset wr_singlescale\n'
        if simType == 'noise' and squaredNoise:
            netlist += '\nset sqrnoise\n'
        netlist += simCmd + '\n'
        if simType == 'noise':
            totalNoise = False
            netlist += '\nsetplot noise1\n'
        for key in list(namesDict.keys()):
            if namesDict[key].lower().split("_")[-1] != "total":
                netlist += 'let ' + key + ' = ' + namesDict[key] + '\n'
            else:
                totalNoise = True
        if simType == 'noise' and totalNoise:
            netlist += '\nsetplot noise2\n'
            for key in  list(namesDict.keys()):
                if namesDict[key].lower().split("_")[-1] == "total":
                    netlist += 'let ' + key + ' = ' + namesDict[key] + '\n' 
        netlist += 'wrdata ' + cirFile + '.csv'
        for key in list(namesDict.keys()):
            netlist += ' ' + key
        netlist += '\n.endc'
        netlist += '\n.end'
        f = open('simFile.sp' , 'w')
        f.write(netlist)
        f.close()
        system(ini.ngspice + ' -b simFile.sp -o simFile.log > temp.txt')
    ##
    f = open(cirFile + '.csv', 'r')
    txt = f.read()
    f.close()
    analysisType = simCmd.split()[0].upper()
    if analysisType == 'DC':
        lines = txt.splitlines()
        xVar = lines[0].split()[0]
        labels[xVar] = simCmd.split()[1]
    if analysisType == 'NOISE' and totalNoise:
        lines = txt.splitlines()
        xVar = lines[0].split()[0]
        #print("X:", xVar)
        labels[xVar] = simCmd.split()[1]
        analysisType = "OP"
    if labels != None:
        for key in labels:
            txt = txt.replace(key + ' ', labels[key] + ' ')
    f = open(cirFile + '.csv', 'w')
    f.write(txt)
    f.close()
    #remove('simFile.sp')
    #remove('simFile.log')
    #remove('temp.txt')
    fileName = cirFile.split('/')[-1]
    copy2(cirFile + '.csv', ini.csv_path + fileName + '.csv')
    traceDict = _processNGspiceResult(cirFile, analysisType, traceType)
    return traceDict

def _processNGspiceResult(cirFile, analysisType, traceType):
    # Read the CSV file
    f = open(cirFile + '.csv', 'r')
    lines = f.readlines()
    f.close()
    analysisType = analysisType.upper()
    if analysisType == 'DC' or analysisType == 'TRAN' or analysisType == 'NOISE':
        traceDict = _makeDCTRNStraces(lines)
    elif analysisType.upper() == 'AC':
        traceDict = _makeACtraces(lines, traceType)
    elif analysisType == "OP":
        traceDict = _makeOPtraces(lines)
    else:
        raise NotImplementedError()
    return traceDict

def _makeOPtraces(lines):
    traceDict = {}
    varNames  = []
    stepPar   = None
    stepVals  = []
    step      = True
    for i in range(len(lines)):
        fields = lines[i].split()
        if i == 0:
            firstVar = fields[0]
            labels = [fields[j].strip() for j in range(1, len(fields))]
            for var in labels:
                try:
                    varName, parDef = var.split(":")
                    stepPar, stepVal = parDef.split("=")
                    varNames.append(varName)
                    traceDict[varName] = []
                except ValueError:
                    step = False
                    varNames.append(var)
                    traceDict[var] = []
        if step:
            if fields[0] == firstVar:
                var = fields[1].strip()
                varName, parDef = var.split(":")
                stepPar, stepVal = parDef.split("=")
            else:
                values = [eval(field) for field in fields]
                for j in range(1, len(values)):
                    traceDict[varNames[j-1]].append(values[j])
                stepVals.append(eval(stepVal))
        elif fields[0] != firstVar:
            values = [eval(fields[j]) for j in range(1, len(fields))]
            for j in range(1, len(fields)):
                traceDict[varNames[j-1]].append(values[j-1])
    if step:
        for key in list(traceDict.keys()):
            traceDict[key] = trace([stepVals, traceDict[key]])
            traceDict[key].label = key
        traceDict = (traceDict, stepPar, "")
    else:
        for key in traceDict.keys():
            traceDict[key] = traceDict[key][0]
    return traceDict

def _makeDCTRNStraces(lines):
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
    if xVar == "frequency":
        xUnits = "Hz"
    elif xVar == "time":
        xUnits = "s"
    else:
        xUnits = ""
    return traceDict, xVar, xUnits

def _makeACtraces(lines, traceType):
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
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real), discont=pi/4, period=pi/2)*180/pi))
            imPhsDict[key].label = key
        elif traceType == 'dBmagPhase':
            reMagDict[key] = trace((freq, 10*log10(real**2+imag**2)))
            reMagDict[key].label = key
            imPhsDict[key] = trace((freq, unwrap(arctan(imag/real), discont=pi/4, period=pi/2)*180/pi))
            imPhsDict[key].label = key
    if xVar == "frequency":
        xUnits = "Hz"
    else:
        xUnits = ""
    return reMagDict, imPhsDict, xVar, xUnits

def selectTraces(traceDict, namesList):
    """
    This function returns a dictionary selected traces from a dictionary with traces.
    
    :param traceDict: A dictionary with key-value pairs:
                      - key: name of the trace
                      - value: a SLiCAP.SLiCAPplots.trace object holding trace (x, y) data and a trace label
    
    :param namesList: A list with names of traces (== keys in traceDict) that needs to be returned
    :return:          a dictionary with selected traces (sub of traceDict)
    :rtype:           dict
    """
    traces = {}
    for key in traceDict.keys():
        if key in namesList:
            traces[key] = traceDict[key]
    return traces