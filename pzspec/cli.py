#!/usr/bin/env python3
"""
Command-line interface for PZSpec.

Allows running tests from any directory after installing PZSpec via pip.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .test_runner import TestRunner
from .dsl import set_runner


def find_pzspec_dir(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the pzspec directory by walking up from start_path.
    
    Looks for a 'pzspec/' directory containing test files.
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = Path(start_path).resolve()
    
    # Check current directory and all parents
    while current != current.parent:
        pzspec_dir = current / "pzspec"
        if pzspec_dir.exists() and pzspec_dir.is_dir():
            # Verify it has test files
            test_files = list(pzspec_dir.glob("test_*.py"))
            if test_files:
                return current
        
        current = current.parent
    
    return None


def run_tests(project_root: Optional[Path] = None, verbose: bool = True,
              file_line: Optional[str] = None) -> bool:
    """
    Run tests in a PZSpec project.

    Args:
        project_root: Root directory of the project. If None, searches from current directory.
        verbose: Whether to show verbose output.
        file_line: Optional "file.py:line" to run a specific test.

    Returns:
        True if all tests passed, False otherwise.
    """
    # If file_line is provided, extract project root from it
    if file_line and project_root is None:
        file_path = file_line.rsplit(':', 1)[0] if ':' in file_line else file_line
        file_path = Path(file_path).resolve()
        if file_path.exists():
            project_root = find_pzspec_dir(file_path.parent)

    if project_root is None:
        project_root = find_pzspec_dir()
        if project_root is None:
            print("Error: No PZSpec project found.", file=sys.stderr)
            print("  Looked for 'pzspec/' directory with test_*.py files", file=sys.stderr)
            print("  Run this command from your project root or specify --project-root", file=sys.stderr)
            return False

    project_root = Path(project_root).resolve()
    pzspec_dir = project_root / "pzspec"

    if not pzspec_dir.exists():
        print(f"Error: pzspec directory not found in {project_root}", file=sys.stderr)
        return False

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    # Create test runner
    runner = TestRunner()
    set_runner(runner)

    # Import test files
    import importlib.util
    import pkgutil

    # If file_line specifies a specific file, only load that file
    if file_line:
        file_path = file_line.rsplit(':', 1)[0] if ':' in file_line else file_line
        file_path = Path(file_path).resolve()
        if file_path.exists() and file_path.suffix == '.py':
            spec = importlib.util.spec_from_file_location(f"pzspec_{file_path.stem}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            print(f"Error: Test file not found: {file_path}", file=sys.stderr)
            return False
    else:
        # Load all test files
        test_count = 0
        for _, name, _ in pkgutil.iter_modules([str(pzspec_dir)]):
            if name != "__init__" and name.startswith("test_"):
                test_file = pzspec_dir / f"{name}.py"
                spec = importlib.util.spec_from_file_location(f"pzspec_{name}", test_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                test_count += 1

        if test_count == 0:
            print(f"Warning: No test files found in {pzspec_dir}", file=sys.stderr)
            return False

    # Run tests
    success = runner.run(verbose=verbose, file_line=file_line)
    return success


def main():
    """Main entry point for pzspec command."""
    parser = argparse.ArgumentParser(
        description="PZSpec - Python DSL for Testing Zig Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests in current directory
  pzspec

  # Run a specific test by line number
  pzspec ./pzspec/test_vectors.py:117

  # Run all tests in a describe block
  pzspec ./pzspec/test_vectors.py:114

  # Run tests in specific project
  pzspec --project-root /path/to/project

  # Quiet mode
  pzspec --quiet
        """
    )

    parser.add_argument(
        "file_line",
        nargs="?",
        type=str,
        help="Run specific test: file.py:line (e.g., ./pzspec/test_vectors.py:117)",
    )

    parser.add_argument(
        "-p", "--project-root",
        type=str,
        help="Root directory of the PZSpec project (default: search from current directory)",
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
    project_root = Path(args.project_root) if args.project_root else None

    success = run_tests(project_root=project_root, verbose=verbose, file_line=args.file_line)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

