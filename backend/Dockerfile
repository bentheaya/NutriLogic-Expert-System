# Production Dockerfile for NutriLogic Django API with SWI-Prolog
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies (SWI-Prolog for pyswip, libpq for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    swi-prolog \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and Prolog KB
COPY backend /app/backend
COPY prolog /app/prolog

WORKDIR /app/backend

# Set environment variable default for Prolog KB
ENV PROLOG_KB_PATH=/app/prolog/kb.pl

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "nutrilogic.wsgi:application"]
