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
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass,protected-access,import-outside-toplevel,unused-variable,redefined-outer-name,reimported,unspecified-encoding,use-implicit-booleaness-not-comparison,unsorted-methods,function-should-be-private,too-many-public-methods tests/

test:
	pytest tests/

# Pylint disable arguments explanation:
#
# UNIVERSAL DISABLES (src/ and tests/):
#   fixme              - Allow TODO/FIXME comments during development
#   unnecessary-pass   - Allow explicit pass statements for clarity
#
# TEST-SPECIFIC DISABLES (tests/ only):
#   protected-access                    - Tests must access private members for comprehensive coverage
#   import-outside-toplevel             - Tests use dynamic imports for isolation and setup
#   unused-variable                     - Tests often unpack tuples but only assert on specific values
#   redefined-outer-name               - Tests shadow outer scope for local imports and fixtures
#   reimported                         - Tests re-import modules in different scopes for isolation
#   unspecified-encoding               - Test files often use default encoding for simplicity
#   use-implicit-booleaness-not-comparison - Test assertions benefit from explicit comparisons
#   unsorted-methods                   - Tests organized by logic/workflow, not alphabetically
#   function-should-be-private         - Test functions are inherently scoped to their files
#   too-many-public-methods            - Test classes naturally have many test methods
#
# PHILOSOPHY: Production code (src/) uses strict rules for maintainability and API design.
# Test code (tests/) uses relaxed rules to enable comprehensive testing without artificial constraints.
#
# QUICK REFERENCE:
#   make test-plugin        - Clean output, matches pre-commit (for daily development)
#   make test-plugin-strict - Shows all issues (for comprehensive code review)
#   make self-check         - Same as test-plugin (for consistency)

# Test plugin with relaxed rules for test files (matches pre-commit behavior)
test-plugin:
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass,protected-access,import-outside-toplevel,unused-variable,redefined-outer-name,reimported,unspecified-encoding,use-implicit-booleaness-not-comparison,unsorted-methods,function-should-be-private,too-many-public-methods tests/

# Test plugin with strict rules for both src and test files (shows all warnings)
test-plugin-strict:
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass tests/

tox:
	tox

view-docs:
	@xdg-open "file://$(ROOT)/docs/_build/html/index.html"
