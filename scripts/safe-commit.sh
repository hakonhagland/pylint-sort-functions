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

    # Run pre-commit on all staged files
    if ! pre-commit run --files $(git diff --cached --name-only); then
        echo -e "${YELLOW}⚠️  Pre-commit checks made changes${NC}"
        echo "Files were modified by pre-commit hooks."
        echo ""
        echo "Options:"
        echo "1. Review changes with: git diff"
        echo "2. Stage changes with: git add -A"
        echo "3. Re-run this script to commit"
        exit 1
    fi

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
