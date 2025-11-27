"""
FFI wrapper for loading and calling Zig functions via C ABI.
"""

import ctypes
import os
import platform
import re
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List
from .builder import auto_build, ZigBuilder, PZSpecConfig


# Mapping from Zig type names to ctypes types
ZIG_TO_CTYPES: Dict[str, Any] = {
    # Signed integers
    "i8": ctypes.c_int8,
    "i16": ctypes.c_int16,
    "i32": ctypes.c_int32,
    "i64": ctypes.c_int64,
    # Unsigned integers
    "u8": ctypes.c_uint8,
    "u16": ctypes.c_uint16,
    "u32": ctypes.c_uint32,
    "u64": ctypes.c_uint64,
    "usize": ctypes.c_size_t,
    "isize": ctypes.c_ssize_t,
    # Floats
    "f32": ctypes.c_float,
    "f64": ctypes.c_double,
    # Boolean
    "bool": ctypes.c_bool,
    # Void
    "void": None,
    # C string (null-terminated)
    "[*:0]const u8": ctypes.c_char_p,
    "[*:0]u8": ctypes.c_char_p,
}


def parse_zig_type(type_str: str, struct_registry: Optional[Dict[str, type]] = None) -> Any:
    """
    Parse a Zig type string and return the corresponding ctypes type.

    Args:
        type_str: Zig type string (e.g., "i32", "*const Vec2", "f32")
        struct_registry: Optional dict mapping struct names to ctypes.Structure classes

    Returns:
        ctypes type or None for void
    """
    type_str = type_str.strip()

    # Check direct mapping first
    if type_str in ZIG_TO_CTYPES:
        return ZIG_TO_CTYPES[type_str]

    # Handle pointers
    if type_str.startswith("*"):
        # *const T or *T
        inner = type_str[1:]
        if inner.startswith("const "):
            inner = inner[6:]
        inner_type = parse_zig_type(inner, struct_registry)
        if inner_type is not None:
            return ctypes.POINTER(inner_type)
        return ctypes.c_void_p

    # Handle [*] pointers (many-pointers)
    if type_str.startswith("[*]"):
        inner = type_str[3:]
        if inner.startswith("const "):
            inner = inner[6:]
        inner_type = parse_zig_type(inner, struct_registry)
        if inner_type is not None:
            return ctypes.POINTER(inner_type)
        return ctypes.c_void_p

    # Handle optional pointers
    if type_str.startswith("?*"):
        inner = type_str[2:]
        if inner.startswith("const "):
            inner = inner[6:]
        inner_type = parse_zig_type(inner, struct_registry)
        if inner_type is not None:
            return ctypes.POINTER(inner_type)
        return ctypes.c_void_p

    # Check struct registry
    if struct_registry and type_str in struct_registry:
        return struct_registry[type_str]

    # Try to extract struct name from qualified path (e.g., "vector.Vec2")
    if "." in type_str:
        parts = type_str.split(".")
        struct_name = parts[-1]
        if struct_registry and struct_name in struct_registry:
            return struct_registry[struct_name]

    # Unknown type - return void pointer as fallback
    return ctypes.c_void_p


class ZigLibrary:
    """
    Wrapper for loading a Zig shared library and calling its functions.

    Automatically detects the correct library extension (.so, .dylib, .dll)
    based on the platform.

    Supports automatic function discovery when the library is built with
    pzspec_exports.zig, which embeds type metadata.
    """

    def __init__(
        self,
        library_path: Optional[str] = None,
        auto_build_lib: bool = True,
        struct_registry: Optional[Dict[str, type]] = None,
    ):
        """
        Initialize the Zig library loader.

        Args:
            library_path: Path to the shared library. If None, tries to find
                         it in common build locations or auto-builds it.
            auto_build_lib: If True, automatically build the library if not found.
            struct_registry: Optional dict mapping struct names to ctypes.Structure
                           classes. Used for auto-binding functions with struct params.

        Environment Variables:
            PZSPEC_COVERAGE_LIB: If set, use this library path (for coverage mode)
        """
        # Check for coverage library override
        coverage_lib = os.environ.get('PZSPEC_COVERAGE_LIB')
        if coverage_lib and os.path.exists(coverage_lib):
            library_path = coverage_lib
        elif library_path is None:
            # Try to find library first
            try:
                library_path = self._find_library()
            except FileNotFoundError:
                # Library not found, try auto-build if enabled
                if auto_build_lib:
                    print("Library not found, attempting auto-build...")
                    built_path = auto_build()
                    if built_path:
                        library_path = str(built_path)
                    else:
                        # Try finding again after build
                        try:
                            library_path = self._find_library()
                        except FileNotFoundError:
                            pass

        if not library_path or not os.path.exists(library_path):
            raise FileNotFoundError(
                f"Zig library not found. "
                "Make sure to build the Zig code first, or enable auto-build. "
                "Expected locations: zig-out/lib/, build/, or project root."
            )

        self.lib_path = library_path
        self._lib = ctypes.CDLL(library_path)
        self._functions: Dict[str, Callable] = {}
        self._metadata: Optional[Dict[str, Any]] = None
        self._struct_registry: Dict[str, type] = struct_registry or {}
        self._auto_bound: Dict[str, Callable] = {}

        # Try to load metadata
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Try to load function metadata from the library or metadata file."""
        project_root = Path.cwd()
        builder = ZigBuilder(project_root)

        # Try embedded metadata first (from __pzspec_metadata function)
        self._metadata = builder.extract_metadata()

        # Fall back to metadata file
        if not self._metadata:
            self._metadata = builder.load_metadata()

        # Auto-bind discovered functions
        if self._metadata and "functions" in self._metadata:
            self._auto_bind_functions()

    def _auto_bind_functions(self) -> None:
        """Auto-bind functions from metadata."""
        if not self._metadata or "functions" not in self._metadata:
            return

        for func_info in self._metadata["functions"]:
            name = func_info.get("name", "")
            params = func_info.get("params", [])
            return_type = func_info.get("return", "void")

            if not name:
                continue

            # Parse types
            argtypes = [
                parse_zig_type(p, self._struct_registry)
                for p in params
            ]
            restype = parse_zig_type(return_type, self._struct_registry)

            # Create bound function
            try:
                func = getattr(self._lib, name)
                func.argtypes = argtypes
                func.restype = restype
                self._auto_bound[name] = func
            except AttributeError:
                # Function not found in library
                pass

    def register_struct(self, name: str, struct_class: type) -> None:
        """
        Register a ctypes.Structure class for use in auto-binding.

        Args:
            name: The Zig struct name (e.g., "Vec2")
            struct_class: The ctypes.Structure subclass
        """
        self._struct_registry[name] = struct_class
        # Re-bind functions that might use this struct
        if self._metadata:
            self._auto_bind_functions()

    def register_structs(self, structs: Dict[str, type]) -> None:
        """
        Register multiple ctypes.Structure classes.

        Args:
            structs: Dict mapping Zig struct names to ctypes.Structure subclasses
        """
        self._struct_registry.update(structs)
        if self._metadata:
            self._auto_bind_functions()

    def get_discovered_functions(self) -> List[str]:
        """
        Get list of auto-discovered function names.

        Returns:
            List of function names that were auto-discovered from metadata.
        """
        return list(self._auto_bound.keys())

    def has_metadata(self) -> bool:
        """Check if the library has embedded metadata."""
        return self._metadata is not None

    def __getattr__(self, name: str) -> Callable:
        """
        Allow calling auto-discovered functions as attributes.

        Example:
            zig = ZigLibrary()
            result = zig.vec2_add(a, b)  # If vec2_add was auto-discovered
        """
        # Check auto-bound functions first
        if name in self._auto_bound:
            return self._auto_bound[name]

        # Fall back to direct library access (for manually exported functions)
        if hasattr(self._lib, name):
            return getattr(self._lib, name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            f"Function '{name}' not found in library. "
            f"Auto-discovered functions: {list(self._auto_bound.keys())}"
        )
    
    def _find_library(self) -> str:
        """Try to find the library in common build locations."""
        from .builder import PZSpecConfig
        
        system = platform.system()
        
        if system == "Darwin":
            ext = ".dylib"
        elif system == "Linux":
            ext = ".so"
        elif system == "Windows":
            ext = ".dll"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
        
        # Try to use project config to find library
        project_root = Path.cwd()
        config = PZSpecConfig(project_root)
        lib_name = config.library_name
        build_dir = config.build_dir
        
        # Try configured location first
        configured_path = build_dir / f"lib{lib_name}{ext}"
        if configured_path.exists():
            return str(configured_path)
        
        # Fallback to common build locations
        possible_paths = [
            f"zig-out/lib/lib{lib_name}{ext}",
            f"zig-out/lib/{lib_name}{ext}",
            f"build/lib{lib_name}{ext}",
            f"lib{lib_name}{ext}",
            # Also try default names for backward compatibility
            f"zig-out/lib/libziglib{ext}",
            f"zig-out/lib/ziglib{ext}",
        ]
        
        for path in possible_paths:
            full_path = project_root / path if not os.path.isabs(path) else Path(path)
            if full_path.exists():
                return str(full_path)
        
        raise FileNotFoundError(
            f"Could not find Zig library. Tried: {possible_paths}. "
            "Build the library first with: zig build"
        )
    
    def get_function(self, name: str, argtypes: list, restype: Any) -> Callable:
        """
        Get a function from the Zig library with proper type annotations.

        Args:
            name: Function name as exported from Zig
            argtypes: List of ctypes types for arguments
            restype: Return type (ctypes type)

        Returns:
            Callable function that can be invoked

        Note:
            If the function is currently mocked (via mock_zig_function),
            a mock wrapper is returned instead of the actual function.
        """
        # Check if function is mocked
        from .mock import get_mock_registry, MockFunction
        registry = get_mock_registry()
        if registry.is_mocked(name):
            return MockFunction(name, argtypes, restype)

        if name not in self._functions:
            func = getattr(self._lib, name)
            func.argtypes = argtypes
            func.restype = restype
            self._functions[name] = func

        return self._functions[name]
    
    # Convenience methods for common types
    def add(self, a: int, b: int) -> int:
        """Call the Zig 'add' function."""
        func = self.get_function("add", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        return func(a, b)
    
    def multiply(self, a: int, b: int) -> int:
        """Call the Zig 'multiply' function."""
        func = self.get_function("multiply", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        return func(a, b)
    
    def subtract(self, a: int, b: int) -> int:
        """Call the Zig 'subtract' function."""
        func = self.get_function("subtract", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        return func(a, b)
    
    def divide(self, a: float, b: float) -> float:
        """Call the Zig 'divide' function."""
        func = self.get_function("divide", [ctypes.c_double, ctypes.c_double], ctypes.c_double)
        return func(a, b)
    
    def is_even(self, n: int) -> bool:
        """Call the Zig 'is_even' function."""
        func = self.get_function("is_even", [ctypes.c_int32], ctypes.c_bool)
        return func(n)
    
    def string_length(self, s: str) -> int:
        """Call the Zig 'string_length' function."""
        func = self.get_function("string_length", [ctypes.c_char_p], ctypes.c_size_t)
        return func(s.encode('utf-8'))
    
    def sum_array(self, arr: list[int]) -> int:
        """Call the Zig 'sum_array' function."""
        arr_type = ctypes.c_int32 * len(arr)
        arr_c = arr_type(*arr)
        func = self.get_function("sum_array", [ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t], ctypes.c_int32)
        return func(arr_c, len(arr))
    
    def reverse_array(self, arr: list[int]) -> list[int]:
        """Call the Zig 'reverse_array' function (modifies array in place)."""
        arr_type = ctypes.c_int32 * len(arr)
        arr_c = arr_type(*arr)
        func = self.get_function("reverse_array", [ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t], None)
        func(arr_c, len(arr))
        return list(arr_c)

