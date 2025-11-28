"""
Test suite for Vector Math library using PZSpec DSL with Pydust.

This demonstrates how tests would look when using Pydust instead of ctypes.
Key differences:
- Import the Zig module directly as a Python module
- No ctypes.Structure definitions needed
- No ctypes.byref() or pointer handling
- Named arguments for function calls
- Direct method calls on Zig structs

NOTE: This is a proof-of-concept. To run these tests:
1. Install ziggy-pydust: pip install ziggy-pydust
2. Build the module: see pyproject_pydust.toml
"""

# When using Pydust, import the Zig module directly
# import vector_math  # This would be the compiled Pydust module

# For comparison, here's how we'd set up the tests with Pydust:
from pzspec import describe, it, expect, assert_almost_equal

# Mock the Pydust module for demonstration purposes
# In a real setup, this would be: import vector_math
class MockVec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def add(self, other):
        return MockVec2(self.x + other.x, self.y + other.y)
    
    def subtract(self, other):
        return MockVec2(self.x - other.x, self.y - other.y)
    
    def scale(self, scalar):
        return MockVec2(self.x * scalar, self.y * scalar)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y
    
    def magnitude(self):
        import math
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self):
        mag = self.magnitude()
        if mag == 0.0:
            return MockVec2(0.0, 0.0)
        return MockVec2(self.x / mag, self.y / mag)
    
    def distance(self, other):
        import math
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)


class MockVec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def add(self, other):
        return MockVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def cross(self, other):
        return MockVec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def magnitude(self):
        import math
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)


# Mock the vector_math module
class MockVectorMath:
    Vec2 = MockVec2
    Vec3 = MockVec3
    
    @staticmethod
    def vec2_new(x, y):
        return MockVec2(x, y)
    
    @staticmethod
    def vec2_add(a, b):
        return a.add(b)
    
    @staticmethod
    def vec2_subtract(a, b):
        return a.subtract(b)
    
    @staticmethod
    def vec2_scale(v, scalar):
        return v.scale(scalar)
    
    @staticmethod
    def vec2_dot(a, b):
        return a.dot(b)
    
    @staticmethod
    def vec2_magnitude(v):
        return v.magnitude()
    
    @staticmethod
    def vec2_normalize(v):
        return v.normalize()
    
    @staticmethod
    def vec2_distance(a, b):
        return a.distance(b)
    
    @staticmethod
    def vec3_new(x, y, z):
        return MockVec3(x, y, z)
    
    @staticmethod
    def vec3_add(a, b):
        return a.add(b)
    
    @staticmethod
    def vec3_cross(a, b):
        return a.cross(b)
    
    @staticmethod
    def vec3_dot(a, b):
        return a.dot(b)
    
    @staticmethod
    def vec3_magnitude(v):
        return v.magnitude()


# Use mock module (replace with actual import when Pydust is set up)
vector_math = MockVectorMath


# ============================================================================
# TEST SUITES - These show the cleaner API with Pydust
# ============================================================================

with describe("Vec2 - Basic Operations (Pydust)"):
    
    @it("should create a new 2D vector")
    def test_vec2_new():
        # Pydust: Direct constructor call, no ctypes!
        v = vector_math.Vec2(x=3.0, y=4.0)
        expect(v.x).to_equal(3.0)
        expect(v.y).to_equal(4.0)
    
    @it("should add two 2D vectors using methods")
    def test_vec2_add_method():
        # Pydust: Direct method calls on Zig structs
        a = vector_math.Vec2(x=1.0, y=2.0)
        b = vector_math.Vec2(x=3.0, y=4.0)
        result = a.add(b)  # No byref() or pointer handling!
        expect(result.x).to_equal(4.0)
        expect(result.y).to_equal(6.0)
    
    @it("should add two 2D vectors using module function")
    def test_vec2_add_function():
        # Pydust: Named arguments
        a = vector_math.Vec2(x=1.0, y=2.0)
        b = vector_math.Vec2(x=3.0, y=4.0)
        result = vector_math.vec2_add(a=a, b=b)
        expect(result.x).to_equal(4.0)
        expect(result.y).to_equal(6.0)
    
    @it("should subtract two 2D vectors")
    def test_vec2_subtract():
        a = vector_math.Vec2(x=5.0, y=7.0)
        b = vector_math.Vec2(x=2.0, y=3.0)
        result = a.subtract(b)
        expect(result.x).to_equal(3.0)
        expect(result.y).to_equal(4.0)
    
    @it("should scale a 2D vector by a scalar")
    def test_vec2_scale():
        v = vector_math.Vec2(x=2.0, y=3.0)
        result = v.scale(2.5)
        expect(result.x).to_equal(5.0)
        expect(result.y).to_equal(7.5)


with describe("Vec2 - Advanced Operations (Pydust)"):
    
    @it("should calculate dot product of two 2D vectors")
    def test_vec2_dot():
        a = vector_math.Vec2(x=1.0, y=2.0)
        b = vector_math.Vec2(x=3.0, y=4.0)
        result = a.dot(b)
        expect(result).to_equal(11.0)  # 1*3 + 2*4 = 11
    
    @it("should calculate magnitude of a 2D vector")
    def test_vec2_magnitude():
        v = vector_math.Vec2(x=3.0, y=4.0)
        result = v.magnitude()
        expect(result).to_equal(5.0)  # sqrt(3^2 + 4^2) = 5
    
    @it("should normalize a 2D vector to unit length")
    def test_vec2_normalize():
        v = vector_math.Vec2(x=3.0, y=4.0)
        result = v.normalize()
        mag = result.magnitude()
        assert_almost_equal(mag, 1.0, delta=0.001)
        assert_almost_equal(result.x, 0.6, delta=0.001)
        assert_almost_equal(result.y, 0.8, delta=0.001)
    
    @it("should handle normalization of zero vector")
    def test_vec2_normalize_zero():
        v = vector_math.Vec2(x=0.0, y=0.0)
        result = v.normalize()
        expect(result.x).to_equal(0.0)
        expect(result.y).to_equal(0.0)
    
    @it("should calculate distance between two 2D vectors")
    def test_vec2_distance():
        a = vector_math.Vec2(x=0.0, y=0.0)
        b = vector_math.Vec2(x=3.0, y=4.0)
        result = a.distance(b)
        expect(result).to_equal(5.0)  # sqrt(3^2 + 4^2) = 5


with describe("Vec3 - Basic Operations (Pydust)"):
    
    @it("should create a new 3D vector")
    def test_vec3_new():
        v = vector_math.Vec3(x=1.0, y=2.0, z=3.0)
        expect(v.x).to_equal(1.0)
        expect(v.y).to_equal(2.0)
        expect(v.z).to_equal(3.0)
    
    @it("should add two 3D vectors")
    def test_vec3_add():
        a = vector_math.Vec3(x=1.0, y=2.0, z=3.0)
        b = vector_math.Vec3(x=4.0, y=5.0, z=6.0)
        result = a.add(b)
        expect(result.x).to_equal(5.0)
        expect(result.y).to_equal(7.0)
        expect(result.z).to_equal(9.0)


with describe("Vec3 - Advanced Operations (Pydust)"):
    
    @it("should calculate dot product of two 3D vectors")
    def test_vec3_dot():
        a = vector_math.Vec3(x=1.0, y=2.0, z=3.0)
        b = vector_math.Vec3(x=4.0, y=5.0, z=6.0)
        result = a.dot(b)
        expect(result).to_equal(32.0)  # 1*4 + 2*5 + 3*6 = 32
    
    @it("should calculate cross product of two 3D vectors")
    def test_vec3_cross():
        a = vector_math.Vec3(x=1.0, y=0.0, z=0.0)  # Unit vector along x-axis
        b = vector_math.Vec3(x=0.0, y=1.0, z=0.0)  # Unit vector along y-axis
        result = a.cross(b)
        expect(result.x).to_equal(0.0)
        expect(result.y).to_equal(0.0)
        expect(result.z).to_equal(1.0)  # Should be unit vector along z-axis
    
    @it("should calculate magnitude of a 3D vector")
    def test_vec3_magnitude():
        v = vector_math.Vec3(x=2.0, y=3.0, z=6.0)
        result = v.magnitude()
        expect(result).to_equal(7.0)  # sqrt(2^2 + 3^2 + 6^2) = sqrt(49) = 7


with describe("Vec3 - Cross Product Properties (Pydust)"):
    
    @it("should satisfy anti-commutativity: a × b = -(b × a)")
    def test_vec3_cross_anticommutative():
        a = vector_math.Vec3(x=1.0, y=2.0, z=3.0)
        b = vector_math.Vec3(x=4.0, y=5.0, z=6.0)
        cross_ab = a.cross(b)
        cross_ba = b.cross(a)
        expect(cross_ab.x).to_equal(-cross_ba.x)
        expect(cross_ab.y).to_equal(-cross_ba.y)
        expect(cross_ab.z).to_equal(-cross_ba.z)
    
    @it("should produce orthogonal vector (a · (a × b) = 0)")
    def test_vec3_cross_orthogonal():
        a = vector_math.Vec3(x=1.0, y=2.0, z=3.0)
        b = vector_math.Vec3(x=4.0, y=5.0, z=6.0)
        cross = a.cross(b)
        dot_product = a.dot(cross)
        assert_almost_equal(dot_product, 0.0, delta=0.001)


# ============================================================================
# COMPARISON: Current ctypes approach vs Pydust approach
# ============================================================================

"""
CURRENT CTYPES APPROACH:
------------------------
# 1. Define ctypes Structure
class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

# 2. Load library
zig = ZigLibrary()

# 3. Create wrapper function with explicit types
def vec2_add(a, b):
    func = zig.get_function("vec2_add", 
        [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(a), ctypes.byref(b))

# 4. Use in test
a = Vec2(x=1.0, y=2.0)
b = Vec2(x=3.0, y=4.0)
result = vec2_add(a, b)


PYDUST APPROACH:
----------------
# 1. Import module directly
import vector_math

# 2. Use directly - no wrappers needed!
a = vector_math.Vec2(x=1.0, y=2.0)
b = vector_math.Vec2(x=3.0, y=4.0)
result = a.add(b)  # Direct method call!
# OR
result = vector_math.vec2_add(a=a, b=b)  # Named arguments


LINES OF CODE COMPARISON:
-------------------------
                    ctypes      Pydust
Python setup        12+ lines   1 import
Per function call   3 lines     1 line
Type definitions    5+ lines    0 lines
Total boilerplate   20+ lines   1 line
"""
