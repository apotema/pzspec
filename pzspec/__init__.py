"""
PZSpec - Python DSL for Testing Zig Code

A Domain-Specific Language built in Python for writing concise, readable tests
for Zig code using FFI (Foreign Function Interface).
"""

from .test_runner import TestRunner, TestSuite
from .zig_ffi import ZigLibrary
from .builder import ZigBuilder, PZSpecConfig, auto_build
from .factory import (
    StructFactory,
    factory_field,
    sequence,
    trait,
)
from .dsl import (
    test,
    describe,
    it,
    it_skip,
    it_slow,
    it_focus,
    expect,
    assert_equal,
    assert_not_equal,
    assert_true,
    assert_false,
    assert_almost_equal,
    set_runner,
    before_all,
    after_all,
    before_each,
    after_each,
    before,
    after,
)
from .mock import (
    mock_zig_function,
    assert_called,
    assert_called_once,
    assert_called_with,
    get_call_count,
    get_calls,
)
from .memory import (
    track_memory,
    check_leaks,
    assert_no_leaks,
    MemoryLeakError,
)
from .sentinel import (
    Sentinel,
    NO_ENTITY,
    NO_INDEX,
    INVALID_ID,
)

# CLI is available but not exported by default
# Access via: from pzspec.cli import main

__all__ = [
    "TestRunner",
    "TestSuite",
    "ZigLibrary",
    "ZigBuilder",
    "PZSpecConfig",
    "auto_build",
    "StructFactory",
    "factory_field",
    "sequence",
    "trait",
    "test",
    "describe",
    "it",
    "it_skip",
    "it_slow",
    "it_focus",
    "expect",
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "assert_almost_equal",
    "set_runner",
    "before_all",
    "after_all",
    "before_each",
    "after_each",
    "before",
    "after",
    "mock_zig_function",
    "assert_called",
    "assert_called_once",
    "assert_called_with",
    "get_call_count",
    "get_calls",
    "track_memory",
    "check_leaks",
    "assert_no_leaks",
    "MemoryLeakError",
    "Sentinel",
    "NO_ENTITY",
    "NO_INDEX",
    "INVALID_ID",
]

__version__ = "0.1.0"
