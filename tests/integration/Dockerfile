FROM python:3.13.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/smoke/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

WORKDIR /smoke

RUN pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY w4_compose_smoke.py w4_real_model_acceptance.py w5_vision_compose_smoke.py w6_hybrid_compose_smoke.py w7_planning_compose_smoke.py w8_recovery_compose_smoke.py w8_restart_driver.py w9_context_compose_smoke.py ./

RUN useradd --create-home --uid 10005 flowpilot-acceptance
USER flowpilot-acceptance

CMD ["python", "w4_compose_smoke.py"]
