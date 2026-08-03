FROM python:3.13.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/load/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

WORKDIR /load

RUN pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY frozen-profile.json result.schema.json profile.py locustfile.py run_profile.py ./

RUN groupadd --gid 10020 flowpilot-results \
    && useradd --create-home --uid 10013 --groups flowpilot-results flowpilot-load \
    && mkdir /results \
    && chown root:flowpilot-results /results \
    && chmod 2770 /results \
    && chmod -R a+rX /load
USER flowpilot-load

CMD ["python", "run_profile.py", "--development"]
