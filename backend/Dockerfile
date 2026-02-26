# ─────────────────────────────────────────────────────────────────────────────
# PPF Workshop Monitoring System — Backend Dockerfile
#
# Multi-stage build:
#   Stage 1 (builder): Install Python deps in a venv
#   Stage 2 (runtime): Copy venv + source only — minimal image
#
# Author: PPF Monitoring Team
# Created: 2026-02-22
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile psycopg2 (binary wheel avoids this, but kept for safety)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies first (layer cache friendly)
COPY requirements.txt .
RUN pip install --upgrade pip --quiet && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="PPF Monitoring Team"
LABEL description="PPF Workshop Monitoring System — FastAPI Backend"
LABEL version="1.0.0"

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd -r ppf && useradd -r -g ppf ppf

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY --chown=ppf:ppf . .

# Create logs directory
RUN mkdir -p /app/logs && chown ppf:ppf /app/logs

USER ppf

EXPOSE 8000

# Default: production mode (no --reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
