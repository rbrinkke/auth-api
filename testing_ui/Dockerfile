# Lightweight Docker image for Auth API Testing UI
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 testuser && \
    mkdir -p /app && \
    chown -R testuser:testuser /app

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy testing UI files
COPY --chown=testuser:testuser . .

# Switch to non-root user
USER testuser

# Expose port 8099
EXPOSE 8099

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8099/health')"

# Start the testing UI
CMD ["python", "-m", "uvicorn", "standalone:app", "--host", "0.0.0.0", "--port", "8099"]
