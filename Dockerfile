# syntax=docker/dockerfile:1.7

# ---------- Frontend build ----------
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- API runtime ----------
FROM python:3.14-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/data/hf-cache

WORKDIR /app/backend

RUN groupadd --system --gid 1000 appuser \
    && useradd --system --uid 1000 --gid appuser --create-home appuser

COPY backend/requirements.lock.txt ./requirements.lock.txt

# CPU-only PyTorch keeps the image small (no CUDA libraries).
RUN python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.14.1" \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements.lock.txt

COPY backend/ ./

RUN mkdir -p /app/data/uploads /app/data/qdrant /app/data/hf-cache \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"

# Embedded Qdrant and SQLite require a single worker and a single instance.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]

# ---------- Web runtime ----------
FROM nginx:1.27-alpine AS web
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
