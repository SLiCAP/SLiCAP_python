#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
statespace.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

# The passive network of the manual: three states
pn = sl.makeCircuit("sch/myPassiveNetwork.slicap_sch")

ssResult = sl.doStateSpace(pn)
sl.listStateSpace(ssResult)

ss = ssResult.stateSpace
print(ss.x, ss.u, ss.y)
print(ss.A, ss.B, ss.C, ss.D)

# A capacitor across a voltage source: two capacitors, one state, and a
# source current that follows the derivative of the source voltage
cv = sl.makeCircuit("cir/CacrossV.cir")

cvResult = sl.doStateSpace(cv)
sl.listStateSpace(cvResult)

# Poles and zeros with the state-space engine instead of the determinant
pzResult = sl.doPZ(pn, pardefs="circuit", numeric=True, method="state")
sl.listPZ(pzResult)

# Generate RST snippets for the Help file
rst = sl.RSTformatter()
rst.stateSpace(ssResult, label="eqn-ss-PN").save("eqn-ss-PN")
rst.stateSpace(ssResult, label="eqn-ss-PN-Ax", parts=("x", "A")).save("eqn-ss-PN-Ax")
rst.stateSpace(cvResult, label="eqn-ss-CV").save("eqn-ss-CV")
rst.stateSpace(cvResult, label="eqn-ss-CV-D", parts=("y", "D")).save("eqn-ss-CV-D")

# Generate LaTeX snippets
ltx = sl.LaTeXformatter()
ltx.stateSpace(ssResult, label="eqn-ss-PN").save("eqn-ss-PN")
ltx.stateSpace(cvResult, label="eqn-ss-CV").save("eqn-ss-CV")
