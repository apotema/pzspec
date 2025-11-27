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
    expect,
    assert_equal,
    assert_not_equal,
    assert_true,
    assert_false,
    assert_almost_equal,
    set_runner,
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
    "expect",
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "assert_almost_equal",
    "set_runner",
]

__version__ = "0.1.0"
