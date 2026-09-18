# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib import metadata


# -- Project information -----------------------------------------------------
project = "LoopWeave"
copyright = "2026 LoopWeave Authors"
author = "LoopWeave Team"
_package_version = metadata.version("loopweave")

version = _package_version
release = _package_version

# -- General configuration ---------------------------------------------------
extensions = ["myst_parser", "sphinx_design", "sphinx.ext.mathjax"]

templates_path = ["../_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "linkify",
    "strikethrough",
    "amsmath",
    "dollarmath",
    "html_admonition",
    "html_image",
]
myst_heading_anchors = 5

# -- Options for HTML output -------------------------------------------------
language = "en"

html_theme = "sphinxawesome_theme"
html_static_path = ["../_static"]
html_css_files = ["custom.css"]
html_js_files = ["custom.js"]

html_logo = "../_static/logo_wo_text.svg"
html_favicon = "../_static/logo_wo_text.svg"
html_title = "LoopWeave"
html_meta = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

# Sidebar templates
html_sidebars = {
    "**": [
        "sidebar_main_nav_links.html",
        "sidebar_toc.html",
    ],
}

# Hide "Show Source" link
html_show_sourcelink = False

# Hide copyright and sphinx info in footer
html_show_copyright = False
html_show_sphinx = False

# Pygments style
pygments_style = "sphinx"
pygments_dark_style = "monokai"
