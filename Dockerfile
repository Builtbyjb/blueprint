FROM python:3.9-slim

WORKDIR /app

COPY . .

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /uvx /bin/

RUN uv sync --frozen --nocache

# Run application
CMD ["/app/.venv/bin/uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3000"]
