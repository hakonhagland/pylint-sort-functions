#!/bin/bash
# Wrapper for make commit that handles multi-line messages properly

if [ $# -eq 0 ]; then
    echo "Usage: $0 'Your commit message'"
    echo "Supports multi-line messages with quotes and special characters"
    exit 1
fi

# Write message to temp file
echo "$1" > .commit_msg_tmp

# Run safe commit with file
bash scripts/safe-commit.sh --file .commit_msg_tmp

# Clean up
rm -f .commit_msg_tmp
