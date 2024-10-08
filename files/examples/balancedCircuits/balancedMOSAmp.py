#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
import SLiCAP as sl

cir = sl.makeCircuit(sl.ini.cir_path + "balancedMOSAmp.asc", imgWidth=600)

sl.htmlPage("DM-CM decomposition")
# Define the decomposition
sl.head2html("MNA matrix equation")

sl.matrices2html(sl.doMatrix(cir, pardefs=None))

sl.head2html("DM-CM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='all'))

sl.head2html("DM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='dd'))

sl.head2html("CM matrix equation")
sl.matrices2html(sl.doMatrix(cir, pardefs=None, convtype='cc'))

sl.htmlPage("Loop Gain")
sl.head2html("Loop Gain of the DM transfer")
result = sl.doLaplace(cir, transfer='loopgain', pardefs='circuit', 
                      convtype='dd', numeric=True)
sl.eqn2html("L_G", result.laplace)