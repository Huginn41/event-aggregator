# Events Aggregator

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-compose-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)

REST API сервис для агрегации мероприятий от внешнего провайдера.
Автоматически синхронизирует события по расписанию, предоставляет 
пагинированный API для просмотра мероприятий и управления билетами.

**Ключевые решения:**
- Фоновая синхронизация через `asyncio` — не блокирует основной поток
- Repository pattern — бизнес-логика отделена от слоя данных
- Интеграционные тесты покрывают все эндпоинты
- CI/CD через GitHub Actions

## Стек

- **Python 3.12**, FastAPI, SQLAlchemy (async), asyncpg
- **PostgreSQL** — основная база данных
- **Alembic** — миграции
- **httpx** — HTTP-клиент для внешнего провайдера
- **uv** — менеджер зависимостей

## Структура проекта

```
├── api/
│   ├── router.py       # Эндпоинты
│   ├── schemas.py      # Pydantic-схемы
│   └── usecases.py     # Бизнес-логика
├── core/
│   ├── cache.py        # Кэш мест
│   └── config.py       # Настройки (pydantic-settings)
├── database/
│   ├── db.py           # Движок и сессии SQLAlchemy
│   ├── models.py       # ORM-модели
│   └── repositories.py # Слой доступа к данным
├── provider/
│   ├── client.py       # HTTP-клиент провайдера событий
│   └── paginator.py    # Постраничный обход API провайдера
├── sync/
│   └── sync_worker.py  # Фоновая синхронизация событий
├── alembic/            # Миграции БД
├── tests/              # Тесты
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Локальный запуск

### Через Docker Compose

1. Скопируй `.env.template` в `.env` и заполни переменные:

```bash
cp .env.template .env
```

2. Укажи `EVENTS_API_KEY` в `.env`:

```env
EVENTS_API_KEY=твой_ключ
```

3. Запусти:

```bash
docker-compose --env-file .env up --build
```

Миграции применятся автоматически при старте. Сервис будет доступен на `http://localhost:8000`.

### Остановка

```bash
# Остановить контейнеры
docker-compose down

# Остановить и удалить данные БД
docker-compose down -v
```

### Без Docker (для разработки)

1. Установи [uv](https://docs.astral.sh/uv/):

```bash
pip install uv
```

2. Установи зависимости:

```bash
uv sync
```

3. Создай `.env` на основе `.env.template` и заполни переменные.

4. Примени миграции:

```bash
uv run alembic upgrade head
```

5. Запусти сервис:

```bash
uv run uvicorn main:app --reload
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `POSTGRES_USERNAME` | Пользователь БД | — |
| `POSTGRES_PASSWORD` | Пароль БД | — |
| `POSTGRES_DATABASE_NAME` | Имя базы данных | — |
| `POSTGRES_CONNECTION_STRING` | Полная строка подключения (приоритет над отдельными полями) | — |
| `EVENTS_API_KEY` | Ключ API провайдера событий | — |
| `EVENTS_API_URL` | URL провайдера событий | `http://events-provider.dev-2.python-labs.ru` |
| `SYNC_INTERVAL_HOURS` | Интервал автосинхронизации (часы) | `24` |
| `SEATS_CACHE_TTL_SECONDS` | TTL кэша мест (секунды) | `30` |

## API

Полная документация доступна по адресу `http://localhost:8000/docs` после запуска.

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/health` | Проверка работоспособности |
| `GET` | `/api/events` | Список событий (с пагинацией и фильтром по дате) |
| `GET` | `/api/events/{event_id}` | Детали события |
| `GET` | `/api/events/{event_id}/seats` | Доступные места |
| `POST` | `/api/tickets` | Регистрация билета |
| `DELETE` | `/api/tickets/{ticket_id}` | Отмена билета |
| `POST` | `/api/sync/trigger` | Запуск синхронизации вручную |

### Примеры запросов

```bash
# Список событий с фильтрацией по дате
curl "http://localhost:8000/api/events?date_from=2026-04-22&page=1&page_size=20"

# Доступные места для события
curl "http://localhost:8000/api/events/{event_id}/seats"

# Регистрация билета
curl -X POST "http://localhost:8000/api/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "uuid",
    "first_name": "Иван",
    "last_name": "Петров",
    "email": "ivan@example.com",
    "seat": "A1"
  }'

# Отмена билета
curl -X DELETE "http://localhost:8000/api/tickets/{ticket_id}"
```

## Синхронизация данных

При старте сервис автоматически запускает синхронизацию событий от внешнего провайдера. Повторная синхронизация происходит каждые `SYNC_INTERVAL_HOURS` часов. Также можно запустить синхронизацию вручную через `POST /api/sync/trigger`.

## Разработка

```bash
# Линтинг
uv run ruff check .

# Автоисправление
uv run ruff check --fix .

# Тесты
uv run pytest
```
