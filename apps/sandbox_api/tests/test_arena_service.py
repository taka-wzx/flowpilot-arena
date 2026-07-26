import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.catalog import get_catalog
from flowpilot_sandbox_api.arena.service import reset_seed, task_fact_snapshot
from flowpilot_sandbox_api.models import Employee, OnboardingTicket


def test_every_task_reset_seed_is_idempotent_and_deterministic(db_session: Session) -> None:
    for spec in get_catalog().specs:
        first = reset_seed(db_session, spec)
        first_snapshot = task_fact_snapshot(db_session, spec.task_id)
        db_session.rollback()

        db_session.add(
            OnboardingTicket(
                employee_id=spec.expected_final_state.employee.id,
                title="Task-owned residue",
                status="open",
                arena_task_id=spec.task_id,
            )
        )
        db_session.commit()

        second = reset_seed(db_session, spec)
        second_snapshot = task_fact_snapshot(db_session, spec.task_id)
        db_session.rollback()

        assert first == second
        assert first_snapshot == second_snapshot
        assert first.seed_summary.counts.model_dump() == {
            "employees": 2,
            "tickets": 0,
            "iam_accounts": 0,
            "assets": 0,
            "mailboxes": 0,
        }


def test_reset_preserves_unowned_w2_records(db_session: Session) -> None:
    unowned = Employee(
        id=77,
        first_name="W2",
        last_name="Example",
        work_email="w2.preserved@flowpilot.invalid",
        department="Manual Sandbox",
        job_title="Development Example",
        location="Local Fiction Lab",
        start_date=get_catalog().specs[0].expected_final_state.employee.start_date,
        status="confirmed",
    )
    db_session.add(unowned)
    db_session.commit()

    spec = get_catalog().specs[0]
    reset_seed(db_session, spec)
    db_session.rollback()
    reset_seed(db_session, spec)
    db_session.rollback()

    assert db_session.get(Employee, 77) is not None
    assert db_session.get(Employee, 77).arena_task_id is None


def test_seed_conflict_rolls_back_without_touching_unowned_record(db_session: Session) -> None:
    spec = get_catalog().specs[0]
    target = spec.expected_final_state.employee
    db_session.add(
        Employee(
            **target.model_dump(),
            arena_task_id=None,
        )
    )
    db_session.commit()

    with pytest.raises(IntegrityError):
        reset_seed(db_session, spec)
    db_session.rollback()

    preserved = db_session.get(Employee, target.id)
    assert preserved is not None
    assert preserved.arena_task_id is None
    assert task_fact_snapshot(db_session, spec.task_id) == {
        "employees": [],
        "tickets": [],
        "iam_accounts": [],
        "assets": [],
        "mailboxes": [],
    }
