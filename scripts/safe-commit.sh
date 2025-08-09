#!/bin/bash
# Safe commit wrapper that runs pre-commit checks first
# This prevents losing commit messages due to file modifications by hooks

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate .venv..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
    else
        echo -e "${RED}❌ Could not find virtual environment${NC}"
        echo "Please run: source .venv/bin/activate"
        exit 1
    fi
fi

# Parse arguments
COMMIT_MESSAGE=""
COMMIT_MESSAGE_FILE=""
AMEND_FLAG=""
NO_VERIFY_FLAG=""
FORCE_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        --file)
            COMMIT_MESSAGE_FILE="$2"
            shift 2
            ;;
        --amend)
            AMEND_FLAG="--amend"
            shift
            ;;
        --no-verify)
            NO_VERIFY_FLAG="--no-verify"
            shift
            ;;
        --force)
            FORCE_FLAG="1"
            shift
            ;;
        *)
            # If it starts with -, it's an unknown option
            if [[ $1 == -* ]]; then
                echo -e "${RED}❌ Unknown option: $1${NC}"
                echo "Usage: $0 [-m] 'commit message' [--file path] [--amend] [--no-verify]"
                exit 1
            else
                # Treat as commit message
                COMMIT_MESSAGE="$1"
                shift
            fi
            ;;
    esac
done

# Read message from file if specified
if [ -n "$COMMIT_MESSAGE_FILE" ]; then
    if [ -f "$COMMIT_MESSAGE_FILE" ]; then
        COMMIT_MESSAGE=$(cat "$COMMIT_MESSAGE_FILE")
    else
        echo -e "${RED}❌ Error: Commit message file not found: $COMMIT_MESSAGE_FILE${NC}"
        exit 1
    fi
fi

# Check if commit message is provided (unless amending)
if [ -z "$COMMIT_MESSAGE" ] && [ -z "$AMEND_FLAG" ]; then
    echo -e "${RED}❌ Commit message required${NC}"
    echo "Usage: $0 'commit message'"
    echo "   or: $0 -m 'commit message'"
    echo "   or: $0 --file path/to/message.txt"
    exit 1
fi

# Check for existing saved commit messages from previous validation failures
if [ -z "$COMMIT_MESSAGE_FILE" ] && [ -z "$FORCE_FLAG" ]; then
    # Use project-specific naming to avoid conflicts: pylint-sort-functions-commit-msg-*
    EXISTING_TEMP_FILES=$(find /tmp -maxdepth 1 -name "pylint-sort-functions-commit-msg-*" -type f 2>/dev/null)
    if [ -n "$EXISTING_TEMP_FILES" ]; then
        TEMP_COUNT=$(echo "$EXISTING_TEMP_FILES" | wc -l)
        echo -e "${YELLOW}⚠️  Found $TEMP_COUNT saved commit message(s) from previous validation failures:${NC}"

        echo "$EXISTING_TEMP_FILES" | head -3 | while read -r temp_file; do
            if [ -f "$temp_file" ] && [ -s "$temp_file" ]; then
                echo "📝 $temp_file"
                echo "   Preview: $(head -c 80 "$temp_file" | tr '\n' ' ')..."
                echo ""
            fi
        done

        if [ "$TEMP_COUNT" -gt 3 ]; then
            echo "   ... and $((TEMP_COUNT - 3)) more files"
            echo ""
        fi

        echo "Options:"
        echo "1. Use most recent saved message: bash scripts/safe-commit.sh --file '$(echo "$EXISTING_TEMP_FILES" | head -1)'"
        echo "2. Continue with new message (ignores saved messages)"
        echo "3. Clean up old messages: rm /tmp/pylint-sort-functions-commit-msg-*"
        echo ""
        echo -e "${YELLOW}💡 Tip: Add --force flag to skip this check: bash scripts/safe-commit.sh --force 'message'${NC}"
        echo ""
        exit 1
    fi
fi

# Check for staged and unstaged changes
STAGED_FILES=$(git diff --cached --name-only)
UNSTAGED_FILES=$(git diff --name-only)

if [ -z "$STAGED_FILES" ] && [ -z "$UNSTAGED_FILES" ]; then
    echo -e "${RED}❌ No changes to commit${NC}"
    echo "Use 'git add <file>' to stage changes first"
    exit 1
fi

if [ -z "$STAGED_FILES" ] && [ -n "$UNSTAGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No files are staged for commit${NC}"
    echo "Modified files found:"
    git status --porcelain
    echo ""
    echo "Options:"
    echo "1. Stage all files: git add -A && bash scripts/safe-commit.sh -m \"$COMMIT_MESSAGE\""
    echo "2. Stage specific files: git add <file1> <file2> && bash scripts/safe-commit.sh -m \"$COMMIT_MESSAGE\""
    echo "3. Review changes first: git diff"
    exit 1
fi

if [ -n "$UNSTAGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  Warning: Unstaged files detected${NC}"
    echo "These files have changes but are not staged:"
    echo "$UNSTAGED_FILES" | sed 's/^/  /'
    echo ""
    echo "Pre-commit will temporarily stash these files during checks."
    echo "Consider staging them first if they should be included in this commit."
    echo ""
fi

# Skip pre-commit if --no-verify is specified
if [ -z "$NO_VERIFY_FLAG" ]; then
    echo -e "${GREEN}🔍 Running pre-commit checks...${NC}"

    # Run pre-commit on all staged files with auto-retry for formatting
    MAX_RETRIES=3
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if pre-commit run --files $(git diff --cached --name-only); then
            # Success - all checks passed
            break
        fi

        # Check if any files were modified by the hooks
        MODIFIED_FILES=$(git status --porcelain)
        if [ -z "$MODIFIED_FILES" ]; then
            # Save commit message to temporary file to avoid losing it (only if not already using --file)
            if [ -z "$COMMIT_MESSAGE_FILE" ]; then
                TEMP_MSG_FILE=$(mktemp /tmp/pylint-sort-functions-commit-msg-XXXXXX)
                echo "$COMMIT_MESSAGE" > "$TEMP_MSG_FILE"
            else
                # Already using a temp file from --file argument
                TEMP_MSG_FILE="$COMMIT_MESSAGE_FILE"
            fi

            echo -e "${RED}❌ Pre-commit validation failed${NC}"
            echo "This indicates a code quality issue that requires manual fixing."
            echo "No files were modified by the hooks, so retrying won't help."
            echo ""
            echo "Common causes:"
            echo "• Syntax errors in code or documentation"
            echo "• Type checking failures"
            echo "• Linting violations that require manual fixes"
            echo ""
            echo "To fix:"
            echo "1. Review the error messages above"
            echo "2. Fix the reported issues manually"
            echo "3. Stage your fixes: git add <fixed-files>"
            echo "4. Re-run with saved message: bash scripts/safe-commit.sh --file '$TEMP_MSG_FILE'"
            echo ""
            echo -e "${YELLOW}💾 Your commit message has been saved to: $TEMP_MSG_FILE${NC}"
            echo "The temporary file will be automatically cleaned up after successful commit."
            exit 1
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}⚠️  Pre-commit hooks modified files (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"

        # Auto-stage modified files and retry
        echo "Staging formatting changes and retrying..."
        git add -A

        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            # Save commit message to temporary file to avoid losing it (only if not already using --file)
            if [ -z "$COMMIT_MESSAGE_FILE" ]; then
                TEMP_MSG_FILE=$(mktemp /tmp/pylint-sort-functions-commit-msg-XXXXXX)
                echo "$COMMIT_MESSAGE" > "$TEMP_MSG_FILE"
            else
                # Already using a temp file from --file argument
                TEMP_MSG_FILE="$COMMIT_MESSAGE_FILE"
            fi

            echo -e "${RED}❌ Maximum retries reached${NC}"
            echo "Pre-commit hooks are still making formatting changes after $MAX_RETRIES attempts."
            echo "This suggests an unstable formatting configuration."
            echo ""
            echo -e "${YELLOW}💾 Your commit message has been saved to: $TEMP_MSG_FILE${NC}"
            echo ""
            echo "To continue manually:"
            echo "1. Review changes: git diff --cached"
            echo "2. Check for conflicting formatter configurations"
            echo "3. Fix issues manually, stage fixes: git add <fixed-files>"
            echo "4. Re-run with saved message: bash scripts/safe-commit.sh --file '$TEMP_MSG_FILE'"
            echo ""
            echo "The temporary file will be automatically cleaned up after successful commit."
            exit 1
        fi
    done

    echo -e "${GREEN}✅ Pre-commit checks passed${NC}"
fi

# Perform the commit
echo -e "${GREEN}📝 Creating commit...${NC}"

if [ -n "$AMEND_FLAG" ]; then
    if [ -n "$COMMIT_MESSAGE" ]; then
        git commit --amend -m "$COMMIT_MESSAGE" $NO_VERIFY_FLAG
    else
        git commit --amend $NO_VERIFY_FLAG
    fi
else
    git commit -m "$COMMIT_MESSAGE" $NO_VERIFY_FLAG
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Commit successful!${NC}"

    # Clean up temporary message files if they exist
    if [ -n "$COMMIT_MESSAGE_FILE" ] && [[ "$COMMIT_MESSAGE_FILE" == /tmp/pylint-sort-functions-commit-msg-* ]]; then
        rm -f "$COMMIT_MESSAGE_FILE"
        echo "🧹 Cleaned up temporary message file"
    fi
else
    echo -e "${RED}❌ Commit failed${NC}"
    exit 1
fi
