#!/usr/bin/env python3
"""Run the auto_export_demo tests."""

import sys
from pathlib import Path

# Add pzspec to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pzspec import TestRunner, set_runner

# Create and set runner
runner = TestRunner()
set_runner(runner)

# Import test file (this registers the tests)
import test_auto_export

# Run tests
success = runner.run(verbose=True)
sys.exit(0 if success else 1)
