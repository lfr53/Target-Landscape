# Hugging Face Spaces (Docker SDK).
#
# The engine needs nothing beyond the standard library; only the web layer has
# dependencies, so this image is deliberately small and has no build step —
# the frontend is plain HTML, CSS and JavaScript served as files.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY landscape/ ./landscape/
COPY web/ ./web/
COPY data/ ./data/
COPY fixtures/ ./fixtures/
COPY scripts/ ./scripts/
COPY calibration/ ./calibration/

# Spaces runs as a non-root user; give the cache somewhere writable. Losing
# this directory on restart is harmless — the curated tier is the durable one.
RUN mkdir -p /tmp/tl-cache && chmod 777 /tmp/tl-cache
ENV LANDSCAPE_CACHE=/tmp/tl-cache/http \
    LANDSCAPE_STORE_CACHE=/tmp/tl-cache/store \
    LANDSCAPE_MAX_BUILDS=2

EXPOSE 7860
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "7860"]
