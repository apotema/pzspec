"""
Example test suite for Zig math operations using the Python DSL.
"""

from pzspec import ZigLibrary, describe, it, expect, assert_equal


# Load the Zig library
zig = ZigLibrary()


# Define test suites using the DSL
with describe("Math Operations"):
    
    @it("should add two positive numbers")
    def test_add_positive():
        result = zig.add(5, 3)
        expect(result).to_equal(8)
    
    @it("should add negative numbers")
    def test_add_negative():
        result = zig.add(-5, -3)
        expect(result).to_equal(-8)
    
    @it("should multiply two numbers")
    def test_multiply():
        result = zig.multiply(4, 7)
        expect(result).to_equal(28)
    
    @it("should subtract numbers")
    def test_subtract():
        result = zig.subtract(10, 4)
        expect(result).to_equal(6)
    
    @it("should handle zero in addition")
    def test_add_zero():
        result = zig.add(5, 0)
        expect(result).to_equal(5)


with describe("Division Operations"):
    
    @it("should divide two numbers")
    def test_divide():
        result = zig.divide(10.0, 2.0)
        expect(result).to_equal(5.0)
    
    @it("should handle division by zero")
    def test_divide_by_zero():
        result = zig.divide(10.0, 0.0)
        expect(result).to_equal(0.0)  # Our implementation returns 0 on division by zero


with describe("Boolean Operations"):
    
    @it("should identify even numbers")
    def test_is_even():
        expect(zig.is_even(4)).to_be_true()
        expect(zig.is_even(2)).to_be_true()
        expect(zig.is_even(0)).to_be_true()
    
    @it("should identify odd numbers")
    def test_is_odd():
        expect(zig.is_even(3)).to_be_false()
        expect(zig.is_even(5)).to_be_false()
        expect(zig.is_even(1)).to_be_false()


with describe("Array Operations"):
    
    @it("should sum an array of integers")
    def test_sum_array():
        arr = [1, 2, 3, 4, 5]
        result = zig.sum_array(arr)
        expect(result).to_equal(15)
    
    @it("should sum an empty array")
    def test_sum_empty_array():
        arr = []
        result = zig.sum_array(arr)
        expect(result).to_equal(0)
    
    @it("should reverse an array in place")
    def test_reverse_array():
        arr = [1, 2, 3, 4, 5]
        result = zig.reverse_array(arr)
        expect(result).to_equal([5, 4, 3, 2, 1])


with describe("String Operations"):
    
    @it("should calculate string length")
    def test_string_length():
        result = zig.string_length("hello")
        expect(result).to_equal(5)
    
    @it("should handle empty strings")
    def test_empty_string_length():
        result = zig.string_length("")
        expect(result).to_equal(0)
    
    @it("should handle unicode strings")
    def test_unicode_string_length():
        # Note: This tests byte length, not character count
        result = zig.string_length("hello世界")
        # UTF-8 encoding of "世界" is 6 bytes, so total is 11 bytes
        expect(result).to_equal(11)

