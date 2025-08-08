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

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}⚠️  Pre-commit checks made changes (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"

        # Check if only formatting files were modified
        MODIFIED_FILES=$(git status --porcelain)
        if [ -z "$MODIFIED_FILES" ]; then
            echo -e "${RED}❌ No files were modified but pre-commit failed${NC}"
            echo "This indicates a code quality issue that requires manual fixing."
            exit 1
        fi

        # Auto-stage modified files and retry
        echo "Staging modified files and retrying..."
        git add -A

        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}❌ Maximum retries reached${NC}"
            echo "Pre-commit hooks are still making changes after $MAX_RETRIES attempts."
            echo "This suggests a code quality issue that needs manual attention."
            echo ""
            echo "To continue manually:"
            echo "1. Review changes: git diff --cached"
            echo "2. Fix any code quality issues"
            echo "3. Re-run: bash scripts/safe-commit.sh -m \"$COMMIT_MESSAGE\""
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
else
    echo -e "${RED}❌ Commit failed${NC}"
    exit 1
fi
