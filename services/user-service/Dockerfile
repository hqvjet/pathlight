FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port (will be overridden by environment)
EXPOSE 8002

# Health check - use environment variable or default
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${USER_SERVICE_PORT:-8002}/health || exit 1

# Start the application using environment variable
CMD python -m uvicorn src.main:app --host 0.0.0.0 --port ${USER_SERVICE_PORT:-8002}
