Docker Validation System
========================

The Docker validation system provides comprehensive integration testing for all documentation examples and framework configurations. This system ensures that all configuration examples in the documentation actually work correctly with the plugin implementation.

.. contents::
   :local:
   :depth: 2

Overview
--------

The validation system addresses critical needs:

- **Configuration Validation**: Ensures all examples in ``docs/pylintrc.rst`` work correctly
- **Framework Compatibility**: Tests decorator exclusions with real framework code
- **Plugin Options Verification**: Validates documented options against implementation
- **Continuous Quality**: Catches documentation/implementation mismatches early

Architecture
------------

The validation system uses a containerized approach:

.. code-block:: text

   Docker Container (Ubuntu 24.04)
   ├── Python + uv + pylint-sort-functions (from local source)
   ├── Flask API Service (port 8080)
   └── Framework Test Projects
       ├── minimal-project/     # Basic sorting violations
       ├── flask-project/       # Flask @app.route testing
       ├── django-project/      # Django decorator testing
       ├── fastapi-project/     # FastAPI endpoint testing
       ├── click-project/       # Click CLI command testing
       └── pytest-project/      # Pytest fixture testing

Local Source Installation
-------------------------

**Important**: The Docker container installs the plugin **from your local source code**, not from PyPI.

**How it works**:

1. **Source Copy**: The build process copies your current ``src/``, ``pyproject.toml``, and ``README.md`` into the container
2. **Development Installation**: Uses ``uv pip install -e .`` to install from the copied source
3. **Current State Testing**: This ensures you're testing the **exact code you're working on**

**Build Evidence**:

.. code-block:: text

   Step 14/19 : RUN cd /app && uv pip install -e .
   [91mResolved 8 packages in 87ms
   [91m   Building pylint-sort-functions @ file:///app
   [91mInstalled 3 packages in 7ms
    + pylint-sort-functions==1.0.1 (from file:///app)

The key indicator is ``(from file:///app)`` - showing local source installation, not PyPI.

**Why This Approach?**

- ✅ **Current Development State**: Tests your exact working code
- ✅ **No PyPI Dependency**: Works with unpublished or development versions
- ✅ **Immediate Testing**: Source changes are immediately testable
- ✅ **Version Accuracy**: Tests actual implementation, not outdated published versions

Quick Usage
-----------

.. code-block:: bash

   # Complete validation workflow (recommended)
   make test-documentation

This single command handles the entire workflow:

1. Builds the Docker image if needed
2. Starts the validation container
3. Runs comprehensive validation tests
4. Automatically cleans up the container
5. Generates detailed validation reports

Manual Container Management
---------------------------

For more control over the validation process:

.. code-block:: bash

   # Step-by-step container management
   make build-docker-image        # Build validation container
   make run-docker-container      # Start container
   make stop-docker-container     # Clean up

Advanced Usage
--------------

.. code-block:: bash

   # Build and start container
   make build-docker-image
   make run-docker-container

   # Run validation tests
   python test-validation/test-runner.py --verbose

   # View validation reports
   ls test-validation/reports/
   cat test-validation/reports/validation_report_*.json

   # Test specific API endpoints
   curl http://localhost:8080/health
   curl http://localhost:8080/projects
   curl -X POST http://localhost:8080/test/flask-project

   # Clean up
   make stop-docker-container

API Endpoints
-------------

The validation container exposes a REST API:

.. list-table:: Validation API Endpoints
   :widths: 10 20 70
   :header-rows: 1

   * - Method
     - Endpoint
     - Purpose
   * - GET
     - ``/health``
     - Health check and readiness status
   * - GET
     - ``/projects``
     - List available test projects
   * - POST
     - ``/config``
     - Upload configuration (.pylintrc, pyproject.toml, setup.cfg)
   * - POST
     - ``/test/{project}``
     - Run PyLint on specific test project
   * - GET
     - ``/results/{test_id}``
     - Get detailed test results
   * - POST
     - ``/reset``
     - Reset configuration to clean state
   * - GET
     - ``/plugin-info``
     - Get plugin information and available options

What Gets Validated
-------------------

**Documentation Examples**
   All configuration examples from ``docs/pylintrc.rst`` are extracted and tested

**Plugin Options**
   Documented options are validated against actual plugin implementation

**Framework Compatibility**
   Decorator exclusion behavior tested with real framework code:

   - **Flask**: ``@app.route``, ``@app.before_request``
   - **Django**: ``@login_required``, ``@csrf_exempt``
   - **FastAPI**: ``@app.get``, ``@app.post``
   - **Click**: ``@cli.command``, ``@click.group``
   - **Pytest**: ``@pytest.fixture``, ``@pytest.mark.*``

**Configuration Formats**
   Multiple configuration formats are tested:

   - ``.pylintrc`` format
   - ``pyproject.toml`` format
   - ``setup.cfg`` format

Configuration Extraction Algorithm
----------------------------------

The ``test-validation/test-runner.py`` script automatically extracts and validates all configuration examples from the documentation using pattern matching.

Extraction Process
~~~~~~~~~~~~~~~~~~

The ``ConfigExtractor`` class (lines 119-220 in test-runner.py) performs the following steps:

1. **Reads documentation file**: Loads ``docs/pylintrc.rst`` content
2. **Scans for code blocks**: Identifies reStructuredText code blocks
3. **Extracts configuration content**: Captures the indented content within each block
4. **Filters relevant examples**: Keeps only blocks containing ``pylint_sort_functions`` references
5. **Categorizes by type**: Groups into .pylintrc, pyproject.toml, and setup.cfg examples

Pattern Details
~~~~~~~~~~~~~~~

The extraction uses regular expressions to find RST code blocks:

**INI Configuration Blocks** (.pylintrc format):

.. code-block:: python

   # Pattern for RST ini code blocks
   rst_ini_pattern = r'\.\. code-block:: ini\s*\n\n((?:[ \t]+.*\n)*)'

**TOML Configuration Blocks** (pyproject.toml format):

.. code-block:: python

   # Pattern for RST toml code blocks
   rst_toml_pattern = r'\.\. code-block:: toml\s*\n\n((?:[ \t]+.*\n)*)'

**Content Extraction**:

- Captures all indented lines following the code-block directive
- Continues until reaching a non-indented line
- Strips the leading indentation from extracted content

Historical Issues (Resolved)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bug (RESOLVED)**: The previous implementation used Markdown-style patterns (````ini`) instead of RST patterns (``.. code-block:: ini``), causing it to miss configuration examples.

**Impact (BEFORE FIX)**: Only 1 example was found instead of the 28+ examples actually present:

- 19 ini code blocks (for .pylintrc examples)
- 9 toml code blocks (for pyproject.toml examples)

**Fix Applied**: Updated the regex patterns to match RST syntax:

.. code-block:: python

   # Previous (incorrect) pattern
   pylintrc_pattern = r"```ini\s*\n(.*?)\n```"  # Markdown style

   # Current (correct) pattern
   pylintrc_pattern = r'\.\. code-block:: ini\s*\n\n((?:[ \t]+.*\n)*)'  # RST style

Current Status
~~~~~~~~~~~~~~

**Extraction Success**: The configuration extraction now works correctly:

- **16 examples found**: 6 .pylintrc + 9 pyproject.toml + 1 setup.cfg
- **100% validation success**: All extracted examples pass validation
- **Proper filtering**: Tox.ini content is correctly excluded from .pylintrc examples
- **Pattern matching**: RST code blocks are properly parsed with indentation handling

**Validation Results**:

- Total tests: 16
- Passed: 16
- Failed: 0
- Success rate: 100.0%

Validation Reports
------------------

The system generates detailed JSON reports in ``test-validation/reports/``:

.. code-block:: json

   {
     "timestamp": "2025-08-07 15:47:44",
     "summary": {
       "total_tests": 1,
       "passed_tests": 1,
       "failed_tests": 0,
       "success_rate": 1.0,
       "config_errors": 0,
       "plugin_issues": 4
     },
     "plugin_issues": [
       "Documented option 'ignore-decorators' not found in plugin implementation",
       "Documented option 'check-privacy' not found in plugin implementation"
     ],
     "framework_results": {
       "flask-project": {
         "total_messages": 12,
         "config_errors": 1,
         "plugin_messages": 7,
         "success": false
       }
     }
   }

Report Contents
~~~~~~~~~~~~~~~

Each validation report includes:

- **Summary Statistics**: Total tests, pass/fail counts, success rate
- **Configuration Errors**: Invalid options or syntax errors in examples
- **Plugin Issues**: Mismatches between documentation and implementation
- **Framework Results**: Per-framework test results with detailed metrics
- **Detailed Results**: Full test output for each validated example

Critical Issues Discovered
--------------------------

The validation system has already identified **4 critical documentation issues**:

.. warning::

   These plugin options are **documented but not implemented**:

   - ``ignore-decorators`` - ✅ **RESOLVED**: Now works in both CLI tool and PyLint plugin (GitHub issue #13)
   - ``enable-privacy-detection`` - ✅ **IMPLEMENTED**: Works correctly
   - ``public-api-patterns`` - ✅ **IMPLEMENTED**: Works correctly
   - ``skip-dirs`` - ❌ **NOT IMPLEMENTED**: Future feature (GitHub issue #7)

   Framework projects now **pass successfully** with decorator exclusions.

GitHub issue #13 has been resolved - decorator exclusions now work in both tools.

Continuous Integration
----------------------

GitHub Actions Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The validation system integrates with CI/CD:

.. code-block:: yaml

   # .github/workflows/validate-docs.yml
   name: Documentation Validation

   on: [push, pull_request]

   jobs:
     validate-docs:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Build validation container
           run: make build-docker-image
         - name: Run documentation tests
           run: make test-documentation
         - name: Upload validation report
           uses: actions/upload-artifact@v3
           with:
             name: validation-report
             path: test-validation/reports/

Pre-commit Integration
~~~~~~~~~~~~~~~~~~~~~~

Validation tests can run in pre-commit hooks:

.. code-block:: yaml

   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: validate-docs
           name: Validate documentation examples
           entry: make test-documentation
           language: system
           pass_filenames: false

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Docker Build Failures**

.. code-block:: bash

   # Clear Docker cache
   docker system prune -f

   # Rebuild without cache
   docker build --no-cache -t pylint-sort-functions-validation .

**Container Won't Start**

.. code-block:: bash

   # Check container logs
   docker logs pylint-validation-container

   # Check if port is in use
   lsof -i :8080

   # Use different port
   docker run -p 8081:8080 pylint-sort-functions-validation

**Plugin Not Found in Container**

.. code-block:: bash

   # Verify plugin installation
   docker exec pylint-validation-container pylint --list-extensions

   # Check Python path
   docker exec pylint-validation-container python -c "
   import pylint_sort_functions; print(pylint_sort_functions.__file__)
   "

**Extraction Finds Too Few Examples**

If the test runner reports finding fewer configuration examples than expected:

1. Check the extraction patterns in ``test-validation/test-runner.py``
2. Verify patterns match the documentation format (RST vs Markdown)
3. Run with ``--verbose`` flag to see extraction details
4. Review ``docs/pylintrc.rst`` for the actual code block format

Performance Considerations
--------------------------

Load Testing the API
~~~~~~~~~~~~~~~~~~~~

Test the validation API under load:

.. code-block:: bash

   # Install hey (HTTP load testing tool)
   go install github.com/rakyll/hey@latest

   # Load test health endpoint
   hey -n 1000 -c 10 http://localhost:8080/health

   # Load test project testing
   hey -n 100 -c 5 -m POST http://localhost:8080/test/minimal-project

Container Resource Usage
~~~~~~~~~~~~~~~~~~~~~~~~

Monitor container performance:

.. code-block:: bash

   # View container resource usage
   docker stats pylint-validation-container

   # View container logs
   docker logs pylint-validation-container

   # Execute commands in container
   docker exec -it pylint-validation-container bash

See Also
--------

- :doc:`testing` - Main testing documentation
- :doc:`pylintrc` - Configuration examples being validated
- :doc:`developer` - Plugin development and architecture
- :doc:`validation-system` - Additional validation system details
