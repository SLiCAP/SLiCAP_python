# -*- coding: utf-8 -*-
from time import strftime
project = u'SLiCAP Sphinx'
html_title = u'SLiCAP Sphinx web reports'
html_short_title = u'SLiCAP'
copyright = u'2024-2025, Anton Montagne'
author = u'Anton Montagne'
extensions = ['sphinx.ext.mathjax', 
              'sphinx_panels', 
              'sphinxcontrib.bibtex', 
              'sphinx.ext.autosectionlabel', 
              'sphinx_togglebutton', 
              'sphinx_tabs.tabs']
autosectionlabel_prefix_document = False
autosectionlabel_maxdepth = None
bibtex_bibfiles = []
source_suffix = '.rst'
master_doc = 'index'
language = 'English'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = 'sphinx'
html_theme = 'sphinx_book_theme'
html_last_updated_fmt = strftime("%d/%m/%Y")
html_domain_indices = True
html_use_index = True
html_show_sourcelink = False
html_show_copyright = True
math_eqref_format = "({number})"
numfig = True
