import sys

# Do not touch these. They use the local docstrfmt over the global docstrfmt.
sys.path.insert(0, ".")
sys.path.insert(1, "..")

from docstrfmt.const import __version__  # noqa: E402

extensions = ["sphinx.ext.autodoc", "sphinxcontrib.mermaid"]
html_static_path = []
html_theme_options = {"collapse_navigation": True}
htmlhelp_basename = "docstrfmt"
intersphinx_mapping = {}
master_doc = "index"
nitpick_ignore = []
nitpicky = True
project = "docstrfmt"
pygments_style = "sphinx"
release = __version__
source_suffix = ".rst"
suppress_warnings = ["image.nonlocal_uri"]
version = ".".join(__version__.split(".", 2)[:2])
