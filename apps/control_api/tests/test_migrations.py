"""Empty-database W10 Control Plane migration round-trip."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect


def test_empty_upgrade_current_check_downgrade_upgrade(tmp_path: Path, monkeypatch: object) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setenv("CONTROL_DATABASE_URL", database_url)  # type: ignore[attr-defined]
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "20260729_0001"
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        assert {
            "w10_organizations",
            "w10_users",
            "w10_oidc_identities",
            "w10_memberships",
            "w10_organization_memories",
        } <= tables
        memory_fks = inspector.get_foreign_keys("w10_organization_memories")
        assert any(
            foreign_key["constrained_columns"] == ["organization_id", "owner_user_id"]
            for foreign_key in memory_fks
        )
        memory_indexes = {
            index["name"] for index in inspector.get_indexes("w10_organization_memories")
        }
        assert "ix_w10_memories_org_status_field_id" in memory_indexes
        assert "ix_w10_memories_org_owner_status" in memory_indexes

    command.check(config)
    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert not {
            name for name in inspect(connection).get_table_names() if name.startswith("w10_")
        }
    command.upgrade(config, "head")
    command.check(config)
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "20260729_0001"
    engine.dispose()
