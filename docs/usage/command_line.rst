######################
 Command Line Options
######################

Every option accepted by the ``docstrfmt`` command is listed below. The reference is
generated directly from the click definitions in ``docstrfmt.main``, so it always
matches the installed version.

.. note::

    Most formatting options can also be set in ``pyproject.toml`` under the
    ``[tool.docstrfmt]`` section. Command-line options take precedence over
    configuration file settings. See :doc:`/configuration` for details.

.. tip::

    For the daemon (``docstrfmtd``) options, see :doc:`/usage/daemon_mode`.

.. click:: docstrfmt.main:main
    :prog: docstrfmt
    :nested: full

.. _line-length-resolution:

************************
 Line length resolution
************************

docstrfmt resolves the effective line length in the following order:

1. :option:`--line-length <docstrfmt --line-length>` on the command line
2. ``tool.docstrfmt.line-length`` in ``pyproject.toml``
3. ``tool.black.line-length`` in the same ``pyproject.toml``
4. Black's default line length (88)

Only one ``pyproject.toml`` is read: the file given with :option:`--pyproject-config
<docstrfmt --pyproject-config>` or, when that option is not passed, the one
auto-discovered in the project root. An auto-discovered file is not consulted as a
fallback when ``--pyproject-config`` is given.
