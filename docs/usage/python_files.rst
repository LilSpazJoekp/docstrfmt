#########################
 Formatting Python Files
#########################

docstrfmt formats docstrings in Python files, leaving the surrounding code untouched.
This page covers how it detects docstrings, the formatting options that apply, and how
to hook it into your dev tools.

******************************
 Basic Python File Formatting
******************************

To format Python files, simply pass them to docstrfmt:

.. code-block:: bash

    docstrfmt mymodule.py
    docstrfmt "src/**/*.py"

docstrfmt will:

- Parse the Python file using LibCST
- Extract all docstrings
- Format the docstrings as reStructuredText
- Preserve all other code unchanged
- Write the formatted file back

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

Python code blocks *inside* reStructuredText docstrings are handed to Black by default.
Toggle with :option:`--format-python-code-blocks / --no-format-python-code-blocks
<docstrfmt --format-python-code-blocks>`.

.. code-block::

    Here's an example function:

    .. code-block:: python

        def hello_world():
            print("Hello, World!")

******************************
 Docstring Formatting Options
******************************

All docstring formatting options live on the CLI and in ``[tool.docstrfmt]``. See
:doc:`command_line` for the full reference and :doc:`/configuration` for the pyproject
keys. The two most commonly-tuned ones:

- :option:`--docstring-trailing-line / --no-docstring-trailing-line <docstrfmt
  --docstring-trailing-line>` — controls the blank line at the end of a docstring.
- :option:`--line-length <docstrfmt --line-length>` — resolved from CLI, then
  ``[tool.docstrfmt]``, then ``[tool.black]``, then Black's default. Full order in
  :ref:`line-length-resolution`.

****************
 Error Handling
****************

Syntax Errors
=============

If docstrfmt encounters a Python syntax error, it will:

1. Report LibCST's parser error and the file's path
2. Skip the problematic file
3. Continue with other files
4. Return a non-zero exit code

For a tokenizer error such as an unclosed string, LibCST reports the position as line 1:

.. code-block:: text

    ParserSyntaxError: Syntax Error @ 1:1.
    tokenizer error: unterminated triple-quoted string literal

    """My package."""
    ^
    Failed to format '/home/me/project/src/mypackage/broken.py'
    1 file was checked.
    Done, but 1 error occurred ❌💥❌

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
        rev: v2.2.1
        hooks:
          - id: docstrfmt

CI/CD Pipelines
===============

Use docstrfmt in your CI/CD pipeline to ensure consistent formatting:

.. code-block:: yaml

    - name: Check docstring formatting
      run: docstrfmt --check src

    - name: Format docstrings
      run: docstrfmt src

IDE Integration
===============

docstrfmt can be integrated with various IDEs (currently only PyCharm is supported, PRs
for other IDEs are welcome):

- PyCharm: Use :ref:`External Tools or File Watchers <pycharm-integration>`

**********
 Examples
**********

.. code-block:: bash

    # Format an entire package
    docstrfmt src/mypackage

    # Custom line length
    docstrfmt --line-length 72 "src/**/*.py"

    # Skip Python code-block reformatting
    docstrfmt --no-format-python-code-blocks "src/**/*.py"

    # Check in CI (non-zero exit if anything needs formatting)
    docstrfmt --check "src/**/*.py"

    # Specific files
    docstrfmt src/mypackage/__init__.py src/mypackage/core.py

    # Verbose output
    docstrfmt --verbose "src/**/*.py"

See :doc:`command_line` for every option.
