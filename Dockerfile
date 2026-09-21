# Multi-stage unified container for Hasamex Interview Analysis Platform
# Hosts both Next.js frontend (static export) and FastAPI backend on a single instance.

# Stage 1: Build Next.js Static Frontend
FROM node:22-alpine AS web-builder
WORKDIR /web

COPY apps/web/package*.json ./
RUN npm ci

COPY apps/web ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Unified FastAPI Application
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8080

# Install runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code and canonical data
COPY apps/api /app/apps/api
COPY data /app/data
COPY evaluation /app/evaluation

# Copy static frontend export into apps/web/out
COPY --from=web-builder /web/out /app/apps/web/out

EXPOSE 8080

# Startup command reading PORT environment variable (default 8080 for Cloud Run)
CMD ["sh", "-c", "uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
