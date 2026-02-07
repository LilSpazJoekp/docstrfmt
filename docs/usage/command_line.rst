######################
 Command Line Options
######################

This page documents all available command-line options for docstrfmt.

.. note::

    All options can also be set in ``pyproject.toml`` under the ``[tool.docstrfmt]``
    section. Command-line options take precedence over configuration file settings.

***************
 Basic Options
***************

.. option:: -h, --help

    Show the help message and exit.

.. option:: --version

    Show the version number and exit.

.. option:: -v, --verbose

    Increase verbosity level. Can be specified multiple times for different levels of
    verbosity.

    - ``-v``: Basic debugging information
    - ``-vv``: More detailed debugging information
    - ``-vvv``: Maximum verbosity

.. option:: -q, --quiet

    Don't emit non-error messages to stderr. Errors are still emitted; silence those
    with ``2>/dev/null``. Overrides ``--verbose``.

*************************
 File Processing Options
*************************

.. option:: -c, --check

    Check files and return a non-zero exit code if files are not formatted correctly.
    Useful for linting. Ignored if ``--raw-input``, ``--raw-output``, or stdin is used.

.. option:: -r, --raw-input TEXT

    Format the text passed in as a string. Formatted text will be output to stdout.

.. option:: -o, --raw-output

    Output the formatted text to stdout instead of modifying files in place.

.. option:: -t, --file-type {py,rst}

    Specify the raw input file type. Can only be used with ``--raw-input`` or stdin.

    Default: ``rst``

.. option:: -T, --include-txt

    Interpret ``*.txt`` files as reStructuredText and format them.

********************
 Formatting Options
********************

.. option:: -l, --line-length LENGTH

    Wrap lines to the given line length where possible. Takes precedence over
    ``line-length`` set in ``pyproject.toml`` if set. Defaults to the length provided to
    Black if not set.

    Minimum value: 4

    .. note::

        Line length is resolved in the following order:

        1. Command-line option
        2. ``tool.docstrfmt.line-length`` in specified pyproject.toml
        3. ``tool.black.line-length`` in specified pyproject.toml
        4. ``tool.docstrfmt.line-length`` in auto-detected pyproject.toml
        5. ``tool.black.line-length`` in auto-detected pyproject.toml
        6. Black's default line length

.. option:: --docstring-trailing-line / --no-docstring-trailing-line

    Whether to add a blank line at the end of docstrings.

    Default: ``--docstring-trailing-line``

.. option:: --format-python-code-blocks / --no-format-python-code-blocks

    Whether to format Python code blocks within reStructuredText.

    Default: ``--format-python-code-blocks``

.. option:: -s, --section-adornments CHARS

    Define adornments for part/chapter/section headers. It defines a sequence of
    adornments to use for each individual section depth. The list must be composed of at
    least N **distinct** characters for documents with N section depths. Provide more if
    unsure. If the special character ``|`` (pipe) is used, then it defines sections
    (left portion) that will have overlines besides underlines only (right portion).
    Overrides ``--preserve-adornments``.

    Default:

    .. literalinclude:: ../../docstrfmt/const.py
        :lines: 23

.. option:: -pA, --preserve-adornments

    Preserve existing section adornments instead of applying the default ones.

*******************
 Exclusion Options
*******************

.. option:: -e, --exclude PATH

    Path(s) to directories/files to exclude in formatting. Supports glob patterns. Can
    be specified multiple times.

    Default: ``["build/", "dist/", "*.egg-info/", ".git/", ".tox/", ".venv/", "venv/",
    ".mypy_cache/", ".pytest_cache/", ".ruff_cache/"]``

.. option:: -x, --extend-exclude PATH

    Path(s) to directories/files to exclude in addition to the default excludes in
    formatting. Supports glob patterns. Can be specified multiple times.

***********************
 Configuration Options
***********************

.. option:: -p, --pyproject-config PATH

    Path to ``pyproject.toml``. Used to load settings.

.. option:: -i, --ignore-cache

    Ignore the cache. Useful for testing.
