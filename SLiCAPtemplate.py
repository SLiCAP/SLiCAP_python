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
>>> LTSPICE     = 'wine ~/.wine/drive_c/Program\ Files/LTC/LTspiceXVII/XVIIx64.exe -wine -netlist'      # Command for netlist generation with LTspice
>>> KICAD       = ''    # Command for kicad-cli
>>> INKSCAPE    = ''    # Command for Inkscape
>>> NETLIST     = 'lepton-netlist -g spice-noqsi'   # Command for netlist generation with gschem or lepton-eda
"""
VERSION     = '$VERSION'
SYSINSTALL  = r'$SYSINSTALL'
USERPATH    = r'$USERPATH'
LIBCOREPATH = r'$LIBCOREPATH'
DOCPATH     = r'$DOCPATH'
LTSPICE     = r'$LTSPICE' # Command for netlist generation with LTspice
NGSPICE     = r'$NGSPICE' # Command for starting NGspice
KICAD       = r'$KICAD' # Command for starting KiCad-cli
INKSCAPE    = r'$INKSCAPE' # Command for starting Inkscape
NETLIST     = 'lepton-netlist -g spice-noqsi' # Command for netlist generation with gschem or lepton-eda