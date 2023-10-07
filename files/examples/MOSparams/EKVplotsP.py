#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 19:15:00 2020

@author: anton
"""

from SLiCAP import *
t1 = time()

#prj = initProject('PMOS EKV plots') # Creates the SLiCAP libraries and the
                             # project HTML index page

fileName = 'mosEKVplotsP.cir'
i1 = instruction()           # Creates an instance of an instruction object
i1.setCircuit(fileName)      # Checks and defines the local circuit object and
                             # sets the index page to the circuit index page                       
htmlPage('Circuit data')
netlist2html(fileName)

elementData2html(i1.circuit)
params2html(i1.circuit)

# Put the plots on a page
htmlPage('CMOS18 EKV model plots')

i1.setDataType('params')

result = i1.execute()

fig_Ids_Vgs  = plotSweep('IdsVgs', '$V_{gs}(I_{ds})$', result, -1e-3, -45, 200, sweepVar= 'I_D', sweepScale = 'u', yVar = 'I_D', yUnits = 'A', yScale = 'u',  xVar = 'V_GS_X1', xUnits = 'V', funcType = 'param', show = True)
fig2html(fig_Ids_Vgs, 600)

fig_gm_Ids  = plotSweep('gmIds', '$g_m(I_{ds})$', result, 0, -45, 100, sweepVar= 'I_D', sweepScale = 'u', xUnits = 'A', yVar = 'g_m_X1', yScale = 'u', yUnits = 'S', funcType = 'param', show = True)
fig2html(fig_gm_Ids, 600)

fig_fT_Ids  = plotSweep('fTIds', '$f_{T}(I_{ds})$', result, 0, -45, 100, sweepVar= 'I_D', sweepScale = 'u', xUnits = 'A', yVar = 'f_T_X1', yScale = 'G', yUnits = 'Hz', funcType = 'param', show = True)
fig2html(fig_fT_Ids, 600)

t2=time()
print(t2-t1,'s')
"""
LTspiceTraces =  LTspiceData2Traces('nmosChar.txt')
traces2fig(LTspiceTraces, fig_Ids_Vgs)
fig_Ids_Vgs.plot()

figLT = plot('LTspiceIdsVgs', 'LTspice $I_{ds}(V_{gs})$', 'lin', LTspiceTraces, xName = '$V_{gs}$', xUnits = 'V', yName = '$I_{ds}$', yUnits = 'A', yScale = 'u', show = True)
"""