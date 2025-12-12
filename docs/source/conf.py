# Sphinx configuration for Axion-HDL documentation

import os
import sys

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'Axion-HDL'
copyright = '2025, Bugra Tufan'
author = 'Bugra Tufan'

# Get version from .version file
version_file = os.path.join(os.path.dirname(__file__), '../../.version')
if os.path.exists(version_file):
    with open(version_file) as f:
        release = f.read().strip()
else:
    release = '0.6.0'

version = '.'.join(release.split('.')[:2])

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

# MyST parser for Markdown support
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]

# Source file suffixes
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master document
master_doc = 'index'

# Templates and static files
templates_path = ['_templates']
exclude_patterns = []
html_static_path = ['_static']

# HTML theme
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
