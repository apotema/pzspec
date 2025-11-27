"""
FFI wrapper for loading and calling Zig functions via C ABI.
"""

import ctypes
import os
import platform
from pathlib import Path
from typing import Any, Callable, Optional
from .builder import auto_build


class ZigLibrary:
    """
    Wrapper for loading a Zig shared library and calling its functions.
    
    Automatically detects the correct library extension (.so, .dylib, .dll)
    based on the platform.
    """
    
    def __init__(self, library_path: Optional[str] = None, auto_build_lib: bool = True):
        """
        Initialize the Zig library loader.
        
        Args:
            library_path: Path to the shared library. If None, tries to find
                         it in common build locations or auto-builds it.
            auto_build_lib: If True, automatically build the library if not found.
        """
        if library_path is None:
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
        self._functions = {}
    
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
        """
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

