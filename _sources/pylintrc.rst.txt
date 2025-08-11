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

The plugin defines eight message types that can be individually controlled:

Message Types
~~~~~~~~~~~~~

**Sorting Violations:**

W9001: unsorted-functions
  Functions in a module are not sorted alphabetically within their visibility scope.

W9002: unsorted-methods
  Methods in a class are not sorted alphabetically within their visibility scope.

W9003: mixed-function-visibility
  Public and private functions/methods are not properly separated.

**Privacy Violations:**

W9004: function-should-be-private
  Function appears to be internal-only based on usage analysis and should be renamed with underscore prefix.

W9005: function-should-be-public
  Private function is used externally and should be made public by removing underscore prefix.

**Section Header Violations (Phase 2):**

W9006: method-wrong-section
  Method appears in incorrect section according to its categorization when section header validation is enabled.

W9007: missing-section-header
  Required section header is missing for a populated category when require-section-headers is enabled.

W9008: empty-section-header
  Section header exists but contains no methods when allow-empty-sections is disabled.

Enabling Messages
~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MESSAGES CONTROL]
   # Enable all sorting messages
   enable = unsorted-functions,unsorted-methods,mixed-function-visibility,function-should-be-private

   # Or enable specific messages only
   enable = unsorted-functions

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."messages control"]
   enable = [
       "unsorted-functions",
       "unsorted-methods",
       "mixed-function-visibility",
       "function-should-be-private"
   ]

Disabling Messages
~~~~~~~~~~~~~~~~~~

**.pylintrc:**

.. code-block:: ini

   [MESSAGES CONTROL]
   # Disable specific sorting messages
   disable = unsorted-methods

   # Disable all sorting messages
   disable = unsorted-functions,unsorted-methods,mixed-function-visibility,function-should-be-private

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."messages control"]
   disable = ["unsorted-methods"]

Plugin-Specific Configuration
-----------------------------

Decorator Exclusions
~~~~~~~~~~~~~~~~~~~~

The ``ignore-decorators`` option configures patterns for decorators that should be excluded from sorting requirements. This is essential for framework compatibility where decorator order matters.

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@app.route,@*.command" src/

**PyLint plugin configuration:**

.. code-block:: ini

   [function-sort]
   ignore-decorators = @app.route,@*.command,@pytest.fixture

.. code-block:: toml

   [tool.pylint."function-sort"]
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

   [function-sort]
   # Enable privacy detection (default: true)
   enable-privacy-detection = yes

   # Custom public API patterns
   public-api-patterns = main,run,execute,setup,teardown,init

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."function-sort"]
   enable-privacy-detection = true
   public-api-patterns = ["main", "run", "execute", "setup", "teardown"]

Method Categorization Configuration (Phase 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Control multi-category method organization with these options:

**.pylintrc:**

.. code-block:: ini

   [function-sort]
   # Enable multi-category system (default: no)
   enable-method-categories = yes

   # Use built-in framework preset
   framework-preset = pytest  # or unittest, pyqt

   # Custom JSON category configuration
   method-categories = [{"name": "test_methods", "patterns": ["test_*"], "priority": 10}]

   # Category sorting behavior (default: alphabetical)
   category-sorting = alphabetical  # or declaration

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."function-sort"]
   # Enable multi-category system
   enable-method-categories = true

   # Framework preset for common patterns
   framework-preset = "pytest"

   # Custom categories with pattern matching
   method-categories = '''[
       {"name": "properties", "decorators": ["@property"], "priority": 15},
       {"name": "test_methods", "patterns": ["test_*"], "priority": 10},
       {"name": "public_methods", "patterns": ["*"], "priority": 5},
       {"name": "private_methods", "patterns": ["_*"], "priority": 1}
   ]'''

   # Sort within categories
   category-sorting = "alphabetical"

Section Header Configuration (Phase 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Control functional section header validation with these options:

**.pylintrc:**

.. code-block:: ini

   [function-sort]
   # Enable section header validation (default: no)
   enforce-section-headers = yes

   # Require headers for all populated sections (default: no)
   require-section-headers = yes

   # Allow empty section headers (default: yes)
   allow-empty-sections = no

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."function-sort"]
   # Make section headers functional, not decorative
   enforce-section-headers = true

   # Require headers for all categories with methods
   require-section-headers = true

   # Disallow empty section headers
   allow-empty-sections = false

Privacy Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Control test file detection and privacy analysis behavior with these options:

**.pylintrc:**

.. code-block:: ini

   [function-sort]
   # Directory exclusions for privacy analysis
   privacy-exclude-dirs = tests,integration_tests,e2e,qa

   # File pattern exclusions for privacy analysis
   privacy-exclude-patterns = test_*.py,*_test.py,conftest.py,*_spec.py

   # Additional test patterns beyond built-in detection
   privacy-additional-test-patterns = spec_*.py,scenario_*.py

   # Enable automatic test file updates when privatizing functions
   privacy-update-tests = yes

   # Override built-in test detection (use custom patterns only)
   privacy-override-test-detection = no

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."function-sort"]
   # Directory exclusions for privacy analysis
   privacy-exclude-dirs = ["tests", "integration_tests", "e2e", "qa"]

   # File pattern exclusions for privacy analysis
   privacy-exclude-patterns = ["test_*.py", "*_test.py", "conftest.py", "*_spec.py"]

   # Additional test patterns beyond built-in detection
   privacy-additional-test-patterns = ["spec_*.py", "scenario_*.py"]

   # Enable automatic test file updates when privatizing functions
   privacy-update-tests = true

   # Override built-in test detection (use custom patterns only)
   privacy-override-test-detection = false

See :doc:`usage` for detailed privacy configuration examples and real-world use cases.

Directory Exclusions (Future Feature)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   **FUTURE FEATURE**: Directory exclusion options are planned but not yet implemented in the PyLint plugin. These configurations will be ignored.

   Track implementation progress at `GitHub Issue #7 <https://github.com/hakonhagland/pylint-sort-functions/issues/7>`_.

**Planned configuration (not yet functional):**

**.pylintrc:**

.. code-block:: ini

   [function-sort]
   # FUTURE: Skip additional directories during analysis
   skip-dirs = vendor,third_party,legacy
   additional-skip-dirs = custom_vendor,generated

**pyproject.toml:**

.. code-block:: toml

   [tool.pylint."function-sort"]
   # FUTURE: Skip additional directories during analysis
   skip-dirs = ["vendor", "third_party", "legacy"]
   additional-skip-dirs = ["custom_vendor", "generated"]

Framework-Specific Configurations
---------------------------------

The following configurations show working examples for both the CLI tool and PyLint plugin. The ``ignore-decorators`` option is supported in both tools for consistent framework compatibility.

Flask Applications
~~~~~~~~~~~~~~~~~~

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@app.route,@app.before_request" src/

**PyLint plugin configuration with decorator exclusions:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [MESSAGES CONTROL]
   enable = unsorted-functions,unsorted-methods,mixed-function-visibility

   [function-sort]
   ignore-decorators = @app.route,@app.before_request,@app.after_request,@app.errorhandler,@app.teardown_appcontext
   # Privacy configuration for Flask projects
   privacy-exclude-dirs = tests,test,testing
   privacy-additional-test-patterns = test_*.py,*_test.py,test_views_*.py,test_models_*.py

.. code-block:: toml

   [tool.pylint.MASTER]
   load-plugins = ["pylint_sort_functions"]

   [tool.pylint."messages control"]
   enable = ["unsorted-functions", "unsorted-methods", "mixed-function-visibility"]

   [tool.pylint."function-sort"]
   ignore-decorators = [
       "@app.route",
       "@app.before_request",
       "@app.after_request",
       "@app.errorhandler",
       "@app.teardown_appcontext"
   ]
   # Privacy configuration for Flask projects
   privacy-exclude-dirs = ["tests", "test", "testing"]
   privacy-additional-test-patterns = ["test_*.py", "*_test.py", "test_views_*.py", "test_models_*.py"]

Click CLI Applications
~~~~~~~~~~~~~~~~~~~~~~

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@*.command,@*.group,@*.option" src/

**PyLint plugin configuration with decorator exclusions:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [function-sort]
   ignore-decorators = @*.command,@*.group,@*.option,@*.argument

.. code-block:: toml

   [tool.pylint."function-sort"]
   ignore-decorators = [
       "@*.command",
       "@*.group",
       "@*.option",
       "@*.argument"
   ]

Django Applications
~~~~~~~~~~~~~~~~~~~

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@login_required,@csrf_exempt" src/

**PyLint plugin configuration with decorator exclusions:**

.. code-block:: ini

   [function-sort]
   ignore-decorators = @login_required,@csrf_exempt,@require_http_methods,@cache_page,@vary_on_headers
   # Privacy configuration for Django projects
   privacy-exclude-dirs = tests,test,testapp
   privacy-exclude-patterns = test*.py,tests.py,*_tests.py
   privacy-additional-test-patterns = test_*.py,*_testcase.py,test_models_*.py,test_views_*.py,test_forms_*.py

FastAPI Applications
~~~~~~~~~~~~~~~~~~~~

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@app.get,@app.post" src/

**PyLint plugin configuration:**

.. code-block:: ini

   [function-sort]
   ignore-decorators = @app.get,@app.post,@app.put,@app.delete,@app.patch,@app.middleware
   # Privacy configuration for FastAPI microservices
   privacy-exclude-dirs = tests,integration,e2e,contracts
   privacy-additional-test-patterns = *_contract.py,*_integration.py,api_test_*.py

Pytest Test Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

**CLI tool usage:**

.. code-block:: bash

   pylint-sort-functions --ignore-decorators "@pytest.fixture,@pytest.mark.*" src/

**PyLint plugin configuration:**

.. code-block:: ini

   [function-sort]
   ignore-decorators = @pytest.fixture,@pytest.mark.*,@pytest.parametrize
   # Privacy configuration for pytest projects
   privacy-exclude-dirs = tests,test,testing
   privacy-exclude-patterns = test_*.py,*_test.py,conftest.py
   privacy-additional-test-patterns = *_fixture.py,*_fixtures.py

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
       third_party/*.py:unsorted-functions,unsorted-methods,mixed-function-visibility,function-should-be-private

Multiple Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For projects with multiple components:

**src/.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [function-sort]
   ignore-decorators = @app.route

**tests/.pylintrc:**

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

   [function-sort]
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
       if msg['message-id'] in ['W9001', 'W9002', 'W9003', 'W9004']
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

   [function-sort]
   # Disable privacy detection for better performance
   enable-privacy-detection = no

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
