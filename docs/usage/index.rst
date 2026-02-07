#############
 Usage Guide
#############

This section covers all the ways to use docstrfmt, from basic command-line usage to
advanced features.

.. toctree::
    :maxdepth: 2

    command_line
    file_processing
    python_integration
    daemon_mode
    editor_integration

************************
 Command Line Interface
************************

The main entry point for docstrfmt is the ``docstrfmt`` command. It provides a
comprehensive set of options for formatting reStructuredText files and Python
docstrings.

Basic Syntax
============

.. code-block:: bash

    docstrfmt [OPTIONS] [FILES...]

If no files are specified, docstrfmt reads from stdin and writes to stdout.

Common Options
==============

Here are the most commonly used options:

- ``-c, --check``: Check files without modifying them
- ``-l, --line-length LENGTH``: Set the maximum line length
- ``-v, --verbose``: Increase verbosity (can be used multiple times)
- ``-q, --quiet``: Suppress non-error output
- ``-h, --help``: Show help message

For a complete list of all available options, see :doc:`command_line`.

*****************
 File Processing
*****************

docstrfmt can process various types of files:

- Standalone reStructuredText files (``.rst``)
- Python files with docstrings (``.py``)
- Text files (``.txt``) when using the ``--include-txt`` option

For detailed information about file processing, see :doc:`file_processing`.

********************
 Python Integration
********************

docstrfmt integrates seamlessly with Python projects, automatically detecting and
formatting docstrings while preserving the rest of your code.

Key features: * Preserves Python code structure * Formats only docstrings * Integrates
with Black for code formatting * Supports all Python docstring formats

For more details, see :doc:`python_integration`.

*************
 Daemon Mode
*************

For high-performance scenarios or editor integration, docstrfmt provides a daemon mode
that runs as an HTTP server.

Features: * Fast formatting via HTTP requests * Avoids startup overhead * Configurable
host and port * Compatible with editor plugins

For setup and usage, see :doc:`daemon_mode`.

********************
 Editor Integration
********************

docstrfmt can be integrated with various editors and IDEs to provide real-time
formatting.

Supported editors: * PyCharm/IntelliJ IDEA * VS Code (via extensions) * Vim/Neovim *
Emacs

For detailed setup instructions, see :doc:`editor_integration`.
