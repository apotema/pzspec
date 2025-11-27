"""
Coverage-aware builder for Zig libraries.

This module handles building Zig libraries from instrumented source code.
"""

import os
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, List

from .instrumenter import ZigInstrumenter, InstrumentationResult


class CoverageBuilder:
    """
    Builds Zig libraries with coverage instrumentation.

    This builder:
    1. Instruments Zig source files with coverage counters
    2. Builds a shared library from the instrumented sources
    3. Provides the library path for loading
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.coverage_dir = self.project_root / ".pzspec-coverage"
        self.instrumenter = ZigInstrumenter(output_dir=str(self.coverage_dir))
        self.instrumentation_results: List[InstrumentationResult] = []
        self._library_path: Optional[Path] = None

    def _get_library_extension(self) -> str:
        """Get the library extension for the current platform."""
        system = platform.system()
        if system == "Darwin":
            return ".dylib"
        elif system == "Linux":
            return ".so"
        elif system == "Windows":
            return ".dll"
        return ".so"

    def find_source_files(self) -> List[Path]:
        """Find Zig source files in the project."""
        src_dir = self.project_root / "src"
        if src_dir.exists():
            return list(src_dir.glob("**/*.zig"))

        # Also check for .zig files in project root
        return list(self.project_root.glob("*.zig"))

    def instrument(self) -> List[InstrumentationResult]:
        """Instrument all Zig source files."""
        source_files = self.find_source_files()

        if not source_files:
            return []

        # Create coverage directory
        self.coverage_dir.mkdir(parents=True, exist_ok=True)

        # Copy directory structure and instrument files
        for source_file in source_files:
            # Preserve relative path structure
            rel_path = source_file.relative_to(self.project_root)
            output_dir = self.coverage_dir / rel_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Instrument the file
            self.instrumenter.output_dir = str(output_dir)
            result = self.instrumenter.instrument_file(str(source_file))
            self.instrumentation_results.append(result)

        return self.instrumentation_results

    def build(self, library_name: Optional[str] = None) -> Optional[Path]:
        """
        Build the instrumented library.

        Args:
            library_name: Name for the library (default: project directory name)

        Returns:
            Path to the built library, or None if build failed
        """
        if not self.instrumentation_results:
            print("No instrumented files. Call instrument() first.")
            return None

        if library_name is None:
            library_name = self.project_root.name

        ext = self._get_library_extension()
        lib_filename = f"lib{library_name}_coverage{ext}"
        output_path = self.coverage_dir / lib_filename

        # Find the main source file in coverage directory
        # Prefer lib.zig or the first .zig file
        coverage_src = self.coverage_dir / "src"
        if coverage_src.exists():
            lib_zig = coverage_src / "lib.zig"
            if lib_zig.exists():
                main_source = lib_zig
            else:
                zig_files = list(coverage_src.glob("*.zig"))
                if zig_files:
                    main_source = zig_files[0]
                else:
                    print("No Zig source found in coverage directory")
                    return None
        else:
            # Check for files directly in coverage dir
            zig_files = list(self.coverage_dir.glob("*.zig"))
            if zig_files:
                main_source = zig_files[0]
            else:
                print("No Zig source found in coverage directory")
                return None

        # Build command
        cmd = [
            "zig", "build-lib",
            "-dynamic",
            "-O", "Debug",  # Debug for better coverage accuracy
            "-fPIC",
            str(main_source),
            "--name", f"{library_name}_coverage",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.coverage_dir),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                return None

            # Find the built library
            # Zig might put it in the coverage dir
            possible_locations = [
                self.coverage_dir / lib_filename,
                self.coverage_dir / f"lib{library_name}_coverage{ext}",
            ]

            for loc in possible_locations:
                if loc.exists():
                    self._library_path = loc
                    return loc

            # Check if it was created with different name
            for lib in self.coverage_dir.glob(f"*{ext}"):
                self._library_path = lib
                return lib

            print(f"Library not found after build. Expected: {output_path}")
            return None

        except FileNotFoundError:
            print("Error: 'zig' command not found. Is Zig installed?")
            return None

    def get_library_path(self) -> Optional[Path]:
        """Get path to the built coverage library."""
        return self._library_path

    def cleanup(self):
        """Remove all coverage files and directories."""
        if self.coverage_dir.exists():
            shutil.rmtree(self.coverage_dir)

        self.instrumentation_results = []
        self._library_path = None
