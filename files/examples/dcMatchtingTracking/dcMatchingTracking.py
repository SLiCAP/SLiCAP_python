#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 08:17:42 2023

@author: anton

voltage and current sources:

    - The 'dcvar' parameter is absolute variance (squared standard deviation
      sigma), in V^2 or A^2, respectively:

      V nodeP nodeN V value={V_DC} dcvar={(sigma_V*V_DC)^2}

    - Temperature dependency can be modeled by making the value a function of
      the absolute temperature T, of of some relative change with respect to the
      default temperature:

      V nodeP nodeN R value={V_DC*(1+T_Delta*TC_V)}

    - Tolerances on the temperature coefficient can be added by letting the
      variance depend on temperature:

      V nodeP nodeN V value={V_DC*(1+T_Delta*TC_V)} dcvar={(sigma_V*V_DC)^2 + (sigma_TC_V*V_DC*T_Delta)^2}

    - Matching and temperature tracking for voltage sources and current sources
      has not (yet) been implemented.

Resistors

    - 'dcvar' parameter is the non matching part of the relative variance
      (squared relative standard deviation sigma). Hence, an individual relative
      standard deviation of 1% corresponds with 0.0001.

      R nodeP nodeN R value={R_a} dcvar={sigma_R^2}

      The temperature behavior can be modeled by letting the value depend on temperature:

      R nodeP nodeN R value={R_a * (1 + T_Delta*TC_R)} dcvar={sigma_R^2}

      T_Delta is the difference between the temperature at which the resistance
      equals R_a, and the actual temperature. TC_R is the relative temperature
      coefficient [1/K]. If this temperature dependency is applied for multiple
      resistors they are tracking over temperature.

      The 'dcvarlot' parameter holds the correlated part of the variance of the value
      as well as the correlated part of the variance of the temperature coefficient.

      Below the definition of two resistors from one lot (lot_1).
      All resistors of this lot have a relative standard deviation 'sigma_R'.
      The standard deviation of their matching error is 'sigma_m_R'.
      The reproducible part of their temperature drift is modeled with TC_R and
      its standard deviation with sigma_TC_R. The standard deviation of
      temperature tracking error is sigma_T_tr_R

      R1 nodeP1 nodeN1 R value={R_a*(1+T_Delta*TC_R)} dcvar={sigma_m_R^2/2 + (sigma_TC_tr_R*T_Delta)^2/2} dcvarlot={lot_1}
      R2 nodeP2 nodeN2 R value={R_b*(1+T_Delta*TC_R)} dcvar={sigma_m_R^2/2 + (sigma_TC_tr_R*T_Delta)^2/2} dcvarlot={lot_1}
      .param lot_1 = {sigma_R^2 + (sigma_TC_R*T_Delta)^2}
"""
from SLiCAP import *

def createOutput(instr):
    params2html(i1.circuit)
    instr.setDetector("V_out")
    dcVarResult = instr.execute()
    Vout = sp.simplify(dcVarResult.dcSolve[instr.depVars().index('V_out')])
    eqn2html("V_out", Vout)
    eqn2html("sigma_Vout^2", sp.simplify(dcVarResult.ovar))

    instr.setDetector("I_V1")
    dcVarResult = instr.execute()
    IV1 = sp.simplify(dcVarResult.dcSolve[instr.depVars().index('I_V1')])
    eqn2html("I_V1", IV1)
    eqn2html("sigma_IV1^2", sp.simplify(dcVarResult.ovar))

prj = initProject("DCVAR")

i1 = instruction()

fileName = "dcMatchingTracking"
i1.setCircuit(fileName + ".cir")
i1.setSimType("numeric")
i1.setGainType("vi")
i1.setDataType("dcvar")

htmlPage("Circuit data")
head2html("Circuit diagram")
img2html(fileName + ".svg", 600)
netlist2html(fileName + ".cir")
elementData2html(i1.circuit)
params2html(i1.circuit)

htmlPage("DC matching-tacking demo")
head2html("Circuit diagram")
img2html(fileName + ".svg", 600)
head2html("No tolerances and no temperature coefficients")

i1.defPar("TC_V", 0)          # Relative temperature coefficient of voltage source [1/K]
i1.defPar("TC_R", 0)          # Relative temperature coefficient of resistors [1/K]
i1.defPar("sigma_V", 0)       # Standard deviation of voltage source [V]
i1.defPar("sigma_R", 0)       # Relative standard deviation of resistors of lot_1 [-]
i1.defPar("sigma_m_R", 0)     # Relative standard deviation of mismatch between resistors from lot_1 [-]
i1.defPar("sigma_TC_R", 0)    # Standard deviation of relative temperature coefficient of resistors [1/K]
i1.defPar("sigma_TC_tr_R", 0) # Standard deviation of mismatch between relative temperature coefficients of resistors from lot_1 [1/K]

createOutput(i1)

###############################################################################
head2html("Only DC voltage soure with standard deviation")
i1.delPar("sigma_V")
createOutput(i1)

###############################################################################
head2html("Only DC voltage soure with temperature coefficient")
i1.defPar("sigma_V", 0)       # Standard deviation of voltage source [V]
i1.delPar("TC_V")
createOutput(i1)

###############################################################################
head2html("Only DC voltage soure with standard deviation and temperature coefficient")
i1.delPar("sigma_V")
createOutput(i1)

###############################################################################
head2html("Only (relative) standard deviation of resistor values with perfect matching")
i1.defPar("sigma_V", 0)       # Standard deviation of voltage source [V]
i1.defPar("TC_V", 0)          # Relative temperature coefficient of voltage source [1/K]
i1.delPar("sigma_R")
createOutput(i1)

###############################################################################
head2html("Only (relative) standard deviation of resistor values with perfect matching and temperature tracking")
i1.delPar("TC_R")
createOutput(i1)

###############################################################################
head2html("Only (relative) standard deviation of resistor values with imperfect matching and temperature tracking")
i1.delPar("sigma_m_R")
i1.delPar("sigma_TC_R")
i1.delPar("sigma_TC_tr_R")
createOutput(i1)

###############################################################################
head2html("DC voltage soure with standard deviation and temperature coefficient and (relative) standard deviation of resistor values with imperfect matching and temperature tracking")
i1.delPar("TC_V")
i1.delPar("sigma_V")
i1.delPar("sigma_TC_V")
createOutput(i1)
