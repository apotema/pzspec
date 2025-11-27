# PZSpec Conventions

PZSpec follows a set of conventions inspired by RSpec to minimize configuration and make testing Zig code as simple as possible.

## Directory Structure

```
your-project/
├── src/              # Zig source files
│   └── lib.zig       # Main library (or any .zig file)
├── pzspec/           # Test files (RSpec convention)
│   └── test_*.py     # Test files
└── .pzspec           # Optional configuration file
```

**Note:** No `run_tests.py` needed! Use the global `pzspec` command after installation.

## Automatic Conventions

PZSpec automatically detects the following without any configuration:

### Source File
- Looks for `src/lib.zig` first
- Falls back to first `.zig` file in `src/` directory
- Can be overridden in `.pzspec`

### Library Name
- Defaults to project directory name
- Can be overridden in `.pzspec`

### Build Output
- Default: `zig-out/lib/lib<name>.<ext>`
- Extension: `.dylib` (macOS), `.so` (Linux), `.dll` (Windows)
- Can be customized in `.pzspec`

### Optimization
- Default: `ReleaseSafe`
- Can be changed in `.pzspec`

## Configuration File (.pzspec)

Create a `.pzspec` file in your project root to customize any of the conventions:

```json
{
  "library_name": "mylib",
  "source_file": "src/custom.zig",
  "optimize": "ReleaseSafe",
  "build_dir": "zig-out/lib",
  "build_flags": ["-fstack-protector", "-march=native"]
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `library_name` | Project directory name | Name of the shared library |
| `source_file` | `src/lib.zig` or first `.zig` in `src/` | Path to Zig source file (relative to project root) |
| `optimize` | `ReleaseSafe` | Optimization level: `Debug`, `ReleaseSafe`, `ReleaseFast`, `ReleaseSmall` |
| `build_dir` | `zig-out/lib` | Output directory for built library |
| `build_flags` | `[]` | Additional flags to pass to `zig build-lib` |

## Auto-Build

PZSpec automatically builds your Zig library when:
1. Tests are run and the library doesn't exist
2. `ZigLibrary()` is instantiated without a library path

To disable auto-build:
```python
zig = ZigLibrary(auto_build_lib=False)
```

## Test File Naming

- Test files must be in `pzspec/` directory
- Test files must start with `test_` (e.g., `test_math.py`, `test_vectors.py`)
- Framework files (`dsl.py`, `test_runner.py`, etc.) are automatically excluded

## Example: Minimal Project

```
my-project/
├── src/
│   └── lib.zig          # Your Zig code
└── pzspec/
    └── test_basic.py    # Your tests
```

That's it! No build scripts, no run_tests.py, no configuration needed. Just:
1. Install PZSpec: `pip install -e /path/to/pzspec` (or globally)
2. Write your Zig code in `src/`
3. Write your tests in `pzspec/`
4. Run `pzspec` from your project directory

The library will be built automatically when you run tests.

