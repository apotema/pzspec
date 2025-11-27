"""
Coverage data collector for reading coverage counters from instrumented Zig code.
"""

import ctypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import CoveragePoint, CoveragePointType
from .instrumenter import InstrumentationResult


@dataclass
class CoverageData:
    """Coverage data for a single file."""
    file_path: str
    coverage_points: List[CoveragePoint]
    hit_counts: Dict[int, int] = field(default_factory=dict)

    @property
    def total_points(self) -> int:
        """Total number of coverage points."""
        return len(self.coverage_points)

    @property
    def covered_points(self) -> int:
        """Number of coverage points that were hit."""
        return sum(1 for count in self.hit_counts.values() if count > 0)

    @property
    def coverage_percent(self) -> float:
        """Coverage percentage."""
        if self.total_points == 0:
            return 100.0
        return (self.covered_points / self.total_points) * 100

    @property
    def functions_covered(self) -> int:
        """Number of functions that were called."""
        return sum(
            1 for point in self.coverage_points
            if point.type == CoveragePointType.FUNCTION_ENTRY
            and self.hit_counts.get(point.id, 0) > 0
        )

    @property
    def total_functions(self) -> int:
        """Total number of functions."""
        return sum(
            1 for point in self.coverage_points
            if point.type == CoveragePointType.FUNCTION_ENTRY
        )

    @property
    def branches_covered(self) -> int:
        """Number of branches that were taken."""
        branch_types = {
            CoveragePointType.BRANCH_IF,
            CoveragePointType.BRANCH_ELSE,
            CoveragePointType.BRANCH_SWITCH,
        }
        return sum(
            1 for point in self.coverage_points
            if point.type in branch_types
            and self.hit_counts.get(point.id, 0) > 0
        )

    @property
    def total_branches(self) -> int:
        """Total number of branches."""
        branch_types = {
            CoveragePointType.BRANCH_IF,
            CoveragePointType.BRANCH_ELSE,
            CoveragePointType.BRANCH_SWITCH,
        }
        return sum(
            1 for point in self.coverage_points
            if point.type in branch_types
        )

    def get_uncovered_functions(self) -> List[CoveragePoint]:
        """Get list of functions that were not called."""
        return [
            point for point in self.coverage_points
            if point.type == CoveragePointType.FUNCTION_ENTRY
            and self.hit_counts.get(point.id, 0) == 0
        ]

    def get_covered_lines(self) -> List[int]:
        """Get list of lines that were covered."""
        return sorted(set(
            point.line for point in self.coverage_points
            if self.hit_counts.get(point.id, 0) > 0
        ))

    def get_uncovered_lines(self) -> List[int]:
        """Get list of lines that were not covered."""
        return sorted(set(
            point.line for point in self.coverage_points
            if self.hit_counts.get(point.id, 0) == 0
        ))


class CoverageCollector:
    """
    Collects coverage data from instrumented Zig libraries.

    This class interfaces with the coverage counters embedded in
    instrumented Zig code via FFI.
    """

    def __init__(self):
        self.instrumentation_results: Dict[str, InstrumentationResult] = {}
        self.coverage_data: Dict[str, CoverageData] = {}
        self._library: Optional[ctypes.CDLL] = None

    def register_instrumentation(self, result: InstrumentationResult):
        """Register an instrumentation result for later collection."""
        self.instrumentation_results[result.original_path] = result

    def set_library(self, library: ctypes.CDLL):
        """Set the loaded Zig library to collect coverage from."""
        self._library = library

    def collect(self) -> Dict[str, CoverageData]:
        """
        Collect coverage data from the instrumented library.

        Returns:
            Dictionary mapping file paths to their coverage data
        """
        if self._library is None:
            raise RuntimeError("No library set. Call set_library() first.")

        # Get the coverage functions from the library
        # Note: We use getattr() because __pzspec names would trigger Python's
        # name mangling if accessed as attributes directly
        try:
            get_counter = getattr(self._library, '__pzspec_coverage_get_counter')
            get_counter.argtypes = [ctypes.c_uint32]
            get_counter.restype = ctypes.c_uint64

            get_count = getattr(self._library, '__pzspec_coverage_get_count')
            get_count.argtypes = []
            get_count.restype = ctypes.c_uint32

            total_counters = get_count()
        except AttributeError:
            # Library was not instrumented
            return {}

        # Build global list of coverage points with their file mapping
        all_points: List[tuple] = []  # (file_path, point)
        for file_path, result in self.instrumentation_results.items():
            for point in result.coverage_points:
                all_points.append((file_path, point))

        # Collect counter values
        counter_values = {}
        for i in range(min(total_counters, len(all_points))):
            counter_values[i] = get_counter(i)

        # Build coverage data per file
        self.coverage_data = {}
        for file_path, result in self.instrumentation_results.items():
            data = CoverageData(
                file_path=file_path,
                coverage_points=list(result.coverage_points),  # Ensure it's a list
            )

            for point in result.coverage_points:
                data.hit_counts[point.id] = counter_values.get(point.id, 0)

            self.coverage_data[file_path] = data

        return self.coverage_data

    def reset(self):
        """Reset coverage counters in the library."""
        if self._library is None:
            return

        try:
            reset_fn = getattr(self._library, '__pzspec_coverage_reset')
            reset_fn.argtypes = []
            reset_fn.restype = None
            reset_fn()
        except AttributeError:
            pass  # Library was not instrumented

    def get_summary(self) -> Dict:
        """
        Get a summary of coverage data.

        Returns:
            Dictionary with coverage summary statistics
        """
        if not self.coverage_data:
            return {
                'total_files': 0,
                'total_points': 0,
                'covered_points': 0,
                'coverage_percent': 0.0,
                'total_functions': 0,
                'covered_functions': 0,
                'total_branches': 0,
                'covered_branches': 0,
            }

        total_points = sum(d.total_points for d in self.coverage_data.values())
        covered_points = sum(d.covered_points for d in self.coverage_data.values())
        total_functions = sum(d.total_functions for d in self.coverage_data.values())
        covered_functions = sum(d.functions_covered for d in self.coverage_data.values())
        total_branches = sum(d.total_branches for d in self.coverage_data.values())
        covered_branches = sum(d.branches_covered for d in self.coverage_data.values())

        return {
            'total_files': len(self.coverage_data),
            'total_points': total_points,
            'covered_points': covered_points,
            'coverage_percent': (covered_points / total_points * 100) if total_points > 0 else 0.0,
            'total_functions': total_functions,
            'covered_functions': covered_functions,
            'function_coverage_percent': (covered_functions / total_functions * 100) if total_functions > 0 else 0.0,
            'total_branches': total_branches,
            'covered_branches': covered_branches,
            'branch_coverage_percent': (covered_branches / total_branches * 100) if total_branches > 0 else 0.0,
        }
