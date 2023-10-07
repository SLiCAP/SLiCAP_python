#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SLiCAP module with settings defined on install, contains fixed parameters

Default parameters:

>>> VERSION     = None  # Version number
>>> SYSINSTALL  = ''    # System install path
>>> USERPATH    = ''    # User install path
>>> LIBCOREPATH = ''    # Library install path
>>> DOCPATH     = ''    # Documentation install path
>>> LTSPICE     = 'wine ~/.wine/drive_c/Program\ Files/LTC/LTspiceXVII/XVIIx64.exe -wine -netlist' # Command for netlist generation with LTspice
>>> NETLIST     = 'lepton-netlist -g spice-noqsi' # Command for netlist generation with gschem or lepton-eda
"""
VERSION     = '2.0.1'
SYSINSTALL  = r' '
USERPATH    = r'/home/charles/SLiCAP'
LIBCOREPATH = r'/home/charles/SLiCAP/lib'
DOCPATH     = r'/home/charles/SLiCAP/docs'
LTSPICE     = r'/home/charles/.wine/drive_c/Program Files/LTC/LTspiceXVII/XVIIx64.exe' # Command for netlist generation with LTspice
NETLIST     = 'lepton-netlist -g spice-noqsi' # Command for netlist generation with gschem or lepton-eda
