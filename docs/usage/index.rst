#############
 Usage Guide
#############

This section covers all the ways to use docstrfmt, from basic command-line usage to
advanced features.

.. toctree::
    :hidden:
    :maxdepth: 2

    command_line
    file_processing
    python_files
    daemon_mode
    editor_integration

:doc:`command_line`
    Every option of ``docstrfmt [OPTIONS] [FILES...]``, generated from the click
    definitions. Pass ``-`` as a file to read from stdin.

:doc:`file_processing`
    docstrfmt handles ``.rst``, ``.py`` (docstrings only), and ``.txt`` (when
    :option:`--include-txt <docstrfmt --include-txt>` is set). Directories are walked
    recursively and results are cached between runs.

:doc:`python_files`
    docstrfmt detects and formats the docstrings in Python files and leaves the rest of
    your code alone. Docstrings are expected to be reStructuredText, and Python code
    blocks inside them are formatted with Black.

:doc:`daemon_mode`
    A daemon that formats over HTTP on a configurable host and port. It avoids
    docstrfmt's startup overhead, which suits editor plugins and other repeated
    requests. It needs the optional daemon dependencies; see
    :ref:`installing-with-daemon-support`.

:doc:`editor_integration`
    Setups for PyCharm / IntelliJ IDEA (External Tools or File Watchers), pre-commit,
    GitHub Actions, and GitLab CI. Other editors can call the command line or the
    daemon.
