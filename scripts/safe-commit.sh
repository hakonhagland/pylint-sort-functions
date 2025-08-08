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
AMEND_FLAG=""
NO_VERIFY_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--message)
            COMMIT_MESSAGE="$2"
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
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Usage: $0 -m 'commit message' [--amend] [--no-verify]"
            exit 1
            ;;
    esac
done

# Check if commit message is provided (unless amending)
if [ -z "$COMMIT_MESSAGE" ] && [ -z "$AMEND_FLAG" ]; then
    echo -e "${RED}❌ Commit message required${NC}"
    echo "Usage: $0 -m 'commit message'"
    exit 1
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
