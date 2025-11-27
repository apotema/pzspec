#!/usr/bin/env python3
"""
Test runner for Vector Math library tests.

Usage:
    python run_tests.py
    python run_tests.py --verbose
"""

import sys
import os
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pzspec import TestRunner, set_runner


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Vector Math library tests")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet output (overrides verbose)",
    )
    
    args = parser.parse_args()
    verbose = args.verbose and not args.quiet
    
    # Create test runner
    runner = TestRunner()
    set_runner(runner)
    
    # Import test files from pzspec directory (following RSpec convention)
    project_dir = Path(__file__).parent
    pzspec_dir = project_dir / "pzspec"
    
    # Add project directory to Python path
    sys.path.insert(0, str(project_dir))
    
    if pzspec_dir.exists():
        import importlib.util
        import pkgutil
        
        # Import all test modules from pzspec directory
        for _, name, _ in pkgutil.iter_modules([str(pzspec_dir)]):
            if name != "__init__" and name.startswith("test_"):
                # Import test file directly (not as package)
                test_file = pzspec_dir / f"{name}.py"
                spec = importlib.util.spec_from_file_location(f"pzspec_{name}", test_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
    else:
        print("Error: pzspec directory not found", file=sys.stderr)
        sys.exit(1)
    
    # Run tests
    success = runner.run(verbose=verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

