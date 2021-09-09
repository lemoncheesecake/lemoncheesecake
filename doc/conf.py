# -*- coding: utf-8 -*-

import os.path as osp
import sys
sys.path.insert(0, osp.join(osp.dirname(__file__), ".."))

from lemoncheesecake import __version__


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx"
]

autodoc_typehints = "description"
autodoc_member_order = "bysource"

templates_path = ['_templates']


source_suffix = ['.rst']

master_doc = 'toc'

project = u'lemoncheesecake'
copyright = u'2021, Nicolas Delon'
author = u'Nicolas Delon'

version = __version__
release = __version__

language = None

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

todo_include_todos = False

html_theme = 'alabaster'
html_theme_options = {
    "page_width": "1150px",
    "sidebar_width": "300px",
}
html_show_sourcelink = False
html_static_path = ['_static']
html_sidebars = {
    '**': [
        'logo.html',
        'relations.html',  # needs 'show_related': True theme option to display
        'navigation.html',
        'links.html',
        'searchbox.html',
    ]
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "lemoncheesecake": ("http://docs.lemoncheesecake.io/en/latest", None),
    "requests": ("https://docs.python-requests.org/en/latest", None)
}