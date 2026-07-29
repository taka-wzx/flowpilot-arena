from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.catalog import get_catalog
from flowpilot_sandbox_api.arena.jml.service import reset_seed


def test_reset_seed_is_deterministic_for_all_non_reporting_instances(
    db_session: Session,
) -> None:
    executable = [item for item in get_catalog().instances if item.split != "reporting"]
    assert len(executable) == 72
    for instance in executable:
        first = reset_seed(db_session, instance)
        db_session.rollback()
        second = reset_seed(db_session, instance)
        assert first == second
        assert first.counts.employees == 2
        expected_downstream = 0 if instance.process == "joiner" else 1
        assert first.counts.tickets == expected_downstream
        assert first.counts.iam_accounts == expected_downstream
        assert first.counts.assets == expected_downstream
        assert first.counts.mailboxes == expected_downstream
        db_session.rollback()


def test_reporting_instances_are_generated_and_frozen_without_runtime_use() -> None:
    reporting = [item for item in get_catalog().instances if item.split == "reporting"]
    assert len(reporting) == 18
    assert len({item.canonical_checksum for item in reporting}) == 18
