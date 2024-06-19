#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 20 16:51:42 2021

@author: anton
"""

from SLiCAP import *
fileName = 'subCKTtest'

prj = initProject(fileName)
ini.dump()
i1=instruction()
i1.setCircuit(fileName + '.cir')
htmlPage('Element data')
netlist2html(fileName + '.cir')
elementData2html(i1.circuit)
