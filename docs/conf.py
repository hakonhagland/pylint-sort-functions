# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib.util
import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pylint-sort-functions"
copyright = "2025, Håkon Hægland"
author = "Håkon Hægland"
release = "0.1"

# -- General configuration ---------------------------------------------------

sys.path.insert(0, os.path.abspath("../src"))
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx_autodoc_typehints",
]

# Enable Markdown support (if myst-parser is available)
if importlib.util.find_spec("myst_parser") is not None:
    extensions.append("myst_parser")
    source_suffix = {
        ".rst": None,
        ".md": None,
    }

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Use Read the Docs theme if available, otherwise default
if importlib.util.find_spec("sphinx_rtd_theme") is not None:
    html_theme = "sphinx_rtd_theme"
else:
    html_theme = "default"
html_static_path = ["_static"]
html_context = {
    "display_github": True,
    "github_user": "hakonhagland",
    "github_repo": "pylint-sort-functions",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
autodoc_default_options = {
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "members": True,
    "show-inheritance": True,
}
