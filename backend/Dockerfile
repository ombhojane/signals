# ── Backend Dockerfile ─────────────────────────────────
# Python 3.11 slim for FastAPI + Uvicorn
FROM python:3.11-slim AS base

WORKDIR /app

# Install system deps for some Python packages (numpy, scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Cloud Run injects PORT (default 8080); shell-form CMD so $PORT expands at runtime.
ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:${PORT} \
    --timeout 120 \
    --access-logfile -
