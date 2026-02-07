#############
 Quick Start
#############

This guide will get you up and running with docstrfmt in just a few minutes.

*************
 Basic Usage
*************

The simplest way to use docstrfmt is to format a file in place:

.. code-block:: bash

    docstrfmt myfile.rst

This will format the file and save the changes back to the same file.

***********************
 Formatting from stdin
***********************

You can also format content from stdin and output to stdout:

.. code-block:: bash

    echo "Some reStructuredText content" | docstrfmt -

***************************
 Formatting Multiple Files
***************************

To format multiple files at once:

.. code-block:: bash

    docstrfmt file1.rst file2.rst file3.py

You can also use glob patterns:

.. code-block:: bash

    docstrfmt *.rst
    docstrfmt docs/**/*.rst

*********************
 Checking Formatting
*********************

To check if files are properly formatted without modifying them:

.. code-block:: bash

    docstrfmt --check myfile.rst

This is useful for CI/CD pipelines or pre-commit hooks.

*************************
 Formatting Python Files
*************************

docstrfmt can format Python docstrings in addition to standalone reStructuredText files:

.. code-block:: bash

    docstrfmt mymodule.py

This will format all docstrings in the Python file while preserving the rest of the
code.

***************
 Configuration
***************

docstrfmt can be configured through a ``pyproject.toml`` file. Create one in your
project root:

.. code-block:: toml

    [tool.docstrfmt]
    line-length = 88
    exclude = ["build/", "dist/"]
    extend-exclude = ["tests/error_files/*"]

For more configuration options, see :doc:`configuration`.

*********
 Example
*********

Here's a simple example of how docstrfmt transforms reStructuredText:

**Before formatting:**

.. literalinclude:: examples/pre/simple_rst.rst
    :language: rst

**After formatting:**

.. literalinclude:: examples/post/simple_rst.rst
    :language: rst

************
 Next Steps
************

- Learn about all available command-line options in :doc:`usage/index`
- Configure docstrfmt for your project in :doc:`configuration`
- See more examples in :doc:`examples`
