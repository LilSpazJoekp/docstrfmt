"""Configuration file for the Sphinx documentation builder."""

import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docstrfmt import __version__

author = "Joel Payne"
copyright = f"{datetime.today():%Y}, {author}"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "examples/**.rst"]
html_static_path = ["_static"]
html_theme = "furo"
language = "en"
master_doc = "index"
project = "docstrfmt"
pygments_style = "sphinx"
release = __version__
source_suffix = {
    ".rst": None,
}

