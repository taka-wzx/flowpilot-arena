FROM python:3.13.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev && chmod -R a+rX /app

RUN useradd --create-home --uid 10006 flowpilot-vision
USER flowpilot-vision

EXPOSE 8004

CMD ["uvicorn", "flowpilot_vision_agent.main:app", "--host", "0.0.0.0", "--port", "8004"]
