PyLint Configuration
====================

This document covers all configuration options for the pylint-sort-functions plugin
when used with PyLint.

Basic Setup
-----------

Plugin Loading
~~~~~~~~~~~~~~

Add the plugin to your PyLint configuration:

**.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint.MASTER]
   load-plugins = ["pylint_sort_functions"]

**setup.cfg:**

.. code-block:: ini

   [pylint]
   load-plugins = pylint_sort_functions

Message Control
---------------

The plugin defines three message types that can be individually controlled:

Message Types
~~~~~~~~~~~~~

W9001: unsorted-functions
  Functions in a module are not sorted alphabetically within their visibility scope.

W9002: unsorted-methods
  Methods in a class are not sorted alphabetically within their visibility scope.

W9003: mixed-function-visibility
  Public and private functions/methods are not properly separated.

Enabling Messages
~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MESSAGES CONTROL]
   # Enable all sorting messages
   enable = unsorted-functions,unsorted-methods,mixed-function-visibility

   # Or enable specific messages only
   enable = unsorted-functions

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."messages control"]
   enable = [
       "unsorted-functions",
       "unsorted-methods",
       "mixed-function-visibility"
   ]

Disabling Messages
~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MESSAGES CONTROL]
   # Disable specific sorting messages
   disable = unsorted-methods

   # Disable all sorting messages
   disable = unsorted-functions,unsorted-methods,mixed-function-visibility

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."messages control"]
   disable = ["unsorted-methods"]

Plugin-Specific Configuration
-----------------------------

Decorator Exclusions
~~~~~~~~~~~~~~~~~~~~

Configure patterns for decorators that should be excluded from sorting requirements.
This is essential for framework compatibility where decorator order matters.

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   # Exclude Flask routes and Click commands
   ignore-decorators = @app.route,@*.command,@pytest.fixture

   # Multiple patterns on separate lines
   ignore-decorators = @app.route
                      @*.command
                      @pytest.fixture

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint-sort-functions]
   ignore-decorators = [
       "@app.route",
       "@*.command",
       "@pytest.fixture"
   ]

Privacy Detection Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure the privacy detection feature that suggests functions should be made private:

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   # Enable privacy detection (default: true)
   check-privacy = yes

   # Custom public API patterns (future feature)
   public-patterns = main,run,execute,setup,teardown,init

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint-sort-functions]
   check-privacy = true
   public-patterns = ["main", "run", "execute", "setup", "teardown"]

Directory Exclusions
~~~~~~~~~~~~~~~~~~~~~

Configure which directories to skip during import analysis (future feature):

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   # Skip additional directories during analysis
   skip-dirs = vendor,third_party,legacy

   # Add to default skip list
   additional-skip-dirs = custom_vendor,generated

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint-sort-functions]
   skip-dirs = ["vendor", "third_party", "legacy"]
   additional-skip-dirs = ["custom_vendor", "generated"]

Framework-Specific Configurations
---------------------------------

Flask Applications
~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [MESSAGES CONTROL]
   enable = unsorted-functions,unsorted-methods,mixed-function-visibility

   [pylint-sort-functions]
   ignore-decorators = @app.route
                      @app.before_request
                      @app.after_request
                      @app.errorhandler
                      @app.teardown_appcontext

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint.MASTER]
   load-plugins = ["pylint_sort_functions"]

   [tool.pylint."messages control"]
   enable = ["unsorted-functions", "unsorted-methods", "mixed-function-visibility"]

   [tool.pylint-sort-functions]
   ignore-decorators = [
       "@app.route",
       "@app.before_request",
       "@app.after_request",
       "@app.errorhandler",
       "@app.teardown_appcontext"
   ]

Click CLI Applications
~~~~~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [pylint-sort-functions]
   ignore-decorators = @*.command
                      @*.group
                      @*.option
                      @*.argument

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint-sort-functions]
   ignore-decorators = [
       "@*.command",
       "@*.group",
       "@*.option",
       "@*.argument"
   ]

Django Applications
~~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   ignore-decorators = @login_required
                      @csrf_exempt
                      @require_http_methods
                      @cache_page
                      @vary_on_headers

FastAPI Applications
~~~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   ignore-decorators = @app.get
                      @app.post
                      @app.put
                      @app.delete
                      @app.patch
                      @app.middleware

Pytest Test Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   ignore-decorators = @pytest.fixture
                      @pytest.mark.*
                      @pytest.parametrize

Integration Examples
--------------------

CI/CD Pipeline
~~~~~~~~~~~~~~

**.github/workflows/lint.yml:**

.. code-block:: yaml

   name: Code Quality
   on: [push, pull_request]

   jobs:
     pylint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install pylint pylint-sort-functions
         - name: Run PyLint with sorting checks
           run: |
             pylint --load-plugins=pylint_sort_functions src/

Pre-commit Hooks
~~~~~~~~~~~~~~~~

**.pre-commit-config.yaml:**

.. code-block:: yaml

   repos:
     - repo: local
       hooks:
         - id: pylint-sort-functions
           name: Check function sorting
           entry: pylint
           args: [--load-plugins=pylint_sort_functions, --disable=all, --enable=unsorted-functions,unsorted-methods,mixed-function-visibility]
           language: system
           files: \\.py$

Makefile Integration
~~~~~~~~~~~~~~~~~~~~

**Makefile:**

.. code-block:: makefile

   .PHONY: lint-sorting
   lint-sorting:
   	pylint --load-plugins=pylint_sort_functions \
   	       --disable=all \
   	       --enable=unsorted-functions,unsorted-methods,mixed-function-visibility \
   	       src/

tox Configuration
~~~~~~~~~~~~~~~~~

**tox.ini:**

.. code-block:: ini

   [testenv:lint]
   deps =
       pylint
       pylint-sort-functions
   commands =
       pylint --load-plugins=pylint_sort_functions src/

Advanced Configuration
----------------------

Per-File Overrides
~~~~~~~~~~~~~~~~~~

Use PyLint's standard per-file configuration:

**.pylintrc:**

.. code-block:: ini

   [MESSAGES CONTROL]
   # Disable sorting checks for specific files
   per-file-ignores =
       legacy_code.py:unsorted-functions,unsorted-methods
       third_party/*.py:unsorted-functions,unsorted-methods,mixed-function-visibility

Multiple Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For projects with multiple components:

**src/.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [pylint-sort-functions]
   ignore-decorators = @app.route

**tests/.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [pylint-sort-functions]
   ignore-decorators = @pytest.fixture,@pytest.mark.*

Custom Message Formats
~~~~~~~~~~~~~~~~~~~~~~

Customize how sorting messages are displayed:

**.pylintrc:**

.. code-block:: ini

   [REPORTS]
   msg-template = {path}:{line}:{column}: [{msg_id}({symbol})] {msg}

Output Configuration
--------------------

JSON Output
~~~~~~~~~~~

For integration with other tools:

.. code-block:: bash

   pylint --load-plugins=pylint_sort_functions --output-format=json src/

Parsing the output:

.. code-block:: python

   import json
   import subprocess

   result = subprocess.run([
       'pylint',
       '--load-plugins=pylint_sort_functions',
       '--output-format=json',
       'src/'
   ], capture_output=True, text=True)

   messages = json.loads(result.stdout)
   sorting_messages = [
       msg for msg in messages
       if msg['message-id'] in ['W9001', 'W9002', 'W9003']
   ]

Colorized Output
~~~~~~~~~~~~~~~~

Enable colors in terminal output:

.. code-block:: bash

   pylint --load-plugins=pylint_sort_functions --output-format=colorized src/

Troubleshooting
---------------

Plugin Not Loading
~~~~~~~~~~~~~~~~~~

**Error:** ``No such message id 'unsorted-functions'``

**Solution:** Ensure the plugin is properly loaded:

.. code-block:: bash

   # Verify plugin loading
   pylint --load-plugins=pylint_sort_functions --list-msgs | grep W900

**Error:** ``ImportError: No module named 'pylint_sort_functions'``

**Solution:** Install the plugin:

.. code-block:: bash

   pip install pylint-sort-functions

Configuration Not Applied
~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** Configuration seems to be ignored

**Solutions:**

1. Verify configuration file location:

   .. code-block:: bash

      # PyLint searches in this order:
      # 1. Command line: --rcfile=path/to/.pylintrc
      # 2. Current directory: ./.pylintrc
      # 3. Parent directories (recursively)
      # 4. Home directory: ~/.pylintrc
      # 5. /etc/pylintrc

2. Test configuration loading:

   .. code-block:: bash

      pylint --load-plugins=pylint_sort_functions --generate-rcfile

3. Use explicit configuration:

   .. code-block:: bash

      pylint --rcfile=.pylintrc --load-plugins=pylint_sort_functions src/

Performance Issues
~~~~~~~~~~~~~~~~~~

For large projects, the import analysis may be slow:

**.pylintrc:**

.. code-block:: ini

   [pylint-sort-functions]
   # Disable privacy detection for better performance
   check-privacy = no

Memory Usage
~~~~~~~~~~~~

For very large codebases:

.. code-block:: bash

   # Process directories individually
   pylint --load-plugins=pylint_sort_functions src/module1/
   pylint --load-plugins=pylint_sort_functions src/module2/

Related Documentation
---------------------

- :doc:`cli` - Command-line auto-fix tool
- :doc:`sorting` - Detailed sorting algorithm documentation
- :doc:`usage` - Usage examples and integration guides
