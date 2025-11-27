#!/usr/bin/env python3
"""
Main test runner script.

Usage:
    python run_tests.py
    python run_tests.py --verbose
    python run_tests.py tests/test_math.py
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pzspec import TestRunner, set_runner


def main():
    parser = argparse.ArgumentParser(description="Run PZSpec tests for Zig code")
    parser.add_argument(
        "test_files",
        nargs="*",
        help="Specific test files to run from pzspec/ directory (default: run all tests)",
    )
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
    # Note: We need to distinguish between the framework package and test directory
    # Tests are in a separate pzspec/ directory at project root
    test_pzspec_dir = project_root / "pzspec"
    
    if args.test_files:
        # Import specific test files
        for test_file in args.test_files:
            # If path doesn't include pzspec/, prepend it
            if not test_file.startswith("pzspec/"):
                test_path = test_pzspec_dir / test_file
            else:
                test_path = project_root / test_file
            
            if not test_path.exists():
                print(f"Error: Test file not found: {test_path}", file=sys.stderr)
                sys.exit(1)
            
            # Import the test module
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_module", test_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
    else:
        # Import all tests from pzspec directory (following RSpec convention)
        if test_pzspec_dir.exists():
            import importlib
            import pkgutil
            
            # Filter out framework files - only import test files
            framework_files = {"__init__", "dsl", "test_runner", "zig_ffi"}
            for _, name, _ in pkgutil.iter_modules([str(test_pzspec_dir)]):
                if name not in framework_files and name.startswith("test_"):
                    importlib.import_module(f"pzspec.{name}")
        else:
            print("Warning: No pzspec directory found", file=sys.stderr)
    
    # Run tests
    success = runner.run(verbose=verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

