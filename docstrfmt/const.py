"""Constants for docstrfmt."""

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
NODE_MAPPING = {
    "attention": "_sub_admonition",
    "caution": "_sub_admonition",
    "danger": "_sub_admonition",
    "error": "_sub_admonition",
    "hint": "_sub_admonition",
    "important": "_sub_admonition",
    "meta": "_sub_admonition",
    "note": "_sub_admonition",
    "seealso": "_sub_admonition",
    "tip": "_sub_admonition",
    "warning": "_sub_admonition",
    "Text": "text",
}
