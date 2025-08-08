#!/usr/bin/env python3
"""Write commit message to file, handling multi-line strings properly."""

import sys

if len(sys.argv) != 3:
    print("Usage: python write-commit-msg.py 'message' output_file")
    sys.exit(1)

message = sys.argv[1]
output_file = sys.argv[2]

with open(output_file, "w") as f:
    f.write(message)
