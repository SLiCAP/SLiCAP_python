#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dcvar.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp

# Define the circuit
cir = sl.makeCircuit("kicad/dcMatchingTracking/dcMatchingTracking.kicad_sch")
# Perform dc variance analysis
dcvarResult = sl.doDCvar(cir, source="V1", detector="V_out", pardefs="circuit")

dcSolve     = dcvarResult.dcSolve
Iv, M, Dv   = dcvarResult.Iv, dcvarResult.M, dcvarResult.Dv
print(dcvarResult.Dv, "=", dcSolve)

ovar        = dcvarResult.ovar
print(ovar)

ivar        = dcvarResult.ivar
print(ivar)

svarTerms = dcvarResult.svarTerms
ovarTerms = dcvarResult.ovarTerms
ivarTerms = dcvarResult.ivarTerms
for term in svarTerms:
    print("\n= " + term + " =")
    print("value        :", svarTerms[term])
    print("det-referred :", ovarTerms[term])
    print("src-referred :", ivarTerms[term])

# Define the model parameters: set tolerances and temperature coefficients to 0
cir.defPar("TC_V", 0)          # Relative temperature coefficient of 
                               # voltage source [1/K]
cir.defPar("TC_R", 0)          # Relative temperature coefficient of 
                               # resistors [1/K]
cir.defPar("sigma_V", 0)       # Standard deviation of voltage source [V]
cir.defPar("sigma_R", 0)       # Relative standard deviation of resistors 
                               # of resistors belonging to lot_1 [-]
cir.defPar("sigma_m_R", 0)     # Relative standard deviation of mismatch 
                               # between resistors from lot_1 [-]
cir.defPar("sigma_TC_R", 0)    # Standard deviation of relative temperature 
                               # coefficient of resistors [1/K]
cir.defPar("sigma_TC_tr_R", 0) # Standard deviation of mismatch between relative 
                               # temperature coefficients of resistors from 
                               # lot_1 [1/K]

###############################################################################
# No tolerances and no temperature coefficients
###############################################################################
dcVarResult_1a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_1      = dcVarResult_1a.dcSolve
idx_v          = cir.depVars().index('V_out')
Vout_1         = sp.simplify(dcSolve_1[idx_v])
dcVarResult_1b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
idx_i          = cir.depVars().index('I_V1')
IV1_1          = sp.simplify(dcVarResult_1b.dcSolve[idx_i])
I_ovar_1       = sp.simplify(dcVarResult_1b.ovar)
print("\nCase 1")
print("V_out     :", Vout_1)     
print("I(V1)     :", IV1_1)     
print("var{I(V1)}:", I_ovar_1)  

###############################################################################
# Only DC voltage soure with standard deviation
###############################################################################
cir.delPar("sigma_V")

dcVarResult_2a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_2      = dcVarResult_2a.dcSolve
Vout_2         = sp.simplify(dcSolve_2[idx_v])
dcVarResult_2b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_2          = sp.simplify(dcVarResult_2b.dcSolve[idx_i])
I_ovar_2       = sp.simplify(dcVarResult_2b.ovar)
print("\nCase 2")
print("V_out     :", Vout_2)     
print("I(V1)     :", IV1_2)     
print("var{I(V1)}:", I_ovar_2)  

###############################################################################
# Only DC voltage soure with temperature coefficient
###############################################################################
cir.defPar("sigma_V", 0)
cir.delPar("TC_V")

dcVarResult_3a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_3      = dcVarResult_3a.dcSolve
Vout_3         = sp.simplify(dcSolve_3[idx_v])
dcVarResult_3b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_3          = sp.simplify(dcVarResult_3b.dcSolve[idx_i])
I_ovar_3       = sp.simplify(dcVarResult_3b.ovar)
print("\nCase 3")
print("V_out     :", Vout_3)     
print("I(V1)     :", IV1_3)     
print("var{I(V1)}:", I_ovar_3)  

###############################################################################
# Only DC voltage soure with standard deviation and temperature coefficient
###############################################################################
cir.delPar("sigma_V")

dcVarResult_4a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_4      = dcVarResult_4a.dcSolve
Vout_4         = sp.simplify(dcSolve_4[idx_v])
dcVarResult_4b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_4          = sp.simplify(dcVarResult_4b.dcSolve[idx_i])
I_ovar_4       = sp.simplify(dcVarResult_4b.ovar)
print("\nCase 4")
print("V_out     :", Vout_4)     
print("I(V1)     :", IV1_4)     
print("var{I(V1)}:", I_ovar_4)  

###############################################################################
# Only (relative) standard deviation of resistor values with perfect matching
###############################################################################
cir.defPar("sigma_V", 0) # Standard deviation of voltage source [V]
cir.defPar("TC_V", 0)    # Rel.temperature coefficient of voltage source [1/K]
cir.delPar("sigma_R")

dcVarResult_5a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_5      = dcVarResult_5a.dcSolve
Vout_5         = sp.simplify(dcSolve_5[idx_v])
dcVarResult_5b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_5          = sp.simplify(dcVarResult_5b.dcSolve[idx_i])
I_ovar_5       = sp.simplify(dcVarResult_5b.ovar)
print("\nCase 5")
print("V_out     :", Vout_5)     
print("I(V1)     :", IV1_5)     
print("var{I(V1)}:", I_ovar_5)  

###############################################################################
# Only (relative) standard deviation of resistor values with perfect matching 
# and temperature tracking
###############################################################################
cir.delPar("TC_R")

dcVarResult_6a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_6      = dcVarResult_6a.dcSolve
Vout_6         = sp.simplify(dcSolve_6[idx_v])
dcVarResult_6b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_6          = sp.simplify(dcVarResult_6b.dcSolve[idx_i])
I_ovar_6       = sp.simplify(dcVarResult_6b.ovar)
print("\nCase 6")
print("V_out     :", Vout_6)     
print("I(V1)     :", IV1_6)     
print("var{I(V1)}:", I_ovar_6)  
 
###############################################################################
# Only (relative) standard deviation of resistor values with imperfect 
# matching and temperature tracking
###############################################################################
cir.delPar("sigma_m_R")
cir.delPar("sigma_TC_R")
cir.delPar("sigma_TC_tr_R")

dcVarResult_7a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_7      = dcVarResult_6a.dcSolve
Vout_7         = sp.simplify(dcSolve_7[idx_v])
dcVarResult_7b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_7          = sp.simplify(dcVarResult_7b.dcSolve[idx_i])
I_ovar_7       = sp.simplify(dcVarResult_7b.ovar)
print("\nCase 7")
print("V_out     :", Vout_7)     
print("I(V1)     :", IV1_7)     
print("var{I(V1)}:", I_ovar_7)  

###############################################################################
# DC voltage soure with standard deviation and temperature coefficient and 
# (relative) standard deviation of resistor values with imperfect matching 
# and temperature tracking
###############################################################################
cir.delPar("TC_V")
cir.delPar("sigma_V")
cir.delPar("sigma_TC_V")

dcVarResult_8a = sl.doDCvar(cir, detector="V_out", pardefs="circuit")
dcSolve_8      = dcVarResult_8a.dcSolve
Vout_8         = sp.simplify(dcSolve_8[idx_v])
dcVarResult_8b = sl.doDCvar(cir, detector="I_V1", pardefs="circuit")
IV1_8          = sp.simplify(dcVarResult_8b.dcSolve[idx_i])
I_ovar_8       = sp.simplify(dcVarResult_8b.ovar)
print("\nCase 8")
print("V_out     :", Vout_8)     
print("I(V1)     :", IV1_8)     
print("var{I(V1)}:", I_ovar_8)   

# Create an RST formatter
rst = sl.RSTformatter()
# Save expressions in the sphinx/SLiCAPdata folder of the project directory
rst.eqn(dcvarResult.Dv, dcSolve).save("eqn-dcSolve")
rst.matrixEqn(Iv, M, Dv).save("eqn-dcMatrix")
rst.eqn("(sigma_o)^2", ovar, units="V**2").save("eqn-ovar")
rst.eqn("(sigma_i)^2", ivar, units="V**2").save("eqn-ivar")
rst.dcvarContribs(dcvarResult, "DC variance contributions").save("table-varContribs")
rst.eqn("(sigma_I_V1)^2", I_ovar_1, units="A**2").save("eqn-I_ovar_1")
rst.eqn("(sigma_I_V1)^2", I_ovar_2, units="A**2").save("eqn-I_ovar_2")
rst.eqn("(sigma_I_V1)^2", I_ovar_3, units="A**2").save("eqn-I_ovar_3")
rst.eqn("(sigma_I_V1)^2", I_ovar_4, units="A**2").save("eqn-I_ovar_4")
rst.eqn("(sigma_I_V1)^2", I_ovar_5, units="A**2").save("eqn-I_ovar_5")
rst.eqn("(sigma_I_V1)^2", I_ovar_6, units="A**2").save("eqn-I_ovar_6")
rst.eqn("(sigma_I_V1)^2", I_ovar_7, units="A**2").save("eqn-I_ovar_7")
rst.eqn("(sigma_I_V1)^2", I_ovar_8, units="A**2").save("eqn-I_ovar_8")