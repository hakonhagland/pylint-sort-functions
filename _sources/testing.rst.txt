Testing
=======

This document provides comprehensive guidance for testing the PyLint Sort Functions plugin using all available testing approaches, from unit tests to integration testing with the Docker validation system.

.. contents::
   :local:
   :depth: 2

Overview
--------

The plugin provides multiple testing approaches for different use cases:

**Unit Testing** (``tests/test_*.py``)
   Fast, isolated tests using pytest and PyLint's CheckerTestCase framework

**Integration Testing** (``tests/integration/``)
   End-to-end tests validating CLI functionality and cross-module behavior using pytest

**Plugin Integration Testing**
   Testing the plugin with real PyLint execution in production scenarios

**Documentation Validation** (``test-validation/``)
   Docker-based system for validating all configuration examples against real frameworks

**Framework Integration Testing**
   Testing decorator exclusions with real framework code (Flask, Django, FastAPI, etc.)

Quick Start
-----------

.. code-block:: bash

   # Run all tests (unit + integration)
   make test-all

   # Run unit tests only
   make test

   # Run integration tests only
   make test-integration

   # Run with coverage
   make coverage

   # Test plugin with PyLint
   make test-plugin

   # Validate all documentation examples
   make test-documentation

Unit Testing
------------

PyLint Testing Framework
~~~~~~~~~~~~~~~~~~~~~~~~

The plugin uses PyLint's ``CheckerTestCase`` framework for unit testing:

.. code-block:: python

   from pylint.testutils import CheckerTestCase
   from pylint_sort_functions.checker import FunctionSortChecker

   class TestFunctionSortChecker(CheckerTestCase):
       CHECKER_CLASS = FunctionSortChecker

       def test_unsorted_functions(self):
           node = astroid.extract_node("""
           def zebra_function():  #@
               pass

           def alpha_function():
               pass
           """)

           with self.assertAddsMessages(
               pylint.testutils.MessageTest(
                   msg_id="W9001",
                   node=node,
               )
           ):
               self.checker.visit_module(node)

Test Structure
~~~~~~~~~~~~~~

Tests are organized in ``tests/`` directory with clear separation between unit and integration tests:

.. code-block:: text

   tests/
   ├── integration/                    # Integration tests (pytest)
   │   ├── test_privacy_cli_integration.py      # CLI integration tests
   │   ├── test_privacy_fixer_integration.py    # Privacy fixer API tests
   │   └── test_privacy_fixer_simple.py         # Simplified CLI tests
   ├── files/                          # Test data files
   │   ├── classes/                    # Class test cases
   │   ├── import_analysis/            # Import analysis test data
   │   └── modules/                    # Module test cases
   ├── test_auto_fix.py                # Auto-fix functionality
   ├── test_checker.py                 # Main checker functionality
   ├── test_cli.py                     # CLI tool unit tests
   ├── test_coverage_gaps.py           # Coverage gap validation
   ├── test_decorator_exclusions.py    # Decorator exclusion testing
   ├── test_init.py                    # Plugin initialization tests
   ├── test_privacy_fixer.py           # Privacy fixer unit tests
   ├── test_privacy_integration.py     # Privacy integration tests
   └── test_utils.py                   # Utility function tests

Running Unit Tests
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run specific test file
   pytest tests/test_checker.py

   # Run with coverage
   coverage run -m pytest tests/
   coverage report -m

   # Using make targets
   make test
   make coverage

The project enforces **100% test coverage** of source code in the ``src/`` directory.

Coverage Configuration
~~~~~~~~~~~~~~~~~~~~~~

Test coverage is configured to measure only source code quality, not test file execution:

.. code-block:: toml

   # pyproject.toml
   [tool.coverage.run]
   source = ["src"]
   omit = ["tests/*"]

   [tool.coverage.report]
   fail_under = 100

**Rationale**: Coverage measures how well tests exercise source code, following industry standard practices. Test files themselves are excluded from coverage measurement because:

- **Logical Purpose**: The goal is measuring source code quality, not test execution completeness
- **Meaningful Metrics**: Focuses coverage reports on actionable insights about production code
- **Industry Standard**: Most Python projects exclude test directories from coverage measurement
- **Cleaner Reports**: Eliminates noise from incomplete integration test execution

**Coverage Scope**: Only files in ``src/pylint_sort_functions/`` are measured, ensuring 100% coverage reflects comprehensive testing of the actual plugin code.

Integration Testing
-------------------

Integration tests validate end-to-end functionality and CLI behavior. These tests are located in ``tests/integration/`` and use pytest exclusively.

Test Types
~~~~~~~~~~

**CLI Integration Tests**
   Test command-line interface functionality with real file systems

**Privacy Fixer Integration**
   Test privacy detection and fixing workflows. The privacy fixer implementation is complete with full cross-module import analysis and comprehensive CLI support

**Cross-Module Testing**
   Test functionality across multiple Python modules and packages

Running Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run all integration tests
   make test-integration

   # Run specific integration test file
   pytest tests/integration/test_privacy_cli_integration.py -v

   # Run integration tests with verbose output
   pytest tests/integration/ -v

   # Run all tests (unit + integration)
   make test-all

**Current Status**: ✅ **All 19 integration tests are passing successfully!** The privacy fixer implementation is complete with cross-module import analysis, comprehensive CLI integration, and 100% test coverage. Integration tests complete in approximately 4 seconds, demonstrating excellent performance. GitHub issues #20, #21, and #23 have been resolved.

**Integration Test Success Metrics**:

- **Test Count**: 19 integration tests
- **Success Rate**: 100% (all tests passing)
- **Execution Time**: ~4.10 seconds
- **Coverage Areas**: CLI integration, privacy fixer workflows, cross-module analysis
- **Test Categories**: API integration, command-line interface, performance validation

Plugin Integration Testing
---------------------------

Testing with PyLint
~~~~~~~~~~~~~~~~~~~~

Test the plugin with real PyLint execution:

.. code-block:: bash

   # Basic plugin testing
   pylint --load-plugins=pylint_sort_functions src/

   # Enable only our messages
   pylint --load-plugins=pylint_sort_functions \
          --disable=all \
          --enable=unsorted-functions,unsorted-methods,mixed-function-visibility \
          src/

   # Using make targets
   make test-plugin          # Production-ready testing
   make test-plugin-strict   # Development testing (shows all issues)
   make self-check          # Same as test-plugin

Configuration Testing
~~~~~~~~~~~~~~~~~~~~~

Test different configuration approaches:

.. code-block:: bash

   # Test with .pylintrc
   echo "[MASTER]\nload-plugins = pylint_sort_functions" > .test-pylintrc
   pylint --rcfile=.test-pylintrc src/

   # Test with pyproject.toml
   pylint src/  # Uses existing pyproject.toml configuration

CLI Tool Testing
----------------

The standalone CLI tool provides auto-fix functionality:

.. code-block:: bash

   # Dry-run (show what would be changed)
   python -m pylint_sort_functions.cli --dry-run src/

   # Apply fixes
   python -m pylint_sort_functions.cli --fix src/

   # With decorator exclusions (CLI-only feature)
   python -m pylint_sort_functions.cli --fix \
          --ignore-decorators "@app.route" src/

See :doc:`cli` for complete CLI documentation.

Docker Validation System
-------------------------

The Docker validation system provides comprehensive integration testing for all documentation examples and framework configurations.

Architecture
~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~

.. code-block:: bash

   # Complete validation workflow
   make test-documentation

   # Manual container management
   make build-docker-image        # Build validation container
   make run-docker-container      # Start container
   make stop-docker-container     # Clean up

Advanced Usage
~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~

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

Validation Reports
~~~~~~~~~~~~~~~~~~

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

Critical Issues Discovered
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The validation system has already identified **4 critical documentation issues**:

.. warning::

   These plugin options are **documented but not implemented**:

   - ``ignore-decorators`` - ✅ **RESOLVED**: Now works in both CLI tool and PyLint plugin (GitHub issue #13)
   - ``enable-privacy-detection`` - ✅ **IMPLEMENTED**: Works correctly
   - ``public-api-patterns`` - ✅ **IMPLEMENTED**: Works correctly
   - ``skip-dirs`` - ❌ **NOT IMPLEMENTED**: Future feature (GitHub issue #7)

   Framework projects now **pass successfully** with decorator exclusions.

GitHub issue #13 has been resolved - decorator exclusions now work in both tools.

Framework Integration Testing
-----------------------------

Testing Decorator Exclusions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Docker validation system includes comprehensive framework testing:

**Flask Example** (``test-validation/test-projects/flask-project/``):

.. code-block:: python

   # These should be excluded from sorting due to @app.route
   @app.route('/users/<int:user_id>')  # More specific route
   def get_user(user_id):
       pass

   @app.route('/users')  # Less specific route
   def list_users():
       pass

   # These regular functions should still trigger violations
   def zebra_helper():  # Should come after alpha_helper
       pass

   def alpha_helper():
       pass

**Expected Behavior**:
   - Decorated functions (``get_user``, ``list_users``) should be **excluded** from sorting
   - Regular functions (``zebra_helper``, ``alpha_helper``) should trigger ``W9001: unsorted-functions``

**Current Reality**:
   - **PyLint Plugin**: Decorator exclusion **doesn't work** (generates config errors)
   - **CLI Tool**: Decorator exclusion works correctly with ``--ignore-decorators``

Testing Custom Frameworks
~~~~~~~~~~~~~~~~~~~~~~~~~~

To test decorator exclusions with your own framework:

1. **Create Test Project**:

   .. code-block:: text

      test-validation/test-projects/myframework-project/
      ├── src/
      │   └── framework_code.py
      ├── .pylintrc  # or pyproject.toml
      └── expected_results.json

2. **Add Configuration**:

   .. code-block:: ini

      [MASTER]
      load-plugins = pylint_sort_functions

      [MESSAGES CONTROL]
      enable = unsorted-functions,unsorted-methods

      [PYLINT_SORT_FUNCTIONS]
      ignore-decorators = @myframework.route,@myframework.command

3. **Test in Container**:

   .. code-block:: bash

      make run-docker-container
      curl -X POST http://localhost:8080/test/myframework-project

Continuous Integration Testing
------------------------------

GitHub Actions Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Performance Testing
--------------------

Load Testing the API
~~~~~~~~~~~~~~~~~~~~~

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

Benchmark Plugin Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Time plugin execution
   time pylint --load-plugins=pylint_sort_functions large_project/

   # Profile with Python profiler
   python -m cProfile -o profile.stats -c "
   import subprocess
   subprocess.run(['pylint', '--load-plugins=pylint_sort_functions', 'src/'])
   "

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

**Test Failures**

.. code-block:: bash

   # Run tests with verbose output
   pytest tests/ -v -s

   # Run specific failing test
   pytest tests/test_checker.py::TestFunctionSortChecker::test_specific_case -v

   # Debug with pdb
   pytest tests/ --pdb

Debug Mode
~~~~~~~~~~

Enable debug output in various components:

.. code-block:: bash

   # PyLint debug output
   pylint --load-plugins=pylint_sort_functions --verbose src/

   # API debug logs
   docker logs pylint-validation-container

   # Test runner debug
   python test-validation/test-runner.py --verbose

Contributing to Tests
---------------------

Adding New Test Cases
~~~~~~~~~~~~~~~~~~~~~

1. **Unit Tests**: Add to appropriate file in ``tests/``
2. **Integration Tests**: Add new test projects to ``test-validation/test-projects/``
3. **Framework Tests**: Create framework-specific test projects

Test Guidelines
~~~~~~~~~~~~~~~

- **100% Coverage Required**: All new code must include tests
- **PyLint Framework**: Use ``CheckerTestCase`` for plugin tests
- **Real Examples**: Use realistic code in test cases
- **Edge Cases**: Test boundary conditions and error cases
- **Documentation**: Update this guide when adding new testing approaches

See Also
--------

- :doc:`developer` - Plugin development and architecture
- :doc:`cli` - Command-line tool usage
- :doc:`validation-system` - Detailed validation system architecture
- :doc:`usage` - User guide with configuration examples
