# Единый образ для всех python-сервисов проекта:
# web, celery, celery-beat, migrations (см. docker-compose.yml)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq-dev нужен для psycopg2, gcc — на случай сборки пакетов без готовых wheel
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Зависимости копируются отдельно: слой кэшируется и не пересобирается при правках кода
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Код проекта (.env, .venv, __pycache__ и прочее исключены через .dockerignore)
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
