#!/usr/bin/env python3
"""
Run tests for the ECS Entities example project.

This demonstrates using PZSpec's Sentinel values for FFI patterns
where 0 is a valid value (like entity IDs).
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
