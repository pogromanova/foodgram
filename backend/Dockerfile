FROM python:3.9-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        postgresql-client build-essential libpq-dev netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

RUN mkdir -p /backend_static \
 && mkdir -p /app/media/avatars /app/media/recipes/images \
 && chmod 755 /backend_static \
 && chmod -R 777 /app/media

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
