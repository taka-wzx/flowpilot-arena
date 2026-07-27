FROM python:3.13.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /smoke
COPY w4_compose_smoke.py w4_real_model_acceptance.py w5_vision_compose_smoke.py ./

RUN useradd --create-home --uid 10005 flowpilot-acceptance
USER flowpilot-acceptance

CMD ["python", "w4_compose_smoke.py"]
