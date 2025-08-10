#!/bin/bash

# Unified RST documentation validation script
# Used by both pre-commit hooks and Makefile to ensure consistency

set -euo pipefail

# Default values
MODE="targeted"  # "targeted" checks docs/*.rst, "recursive" checks all docs/
REPORT_LEVEL="WARNING"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --recursive|-r)
            MODE="recursive"
            shift
            ;;
        --report-level)
            REPORT_LEVEL="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--recursive|-r] [--report-level LEVEL]"
            echo ""
            echo "Options:"
            echo "  --recursive, -r         Check all files recursively in docs/ directory"
            echo "  --report-level LEVEL    Set rstcheck report level (default: WARNING)"
            echo ""
            echo "Default mode: Check docs/*.rst files only (targeted mode)"
            echo "Recursive mode: Check all files in docs/ directory recursively"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Ensure virtual environment is activated
if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source .venv/bin/activate
    elif [[ -f ".venv-linux/bin/activate" ]]; then
        # WSL-specific virtual environment
        # shellcheck source=/dev/null
        source .venv-linux/bin/activate
    else
        echo "Error: No virtual environment found. Please activate .venv or .venv-linux" >&2
        exit 1
    fi
fi

# Common rstcheck configuration
# Note: automodule is a Sphinx directive, click is used in CLI documentation
IGNORED_DIRECTIVES="automodule,click"

# Run rstcheck with appropriate arguments based on mode and filter output
# Suppress known rstcheck-core warnings while preserving actual errors
run_rstcheck() {
    local temp_output temp_stderr
    temp_output=$(mktemp)
    temp_stderr=$(mktemp)
    local exit_code=0

    if [[ "$MODE" == "recursive" ]]; then
        echo "Running rstcheck recursively on docs/ directory..."
        rstcheck --ignore-directives="$IGNORED_DIRECTIVES" --report-level="$REPORT_LEVEL" -r docs/ >"$temp_output" 2>"$temp_stderr" || exit_code=$?
    else
        echo "Running rstcheck on docs/*.rst files..."
        rstcheck --ignore-directives="$IGNORED_DIRECTIVES" --report-level="$REPORT_LEVEL" docs/*.rst >"$temp_output" 2>"$temp_stderr" || exit_code=$?
    fi

    # Show stdout (actual validation results)
    if [[ -s "$temp_output" ]]; then
        cat "$temp_output"
    fi

    # Filter stderr to suppress known rstcheck-core warnings but preserve actual errors
    if [[ -s "$temp_stderr" ]]; then
        # Suppress the specific known AttributeError warning, but show other stderr content
        grep -v "WARNING:rstcheck_core.checker:An \`AttributeError\` error occured" "$temp_stderr" || true
    fi

    # Clean up temp files
    rm -f "$temp_output" "$temp_stderr"

    # Preserve rstcheck exit code for actual validation failures
    if [[ $exit_code -ne 0 ]]; then
        echo "❌ RST documentation validation failed"
        exit $exit_code
    fi
}

run_rstcheck

echo "✅ RST documentation validation passed"
