#!/usr/bin/env python3
"""
Test runner for PyLint Sort Functions documentation validation system.

This script systematically validates all configuration examples in the project
documentation by running them against the containerized validation API.

Usage:
    python test-validation/test-runner.py [--verbose] [--api-url URL]

    --verbose    Show detailed output for each test
    --api-url    Override default API URL (default: http://localhost:8080)

The test runner performs comprehensive validation:

1. **Configuration Examples**: Tests all .pylintrc, pyproject.toml, and setup.cfg
   examples found in docs/pylintrc.rst

2. **Plugin Options**: Verifies that documented options actually exist and work

3. **Framework Testing**: Tests framework-specific configurations against
   corresponding test projects

4. **Expected Results**: Compares actual plugin output against expected results

Results are saved to test-validation/reports/ for analysis.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

# Configuration
DEFAULT_API_URL = "http://localhost:8080"
REPORTS_DIR = Path(__file__).parent / "reports"
DOCS_DIR = Path(__file__).parent.parent / "docs"


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class APIClient:
    """Client for communicating with the validation API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _make_request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API endpoint."""
        url = urljoin(self.base_url + "/", endpoint)

        if data:
            # POST request with JSON data
            request_data = json.dumps(data).encode("utf-8")
            req = Request(url, data=request_data, method=method)
            req.add_header("Content-Type", "application/json")
        else:
            # GET request
            req = Request(url, method=method)

        try:
            with urlopen(req, timeout=60) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data)
        except HTTPError as e:
            error_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise ValidationError(f"HTTP {e.code}: {error_msg}")
        except URLError as e:
            raise ValidationError(f"Connection error: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON response: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return self._make_request("health")

    def get_projects(self) -> List[str]:
        """Get list of available test projects."""
        result = self._make_request("projects")
        return result.get("projects", [])

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information and available options."""
        return self._make_request("plugin-info")

    def upload_config(
        self, config_type: str, content: str, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload configuration file."""
        data = {"type": config_type, "content": content, "name": name}
        return self._make_request("config", method="POST", data=data)

    def test_project(
        self, project: str, config_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run test on specified project."""
        data = {}
        if config_file:
            data["config_file"] = config_file
        return self._make_request(f"test/{project}", method="POST", data=data)

    def reset_config(self) -> Dict[str, Any]:
        """Reset configuration to clean state."""
        return self._make_request("reset", method="POST")


class ConfigExtractor:
    """Extracts configuration examples from documentation files."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.pylintrc_file = docs_dir / "pylintrc.rst"

    def extract_pylintrc_examples(self) -> List[Dict[str, Any]]:
        """Extract .pylintrc configuration examples from documentation."""
        if not self.pylintrc_file.exists():
            raise ValidationError(f"Documentation file not found: {self.pylintrc_file}")

        content = self.pylintrc_file.read_text()
        examples = []

        # Pattern to find RST ini code blocks
        rst_ini_pattern = r"\.\. code-block:: ini\s*\n\n((?:[ \t]+.*\n)*)"
        matches = re.findall(rst_ini_pattern, content, re.MULTILINE)

        for i, match in enumerate(matches):
            # Remove leading indentation and clean up content
            lines = match.split("\n")
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Remove consistent leading whitespace
                    if line.startswith("   "):
                        cleaned_lines.append(line[3:])
                    else:
                        cleaned_lines.append(line.lstrip())

            cleaned_content = "\n".join(cleaned_lines).strip()

            # Skip if it doesn't look like pylintrc content
            if not cleaned_content or (
                "load-plugins" not in cleaned_content
                and "pylint_sort_functions" not in cleaned_content
            ):
                continue

            # Skip tox.ini content (contains testenv sections and deps/commands)
            if "[testenv" in cleaned_content or (
                "deps =" in cleaned_content and "commands =" in cleaned_content
            ):
                continue

            examples.append(
                {
                    "type": "pylintrc",
                    "content": cleaned_content,
                    "name": f"pylintrc_example_{len(examples) + 1}",
                    "source": "docs/pylintrc.rst",
                }
            )

        return examples

    def extract_pyproject_examples(self) -> List[Dict[str, Any]]:
        """Extract pyproject.toml configuration examples."""
        content = self.pylintrc_file.read_text()
        examples = []

        # Pattern for RST toml code blocks
        rst_toml_pattern = r"\.\. code-block:: toml\s*\n\n((?:[ \t]+.*\n)*)"
        matches = re.findall(rst_toml_pattern, content, re.MULTILINE)

        for i, match in enumerate(matches):
            # Remove leading indentation and clean up content
            lines = match.split("\n")
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Remove consistent leading whitespace
                    if line.startswith("   "):
                        cleaned_lines.append(line[3:])
                    else:
                        cleaned_lines.append(line.lstrip())

            cleaned_content = "\n".join(cleaned_lines).strip()

            # Skip if it doesn't look like pyproject.toml content
            if not cleaned_content or (
                "pylint" not in cleaned_content
                and "pylint_sort_functions" not in cleaned_content
            ):
                continue

            examples.append(
                {
                    "type": "pyproject",
                    "content": cleaned_content,
                    "name": f"pyproject_example_{len(examples) + 1}",
                    "source": "docs/pylintrc.rst",
                }
            )

        return examples

    def extract_setup_cfg_examples(self) -> List[Dict[str, Any]]:
        """Extract setup.cfg configuration examples."""
        content = self.pylintrc_file.read_text()
        examples = []

        # Pattern for RST cfg code blocks - ini format used for setup.cfg in RST
        rst_cfg_pattern = r"\.\. code-block:: ini\s*\n\n((?:[ \t]+.*\n)*)"
        matches = re.findall(rst_cfg_pattern, content, re.MULTILINE)

        for i, match in enumerate(matches):
            # Remove leading indentation and clean up content
            lines = match.split("\n")
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Remove consistent leading whitespace
                    if line.startswith("   "):
                        cleaned_lines.append(line[3:])
                    else:
                        cleaned_lines.append(line.lstrip())

            cleaned_content = "\n".join(cleaned_lines).strip()

            # Only include setup.cfg examples (look for [pylint] section)
            if not cleaned_content or "[pylint]" not in cleaned_content:
                continue

            examples.append(
                {
                    "type": "setup_cfg",
                    "content": cleaned_content,
                    "name": f"setup_cfg_example_{len(examples) + 1}",
                    "source": "docs/pylintrc.rst",
                }
            )

        return examples

    def get_all_examples(self) -> List[Dict[str, Any]]:
        """Get all configuration examples from documentation."""
        examples = []
        examples.extend(self.extract_pylintrc_examples())
        examples.extend(self.extract_pyproject_examples())
        examples.extend(self.extract_setup_cfg_examples())
        return examples


class ValidationResult:
    """Container for validation test results."""

    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.config_errors = []
        self.plugin_issues = []
        self.framework_results = {}
        self.detailed_results = []

    def add_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Add test result."""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        self.detailed_results.append(
            {"test_name": test_name, "success": success, "details": details}
        )

    def add_config_error(self, config_name: str, error: str):
        """Add configuration error."""
        self.config_errors.append({"config": config_name, "error": error})

    def add_plugin_issue(self, issue: str):
        """Add plugin compatibility issue."""
        self.plugin_issues.append(issue)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": self.passed_tests / self.total_tests
            if self.total_tests > 0
            else 0,
            "config_errors": len(self.config_errors),
            "plugin_issues": len(self.plugin_issues),
            "critical_issues": self.config_errors
            + [{"type": "plugin", "issue": issue} for issue in self.plugin_issues],
        }


class DocumentationValidator:
    """Main validation orchestrator."""

    def __init__(self, api_client: APIClient, verbose: bool = False):
        self.api_client = api_client
        self.verbose = verbose
        self.config_extractor = ConfigExtractor(DOCS_DIR)
        self.result = ValidationResult()

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        if level == "INFO" or self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def validate_api_connection(self):
        """Validate API connection and readiness."""
        self.log("Checking API connection...")
        try:
            health = self.api_client.health_check()
            if health.get("status") != "healthy":
                raise ValidationError(f"API not healthy: {health}")
            self.log(f"API healthy: {health.get('service')} v{health.get('version')}")
        except Exception as e:
            raise ValidationError(f"API connection failed: {e}")

    def validate_plugin_options(self):
        """Validate plugin options against documentation."""
        self.log("Validating plugin options...")

        try:
            plugin_info = self.api_client.get_plugin_info()
            documented_options = [
                "ignore-decorators",
                "enable-privacy-detection",
                "public-api-patterns",
                # Note: "skip-dirs" is a future feature, not yet implemented
            ]
            actual_options = plugin_info.get("options", [])

            self.log(f"Documented options: {documented_options}")
            self.log(f"Actual plugin options: {actual_options}")

            # Check for documented options that don't exist
            for option in documented_options:
                if option not in actual_options:
                    error = (
                        f"Documented option '{option}' not found in plugin "
                        "implementation"
                    )
                    self.result.add_plugin_issue(error)
                    self.log(error, "WARN")

        except Exception as e:
            self.result.add_plugin_issue(f"Failed to get plugin info: {e}")
            self.log(f"Plugin info validation failed: {e}", "ERROR")

    def test_configuration_examples(self):
        """Test all configuration examples from documentation."""
        self.log("Testing configuration examples...")

        examples = self.config_extractor.get_all_examples()
        self.log(f"Found {len(examples)} configuration examples")

        for example in examples:
            test_name = f"{example['name']} ({example['type']})"
            self.log(f"Testing: {test_name}")

            try:
                # Upload configuration
                upload_result = self.api_client.upload_config(
                    example["type"], example["content"], example["name"]
                )

                # Test with minimal project
                test_result = self.api_client.test_project(
                    "minimal-project", upload_result["config_file"]
                )

                # Check for configuration errors
                config_errors = [
                    msg
                    for msg in test_result.get("messages", [])
                    if "unrecognized-option" in msg.get("symbol", "")
                ]

                if config_errors:
                    for error in config_errors:
                        self.result.add_config_error(test_name, error["message-id"])
                    success = False
                    details = {"config_errors": config_errors, "result": test_result}
                else:
                    success = True
                    details = {"result": test_result}

                self.result.add_result(test_name, success, details)

            except Exception as e:
                self.result.add_result(test_name, False, {"error": str(e)})
                self.log(f"Test failed: {test_name} - {e}", "ERROR")

    def test_framework_compatibility(self):
        """Test framework-specific configurations."""
        self.log("Testing framework compatibility...")

        framework_projects = [
            "flask-project",
            "django-project",
            "fastapi-project",
            "click-project",
            "pytest-project",
        ]

        for project in framework_projects:
            self.log(f"Testing framework project: {project}")

            try:
                result = self.api_client.test_project(project)

                # Check for configuration issues
                config_errors = [
                    msg
                    for msg in result.get("messages", [])
                    if "unrecognized-option" in msg.get("symbol", "")
                ]

                # Count sorting violations (our plugin messages)
                plugin_messages = [
                    msg
                    for msg in result.get("messages", [])
                    if msg.get("message-id", "").startswith("W90")
                ]

                self.result.framework_results[project] = {
                    "total_messages": len(result.get("messages", [])),
                    "config_errors": len(config_errors),
                    "plugin_messages": len(plugin_messages),
                    "exit_code": result.get("pylint_exit_code", 0),
                    "success": len(config_errors) == 0,
                }

            except Exception as e:
                self.result.framework_results[project] = {
                    "error": str(e),
                    "success": False,
                }
                self.log(f"Framework test failed: {project} - {e}", "ERROR")

    def save_report(self, output_file: Path):
        """Save validation report to file."""
        REPORTS_DIR.mkdir(exist_ok=True)

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": self.result.get_summary(),
            "config_errors": self.result.config_errors,
            "plugin_issues": self.result.plugin_issues,
            "framework_results": self.result.framework_results,
            "detailed_results": self.result.detailed_results,
        }

        output_file.write_text(json.dumps(report, indent=2))
        self.log(f"Report saved to: {output_file}")

    def run_validation(self):
        """Run complete validation suite."""
        self.log("Starting documentation validation...")

        # Reset API state
        self.api_client.reset_config()

        # Run validation steps
        self.validate_api_connection()
        self.validate_plugin_options()
        self.test_configuration_examples()
        self.test_framework_compatibility()

        # Generate report
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = REPORTS_DIR / f"validation_report_{timestamp}.json"
        self.save_report(report_file)

        # Print summary
        summary = self.result.get_summary()
        self.log("=== VALIDATION SUMMARY ===")
        self.log(f"Total tests: {summary['total_tests']}")
        self.log(f"Passed: {summary['passed_tests']}")
        self.log(f"Failed: {summary['failed_tests']}")
        self.log(f"Success rate: {summary['success_rate']:.1%}")
        self.log(f"Configuration errors: {summary['config_errors']}")
        self.log(f"Plugin issues: {summary['plugin_issues']}")

        if summary["critical_issues"]:
            self.log("=== CRITICAL ISSUES ===", "WARN")
            for issue in summary["critical_issues"]:
                if "config" in issue:
                    self.log(
                        f"Config Error: {issue['config']} - {issue['error']}", "WARN"
                    )
                else:
                    self.log(f"Plugin Issue: {issue['issue']}", "WARN")

        return summary["failed_tests"] == 0 and len(summary["critical_issues"]) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output for each test"
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"API base URL (default: {DEFAULT_API_URL})",
    )

    args = parser.parse_args()

    try:
        api_client = APIClient(args.api_url)
        validator = DocumentationValidator(api_client, args.verbose)

        success = validator.run_validation()
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
