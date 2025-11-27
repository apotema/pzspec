"""
Mocking and stubbing support for Zig functions via FFI.

Provides context managers for temporarily replacing Zig function behavior
during tests. This is implemented at the FFI layer using ctypes.

Note: This approach has limitations:
- Only works with functions accessed through ZigLibrary
- Cannot mock internal Zig-to-Zig calls
- Functions must be accessed via get_function() after mock is set up
"""

import ctypes
from typing import Any, Callable, List, Optional, Union
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class MockCall:
    """Record of a call to a mocked function."""
    args: tuple
    kwargs: dict = field(default_factory=dict)


@dataclass
class MockConfig:
    """Configuration for a mocked function."""
    returns: Any = None
    returns_sequence: Optional[List[Any]] = None
    side_effect: Optional[Callable] = None
    call_count: int = 0
    calls: List[MockCall] = field(default_factory=list)
    _sequence_index: int = 0


class MockRegistry:
    """
    Registry of active mocks for Zig functions.

    This is used by ZigLibrary to intercept function calls and return
    mocked values instead of calling the actual Zig function.
    """

    def __init__(self):
        self._mocks: dict = {}
        self._original_functions: dict = {}

    def register_mock(self, name: str, config: MockConfig):
        """Register a mock for a function."""
        self._mocks[name] = config

    def unregister_mock(self, name: str):
        """Remove a mock for a function."""
        if name in self._mocks:
            del self._mocks[name]

    def is_mocked(self, name: str) -> bool:
        """Check if a function is mocked."""
        return name in self._mocks

    def get_mock_config(self, name: str) -> Optional[MockConfig]:
        """Get the mock configuration for a function."""
        return self._mocks.get(name)

    def call_mock(self, name: str, *args, **kwargs) -> Any:
        """
        Call a mocked function and return the configured result.

        Records the call and returns the appropriate value based on
        the mock configuration.
        """
        config = self._mocks.get(name)
        if config is None:
            raise ValueError(f"No mock registered for '{name}'")

        # Record the call
        config.calls.append(MockCall(args=args, kwargs=kwargs))
        config.call_count += 1

        # Handle side_effect (callable)
        if config.side_effect is not None:
            return config.side_effect(*args, **kwargs)

        # Handle returns_sequence
        if config.returns_sequence is not None:
            if config._sequence_index < len(config.returns_sequence):
                result = config.returns_sequence[config._sequence_index]
                config._sequence_index += 1
                return result
            # If sequence exhausted, return the last value
            return config.returns_sequence[-1] if config.returns_sequence else None

        # Handle simple returns
        return config.returns

    def clear_all(self):
        """Clear all mocks."""
        self._mocks.clear()


# Global mock registry
_mock_registry = MockRegistry()


def get_mock_registry() -> MockRegistry:
    """Get the global mock registry."""
    return _mock_registry


@contextmanager
def mock_zig_function(
    name: str,
    returns: Any = None,
    returns_sequence: Optional[List[Any]] = None,
    side_effect: Optional[Callable] = None,
):
    """
    Context manager to mock a Zig function during a test.

    The mock intercepts calls to the function made through ZigLibrary.get_function()
    and returns the configured values instead of calling the actual Zig code.

    Args:
        name: The name of the Zig function to mock
        returns: A fixed value to return for all calls
        returns_sequence: A sequence of values to return in order
        side_effect: A callable to execute instead of the function

    Usage:
        with mock_zig_function("external_api", returns=42):
            result = zig.get_function("external_api", [], ctypes.c_int32)()
            assert result == 42

        with mock_zig_function("retry_func", returns_sequence=[False, False, True]):
            # First call returns False, second False, third True
            ...

        def my_side_effect(x):
            return x * 2

        with mock_zig_function("compute", side_effect=my_side_effect):
            result = zig.get_function("compute", [ctypes.c_int32], ctypes.c_int32)(21)
            assert result == 42

    Note:
        - The mock only works for functions retrieved AFTER entering the context
        - Functions cached before the mock won't be affected
        - Internal Zig-to-Zig calls are not intercepted
    """
    config = MockConfig(
        returns=returns,
        returns_sequence=returns_sequence,
        side_effect=side_effect,
    )

    registry = get_mock_registry()
    registry.register_mock(name, config)

    try:
        yield config
    finally:
        registry.unregister_mock(name)


class MockFunction:
    """
    A wrapper that acts like a ctypes function but returns mocked values.

    This is returned by ZigLibrary.get_function() when the function is mocked.
    """

    def __init__(self, name: str, argtypes: List, restype):
        self.name = name
        self.argtypes = argtypes
        self.restype = restype
        self._registry = get_mock_registry()

    def __call__(self, *args, **kwargs):
        """Call the mock and return the configured result."""
        result = self._registry.call_mock(self.name, *args, **kwargs)

        # Convert result to the expected return type if needed
        if self.restype is not None and result is not None:
            if self.restype == ctypes.c_int32:
                return int(result)
            elif self.restype == ctypes.c_float:
                return float(result)
            elif self.restype == ctypes.c_double:
                return float(result)
            elif self.restype == ctypes.c_bool:
                return bool(result)

        return result


def assert_called(name: str, msg: Optional[str] = None):
    """Assert that a mocked function was called at least once."""
    config = get_mock_registry().get_mock_config(name)
    if config is None:
        raise AssertionError(f"No mock registered for '{name}'")
    if config.call_count == 0:
        error_msg = msg or f"Expected '{name}' to be called, but it was not"
        raise AssertionError(error_msg)


def assert_called_once(name: str, msg: Optional[str] = None):
    """Assert that a mocked function was called exactly once."""
    config = get_mock_registry().get_mock_config(name)
    if config is None:
        raise AssertionError(f"No mock registered for '{name}'")
    if config.call_count != 1:
        error_msg = msg or f"Expected '{name}' to be called once, but it was called {config.call_count} times"
        raise AssertionError(error_msg)


def assert_called_with(name: str, *args, **kwargs):
    """Assert that a mocked function was called with specific arguments."""
    config = get_mock_registry().get_mock_config(name)
    if config is None:
        raise AssertionError(f"No mock registered for '{name}'")
    if not config.calls:
        raise AssertionError(f"Expected '{name}' to be called, but it was not")

    last_call = config.calls[-1]
    if last_call.args != args or last_call.kwargs != kwargs:
        raise AssertionError(
            f"Expected '{name}' to be called with args={args}, kwargs={kwargs}, "
            f"but was called with args={last_call.args}, kwargs={last_call.kwargs}"
        )


def get_call_count(name: str) -> int:
    """Get the number of times a mocked function was called."""
    config = get_mock_registry().get_mock_config(name)
    if config is None:
        return 0
    return config.call_count


def get_calls(name: str) -> List[MockCall]:
    """Get all calls made to a mocked function."""
    config = get_mock_registry().get_mock_config(name)
    if config is None:
        return []
    return config.calls
