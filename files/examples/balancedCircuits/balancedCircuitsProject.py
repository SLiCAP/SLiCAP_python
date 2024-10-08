#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 17:14:45 2023

@author: anton
"""
import SLiCAP as sl

prj = sl.initProject("Balanced circuits")

from Tcircuit1 import *
from balancedAmp import *
from balancedMOSAmp import *
