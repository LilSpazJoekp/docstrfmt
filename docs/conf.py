"""Configuration file for the Sphinx documentation builder."""

from datetime import datetime
from importlib.metadata import version as _pkg_version

__version__ = _pkg_version("docstrfmt")

author = "Joel Payne"
copyright = f"{datetime.today():%Y}, {author}"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "examples/**.rst"]
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_click",
]
html_static_path = ["_static"]
html_theme = "furo"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "click": ("https://click.palletsprojects.com/en/stable", None),
}
language = "en"
master_doc = "index"
project = "docstrfmt"
pygments_style = "sphinx"
release = __version__
source_suffix = {
    ".rst": None,
}
