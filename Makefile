ROOT := $(shell pwd)

.PHONY: coverage coverage-all coverage-html docs eof-fix help mypy ruff-check ruff-fix ruff-format test test-unit test-fast test-integration test-all test-plugin test-plugin-strict tox view-cover view-docs
.PHONY: publish-to-pypi publish-to-pypi-minor publish-to-pypi-major rstcheck rst-list-check rst-toml-check self-check
.PHONY: build-docker-image run-docker-container stop-docker-container test-documentation
.PHONY: changelog-add changelog-prepare changelog-validate

# Changelog management targets
changelog-add:
	@echo "Adding changelog entry interactively..."
	@echo "Usage: make changelog-add TYPE='fixed' MESSAGE='Bug in X module'"
	@echo "   or: make changelog-add TYPE='added' MESSAGE='New feature Y' PR=123"
	@if [ -z "$(TYPE)" ] || [ -z "$(MESSAGE)" ]; then \
		echo "❌ Error: TYPE and MESSAGE are required"; \
		echo "Example: make changelog-add TYPE='fixed' MESSAGE='Memory leak in parser'"; \
		exit 1; \
	fi
	@python scripts/add-changelog-entry.py $(TYPE) "$(MESSAGE)" \
		$(if $(PR),--pr $(PR)) \
		$(if $(ISSUE),--issue $(ISSUE)) \
		$(if $(BREAKING),--breaking)

changelog-prepare:
	@echo "Preparing changelog for release..."
	@python scripts/prepare-release-changelog.py

changelog-validate:
	@echo "Validating changelog format..."
	@python scripts/validate-changelog.py


coverage:
	@bash -c "source scripts/coverage-config.sh && coverage_unit_with_report"

coverage-html:
	@bash -c "source scripts/coverage-config.sh && coverage_unit_with_html"

coverage-all:
	@bash -c "source scripts/coverage-config.sh && coverage_all_with_report"

docs:
	cd "$(ROOT)"/docs && make clean && make html

eof-fix:
	pre-commit run end-of-file-fixer --all-files

help:
	@echo "Available targets:"
	@echo ""
	@echo "Changelog management:"
	@echo "  changelog-add         - Add entry to [Unreleased] section"
	@echo "                          Usage: make changelog-add TYPE='fixed' MESSAGE='Bug fix'"
	@echo "  changelog-prepare     - Move [Unreleased] to version (for releases)"
	@echo "  changelog-validate    - Validate changelog format"
	@echo ""
	@echo "Testing and quality:"
	@echo "  coverage              - Run unit tests with coverage report (~6s)"
	@echo "  coverage-html         - Generate HTML coverage report (unit tests only)"
	@echo "  coverage-all          - Run all tests with coverage report (~23s)"
	@echo "  view-cover            - Open coverage report in browser"
	@echo "  mypy                  - Run type checking"
	@echo "  pre-commit            - Run all pre-commit hooks"
	@echo "  rstcheck              - Check reStructuredText documentation (syntax + formatting + TOML blocks)"
	@echo "  rst-list-check        - Check RST files for list formatting issues"
	@echo "  rst-toml-check        - Check TOML syntax in RST code blocks"
	@echo "  ruff-check            - Run ruff linting"
	@echo "  ruff-fix              - Run ruff with auto-fix"
	@echo "  ruff-format           - Format code with ruff"
	@echo "  self-check            - Check code with our plugin (relaxed test rules)"
	@echo "  test                  - Run pytest tests"
	@echo "  test-unit             - Run unit tests only (~4s, excludes integration tests)"
	@echo "  test-fast             - Run unit tests excluding slow tests (~2s)"
	@echo "  test-integration      - Run integration tests only"
	@echo "  test-all              - Run all tests (unit + integration)"
	@echo "  test-plugin           - Check code with our plugin (relaxed test rules)"
	@echo "  test-plugin-strict    - Check code with our plugin (strict rules everywhere)"
	@echo "  tox                   - Run tests across Python versions"
	@echo ""
	@echo "Documentation:"
	@echo "  docs                  - Build documentation"
	@echo "  view-docs             - Open documentation in browser"
	@echo ""
	@echo "Publishing:"
	@echo "  publish-to-pypi       - Build and publish to PyPI (patch version bump)"
	@echo "  publish-to-pypi-minor - Build and publish to PyPI (minor version bump)"
	@echo "  publish-to-pypi-major - Build and publish to PyPI (major version bump)"
	@echo ""
	@echo "Git and commits:"
	@echo "  bash scripts/safe-commit.sh 'message' - Safe commit with pre-commit checks"
	@echo "                                           Supports both single-line and multi-line messages"
	@echo ""
	@echo "Utilities:"
	@echo "  eof-fix               - Fix missing newlines at end of files"
	@echo "  help                  - Show this help message"
	@echo ""
	@echo "Docker validation targets:"
	@echo "  build-docker-image    - Build the validation container"
	@echo "  run-docker-container  - Start the validation container"
	@echo "  stop-docker-container - Stop and remove the container"
	@echo "  test-documentation    - Run documentation validation tests"
	@echo ""
	@echo "Plugin testing options:"
	@echo "  test-plugin        - Production-ready (clean output, matches pre-commit)"
	@echo "  test-plugin-strict - Development review (shows all potential issues)"
	@echo ""
	@echo "Publishing options:"
	@echo "  publish-to-pypi       - Patch release (0.1.0 → 0.1.1) for bug fixes"
	@echo "  publish-to-pypi-minor - Minor release (0.1.0 → 0.2.0) for new features"
	@echo "  publish-to-pypi-major - Major release (0.1.0 → 1.0.0) for breaking changes"

mypy:
	mypy src/ tests/

pre-commit:
	pre-commit run --all-files

publish-to-pypi:
	python scripts/publish-to-pypi.py patch

publish-to-pypi-minor:
	python scripts/publish-to-pypi.py minor

publish-to-pypi-major:
	python scripts/publish-to-pypi.py major

# NOTE: Using unified rstcheck script for consistency with pre-commit hooks
# Also runs RST list format checker and TOML validation for comprehensive documentation validation
rstcheck:
	bash scripts/rstcheck.sh --recursive
	python scripts/check_rst_list_format.py --recursive docs/
	python scripts/check_rst_toml_blocks.py docs/*.rst

# Check RST files for missing newlines before lists (formatting issues)
rst-list-check:
	python scripts/check_rst_list_format.py --recursive docs/

# Check TOML syntax in RST code blocks
rst-toml-check:
	python scripts/check_rst_toml_blocks.py docs/*.rst

ruff-check:
	ruff check src tests

ruff-fix:
	ruff check --fix src tests

ruff-format:
	ruff format src tests

# Self-check using plugin (same as test-plugin for consistency)
self-check:
	@bash -c "source scripts/pylint-config.sh && pylint_check_relaxed"

test:
	pytest tests/

test-unit:
	pytest tests/ --ignore=tests/integration/

test-fast:
	pytest tests/ --ignore=tests/integration/ -m "not slow"

test-integration:
	pytest tests/integration/ -v

test-all:
	pytest tests/ -v

# Pylint configuration is centralized in scripts/pylint-config.sh
# This eliminates duplication across Makefile, pre-commit, and CI configurations.
#
# For detailed explanation of disable arguments, see scripts/pylint-config.sh
#
# QUICK REFERENCE:
#   make test-plugin        - Clean output, matches pre-commit (for daily development)
#   make test-plugin-strict - Shows all issues (for comprehensive code review)
#   make self-check         - Same as test-plugin (for consistency)

# Test plugin with relaxed rules for test files (matches pre-commit behavior)
test-plugin:
	@bash -c "source scripts/pylint-config.sh && pylint_check_relaxed"

# Test plugin with strict rules for both src and test files (shows all warnings)
test-plugin-strict:
	@bash -c "source scripts/pylint-config.sh && pylint_check_strict"

tox:
	tox

view-cover:
	@xdg-open "file://$(ROOT)/htmlcov/index.html"

view-docs:
	@xdg-open "file://$(ROOT)/docs/_build/html/index.html"

# Docker-based documentation validation system targets
# See docs/validation-system.rst for detailed documentation

build-docker-image:
	@echo "Building Docker validation container..."
	@bash scripts/build-container.sh

run-docker-container: build-docker-image
	@echo "Starting Docker validation container..."
	@echo "Cleaning up any existing container..."
	@docker stop pylint-validation-container 2>/dev/null || true
	@docker rm pylint-validation-container 2>/dev/null || true
	@docker run -d --name pylint-validation-container \
		-p 8080:8080 \
		-v $(ROOT)/dist:/dist:ro \
		pylint-sort-functions-validation
	@echo "Container started. Waiting for health check..."
	@sleep 3
	@curl -f http://localhost:8080/health || echo "Warning: Health check failed"

stop-docker-container:
	@echo "Stopping Docker validation container..."
	@docker stop pylint-validation-container 2>/dev/null || true
	@docker rm pylint-validation-container 2>/dev/null || true
	@echo "Container stopped and removed."

test-documentation: run-docker-container
	@echo "Running comprehensive documentation validation tests..."
	@echo "This validates all configuration examples in docs/ against the plugin"
	@python test-validation/test-runner.py --verbose
	@$(MAKE) stop-docker-container
