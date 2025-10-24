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
- `uv <https://docs.astral.sh/uv/>`_ (recommended) or pip

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

Run the test suite using pytest:

.. code-block:: sh

    uv run pytest

Run tests with coverage:

.. code-block:: sh

    uv run coverage run --source docstrfmt --module pytest
    uv run coverage report -m

Run tests across all Python versions using tox:

.. code-block:: sh

    uv run tox

Run tests for a specific Python version:

.. code-block:: sh

    # For Python 3.10
    uv run tox -e py310

Running Linters
===============

The project uses pre-commit hooks to ensure code quality. Run all checks:

.. code-block:: sh

    uv run pre-commit run --all-files

You can also run pre-commit checks using tox:

.. code-block:: sh

    uv run tox -e pre-commit

Run style checks:

.. code-block:: sh

    uv run tox -e style

Run style checks and auto-fix issues:

.. code-block:: sh

    uv run tox -e style-fix

Format the docs with docstrfmt:

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

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for all public modules, functions, classes, and methods
- Keep line length to 88 characters (Black's default)
- Use meaningful variable and function names

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

5. Open a Pull Request on GitHub

*************************
 Pull Request Guidelines
*************************

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass and coverage remains at 100%

********************
 Testing Guidelines
********************

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a PR
- Maintain 100% test coverage
- Use descriptive test names that explain what is being tested

*********************
 Adding New Features
*********************

When adding new reStructuredText constructs or features:

1. Add test files in ``tests/test_files/``. These files should contain examples of
   properly formatted constructs.
2. Implement the feature in the appropriate module
3. Add tests in ``tests/test_main.py``
4. Add an entry to CHANGES.rst
