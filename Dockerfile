# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first (for better layer caching)
# This way, if requirements.txt doesn't change, Docker can reuse this layer
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't cache packages (smaller image)
# --user: Install to user directory (not system)
RUN pip install --no-cache-dir --user -r requirements.txt

# Remove build dependencies to keep builder small
RUN apt-get purge -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# ========== Production Stage ==========
FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -u 1000 authuser && \
    mkdir -p /app && \
    mkdir -p /app/logs && \
    chown -R authuser:authuser /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder (cached layer)
COPY --from=builder /root/.local /home/authuser/.local

# Copy application code (this changes frequently, so it's last)
COPY --chown=authuser:authuser ./app ./app
COPY --chown=authuser:authuser ./config ./config

# Switch to non-root user (security best practice)
USER authuser

# Add local bin to PATH
ENV PATH=/home/authuser/.local/bin:$PATH

# Set production environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
