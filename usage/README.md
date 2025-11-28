# Usage Examples

This directory contains real-world examples demonstrating how to use PZSpec to test Zig projects.

## Available Examples

### vector_math

A complete 2D/3D vector math library in Zig with comprehensive tests using PZSpec.

**Features:**
- 2D vector operations (addition, subtraction, scaling, dot product, magnitude, normalization, distance)
- 3D vector operations (addition, cross product, dot product, magnitude)
- 16 test cases covering all functionality
- Demonstrates struct passing via FFI
- Shows how to handle floating-point comparisons

**Quick Start:**
```bash
# Install PZSpec (one time, from PZSpec root)
pip install -e ../..

# Then run tests from any project
cd vector_math
pzspec  # No run_tests.py needed!
```

See `vector_math/README.md` for detailed documentation.

### pydust_poc

**Proof-of-concept evaluation of Ziggy-Pydust as an alternative FFI backend.**

This directory contains evaluation materials for using [Ziggy-Pydust](https://github.com/spiraldb/ziggy-pydust) instead of manual ctypes wrappers.

**Features:**
- Comparison of ctypes vs Pydust approaches
- Example Zig code using Pydust's comptime registration
- Mock-based tests demonstrating the cleaner Pydust API
- Detailed evaluation report with trade-offs analysis
- Configuration examples for Poetry/maturin integration

**Key Benefits of Pydust:**
- No manual `export fn` wrappers needed
- No ctypes.Structure definitions required
- Direct method calls on Zig structs
- Named function arguments
- Automatic type conversion

See `pydust_poc/README.md` and `pydust_poc/EVALUATION.md` for detailed documentation.

### factory_demo

Demonstrates PZSpec's factory framework with Zig comptime generics.

**Features:**
- Zig comptime generic pattern: `pub fn ButcheryFactory(comptime L: RoomLevel) type {}`
- Python factories with defaults, sequences, and traits
- Testing concrete instantiations of generic types
- Multi-factory test scenarios

**Quick Start:**
```bash
cd factory_demo
pzspec
```

See `factory_demo/README.md` for detailed documentation.

## Creating Your Own Example

To create a new example project:

1. Create a new subdirectory in `usage/`
2. Set up your Zig project with:
   - `src/` directory with your Zig code (convention: `src/lib.zig` or `src/*.zig`)
   - Optional: `.pzspec` file for customization
3. Create tests using PZSpec (following RSpec convention):
   - `pzspec/` directory with Python test files (named `test_*.py`)
4. Export functions from Zig using `export` keyword
5. Use `ctypes` in Python to define matching structures and call functions

**No build scripts or run_tests.py needed!** 
- Install PZSpec: `pip install -e /path/to/pzspec`
- Run tests: `pzspec` (automatically finds and runs tests)
- Library builds automatically when needed

## Key Patterns

### Struct Definitions

Define C-compatible structures at module level:

```python
class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]
```

### Function Calls

Use `ctypes.byref()` to pass struct pointers:

```python
func = zig.get_function("vec2_add", 
                        [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], 
                        Vec2)
result = func(ctypes.byref(a), ctypes.byref(b))
```

### Test Organization

Place test files in the `pzspec/` directory (following RSpec convention) and use PZSpec's DSL:

```python
# In pzspec/test_my_feature.py
with describe("Feature Name"):
    @it("should do something")
    def test_something():
        result = call_zig_function()
        expect(result).to_equal(expected_value)
```

## Contributing Examples

If you create a useful example, consider contributing it back to the project! Examples should:

- Be self-contained and runnable
- Include a README with setup instructions
- Demonstrate real-world use cases
- Show best practices for FFI integration
- Include comprehensive tests

