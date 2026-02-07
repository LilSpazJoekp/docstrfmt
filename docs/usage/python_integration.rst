####################
 Python Integration
####################

docstrfmt provides seamless integration with Python projects, allowing you to format
docstrings while preserving your code structure and integrating with other Python tools.

******************************
 Basic Python File Formatting
******************************

To format Python files, simply pass them to docstrfmt:

.. code-block:: bash

    docstrfmt mymodule.py
    docstrfmt src/**/*.py

docstrfmt will: * Parse the Python file using LibCST * Extract all docstrings * Format
the docstrings as reStructuredText * Preserve all other code unchanged * Write the
formatted file back

*********************
 Docstring Detection
*********************

docstrfmt automatically detects and formats various types of docstrings:

Module-level docstrings
=======================

.. code-block:: python

    """This is a module docstring that will be formatted."""


    def function():
        pass

Class docstrings
================

.. code-block:: python

    class MyClass:
        """This is a class docstring that will be formatted."""

        def method(self):
            pass

Function and method docstrings
==============================

.. code-block:: python

    def my_function(param1, param2):
        """This is a function docstring that will be formatted.

        :param param1: Description of param1
        :param param2: Description of param2

        :returns: Description of return value
        """
        return param1 + param2

************************
 Integration with Black
************************

docstrfmt integrates with Black for consistent code formatting:

Automatic Black Integration
===========================

When formatting Python code blocks within reStructuredText, docstrfmt uses Black to
format the Python code:

.. code-block:: python

    def example_function():
        # This Python code will be formatted by Black
        return {"key": "value", "nested": {"data": [1, 2, 3]}}

Configuration Inheritance
=========================

docstrfmt inherits Black's configuration from your ``pyproject.toml``:

.. code-block:: toml

    [tool.black]
    line-length = 88
    target-version = ['py310']

    [tool.docstrfmt]
    line-length = 88  # Inherits from Black if not specified

***********************
 Code Block Formatting
***********************

Python Code Blocks
==================

docstrfmt can format Python code blocks within reStructuredText documents:

.. code-block::

    Here's an example function:

    .. code-block:: python

        def hello_world():
            print("Hello, World!")

Use the ``--format-python-code-blocks`` option to enable this (default) or
``--no-format-python-code-blocks`` to disable it.

******************************
 Docstring Formatting Options
******************************

Trailing Line
=============

By default, docstrfmt adds a blank line at the end of docstrings. You can control this
with the ``--docstring-trailing-line`` and ``--no-docstring-trailing-line`` options:

.. code-block:: python

    def example():
        """This docstring will have a trailing blank line by default."""
        pass


    def example_no_trailing():
        """This docstring won't have a trailing blank line."""
        pass

Line Length
===========

The line length for docstring formatting follows the same resolution order as other
formatting:

1. Command-line ``--line-length`` option
2. ``tool.docstrfmt.line-length`` in pyproject.toml
3. ``tool.black.line-length`` in pyproject.toml
4. Black's default (88)

****************
 Error Handling
****************

Syntax Errors
=============

If docstrfmt encounters a Python syntax error, it will:

1. Report the error with file and line information
2. Skip the problematic file
3. Continue with other files
4. Return a non-zero exit code

.. code-block:: bash

    Failed to format '/Users/jkpayne/Desktop/PythonProjects/docstrfmt/test.rst'
    SyntaxError: unterminated string literal (detected at line 6):

    File "/Users/jkpayne/Desktop/PythonProjects/docstrfmt/docs/usage/python_integration.rst", line 122:
        """This docstring won't have a trailing blank line."""

Parse Errors
============

If docstrfmt cannot parse a docstring as reStructuredText, it will:

1. Report the error with file and line information
2. Leave the docstring unchanged
3. Continue processing other docstrings
4. Return a non-zero exit code

************************************
 Integration with Development Tools
************************************

pre-commit Hooks
================

Add docstrfmt to your pre-commit configuration:

.. code-block:: yaml

    repos:
      - repo: https://github.com/LilSpazJoekp/docstrfmt
        rev: stable
        hooks:
          - id: docstrfmt
            language_version: python3
            types_or: [python, rst, txt]

CI/CD Pipelines
===============

Use docstrfmt in your CI/CD pipeline to ensure consistent formatting:

.. code-block:: yaml

    - name: Check docstring formatting
      run: docstrfmt --check src/**/*.py

    - name: Format docstrings
      run: docstrfmt src/**/*.py

IDE Integration
===============

docstrfmt can be integrated with various IDEs (currently only PyCharm is supported, PRs
for other IDEs are welcome):

- PyCharm: Use External Tools or File Watchers

**********
 Examples
**********

Format a Python package:

.. code-block:: bash

    docstrfmt src/mypackage/**/*.py

Format with custom line length:

.. code-block:: bash

    docstrfmt --line-length 72 src/**/*.py

Format without Python code block formatting:

.. code-block:: bash

    docstrfmt --no-format-python-code-blocks src/**/*.py

Format with verbose output:

.. code-block:: bash

    docstrfmt --verbose src/**/*.py

Check formatting in CI:

.. code-block:: bash

    docstrfmt --check src/**/*.py

Format specific files:

.. code-block:: bash

    docstrfmt src/mypackage/__init__.py src/mypackage/core.py
