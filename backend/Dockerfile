FROM python:3.9-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY entrypoint.sh .

RUN mkdir -p /backend_static && chmod 755 /backend_static

RUN mkdir -p /app/media/avatars /app/media/recipes/images && \
    chmod -R 777 /app/media

RUN chmod +x entrypoint.sh

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /backend_static

USER appuser

ENTRYPOINT ["./entrypoint.sh"]