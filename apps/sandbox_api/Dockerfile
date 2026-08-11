FROM python:3.13.14-alpine3.24@sha256:c25cd44f45df1279a2cba589e67dfcd9db04647ea483b117a7de8b1a99bdfb23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.12.3"

COPY pyproject.toml uv.lock alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --locked --no-dev --no-cache \
    && /usr/local/bin/python -m pip uninstall --yes uv pip

RUN adduser -D -u 10002 flowpilot
USER flowpilot

EXPOSE 8001

CMD ["uvicorn", "flowpilot_sandbox_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
