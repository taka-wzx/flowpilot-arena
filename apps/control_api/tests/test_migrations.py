"""Empty-database W12 Control Plane migration round-trip."""

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
        assert MigrationContext.configure(connection).get_current_revision() == "20260803_0004"
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
            "w12_production_runs",
            "w12_dispatch_outbox",
            "w12_worker_leases",
            "w12_scheduler_partitions",
            "w12_rate_limit_buckets",
            "w12_idempotency_records",
            "w13_observability_events",
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
        w12_triggers = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'trg_w12_%'"
            )
        }
        assert len(w12_triggers) == 4
        w13_triggers = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'trg_w13_%'"
            )
        }
        assert len(w13_triggers) == 2
        run_fks = inspector.get_foreign_keys("w12_production_runs")
        assert any(
            item["constrained_columns"] == ["organization_id", "executor_user_id"]
            for item in run_fks
        )
        outbox_indexes = {item["name"] for item in inspector.get_indexes("w12_dispatch_outbox")}
        assert {
            "ix_w12_outbox_org_status_available",
            "ix_w12_outbox_status_lease_expiry",
        } <= outbox_indexes
        run_checks = {
            item["name"]: item["sqltext"]
            for item in inspector.get_check_constraints("w12_production_runs")
        }
        assert {"ck_w12_run_task", "ck_w12_run_task_binding"} <= set(run_checks)
        task_check = str(run_checks["ck_w12_run_task"])
        for task_id in (
            "w7-jml-joiner-001-v1",
            "w7-jml-joiner-001-v2",
            "w7-jml-joiner-002-v1",
            "w7-jml-joiner-002-v2",
            "w7-jml-mover-001-v1",
            "w7-jml-mover-001-v2",
            "w7-jml-leaver-001-v1",
            "w7-jml-leaver-001-v2",
        ):
            assert task_id in task_check
        binding_check = str(run_checks["ck_w12_run_task_binding"])
        assert "process = 'joiner'" in binding_check
        assert "category = 'standard_joiner'" in binding_check
        assert "process = 'mover'" in binding_check
        assert "category = 'standard_mover'" in binding_check
        assert "process = 'leaver'" in binding_check
        assert "category = 'standard_leaver'" in binding_check
        w13_indexes = {item["name"] for item in inspector.get_indexes("w13_observability_events")}
        assert {
            "ix_w13_events_org_run_sequence",
            "ix_w13_events_org_phase_status",
        } <= w13_indexes
        w13_checks = {
            item["name"]: item["sqltext"]
            for item in inspector.get_check_constraints("w13_observability_events")
        }
        assert {
            "ck_w13_phase",
            "ck_w13_status",
            "ck_w13_failure_category",
            "ck_w13_reason",
            "ck_w13_attributes_size",
        } <= set(w13_checks)
        assert "browser_timeout" in str(w13_checks["ck_w13_failure_category"])
        assert "fake_cost_accounted" in str(w13_checks["ck_w13_reason"])

    command.check(config)
    command.downgrade(config, "20260801_0003")
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        assert "w12_production_runs" in tables
        assert "w13_observability_events" not in tables
    command.downgrade(config, "20260729_0002")
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        assert "w10_organizations" in tables
        assert "w11_audit_events" in tables
        assert not {name for name in tables if name.startswith("w12_")}
        assert not {name for name in tables if name.startswith("w13_")}
    command.upgrade(config, "head")
    command.check(config)
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "20260803_0004"
    engine.dispose()
