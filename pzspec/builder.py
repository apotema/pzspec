"""
Automatic build system for Zig libraries in PZSpec projects.

Follows conventions to automatically build shared libraries without requiring
manual build scripts.
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import json


class PZSpecConfig:
    """Configuration for a PZSpec project."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_file = project_root / ".pzspec"
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from .pzspec file if it exists."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not parse .pzspec file: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    @property
    def library_name(self) -> str:
        """Get the library name, defaulting to project directory name."""
        return self.get("library_name", self.project_root.name)
    
    @property
    def source_file(self) -> Optional[Path]:
        """Get the source file path."""
        source = self.get("source_file")
        if source:
            return self.project_root / source
        # Convention: look for src/*.zig or src/lib.zig
        src_dir = self.project_root / "src"
        if src_dir.exists():
            # Prefer lib.zig, then any .zig file
            lib_zig = src_dir / "lib.zig"
            if lib_zig.exists():
                return lib_zig
            zig_files = list(src_dir.glob("*.zig"))
            if zig_files:
                return zig_files[0]
        return None
    
    @property
    def optimize(self) -> str:
        """Get optimization level."""
        return self.get("optimize", "ReleaseSafe")
    
    @property
    def build_dir(self) -> Path:
        """Get build output directory."""
        build_dir = self.get("build_dir", "zig-out/lib")
        return self.project_root / build_dir


class ZigBuilder:
    """Automatic builder for Zig shared libraries."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.config = PZSpecConfig(self.project_root)
    
    def _get_library_extension(self) -> str:
        """Get the library extension for the current platform."""
        system = platform.system()
        if system == "Darwin":
            return ".dylib"
        elif system == "Linux":
            return ".so"
        elif system == "Windows":
            return ".dll"
        else:
            return ".so"  # Default
    
    def _get_library_path(self) -> Path:
        """Get the expected library path."""
        ext = self._get_library_extension()
        lib_name = f"lib{self.config.library_name}{ext}"
        build_dir = self.config.build_dir
        # Handle relative paths
        if not build_dir.is_absolute():
            build_dir = self.project_root / build_dir
        return build_dir / lib_name
    
    def library_exists(self) -> bool:
        """Check if the library already exists."""
        return self._get_library_path().exists()
    
    def build(self, force: bool = False) -> bool:
        """
        Build the Zig shared library.
        
        Args:
            force: If True, rebuild even if library exists
        
        Returns:
            True if build succeeded, False otherwise
        """
        if not force and self.library_exists():
            return True
        
        source_file = self.config.source_file
        if not source_file or not source_file.exists():
            print(f"Error: Source file not found: {source_file}")
            print("  Convention: Place Zig source in src/lib.zig or src/*.zig")
            print("  Or specify 'source_file' in .pzspec")
            return False
        
        # Ensure build directory exists
        self.config.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Build command
        ext = self._get_library_extension()
        lib_name = f"lib{self.config.library_name}{ext}"
        output_path = self.config.build_dir / lib_name
        
        cmd = [
            "zig", "build-lib",
            "-dynamic",
            "-O", self.config.optimize,
            "-fPIC",
            str(source_file),
            "--name", self.config.library_name,
        ]
        
        # Add custom build flags if specified
        extra_flags = self.config.get("build_flags", [])
        if extra_flags:
            cmd.extend(extra_flags)
        
        try:
            print(f"Building {lib_name}...")
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True
            )
            
            # Move library to expected location if needed
            # Zig might create it in current directory
            current_dir_lib = self.project_root / lib_name
            if current_dir_lib.exists() and current_dir_lib != output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                current_dir_lib.rename(output_path)
                print(f"  → {output_path}")
            
            # Also check for liblib.* fallback
            fallback_pattern = f"liblib.{ext[1:]}"  # Remove leading dot
            fallback_lib = self.project_root / fallback_pattern
            if fallback_lib.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                fallback_lib.rename(output_path)
                print(f"  → {output_path} (renamed from {fallback_pattern})")
            
            if output_path.exists():
                print(f"✓ Built successfully: {output_path}")
                return True
            else:
                print(f"Warning: Library not found at expected location: {output_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Error building library:")
            print(e.stderr)
            return False
        except FileNotFoundError:
            print("Error: 'zig' command not found. Is Zig installed?")
            return False
    
    def get_library_path(self) -> Optional[Path]:
        """Get the path to the built library."""
        if self.library_exists():
            return self._get_library_path()
        return None


def auto_build(project_root: Optional[Path] = None) -> Optional[Path]:
    """
    Automatically build Zig library if needed.
    
    Args:
        project_root: Root directory of the project. If None, uses current directory.
    
    Returns:
        Path to the built library, or None if build failed/not needed.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    builder = ZigBuilder(project_root)
    
    if not builder.library_exists():
        if not builder.build():
            return None
    
    return builder.get_library_path()

