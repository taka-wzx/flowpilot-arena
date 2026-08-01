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
        assert MigrationContext.configure(connection).get_current_revision() == "20260729_0002"
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        assert {
            "w10_organizations",
            "w10_users",
            "w10_oidc_identities",
            "w10_memberships",
            "w10_organization_memories",
            "w11_approval_authorities",
            "w11_approval_requests",
            "w11_approval_decisions",
            "w11_approval_grants",
            "w11_audit_chain_heads",
            "w11_audit_events",
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
        authority_indexes = {
            index["name"] for index in inspector.get_indexes("w11_approval_authorities")
        }
        assert "ix_w11_authorities_org_status_role_user" in authority_indexes
        grant_indexes = {index["name"] for index in inspector.get_indexes("w11_approval_grants")}
        assert "ix_w11_grants_org_status_expiry_id" in grant_indexes
        request_checks = {
            item["name"] for item in inspector.get_check_constraints("w11_approval_requests")
        }
        assert {
            "ck_w11_request_action",
            "ck_w11_request_risk_roles_action",
            "ck_w11_request_closed_reason",
        } <= request_checks
        decision_fks = inspector.get_foreign_keys("w11_approval_decisions")
        assert any(
            item["constrained_columns"]
            == ["organization_id", "request_id", "action_type", "parameter_hash"]
            for item in decision_fks
        )
        assert any(
            item["constrained_columns"]
            == ["organization_id", "authority_id", "approver_user_id", "approval_role"]
            for item in decision_fks
        )
        grant_fks = inspector.get_foreign_keys("w11_approval_grants")
        assert any(
            item["constrained_columns"]
            == [
                "organization_id",
                "request_id",
                "action_type",
                "parameter_hash",
                "risk_level",
                "executor_user_id",
            ]
            for item in grant_fks
        )
        triggers = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'trg_w11_%'"
            )
        }
        assert len(triggers) == 4

    command.check(config)
    command.downgrade(config, "20260729_0001")
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        assert "w10_organizations" in tables
        assert not {name for name in tables if name.startswith("w11_")}
    command.upgrade(config, "head")
    command.check(config)
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "20260729_0002"
    engine.dispose()
