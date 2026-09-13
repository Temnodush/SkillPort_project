# SkillPort

Backend платформы онлайн-обучения на Django REST Framework: курсы и уроки, пользователи с
JWT-авторизацией, подписки на обновления курсов, оплата через Stripe, отложенные задачи на Celery.

Проект полностью запускается одной командой через **Docker Compose**: приложение, база данных,
Redis, воркер и планировщик Celery поднимаются вместе, миграции применяются автоматически.

## Стек

| Технология | Назначение |
|---|---|
| Python 3.12, Django 6, DRF | API приложения |
| PostgreSQL 16 | основная база данных |
| Redis 7 | брокер сообщений и result backend Celery |
| Celery + django-celery-beat | фоновые и периодические задачи |
| drf-spectacular | документация API (Swagger / Redoc) |
| Stripe | приём оплаты курсов |

## Требования

- [Docker](https://docs.docker.com/get-docker/) (Docker Desktop для Windows/macOS);
- Docker Compose (входит в Docker Desktop). Проверить: `docker compose version`.

## Запуск проекта

1. Склонируйте репозиторий и перейдите в его папку.

2. Создайте файл `.env` из шаблона:

   ```bash
   # Linux / macOS
   cp .env_example .env

   # Windows (cmd)
   copy .env_example .env
   ```

3. Заполните переменные в `.env` (см. раздел «Переменные окружения»).
   Для запуска через Docker достаточно указать `SECRET_KEY` и ключи Stripe —
   остальные значения уже подставлены в `.env_example`.

4. Соберите образы и поднимите все сервисы:

   ```bash
   docker compose up --build
   ```

   Первый запуск занимает несколько минут (сборка образа, установка зависимостей,
   инициализация базы). Миграции применяются автоматически сервисом `migrations`.

5. Приложение доступно по адресам:

   | Адрес | Описание |
   |---|---|
   | http://localhost:8000/api/schema/swagger-ui/ | Swagger UI — вся документация API |
   | http://localhost:8000/api/schema/redoc/ | Redoc |
   | http://localhost:8000/admin/ | Админка Django |
   | http://localhost:8000/api/ | корень API |

6. Остановить проект: `Ctrl+C`, затем удалить контейнеры:

   ```bash
   docker compose down          # остановить и удалить контейнеры (данные сохранятся)
   docker compose down -v       # + удалить тома (полностью очистить БД и Redis)
   ```

## Сервисы

| Сервис | Что это | Доступ извне | Данные |
|---|---|---|---|
| `web` | Django + DRF (`runserver 0.0.0.0:8000`) | `ports: 8000:8000` | код с хоста + том `media_data` |
| `db` | PostgreSQL 16 | `expose: 5432` — только внутри docker-сети | том `postgres_data` |
| `redis` | Redis 7 (брокер Celery, appendonly) | `expose: 6379` — только внутри docker-сети | том `redis_data` |
| `migrations` | одноразовый сервис: `manage.py migrate`, завершается | нет | — |
| `celery` | воркер Celery (`celery -A config worker`) | нет | код с хоста |
| `celery-beat` | планировщик периодических задач (`celery -A config beat`) | нет | код с хоста |

Порты `db` и `redis` наружу не публикуются: снаружи они не нужны, связь идёт по внутренней
docker-сети `skillport` по именам сервисов (`db`, `redis`).

## Переменные окружения

Все переменные хранятся в файле `.env` (в репозиторий не попадает, см. `.gitignore`).
Шаблон — `.env_example`.

| Переменная | Описание | Пример |
|---|---|---|
| `SECRET_KEY` | секретный ключ Django | `django-insecure-...` |
| `DEBUG` | режим отладки (`True` для разработки) | `True` |
| `POSTGRES_DB` | имя базы данных | `skillport` |
| `POSTGRES_USER` | пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | пароль пользователя БД | `postgres` |
| `POSTGRES_HOST` | хост БД | `localhost` (в Docker — `db`) |
| `POSTGRES_PORT` | порт БД | `5432` |
| `REDIS_HOST` | хост Redis | `localhost` (в Docker — `redis`) |
| `REDIS_PORT` | порт Redis | `6379` |
| `STRIPE_SECRET_KEY` | секретный ключ Stripe | `sk_test_...` |
| `STRIPE_PUBLISHABLE_KEY` | публичный ключ Stripe | `pk_test_...` |

`POSTGRES_HOST` и `REDIS_HOST` со значением `localhost` нужны для запуска без Docker;
внутри docker-сети `docker-compose.yml` переопределяет их на имена сервисов `db` и `redis`.

Файл `.env` подключается к сервисам через `env_file` и исключён из образа через `.dockerignore`,
поэтому секреты не попадают ни в репозиторий, ни в собранный образ.

## Работа с приложением

Все команды выполняются внутри контейнера `web`:

```bash
# создать суперпользователя для админки
docker compose exec web python manage.py createsuperuser

# создать группу «Модераторы» с правами на курсы и уроки
docker compose exec web python manage.py create_groups

# загрузить тестовые данные (фикстуры)
docker compose exec web python manage.py loaddata users/fixtures/users.json
docker compose exec web python manage.py loaddata education/fixtures/courses.json
docker compose exec web python manage.py loaddata education/fixtures/lessons.json
docker compose exec web python manage.py loaddata users/fixtures/payment.json

# тесты
docker compose exec web python manage.py test

# произвольная management-команда
docker compose exec web python manage.py shell
```

Получение JWT-токена:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Основные эндпоинты: `/api/courses/`, `/api/lessons/`, `/api/users/`, `/api/register/`,
`/api/token/`, `/api/token/refresh/`, `/api/payments/`, `/api/payments/create/`,
`/api/courses/subscribe/`. Полный список — в Swagger UI.

## Полезные команды

```bash
docker compose up --build -d        # запустить в фоне
docker compose ps                   # статус сервисов
docker compose logs -f web          # логи приложения
docker compose logs -f celery       # логи воркера
docker compose exec web bash        # зайти внутрь контейнера
docker compose up --build           # пересобрать после изменения requirements.txt
docker compose down                 # остановить проект
```

## Запуск без Docker (опционально)

1. Установите зависимости: `pip install -r requirements.txt`.
2. Поднимите PostgreSQL и Redis локально — на портах `5432` и `6379`
   (порты сервисов `db` и `redis` из `docker-compose.yml` наружу не публикуются,
   поэтому локальный запуск использует собственные установленные сервисы).
3. В `.env` укажите `POSTGRES_HOST=localhost` и `REDIS_HOST=localhost`.
4. Примените миграции и запустите сервер:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. Отдельно запустите Celery (в отдельных терминалах):

   ```bash
   celery -A config worker -l info
   celery -A config beat -l info
   ```

## Структура проекта

```
.
├── config/              # настройки проекта: settings.py, urls.py, celery.py
├── education/           # приложение курсов и уроков (+ фикстуры)
├── users/               # приложение пользователей, подписок и оплат (+ фикстуры)
├── Dockerfile           # образ для web / celery / celery-beat / migrations
├── docker-compose.yml   # описание всех сервисов проекта
├── .dockerignore        # что не попадает в образ (в т.ч. .env)
├── .env_example         # шаблон переменных окружения
├── requirements.txt     # зависимости проекта
└── manage.py
```
