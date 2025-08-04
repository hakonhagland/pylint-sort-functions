# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PyLint plugin that enforces alphabetical sorting of functions and methods within Python classes and modules. The plugin helps maintain consistent code organization by ensuring:

- Functions are organized with public functions first (no underscore prefix), followed by private functions (underscore prefix)
- Each section is alphabetically sorted within its scope
- Clear separation between public and private sections with comment blocks
- Consistent, predictable code structure that improves readability and navigation

The plugin is designed to be published to PyPI for use by other Python projects that want to enforce this organizational pattern.

## Architecture

The plugin follows standard PyLint plugin architecture:

### Core Components
- **Checker Class**: Inherits from `BaseChecker`, implements the main sorting validation logic
- **AST Visitors**: Methods that visit function and class definition nodes to analyze code structure
- **Message Definitions**: Define warning/error messages for sorting violations
- **Registration**: Plugin registration function for PyLint integration

### Key Components
- `checker.py`: Main checker class implementing sorting validation
- `messages.py`: Message definitions and error codes
- `utils.py`: Helper functions for AST analysis and sorting logic
- `__init__.py`: Plugin entry point and registration function
- `tests/`: Comprehensive test suite using PyLint test framework

### Message Types
The plugin defines these message types:
- **W9001**: `unsorted-functions` - Functions not sorted alphabetically within their scope
- **W9002**: `unsorted-methods` - Class methods not sorted alphabetically within their scope
- **W9003**: `mixed-function-visibility` - Public and private functions not properly separated

## Development Commands

### Virtual Environment

**Standard environments (Linux, macOS, Windows with proper setup):**
Always activate the virtual environment before running commands:
```bash
source .venv/bin/activate
```

**WSL-only exception**: When Claude Code runs in WSL while the user is on Windows (e.g., user uses PowerShell but Claude runs in WSL), you cannot use the Windows `.venv` directory because:
- Windows virtual environments contain `.exe` files that cannot execute in Linux
- The `uv.lock` file contains Windows-specific Python interpreter paths
- Cross-platform path conflicts prevent proper tool execution

In this specific WSL scenario, create a separate Linux virtual environment:

```bash
# First-time WSL setup (install required system packages - run manually)
sudo apt update
sudo apt install python3-pip python3-dev python3-venv

# Create Linux-specific virtual environment (one-time setup)
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -e .  # Install main dependencies
pip install coverage mypy pytest-mock pytest ruff sphinx-rtd-theme pre-commit rstcheck tox sphinx-autodoc-typehints pylint astroid
# Note: Manual installation needed because dev dependencies are in uv-specific [tool.uv] section
# Note: pylint and astroid are core dependencies for plugin development
pre-commit install --hook-type pre-commit
pre-commit install --hook-type commit-msg

# For subsequent commands, always use .venv-linux
source .venv-linux/bin/activate
```

**Claude Code Instruction**:
- **Pure Linux/macOS environments**: Use `.venv/bin/activate`
- **WSL with Windows user setup**: Use `.venv-linux/bin/activate`
- **Windows environments**: Use `.venv/Scripts/activate` (PowerShell) or `.venv/bin/activate` (Git Bash)

### Common Commands
```bash
# Run tests
pytest tests/
make test

# Type checking
mypy src/ tests/
make mypy

# Linting and formatting
ruff check src tests
ruff check --fix src tests
ruff format src tests
make ruff-check
make ruff-fix
make ruff-format

# Coverage (requires 100%)
coverage run -m pytest tests
coverage report -m
make coverage

# Verify 100% coverage before commits
# This project enforces 100% test coverage - always run before committing:
make coverage

# Build documentation
cd docs && make clean && make html
make docs
make view-docs  # Opens docs in browser

# Test the plugin with pylint
pylint --load-plugins=pylint_sort_functions src/
pylint --load-plugins=pylint_sort_functions tests/
make test-plugin

# Plugin self-check (focused on sorting violations only)
pylint --load-plugins=pylint_sort_functions --disable=all --enable=unsorted-functions,unsorted-methods,mixed-function-visibility src/
make self-check

# Build and publish (with automatic version bumping)
make publish-to-pypi        # Patch release (0.1.0 → 0.1.1) for bug fixes
make publish-to-pypi-minor  # Minor release (0.1.0 → 0.2.0) for new features
make publish-to-pypi-major  # Major release (0.1.0 → 1.0.0) for breaking changes

# Manual version bumping (for testing)
python scripts/bump-version.py --dry-run patch  # Test version bump
python scripts/bump-version.py patch            # Actual version bump with commit
python scripts/bump-version.py --no-commit patch  # Version bump without commit

# Run all tests across Python versions
tox
make tox

# Check RST documentation
make rstcheck

# Run pre-commit hooks manually
make pre-commit
```


## Git Workflow Requirements

**Important**: This project has specific git commit requirements from Cursor rules:
- **Always activate virtual environment before running git commands**
- **NEVER use `git commit --amend` without asking user first**: Creates duplicate commit messages, overwrites history, and can cause push conflicts that require complex merge resolution

### Pre-commit Best Practices

**CRITICAL**: Always run formatting and quality checks BEFORE committing to avoid post-commit formatting changes that tempt the use of `git commit --amend`:

```bash
# Required workflow for all commits
source .venv/bin/activate

# 1. Run all checks and formatters FIRST
make pre-commit  # Runs ruff format, mypy, coverage, etc.

# 2. THEN stage and commit (hooks will pass cleanly)
git add .
git commit -m "your message"
```

**Why this prevents problems**:
- Pre-commit hooks run formatters (like `ruff format`) that modify files
- If you commit first, these modifications happen AFTER the commit
- This creates unstaged changes that tempt using `git commit --amend`
- Running checks first ensures everything is formatted before the commit

**If pre-commit hooks modify files anyway**:
```bash
# If hooks still make changes, create a separate style commit
git add .
git commit -m "style: format code with pre-commit hooks"
```

**Never use these anti-patterns**:
```bash
# ❌ DON'T: Commit then amend with formatting changes
git commit -m "fix: something"
# (pre-commit hooks modify files)
git add .
git commit --amend --no-edit  # NEVER DO THIS

# ✅ DO: Run checks first, then commit clean
make pre-commit
git add .
git commit -m "fix: something"
```

### Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. All commit messages must follow this format:

```
<type>: <description>

[optional body]

[optional footer(s)]
```

**Allowed types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, linting)
- `refactor`: Code refactoring without feature changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates
- `ci`: CI/CD configuration changes
- `perf`: Performance improvements
- `build`: Build system changes
- `revert`: Reverting previous commits

**Examples**:
- `feat: add dark mode toggle to settings`
- `fix: resolve memory leak in task processor`
- `style: format code with ruff`
- `docs: update installation instructions`

The conventional commits format is enforced by a pre-commit hook.

### Pre-commit Hooks

This project uses pre-commit hooks for code quality checks. **See "Pre-commit Best Practices" section above for the recommended workflow.**

**Why virtual environment is required**: Pre-commit hooks inherit the shell environment. If the virtual environment isn't activated, hooks that depend on tools like `coverage` (installed in `.venv`) will fail with "command not found" errors.

**Windows: Cross-Platform Pre-commit Hook Management**:
In the Windows platform, the project supports both Windows (.venv) and WSL Linux (.venv-linux) environments. However, `pre-commit install` creates hooks with hardcoded Python paths, so the last environment to run `pre-commit install` determines which environment the hooks will work in.

**For Claude Code sessions in Windows**:
- Claude uses `.venv-linux` and may run `pre-commit install` during development
- **After Claude sessions that involve commits**: User should run `pre-commit install` in Windows to restore Windows compatibility
- Claude will explicitly notify when this is needed

**Manual hook execution**:
```bash
# Run all hooks manually (recommended before committing)
source .venv/bin/activate
make pre-commit

# Bypass hooks only if absolutely necessary
git commit --no-verify -m "message"
```

The project includes these pre-commit hooks:
- `trim-trailing-whitespace`: Remove trailing whitespace
- `end-of-file-fixer`: Ensure files end with newline
- `check-yaml`: Validate YAML syntax
- `ruff`: Python linting
- `ruff-format`: Python code formatting
- `mypy`: Type checking
- `rstcheck`: reStructuredText validation
- `coverage`: Test coverage verification (enforces 100% coverage)

## Configuration

- Plugin is configured through standard PyLint configuration files (`.pylintrc` or `pyproject.toml`)
- Message codes W9001-W9003 can be enabled/disabled individually
- Plugin supports configurable options for sorting strictness and comment requirements
- Entry point defined in `pyproject.toml` for automatic plugin discovery

## Testing

- Target: 100% test coverage (enforced in pyproject.toml)
- Uses pytest with PyLint's `CheckerTestCase` for plugin testing
- Tests include both positive and negative cases for function/method sorting
- AST-based testing using `astroid.extract_node()` for test case creation
- Tests located in `tests/` directory with comprehensive edge case coverage

## Code Style

Follow the Python style guide in `.cursor/rules/python.mdc`:
- 88 character line length (Black compatible)
- Use f-strings for string interpolation
- reStructuredText docstrings for all public APIs
- Type hints for all function parameters and return types
- Use `ruff` for formatting/linting and `mypy` for type checking
- Import order: standard library → third-party → local (alphabetically sorted)
- **Avoid inline imports**: Move all imports to the top of the file for better readability and maintainability
- Functions/methods organized alphabetically within their scope
- **Module imports**: Prefer `from package import module` over `from package.module import function` for better readability and explicit provenance (e.g., `from pylint_sort_functions import utils` then use `utils.function()` instead of importing `function` directly)
- **Function organization**: Organize functions with public functions first (no underscore prefix), followed by private functions (underscore prefix), each section alphabetically sorted and clearly separated with comment blocks (e.g., `# Public functions` and `# Private functions`)
- **Class method organization**: Apply the same organization principle to class methods - organize with public methods first, followed by private methods (underscore prefix), each section alphabetically sorted and clearly separated with comment blocks (e.g., `# Public methods` and `# Private methods`). This provides predictable structure regardless of class size and makes method lookup efficient.

### Type Hints
- Always include type hints for all function parameters and return types
- Use built-in types (`list`, `dict`, `tuple`) instead of `typing` equivalents (Python 3.11+)
- Use `typing.TYPE_CHECKING` for forward references to avoid import cycles
- Example: `def process_items(items: list[str]) -> dict[str, int]:`

### Import Guidelines

**Avoid inline imports** - Place all imports at the top of the file for better readability and maintainability:

```python
# ❌ Bad: Inline imports scattered throughout functions
def test_something():
    from unittest.mock import patch
    with patch('module.function'):
        # test code

def another_test():
    from astroid import extract_node
    # more test code

# ✅ Good: All imports at the top
from unittest.mock import patch
from astroid import extract_node

def test_something():
    with patch('module.function'):
        # test code

def another_test():
    # test code using extract_node
```

**Exception**: Inline imports are acceptable only when:
- Import is conditional and may not always be needed
- Import is expensive and only used in specific code paths
- Working around circular import issues

```python
# ✅ Acceptable: Conditional import
def get_platform_specific_tool():
    if sys.platform == "win32":
        from windows_specific import Tool
        return Tool()
    else:
        from unix_specific import Tool
        return Tool()
```

## Mypy

- Always verify that added coded has sufficient type annotations by running
 `make mypy` (`mypy --strict src/ tests/`)
