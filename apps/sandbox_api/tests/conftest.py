from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from flowpilot_sandbox_api.database import get_session
from flowpilot_sandbox_api.main import app
from flowpilot_sandbox_api.models import Base


@pytest.fixture
def db_engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_engine: Engine) -> Iterator[TestClient]:
    def test_session() -> Iterator[Session]:
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()
