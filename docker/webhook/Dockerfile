# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy dependency files
COPY pyproject.toml pdm.lock ./

# Install dependencies (without installing the project itself)
RUN pdm install --check --prod --no-editable --no-self

# Copy the webhook service code
COPY services/webhook/ .

# Expose the port the app runs on
EXPOSE 8000

# Healthcheck to ensure the container is running
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["pdm", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
