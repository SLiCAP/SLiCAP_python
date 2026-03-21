#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pz.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

pz_network = sl.makeCircuit("kicad/pzNetwork/pzNetwork.kicad_sch")

pResult    = sl.doPoles(pz_network)
print(pResult.poles)

pResult_num = sl.doPoles(pz_network, pardefs="circuit")
print(pResult_num.poles)

zResult     = sl.doZeros(pz_network)
print(zResult.zeros)

zResult_num = sl.doZeros(pz_network, pardefs="circuit")
print(zResult_num.zeros)

pzResult   = sl.doPZ(pz_network)
print(pzResult.DCvalue)
print(pzResult.poles)
print(pzResult.zeros)

pzResult_num   = sl.doPZ(pz_network, pardefs="circuit")
sl.listPZ(pzResult_num)

M        = pzResult.M
Iv       = pzResult.Iv
Dv       = pzResult.Dv
denom    = pzResult.denom
numer    = pzResult.numer
transfer = pzResult.laplace

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

rst.pz(pResult     , caption="Poles").save("table-P")
rst.pz(pResult_num , caption="Poles").save("table-Pnum")
rst.pz(zResult     , caption="Zeros").save("table-Z")
rst.pz(zResult_num , caption="Zeros").save("table-Znum")
rst.pz(pzResult    , caption="Observable poles and  zeros").save("table-PZ")
rst.pz(pzResult_num, caption="Observable poles and  zeros").save("table-PZnum")

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()

ltx.pz(pResult     , caption="Poles").save("table-P")
ltx.pz(pResult_num , caption="Poles").save("table-Pnum")
ltx.pz(zResult     , caption="Zeros").save("table-Z")
ltx.pz(zResult_num , caption="Zeros").save("table-Znum")
ltx.pz(pzResult    , caption="Observable poles and  zeros").save("table-PZ")
ltx.pz(pzResult_num, caption="Observable poles and  zeros").save("table-PZnum")