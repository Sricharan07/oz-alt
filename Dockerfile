FROM python:3.12-slim AS oz-python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OZ_REPO_ROOT=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      curl \
      libxml2 \
      libxslt1.1 \
      libpq5 \
      postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY packages/oz-api packages/oz-api
COPY packages/oz-crawler packages/oz-crawler
COPY third_party/Scrapling third_party/Scrapling
COPY registry registry
COPY infra/sql infra/sql
COPY scripts scripts

RUN python -m pip install --upgrade pip \
    && python -m pip install -e packages/oz-api -e packages/oz-crawler

EXPOSE 8765

CMD ["python", "-m", "oz_api.server", "--repo-root", "/app", "--host", "0.0.0.0", "--port", "8765", "--require-auth"]
