# Dockerfile for the News Application (Django + DRF)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for better layer caching.
# The project uses PyMySQL (pure Python) as its MySQL driver via
# news/__init__.py, so no system MySQL client libraries are needed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Default configuration for containerised runs; override at `docker run`
# time or via docker-compose.yml.
ENV DJANGO_SECRET_KEY=please-change-this-secret-key
ENV DJANGO_DEBUG=False
ENV DJANGO_ALLOWED_HOSTS=*
ENV DATABASE_ENGINE=django.db.backends.mysql
ENV DATABASE_HOST=db
ENV DATABASE_PORT=3306
ENV DATABASE_NAME=newsapp_db
ENV DATABASE_USER=newsapp
ENV DATABASE_PASSWORD=please-change-this-password

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
