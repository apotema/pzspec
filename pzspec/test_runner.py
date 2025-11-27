"""
Test runner for executing test suites and collecting results.

Supports nested describe blocks with before/after hooks like RSpec.
"""

import sys
import time
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


class Context:
    """
    A test context (describe block) that can be nested.

    Supports:
    - Nested contexts with hierarchical names
    - before(:each) / after(:each) hooks - run for each test
    - before(:all) / after(:all) hooks - run once per context
    """

    def __init__(self, name: str, parent: Optional['Context'] = None):
        self.name = name
        self.parent = parent
        self.children: List['Context'] = []
        self.tests: List[TestCase] = []

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
        context = Context(name=name, parent=self.current_context)
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
        self.current_context.tests.append(TestCase(name=name, func=func))

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

    def _count_tests(self, context: Context) -> int:
        """Count total tests in a context and its children."""
        count = len(context.tests)
        for child in context.children:
            count += self._count_tests(child)
        return count

    def _run_context(self, context: Context, verbose: bool, indent: int = 0) -> tuple:
        """
        Run all tests in a context and its children.

        Returns:
            (passed_count, failed_count)
        """
        passed = 0
        failed = 0
        prefix = "  " * indent

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

        for test in context.tests:
            start_time = time.time()
            error_msg = None
            test_passed = True

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
                child, verbose, indent + 1
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

    def run(self, verbose: bool = True) -> bool:
        """
        Run all collected tests.

        Returns:
            True if all tests passed, False otherwise
        """
        total_tests = self._count_tests(self.root)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Running {total_tests} test(s)")
            print(f"{'='*60}\n")

        passed, failed = self._run_context(self.root, verbose)

        if verbose:
            print(f"{'='*60}")
            print(f"Results: {passed} passed, {failed} failed, {total_tests} total")
            print(f"{'='*60}\n")

        return failed == 0

    def get_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.results
