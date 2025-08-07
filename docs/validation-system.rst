Documentation Validation System
=================================

This document describes the comprehensive Docker-based testing system for validating all PyLint configuration examples in the project documentation.

Overview
--------

The validation system addresses a critical need: ensuring all configuration examples in ``docs/pylintrc.rst`` actually work correctly. Currently, numerous ``.pylintrc``, ``pyproject.toml``, and framework-specific configurations are untested, potentially leading to user frustration when examples don't work.

**Problem Solved:**
- Configuration examples that don't match actual plugin options
- Framework decorator exclusions that may not work as documented
- "Future feature" labels that may actually be implemented
- Integration examples (CI/CD, pre-commit) with syntax errors

Architecture
------------

System Components
~~~~~~~~~~~~~~~~~

The validation system uses a containerized approach with HTTP API communication::

    Docker Container (Ubuntu 24.04)
    ├── HTTP API Service (Flask on port 8080)
    ├── Python Environment (uv + pylint + pylint-sort-functions)
    └── Test Projects/
        ├── minimal-project/       # Basic sorting violations
        ├── flask-project/         # Flask route decorators
        ├── click-project/         # Click CLI commands
        ├── django-project/        # Django view decorators
        ├── fastapi-project/       # FastAPI route decorators
        └── pytest-project/        # Pytest fixture decorators

Makefile Integration
~~~~~~~~~~~~~~~~~~~~

The system integrates with the existing build process:

.. code-block:: makefile

   .PHONY: build-validation-image run-validation-container test-documentation

   build-validation-image:
   	docker build -t pylint-sort-functions-validation ./test-validation/docker/

   run-validation-container:
   	docker run -d --name pylint-validation-container \
   	           -p 8080:8080 \
   	           -v $(PWD)/dist:/dist \
   	           pylint-sort-functions-validation
   	@echo "Container started. Health check:"
   	@sleep 3
   	@curl -f http://localhost:8080/health

   test-documentation:
   	python test-validation/test-runner.py --verbose

   stop-validation-container:
   	docker stop pylint-validation-container || true
   	docker rm pylint-validation-container || true

API Design
----------

Container HTTP API
~~~~~~~~~~~~~~~~~~

The container exposes a REST API for configuration testing:

**Base URL:** ``http://localhost:8080``

.. list-table:: API Endpoints
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
     - Upload configuration (.pylintrc or pyproject.toml)
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

Request/Response Schemas
~~~~~~~~~~~~~~~~~~~~~~~~

**Configuration Upload (POST /config):**

.. code-block:: json

   {
     "type": "pylintrc|pyproject|setup_cfg",
     "content": "configuration file content",
     "name": "optional-config-name"
   }

**Test Results (POST /test/{project} Response):**

.. code-block:: json

   {
     "test_id": "uuid",
     "project": "minimal-project",
     "status": "completed|failed|running",
     "pylint_exit_code": 4,
     "messages": [
       {
         "type": "warning",
         "message-id": "W9001",
         "symbol": "unsorted-functions",
         "path": "src/test_module.py",
         "line": 10,
         "message": "Functions are not sorted alphabetically"
       }
     ],
     "execution_time": 1.23,
     "config_applied": "pylintrc"
   }

Test Projects
-------------

Each test project contains intentional violations to verify PyLint message detection and configuration behavior.

Test Project Structure
~~~~~~~~~~~~~~~~~~~~~~

**minimal-project/**: Basic sorting violations

.. code-block:: text

   minimal-project/
   ├── pyproject.toml          # Basic configuration
   ├── src/
   │   └── bad_sorting.py      # Mixed violations (W9001, W9002, W9003, W9004)
   └── expected_results.json   # Expected PyLint messages

**Example violation code:**

.. code-block:: python

   """Test module with intentional sorting violations."""

   # This should trigger W9001, W9003
   def zebra_function():
       """Public function out of order."""
       pass

   def alpha_function():
       """Should come before zebra."""
       pass

   def _private_helper():  # W9003: private before public
       """Private function in wrong position."""
       pass

   def public_after_private():  # W9003: public after private
       """Public function after private."""
       pass

   def internal_only_function():  # W9004: should be private
       """Only used internally."""
       return "helper"

   class BadClass:
       """Class with method sorting issues."""

       def zebra_method(self):  # W9002: methods unsorted
           """Method out of order."""
           pass

       def alpha_method(self):
           """Should come before zebra."""
           pass

Framework-Specific Projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**flask-project/**: Tests decorator exclusion behavior

.. code-block:: python

   from flask import Flask
   app = Flask(__name__)

   # Should be excluded from sorting due to @app.route decorators
   @app.route('/users/<int:id>')  # More specific route
   def get_user(id):
       pass

   @app.route('/users')  # Less specific route
   def list_users():
       pass

   # Regular functions should still be sorted
   def zebra_helper():
       pass

   def alpha_helper():  # W9001: should come before zebra
       pass

Expected Results Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each project includes ``expected_results.json`` with anticipated PyLint messages:

.. code-block:: json

   {
     "minimal-project": {
       "W9001": 1,
       "W9002": 1,
       "W9003": 2,
       "W9004": 1
     },
     "flask-project": {
       "W9001": 1,
       "W9002": 0,
       "W9003": 0,
       "W9004": 0
     }
   }

Test Scenarios
--------------

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Plugin Loading Syntax**

   - ``.pylintrc`` plugin loading format
   - ``pyproject.toml`` plugin loading format
   - ``setup.cfg`` plugin loading format

2. **Message Control**

   - Enable specific messages (W9001, W9002, W9003, W9004)
   - Disable specific messages
   - Message inheritance and precedence rules

3. **Plugin-Specific Options** *(Verify actual existence)*

   - ``ignore-decorators`` *(✅ implemented in both CLI and PyLint plugin)*
   - ``enable-privacy-detection`` *(✅ implemented)*
   - ``public-api-patterns`` *(✅ implemented)*
   - ``skip-dirs`` *(❌ future feature - GitHub Issue #7)*

Framework Configuration Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Decorator Exclusion Verification:**

- **Flask**: ``@app.route``, ``@app.before_request``, ``@app.errorhandler``
- **Click**: ``@*.command``, ``@*.group``, ``@*.option``
- **Django**: ``@login_required``, ``@csrf_exempt``, ``@require_http_methods``
- **FastAPI**: ``@app.get``, ``@app.post``, ``@app.middleware``
- **Pytest**: ``@pytest.fixture``, ``@pytest.mark.*``, ``@pytest.parametrize``

Integration Example Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **CI/CD Examples** - GitHub Actions YAML syntax validation
2. **Pre-commit Hooks** - YAML configuration correctness
3. **Makefile Integration** - Command syntax verification
4. **tox Configuration** - INI format and command execution

Implementation Phases
---------------------

Phase 1: Core Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Create Dockerfile with Ubuntu 24.04 + Python + uv environment
- [ ] Implement Flask API service within container
- [ ] Create Makefile targets for container management
- [ ] Test container startup and API communication
- [ ] Basic health check and project listing endpoints

Phase 2: Test Projects Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Create minimal-project with comprehensive sorting violations
- [ ] Develop framework-specific test projects (Flask, Click, Django, etc.)
- [ ] Define expected results for each test scenario
- [ ] Implement project validation logic and result comparison

Phase 3: Configuration Testing Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Test all ``.pylintrc`` examples from documentation
- [ ] Test all ``pyproject.toml`` configuration examples
- [ ] Validate plugin option names against actual implementation
- [ ] Identify discrepancies between documentation and reality

Phase 4: Integration & Automation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Create comprehensive test runner script with detailed reporting
- [ ] Integrate with GitHub Actions CI pipeline for automated testing
- [ ] Generate validation reports highlighting documentation issues
- [ ] Establish documentation update workflow based on validation results

Phase 5: Documentation Maintenance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Update ``docs/pylintrc.rst`` based on validation findings
- [ ] Add missing W9004 message documentation
- [ ] Remove "future feature" labels where features are implemented
- [ ] Fix configuration syntax errors and option name mismatches

File Structure
--------------

The validation system files are organized as follows:

.. code-block:: text

   test-validation/
   ├── docker/
   │   ├── Dockerfile              # Container build definition
   │   ├── requirements.txt        # Python dependencies
   │   └── api-service.py          # Flask API service
   ├── test-projects/
   │   ├── minimal-project/        # Basic violation testing
   │   ├── flask-project/          # Flask decorator testing
   │   ├── click-project/          # Click CLI testing
   │   ├── django-project/         # Django view testing
   │   ├── fastapi-project/        # FastAPI route testing
   │   └── pytest-project/         # Pytest fixture testing
   ├── test-runner.py              # Main test execution script
   ├── validation-report.py        # Report generation
   └── README.md                   # Usage instructions

Usage Instructions
------------------

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Build and Start Container:**

   .. code-block:: bash

      make build-validation-image
      make run-validation-container

2. **Run Documentation Tests:**

   .. code-block:: bash

      make test-documentation

3. **View Results:**

   .. code-block:: bash

      # Detailed validation report
      python test-validation/validation-report.py --output=html

4. **Clean Up:**

   .. code-block:: bash

      make stop-validation-container

CI/CD Integration
~~~~~~~~~~~~~~~~~

The validation system integrates with continuous integration:

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
           run: make build-validation-image
         - name: Run documentation tests
           run: make test-documentation
         - name: Upload validation report
           uses: actions/upload-artifact@v3
           with:
             name: validation-report
             path: test-validation/reports/

Benefits
--------

Documentation Quality Assurance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Catch Configuration Errors**: Identify broken examples before users encounter them
- **Verify Plugin Options**: Ensure all documented options actually exist and function
- **Test Integration Examples**: Validate CI/CD, pre-commit, and build tool configurations

Developer Confidence
~~~~~~~~~~~~~~~~~~~~

- **Regression Prevention**: Automated testing prevents documentation breaks in future releases
- **Implementation Verification**: Confirm plugin behavior matches documentation claims
- **Framework Compatibility**: Verify decorator exclusions work with real framework code

User Experience Improvement
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Working Examples**: Every configuration example guaranteed to function correctly
- **Accurate Documentation**: Eliminate discrepancies between docs and actual behavior
- **Framework Support**: Reliable guidance for Flask, Django, FastAPI, and other integrations

Maintenance Automation
~~~~~~~~~~~~~~~~~~~~~~

- **Continuous Validation**: Run tests on every documentation change
- **Update Detection**: Identify when new features make "future" labels obsolete
- **Quality Metrics**: Track documentation accuracy over time

Contributing
------------

To contribute to the validation system:

1. **Add Test Projects**: Create new framework-specific test projects in ``test-validation/test-projects/``
2. **Extend API**: Add new endpoints to the container API service for additional testing scenarios
3. **Improve Reporting**: Enhance validation report generation and formatting
4. **Documentation Updates**: Update this document when adding new capabilities

See `GitHub Issue #14 <https://github.com/hakonhagland/pylint-sort-functions/issues/14>`_ for current development status and planned enhancements.

Related Documentation
---------------------

- :doc:`pylintrc` - PyLint configuration options (validated by this system)
- :doc:`usage` - Usage examples and integration guides
- :doc:`cli` - Command-line tool reference
- :doc:`developer` - Plugin development and architecture

----

*This validation system transforms our documentation from "probably works" to "definitely works" and provides a foundation for maintaining accuracy as the plugin evolves.*
