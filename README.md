# PZSpec - Python DSL for Testing Zig Code

A Domain-Specific Language built in Python for writing concise, readable tests for Zig code using FFI (Foreign Function Interface).

## Overview

PZSpec allows you to write expressive, readable tests in Python that call into Zig code compiled as a shared library. This combines Python's ease of use for test scripting with Zig's performance and safety guarantees.

**Key Features:**
- 🚀 **Zero Configuration**: Automatic library building, no build scripts needed
- 📁 **Convention Over Configuration**: Follows RSpec-style conventions
- 🔧 **Optional Customization**: `.pzspec` file for advanced configuration
- 🎯 **Simple Setup**: Just write tests, PZSpec handles the rest

## Project Structure

```
your-project/
├── src/
│   └── lib.zig          # Zig library with functions to test
├── .pzspec              # Optional configuration file
└── pzspec/              # Test files (RSpec convention)
    └── test_*.py        # Test files
```

**No `run_tests.py` needed!** Install PZSpec and use the `pzspec` command globally.

## Setup

### Prerequisites

1. **Zig**: Install Zig (version 0.11+ recommended)
   - Download from: https://ziglang.org/download/
   - Or use a package manager: `brew install zig` (macOS)

2. **Python**: Python 3.8+ (uses standard library only, no external dependencies)

### Build the Zig Library

PZSpec automatically builds your Zig library when needed! No build scripts required.

**Conventions (automatic):**
- Source file: `src/lib.zig` or first `.zig` file in `src/`
- Library name: Project directory name
- Output: `zig-out/lib/lib<name>.<ext>`

**Customization (optional):**

Create a `.pzspec` file in your project root to customize:

```json
{
  "library_name": "mylib",
  "source_file": "src/custom.zig",
  "optimize": "ReleaseSafe",
  "build_dir": "zig-out/lib",
  "build_flags": ["-fstack-protector"]
}
```

The library will be automatically built when you run tests if it doesn't exist.

### Install PZSpec

**Option 1: Install globally (Recommended)**
```bash
pip install -e .
# or for production:
# pip install pzspec
```

After installation, use the `pzspec` command from any directory:
```bash
cd your-project
pzspec  # Automatically finds and runs tests
```

**Option 2: Use without installation**
Just run tests directly from the PZSpec project directory:
```bash
python run_tests.py
```

## Writing Tests

PZSpec follows the RSpec convention: test files go in the `pzspec/` directory and should be named `test_*.py`.

### Basic Example

Create a file `pzspec/test_math.py`:

```python
from pzspec import ZigLibrary, describe, it, expect

# Load the Zig library
zig = ZigLibrary()

# Define test suites
with describe("Math Operations"):
    @it("should add two numbers")
    def test_add():
        result = zig.add(2, 3)
        expect(result).to_equal(5)
```

### DSL Features

The DSL provides several ways to write tests:

**Fluent API:**
```python
expect(zig.add(2, 3)).to_equal(5)
expect(zig.is_even(4)).to_be_true()
expect(zig.divide(10.0, 3.0)).to_be_almost_equal(3.333, delta=0.001)
```

**Function-based API:**
```python
from pzspec import assert_equal, assert_true

assert_equal(zig.add(2, 3), 5)
assert_true(zig.is_even(4))
```

**Test organization:**
```python
with describe("Suite Name"):
    @it("test case 1")
    def test1():
        # test code
    
    @it("test case 2")
    def test2():
        # test code
```

## Running Tests

### Using the `pzspec` command (after installation):

```bash
# From your project directory
pzspec

# From any directory
pzspec --project-root /path/to/project

# Quiet mode
pzspec --quiet
```

### Using run_tests.py (without installation):

```bash
# From PZSpec project directory
python run_tests.py

# Quiet mode
python run_tests.py --quiet
```

## How It Works

1. **Zig Compilation**: The Zig code is compiled to a shared library (`.so`, `.dylib`, or `.dll`) using the C ABI.

2. **FFI Loading**: Python's `ctypes` library loads the shared library and provides type-safe wrappers for Zig functions.

3. **Test Execution**: The Python DSL collects tests and executes them, reporting results in a readable format.

## Adding New Zig Functions

1. Add the function to `src/lib.zig` with the `export` keyword:
   ```zig
   export fn my_function(a: i32) i32 {
       return a * 2;
   }
   ```

2. The library will be automatically rebuilt when you run tests. No manual build needed!

3. Call it in your tests using `get_function()`:
   ```python
   func = zig.get_function("my_function", [ctypes.c_int32], ctypes.c_int32)
   result = func(42)
   expect(result).to_equal(84)
   ```

## Example Test Suite

See `pzspec/test_math.py` for a complete example covering:
- Basic math operations
- Array operations
- String operations
- Boolean logic
- Error handling

## Type Mapping

| Zig Type | Python/ctypes Type |
|----------|-------------------|
| `i32` | `ctypes.c_int32` |
| `i64` | `ctypes.c_int64` |
| `f64` | `ctypes.c_double` |
| `f32` | `ctypes.c_float` |
| `bool` | `ctypes.c_bool` |
| `[*:0]const u8` | `ctypes.c_char_p` |
| `[*]i32` | `ctypes.POINTER(ctypes.c_int32)` |
| `usize` | `ctypes.c_size_t` |

## Conventions

PZSpec follows convention over configuration. See [CONVENTIONS.md](CONVENTIONS.md) for details on:
- Automatic source file detection
- Library naming conventions
- Build output locations
- Configuration via `.pzspec` file

## License

MIT

## Contributing

Contributions welcome! This is a simple framework designed to be extended for your specific testing needs.

