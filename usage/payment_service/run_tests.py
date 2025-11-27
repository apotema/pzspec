#!/usr/bin/env python3
"""
Run tests for the Payment Service example project.

This demonstrates using PZSpec's mocking capabilities to test
business logic in isolation by mocking external service calls.
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
