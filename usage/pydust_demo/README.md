# Pydust Demo

This example demonstrates using [Ziggy-Pydust](https://github.com/spiraldb/ziggy-pydust) with PZSpec for testing Zig code.

## What is Ziggy-Pydust?

Ziggy-Pydust is a framework for writing Python extension modules in Zig. Unlike the traditional ctypes/FFI approach used by PZSpec, Pydust:

- **Eliminates manual C ABI wrappers** - No `export fn` needed
- **Automatic type conversion** - Python objects ↔ Zig types
- **Native Python modules** - Direct import, no ctypes
- **Struct methods** - Zig struct methods become Python methods

## Comparison

### Traditional PZSpec (ctypes)

```python
import ctypes
from pzspec import ZigLibrary

class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

zig = ZigLibrary()

# Manual type declaration for each function
func = zig.get_function("point_distance",
    [ctypes.POINTER(Point), ctypes.POINTER(Point)],
    ctypes.c_float)

# Need byref() for pointer parameters
result = func(ctypes.byref(p1), ctypes.byref(p2))
```

```zig
// Need explicit export wrappers
export fn point_distance(p1: *const Point, p2: *const Point) f32 {
    return p1.distance_to(p2.*);
}
```

### With Pydust

```python
import mathlib  # Direct import!

# No type declarations needed
result = mathlib.point_distance(p1, p2)

# Struct methods work too
p = mathlib.point_new(3.0, 4.0)
magnitude = p.magnitude()
```

```zig
// No export wrappers - just regular Zig code
pub fn point_distance(p1: Point, p2: Point) f64 {
    return p1.distance_to(p2);
}

comptime {
    py.rootmodule(@This());  // One line to export everything
}
```

## Setup

1. Install Poetry if not already installed
2. Run `poetry install` to build the Zig module
3. Run tests: `poetry run python test_pydust_mathlib.py`

## Requirements

- Python 3.11+
- Zig 0.15.1 (installed automatically by ziggy-pydust)
- Poetry

## When to Use Pydust vs Traditional FFI

**Use Pydust when:**
- Building Python packages with Zig backends
- You want the cleanest Python API possible
- You need automatic type conversion
- Using Poetry as your build system

**Use Traditional FFI when:**
- Testing existing Zig libraries without modification
- You can't add Poetry as a dependency
- You need fine-grained control over memory layout
- Working with existing C ABI conventions

## Files

- `src/mathlib.zig` - Zig module using Pydust
- `test_pydust_mathlib.py` - PZSpec tests
- `pyproject.toml` - Poetry + Pydust configuration
- `build.py` - Pydust build script
