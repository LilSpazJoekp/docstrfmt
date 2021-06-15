Change Log
==========

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
