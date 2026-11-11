#################
 File Processing
#################

docstrfmt discovers files, decides what to format, and caches results between runs. This
page covers the *behavior* of that pipeline; every flag mentioned is documented in full
on :doc:`command_line`.

**********************
 Supported File Types
**********************

- ``.rst`` — reStructuredText, docstrfmt's primary target.
- ``.py`` — Python files; only docstrings are formatted (see :doc:`python_files`).
- ``.txt`` — treated as reStructuredText when :option:`--include-txt <docstrfmt
  --include-txt>` is set.

Extensions are inferred from the filename. When reading from stdin or via
:option:`--raw-input <docstrfmt --raw-input>`, set :option:`--file-type <docstrfmt
--file-type>` explicitly.

******************
 Processing Modes
******************

In-place (default)
    Files are rewritten in place with the formatted output.

Check mode (:option:`-c/--check <docstrfmt --check>`)
    Files are not modified; exit code is non-zero if any file would change. Intended for
    CI and pre-commit.

Raw output (:option:`-o/--raw-output <docstrfmt --raw-output>`)
    Formatted content is written to stdout; source files are left alone.

Stdin
    Pass ``-`` as the file argument. Content is read from stdin and formatted output is
    written to stdout.

Raw input (:option:`-r/--raw-input <docstrfmt --raw-input>`)
    Format a string given directly on the command line and print the result.

****************
 File Discovery
****************

Any argument that resolves to a directory is walked recursively; extensions are filtered
as described above. docstrfmt also expands glob patterns itself, including ``**`` for
recursive matches:

.. code-block:: bash

    docstrfmt "docs/**/*.rst"
    docstrfmt "src/**/*.py" "*.rst"

Quote patterns that contain ``**``. Most shells (including Bash without ``globstar``)
treat an unquoted ``**`` like ``*`` and only match one directory level before docstrfmt
sees the pattern. Passing a directory, such as ``docstrfmt src docs``, is the simplest
way to format a whole tree.

*******************
 Caching Mechanism
*******************

docstrfmt keeps a cache so unchanged files are skipped between runs. It applies whether
you pass one file or many; only stdin and :option:`-r/--raw-input <docstrfmt
--raw-input>` are never cached. The cache lives in the user's platform cache directory,
in a subdirectory per docstrfmt version:

- **macOS**: ``~/Library/Caches/docstrfmt/<version>/``
- **Linux**: ``~/.cache/docstrfmt/<version>/``
- **Windows**: ``%LOCALAPPDATA%\docstrfmt\docstrfmt\Cache\<version>\``

Each combination of formatting options gets its own cache file. The key covers every
option that can change the output (line length, section adornments, list markers,
Black's mode, and so on), so changing any of them reformats files instead of skipping
them. Options that don't affect output, such as ``--check``, ``--quiet`` and the
exclusion lists, are left out of the key.

Each entry records the file's modification time and size; if either changes, the file is
reprocessed. A file is only cached after it formats without errors. In check mode, a
file that still needs formatting is not cached, so it is reported again on the next run.
With :option:`-o/--raw-output <docstrfmt --raw-output>`, a single file is always printed
even if it is cached.

Use :option:`-i/--ignore-cache <docstrfmt --ignore-cache>` to force a full re-scan;
delete the cache directory to clear it entirely.

********************
 Exclusion Patterns
********************

docstrfmt ships with a default exclusion list covering common build and VCS directories
(see :doc:`/configuration`). :option:`-e/--exclude <docstrfmt --exclude>` *replaces*
that list; :option:`-x/--extend-exclude <docstrfmt --extend-exclude>` *adds* to it. Both
can be repeated and both accept glob patterns.

****************
 Error Handling
****************

- **Parse errors** are reported with file and line, docstrfmt continues with the
  remaining files, and the process exits non-zero if any file failed.
- **Missing files** are not reported. A path that doesn't exist matches nothing, so it
  is silently skipped; check the "N files checked" summary if you suspect a typo.
- **Permission errors** are reported, the file is skipped, and the process exits
  non-zero.

When formatting Python files, docstring parse errors leave the docstring unchanged and
the rest of the file is still processed (see :doc:`python_files`).
