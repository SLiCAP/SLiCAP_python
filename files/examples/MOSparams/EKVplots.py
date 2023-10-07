#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 19:15:00 2020

@author: anton
"""

from SLiCAP import *
t1 = time()

prj = initProject('NMOS EKV plots') # Creates the SLiCAP libraries and the
                             # project HTML index page

fileName = 'mosEKVplots.cir'
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
i1.stepOn()
i1.setStepVar('V_G')
i1.setStepStart(0.001)
i1.setStepStop(1.8)
i1.setStepNum(10)
i1.setStepMethod('lin')
result = i1.execute()

fig_Ids_Vds = plotSweep('IdsVds', '$I_{ds}(V_{ds})$', result, 0, 1.8, 50, sweepVar= 'V_D', xUnits = 'V', yVar = 'I_DS_X1', yScale = 'u', yUnits = 'A', funcType = 'param', show = True)
fig2html(fig_Ids_Vds, 600)

i1.setStepVar('V_D')
result = i1.execute()

fig_Ids_Vgs = plotSweep('IdsVgs', '$I_{ds}(V_{gs})$', result, 0, 1.8, 50, sweepVar= 'V_G', xUnits = 'V', yVar = 'I_DS_X1', yScale = 'u', yUnits = 'A', funcType = 'param', show = True)
fig2html(fig_Ids_Vgs, 600)

fig_gm_Ids  = plotSweep('gmIds', '$g_m(I_{ds})$', result, 0, 1.8, 50, sweepVar= 'V_G', xVar = 'I_DS_X1', xScale = 'u', xUnits = 'A', yVar = 'g_m_X1', yScale = 'u', yUnits = 'S', funcType = 'param', show = True)
fig2html(fig_gm_Ids, 600)

fig_fT_Ids  = plotSweep('fTIds', '$f_{T}(I_{ds})$', result, 0, 1.8, 50, sweepVar= 'V_G', xVar = 'I_DS_X1', xScale = 'u', xUnits = 'A', yVar = 'f_T_X1', yScale = 'G', yUnits = 'Hz', funcType = 'param', show = True)
fig2html(fig_fT_Ids, 600)

fig_CissVg  = plotSweep('CissVg', '$c_{iss}(V_{gs})$', result, 0, 1.8, 50, sweepVar= 'V_G', xScale = '', xUnits = 'V', yVar = 'c_iss_X1', yScale = 'f', yUnits = 'F', funcType = 'param', show = True)
fig2html(fig_CissVg, 600)

t2=time()
print(t2-t1,'s')