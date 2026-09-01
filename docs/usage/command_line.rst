######################
 Command Line Options
######################

This page documents every option accepted by the ``docstrfmt`` and ``docstrfmtd``
commands. The reference below is generated directly from the click definitions in
``docstrfmt.main`` and ``docstrfmt.server``, so it always matches the installed
version.

.. note::

    Most formatting options can also be set in ``pyproject.toml`` under the
    ``[tool.docstrfmt]`` section. Command-line options take precedence over
    configuration file settings. See :doc:`/configuration` for details.

**********
 docstrfmt
**********

.. click:: docstrfmt.main:main
    :prog: docstrfmt
    :nested: full

Line length resolution
======================

When ``--line-length`` is not passed on the command line, docstrfmt resolves the
effective line length in the following order:

1. ``--line-length`` on the command line
2. ``tool.docstrfmt.line-length`` in the ``pyproject.toml`` specified via
   ``--pyproject-config``
3. ``tool.black.line-length`` in the ``pyproject.toml`` specified via
   ``--pyproject-config``
4. ``tool.docstrfmt.line-length`` in an auto-discovered ``pyproject.toml``
5. ``tool.black.line-length`` in an auto-discovered ``pyproject.toml``
6. Black's default line length

***********
 docstrfmtd
***********

The daemon exposes the same formatter over HTTP. Install the ``d`` extra
(``pip install "docstrfmt[d]"``) to pull in the ``aiohttp`` dependency, then
start the server:

.. click:: docstrfmt.server:main
    :prog: docstrfmtd
    :nested: full

See :doc:`/usage/daemon_mode` for the request format and client integration
examples.
