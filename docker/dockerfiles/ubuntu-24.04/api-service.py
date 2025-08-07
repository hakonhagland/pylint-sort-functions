#!/usr/bin/env python3
"""
Flask API service for PyLint Sort Functions validation container.

This service provides endpoints for testing PyLint configurations and
validating documentation examples within the Docker container environment.
"""

import os
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# Global storage for test results
test_results: Dict[str, Dict[str, Any]] = {}

# Base paths
BASE_DIR = Path("/app")
TEST_PROJECTS_DIR = BASE_DIR / "test-projects"
CONFIG_DIR = BASE_DIR / "config"

# Ensure config directory exists
CONFIG_DIR.mkdir(exist_ok=True)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def get_available_projects() -> List[str]:
    """Get list of available test projects."""
    if not TEST_PROJECTS_DIR.exists():
        return []

    projects = []
    for path in TEST_PROJECTS_DIR.iterdir():
        if path.is_dir() and not path.name.startswith("."):
            projects.append(path.name)

    return sorted(projects)


def save_config(config_type: str, content: str, name: Optional[str] = None) -> str:
    """Save configuration file and return filename."""
    if config_type not in ["pylintrc", "pyproject", "setup_cfg"]:
        raise ValidationError(f"Unsupported config type: {config_type}")

    # Generate filename
    if name:
        filename = f"{name}.{config_type}"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{timestamp}.{config_type}"

    # Determine file extension and format
    if config_type == "pylintrc":
        filepath = CONFIG_DIR / filename
    elif config_type == "pyproject":
        filepath = CONFIG_DIR / f"{filename}.toml"
    else:  # setup_cfg
        filepath = CONFIG_DIR / f"{filename}.cfg"

    # Write configuration file
    filepath.write_text(content)
    return str(filepath)


def run_pylint_test(project: str, config_file: Optional[str] = None) -> Dict[str, Any]:
    """Run PyLint on specified test project with optional configuration."""
    project_path = TEST_PROJECTS_DIR / project
    if not project_path.exists():
        raise ValidationError(f"Project not found: {project}")

    # Build pylint command
    cmd = ["pylint", "--load-plugins=pylint_sort_functions"]

    # Add configuration if provided
    if config_file:
        config_path = Path(config_file)
        if config_path.suffix == ".toml":
            # For pyproject.toml, no special flag needed (auto-detected)
            pass
        elif config_path.suffix == ".cfg":
            cmd.extend(["--rcfile", str(config_file)])
        else:
            # Default .pylintrc format
            cmd.extend(["--rcfile", str(config_file)])

    # Add source directory or files
    src_dir = project_path / "src"
    if src_dir.exists():
        cmd.append(str(src_dir))
    else:
        # Look for Python files in project root
        py_files = list(project_path.glob("*.py"))
        if py_files:
            cmd.extend(str(f) for f in py_files)
        else:
            raise ValidationError(f"No Python files found in project: {project}")

    # Change to project directory for execution
    original_cwd = os.getcwd()
    try:
        os.chdir(project_path)

        # Run pylint
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )
        end_time = datetime.now()

        execution_time = (end_time - start_time).total_seconds()

        # Parse pylint output
        messages = parse_pylint_output(result.stdout)

        return {
            "project": project,
            "status": "completed",
            "pylint_exit_code": result.returncode,
            "messages": messages,
            "execution_time": execution_time,
            "config_applied": config_file or "default",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "project": project,
            "status": "failed",
            "error": "PyLint execution timed out",
            "execution_time": 60.0,
        }
    except Exception as e:
        return {
            "project": project,
            "status": "failed",
            "error": str(e),
            "execution_time": 0.0,
        }
    finally:
        os.chdir(original_cwd)


def parse_pylint_output(output: str) -> List[Dict[str, Any]]:
    """Parse PyLint output into structured messages."""
    messages = []

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Parse pylint message format: path:line:column: message-id (symbol) message
        parts = line.split(":", 3)
        if len(parts) >= 4:
            path = parts[0]
            try:
                line_num = int(parts[1])
                column = int(parts[2]) if parts[2].isdigit() else 0
                message_part = parts[3].strip()

                # Extract message-id and symbol
                message_id = ""
                symbol = ""
                message_text = message_part

                if "(" in message_part and ")" in message_part:
                    # Format: message-id (symbol) message
                    paren_start = message_part.find("(")
                    paren_end = message_part.find(")")
                    if paren_start > 0 and paren_end > paren_start:
                        message_id = message_part[:paren_start].strip()
                        symbol = message_part[paren_start + 1 : paren_end]
                        message_text = message_part[paren_end + 1 :].strip()

                message_type = "warning"
                if message_id.startswith("E"):
                    message_type = "error"
                elif message_id.startswith("C"):
                    message_type = "convention"
                elif message_id.startswith("R"):
                    message_type = "refactor"

                messages.append(
                    {
                        "type": message_type,
                        "message-id": message_id,
                        "symbol": symbol,
                        "path": path,
                        "line": line_num,
                        "column": column,
                        "message": message_text,
                    }
                )
            except (ValueError, IndexError):
                # Skip lines that don't match expected format
                continue

    return messages


def get_plugin_info() -> Dict[str, Any]:
    """Get information about the pylint-sort-functions plugin."""
    try:
        # Get actual plugin help to find real options
        result = subprocess.run(
            ["pylint", "--load-plugins=pylint_sort_functions", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Parse actual options from pylint help output
        help_text = result.stdout
        actual_options = []

        # Look for function-sort specific options in help text
        in_function_sort_section = False
        for line in help_text.split("\n"):
            if "function-sort" in line.lower():
                in_function_sort_section = True
            elif in_function_sort_section and line.strip() and not line.startswith(" "):
                in_function_sort_section = False
            elif in_function_sort_section and "--" in line:
                # Extract option name from line like "  --public-api-patterns=..."
                option_match = re.search(r"--([a-z-]+)", line)
                if option_match:
                    actual_options.append(option_match.group(1))

        # Basic plugin information with ACTUAL options found
        info = {
            "plugin_name": "pylint-sort-functions",
            "version": "development",
            "messages": {
                "W9001": {
                    "symbol": "unsorted-functions",
                    "description": "Functions are not sorted alphabetically",
                },
                "W9002": {
                    "symbol": "unsorted-methods",
                    "description": "Class methods are not sorted alphabetically",
                },
                "W9003": {
                    "symbol": "mixed-function-visibility",
                    "description": "Public and private functions not separated",
                },
                "W9004": {
                    "symbol": "function-should-be-private",
                    "description": "Function should be private based on usage",
                },
            },
            "options": actual_options,
            "help_output": help_text,  # Include raw help for debugging
        }

        return info

    except subprocess.TimeoutExpired:
        return {"error": "Plugin information request timed out"}
    except Exception as e:
        return {"error": str(e)}


# API Routes


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "service": "pylint-sort-functions-validation",
            "status": "healthy",
            "version": "0.1.0",
        }
    )


@app.route("/projects", methods=["GET"])
def list_projects():
    """List available test projects."""
    projects = get_available_projects()
    return jsonify({"projects": projects})


@app.route("/config", methods=["POST"])
def upload_config():
    """Upload and save a configuration file."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        config_type = data.get("type")
        content = data.get("content")
        name = data.get("name")

        if not config_type or not content:
            return jsonify({"error": "Missing required fields: type, content"}), 400

        config_file = save_config(config_type, content, name)

        return jsonify(
            {
                "message": "Configuration uploaded successfully",
                "config_file": config_file,
                "type": config_type,
            }
        )

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/test/<project>", methods=["POST"])
def test_project(project):
    """Run PyLint on specified test project."""
    try:
        # Check if project exists
        if project not in get_available_projects():
            return jsonify({"error": f"Project not found: {project}"}), 404

        # Get optional configuration file from request
        config_file = None
        data = request.get_json() if request.is_json else {}
        if data and "config_file" in data:
            config_file = data["config_file"]

        # Generate test ID
        test_id = str(uuid.uuid4())

        # Run the test
        result = run_pylint_test(project, config_file)
        result["test_id"] = test_id

        # Store result
        test_results[test_id] = result

        return jsonify(result)

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/results/<test_id>", methods=["GET"])
def get_results(test_id):
    """Get detailed test results by test ID."""
    if test_id not in test_results:
        return jsonify({"error": f"Test ID not found: {test_id}"}), 404

    return jsonify(test_results[test_id])


@app.route("/reset", methods=["POST"])
def reset_config():
    """Reset configuration to clean state."""
    try:
        # Clear configuration directory
        for config_file in CONFIG_DIR.glob("*"):
            if config_file.is_file():
                config_file.unlink()

        # Clear test results
        test_results.clear()

        return jsonify({"message": "Configuration reset successfully"})

    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/plugin-info", methods=["GET"])
def plugin_info():
    """Get plugin information and available options."""
    info = get_plugin_info()
    return jsonify(info)


# Error handlers


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting PyLint Sort Functions Validation API...")
    print(f"Available projects: {get_available_projects()}")

    app.run(host="0.0.0.0", port=8080, debug=False)
