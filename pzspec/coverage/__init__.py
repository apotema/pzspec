"""
PZSpec Coverage - Source-level code coverage for Zig code.

This module provides code coverage tracking for Zig code tested through PZSpec.
It works by instrumenting Zig source code with coverage counters that are
accessible via FFI.
"""

from .instrumenter import ZigInstrumenter
from .collector import CoverageCollector
from .report import CoverageReport, CoverageData
from .builder import CoverageBuilder

__all__ = [
    "ZigInstrumenter",
    "CoverageCollector",
    "CoverageReport",
    "CoverageData",
    "CoverageBuilder",
]
