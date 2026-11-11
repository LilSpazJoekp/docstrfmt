"""Configuration file for the Sphinx documentation builder."""

from datetime import UTC, datetime
from importlib.metadata import version as _pkg_version

__version__ = _pkg_version("docstrfmt")

author = "Joel Payne"
copyright = f"{datetime.now(UTC):%Y}, {author}"  # noqa: A001
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "examples/**.rst"]
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_click",
]
html_theme = "furo"
intersphinx_mapping = {
    "click": ("https://click.palletsprojects.com/en/stable", None),
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}
language = "en"
master_doc = "index"
project = "docstrfmt"
pygments_style = "sphinx"
release = __version__
smartquotes_action = "qe"
source_suffix = {
    ".rst": None,
}
