#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
math.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl
import sympy as sp

###############################################################################
# work with analysis results
###############################################################################

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()