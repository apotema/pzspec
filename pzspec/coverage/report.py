"""
Coverage report generation for PZSpec.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .collector import CoverageData, CoverageCollector
from .parser import CoveragePointType


class CoverageReport:
    """Generates coverage reports in various formats."""

    def __init__(self, collector: CoverageCollector):
        self.collector = collector

    def print_summary(self):
        """Print a summary of coverage to stdout."""
        summary = self.collector.get_summary()

        print("\n" + "=" * 60)
        print("Coverage Report")
        print("=" * 60)

        if summary['total_files'] == 0:
            print("No coverage data collected.")
            print("=" * 60 + "\n")
            return

        # Per-file breakdown
        for file_path, data in self.collector.coverage_data.items():
            filename = os.path.basename(file_path)
            pct = data.coverage_percent
            covered = data.covered_points
            total = data.total_points

            # Color coding based on coverage
            if pct >= 80:
                status = "✓"
            elif pct >= 50:
                status = "○"
            else:
                status = "✗"

            print(f"  {status} {filename:<30} {pct:>5.1f}%  ({covered}/{total})")

        print("-" * 60)

        # Summary line
        print(f"  Total Coverage: {summary['coverage_percent']:.1f}%")
        print(f"  Functions: {summary['covered_functions']}/{summary['total_functions']} "
              f"({summary['function_coverage_percent']:.1f}%)")
        print(f"  Branches:  {summary['covered_branches']}/{summary['total_branches']} "
              f"({summary['branch_coverage_percent']:.1f}%)")

        print("=" * 60 + "\n")

    def print_detailed(self):
        """Print detailed coverage information."""
        self.print_summary()

        for file_path, data in self.collector.coverage_data.items():
            print(f"\nFile: {file_path}")
            print("-" * 60)

            # Show uncovered functions
            uncovered_funcs = data.get_uncovered_functions()
            if uncovered_funcs:
                print("  Uncovered functions:")
                for point in uncovered_funcs:
                    print(f"    - {point.name} (line {point.line})")

            # Show uncovered lines
            uncovered_lines = data.get_uncovered_lines()
            if uncovered_lines:
                print(f"  Uncovered lines: {', '.join(map(str, uncovered_lines))}")

            if not uncovered_funcs and not uncovered_lines:
                print("  All code covered!")

    def generate_html(self, output_dir: str):
        """Generate HTML coverage report."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate index page
        self._generate_html_index(output_path)

        # Generate per-file pages
        for file_path, data in self.collector.coverage_data.items():
            self._generate_html_file(output_path, file_path, data)

        print(f"HTML coverage report generated in: {output_path}")

    def _generate_html_index(self, output_path: Path):
        """Generate the index HTML page."""
        summary = self.collector.get_summary()

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>PZSpec Coverage Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 800px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .coverage-high {{ color: #2e7d32; font-weight: bold; }}
        .coverage-medium {{ color: #f9a825; font-weight: bold; }}
        .coverage-low {{ color: #c62828; font-weight: bold; }}
        .summary {{ background-color: #e8f5e9; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .progress {{ background-color: #e0e0e0; border-radius: 4px; overflow: hidden; }}
        .progress-bar {{ height: 20px; transition: width 0.3s; }}
        .progress-high {{ background-color: #4CAF50; }}
        .progress-medium {{ background-color: #FFC107; }}
        .progress-low {{ background-color: #F44336; }}
    </style>
</head>
<body>
    <h1>PZSpec Coverage Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Coverage:</strong> {summary['coverage_percent']:.1f}%</p>
        <div class="progress">
            <div class="progress-bar {self._get_coverage_class(summary['coverage_percent'])}"
                 style="width: {summary['coverage_percent']:.1f}%"></div>
        </div>
        <p><strong>Functions:</strong> {summary['covered_functions']}/{summary['total_functions']}
           ({summary['function_coverage_percent']:.1f}%)</p>
        <p><strong>Branches:</strong> {summary['covered_branches']}/{summary['total_branches']}
           ({summary['branch_coverage_percent']:.1f}%)</p>
    </div>

    <h2>Files</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Coverage</th>
            <th>Points</th>
            <th>Functions</th>
            <th>Branches</th>
        </tr>
'''

        for file_path, data in self.collector.coverage_data.items():
            filename = os.path.basename(file_path)
            safe_filename = filename.replace('.', '_') + '.html'
            coverage_class = self._get_coverage_text_class(data.coverage_percent)

            html += f'''        <tr>
            <td><a href="{safe_filename}">{filename}</a></td>
            <td class="{coverage_class}">{data.coverage_percent:.1f}%</td>
            <td>{data.covered_points}/{data.total_points}</td>
            <td>{data.functions_covered}/{data.total_functions}</td>
            <td>{data.branches_covered}/{data.total_branches}</td>
        </tr>
'''

        html += '''    </table>

    <footer style="margin-top: 40px; color: #666;">
        Generated by PZSpec Coverage
    </footer>
</body>
</html>
'''

        with open(output_path / 'index.html', 'w') as f:
            f.write(html)

    def _generate_html_file(self, output_path: Path, file_path: str, data: CoverageData):
        """Generate HTML page for a single file."""
        filename = os.path.basename(file_path)
        safe_filename = filename.replace('.', '_') + '.html'

        # Read the original source file
        try:
            with open(file_path, 'r') as f:
                source_lines = f.readlines()
        except FileNotFoundError:
            source_lines = ["// Source file not found"]

        covered_lines = set(data.get_covered_lines())
        uncovered_lines = set(data.get_uncovered_lines())

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Coverage: {filename}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .source {{ font-family: "SF Mono", Monaco, monospace; font-size: 14px; }}
        .line {{ display: flex; }}
        .line-number {{ width: 50px; text-align: right; padding-right: 10px; color: #999; user-select: none; }}
        .line-content {{ flex: 1; padding-left: 10px; white-space: pre; }}
        .covered {{ background-color: #c8e6c9; }}
        .uncovered {{ background-color: #ffcdd2; }}
        .summary {{ background-color: #e8f5e9; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        a {{ color: #1976D2; }}
    </style>
</head>
<body>
    <p><a href="index.html">&larr; Back to Index</a></p>
    <h1>{filename}</h1>

    <div class="summary">
        <p><strong>Coverage:</strong> {data.coverage_percent:.1f}%
           ({data.covered_points}/{data.total_points} points)</p>
        <p><strong>Functions:</strong> {data.functions_covered}/{data.total_functions}</p>
        <p><strong>Branches:</strong> {data.branches_covered}/{data.total_branches}</p>
    </div>

    <h2>Source</h2>
    <div class="source">
'''

        for i, line in enumerate(source_lines):
            line_num = i + 1
            line_content = line.rstrip('\n')

            if line_num in covered_lines:
                line_class = 'covered'
            elif line_num in uncovered_lines:
                line_class = 'uncovered'
            else:
                line_class = ''

            # Escape HTML
            line_content = (line_content
                          .replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;'))

            html += f'''        <div class="line {line_class}">
            <span class="line-number">{line_num}</span>
            <span class="line-content">{line_content}</span>
        </div>
'''

        html += '''    </div>
</body>
</html>
'''

        with open(output_path / safe_filename, 'w') as f:
            f.write(html)

    def _get_coverage_class(self, percent: float) -> str:
        """Get CSS class for progress bar based on coverage percentage."""
        if percent >= 80:
            return 'progress-high'
        elif percent >= 50:
            return 'progress-medium'
        return 'progress-low'

    def _get_coverage_text_class(self, percent: float) -> str:
        """Get CSS class for text based on coverage percentage."""
        if percent >= 80:
            return 'coverage-high'
        elif percent >= 50:
            return 'coverage-medium'
        return 'coverage-low'

    def to_json(self) -> Dict:
        """Export coverage data as JSON-serializable dict."""
        result = {
            'summary': self.collector.get_summary(),
            'files': {}
        }

        for file_path, data in self.collector.coverage_data.items():
            result['files'][file_path] = {
                'coverage_percent': data.coverage_percent,
                'total_points': data.total_points,
                'covered_points': data.covered_points,
                'total_functions': data.total_functions,
                'covered_functions': data.functions_covered,
                'total_branches': data.total_branches,
                'covered_branches': data.branches_covered,
                'covered_lines': data.get_covered_lines(),
                'uncovered_lines': data.get_uncovered_lines(),
                'uncovered_functions': [
                    {'name': p.name, 'line': p.line}
                    for p in data.get_uncovered_functions()
                ],
            }

        return result
