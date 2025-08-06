#!/bin/bash
# Centralized pylint configuration for pylint-sort-functions project
#
# This script provides a single source of truth for pylint disable arguments,
# eliminating duplication across:
# - Makefile targets (test-plugin, test-plugin-strict, self-check)
# - Pre-commit hooks (.pre-commit-config.yaml)
# - CI pipeline (.github/workflows/ci.yml)
#
# Usage:
#   source scripts/pylint-config.sh
#   pylint_check_relaxed    # Standard development checks
#   pylint_check_strict     # Comprehensive code review

# PYLINT DISABLE ARGUMENTS EXPLANATION:
#
# UNIVERSAL DISABLES (src/ and tests/):
#   fixme              - Allow TODO/FIXME comments during development
#   unnecessary-pass   - Allow explicit pass statements for clarity
#   duplicate-code     - Allow intentional duplication (e.g., synchronized default patterns)
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

# Universal disables for both src/ and tests/
PYLINT_UNIVERSAL_DISABLES="fixme,unnecessary-pass,broad-exception-caught,duplicate-code"

# Additional disables for test files only
PYLINT_TEST_ADDITIONAL_DISABLES="protected-access,import-outside-toplevel,unused-variable,redefined-outer-name,reimported,unspecified-encoding,use-implicit-booleaness-not-comparison,unsorted-methods,function-should-be-private,too-many-public-methods"

# Combined disables for test files
PYLINT_TEST_DISABLES="${PYLINT_UNIVERSAL_DISABLES},${PYLINT_TEST_ADDITIONAL_DISABLES}"

# Export variables for use in other scripts
export PYLINT_UNIVERSAL_DISABLES
export PYLINT_TEST_ADDITIONAL_DISABLES
export PYLINT_TEST_DISABLES

# Determine pylint runner (uv run for CI, direct for local development)
PYLINT_RUNNER=""
if command -v uv >/dev/null 2>&1 && [ -f "pyproject.toml" ]; then
    PYLINT_RUNNER="uv run "
fi

# Convenience functions for common pylint commands
pylint_check_src() {
    ${PYLINT_RUNNER}pylint --load-plugins=pylint_sort_functions --disable="$PYLINT_UNIVERSAL_DISABLES" --fail-on=unsorted-functions,unsorted-methods,mixed-function-visibility,function-should-be-private src/
}

pylint_check_tests_relaxed() {
    ${PYLINT_RUNNER}pylint --load-plugins=pylint_sort_functions --disable="$PYLINT_TEST_DISABLES" tests/
}

pylint_check_tests_strict() {
    ${PYLINT_RUNNER}pylint --load-plugins=pylint_sort_functions --disable="$PYLINT_UNIVERSAL_DISABLES" tests/
}

# Full check functions
pylint_check_relaxed() {
    echo "Checking src/ with strict rules..."
    pylint_check_src
    local src_exit_code=$?

    echo "Checking tests/ with relaxed rules..."
    pylint_check_tests_relaxed
    local tests_exit_code=$?

    # Return non-zero if either check failed
    if [ $src_exit_code -ne 0 ] || [ $tests_exit_code -ne 0 ]; then
        return 1
    fi
    return 0
}

pylint_check_strict() {
    echo "Checking src/ with strict rules..."
    pylint_check_src
    local src_exit_code=$?

    echo "Checking tests/ with strict rules..."
    pylint_check_tests_strict
    local tests_exit_code=$?

    # Return non-zero if either check failed
    if [ $src_exit_code -ne 0 ] || [ $tests_exit_code -ne 0 ]; then
        return 1
    fi
    return 0
}
