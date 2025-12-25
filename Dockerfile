FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml .

RUN uv sync --system --group dev

COPY src/ src/
COPY .env.example .

EXPOSE 8080

CMD ["uv", "run", "coach"]
