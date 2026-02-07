####################
 Editor Integration
####################

docstrfmt can be integrated with various editors and IDEs to provide real-time
formatting and seamless workflow integration.

*********
 PyCharm
*********

Instructions derived from `black documentation
<https://black.readthedocs.io/en/stable/editor_integration.html#pycharm-intellij-idea>`_

1. Install.

   .. code-block:: sh

       pip install "docstrfmt[d]"

2. Locate where `docstrfmt` is installed.

   - On macOS / Linux / BSD:

     .. code-block:: sh

         which docstrfmt
         # /usr/local/bin/docstrfmt  # possible location

   - On Windows:

     .. code-block:: shell

         where docstrfmt
         # C:\Program Files\Python39\Scripts\docstrfmt.exe

.. note::

    Note that if you are using a virtual environment detected by PyCharm, this is an
    unneeded step. In this case the path to `docstrfmt` is
    ``$PyInterpreterDirectory$/docstrfmt``.

3. Open External tools in PyCharm.

   - On macOS:

     `PyCharm -> Preferences -> Tools -> External Tools`

   - On Windows / Linux / BSD:

     `File -> Settings -> Tools -> External Tools`

4. Click the + icon to add a new external tool with the following values:

   - Name: docstrfmt
   - Description:
   - Program: <install_location_from_step_2>
   - Arguments: ``"$FilePath$"``

5. Format the currently opened file by selecting `Tools -> External Tools -> docstrfmt`.

   - Alternatively, you can set a keyboard shortcut by navigating to `Preferences or
     Settings -> Keymap -> External Tools -> External Tools - docstrfmt`.

6. Optionally, run `docstrfmt` on every file save:

   1. Make sure you have the `File Watchers
      <https://plugins.jetbrains.com/plugin/7177-file-watchers>`_ plugin installed.
   2. Go to `Preferences or Settings -> Tools -> File Watchers` and click `+` to add a
      new watcher:

      - Name: docstrfmt
      - File type: Python
      - Scope: Project Files
      - Program: <install_location_from_step_2>
      - Arguments: ``$FilePath$``
      - Output paths to refresh: ``$FilePath$``
      - Working directory: ``$ProjectFileDir$``

   3. Uncheck "Auto-save edited files to trigger the watcher" in Advanced Options

#################
 With pre-commit
#################

.. code-block:: yaml

    repos:
      - repo: https://github.com/LilSpazJoekp/docstrfmt
        rev: stable # Replace by any tag/version: https://github.com/LilSpazJoekp/docstrfmt/tags
        hooks:
          - id: docstrfmt
            language_version: python3
            types_or: [python, rst, txt] # only needed if you want to include txt files.

**********************
 Custom Configuration
**********************

You can customize the pre-commit hook:

.. code-block:: yaml

    repos:
      - repo: https://github.com/LilSpazJoekp/docstrfmt
        rev: stable
        hooks:
          - id: docstrfmt
            language_version: python3
            types_or: [python, rst, txt]
            args: [--line-length, "72", --check]

###################
 CI/CD Integration
###################

****************
 GitHub Actions
****************

Add to your workflow:

.. code-block:: yaml

    - name: Check docstring formatting
      run: |
        pip install docstrfmt
        docstrfmt --check src/**/*.py docs/**/*.rst

    - name: Format docstrings
      run: |
        pip install docstrfmt
        docstrfmt src/**/*.py docs/**/*.rst

***********
 GitLab CI
***********

Add to your ``.gitlab-ci.yml``:

.. code-block:: yaml

    format:
      stage: format
      script:
        - pip install docstrfmt
        - docstrfmt --check src/**/*.py docs/**/*.rst
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
