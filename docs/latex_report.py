#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
latex_report.py: SLiCAP scripts for the HTML help file
"""
import SLiCAP as sl

# Generate RST snippets for the Help file
rst = sl.RSTformatter()

# Generate LaTeX snippets for the Help file
ltx = sl.LaTeXformatter()