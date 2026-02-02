# Use Python 3.13 as the base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PDM_CHECK_UPDATE=false

# Install PDM
RUN pip install -U pdm

# Install compile dependencies (for tree-sitter)
RUN apt-get update && apt-get install -y build-essential python3-dev && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
# We use pdm install to create the virtual environment in /app/.venv
RUN pdm install --prod --no-editable

# Copy the entire services directory to maintain package structure
COPY services /app/services

# Ensure the .venv is used
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Command to run the orchestrator worker
# We use python -m to run it as a module so relative imports work correctly
CMD ["pdm", "run", "python", "-m", "services.orchestrator.main"]
