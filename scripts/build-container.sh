#!/bin/bash
set -e

# Script to build the Docker container for PyLint Sort Functions validation system
# This builds the Ubuntu 24.04 container with Python, uv, and Flask API service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker/dockerfiles/ubuntu-24.04"

echo "Building PyLint Sort Functions validation container..."
echo "Project root: $PROJECT_ROOT"
echo "Docker directory: $DOCKER_DIR"

# Check if Dockerfile exists
if [ ! -f "$DOCKER_DIR/Dockerfile" ]; then
    echo "Error: Dockerfile not found at $DOCKER_DIR/Dockerfile"
    exit 1
fi

# Create temporary build context directory
BUILD_CONTEXT="$PROJECT_ROOT/docker/build-context"
rm -rf "$BUILD_CONTEXT"
mkdir -p "$BUILD_CONTEXT"

# Copy Dockerfile and requirements
cp "$DOCKER_DIR/Dockerfile" "$BUILD_CONTEXT/"
cp "$DOCKER_DIR/requirements.txt" "$BUILD_CONTEXT/"

# Copy plugin source files for installation
cp -r "$PROJECT_ROOT/src" "$BUILD_CONTEXT/"
cp "$PROJECT_ROOT/pyproject.toml" "$BUILD_CONTEXT/"
cp "$PROJECT_ROOT/README.md" "$BUILD_CONTEXT/"

# Copy the comprehensive API service
if [ -f "$DOCKER_DIR/api-service.py" ]; then
    cp "$DOCKER_DIR/api-service.py" "$BUILD_CONTEXT/"
else
    echo "Warning: API service not found at $DOCKER_DIR/api-service.py, creating minimal version"
    cat > "$BUILD_CONTEXT/api-service.py" << 'EOF'
#!/usr/bin/env python3
"""Flask API service for PyLint configuration validation."""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'pylint-sort-functions-validation',
        'version': '0.1.0'
    })

@app.route('/projects')
def list_projects():
    """List available test projects."""
    return jsonify({
        'projects': [
            'minimal-project',
            'flask-project',
            'django-project',
            'fastapi-project',
            'click-project',
            'pytest-project'
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
EOF
fi

# Copy comprehensive test projects
if [ -d "$PROJECT_ROOT/test-validation/test-projects" ]; then
    echo "Copying comprehensive test projects..."
    cp -r "$PROJECT_ROOT/test-validation/test-projects" "$BUILD_CONTEXT/"
else
    echo "Warning: Test projects not found at $PROJECT_ROOT/test-validation/test-projects"
    echo "Creating minimal test project..."
    # Create test projects directory structure
    mkdir -p "$BUILD_CONTEXT/test-projects/minimal-project/src"

    # Create a minimal test file with violations
    cat > "$BUILD_CONTEXT/test-projects/minimal-project/src/bad_sorting.py" << 'EOF'
"""Test module with intentional sorting violations."""


def zebra_function():
    """Public function out of order."""
    pass


def alpha_function():
    """Should come before zebra."""
    pass


def _private_helper():
    """Private function in wrong position."""
    pass


def public_after_private():
    """Public function after private."""
    pass


class BadClass:
    """Class with method sorting issues."""

    def zebra_method(self):
        """Method out of order."""
        pass

    def alpha_method(self):
        """Should come before zebra."""
        pass
EOF
fi

# Build the Docker image
echo "Building Docker image: pylint-sort-functions-validation"
# Try to use modern buildx, fall back to legacy build if not available
if docker buildx version >/dev/null 2>&1; then
    docker buildx build -t pylint-sort-functions-validation "$BUILD_CONTEXT"
else
    echo "Warning: docker buildx not available, using legacy build"
    docker build -t pylint-sort-functions-validation "$BUILD_CONTEXT"
fi

# Clean up build context
rm -rf "$BUILD_CONTEXT"

echo "Docker image built successfully: pylint-sort-functions-validation"
echo "To run the container, use: make run-docker-container"
