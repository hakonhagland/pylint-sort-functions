#!/bin/bash
# Centralized coverage configuration for pylint-sort-functions project
#
# This script provides a single source of truth for coverage commands,
# eliminating duplication across:
# - Makefile targets (coverage, coverage-html, coverage-all)
# - Pre-commit hooks (.pre-commit-config.yaml)
# - CI pipeline (.github/workflows/ci.yml)
# - Documentation examples
#
# Usage:
#   source scripts/coverage-config.sh
#   coverage_unit_tests        # Fast unit tests only (~6.5s, 332 tests)
#   coverage_all_tests         # All tests including integration (~23s, 392 tests)
#   coverage_report            # Display coverage report
#   coverage_html              # Generate HTML coverage report
#   coverage_unit_with_report  # Unit tests + report (common pattern)

# COVERAGE STRATEGY EXPLANATION:
#
# UNIT TESTS (Default for most use cases):
#   - Excludes tests/integration/ directory
#   - 332 tests in ~6.5 seconds
#   - Achieves 100% coverage (1655 statements)
#   - Used for: local development, pre-commit hooks, CI
#
# ALL TESTS (Comprehensive testing):
#   - Includes integration tests (tests/integration/)
#   - 392 tests in ~23 seconds
#   - Same 100% coverage result as unit tests
#   - Used for: comprehensive validation when needed
#
# RATIONALE:
#   Integration tests validate CLI behavior and end-to-end workflows,
#   but they don't add additional source code coverage. Unit tests
#   provide complete coverage while being 3.5x faster.

# Run coverage with unit tests only (fast, recommended for most use cases)
coverage_unit_tests() {
    coverage run -m pytest tests/ --ignore=tests/integration/
}

# Run coverage with all tests including integration tests
coverage_all_tests() {
    coverage run -m pytest tests/
}

# Display coverage report to terminal
coverage_report() {
    coverage report -m --fail-under=100
}

# Generate HTML coverage report  
coverage_html() {
    coverage html
    echo "HTML coverage report generated: htmlcov/index.html"
}

# Combined function: unit tests + report (most common pattern)
coverage_unit_with_report() {
    coverage_unit_tests && coverage_report
}

# Combined function: all tests + report
coverage_all_with_report() {
    coverage_all_tests && coverage_report
}

# Combined function: unit tests + HTML report
coverage_unit_with_html() {
    coverage_unit_tests && coverage_html
}

# Display usage information
coverage_help() {
    echo "Coverage configuration functions:"
    echo "  coverage_unit_tests         - Run unit tests with coverage (~6.5s)"
    echo "  coverage_all_tests          - Run all tests with coverage (~23s)"
    echo "  coverage_report             - Display coverage report"
    echo "  coverage_html               - Generate HTML report"
    echo "  coverage_unit_with_report   - Unit tests + report (common pattern)"
    echo "  coverage_all_with_report    - All tests + report"
    echo "  coverage_unit_with_html     - Unit tests + HTML report"
    echo "  coverage_help               - Show this help"
}