# ============================================================================
# AUTH SERVICE - DOCKERFILE
# ============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base image
# -----------------------------------------------------------------------------
# python:3.13-slim = Debian-based minimal Python image (~150MB)
# Why slim? Smaller image, faster deployments, less attack surface
# Why not alpine? Some Python packages have compatibility issues with Alpine
# -----------------------------------------------------------------------------
FROM python:3.13-slim

# -----------------------------------------------------------------------------
# Set environment variables
# -----------------------------------------------------------------------------
# PYTHONDONTWRITEBYTECODE=1 : Don't create .pyc files (smaller image)
# PYTHONUNBUFFERED=1 : Print logs immediately (don't buffer)
# -----------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# -----------------------------------------------------------------------------
# Set working directory
# -----------------------------------------------------------------------------
# All subsequent commands run from /app
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# Install system dependencies
# -----------------------------------------------------------------------------
# gcc, libpq-dev needed for psycopg2 (PostgreSQL driver)
# After install, clean up apt cache to keep image small
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Copy requirements first (Docker layer caching optimization)
# -----------------------------------------------------------------------------
# Why separate COPY for requirements?
# If code changes but requirements don't, Docker uses cached layer
# = Faster rebuilds!
# -----------------------------------------------------------------------------
COPY requirements.txt .

# -----------------------------------------------------------------------------
# Install Python dependencies
# -----------------------------------------------------------------------------
# --no-cache-dir : Don't store pip cache (smaller image)
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Copy application code
# -----------------------------------------------------------------------------
# In development: This gets overridden by volume mount
# In production: This is the actual code that runs
# -----------------------------------------------------------------------------
COPY ./app ./app

# -----------------------------------------------------------------------------
# Expose port
# -----------------------------------------------------------------------------
# Documentation only - tells users this container listens on 8001
# Actual port mapping happens in docker-compose
# -----------------------------------------------------------------------------
EXPOSE 8001

# -----------------------------------------------------------------------------
# Run the application
# -----------------------------------------------------------------------------
# uvicorn: ASGI server for FastAPI
# app.main:app : Import 'app' from app/main.py
# --host 0.0.0.0 : Accept connections from any IP (required in Docker)
# --port 8001 : Listen on port 8001
# --reload : Auto-restart on code change (dev only, remove in prod)
# -----------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
