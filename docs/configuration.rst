###############
 Configuration
###############

docstrfmt can be configured through various methods, with a clear precedence order for
resolving settings.

***********************
 Configuration Methods
***********************

1. Command-line options (highest precedence)
2. pyproject.toml files specified with ``--pyproject-config``
3. pyproject.toml file auto-detected in the project root
4. Default values (lowest precedence)

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
Black's line length setting

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
    :lines: 4-17

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

***************************
 Line Length Configuration
***************************

docstrfmt shares line length configuration with Black, allowing for consistent
formatting across code and docstrings.

Shared Configuration
====================

Both tools can share the same ``pyproject.toml``:

.. code-block:: toml

    [tool.black]
    line-length = 88
    target-version = ['py310']

    [tool.docstrfmt]
    line-length = 88  # Inherits from Black if not specified

Configuration Resolution
========================

docstrfmt resolves configuration in this order:

1. Command-line ``--line-length`` option
2. ``tool.docstrfmt.line-length`` in specified pyproject.toml
3. ``tool.black.line-length`` in specified pyproject.toml
4. ``tool.docstrfmt.line-length`` in auto-detected pyproject.toml
5. ``tool.black.line-length`` in auto-detected pyproject.toml
6. Black's default line length

***********************
 Command Line Override
***********************

You can override any configuration option from the command line:

.. code-block:: bash

    # Override line length
    docstrfmt --line-length 72 myfile.rst

    # Override exclusions
    docstrfmt --exclude "custom_dir/" myfile.rst

    # Override section adornments
    docstrfmt --section-adornments "#*=-^~" myfile.rst

*************************
 Debugging Configuration
*************************

Use the ``--verbose`` option to see how configuration is resolved:

.. code-block:: bash

    docstrfmt --verbose --verbose myfile.rst

This will show:

- Which configuration file is being used
- How each setting is resolved
- Any fallbacks being applied
