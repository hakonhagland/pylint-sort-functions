# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Always Use Safe Commits

**MANDATORY FOR ALL COMMITS**: Use `bash scripts/safe-commit.sh 'message'` instead of `git commit -m`
- This prevents losing detailed commit messages due to pre-commit hook modifications
- Supports both single-line and multi-line messages automatically
- See "Git Workflow Requirements" section for full details

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
# Uses centralized coverage configuration from scripts/coverage-config.sh
make coverage       # Fast unit tests only (~6s, recommended)
make coverage-all   # All tests including integration (~23s)
make coverage-html  # Generate HTML report
make view-cover     # Open HTML report in browser

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

# Changelog management (use during development)
make changelog-add TYPE='fixed' MESSAGE='Memory leak in parser'  # Add bug fix
make changelog-add TYPE='added' MESSAGE='New CLI option' PR=123  # With PR link
make changelog-add TYPE='changed' MESSAGE='Improved performance' BREAKING=1  # Breaking change
# Types: added, changed, deprecated, removed, fixed, security

# Build and publish (with automatic version bumping and changelog)
make publish-to-pypi        # Patch release (0.1.0 → 0.1.1) for bug fixes
make publish-to-pypi-minor  # Minor release (0.1.0 → 0.2.0) for new features
make publish-to-pypi-major  # Major release (0.1.0 → 1.0.0) for breaking changes
# These commands will:
# 1. Move [Unreleased] changelog entries to versioned section
# 2. Bump version in pyproject.toml
# 3. Build and upload to PyPI
# 4. Create and push git tag (triggers GitHub Action for release)

# Manual version bumping (for testing)
python scripts/bump-version.py --dry-run patch  # Test version bump
python scripts/bump-version.py patch            # Actual version bump with commit
python scripts/bump-version.py --no-commit patch  # Version bump without commit

# Run all tests across Python versions
tox
make tox

# Check RST documentation (syntax, formatting, and code block validation)
make rstcheck  # Runs rstcheck, list format checker, and TOML validation
make rst-list-check   # Only check RST list formatting issues
make rst-toml-check   # Only check TOML syntax in RST code blocks

# Run pre-commit hooks manually
make pre-commit

# Fix missing newlines at end of files
make eof-fix
```

## Changelog Management Workflow

### During Development
**Update CHANGELOG.md continuously** as you develop, not just when releasing:

```bash
# After implementing a feature or fix:
make changelog-add TYPE='fixed' MESSAGE='Memory leak in parser'

# With PR/issue references:
make changelog-add TYPE='added' MESSAGE='Dark mode support' PR=45 ISSUE=12

# For breaking changes:
make changelog-add TYPE='changed' MESSAGE='API redesign' BREAKING=1
```

Entries are added to the `[Unreleased]` section at the top of CHANGELOG.md.

### Release Process
When ready to release, the `make publish-to-pypi*` commands handle everything:

1. **Changelog**: Moves `[Unreleased]` → `[1.0.1] - 2025-01-08`
2. **Version**: Bumps version in `pyproject.toml`
3. **Build**: Creates distribution packages
4. **Upload**: Publishes to PyPI
5. **Tag**: Creates git tag `v1.0.1` and pushes it
6. **GitHub Action**: Tag push triggers automated GitHub release

### GitHub Actions Automation
The `.github/workflows/release.yml` provides multiple trigger methods:

- **Tag push** (primary): `git push origin v1.0.1` → Automatic PyPI release
- **Manual dispatch**: GitHub Actions UI → Test PyPI for testing
- **GitHub Release**: Creating release in UI → PyPI publication

### Best Practices for Claude Code
When using Claude Code to make changes:

1. **For bug fixes/features**: Always add changelog entry
   ```bash
   make changelog-add TYPE='fixed' MESSAGE='Your fix description'
   ```

2. **For internal changes**: Skip changelog (tests, docs, refactoring)

3. **Claude will remind you**: When completing user-facing changes

## Git Workflow Requirements

**Important**: This project has specific git commit requirements from Cursor rules:
- **Always activate virtual environment before running git commands**
- **NEVER use `git commit --amend` without asking user first**: Creates duplicate commit messages, overwrites history, and can cause push conflicts that require complex merge resolution

### MANDATORY: Safe Commit Workflow for Claude Code

**IMPORTANT FOR CLAUDE CODE**: ALWAYS use the safe commit workflow to prevent losing commit messages:

```bash
# STEP 1: Always stage files BEFORE running safe-commit
git add <file1> <file2>  # Stage specific files
# OR
git add -A               # Stage all changes

# STEP 2: Then run safe-commit
bash scripts/safe-commit.sh 'Your detailed commit message'

# Works seamlessly with multi-line messages:
bash scripts/safe-commit.sh 'feat: comprehensive feature description

- Detailed bullet point
- Another detail
- Handles quotes and special characters automatically

Co-Authored-By: Claude <noreply@anthropic.com>'
```

**Why this is MANDATORY**:
- **Staging first prevents confusing workflows**: Without staging, pre-commit will temporarily stash unstaged files, creating cryptic warnings and potential confusion
- **Clear intent**: Explicitly staging files shows exactly what you intend to commit
- **Pre-commit runs cleanly**: The script runs pre-commit checks on staged files only, avoiding stash/restore operations
- **Better error detection**: The improved script now detects staging issues upfront with helpful guidance
- **Prevents commit message loss**: Ensures comprehensive commit messages are preserved throughout the process
- **Handles multi-line messages**: Works seamlessly with detailed commit messages
- **Avoids git commit --amend**: Prevents the need for potentially problematic history rewrites

**Alternative usage (legacy compatibility)**:
```bash
# Also supports traditional flag-based usage:
bash scripts/safe-commit.sh -m "Your commit message"
bash scripts/safe-commit.sh --file path/to/message.txt
```

### Handling Validation Failures

**Enhanced Message Preservation (v2.0)**: The script now preserves your commit message in ALL failure scenarios:

#### Scenario 1: Validation Fails (No File Modifications)
```bash
# When validation fails with syntax/type errors that require manual fixes
bash scripts/safe-commit.sh 'feat: comprehensive feature description

- Detailed implementation notes
- Important context and rationale
- Complex multi-line message'

# Output:
# ❌ Pre-commit validation failed
# 💾 Your commit message has been saved to: /tmp/pylint-sort-functions-commit-msg-abc123
# 4. Re-run with saved message: bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'

# Fix the validation issues, stage files, then recover message:
git add fixed-files.py
bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'  # Message restored!
```

#### Scenario 2: Maximum Retries Reached (NEW!)
```bash
# When pre-commit hooks keep making changes and hit retry limit
bash scripts/safe-commit.sh 'fix: critical bug with detailed explanation

- Multiple paragraphs of context
- Implementation details'

# Output (after 3 auto-retry attempts):
# ❌ Maximum retries reached
# 💾 Your commit message has been saved to: /tmp/pylint-sort-functions-commit-msg-xyz789
# 3. Fix issues manually, stage fixes: git add <fixed-files>
# 4. Re-run with saved message: bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-xyz789'
```

**Collision Detection with Project-Specific Naming**: The script now uses project-specific temp file naming to prevent conflicts:

```bash
bash scripts/safe-commit.sh 'different message'

# Output:
# ⚠️  Found 1 saved commit message(s) from previous validation failures:
# 📝 /tmp/pylint-sort-functions-commit-msg-abc123
#    Preview: feat: comprehensive feature description...
#
# Options:
# 1. Use most recent saved message: bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'
# 2. Continue with new message (ignores saved messages)
# 3. Clean up old messages: rm /tmp/pylint-sort-functions-commit-msg-*
# 💡 Tip: Add --force flag to skip this check
```

**Security Improvements**:
- **Project-specific naming**: Uses `pylint-sort-functions-commit-msg-*` pattern instead of generic `tmp.*`
- **Namespace isolation**: Prevents conflicts with other processes using `/tmp`
- **Automatic cleanup**: Temp files are removed after successful commits

**Force Override**: Skip saved message detection when intentional:
```bash
bash scripts/safe-commit.sh --force 'intentionally new message'
```

**Key Benefits**:
- **No more lost messages**: Validation failures no longer lose detailed commit messages
- **Immediate failure detection**: Validation errors exit immediately (no pointless retries)
- **Claude Code friendly**: Handles complex multi-line messages seamlessly
- **Automatic cleanup**: Temporary files removed after successful commits

### Pre-commit Best Practices

**The Problem**: Pre-commit hooks run formatters that modify files AFTER you stage them. If you commit without running checks first, the hooks modify files during the commit, which can:
1. Cause the commit to fail, losing your detailed message
2. Create unstaged changes that tempt using `git commit --amend`
3. Result in generic "style fix" commits instead of comprehensive messages

**The Solution**: The `safe-commit.sh` script handles this automatically by:
1. Running all pre-commit checks first
2. Auto-retrying if hooks make formatting changes (up to 3 attempts)
3. Only committing when all checks pass
4. Preserving your complete commit message throughout the process

**If pre-commit hooks modify files anyway**:
```bash
# If hooks still make changes, create a separate style commit
git add .
bash scripts/safe-commit.sh 'style: format code with pre-commit hooks'
```

### Handling Pre-commit Hook File Modifications

**Problem**: When pre-commit hooks modify files after staging, this can interfere with comprehensive commit messages, potentially replacing detailed commit messages with generic "style" messages.

**Root Cause**: Pre-commit hooks run after `git commit` but before the commit is finalized. If hooks modify staged files, the modifications become part of the commit, potentially overriding the intended commit message flow.

**Prevention Strategy**:

1. **Always run pre-commit checks manually BEFORE staging**:
```bash
# 1. Make your changes
# 2. Run pre-commit manually to catch all formatting issues
make pre-commit

# 3. Stage files AFTER pre-commit formatting is complete
git add .

# 4. Commit with confidence that hooks won't modify files
bash scripts/safe-commit.sh 'your comprehensive commit message'
```

2. **For comprehensive commits with detailed messages, use this workflow**:
```bash
# For major documentation/feature work requiring detailed commit messages:

# 1. Complete all work
# 2. Run pre-commit to fix any formatting
make pre-commit

# 3. Review changes and ensure everything is ready
git status
git diff --staged

# 4. Stage everything and commit with comprehensive message
git add .
bash scripts/safe-commit.sh 'docs: comprehensive feature enhancement

Detailed multi-line commit message
with all the important details...

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>'
```

3. **If commit message gets lost due to validation failures**:
```bash
# safe-commit.sh v2.0+ automatically saves your message on failure
# The script will show you the saved file path and recovery command:
bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'
```

**Key Principle**: Separate formatting fixes from substantive commits to preserve detailed commit messages for important work.

**Never use these anti-patterns**:
```bash
# ❌ DON'T: Commit then amend with formatting changes
bash scripts/safe-commit.sh 'fix: something'
# (pre-commit hooks modify files)
git add .
git commit --amend --no-edit  # NEVER DO THIS

# ✅ DO: Run checks first, then commit clean
make pre-commit
git add .
bash scripts/safe-commit.sh 'fix: something'
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

# Note: safe-commit.sh handles pre-commit checks automatically
# If you absolutely must bypass hooks (not recommended):
bash scripts/safe-commit.sh --force 'message'
```

The project includes these pre-commit hooks:
- `trim-trailing-whitespace`: Remove trailing whitespace
- `end-of-file-fixer`: Ensure files end with newline (run `make eof-fix` to fix manually)
- `check-yaml`: Validate YAML syntax
- `ruff`: Python linting
- `ruff-format`: Python code formatting
- `mypy`: Type checking
- `rstcheck`: reStructuredText syntax validation
- `rst-list-format`: RST list formatting checker (detects missing newlines before lists)
- `coverage`: Test coverage verification (enforces 100% coverage)

### RST List Format Checker

The project includes a custom RST list format checker (`scripts/check_rst_list_format.py`) that detects a common documentation formatting issue where bullet lists immediately follow text ending with a colon without a blank line separator. This causes RST to render the list items inline rather than as proper bullet points.

**Example of the issue detected:**
```rst
# Incorrect (missing blank line):
**Some heading**:
- Item 1
- Item 2

# Correct (with blank line):
**Some heading**:

- Item 1
- Item 2
```

The checker is integrated into:
- Makefile: `make rstcheck` and `make rst-list-check`
- Pre-commit hooks: Runs automatically on RST file changes
- CI/CD: Validates documentation in GitHub Actions

## Configuration

- Plugin is configured through standard PyLint configuration files (`.pylintrc` or `pyproject.toml`)
- Message codes W9001-W9003 can be enabled/disabled individually
- Plugin supports configurable options for sorting strictness and comment requirements
- Entry point defined in `pyproject.toml` for automatic plugin discovery

## Testing

**Test Organization Structure:**
```
tests/
├── integration/              # End-to-end pytest tests
│   ├── test_privacy_cli_integration.py    # CLI functionality
│   ├── test_privacy_fixer_integration.py  # Privacy fixer API (some skipped)
│   └── test_privacy_fixer_simple.py       # Simplified CLI tests
├── files/                    # Test data and fixtures
└── test_*.py                 # Unit tests (pytest + CheckerTestCase)
```

**Testing Frameworks:**
- **Unit Tests**: Use pytest with PyLint's `CheckerTestCase` for plugin-specific testing
- **Integration Tests**: Pure pytest for CLI and end-to-end functionality
- **Target**: 100% test coverage (enforced in pyproject.toml)
- **AST-based testing**: Uses `astroid.extract_node()` for test case creation

**Running Tests:**
```bash
make test              # Unit tests only
make test-integration  # Integration tests only
make test-all         # All tests (unit + integration)
make coverage         # Coverage report (must be 100%)
```

## Documentation Validation Tools

The project includes comprehensive validation tools for documentation quality:

### RST Documentation Validation

**rstcheck**: Validates reStructuredText syntax and formatting
- Integrated into pre-commit hooks and `make rstcheck`
- Catches RST syntax errors, broken links, and formatting issues

**RST List Format Checker** (`scripts/check_rst_list_format.py`):
- Detects missing blank lines before bullet lists in RST files
- Prevents common formatting issues where lists render inline instead of as proper bullets
- Example of caught issue:
  ```rst
  # Incorrect (missing blank line):
  **Some heading**:
  - Item 1

  # Correct (with blank line):
  **Some heading**:

  - Item 1
  ```

**TOML Code Block Validator** (`scripts/check_rst_toml_blocks.py`):
- Validates TOML syntax within `.. code-block:: toml` directives
- Prevents documentation rendering issues caused by invalid TOML syntax
- Catches common issues like incorrect multi-line string syntax
- Integrated into pre-commit hooks and `make rstcheck`

### Usage

```bash
# Run all documentation validation (recommended)
make rstcheck

# Individual validation tools
make rst-list-check   # Check list formatting only
make rst-toml-check   # Check TOML blocks only
```

All validation tools are automatically run by pre-commit hooks, ensuring documentation quality before commits.

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
- **ALWAYS ensure files end with a newline character** - Include trailing newline when editing/creating files to prevent pre-commit hook modifications
- **Module imports**:
  - **Functions**: Prefer `from package import module` over `from package.module import function` for better readability and explicit provenance (e.g., `from pylint_sort_functions import utils` then use `utils.function()` instead of importing `function` directly)
  - **Classes**: Use author's judgment based on context - consider number of classes, name clarity, and usage patterns. Direct import of classes is acceptable when it improves readability (e.g., `from package.module import ClassName` is fine for clear configuration classes)
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
