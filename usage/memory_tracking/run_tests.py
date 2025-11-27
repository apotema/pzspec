#!/usr/bin/env python3
"""
Run tests for the Memory Tracking example project.

This demonstrates using PZSpec's memory leak detection to find
memory leaks in Zig code via the tracking allocator.
"""

import sys
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pzspec.cli import run_tests


if __name__ == "__main__":
    success = run_tests(project_root=Path(__file__).parent)
    sys.exit(0 if success else 1)
