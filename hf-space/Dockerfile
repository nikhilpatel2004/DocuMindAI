FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/data/hf-cache \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

RUN groupadd --system --gid 1000 appuser \
    && useradd --system --uid 1000 --gid appuser --create-home appuser

RUN git clone --depth 1 https://github.com/nikhilpatel2004/DocuMindAI.git /tmp/src \
    && cp -r /tmp/src/backend/. /app/backend/ \
    && cp /tmp/src/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh \
    && rm -rf /tmp/src

RUN python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.14.1" \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements.lock.txt

RUN chmod +x /usr/local/bin/api-entrypoint.sh \
    && mkdir -p /app/data/uploads /app/data/qdrant /app/data/hf-cache \
    && chown -R appuser:appuser /app

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/api-entrypoint.sh"]
