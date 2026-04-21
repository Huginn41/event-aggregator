FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv --break-system-packages && uv sync --frozen --no-dev --system

COPY . .

ENV PYTHONPATH=/app

CMD ["sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]