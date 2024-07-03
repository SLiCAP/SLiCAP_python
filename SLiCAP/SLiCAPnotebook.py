#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main module for working with SLiCAP from within Jupyter Notebook or Jupyter Lab.

This module imports specific modules for rendering HTML and SVG in notebooks. It
also sets the configuration variable *ini.notebook* that provides correct latex
output from the functions in the module **SLiCAPhtml.py**.

It also activates a work around for rendering reStructured text (.rst files)
in notebooks.
"""

from IPython.core.display import HTML, SVG
from IPython.core.magic import register_cell_magic, register_line_magic
from IPython.display import Image

# Work around for displaying rst in jupyter notebooks

@register_cell_magic
def rst(line, cell):
    """
    Render ReStructuredText:
        
        %%rst
        ============
         Main title
        ============
    """
    writer = docutils.writers.html5_polyglot.Writer()
    return HTML(docutils.core.publish_string(cell, writer=writer).decode('UTF-8'))

@register_line_magic
def rstfile(filename):
    """
    Render ReStructuredText file:
    
        %rstfile <file name>
    """
    writer = docutils.writers.html5_polyglot.Writer()
    with open(filename, 'r') as file:
        cell = file.read()
    return HTML(docutils.core.publish_string(cell, writer=writer).decode('UTF-8'))

