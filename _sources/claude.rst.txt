Claude Code Guidelines
======================

This document provides specific guidance for Claude Code (claude.ai/code) when working with this repository.

.. note::
   **Comprehensive Guide Available**: For complete development commands, architecture details, and in-depth workflows, see `CLAUDE.md <https://github.com/hakonhagland/pylint-sort-functions/blob/main/CLAUDE.md>`_ in the project root. This document focuses on the essential Claude Code workflow.

Overview
--------

Claude Code is Anthropic's AI coding assistant that can directly read, write, and execute code in your repository. This document contains the essential workflow guidelines for Claude Code sessions.

Critical: Safe Commit Workflow
-------------------------------

**MANDATORY FOR ALL COMMITS**: Claude Code must use the safe commit workflow to prevent losing detailed commit messages when pre-commit hooks modify files.

Why This Is Required
~~~~~~~~~~~~~~~~~~~~

Pre-commit hooks run formatters (like ``ruff format``) that modify files AFTER staging. Without the safe commit workflow:

1. Commits fail due to file modifications
2. Detailed commit messages are lost
3. Generic "style fix" commits replace comprehensive messages
4. Important context and attribution is lost

Required Workflow
~~~~~~~~~~~~~~~~~

**STEP 1: Always stage files BEFORE running safe-commit**

.. code-block:: bash

   # Stage specific files
   git add file1.py file2.py
   # OR stage all changes
   git add -A

**STEP 2: Then run safe-commit**

.. code-block:: bash

   # Single command handles both simple and complex messages
   bash scripts/safe-commit.sh 'Your commit message'

   # Works seamlessly with multi-line messages and special characters
   bash scripts/safe-commit.sh 'feat: comprehensive feature description

   - Detailed bullet point
   - Another detail
   - Handles quotes and special characters automatically

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>'

**Why staging first is important:**
- Prevents confusing pre-commit warnings about unstaged files
- Makes your commit intent explicit and clear
- Allows pre-commit to run cleanly on staged files only

**Legacy compatibility (also supported):**

.. code-block:: bash

   # Traditional flag-based usage still works
   bash scripts/safe-commit.sh -m "Your message"
   bash scripts/safe-commit.sh --file path/to/message.txt

**Never use:**

.. code-block:: bash

   # ❌ AVOID: Direct git commit
   git commit -m "message"

   # ❌ AVOID: Git commit --amend without permission
   git commit --amend

How Safe Commit Works
~~~~~~~~~~~~~~~~~~~~~

The enhanced safe commit workflow (v2.0):

1. Automatically activates virtual environment
2. Runs pre-commit checks on staged files BEFORE committing
3. Auto-retries if hooks make formatting changes (up to 3 attempts)
4. Automatically stages any formatting changes made by hooks
5. Only commits when all checks pass cleanly
6. **NEW**: Preserves commit messages in ALL failure scenarios:

   * **Validation failures**: Saves message when syntax/type errors require manual fixes
   * **Max retries reached**: Saves message when persistent errors exhaust retry attempts

7. **NEW**: Uses project-specific temp file naming (``pylint-sort-functions-commit-msg-*``) to prevent conflicts
8. Automatically cleans up temporary message files after successful commits

Message Preservation Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario 1: Validation Fails (No File Modifications)**

.. code-block:: bash

   # When validation fails with errors requiring manual fixes
   bash scripts/safe-commit.sh 'feat: new feature with details'

   # Output:
   # ❌ Pre-commit validation failed
   # 💾 Your commit message has been saved to: /tmp/pylint-sort-functions-commit-msg-abc123
   # 4. Re-run with saved message: bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'

   # Fix issues, stage files, then recover message:
   git add fixed-files.py
   bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-abc123'

**Scenario 2: Maximum Retries Reached (NEW)**

.. code-block:: bash

   # When hooks keep making changes and hit retry limit
   bash scripts/safe-commit.sh 'fix: critical bug fix'

   # Output (after 3 auto-retry attempts):
   # ❌ Maximum retries reached
   # 💾 Your commit message has been saved to: /tmp/pylint-sort-functions-commit-msg-xyz789
   # 3. Fix issues manually, stage fixes: git add <fixed-files>
   # 4. Re-run with saved message: bash scripts/safe-commit.sh --file '/tmp/pylint-sort-functions-commit-msg-xyz789'

**Security Improvements**:

* **Project-specific naming**: Uses ``pylint-sort-functions-commit-msg-*`` pattern instead of generic ``tmp.*``
* **Namespace isolation**: Prevents conflicts with other processes using ``/tmp``
* **Automatic cleanup**: Temp files are removed after successful commits

This unified approach eliminates confusion between different commit methods and ensures comprehensive commit messages are always preserved, regardless of complexity.

Development Guidelines
----------------------

.. note::
   For complete development commands (``make test``, ``make coverage``, etc.) and detailed configuration, see `CLAUDE.md <https://github.com/hakonhagland/pylint-sort-functions/blob/main/CLAUDE.md>`_.

Code Style
~~~~~~~~~~

Key Python style guidelines:

* **Line length**: 88 characters (Black compatible)
* **String formatting**: Use f-strings
* **Type hints**: Always include for parameters and return types
* **File endings**: ALWAYS ensure files end with a newline character

Function Organization
~~~~~~~~~~~~~~~~~~~~~

Organize functions and methods alphabetically within their scope:

.. code-block:: python

   # Public functions (alphabetical)
   def analyze_data():
       pass

   def build_report():
       pass

   # Private functions (alphabetical)
   def _calculate_metrics():
       pass

   def _validate_input():
       pass

Testing Requirements
~~~~~~~~~~~~~~~~~~~~

* **Coverage**: Maintain 100% test coverage of source code
* **Run tests**: Always run ``make test`` before committing
* **Check quality**: Run ``make pre-commit`` before commits

Changelog Management
--------------------

For User-Facing Changes
~~~~~~~~~~~~~~~~~~~~~~~~

Always add changelog entries for bug fixes, features, or breaking changes:

.. code-block:: bash

   # Add bug fix
   make changelog-add TYPE='fixed' MESSAGE='Memory leak in parser'

   # Add feature with references
   make changelog-add TYPE='added' MESSAGE='Dark mode support' PR=45

   # Add breaking change
   make changelog-add TYPE='changed' MESSAGE='API redesign' BREAKING=1

Skip Changelog For
~~~~~~~~~~~~~~~~~~

* Internal refactoring
* Test additions
* Documentation updates
* Code style changes

Release Workflow
----------------

Claude Code should NOT initiate releases without explicit user request. When asked to release:

.. code-block:: bash

   # Check for unreleased changes
   cat CHANGELOG.md | head -20

   # Run all quality checks
   make test
   make pre-commit

   # Only if explicitly requested by user
   make publish-to-pypi        # Patch release
   make publish-to-pypi-minor  # Minor release
   make publish-to-pypi-major  # Major release

Common Tasks
------------

When Asked to Fix a Bug
~~~~~~~~~~~~~~~~~~~~~~~~

1. Search for the issue:

   .. code-block:: bash

      bash scripts/safe-commit.sh 'chore: investigating issue'
      grep -r "error_pattern" src/ tests/

2. Fix the bug and add tests

3. Add changelog entry:

   .. code-block:: bash

      make changelog-add TYPE='fixed' MESSAGE='Description of fix'

4. Commit with safe workflow:

   .. code-block:: bash

      bash scripts/safe-commit.sh 'fix: clear description of the fix'

When Asked to Add a Feature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create todo list using TodoWrite tool
2. Implement feature with tests
3. Add changelog entry
4. Use safe commit workflow

Important Reminders
-------------------

Virtual Environment
~~~~~~~~~~~~~~~~~~~

* **Always** work within the virtual environment
* The safe commit script auto-activates if needed
* For manual commands: ``source .venv/bin/activate``

Git Workflow
~~~~~~~~~~~~

* **NEVER** use ``git commit --amend`` without user permission
* **ALWAYS** use safe commit workflow
* **ASK** before pushing to remote repositories
* **CHECK** git status before major operations

Documentation
~~~~~~~~~~~~~

* **UPDATE** docstrings for new/changed functions
* **ADD** RST documentation for new features
* **LINK** related documentation with cross-references

Quality Standards
~~~~~~~~~~~~~~~~~

Before ANY commit:

1. ✅ Tests pass: ``make test``
2. ✅ Coverage 100% (source code): ``make coverage``
3. ✅ Linting clean: ``make pre-commit``
4. ✅ Changelog updated (if user-facing)
5. ✅ Safe commit used

Error Recovery
--------------

If Commit Fails
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check what changed
   git status
   git diff

   # Stage changes
   git add -A

   # Retry with safe commit
   bash scripts/safe-commit.sh 'Your message'

If Pre-commit Modifies Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is expected! The safe commit workflow handles this:

.. code-block:: bash

   # The script will tell you:
   # "Pre-commit checks made changes"
   # Simply:
   git add -A
   bash scripts/safe-commit.sh 'Your message'  # Retry

Best Practices Summary
----------------------

**DO:**

* ✅ Use ``bash scripts/safe-commit.sh`` for all commits
* ✅ Add changelog entries for user-facing changes
* ✅ Run tests before committing
* ✅ Keep functions alphabetically sorted
* ✅ Include comprehensive commit messages

**DON'T:**

* ❌ Use ``git commit`` directly
* ❌ Use ``git commit --amend`` without permission
* ❌ Skip changelog for bug fixes/features
* ❌ Commit without running tests
* ❌ Leave files without trailing newlines

See Also
--------

* :doc:`developer` - General development guide
* :doc:`release` - Release management process
* `CLAUDE.md <https://github.com/hakonhagland/pylint-sort-functions/blob/main/CLAUDE.md>`_ - Project root file with additional Claude Code instructions
