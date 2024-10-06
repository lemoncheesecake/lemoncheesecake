# -*- coding: utf-8 -*-

import os
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

project = 'lemoncheesecake'
copyright = '2024, Nicolas Delon'
author = 'Nicolas Delon'

version = __version__
release = __version__

language = "en"

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

html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    if "html_context" not in globals():
        html_context = {}
    html_context["READTHEDOCS"] = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "lemoncheesecake": ("http://docs.lemoncheesecake.io/en/latest", None),
    "requests": ("https://docs.python-requests.org/en/latest", None)
}