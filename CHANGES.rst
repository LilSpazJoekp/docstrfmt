Change Log
==========

1.9.0 (2024/08/26)
------------------

**Added**

- Added support to run using ``python -m``.

**Changed**

- Relaxed sphinx dependency.

**Fixed**

- Line length is now correctly resolved. Previously, it was always set to 88.
- Fix handling of ``.. code::`` blocks. They should now be correctly formatted to ``..
  code-block::``.

1.8.0 (2024/07/28)
------------------

**Added**

- Added support for nested tables.
- Added support for arbitrary directives.
- Added support for arbitrary roles.

**Fixed**

- Incorrect import of ``dataclass``.

1.7.0 (2024/07/25)
------------------

**Added**

- Added support for ``code-block`` directive.
- Added support for ``highlight`` directive.
- Added support for Sphinx metadata fields.
- Added support for Sphinx Python directives.

1.6.1 (2023/12/12)
------------------

**Fixed**

- Fix incorrect blank line padding around ``:returns:`` and ``:raises:`` fields.

1.6.0 (2023/12/10)
------------------

**Added**

- Added more missing roles.
- Added support for Python 3.11.
- Added support for Python 3.12.

**Changed**

- Improved field sorting and formatting.
- Improved handling of ``:param:`` and ``:type:`` fields.
- Bumped ``black``, ``docutils``, ``libcst``, ``platformdirs``, and ``sphinx`` to latest
  versions.

**Fixed**

- Fix ``:raises:`` field not supporting types.

**Removed**

- Removed support for Python 3.6.
- Removed support for Python 3.7.

1.5.1 (2022/09/01)
------------------

**Fixed**

- Fix ``ImportError`` when importing from black. Pinned black to 22.8.*.

1.5.0 (2022/07/19)
------------------

**Added**

- Added a flag to skip the cache.

**Fixed**

- Fix ``AttributeError`` when accessing ``rawsource`` during the handling ``Text``
  nodes.

1.4.4 (2022/02/06)
------------------

**Changed**

- Bump maximum version of ``click`` from ``8.0.0`` to ``9.0.0``.
- Bump minimum version of ``black`` to ``22``.

1.4.3 (2021/11/19)
------------------

**Fixed**

- An issue where docstrfmt would not properly find the ``pyproject.toml`` file.

1.4.2 (2021/11/16)
------------------

**Changed**

- Switch from unmaintained ``appdirs`` to the replacement ``platformdirs``.

**Fixed**

- An issue where the summary line of docstring was incorrectly wrapped.

1.4.1 (2021/09/10)
------------------

**Added**

- Add ``appdirs`` dependency.

1.4.0 (2021/07/30)
------------------

**Added**

- Add Pre-commit hooks.

1.3.0 (2021/07/16)
------------------

**Added**

- Add a check for blank fields and raise an error when found.
- Add ``toml`` dependency.

1.2.0 (2021/06/15)
------------------

**Added**

- Add ability to specify config setting from ``pyproject.toml``.

1.1.4 (2021/05/18)
------------------

**Changed**

- Use click<8.0.0 due to an issue with globbing on Windows.

**Fixed**

- Fix bug where exclude paths were not being excluded properly.

1.1.3 (2021/05/10)
------------------

**Changed**

- Paths are now casted to string when parsing rst with docutils.

**Fixed**

- Fixed import error with sphinx>=4.0.0.

1.1.2 (2021/05/04)
------------------

**Fixed**

- Fixed issue when `target_version` is not set in `pyproject.toml`.

1.1.1 (2021/05/04)
------------------

**Added**

- Added `currentmodule`, `function`, and `py:function` directives.

**Changed**

- Updated black config parsing.

**Fixed**

- Fixed import error when parsing black config.

1.1.0 (2021/02/18)
------------------

- Make docstrfmt operate in parallel when processing more than 2 files similar to
  psf/black.
- Added a caching mechanism similar to psf/black has so files that haven't changed from
  the last run won't be checked again.

1.0.3 (2021/01/23)
------------------

**Added**

- Support for asynchronous functions.
- Ability to remove the blank line at the end of docstrings.

**Changed**

- Python file parsing now uses `libcst <https://libcst.readthedocs.io/en/latest>`_.
- When misformatted files are found, location info is printed with the line where the
  error is found if possible.

**Fixed**

- Bug where some raw docstrings were not being formatted.
- Bug where some syntax errors in python blocks were not caught or raised correctly.

1.0.2 (2020/12/27)
------------------

**Fixed**

- Fix UnicodeEncodeError in Windows Github Actions jobs.

1.0.1 (2020/12/27)
------------------

**Changed**

- Open files with ``UTF-8`` encoding.

**Fixed**

- Fix encoding/decoding errors when opening files on Windows.

1.0.0 (2020/12/26)
------------------

- First official docstrfmt release!

1.0.0.pre0 (2020/12/26)
-----------------------

- Forked from `dzhu/rstfmt <https://github.com/dzhu/rstfmt>`_
- Renamed to docstrfmt
- Added ability to format Python docstrings
- Switched to click for argument parsing
- Formatted code with black
- Made code easier to read
- Added more rst constructs
- Added more tests
