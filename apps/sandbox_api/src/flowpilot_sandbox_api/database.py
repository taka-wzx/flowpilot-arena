import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://flowpilot:flowpilot_local_only@postgres:5432/flowpilot_sandbox"
)


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def build_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or get_database_url(), pool_pre_ping=True)


engine = build_engine()


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
