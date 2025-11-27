"""
JUnit XML report generation for CI integration.

Generates JUnit XML format output compatible with:
- GitHub Actions
- GitLab CI
- Jenkins
- Any CI system that parses JUnit XML
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import time


@dataclass
class JUnitTestCase:
    """Represents a single test case in JUnit format."""
    name: str
    classname: str
    time: float
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    skipped: bool = False
    skip_message: Optional[str] = None


@dataclass
class JUnitTestSuite:
    """Represents a test suite in JUnit format."""
    name: str
    tests: int
    failures: int
    errors: int
    skipped: int
    time: float
    testcases: List[JUnitTestCase]
    timestamp: Optional[str] = None


class JUnitReportGenerator:
    """Generates JUnit XML reports from test results."""

    def __init__(self):
        self.testsuites: List[JUnitTestSuite] = []
        self.start_time: Optional[float] = None

    def start(self):
        """Mark the start of test execution."""
        self.start_time = time.time()

    def add_results(self, results: List, context_name: str = "pzspec"):
        """
        Add test results to the report.

        Args:
            results: List of TestResult objects from the test runner
            context_name: Name for the test suite
        """
        testcases = []
        failures = 0
        errors = 0
        skipped = 0
        total_time = 0.0

        for result in results:
            # Parse the test name to get classname and method name
            if "::" in result.name:
                parts = result.name.rsplit("::", 1)
                classname = parts[0].replace(" > ", ".").replace(" ", "_")
                name = parts[1]
            else:
                classname = context_name
                name = result.name

            tc = JUnitTestCase(
                name=name,
                classname=classname,
                time=result.duration
            )

            if not result.passed:
                if result.error:
                    if "AssertionError" in result.error or "Expected" in result.error:
                        tc.failure_message = result.error
                        tc.failure_type = "AssertionError"
                        failures += 1
                    else:
                        tc.error_message = result.error
                        tc.error_type = "Error"
                        errors += 1
                else:
                    tc.failure_message = "Test failed"
                    tc.failure_type = "AssertionError"
                    failures += 1

            total_time += result.duration
            testcases.append(tc)

        suite = JUnitTestSuite(
            name=context_name,
            tests=len(testcases),
            failures=failures,
            errors=errors,
            skipped=skipped,
            time=total_time,
            testcases=testcases,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        self.testsuites.append(suite)

    def add_results_by_context(self, results: List, contexts: Dict[str, List]):
        """
        Add test results organized by describe block context.

        Args:
            results: List of TestResult objects
            contexts: Dict mapping context names to lists of results
        """
        for context_name, context_results in contexts.items():
            self.add_results(context_results, context_name)

    def generate_xml(self) -> str:
        """
        Generate the JUnit XML report.

        Returns:
            XML string in JUnit format
        """
        # Create root element
        testsuites = ET.Element("testsuites")

        # Calculate totals
        total_tests = sum(s.tests for s in self.testsuites)
        total_failures = sum(s.failures for s in self.testsuites)
        total_errors = sum(s.errors for s in self.testsuites)
        total_skipped = sum(s.skipped for s in self.testsuites)
        total_time = sum(s.time for s in self.testsuites)

        testsuites.set("tests", str(total_tests))
        testsuites.set("failures", str(total_failures))
        testsuites.set("errors", str(total_errors))
        testsuites.set("skipped", str(total_skipped))
        testsuites.set("time", f"{total_time:.3f}")

        for suite in self.testsuites:
            testsuite = ET.SubElement(testsuites, "testsuite")
            testsuite.set("name", suite.name)
            testsuite.set("tests", str(suite.tests))
            testsuite.set("failures", str(suite.failures))
            testsuite.set("errors", str(suite.errors))
            testsuite.set("skipped", str(suite.skipped))
            testsuite.set("time", f"{suite.time:.3f}")
            if suite.timestamp:
                testsuite.set("timestamp", suite.timestamp)

            for tc in suite.testcases:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", tc.name)
                testcase.set("classname", tc.classname)
                testcase.set("time", f"{tc.time:.3f}")

                if tc.failure_message:
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", tc.failure_message)
                    if tc.failure_type:
                        failure.set("type", tc.failure_type)
                    failure.text = tc.failure_message

                if tc.error_message:
                    error = ET.SubElement(testcase, "error")
                    error.set("message", tc.error_message)
                    if tc.error_type:
                        error.set("type", tc.error_type)
                    error.text = tc.error_message

                if tc.skipped:
                    skipped = ET.SubElement(testcase, "skipped")
                    if tc.skip_message:
                        skipped.set("message", tc.skip_message)

        # Pretty print
        xml_str = ET.tostring(testsuites, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Remove extra blank lines and add XML declaration
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        return "\n".join(lines)

    def write_to_file(self, filepath: str):
        """
        Write the JUnit XML report to a file.

        Args:
            filepath: Path to the output file
        """
        xml_content = self.generate_xml()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(xml_content, encoding="utf-8")


def generate_junit_xml(results: List, output_path: str, suite_name: str = "pzspec"):
    """
    Convenience function to generate a JUnit XML report.

    Args:
        results: List of TestResult objects from the test runner
        output_path: Path to write the XML file
        suite_name: Name for the test suite
    """
    generator = JUnitReportGenerator()
    generator.add_results(results, suite_name)
    generator.write_to_file(output_path)
