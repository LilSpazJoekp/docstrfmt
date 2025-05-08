"""Constants for docstrfmt."""

# pragma: no cover

DEFAULT_EXCLUDE = [
    "**/.direnv/",
    "**/.direnv/",
    "**/.eggs/",
    "**/.git/",
    "**/.hg/",
    "**/.mypy_cache/",
    "**/.nox/",
    "**/.tox/",
    "**/.venv/",
    "**/.svn/",
    "**/_build",
    "**/buck-out",
    "**/build",
    "**/dist",
]
# Part/Chapter/Section adornment characters. The special `|` character separated
# sections without overlines. If that is not present, then we consider all sections to
# only contain underlines. From:
# https://devguide.python.org/documentation/markup/#sections
SECTION_CHARS = "#*|=-^\"'~+.`_:"
ROLE_ALIASES = {
    "pep": "PEP",
    "pep-reference": "PEP",
    "rfc": "RFC",
    "rfc-reference": "RFC",
    "subscript": "sub",
    "superscript": "sup",
}
DEFAULT_LINE_LENGTH = 88
