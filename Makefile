ROOT := $(shell pwd)

.PHONY: coverage docs help mypy ruff-check ruff-fix ruff-format test test-plugin test-plugin-strict tox
.PHONY: publish-to-pypi rstcheck self-check

coverage:
	coverage run -m pytest tests
	coverage report -m

coverage-html:
	coverage run -m pytest tests
	coverage html

docs:
	cd "$(ROOT)"/docs && make clean && make html

help:
	@echo "Available targets:"
	@echo "  coverage              - Run tests with coverage report"
	@echo "  coverage-html         - Generate HTML coverage report"
	@echo "  docs                  - Build documentation"
	@echo "  help                  - Show this help message"
	@echo "  mypy                  - Run type checking"
	@echo "  pre-commit            - Run all pre-commit hooks"
	@echo "  publish-to-pypi       - Build and publish to PyPI"
	@echo "  rstcheck              - Check reStructuredText documentation"
	@echo "  ruff-check            - Run ruff linting"
	@echo "  ruff-fix              - Run ruff with auto-fix"
	@echo "  ruff-format           - Format code with ruff"
	@echo "  self-check            - Check code with our plugin (relaxed test rules)"
	@echo "  test                  - Run pytest tests"
	@echo "  test-plugin           - Check code with our plugin (relaxed test rules)"
	@echo "  test-plugin-strict    - Check code with our plugin (strict rules everywhere)"
	@echo "  tox                   - Run tests across Python versions"
	@echo "  view-docs             - Open documentation in browser"
	@echo ""
	@echo "Plugin testing options:"
	@echo "  test-plugin        - Production-ready (clean output, matches pre-commit)"
	@echo "  test-plugin-strict - Development review (shows all potential issues)"

mypy:
	mypy src/ tests/

pre-commit:
	pre-commit run --all-files

publish-to-pypi:
	uv build
	twine upload dist/*

# NOTE: to avoid rstcheck to fail on info-level messages, we set the report-level to WARNING
rstcheck:
	rstcheck --report-level=WARNING -r docs/

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

view-docs:
	@xdg-open "file://$(ROOT)/docs/_build/html/index.html"
