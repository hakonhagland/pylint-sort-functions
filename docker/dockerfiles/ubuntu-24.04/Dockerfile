FROM ubuntu:24.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, pip, and required system packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Create Python virtual environment using uv
RUN uv venv .venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy requirements file (will be created next)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN uv pip install -r requirements.txt

# Copy and install the pylint-sort-functions plugin from source
COPY src/ /app/src/
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# Install the plugin in development mode
RUN cd /app && uv pip install -e .

# Copy the Flask API service
COPY api-service.py /app/api-service.py

# Copy test projects
COPY test-projects/ /app/test-projects/

# Expose port for Flask API
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the Flask API service
CMD ["python3", "api-service.py"]
