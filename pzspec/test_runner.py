"""
Test runner for executing test suites and collecting results.

Supports nested describe blocks with before/after hooks like RSpec.
"""

import sys
import time
import inspect
import os
import re
from typing import Callable, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class TestResult:
    """Result of a single test execution."""
    name: str
    passed: bool
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class TestCase:
    """A single test case."""
    name: str
    func: Callable
    source_file: Optional[str] = None
    source_line: Optional[int] = None


class Context:
    """
    A test context (describe block) that can be nested.

    Supports:
    - Nested contexts with hierarchical names
    - before(:each) / after(:each) hooks - run for each test
    - before(:all) / after(:all) hooks - run once per context
    """

    def __init__(self, name: str, parent: Optional['Context'] = None,
                 source_file: Optional[str] = None, source_line: Optional[int] = None):
        self.name = name
        self.parent = parent
        self.children: List['Context'] = []
        self.tests: List[TestCase] = []
        self.source_file = source_file
        self.source_line = source_line

        # Hooks
        self.before_all_hooks: List[Callable] = []
        self.after_all_hooks: List[Callable] = []
        self.before_each_hooks: List[Callable] = []
        self.after_each_hooks: List[Callable] = []

    @property
    def full_name(self) -> str:
        """Get the full hierarchical name of this context."""
        if self.parent and self.parent.name:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    @property
    def depth(self) -> int:
        """Get the nesting depth of this context."""
        if self.parent is None:
            return 0
        return self.parent.depth + 1

    def get_before_each_hooks(self) -> List[Callable]:
        """Get all before_each hooks including from ancestors (parent first)."""
        hooks = []
        if self.parent:
            hooks.extend(self.parent.get_before_each_hooks())
        hooks.extend(self.before_each_hooks)
        return hooks

    def get_after_each_hooks(self) -> List[Callable]:
        """Get all after_each hooks including from ancestors (child first)."""
        hooks = list(self.after_each_hooks)
        if self.parent:
            hooks.extend(self.parent.get_after_each_hooks())
        return hooks


# Legacy alias for compatibility
TestSuite = Context


class TestRunner:
    """
    Main test runner that collects and executes tests.

    Supports nested describe blocks with RSpec-style hooks:
    - before(:all) / before_all - runs once before all tests in context
    - after(:all) / after_all - runs once after all tests in context
    - before(:each) / before - runs before each test
    - after(:each) / after - runs after each test
    """

    def __init__(self):
        self.root = Context(name="", parent=None)
        self.current_context: Context = self.root
        self.results: List[TestResult] = []

        # Legacy compatibility
        self.suites: List[Context] = []
        self.current_suite: Optional[Context] = None

    @contextmanager
    def describe(self, name: str):
        """
        Context manager for creating a nested test context.

        Usage:
            with runner.describe("Math Operations"):
                with runner.describe("Addition"):
                    runner.add_test("should add", lambda: ...)
        """
        # Get caller's source location (skip dsl.py and contextlib.py wrappers)
        frame = inspect.currentframe()
        source_file = None
        source_line = None
        if frame and frame.f_back:
            caller = frame.f_back
            # Walk up the stack to find the actual test file
            while caller:
                filename = caller.f_code.co_filename
                if not (filename.endswith('dsl.py') or
                        filename.endswith('contextlib.py') or
                        filename.endswith('test_runner.py')):
                    break
                caller = caller.f_back
            if caller:
                source_file = caller.f_code.co_filename
                source_line = caller.f_lineno

        context = Context(name=name, parent=self.current_context,
                         source_file=source_file, source_line=source_line)
        self.current_context.children.append(context)

        old_context = self.current_context
        self.current_context = context

        # Legacy compatibility
        old_suite = self.current_suite
        self.current_suite = context

        try:
            yield context
        finally:
            self.current_context = old_context
            self.current_suite = old_suite

    def add_test(self, name: str, func: Callable):
        """Add a test to the current context."""
        # Get caller's source location
        frame = inspect.currentframe()
        source_file = None
        source_line = None
        if frame and frame.f_back:
            caller = frame.f_back
            # Walk up the stack to find the actual test file (skip dsl.py wrapper)
            while caller and caller.f_code.co_filename.endswith('dsl.py'):
                caller = caller.f_back
            if caller:
                source_file = caller.f_code.co_filename
                source_line = caller.f_lineno

        self.current_context.tests.append(TestCase(
            name=name, func=func,
            source_file=source_file, source_line=source_line
        ))

    def before_all(self, func: Callable):
        """Add a before(:all) hook to run once before all tests in context."""
        self.current_context.before_all_hooks.append(func)
        return func

    def after_all(self, func: Callable):
        """Add an after(:all) hook to run once after all tests in context."""
        self.current_context.after_all_hooks.append(func)
        return func

    def before_each(self, func: Callable):
        """Add a before(:each) hook to run before each test."""
        self.current_context.before_each_hooks.append(func)
        return func

    def after_each(self, func: Callable):
        """Add an after(:each) hook to run after each test."""
        self.current_context.after_each_hooks.append(func)
        return func

    # Aliases
    def before(self, func: Callable):
        """Alias for before_each."""
        return self.before_each(func)

    def after(self, func: Callable):
        """Alias for after_each."""
        return self.after_each(func)

    def _count_tests(self, context: Context, filter_set: Optional[set] = None) -> int:
        """Count total tests in a context and its children."""
        if filter_set is not None:
            count = sum(1 for t in context.tests if id(t) in filter_set)
        else:
            count = len(context.tests)
        for child in context.children:
            count += self._count_tests(child, filter_set)
        return count

    def _normalize_path(self, path: str) -> str:
        """Normalize a file path for comparison."""
        return os.path.normpath(os.path.abspath(path))

    def _find_tests_at_line(self, target_file: str, target_line: int) -> set:
        """
        Find tests that match a file:line specification.

        Returns a set of test IDs (using id()) that should be run.
        The matching logic:
        1. If line points to a specific test (or within a test), run just that test
        2. If line points to a describe block, run all tests in that block
        3. If line is within a describe block but before any test, run all tests in that block
        """
        target_file = self._normalize_path(target_file)
        matching_tests = set()

        # Collect all tests with their line info
        all_tests = []

        def collect_tests(context: Context):
            context_file = self._normalize_path(context.source_file) if context.source_file else None

            # Check if this context's describe line matches exactly
            if context_file == target_file and context.source_line == target_line:
                # Line points to describe block - run all tests in it
                self._add_all_tests_in_context(context, matching_tests)
                return True

            for test in context.tests:
                test_file = self._normalize_path(test.source_file) if test.source_file else None
                if test_file == target_file:
                    all_tests.append((test.source_line, test, context))

            for child in context.children:
                if collect_tests(child):
                    return True  # Found exact describe match

            return False

        if collect_tests(self.root):
            return matching_tests

        # Sort tests by line number
        all_tests.sort(key=lambda x: x[0] if x[0] else 0)

        # Find the test that contains the target line
        # A test "contains" a line if the line is >= test's start line and < next test's start line
        best_test = None
        for i, (line, test, context) in enumerate(all_tests):
            if line is None:
                continue
            if line <= target_line:
                # Check if this is the right test (target_line is before the next test)
                if i + 1 < len(all_tests):
                    next_line = all_tests[i + 1][0]
                    if next_line and target_line < next_line:
                        best_test = test
                        break
                else:
                    # Last test - target line is after this test's start
                    best_test = test
                    break
            elif line > target_line and best_test is None:
                # Target line is before the first test in this file
                break

        if best_test:
            matching_tests.add(id(best_test))
            return matching_tests

        # If no test match, find the innermost context containing the line
        innermost = self._find_innermost_context_at_line(target_file, target_line)
        if innermost:
            self._add_all_tests_in_context(innermost, matching_tests)

        return matching_tests

    def _find_innermost_context_at_line(self, target_file: str, target_line: int) -> Optional[Context]:
        """Find the innermost context that contains the target line."""
        target_file = self._normalize_path(target_file)
        best_match = None
        best_line = -1

        def search(context: Context):
            nonlocal best_match, best_line
            context_file = self._normalize_path(context.source_file) if context.source_file else None

            if (context_file == target_file and
                context.source_line is not None and
                context.source_line <= target_line and
                context.source_line > best_line):
                best_match = context
                best_line = context.source_line

            for child in context.children:
                search(child)

        search(self.root)
        return best_match

    def _add_all_tests_in_context(self, context: Context, test_set: set):
        """Add all tests in a context and its children to the set."""
        for test in context.tests:
            test_set.add(id(test))
        for child in context.children:
            self._add_all_tests_in_context(child, test_set)

    def _run_context(self, context: Context, verbose: bool, indent: int = 0,
                     filter_set: Optional[set] = None) -> tuple:
        """
        Run all tests in a context and its children.

        Args:
            filter_set: If provided, only run tests whose id() is in this set

        Returns:
            (passed_count, failed_count)
        """
        passed = 0
        failed = 0
        prefix = "  " * indent

        # Check if this context has any tests to run (considering filter)
        has_tests_to_run = self._count_tests(context, filter_set) > 0
        if not has_tests_to_run:
            return passed, failed

        # Print context name if it has one
        if context.name and verbose:
            print(f"{prefix}{context.name}")
            print(f"{prefix}{'-' * (60 - len(prefix))}")

        # Run before_all hooks
        for hook in context.before_all_hooks:
            try:
                hook()
            except Exception as e:
                if verbose:
                    print(f"{prefix}  BEFORE_ALL FAILED: {e}")
                return passed, failed

        # Run tests in this context
        before_hooks = context.get_before_each_hooks()
        after_hooks = context.get_after_each_hooks()

        # Filter tests if filter_set is provided
        tests_to_run = context.tests
        if filter_set is not None:
            tests_to_run = [t for t in context.tests if id(t) in filter_set]

        for test in tests_to_run:
            start_time = time.time()
            error_msg = None
            test_passed = True

            # Set snapshot context for this test
            try:
                from .snapshot import get_snapshot_manager
                snapshot_mgr = get_snapshot_manager()
                test_file = test.source_file or "unknown"
                full_test_name = f"{context.full_name}::{test.name}" if context.full_name else test.name
                snapshot_mgr.set_current_test(test_file, full_test_name)
            except Exception:
                pass  # Snapshot manager not initialized, that's ok

            try:
                # Run before_each hooks (parent to child order)
                for hook in before_hooks:
                    hook()

                # Run the test
                test.func()

            except Exception as e:
                test_passed = False
                error_msg = str(e)

            finally:
                # Run after_each hooks (child to parent order)
                for hook in after_hooks:
                    try:
                        hook()
                    except Exception as e:
                        if test_passed:
                            test_passed = False
                            error_msg = f"after_each failed: {e}"

            duration = time.time() - start_time
            full_name = f"{context.full_name}::{test.name}" if context.full_name else test.name

            result = TestResult(
                name=full_name,
                passed=test_passed,
                error=error_msg,
                duration=duration
            )
            self.results.append(result)

            if test_passed:
                passed += 1
                if verbose:
                    print(f"{prefix}  ✓ {test.name} ({duration*1000:.2f}ms)")
            else:
                failed += 1
                if verbose:
                    print(f"{prefix}  ✗ {test.name} ({duration*1000:.2f}ms)")
                    print(f"{prefix}    Error: {error_msg}")

        # Run child contexts
        for child in context.children:
            child_passed, child_failed = self._run_context(
                child, verbose, indent + 1, filter_set
            )
            passed += child_passed
            failed += child_failed

        # Run after_all hooks
        for hook in context.after_all_hooks:
            try:
                hook()
            except Exception as e:
                if verbose:
                    print(f"{prefix}  AFTER_ALL FAILED: {e}")

        if context.name and verbose:
            print()

        return passed, failed

    def run(
        self,
        verbose: bool = True,
        file_line: Optional[str] = None,
        filter_pattern: Optional[str] = None,
        filter_regex: bool = False,
    ) -> bool:
        """
        Run all collected tests, optionally filtered by file:line or name pattern.

        Args:
            verbose: Whether to print verbose output
            file_line: Optional "file.py:line" string to filter tests
            filter_pattern: Optional pattern to filter tests by name (like pytest -k)
            filter_regex: Whether to treat filter_pattern as a regex

        Returns:
            True if all tests passed, False otherwise
        """
        filter_set = None

        # Apply name pattern filter first
        if filter_pattern:
            filter_set = self._filter_tests_by_pattern(filter_pattern, filter_regex)
            if not filter_set:
                print(f"Error: No tests matched pattern '{filter_pattern}'", file=sys.stderr)
                return False

        if file_line:
            # Parse file:line format
            if ':' in file_line:
                parts = file_line.rsplit(':', 1)
                target_file = parts[0]
                try:
                    target_line = int(parts[1])
                except ValueError:
                    print(f"Error: Invalid line number in '{file_line}'", file=sys.stderr)
                    return False
            else:
                print(f"Error: Expected format 'file.py:line', got '{file_line}'", file=sys.stderr)
                return False

            line_filter_set = self._find_tests_at_line(target_file, target_line)

            if not line_filter_set:
                print(f"Error: No tests found at {file_line}", file=sys.stderr)
                return False

            # Combine with name pattern filter if both are specified
            if filter_set is not None:
                filter_set = filter_set & line_filter_set
            else:
                filter_set = line_filter_set

        total_tests = self._count_tests(self.root, filter_set)

        if verbose:
            print(f"\n{'='*60}")
            if file_line:
                print(f"Running {total_tests} test(s) from {file_line}")
            else:
                print(f"Running {total_tests} test(s)")
            print(f"{'='*60}\n")

        passed, failed = self._run_context(self.root, verbose, filter_set=filter_set)

        if verbose:
            print(f"{'='*60}")
            print(f"Results: {passed} passed, {failed} failed, {total_tests} total")
            print(f"{'='*60}\n")

        return failed == 0

    def get_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.results

    def _parse_filter_pattern(self, pattern: str) -> Callable[[str], bool]:
        """
        Parse a filter pattern string and return a matcher function.

        Supports:
        - Simple substring matching: "Vec2" matches any test containing "Vec2"
        - Boolean operators: "Vec2 and add", "Vec2 or sub", "not slow"
        - Combinations: "Vec2 and not slow"
        - Regex mode (when use_regex=True): "Vec2.*add"

        Args:
            pattern: The filter pattern string

        Returns:
            A function that takes a test name and returns True if it matches
        """
        pattern = pattern.strip()

        # Handle boolean operators (case-insensitive)
        lower_pattern = pattern.lower()

        # Split on " and " first (highest precedence after grouping)
        if " and " in lower_pattern:
            parts = re.split(r'\s+and\s+', pattern, flags=re.IGNORECASE)
            matchers = [self._parse_filter_pattern(p) for p in parts]
            return lambda name: all(m(name) for m in matchers)

        # Split on " or "
        if " or " in lower_pattern:
            parts = re.split(r'\s+or\s+', pattern, flags=re.IGNORECASE)
            matchers = [self._parse_filter_pattern(p) for p in parts]
            return lambda name: any(m(name) for m in matchers)

        # Handle "not " prefix
        if lower_pattern.startswith("not "):
            inner_pattern = pattern[4:].strip()
            inner_matcher = self._parse_filter_pattern(inner_pattern)
            return lambda name: not inner_matcher(name)

        # Simple case-insensitive substring match
        return lambda name: pattern.lower() in name.lower()

    def _parse_regex_pattern(self, pattern: str) -> Callable[[str], bool]:
        """
        Parse a regex pattern and return a matcher function.

        Args:
            pattern: The regex pattern string

        Returns:
            A function that takes a test name and returns True if it matches
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            return lambda name: regex.search(name) is not None
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
            # Fall back to literal match
            return lambda name: pattern.lower() in name.lower()

    def _filter_tests_by_pattern(
        self, pattern: str, use_regex: bool = False
    ) -> set:
        """
        Find tests matching a name pattern.

        Args:
            pattern: The filter pattern
            use_regex: Whether to use regex matching

        Returns:
            A set of test IDs (using id()) that match the pattern
        """
        if use_regex:
            matcher = self._parse_regex_pattern(pattern)
        else:
            matcher = self._parse_filter_pattern(pattern)

        matching_tests = set()

        def search(context: Context):
            for test in context.tests:
                # Match against full test name including context
                full_name = f"{context.full_name}::{test.name}" if context.full_name else test.name
                if matcher(full_name):
                    matching_tests.add(id(test))

            for child in context.children:
                search(child)

        search(self.root)
        return matching_tests
