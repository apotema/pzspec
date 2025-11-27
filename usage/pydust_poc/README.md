# Ziggy-Pydust Proof-of-Concept

This directory contains the evaluation materials for using [Ziggy-Pydust](https://github.com/spiraldb/ziggy-pydust) as an alternative to the current manual FFI wrapper approach in PZSpec.

## Overview

Ziggy-Pydust is a framework for writing native Python extension modules in Zig. Unlike PZSpec's current ctypes approach (runtime FFI), Pydust generates Python C extensions at compile time.

## Key Differences

| Aspect | Current PZSpec (ctypes) | Ziggy-Pydust |
|--------|------------------------|--------------|
| FFI Mechanism | Runtime (ctypes) | Compile-time (C extensions) |
| Wrapper Code | Manual `export fn` in Zig | Automatic via comptime |
| Type Marshaling | Manual ctypes definitions | Automatic type conversion |
| Build System | zig build-lib | Poetry + Pydust |
| Dependencies | None (stdlib only) | pydantic, setuptools, poetry |
| Python Integration | ctypes.CDLL | Native module import |

## Example Comparison

### Current PZSpec Approach

**Zig code (src/vector.zig):**
```zig
// Must define C-ABI compatible struct
pub const Vec2 = extern struct {
    x: f32,
    y: f32,
};

// Must manually create export wrapper
export fn vec2_add(a: *const Vec2, b: *const Vec2) Vec2 {
    return Vec2{ .x = a.x + b.x, .y = a.y + b.y };
}
```

**Python test (pzspec/test_vectors.py):**
```python
import ctypes
from pzspec import ZigLibrary, describe, it, expect

class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

zig = ZigLibrary()

def vec2_add(a, b):
    func = zig.get_function("vec2_add", 
        [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(a), ctypes.byref(b))

with describe("Vec2"):
    @it("should add two vectors")
    def test_add():
        a = Vec2(x=1.0, y=2.0)
        b = Vec2(x=3.0, y=4.0)
        result = vec2_add(a, b)
        expect(result.x).to_equal(4.0)
        expect(result.y).to_equal(6.0)
```

### Pydust Approach

**Zig code (src/vector.zig):**
```zig
const py = @import("pydust");

// Define regular Zig struct (not extern)
const Vec2 = struct {
    x: f32,
    y: f32,

    // Regular Zig methods
    fn add(self: Vec2, other: Vec2) Vec2 {
        return Vec2{ .x = self.x + other.x, .y = self.y + other.y };
    }
};

// Function with named args - Pydust handles conversion
pub fn vec2_add(args: struct { a: Vec2, b: Vec2 }) Vec2 {
    return args.a.add(args.b);
}

comptime {
    py.rootmodule(@This());
}
```

**Python test (pzspec/test_vectors.py):**
```python
from pzspec import describe, it, expect
import vector  # Native Python module!

with describe("Vec2"):
    @it("should add two vectors")
    def test_add():
        a = vector.Vec2(x=1.0, y=2.0)
        b = vector.Vec2(x=3.0, y=4.0)
        result = vector.vec2_add(a=a, b=b)
        expect(result.x).to_equal(4.0)
        expect(result.y).to_equal(6.0)
```

## Trade-offs Analysis

### Advantages of Pydust

1. **No Manual Wrapper Code**: Write native Zig code, Pydust generates FFI glue at comptime
2. **Automatic Type Conversion**: No need for ctypes.Structure definitions in Python
3. **Named Arguments**: Function arguments are named and type-checked
4. **Native Performance**: No ctypes overhead, direct C extension calls
5. **Pytest Integration**: Built-in pytest plugin for running Zig tests alongside Python
6. **Buffer Protocol**: Zero-copy NumPy integration for array types
7. **Error Handling**: Zig errors automatically converted to Python exceptions

### Disadvantages of Pydust

1. **Build Complexity**: Requires Poetry, pydantic, setuptools (vs. simple zig build-lib)
2. **Additional Dependencies**: Current PZSpec is stdlib-only
3. **Learning Curve**: Different paradigm from ctypes
4. **Architecture Changes**: Would require significant PZSpec modifications
5. **Less Flexible**: Tied to Pydust's type system

## Integration Options

### Option 1: Parallel Support (Recommended)

Add Pydust as an opt-in alternative alongside the current ctypes approach:

```python
# pzspec/__init__.py
from .zig_ffi import ZigLibrary  # Current approach
from .pydust_loader import PydustModule  # New approach

# Users choose which approach to use
```

**Configuration (.pzspec):**
```json
{
  "backend": "pydust",  // or "ctypes" (default)
  "pydust_module": "vector"
}
```

### Option 2: Gradual Migration

Keep ctypes as default, but allow individual test files to use Pydust:

```python
# Test file can import either
from pzspec import ZigLibrary  # ctypes
# OR
import vector  # Pydust-generated module
```

### Option 3: Full Migration

Replace ctypes entirely with Pydust (not recommended due to dependency overhead).

## Recommended Evaluation Steps

1. **Install Pydust**: `pip install ziggy-pydust`
2. **Create vector module**: Follow `src/vector_pydust.zig` example
3. **Build with Poetry**: Configure `pyproject.toml` with Pydust build
4. **Run benchmarks**: Compare ctypes vs native module performance
5. **Evaluate API**: Test PZSpec DSL compatibility

## Benchmarking Plan

Create a benchmark comparing:

1. **Call overhead**: Empty function call latency
2. **Struct passing**: Vec2/Vec3 creation and manipulation
3. **Array operations**: Large array processing
4. **String handling**: String marshaling performance

## Files in This POC

- `README.md` - This file
- `src/vector_pydust.zig` - Example Zig code using Pydust
- `pyproject_pydust.toml` - Example Poetry configuration for Pydust
- `EVALUATION.md` - Detailed evaluation report

## Conclusion

Ziggy-Pydust offers significant developer experience improvements by eliminating manual FFI wrapper code. However, it introduces additional dependencies and build complexity. The recommended approach is to add Pydust as an **opt-in backend** for projects that want cleaner FFI integration, while keeping the current ctypes approach as the default for projects that prefer simplicity and zero dependencies.

## References

- [Ziggy-Pydust GitHub](https://github.com/spiraldb/ziggy-pydust)
- [Pydust Documentation](https://pydust.fulcrum.so/latest/)
- [Getting Started Guide](https://pydust.fulcrum.so/latest/getting_started/)
- [Parent Issue #22](https://github.com/apotema/pzspec/issues/22)
