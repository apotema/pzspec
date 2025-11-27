"""
Ziggy-Pydust integration for PZSpec.

This module provides utilities for using PZSpec with Ziggy-Pydust-based
Python extension modules. Pydust eliminates the need for manual C ABI
wrappers and ctypes declarations.

Example usage:
    from pzspec.pydust import PydustModule
    from pzspec import describe, it, expect

    # Wrap a Pydust module for PZSpec compatibility
    math = PydustModule("mathlib")

    with describe("Math"):
        @it("should add")
        def test_add():
            expect(math.add(1, 2)).to_equal(3)
"""

import importlib
from typing import Any, Callable, List, Optional


class PydustModuleNotFoundError(ImportError):
    """Raised when a Pydust module cannot be imported."""

    def __init__(self, module_name: str, original_error: Optional[Exception] = None):
        self.module_name = module_name
        self.original_error = original_error
        message = (
            f"Pydust module '{module_name}' not found. "
            "Make sure you've run 'poetry install' to build the module."
        )
        if original_error:
            message += f" Original error: {original_error}"
        super().__init__(message)


class PydustModule:
    """
    Wrapper for Ziggy-Pydust modules that provides a consistent API.

    This class provides compatibility between Pydust modules and PZSpec's
    testing patterns. While Pydust modules can be imported and used directly,
    this wrapper provides:

    - Consistent error messages if module isn't built
    - Method discovery for introspection
    - Compatibility with PZSpec's mock system (future)

    Example:
        # Direct usage (works without wrapper):
        import mathlib
        result = mathlib.add(1, 2)

        # With wrapper (for PZSpec compatibility):
        math = PydustModule("mathlib")
        result = math.add(1, 2)
    """

    def __init__(self, module_name: str):
        """
        Initialize a Pydust module wrapper.

        Args:
            module_name: The name of the Pydust module to import.

        Raises:
            PydustModuleNotFoundError: If the module cannot be imported.
        """
        self.module_name = module_name
        try:
            self._module = importlib.import_module(module_name)
        except ImportError as e:
            raise PydustModuleNotFoundError(module_name, e) from e

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped module."""
        try:
            return getattr(self._module, name)
        except AttributeError:
            raise AttributeError(
                f"Pydust module '{self.module_name}' has no attribute '{name}'"
            ) from None

    def get_functions(self) -> List[str]:
        """
        Get list of callable functions in the module.

        Returns:
            List of function names that can be called.
        """
        return [
            name
            for name in dir(self._module)
            if not name.startswith("_") and callable(getattr(self._module, name))
        ]

    def get_types(self) -> List[str]:
        """
        Get list of types (structs/classes) defined in the module.

        Returns:
            List of type names.
        """
        return [
            name
            for name in dir(self._module)
            if not name.startswith("_")
            and isinstance(getattr(self._module, name), type)
        ]

    def has_function(self, name: str) -> bool:
        """Check if the module has a callable function with the given name."""
        return hasattr(self._module, name) and callable(getattr(self._module, name))

    def reload(self) -> None:
        """
        Reload the module (useful during development).

        Note: This may not work correctly for extension modules that
        have native code. Use with caution.
        """
        self._module = importlib.reload(self._module)


def try_import_pydust_module(module_name: str) -> Optional[Any]:
    """
    Try to import a Pydust module, returning None if not found.

    This is useful for optional Pydust integration where tests should
    be skipped if the module isn't built.

    Example:
        mathlib = try_import_pydust_module("mathlib")
        if mathlib is None:
            print("mathlib not built, skipping tests")
        else:
            result = mathlib.add(1, 2)
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def is_pydust_available() -> bool:
    """
    Check if Ziggy-Pydust is installed.

    Returns:
        True if ziggy-pydust package is available.
    """
    try:
        import pydust  # noqa: F401

        return True
    except ImportError:
        return False


def skip_if_no_pydust(func: Callable) -> Callable:
    """
    Decorator to skip a test if Pydust is not available.

    Usage:
        @skip_if_no_pydust
        @it("should work with pydust")
        def test_pydust():
            import mathlib
            expect(mathlib.add(1, 2)).to_equal(3)
    """
    from functools import wraps
    from .dsl import it_skip

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_pydust_available():
            return it_skip("ziggy-pydust not installed")(func)
        return func(*args, **kwargs)

    return wrapper


# Re-export for convenience
__all__ = [
    "PydustModule",
    "PydustModuleNotFoundError",
    "try_import_pydust_module",
    "is_pydust_available",
    "skip_if_no_pydust",
]
