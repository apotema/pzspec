"""
Domain-Specific Language for writing tests in a readable, expressive way.
"""

from typing import Any, Callable, Optional, List
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


def describe(name: str, tags: Optional[List[str]] = None):
    """
    Create a test suite (describe block).

    Usage:
        with describe("Math Operations"):
            it("should add two numbers", lambda: ...)

        # With tags (tags are inherited by all tests in the block)
        with describe("Slow Tests", tags=["slow", "integration"]):
            @it("should work")
            def test_slow():
                ...
    """
    return get_runner().describe(name, tags=tags)


def it(name: str, tags: Optional[List[str]] = None):
    """
    Decorator for defining a test case.

    Usage:
        @it("should add two numbers")
        def test_add():
            expect(add(2, 3)).to_equal(5)

        # With tags
        @it("should handle large dataset", tags=["slow", "integration"])
        def test_large():
            ...
    """
    def decorator(func: Callable):
        get_runner().add_test(name, func, tags=tags)
        return func
    return decorator


# Convenience shortcuts for common tags
class it_skip:
    """Mark a test to be skipped."""
    def __init__(self, name: str):
        self.name = name

    def __call__(self, func: Callable):
        get_runner().add_test(self.name, func, tags=["skip"])
        return func


class it_slow:
    """Mark a test as slow."""
    def __init__(self, name: str):
        self.name = name

    def __call__(self, func: Callable):
        get_runner().add_test(self.name, func, tags=["slow"])
        return func


class it_focus:
    """Mark a test to be focused (only this test runs)."""
    def __init__(self, name: str):
        self.name = name

    def __call__(self, func: Callable):
        get_runner().add_test(self.name, func, tags=["focus"])
        return func


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


def before_all(func: Callable):
    """
    Decorator to run a function once before all tests in the current context.

    Usage:
        with describe("Database"):
            @before_all
            def setup_db():
                db.connect()
    """
    return get_runner().before_all(func)


def after_all(func: Callable):
    """
    Decorator to run a function once after all tests in the current context.

    Usage:
        with describe("Database"):
            @after_all
            def teardown_db():
                db.disconnect()
    """
    return get_runner().after_all(func)


def before_each(func: Callable):
    """
    Decorator to run a function before each test in the current context.
    Also runs before tests in nested contexts.

    Usage:
        with describe("User"):
            @before_each
            def setup_user():
                user = User.create()
    """
    return get_runner().before_each(func)


def after_each(func: Callable):
    """
    Decorator to run a function after each test in the current context.
    Also runs after tests in nested contexts.

    Usage:
        with describe("User"):
            @after_each
            def cleanup():
                User.delete_all()
    """
    return get_runner().after_each(func)


# Aliases for convenience
def before(func: Callable):
    """Alias for before_each."""
    return before_each(func)


def after(func: Callable):
    """Alias for after_each."""
    return after_each(func)


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

    def to_match_snapshot(self, name: Optional[str] = None, serializer: Optional[Callable] = None):
        """
        Assert that actual matches a saved snapshot.

        On first run, saves the value as the snapshot.
        On subsequent runs, compares against the saved snapshot.

        Args:
            name: Optional name for the snapshot (auto-generated if not provided)
            serializer: Optional custom serializer function

        Usage:
            expect(result).to_match_snapshot()
            expect(config).to_match_snapshot("config_v1")
        """
        from .snapshot import get_snapshot_manager

        manager = get_snapshot_manager()
        result = manager.match_snapshot(self.actual, name=name, serializer=serializer)

        if not result.matched:
            if result.is_new:
                raise AssertionError(
                    f"New snapshot '{name or 'auto'}' - run with --update-snapshots to save"
                )
            else:
                error_msg = f"Snapshot mismatch:\n{result.diff}"
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

