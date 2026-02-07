#################
 File Processing
#################

docstrfmt can process various types of files and provides flexible options for handling
different file formats and processing modes.

**********************
 Supported File Types
**********************

reStructuredText Files (``.rst``)
=================================

The primary file type that docstrfmt is designed to format. These files contain
reStructuredText markup and are commonly used for documentation.

.. code-block:: bash

    docstrfmt documentation.rst
    docstrfmt *.rst

Python Files (``.py``)
======================

docstrfmt can format Python files by extracting and formatting docstrings while
preserving the rest of the code structure.

.. code-block:: bash

    docstrfmt mymodule.py
    docstrfmt src/**/*.py

Text Files (``.txt``)
=====================

When using the ``--include-txt`` option, docstrfmt will treat ``.txt`` files as
reStructuredText and format them.

.. code-block:: bash

    docstrfmt --include-txt *.txt

******************
 Processing Modes
******************

In-Place Formatting
===================

By default, docstrfmt modifies files in place, overwriting the original content with the
formatted version.

.. code-block:: bash

    docstrfmt myfile.rst  # Modifies myfile.rst directly

Check Mode
==========

Use the ``--check`` option to verify formatting without modifying files. This is useful
for CI/CD pipelines and pre-commit hooks.

.. code-block:: bash

    docstrfmt --check myfile.rst  # Returns non-zero exit code if misformatted

Output to stdout
================

Use the ``--raw-output`` option to output formatted content to stdout instead of
modifying files.

.. code-block:: bash

    docstrfmt --raw-output myfile.rst  # Prints formatted content to stdout

Input from stdin
================

When ``-`` is specified for files, docstrfmt reads from stdin and writes to stdout.

.. code-block:: bash

    echo "Some reStructuredText content" | docstrfmt -

Raw Input
=========

Use the ``--raw-input`` option to format text passed directly as a string.

.. code-block:: bash

    docstrfmt --raw-input "Some reStructuredText content"

****************
 File Discovery
****************

Glob Patterns
=============

docstrfmt supports glob patterns for file discovery:

.. code-block:: bash

    docstrfmt *.rst          # All .rst files in current directory
    docstrfmt docs/**/*.rst  # All .rst files in docs subdirectories
    docstrfmt src/**/*.py    # All .py files in src subdirectories

Multiple Files
==============

You can specify multiple files or patterns:

.. code-block:: bash

    docstrfmt file1.rst file2.rst file3.py
    docstrfmt *.rst *.py

*******************
 Caching Mechanism
*******************

Disabling Cache
===============

Use the ``--ignore-cache`` option to bypass the cache entirely:

.. code-block:: bash

    docstrfmt --ignore-cache *.rst

This is useful for:

- Testing: Ensuring all files are processed
- Debugging: Troubleshooting cache-related issues
- CI/CD: Ensuring consistent behavior in automated environments

How Caching Works
=================

docstrfmt uses a file-based caching system to avoid re-processing files that haven't
changed since the last formatting run. This significantly improves performance when
running docstrfmt on large codebases or when running it frequently.

Cache Location
==============

The cache is stored in the user's cache directory, which varies by platform:

- **macOS**: ``~/Library/Caches/docstrfmt/``
- **Linux**: ``~/.cache/docstrfmt/``
- **Windows**: ``%LOCALAPPDATA%/docstrfmt/cache/``

Each version of docstrfmt uses a separate cache directory to avoid conflicts between
versions.

Cache Structure
===============

The cache uses pickle files with names based on the formatting configuration:

.. code-block:: text

    cache.{docstring_trailing_line}_{format_python_code_blocks}_{include_txt}_{line_length}_{mode}.pickle

For example: ``cache.True_True_False_88_black.pickle``

Cache Contents
==============

Each cache file contains a dictionary mapping file paths to tuples of:

- **Modification time** (``mtime``): When the file was last modified
- **File size**: The size of the file in bytes

Cache Key Generation
====================

The cache key is generated from the following parameters:

- ``docstring_trailing_line``: Whether to add trailing lines to docstrings
- ``format_python_code_blocks``: Whether to format Python code blocks
- ``include_txt``: Whether to include .txt files
- ``line_length``: The maximum line length
- ``mode``: The Black formatting mode (e.g., "black", "pyproject")

This ensures that different configurations use separate cache files.

Cache Behavior
==============

File Processing
---------------

When docstrfmt processes two or more files, it:

1. Checks the cache for each file's current modification time and size
2. Compares with the cached values
3. Skips processing if the file hasn't changed and is in the cache
4. Processes files that have changed or aren't in the cache
5. Updates the cache with successfully processed files

Cache Updates
-------------

The cache is updated after successful file processing:

- Only files that were successfully processed are added to the cache
- Files with errors are not cached
- The cache is written atomically using temporary files

Cache Invalidation
------------------

The cache is automatically invalidated when:

- File modification time changes: The file has been edited
- File size changes: The file content has changed
- Configuration changes* Different formatting options are used
- Version changes: docstrfmt is updated to a new version

Clearing the Cache
==================

To clear the cache manually, delete the cache directory:

.. code-block:: bash

    # macOS/Linux
    rm -rf ~/.cache/docstrfmt/
    # or
    rm -rf ~/Library/Caches/docstrfmt/

    # Windows
    rmdir /s "%LOCALAPPDATA%\docstrfmt\cache"

********************
 Exclusion Patterns
********************

Default Exclusions
==================

By default, docstrfmt excludes certain directories and files:

- ``build/``
- ``dist/``
- ``*.egg-info/``
- ``.git/``
- ``.tox/``
- ``.venv/``
- ``venv/``
- ``.mypy_cache/``
- ``.pytest_cache/``
- ``.ruff_cache/``

Custom Exclusions
=================

Use the ``--exclude`` option to specify custom exclusion patterns:

.. code-block:: bash

    docstrfmt --exclude "build/" --exclude "*.egg-info/" *.rst

Use the ``--extend-exclude`` option to add exclusions to the default list:

.. code-block:: bash

    docstrfmt --extend-exclude "custom_dir/" --extend-exclude "*.tmp" *.rst

*********************
 File Type Detection
*********************

Automatic Detection
===================

docstrfmt automatically detects file types based on extensions:

- ``.rst`` files are treated as reStructuredText
- ``.py`` files are treated as Python files
- ``.txt`` files are treated as text (requires ``--include-txt``)

Manual Override
===============

Use the ``--file-type`` option to manually specify the file type when using
``--raw-input`` or stdin:

.. code-block:: bash

    echo "Some content" | docstrfmt --file-type py

****************
 Error Handling
****************

Parse Errors
============

When docstrfmt encounters parsing errors, it will:

1. Report the error with file and line information
2. Continue processing other files
3. Return a non-zero exit code if any errors occurred

.. code-block:: bash

    docstrfmt invalid.rst
    # Output: Error: Invalid reStructuredText syntax in invalid.rst:5:10

File Not Found
==============

If a specified file doesn't exist, docstrfmt will report an error and continue with
other files:

.. code-block:: bash

    docstrfmt nonexistent.rst existing.rst
    # Output: Error: File 'nonexistent.rst' not found
    # Continues with existing.rst

Permission Errors
=================

If docstrfmt cannot read or write a file due to permission issues, it will report an
error and continue with other files.

**********
 Examples
**********

Format all reStructuredText files in a project:

.. code-block:: bash

    docstrfmt docs/**/*.rst

Format Python files with custom exclusions:

.. code-block:: bash

    docstrfmt --exclude "tests/" --exclude "build/" *.py

Check formatting in a CI pipeline:

.. code-block:: bash

    docstrfmt --check docs/**/*.rst

Format files with different line lengths:

.. code-block:: bash

    docstrfmt --line-length 72 docs/**/*.rst
    docstrfmt --line-length 88 src/**/*.py

Format with verbose output:

.. code-block:: bash

    docstrfmt --verbose --verbose docs/**/*.rst
