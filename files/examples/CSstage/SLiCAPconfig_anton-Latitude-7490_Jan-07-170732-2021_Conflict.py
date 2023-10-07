#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLiCAP module with user-defined path settings.

Default values:

>>> PROJECTPATH = None      # Leave it for automatic detection
>>> # PATHS: relative to the project path
>>> HTMLPATH    = 'html/'   # path for html output
>>> CIRCUITPATH = 'cir/'    # path for .asc, .net, .cir, .sch files
>>> LIBRARYPATH = 'lib/'    # path for include and library files
>>> TXTPATH     = 'txt/'    # path for text files (text2html)
>>> CSVPATH     = 'csv/'    # path for CSV files (csv2html)
>>> LATEXPATH   = 'tex/'    # path for LaTeX output saveTeX()
>>> MATHMLPATH  = 'mathml/' # path for mathML output saveMathML()
>>> IMGPATH     = 'img/'    # path for image files
"""
PROJECTPATH = None      # Leave it for automatic detection
# PATHS: relative to the project path
HTMLPATH    = 'html/'   # path for html output
CIRCUITPATH = 'cir/'    # path for .asc, .net, .cir, .sch files
LIBRARYPATH = 'lib/'    # path for include and library files
TXTPATH     = 'txt/'    # path for text files (text2html)
CSVPATH     = 'csv/'    # path for CSV files (csv2html)
LATEXPATH   = 'tex/'    # path for LaTeX output saveTeX()
MATHMLPATH  = 'mathml/' # path for mathML output saveMathML()
IMGPATH     = 'img/'    # path for image files


# Project information
PROJECT    = 'CS stage noise with resistive source'
AUTHOR     = 'anton'
CREATED    = '2020-12-16 18:02:29.160355'
LASTUPDATE = '2021-01-03 14:55:04.116631'