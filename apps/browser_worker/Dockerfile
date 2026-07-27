FROM python:3.13.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project \
    && .venv/bin/playwright install --with-deps chromium

COPY src ./src
RUN uv sync --locked --no-dev && chmod -R a+rX /ms-playwright /app

RUN useradd --create-home --uid 10003 flowpilot-browser
USER flowpilot-browser

EXPOSE 8002

CMD ["uvicorn", "flowpilot_browser_worker.main:app", "--host", "0.0.0.0", "--port", "8002"]
