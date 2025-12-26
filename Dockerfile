FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY src/ src/

COPY data/rules/ data/rules/
COPY data/notes/ data/notes/

EXPOSE 8080

CMD ["uv", "run", "coach"]
