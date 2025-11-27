"""
Test suite for Calculator library - demonstrates partial code coverage.

This test file intentionally only tests some functions to show
how coverage reports highlight untested code.
"""

import sys
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pzspec.zig_ffi import ZigLibrary
from pzspec.dsl import describe, it, expect
import ctypes


# Load the Zig library
zig = ZigLibrary()


# Test only basic arithmetic - leaving advanced operations untested
with describe("Calculator - Basic Arithmetic"):

    @it("should add two numbers")
    def test_add():
        func = zig.get_function("add", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        expect(func(2, 3)).to_equal(5)
        expect(func(-1, 1)).to_equal(0)
        expect(func(0, 0)).to_equal(0)

    @it("should subtract two numbers")
    def test_subtract():
        func = zig.get_function("subtract", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        expect(func(5, 3)).to_equal(2)
        expect(func(3, 5)).to_equal(-2)

    @it("should multiply two numbers")
    def test_multiply():
        func = zig.get_function("multiply", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        expect(func(3, 4)).to_equal(12)
        expect(func(-2, 3)).to_equal(-6)
        expect(func(0, 100)).to_equal(0)


with describe("Calculator - Division"):

    @it("should divide two numbers")
    def test_divide():
        func = zig.get_function("divide", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        expect(func(10, 2)).to_equal(5)
        expect(func(7, 3)).to_equal(2)  # Integer division

    # Note: We're NOT testing division by zero!
    # This branch will show as uncovered


with describe("Calculator - Even/Odd Check"):

    @it("should check if number is even")
    def test_is_even():
        func = zig.get_function("is_even", [ctypes.c_int32], ctypes.c_bool)
        expect(func(4)).to_equal(True)
        expect(func(3)).to_equal(False)
        expect(func(0)).to_equal(True)

    # Note: We're NOT testing is_odd!
    # This function will show as completely uncovered


# Note: The following functions are NOT tested at all:
# - power()
# - factorial()
# - fibonacci()
# - max()
# - min()
# - abs()
# - sign()
# - gcd()
# - is_odd()
#
# Run with: pzspec --coverage
# to see these functions marked as uncovered
