###############
 Configuration
###############

docstrfmt can be configured through various methods, with a clear precedence order for
resolving settings.

***********************
 Configuration Methods
***********************

1. Command-line options (highest precedence)
2. The ``[tool.docstrfmt]`` section of ``pyproject.toml``
3. For line length only, the ``[tool.black]`` section of the same ``pyproject.toml``
4. Default values (lowest precedence)

docstrfmt reads exactly one ``pyproject.toml``: the file given with
:option:`-p/--pyproject-config <docstrfmt --pyproject-config>` or, when that option is
not passed, the one auto-detected in the project root the way Black finds it. Keys may
be written with hyphens or underscores (``line-length`` and ``line_length`` are the same
key).

******************************
 pyproject.toml Configuration
******************************

The primary configuration method is through a ``pyproject.toml`` file in your project
root. docstrfmt looks for configuration in the ``[tool.docstrfmt]`` section.

Basic Configuration
===================

Create a ``pyproject.toml`` file in your project root:

.. code-block:: toml

    [tool.docstrfmt]
    line-length = 88
    exclude = ["build/", "dist/"]
    extend-exclude = ["tests/error_files/*"]

***********************
 Configuration Options
***********************

Line Length
===========

.. code-block:: toml

    [tool.docstrfmt]
    line-length = 88

Controls the maximum line length for wrapping text. If not specified, docstrfmt will use
Black's line length setting.

File Exclusions
===============

.. code-block:: toml

    [tool.docstrfmt]
    exclude = ["build/", "dist/", "*.egg-info/"]
    extend-exclude = ["tests/error_files/*", "custom_dir/"]

- ``exclude``: Completely replaces the default exclusion list
- ``extend-exclude``: Adds to the default exclusion list

Default exclusions:

.. literalinclude:: ../docstrfmt/const.py
    :language: python
    :start-at: DEFAULT_EXCLUDE = [
    :end-at: ]

Docstring Formatting
====================

.. code-block:: toml

    [tool.docstrfmt]
    docstring-trailing-line = true
    format-python-code-blocks = true

- ``docstring-trailing-line``: Whether to add a blank line at the end of docstrings
- ``format-python-code-blocks``: Whether to format Python code blocks within
  reStructuredText

Section Adornments
==================

.. code-block:: toml

    [tool.docstrfmt]
    section-adornments = "#*=-^"

Defines the sequence of characters to use for section headers. Each character represents
a different section depth.

The pipe character (``|``) can be used to define sections that have both overlines and
underlines. The characters to the left of the pipe will have overlines, while those to
the right will have only underlines. The following example would make all section levels
have no overlines:

.. code-block:: toml

    [tool.docstrfmt]
    section-adornments = "|#*=-^"

Files to Process
================

.. code-block:: toml

    [tool.docstrfmt]
    files = ["src", "tests"]

Specifies which files or directories to process. Supports glob patterns.

********************************
 Sharing line length with Black
********************************

docstrfmt reuses Black's ``line-length`` when its own is unset, so a single
``pyproject.toml`` can drive both:

.. code-block:: toml

    [tool.black]
    line-length = 88
    target-version = ['py310']

    [tool.docstrfmt]
    # inherits line-length from [tool.black]

The full resolution order (CLI → ``[tool.docstrfmt]`` → ``[tool.black]`` → default) is
documented under :ref:`line-length-resolution`.

*****************************
 Custom Directives and Roles
*****************************

Unknown directives and roles are registered automatically the first time they are seen,
with their body preserved verbatim. To register them explicitly, list them under
``custom_directives`` and ``custom_roles``:

.. code-block:: toml

    [tool.docstrfmt]
    custom_directives = [
        "mydirective",
        { name = "callout", raw = false, has_content = true },
    ]
    custom_roles = ["mycolor", "mystyle"]

A plain name behaves like the automatic fallback. A table accepts ``raw``,
``has_content``, ``required_arguments``, ``optional_arguments`` and
``final_argument_whitespace``; ``raw = false`` makes docstrfmt reformat the directive's
body as reStructuredText. The command-line equivalents are :option:`--custom-directive
<docstrfmt --custom-directive>` and :option:`--custom-role <docstrfmt --custom-role>`.
When a name appears in both places, the ``pyproject.toml`` entry wins.

***********************
 Command Line Override
***********************

Every ``[tool.docstrfmt]`` key has a matching CLI flag with higher precedence. The
complete list is in :doc:`usage/command_line`.

*************************
 Debugging Configuration
*************************

:option:`-v/--verbose <docstrfmt --verbose>` does not print configuration; it logs the
files being processed. ``-v`` reports each correctly formatted file, ``-vv`` adds a line
as each file is checked, and ``-vvv`` also dumps the parsed document tree of every file.
