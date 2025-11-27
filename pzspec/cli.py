#!/usr/bin/env python3
"""
Command-line interface for PZSpec.

Allows running tests from any directory after installing PZSpec via pip.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List

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


def find_zig_sources(project_root: Path) -> list:
    """Find Zig source files in the project."""
    src_dir = project_root / "src"
    if src_dir.exists():
        return list(src_dir.glob("**/*.zig"))
    return list(project_root.glob("*.zig"))


def run_tests(
    project_root: Optional[Path] = None,
    verbose: bool = True,
    file_line: Optional[str] = None,
    coverage: bool = False,
    coverage_html: Optional[str] = None,
    filter_pattern: Optional[str] = None,
    filter_regex: bool = False,
    update_snapshots: bool = False,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> bool:
    """
    Run tests in a PZSpec project.

    Args:
        project_root: Root directory of the project. If None, searches from current directory.
        verbose: Whether to show verbose output.
        file_line: Optional "file.py:line" to run a specific test.
        coverage: Whether to collect code coverage.
        coverage_html: Path to generate HTML coverage report.
        filter_pattern: Optional pattern to filter tests by name (like pytest -k).
        filter_regex: Whether to treat filter_pattern as a regex.
        update_snapshots: Whether to update snapshots instead of comparing.
        include_tags: Only run tests with at least one of these tags.
        exclude_tags: Exclude tests with any of these tags.

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

    # Initialize snapshot manager
    from .snapshot import init_snapshot_manager, set_update_snapshots
    init_snapshot_manager(project_root)
    set_update_snapshots(update_snapshots)

    # Coverage instrumentation
    coverage_builder = None
    collector = None
    coverage_lib_path = None

    if coverage:
        from .coverage import CoverageBuilder, CoverageCollector, CoverageReport

        # Find and instrument Zig sources
        zig_sources = find_zig_sources(project_root)
        if not zig_sources:
            print("Warning: No Zig source files found for coverage", file=sys.stderr)
        else:
            coverage_builder = CoverageBuilder(project_root)
            collector = CoverageCollector()

            if verbose:
                print(f"Instrumenting {len(zig_sources)} Zig file(s) for coverage...")

            results = coverage_builder.instrument()
            for result in results:
                collector.register_instrumentation(result)

            if verbose:
                total_points = sum(r.counter_count for r in results)
                print(f"  {total_points} coverage points instrumented")

            # Build the instrumented library
            if verbose:
                print("Building instrumented library...")

            coverage_lib_path = coverage_builder.build()
            if coverage_lib_path:
                # Set environment variable so ZigLibrary uses our instrumented build
                os.environ['PZSPEC_COVERAGE_LIB'] = str(coverage_lib_path)
                if verbose:
                    print(f"  Built: {coverage_lib_path}")
                    print()
            else:
                print("Warning: Failed to build coverage library", file=sys.stderr)
                coverage = False

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
    success = runner.run(
        verbose=verbose,
        file_line=file_line,
        filter_pattern=filter_pattern,
        filter_regex=filter_regex,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
    )

    # Collect and report coverage
    if coverage and collector and coverage_lib_path:
        try:
            import ctypes

            # Load the coverage library directly
            coverage_lib = ctypes.CDLL(str(coverage_lib_path))
            collector.set_library(coverage_lib)
            collector.collect()

            from .coverage import CoverageReport
            report = CoverageReport(collector)

            if coverage_html:
                report.generate_html(coverage_html)
            else:
                report.print_summary()

        except Exception as e:
            print(f"Warning: Could not collect coverage data: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        # Cleanup instrumented files
        if coverage_builder:
            coverage_builder.cleanup()

        # Clear the environment variable
        if 'PZSPEC_COVERAGE_LIB' in os.environ:
            del os.environ['PZSPEC_COVERAGE_LIB']

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

  # Filter tests by name pattern
  pzspec -k "Vec2"              # tests containing "Vec2"
  pzspec -k "add"               # tests containing "add"
  pzspec -k "Vec2 and add"      # tests matching both
  pzspec -k "not slow"          # exclude tests containing "slow"

  # Filter tests using regex
  pzspec -k "Vec2.*add" --regex

  # Run tests by tag
  pzspec --tags unit              # run only unit tests
  pzspec --tags "slow,integration" # run tests with either tag
  pzspec --exclude-tags slow      # skip slow tests
  pzspec --tags unit --exclude-tags flaky  # combine filters

  # Run tests with coverage
  pzspec --coverage

  # Generate HTML coverage report
  pzspec --coverage --html coverage/

  # Update all snapshots
  pzspec --update-snapshots

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

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Collect code coverage for Zig source files",
    )

    parser.add_argument(
        "--html",
        type=str,
        metavar="DIR",
        help="Generate HTML coverage report in the specified directory",
    )

    parser.add_argument(
        "-k",
        type=str,
        metavar="PATTERN",
        help="Filter tests by name pattern. Supports boolean operators: "
             "'Vec2 and add', 'Vec2 or sub', 'not slow'",
    )

    parser.add_argument(
        "--regex",
        action="store_true",
        help="Treat -k pattern as a regular expression",
    )

    parser.add_argument(
        "--update-snapshots",
        action="store_true",
        help="Update snapshots instead of comparing against them",
    )

    parser.add_argument(
        "--tags",
        type=str,
        metavar="TAGS",
        help="Only run tests with these tags (comma-separated)",
    )

    parser.add_argument(
        "--exclude-tags",
        type=str,
        metavar="TAGS",
        help="Exclude tests with these tags (comma-separated)",
    )

    args = parser.parse_args()

    verbose = args.verbose and not args.quiet
    project_root = Path(args.project_root) if args.project_root else None

    # --html implies --coverage
    coverage = args.coverage or args.html is not None

    # Parse tag filters
    include_tags = None
    if args.tags:
        include_tags = [t.strip() for t in args.tags.split(',') if t.strip()]

    exclude_tags = None
    if args.exclude_tags:
        exclude_tags = [t.strip() for t in args.exclude_tags.split(',') if t.strip()]

    success = run_tests(
        project_root=project_root,
        verbose=verbose,
        file_line=args.file_line,
        coverage=coverage,
        coverage_html=args.html,
        filter_pattern=args.k,
        filter_regex=args.regex,
        update_snapshots=args.update_snapshots,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
