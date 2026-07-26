FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev

RUN useradd --create-home --uid 10001 flowpilot
USER flowpilot

EXPOSE 8000

CMD ["uvicorn", "flowpilot_control_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
