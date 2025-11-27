"""
Domain-Specific Language for writing tests in a readable, expressive way.
"""

from typing import Any, Callable, Optional
from .test_runner import TestRunner, TestSuite


# Global test runner instance
_runner: Optional[TestRunner] = None


def set_runner(runner: TestRunner):
    """Set the global test runner instance."""
    global _runner
    _runner = runner


def get_runner() -> TestRunner:
    """Get the global test runner instance."""
    global _runner
    if _runner is None:
        _runner = TestRunner()
    return _runner


def describe(name: str):
    """
    Create a test suite (describe block).
    
    Usage:
        with describe("Math Operations"):
            it("should add two numbers", lambda: ...)
    """
    return get_runner().describe(name)


def it(name: str):
    """
    Decorator for defining a test case.
    
    Usage:
        @it("should add two numbers")
        def test_add():
            expect(add(2, 3)).to_equal(5)
    """
    def decorator(func: Callable):
        get_runner().add_test(name, func)
        return func
    return decorator


def test(name: str, func: Optional[Callable] = None):
    """
    Define a test case (alternative syntax).
    
    Usage:
        test("should add two numbers", lambda: expect(add(2, 3)).to_equal(5))
    """
    if func is None:
        def decorator(f: Callable):
            get_runner().add_test(name, f)
            return f
        return decorator
    else:
        get_runner().add_test(name, func)


class Expectation:
    """Expectation object for fluent assertions."""
    
    def __init__(self, actual: Any):
        self.actual = actual
    
    def to_equal(self, expected: Any, msg: Optional[str] = None):
        """Assert that actual equals expected."""
        if self.actual != expected:
            error_msg = msg or f"Expected {expected}, but got {self.actual}"
            raise AssertionError(error_msg)
    
    def to_not_equal(self, expected: Any, msg: Optional[str] = None):
        """Assert that actual does not equal expected."""
        if self.actual == expected:
            error_msg = msg or f"Expected not {expected}, but got {self.actual}"
            raise AssertionError(error_msg)
    
    def to_be_true(self, msg: Optional[str] = None):
        """Assert that actual is True."""
        if not self.actual:
            error_msg = msg or f"Expected True, but got {self.actual}"
            raise AssertionError(error_msg)
    
    def to_be_false(self, msg: Optional[str] = None):
        """Assert that actual is False."""
        if self.actual:
            error_msg = msg or f"Expected False, but got {self.actual}"
            raise AssertionError(error_msg)
    
    def to_be_almost_equal(self, expected: float, delta: float = 0.0001, msg: Optional[str] = None):
        """Assert that actual is approximately equal to expected."""
        if abs(self.actual - expected) > delta:
            error_msg = msg or f"Expected {expected} ± {delta}, but got {self.actual}"
            raise AssertionError(error_msg)


def expect(actual: Any) -> Expectation:
    """
    Create an expectation for fluent assertions.
    
    Usage:
        expect(add(2, 3)).to_equal(5)
        expect(is_even(4)).to_be_true()
    """
    return Expectation(actual)


# Convenience assertion functions (alternative to fluent API)
def assert_equal(actual: Any, expected: Any, msg: Optional[str] = None):
    """Assert that actual equals expected."""
    expect(actual).to_equal(expected, msg)


def assert_not_equal(actual: Any, expected: Any, msg: Optional[str] = None):
    """Assert that actual does not equal expected."""
    expect(actual).to_not_equal(expected, msg)


def assert_true(condition: bool, msg: Optional[str] = None):
    """Assert that condition is True."""
    expect(condition).to_be_true(msg)


def assert_false(condition: bool, msg: Optional[str] = None):
    """Assert that condition is False."""
    expect(condition).to_be_false(msg)


def assert_almost_equal(actual: float, expected: float, delta: float = 0.0001, msg: Optional[str] = None):
    """Assert that actual is approximately equal to expected."""
    expect(actual).to_be_almost_equal(expected, delta, msg)

