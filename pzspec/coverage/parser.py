"""
Zig source code parser for identifying coverage points.

This is a lightweight parser that identifies:
- Function definitions (pub fn, fn, export fn)
- Branch points (if, else, switch cases)
- Executable lines
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class CoveragePointType(Enum):
    """Types of coverage points we track."""
    FUNCTION_ENTRY = "function"
    BRANCH_IF = "branch_if"
    BRANCH_ELSE = "branch_else"
    BRANCH_SWITCH = "branch_switch"
    LINE = "line"


@dataclass
class CoveragePoint:
    """A point in the source code that can be covered."""
    type: CoveragePointType
    line: int
    column: int
    name: str  # Function name or branch description
    file: str
    id: int = 0  # Assigned during instrumentation


@dataclass
class ZigFunction:
    """Represents a Zig function."""
    name: str
    line: int
    column: int
    is_public: bool
    is_export: bool
    body_start: int  # Line where body starts (after {)
    body_end: int  # Line where body ends (})


@dataclass
class ZigBranch:
    """Represents a branch point in Zig code."""
    type: CoveragePointType
    line: int
    column: int
    parent_function: str


@dataclass
class ParseResult:
    """Result of parsing a Zig source file."""
    file_path: str
    functions: List[ZigFunction] = field(default_factory=list)
    branches: List[ZigBranch] = field(default_factory=list)
    coverage_points: List[CoveragePoint] = field(default_factory=list)
    total_lines: int = 0
    executable_lines: List[int] = field(default_factory=list)


class ZigParser:
    """
    Parser for Zig source code to identify coverage instrumentation points.

    This is a regex-based parser that handles common Zig patterns.
    It's not a full AST parser but sufficient for coverage instrumentation.
    """

    # Patterns for Zig constructs
    FUNCTION_PATTERN = re.compile(
        r'^(\s*)(pub\s+)?(export\s+)?fn\s+(\w+)\s*\([^)]*\)[^{]*\{',
        re.MULTILINE
    )

    IF_PATTERN = re.compile(r'\bif\s*\(')
    ELSE_PATTERN = re.compile(r'\}\s*else\s*[\{]')
    SWITCH_PATTERN = re.compile(r'\bswitch\s*\(')
    RETURN_PATTERN = re.compile(r'\breturn\b')

    # Lines that are not executable
    NON_EXECUTABLE_PATTERNS = [
        re.compile(r'^\s*$'),  # Empty lines
        re.compile(r'^\s*//'),  # Comments
        re.compile(r'^\s*\*'),  # Multi-line comment continuation
        re.compile(r'^\s*/\*'),  # Multi-line comment start
        re.compile(r'^\s*\*/'),  # Multi-line comment end
        re.compile(r'^\s*const\s+\w+\s*=\s*@import'),  # Import statements
        re.compile(r'^\s*pub\s+const\s+\w+\s*=\s*\w+;'),  # Type aliases
        re.compile(r'^\s*\};?\s*$'),  # Closing braces only
        re.compile(r'^\s*\{\s*$'),  # Opening braces only
    ]

    def __init__(self):
        self.current_function: Optional[str] = None
        self.brace_depth = 0

    def parse(self, source: str, file_path: str) -> ParseResult:
        """Parse Zig source code and identify coverage points."""
        result = ParseResult(file_path=file_path)
        lines = source.split('\n')
        result.total_lines = len(lines)

        # First pass: find all functions
        self._find_functions(source, result)

        # Second pass: find branches and executable lines
        self._find_branches_and_lines(lines, result)

        # Generate coverage points
        self._generate_coverage_points(result)

        return result

    def _find_functions(self, source: str, result: ParseResult):
        """Find all function definitions in the source."""
        for match in self.FUNCTION_PATTERN.finditer(source):
            indent = match.group(1)
            is_public = match.group(2) is not None
            is_export = match.group(3) is not None
            name = match.group(4)

            # Calculate line number
            line = source[:match.start()].count('\n') + 1
            column = len(indent)

            # Find the body extent
            body_start, body_end = self._find_function_body(source, match.end() - 1)
            body_start_line = source[:body_start].count('\n') + 1
            body_end_line = source[:body_end].count('\n') + 1

            func = ZigFunction(
                name=name,
                line=line,
                column=column,
                is_public=is_public,
                is_export=is_export,
                body_start=body_start_line,
                body_end=body_end_line,
            )
            result.functions.append(func)

    def _find_function_body(self, source: str, brace_pos: int) -> Tuple[int, int]:
        """Find the start and end positions of a function body."""
        depth = 1
        pos = brace_pos + 1
        start = brace_pos

        while pos < len(source) and depth > 0:
            char = source[pos]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            pos += 1

        return start, pos - 1

    def _find_branches_and_lines(self, lines: List[str], result: ParseResult):
        """Find branch points and executable lines."""
        current_function = None

        for i, line in enumerate(lines):
            line_num = i + 1

            # Check if this is an executable line
            if self._is_executable_line(line):
                result.executable_lines.append(line_num)

            # Track current function context
            for func in result.functions:
                if func.body_start <= line_num <= func.body_end:
                    current_function = func.name
                    break

            # Find branch points
            if current_function:
                # Check for if statements
                for match in self.IF_PATTERN.finditer(line):
                    result.branches.append(ZigBranch(
                        type=CoveragePointType.BRANCH_IF,
                        line=line_num,
                        column=match.start(),
                        parent_function=current_function,
                    ))

                # Check for else clauses
                for match in self.ELSE_PATTERN.finditer(line):
                    result.branches.append(ZigBranch(
                        type=CoveragePointType.BRANCH_ELSE,
                        line=line_num,
                        column=match.start(),
                        parent_function=current_function,
                    ))

                # Check for switch statements
                for match in self.SWITCH_PATTERN.finditer(line):
                    result.branches.append(ZigBranch(
                        type=CoveragePointType.BRANCH_SWITCH,
                        line=line_num,
                        column=match.start(),
                        parent_function=current_function,
                    ))

    def _is_executable_line(self, line: str) -> bool:
        """Check if a line is executable code."""
        for pattern in self.NON_EXECUTABLE_PATTERNS:
            if pattern.match(line):
                return False

        # Additional check: line must have some content
        stripped = line.strip()
        if not stripped:
            return False

        # Skip struct/enum declarations (they're not executable)
        if stripped.startswith('pub const') and '= extern struct' in stripped:
            return False
        if stripped.startswith('pub const') and '= struct' in stripped:
            return False
        if stripped.startswith('pub const') and '= enum' in stripped:
            return False

        return True

    def _generate_coverage_points(self, result: ParseResult):
        """Generate coverage points from parsed data."""
        point_id = 0

        # Add function entry points
        for func in result.functions:
            result.coverage_points.append(CoveragePoint(
                type=CoveragePointType.FUNCTION_ENTRY,
                line=func.body_start,
                column=0,
                name=func.name,
                file=result.file_path,
                id=point_id,
            ))
            point_id += 1

        # Add branch points
        for branch in result.branches:
            result.coverage_points.append(CoveragePoint(
                type=branch.type,
                line=branch.line,
                column=branch.column,
                name=f"{branch.parent_function}:{branch.type.value}",
                file=result.file_path,
                id=point_id,
            ))
            point_id += 1
