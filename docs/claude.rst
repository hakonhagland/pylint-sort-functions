Claude Code Guidelines
======================

This document provides specific guidance for Claude Code (claude.ai/code) when working with this repository.

Overview
--------

Claude Code is Anthropic's AI coding assistant that can directly read, write, and execute code in your repository. This document contains important guidelines and workflows specifically designed for Claude Code sessions to ensure consistent, high-quality contributions.

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

**Always use for commits:**

.. code-block:: bash

   # For simple single-line messages
   make commit MSG='Your commit message'

   # For complex messages, use the script directly
   bash scripts/safe-commit.sh -m "feat: comprehensive feature

   - Detailed bullet point
   - Another detail

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"

**Never use:**

.. code-block:: bash

   # ❌ AVOID: Direct git commit
   git commit -m "message"

   # ❌ AVOID: Git commit --amend without permission
   git commit --amend

How Safe Commit Works
~~~~~~~~~~~~~~~~~~~~~

The safe commit workflow:

1. Automatically activates virtual environment
2. Runs pre-commit checks on staged files BEFORE committing
3. Stops if files are modified, preserving your message
4. Only commits if all checks pass cleanly

This ensures comprehensive commit messages are always preserved.

Development Guidelines
----------------------

Code Style
~~~~~~~~~~

Claude Code should follow these Python style guidelines:

* **Line length**: 88 characters (Black compatible)
* **String formatting**: Use f-strings
* **Docstrings**: reStructuredText format for all public APIs
* **Type hints**: Always include for parameters and return types
* **Import order**: standard library → third-party → local (alphabetically sorted)
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

* **Coverage**: Maintain 100% test coverage
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

      make commit MSG='chore: investigating issue'
      grep -r "error_pattern" src/ tests/

2. Fix the bug and add tests

3. Add changelog entry:

   .. code-block:: bash

      make changelog-add TYPE='fixed' MESSAGE='Description of fix'

4. Commit with safe workflow:

   .. code-block:: bash

      make commit MSG='fix: clear description of the fix'

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
2. ✅ Coverage 100%: ``make coverage``
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
   make commit MSG='Your message'

If Pre-commit Modifies Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is expected! The safe commit workflow handles this:

.. code-block:: bash

   # The script will tell you:
   # "Pre-commit checks made changes"
   # Simply:
   git add -A
   make commit MSG='Your message'  # Retry

Best Practices Summary
----------------------

**DO:**

* ✅ Use ``make commit`` for all commits
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
