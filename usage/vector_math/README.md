# Vector Math Library - Example Project Using PZSpec

This is a real-world example demonstrating how to use **PZSpec** (Python DSL for Testing Zig Code) to test a Zig library.

## Project Overview

This project implements a simple 2D and 3D vector math library in Zig, with comprehensive tests written using the PZSpec Python DSL.

### Features

- **2D Vector Operations**:
  - Vector creation, addition, subtraction
  - Scalar multiplication
  - Dot product
  - Magnitude calculation
  - Normalization
  - Distance calculation

- **3D Vector Operations**:
  - Vector creation, addition
  - Cross product
  - Dot product
  - Magnitude calculation

## Project Structure

```
vector_math/
├── src/
│   └── vector.zig       # Zig vector math implementation
├── .pzspec              # Optional configuration file
├── pzspec/              # Test directory (RSpec convention)
│   └── test_vectors.py  # PZSpec test suite
└── README.md            # This file
```

**Note:** 
- No `build_shared.sh` needed - library builds automatically
- `run_tests.py` is optional - use global `pzspec` command after installation

## Setup

### Prerequisites

1. **Zig**: Version 0.11+ (tested with 0.15.1)
2. **Python**: Python 3.8+
3. **PZSpec**: Install PZSpec globally:
   ```bash
   cd ../../  # PZSpec root directory
   pip install -e .
   ```

### Building the Library

**No build script needed!** PZSpec automatically builds the library when you run tests.

The library follows these conventions:
- Source: `src/vector.zig`
- Library name: `vector_math` (from project directory or `.pzspec`)
- Output: `zig-out/lib/libvector_math.dylib` (or `.so`/`.dll`)

You can customize the build by creating a `.pzspec` file (see example in this directory).

## Running Tests

**Option 1: Using the `pzspec` command (after installing PZSpec):**

```bash
# Install PZSpec first (from PZSpec root directory)
pip install -e ../..

# Then run tests from this directory
pzspec
```

**Option 2: Using run_tests.py (without installation):**

```bash
python3 run_tests.py
```

**Options:**
- `--verbose` or `-v`: Verbose output (default)
- `--quiet` or `-q`: Quiet output

## Example Test Output

```
============================================================
Running 15 test(s)
============================================================

Suite: Vec2 - Basic Operations
------------------------------------------------------------
  ✓ should create a new 2D vector (2.45ms)
  ✓ should add two 2D vectors (0.12ms)
  ✓ should subtract two 2D vectors (0.08ms)
  ✓ should scale a 2D vector by a scalar (0.05ms)

Suite: Vec2 - Advanced Operations
------------------------------------------------------------
  ✓ should calculate dot product of two 2D vectors (0.03ms)
  ✓ should calculate magnitude of a 2D vector (0.02ms)
  ✓ should normalize a 2D vector to unit length (0.15ms)
  ...

============================================================
Results: 15 passed, 0 failed, 15 total
============================================================
```

## How It Works

1. **Zig Library**: The `src/vector.zig` file defines vector structures and operations, with functions exported using the `export` keyword for C ABI compatibility.

2. **FFI Integration**: The Python test file (`pzspec/test_vectors.py`) uses `ctypes` to:
   - Load the compiled Zig shared library
   - Define C-compatible structures matching Zig's `extern struct`
   - Call Zig functions with proper type conversions

3. **PZSpec DSL**: Tests are written using PZSpec's fluent API in the `pzspec/` directory (following RSpec convention):
   ```python
   # In pzspec/test_vectors.py
   with describe("Vec2 - Basic Operations"):
       @it("should add two 2D vectors")
       def test_vec2_add():
           a = vec2_new(1.0, 2.0)
           b = vec2_new(3.0, 4.0)
           result = vec2_add(a, b)
           expect(result.x).to_equal(4.0)
           expect(result.y).to_equal(6.0)
   ```

## Key Concepts Demonstrated

### 1. Struct Passing

Zig structs are passed by pointer in C ABI. The Python code uses `ctypes.Structure` to define matching structures:

```python
class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]
```

### 2. Pointer Arguments

Functions that take struct pointers use `ctypes.byref()`:

```python
result = vec2_add(ctypes.byref(a), ctypes.byref(b))
```

### 3. Floating Point Comparisons

Use `assert_almost_equal` for floating point comparisons:

```python
assert_almost_equal(result.x, 0.6, delta=0.001)
```

## Extending the Project

### Adding New Vector Operations

1. Add the function to `src/vector.zig` with `export` keyword
2. Rebuild the library: `./build_shared.sh`
3. Add a Python wrapper function in `pzspec/test_vectors.py`
4. Write tests using the PZSpec DSL

### Example: Adding Vec2 Length Squared

**In `src/vector.zig`:**
```zig
export fn vec2_length_squared(v: *const Vec2) f32 {
    return v.x * v.x + v.y * v.y;
}
```

**In `pzspec/test_vectors.py`:**
```python
def vec2_length_squared(v):
    class Vec2(ctypes.Structure):
        _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]
    func = zig.get_function("vec2_length_squared", 
                            [ctypes.POINTER(Vec2)], 
                            ctypes.c_float)
    return func(ctypes.byref(v))

@it("should calculate length squared")
def test_vec2_length_squared():
    v = vec2_new(3.0, 4.0)
    result = vec2_length_squared(v)
    expect(result).to_equal(25.0)
```

## Troubleshooting

### Library Not Found

If you get a "library not found" error:
1. Make sure you've built the library: `./build_shared.sh`
2. Check that `zig-out/lib/libvector_math.dylib` exists
3. On Linux, the extension will be `.so`, on Windows `.dll`

### Import Errors

If you get import errors for PZSpec:
1. Make sure the parent PZSpec directory is in the Python path
2. The `run_tests.py` script should handle this automatically
3. You can manually add it: `sys.path.insert(0, '/path/to/pzspec')`

## License

This example project is part of the PZSpec framework and follows the same license.

