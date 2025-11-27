"""
PZSpec Zig helpers - Zig source files for automatic FFI export generation.

This package contains Zig source files that can be imported into your Zig
project to automatically export C-compatible functions for PZSpec testing.

Usage:
    Copy pzspec_exports.zig to your project, or add the pzspec/zig directory
    to your Zig build's module paths.
"""

from pathlib import Path


def get_exports_path() -> Path:
    """Get the path to pzspec_exports.zig."""
    return Path(__file__).parent / "pzspec_exports.zig"


__all__ = ["get_exports_path"]
