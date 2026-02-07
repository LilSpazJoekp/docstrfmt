###########################
 Contributing to docstrfmt
###########################

Thank you for your interest in contributing to docstrfmt! This document provides
guidelines and instructions for contributing to the project.

*****************
 Getting Started
*****************

Prerequisites
=============

- Python 3.10 or higher
- uv_ (recommended) or pip

Setting Up Your Development Environment
=======================================

1. Fork the repository on GitHub and clone your fork:

   .. code-block:: sh

       git clone https://github.com/YOUR-USERNAME/docstrfmt.git
       cd docstrfmt

2. Install uv (if not already installed):

   .. code-block:: sh

       # On macOS and Linux
       curl -LsSf https://astral.sh/uv/install.sh | sh

       # On Windows
       powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

3. Create a virtual environment and install dependencies:

   .. code-block:: sh

       uv sync --group dev

   .. note::

       The ``dev`` dependency group includes all the dependencies needed for
       development: linting tools, testing tools, and coverage reporting.

4. Install pre-commit hooks:

   .. code-block:: sh

       uv run pre-commit install

**********************
 Development Workflow
**********************

Running Tests
=============

`GitHub Actions`_ automatically runs all updates to known branches and pull requests.
However, it's useful to be able to run the tests locally. The simplest way is via
pytest:

.. code-block:: sh

    uv run pytest

To run tests with coverage:

.. code-block:: sh

    uv run coverage run --source docstrfmt --module pytest
    uv run coverage report -m

To run tests across all Python versions using tox:

.. code-block:: sh

    uv run tox

To run tests for a specific Python version:

.. code-block:: sh

    # For Python 3.10
    uv run tox -e py310

Running Linters
===============

docstrfmt follows :PEP:`8`. pre-commit_ is used to manage a suite of pre-commit hooks
that enforce conformance PEP8 along with several other checks.

To run all pre-commit checks on all files:

.. code-block:: sh

    uv run pre-commit run --all-files

You can also run pre-commit checks using tox:

.. code-block:: sh

    uv run tox -e pre-commit

To run style checks:

.. code-block:: sh

    uv run tox -e style

To run style checks and auto-fix issues:

.. code-block:: sh

    uv run tox -e style-fix

To self format with docstrfmt:

.. code-block:: sh

    uv run docstrfmt .

Running the Daemon
==================

To test the daemon functionality, first install with the daemon extras:

.. code-block:: sh

    uv sync --group dev --extra d

Then start the daemon:

.. code-block:: sh

    uv run docstrfmtd

***********************
 Code Style Guidelines
***********************

- Follow PEP 8 guidelines.
- Use type hints for function signatures.
- Write docstrings for all public modules, functions, classes, and methods.
- Keep line length to 88 characters (Black's default).
- Use meaningful variable and function names.

Type Hints
==========

Use type hints for all function parameters and return values:

.. code-block:: python

    def process_files(
        files: list[str],
        line_length: int | None = None,
        exclude: list[str] | None = None,
    ) -> str | list[str]:
        """Process files with the given options."""
        pass

****************
 Making Changes
****************

1. Create a new branch for your changes:

   .. code-block:: sh

       git checkout -b feature/your-feature-name

2. Make your changes and ensure tests pass:

   .. code-block:: sh

       uv run pytest
       uv run pre-commit run --all-files

3. Commit your changes with a descriptive commit message:

   .. code-block:: sh

       git add .
       git commit -m "Add feature: description of your changes"

4. Push to your fork:

   .. code-block:: sh

       git push origin feature/your-feature-name

5. Open a Pull Request on GitHub.

*********************
 Adding New Features
*********************

When adding new reStructuredText constructs or features:

1. Add test files in ``tests/test_files/``. These files should contain examples of
   properly formatted constructs.
2. Implement the feature in the appropriate module
3. Add tests in ``tests/test_main.py``

Files to Update
===============

AUTHORS.rst
-----------

For your first contribution, please add yourself to the end of the respective list in
the ``AUTHORS.rst`` file.

CHANGES.rst
-----------

For feature additions, bug fixes, or code removal please add an appropriate entry to
``CHANGES.rst``. If your change is not user-facing (e.g., refactoring, adding tests),
you do not need to add an entry. Each version is divided four sections: Added, Changed,
Fixed, and Removed. Please add your entry to the appropriate section under the
``Unreleased`` section (the topmost section).

********************
 Testing Guidelines
********************

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a PR
- Maintain 100% test coverage
- Use descriptive test names that explain what is being tested

Example Test
============

Tests typically are added to the ``tests/test_main.py`` file. Here's an example test for
line length parameterization:

.. code-block:: python

    @pytest.mark.parametrize("length", test_line_length)
    @pytest.mark.parametrize(
        "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
    )
    def test_line_length(runner, length, file):
        args = ["-l", length, file]
        result = runner.invoke(main, args=args, catch_exceptions=False)
        assert result.exit_code == 0
        assert result.output == (
            f"Reformatted '{os.path.abspath(file)}'.\n1 out of 1 file were"
            " reformatted.\nDone! 🎉\n"
        )
        result = runner.invoke(main, args=args)
        assert result.exit_code == 0
        assert result.output == "1 file was checked.\nDone! 🎉\n"

**************************
 Documentation Guidelines
**************************

Building Documentation
======================

Build documentation locally:

.. code-block:: bash

    sphinx-build -b html docs/ docs/_build/html

To automatically rebuild on changes:

.. code-block:: bash

    sphinx-autobuild docs/ docs/_build/html

Documentation Structure
=======================

- User Guide: :doc:`../usage/index`
- Examples: :doc:`../examples`
- Contributing: :doc:`contributing`

Writing Documentation
=====================

- Use clear, concise language.
- Provide examples for complex concepts.
- Include code samples.
- Cross-reference related topics.
- Keep documentation up-to-date.

*************************
 Pull Request Guidelines
*************************

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass and coverage remains at 100%

**********
 See Also
**********

Please also read the `Contributing Guidelines`_

.. _contributing guidelines: https://github.com/LilSpazJoekp/docstrfmt/blob/main/.github/CONTRIBUTING.rst

.. _github actions: https://github.com/LilSpazJoekp/docstrfmt/actions

.. _pre-commit: https://pre-commit.com

.. _uv: https://docs.astral.sh/uv/
