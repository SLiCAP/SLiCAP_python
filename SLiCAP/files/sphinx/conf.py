# -*- coding: utf-8 -*-

import time
import sphinx_bootstrap_theme
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinxcontrib.excel',
    'sphinxcontrib.excel_table',
]
templates_path = ['_templates']
source_suffix = '.rst'
source_encoding = 'utf-8-sig'
master_doc = 'index'
project = u'SLiCAP project'
copyright = u'The Company'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
numfig = True
def setup(app):
    app.add_stylesheet('custom.css')
todo_include_todos = False
html_theme = 'bootstrap'
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
html_title = u'SLiCAP project'
html_short_title = u'SLiCAP'
html_static_path = ['_static']
html_last_updated_fmt = time.strftime("%d/%m/%Y")
html_domain_indices = True
html_use_index = True
html_show_sourcelink = False
html_show_copyright = False
numfig = True
html_theme_options = {
    'navbar_title': "Home",
    'navbar_site_name': "Pages",
    'navbar_links': [('SLiCAP','https://analog-electronics.tudelft.nl/slicap/slicap')],
    'navbar_sidebarrel': True,
    'navbar_pagenav': True,
    'navbar_pagenav_name': "Page",
    'globaltoc_depth': 2,
    'globaltoc_includehidden': "true",
    'navbar_class': "navbar navbar-inverse",
    'navbar_fixed_top': "true",
    'bootswatch_theme': "cerulean",
    'bootstrap_version': "3",
}
