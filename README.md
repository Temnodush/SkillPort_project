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

## Деплой на сервер (venv + Gunicorn + Nginx + systemd)

Продовый запуск отличается от локального: приложение работает под **Gunicorn**, перед ним стоит
**Nginx**, а автозапуск и авто-перезапуск обеспечивает **systemd**. Docker on сервере не используется —
там применяется схема из урока по ручному деплою.

```
браузер → Nginx (:80) → Gunicorn (127.0.0.1:8000) → Django
                       └─ /static/ и /media/ Nginx отдаёт сам с диска
```

### Что установлено на сервере (Ubuntu 24.04)

| Компонент | Назначение |
|---|---|
| Python 3.12 + `python3-venv` | окружение приложения (версия совпадает с Django 6) |
| PostgreSQL 16 | база данных, слушает только `127.0.0.1:5432` |
| Redis 7 | брокер Celery, слушает только `127.0.0.1:6379` |
| Gunicorn | WSGI-сервер приложения, слушает только `127.0.0.1:8000` |
| Nginx 1.24 | приём запросов на порт 80, отдача статики, прокси на Gunicorn |
| systemd | юнит `skillport.service`: автозапуск и авто-перезапуск |

### Файлы деплоя в репозитории

| Файл | Назначение |
|---|---|
| `.setup/skillport.service` | systemd-юнит для Gunicorn (`Restart=always`) |
| `.setup/nginx.conf` | конфиг Nginx: `proxy_pass` на Gunicorn + раздача статики |
| `.github/workflows/deploy.yml` | CI/CD: линт → тесты → проверка → деплой |

### Разовая настройка сервера

```bash
# 1. Пакеты
sudo apt update && sudo apt install -y \
  python3-venv python3-dev build-essential libpq-dev \
  postgresql postgresql-contrib redis-server nginx git

sudo systemctl enable --now postgresql redis-server nginx

# 2. Файрвол: наружу открыты только SSH, HTTP и HTTPS
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable

# 3. Пользователь и база данных
sudo -u postgres psql -c "CREATE ROLE skillport LOGIN PASSWORD 'ПАРОЛЬ';"
sudo -u postgres createdb -O skillport skillport
sudo -u postgres psql -c "ALTER ROLE skillport CREATEDB;"   # нужно для запуска тестов

# 4. Код и виртуальное окружение (venv намеренно лежит вне каталога проекта)
sudo mkdir -p /var/www && sudo chown -R "$USER":"$USER" /var/www
git clone git@github.com:Temnodush/SkillPort_project.git /var/www/SkillPort_project
python3 -m venv /var/www/skillport-venv
/var/www/skillport-venv/bin/pip install -r /var/www/SkillPort_project/requirements.txt

# 5. Файл .env (в репозиторий не попадает) — создаётся из .env_example
nano /var/www/SkillPort_project/.env
chmod 600 /var/www/SkillPort_project/.env

# 6. Миграции, статика, сервисы
cd /var/www/SkillPort_project
/var/www/skillport-venv/bin/python manage.py migrate --noinput
/var/www/skillport-venv/bin/python manage.py collectstatic --noinput

sudo cp .setup/skillport.service /etc/systemd/system/skillport.service
sudo cp .setup/nginx.conf /etc/nginx/sites-available/skillport
sudo ln -sf /etc/nginx/sites-available/skillport /etc/nginx/sites-enabled/skillport
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now skillport
sudo nginx -t && sudo systemctl restart nginx
```

### Разрешение на перезапуск сервиса без пароля

Workflow деплоя выполняет `sudo systemctl restart skillport.service` по SSH. Чтобы команда
не запрашивала пароль, добавьте правило sudoers:

```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart skillport.service, /usr/bin/systemctl status skillport.service" | sudo tee /etc/sudoers.d/skillport
sudo chmod 440 /etc/sudoers.d/skillport
sudo visudo -c
```

### Управление приложением

```bash
sudo systemctl status skillport        # состояние
sudo systemctl restart skillport       # перезапуск
journalctl -u skillport -f             # логи приложения
sudo tail -f /var/log/nginx/error.log  # логи Nginx
sudo nginx -t                          # проверка конфига Nginx
```

После перезагрузки сервера приложение поднимается автоматически: `systemctl enable` для
`postgresql`, `redis-server`, `nginx` и `skillport` включён.

## CI/CD: GitHub Actions

Workflow `.github/workflows/deploy.yml` запускается при каждом `push` и `pull_request`
и состоит из четырёх последовательных этапов. Каждый следующий запускается только при
успехе предыдущего (`needs`) — падение тестов или линтера **останавливает** весь пайплайн,
и на сервер ничего не выкладывается.

| Этап | Job | Что делает |
|---|---|---|
| 1 | `lint` | `flake8` по коду проекта |
| 2 | `test` | `python manage.py test` на PostgreSQL 16 (сервисный контейнер) |
| 3 | `build` | `manage.py check --deploy` с боевыми настройками (`DEBUG=False`) |
| 4 | `deploy` | по SSH: `rsync` → `pip install` → `migrate` → `collectstatic` → `systemctl restart` |

### Секреты репозитория

Настраиваются в GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

| Секрет | Значение | Пример |
|---|---|---|
| `SERVER_IP` | публичный IP сервера | `81.26.176.220` |
| `SSH_USER` | пользователь для SSH | `novotropsk` |
| `SSH_KEY` | приватный SSH-ключ | содержимое `~/.ssh/id_ed25519` |
| `DEPLOY_DIR` | каталог проекта на сервере | `/var/www/SkillPort_project` |
| `SECRET_KEY` | секретный ключ Django | результат `get_random_secret_key()` |

`SECRET_KEY` используется в job-ах `test` и `build`. Отдельный шаг проверяет, что секрет
действительно получен из GitHub Secrets, и печатает только его длину — сам ключ в логах
не появляется.

Секреты самого приложения (пароль БД, ключи Stripe, пароль почты) хранятся в файле `.env`
**на сервере** и в репозиторий не попадают: он перечислен в `.gitignore` (не уедет в git)
и в `.dockerignore` (не попадёт в образ). Деплой исключает `.env` из `rsync`, поэтому
обновление кода не затирает настройки сервера.

### Проверка после деплоя

1. Открыть `http://<SERVER_IP>/api/schema/swagger-ui/` — документация API.
2. `http://<SERVER_IP>/admin/` — админка Django.
3. Снаружи порт `8000` недоступен: `curl -m 5 http://<SERVER_IP>:8000` завершается ошибкой,
   потому что Gunicorn слушает только `127.0.0.1`. Порты `5432` и `6379` закрыты так же.
4. Авто-перезапуск: `sudo reboot`, после загрузки приложение отвечает без ручного запуска.

## Структура проекта

```
.
├── .github/workflows/   # CI/CD: линт → тесты → build → деплой по SSH
├── .setup/              # файлы деплоя: skillport.service, nginx.conf
├── config/              # настройки проекта: settings.py, urls.py, celery.py
├── education/           # приложение курсов и уроков (+ фикстуры)
├── users/               # приложение пользователей, подписок и оплат (+ фикстуры)
├── Dockerfile           # образ для локального запуска через docker compose
├── docker-compose.yml   # локальная разработка: web, db, redis, celery, beat
├── .flake8              # настройки линтера
├── .dockerignore        # что не попадает в образ (в т.ч. .env)
├── .env_example         # шаблон переменных окружения (скопировать в .env)
├── requirements.txt     # зависимости проекта
└── manage.py
```
