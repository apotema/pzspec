"""
Zig source code instrumenter for coverage tracking.

This module transforms Zig source code by injecting coverage tracking calls
that can be read from Python via FFI.
"""

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .parser import ZigParser, ParseResult, CoveragePoint, CoveragePointType


@dataclass
class InstrumentationResult:
    """Result of instrumenting a Zig source file."""
    original_path: str
    instrumented_path: str
    parse_result: ParseResult
    coverage_points: List[CoveragePoint]
    counter_count: int


class ZigInstrumenter:
    """
    Instruments Zig source code with coverage tracking.

    The instrumentation strategy:
    1. Add a global coverage counter array
    2. Export functions to access/reset the counters
    3. Insert counter increment calls at coverage points
    """

    # Template for the coverage runtime that gets added to instrumented files
    COVERAGE_RUNTIME = '''
// PZSpec Coverage Runtime
// This code is automatically generated - do not edit

var __pzspec_coverage_counters: [{count}]u64 = [_]u64{{0}} ** {count};
var __pzspec_coverage_initialized: bool = false;

export fn __pzspec_coverage_get_counter(index: u32) u64 {{
    if (index >= {count}) return 0;
    return __pzspec_coverage_counters[index];
}}

export fn __pzspec_coverage_get_count() u32 {{
    return {count};
}}

export fn __pzspec_coverage_reset() void {{
    for (&__pzspec_coverage_counters) |*counter| {{
        counter.* = 0;
    }}
}}

inline fn __pzspec_cov(comptime index: u32) void {{
    if (index < {count}) {{
        __pzspec_coverage_counters[index] += 1;
    }}
}}

// End PZSpec Coverage Runtime

'''

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the instrumenter.

        Args:
            output_dir: Directory to write instrumented files.
                       If None, creates a .pzspec-coverage directory.
        """
        self.parser = ZigParser()
        self.output_dir = output_dir
        self.results: Dict[str, InstrumentationResult] = {}

    def instrument_file(self, file_path: str) -> InstrumentationResult:
        """
        Instrument a single Zig source file.

        Args:
            file_path: Path to the Zig source file

        Returns:
            InstrumentationResult with details about the instrumentation
        """
        file_path = os.path.abspath(file_path)

        # Read original source
        with open(file_path, 'r') as f:
            source = f.read()

        # Parse the source
        parse_result = self.parser.parse(source, file_path)

        # Determine output path
        if self.output_dir:
            output_dir = Path(self.output_dir)
        else:
            output_dir = Path(file_path).parent / '.pzspec-coverage'

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / Path(file_path).name

        # Instrument the source
        instrumented_source, coverage_points = self._instrument_source(
            source, parse_result
        )

        # Write instrumented source
        with open(output_path, 'w') as f:
            f.write(instrumented_source)

        result = InstrumentationResult(
            original_path=file_path,
            instrumented_path=str(output_path),
            parse_result=parse_result,
            coverage_points=coverage_points,
            counter_count=len(coverage_points),
        )

        self.results[file_path] = result
        return result

    def instrument_directory(self, dir_path: str) -> List[InstrumentationResult]:
        """
        Instrument all Zig files in a directory.

        Args:
            dir_path: Path to directory containing Zig files

        Returns:
            List of InstrumentationResult for each file
        """
        results = []
        dir_path = Path(dir_path)

        for zig_file in dir_path.glob('**/*.zig'):
            # Skip already instrumented files
            if '.pzspec-coverage' in str(zig_file):
                continue

            result = self.instrument_file(str(zig_file))
            results.append(result)

        return results

    def _instrument_source(
        self, source: str, parse_result: ParseResult
    ) -> Tuple[str, List[CoveragePoint]]:
        """
        Add coverage instrumentation to source code.

        Returns:
            (instrumented_source, coverage_points)
        """
        coverage_points = parse_result.coverage_points
        if not coverage_points:
            # No coverage points found, return original
            return source, []

        lines = source.split('\n')

        # Assign IDs to coverage points
        for i, point in enumerate(coverage_points):
            point.id = i

        # Group coverage points by line for efficient insertion
        points_by_line: Dict[int, List[CoveragePoint]] = {}
        for point in coverage_points:
            if point.line not in points_by_line:
                points_by_line[point.line] = []
            points_by_line[point.line].append(point)

        # Insert coverage calls (work backwards to preserve line numbers)
        for line_num in sorted(points_by_line.keys(), reverse=True):
            points = points_by_line[line_num]
            line_idx = line_num - 1

            if line_idx >= len(lines):
                continue

            line = lines[line_idx]

            for point in sorted(points, key=lambda p: p.column, reverse=True):
                if point.type == CoveragePointType.FUNCTION_ENTRY:
                    # Insert coverage call at the start of function body
                    # Find the opening brace and insert after it
                    lines[line_idx] = self._insert_function_coverage(
                        line, point.id
                    )
                elif point.type in (
                    CoveragePointType.BRANCH_IF,
                    CoveragePointType.BRANCH_ELSE,
                    CoveragePointType.BRANCH_SWITCH,
                ):
                    # Insert coverage call before the branch
                    lines[line_idx] = self._insert_branch_coverage(
                        line, point.column, point.id
                    )

        # Add coverage runtime at the top (after imports)
        runtime = self.COVERAGE_RUNTIME.format(count=len(coverage_points))
        instrumented_lines = self._insert_runtime(lines, runtime)

        return '\n'.join(instrumented_lines), coverage_points

    def _insert_runtime(self, lines: List[str], runtime: str) -> List[str]:
        """Insert the coverage runtime after imports."""
        # Find the last import line
        last_import = -1
        for i, line in enumerate(lines):
            if '@import' in line:
                last_import = i

        # Insert runtime after imports
        insert_pos = last_import + 1 if last_import >= 0 else 0

        result = lines[:insert_pos]
        result.append('')
        result.extend(runtime.split('\n'))
        result.extend(lines[insert_pos:])

        return result

    def _insert_function_coverage(self, line: str, point_id: int) -> str:
        """Insert coverage call at function entry."""
        # Find the opening brace
        brace_pos = line.find('{')
        if brace_pos == -1:
            return line

        # Insert coverage call after the brace
        call = f' __pzspec_cov({point_id});'
        return line[:brace_pos + 1] + call + line[brace_pos + 1:]

    def _insert_branch_coverage(
        self, line: str, column: int, point_id: int
    ) -> str:
        """Insert coverage call before a branch."""
        # For branches, we wrap the condition
        # This is tricky - for now, we'll add a block before
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        # Simple approach: add coverage call on the same line before the branch
        # This works for simple cases
        if 'if (' in line or 'if(' in line:
            # Insert before the if
            match = re.search(r'\bif\s*\(', line)
            if match:
                pos = match.start()
                call = f'{{ __pzspec_cov({point_id}); }} '
                return line[:pos] + call + line[pos:]

        return line

    def get_coverage_points(self) -> Dict[str, List[CoveragePoint]]:
        """Get all coverage points organized by file."""
        return {
            path: result.coverage_points
            for path, result in self.results.items()
        }

    def cleanup(self):
        """Remove instrumented files."""
        for result in self.results.values():
            instrumented_path = Path(result.instrumented_path)
            if instrumented_path.exists():
                instrumented_path.unlink()

            # Remove the coverage directory if empty
            coverage_dir = instrumented_path.parent
            if coverage_dir.name == '.pzspec-coverage' and coverage_dir.exists():
                try:
                    coverage_dir.rmdir()
                except OSError:
                    pass  # Directory not empty
