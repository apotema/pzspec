"""
Test runner for executing test suites and collecting results.
"""

import sys
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
class TestSuite:
    """A collection of related tests."""
    name: str
    tests: List[Callable] = field(default_factory=list)
    test_names: List[str] = field(default_factory=list)
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None


class TestRunner:
    """
    Main test runner that collects and executes tests.
    """
    
    def __init__(self):
        self.suites: List[TestSuite] = []
        self.current_suite: Optional[TestSuite] = None
        self.results: List[TestResult] = []
    
    @contextmanager
    def describe(self, name: str):
        """
        Context manager for creating a test suite.
        
        Usage:
            with runner.describe("Math Operations"):
                runner.add_test("should add", lambda: ...)
        """
        suite = TestSuite(name=name)
        old_suite = self.current_suite
        self.current_suite = suite
        try:
            yield suite
            self.suites.append(suite)
        finally:
            self.current_suite = old_suite
    
    def add_test(self, name: str, func: Callable):
        """Add a test to the current suite or create a default suite."""
        if self.current_suite is None:
            # Create a default suite if none exists
            self.current_suite = TestSuite(name="Default Suite")
            self.suites.append(self.current_suite)
        
        self.current_suite.tests.append(func)
        self.current_suite.test_names.append(name)
    
    def run(self, verbose: bool = True) -> bool:
        """
        Run all collected tests.
        
        Returns:
            True if all tests passed, False otherwise
        """
        import time
        
        total_tests = sum(len(suite.tests) for suite in self.suites)
        passed_count = 0
        failed_count = 0
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Running {total_tests} test(s)")
            print(f"{'='*60}\n")
        
        for suite in self.suites:
            if verbose:
                print(f"Suite: {suite.name}")
                print("-" * 60)
            
            # Run setup if present
            if suite.setup:
                try:
                    suite.setup()
                except Exception as e:
                    if verbose:
                        print(f"  SETUP FAILED: {e}")
                    continue
            
            # Run tests
            for i, (test_func, test_name) in enumerate(zip(suite.tests, suite.test_names)):
                start_time = time.time()
                try:
                    test_func()
                    duration = time.time() - start_time
                    result = TestResult(name=f"{suite.name}::{test_name}", passed=True, duration=duration)
                    passed_count += 1
                    if verbose:
                        print(f"  ✓ {test_name} ({duration*1000:.2f}ms)")
                except Exception as e:
                    duration = time.time() - start_time
                    error_msg = str(e)
                    result = TestResult(name=f"{suite.name}::{test_name}", passed=False, error=error_msg, duration=duration)
                    failed_count += 1
                    if verbose:
                        print(f"  ✗ {test_name} ({duration*1000:.2f}ms)")
                        print(f"    Error: {error_msg}")
                
                self.results.append(result)
            
            # Run teardown if present
            if suite.teardown:
                try:
                    suite.teardown()
                except Exception as e:
                    if verbose:
                        print(f"  TEARDOWN FAILED: {e}")
            
            if verbose:
                print()
        
        # Summary
        if verbose:
            print(f"{'='*60}")
            print(f"Results: {passed_count} passed, {failed_count} failed, {total_tests} total")
            print(f"{'='*60}\n")
        
        return failed_count == 0
    
    def get_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.results

