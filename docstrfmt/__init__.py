"""docstrfmt: A formatter for Sphinx flavored reStructuredText."""

from .const import (
    DEFAULT_EXCLUDE,
    DEFAULT_LINE_LENGTH,
    NODE_MAPPING,
    ROLE_ALIASES,
    SECTION_CHARS,
)
from .docstrfmt import Manager
from .options import FormatOptions, RunOptions

__version__ = "2.2.2.dev0"
