##############
 Installation
##############

docstrfmt requires Python 3.10+ to run.

*******************************
 Installing the Stable Version
*******************************

With uv
=======

To add docstrfmt to a project managed with `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

    uv add docstrfmt --group lint

With pip
========

To install the latest stable version of docstrfmt from PyPI:

.. code-block:: bash

    pip install docstrfmt

************************************
 Installing the Development Version
************************************

To install the latest development version directly from GitHub:

With uv
=======

.. code-block:: bash

    uv pip install https://github.com/LilSpazJoekp/docstrfmt/archive/master.zip

With pip
========

.. code-block:: bash

    pip install https://github.com/LilSpazJoekp/docstrfmt/archive/master.zip

.. _installing-with-daemon-support:

********************************
 Installing with Daemon Support
********************************

To install docstrfmt with support for the HTTP daemon (useful for editor integration):

With uv
=======

.. code-block:: bash

    uv add "docstrfmt[d]" --group lint

Or for the development version with daemon support:

.. code-block:: bash

    uv pip install "docstrfmt[d] @ https://github.com/LilSpazJoekp/docstrfmt/archive/master.zip"

With pip
========

.. code-block:: bash

    pip install "docstrfmt[d]"

Or for the development version with daemon support:

.. code-block:: bash

    pip install "docstrfmt[d] @ https://github.com/LilSpazJoekp/docstrfmt/archive/master.zip"

*************
 Basic Usage
*************

After installation, you can run docstrfmt from the command line:

.. code-block:: bash

    docstrfmt path/to/your_file.py path/to/your_docs.rst

You can also run docstrfmt as a module:

.. code-block:: bash

    python -m docstrfmt path/to/your_file.py path/to/your_docs.rst
