from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.catalog import get_catalog
from flowpilot_sandbox_api.arena.jml.grader import grade_task
from flowpilot_sandbox_api.arena.jml.service import reset_seed
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)


def _complete(db_session: Session, task_id: str) -> None:
    instance = get_catalog().get(task_id)
    expected = instance.expected_state
    target = db_session.get(Employee, expected.target.id)
    assert target is not None
    for field in ("department", "job_title", "location", "status"):
        setattr(target, field, getattr(expected.target, field))

    model_and_fact = (
        (OnboardingTicket, expected.ticket),
        (IamAccount, expected.account),
        (AssetAssignment, expected.asset),
        (Mailbox, expected.mailbox),
    )
    for model, fact in model_and_fact:
        assert fact is not None
        record = db_session.get(model, fact.id)
        if record is None:
            db_session.add(model(**fact.model_dump(), arena_task_id=task_id))
        else:
            for field, value in fact.model_dump(exclude={"id"}).items():
                setattr(record, field, value)
    db_session.commit()


def test_joiner_mover_and_leaver_grade_only_database_facts(db_session: Session) -> None:
    task_ids = (
        "w7-jml-joiner-001-v1",
        "w7-jml-mover-001-v1",
        "w7-jml-leaver-001-v1",
    )
    for task_id in task_ids:
        instance = get_catalog().get(task_id)
        reset_seed(db_session, instance)
        db_session.rollback()
        untouched = grade_task(db_session, instance)
        assert not untouched.passed
        assert untouched.total_score < 100
        db_session.rollback()
        _complete(db_session, task_id)
        first = grade_task(db_session, instance)
        second = grade_task(db_session, instance)
        assert first == second
        assert first.total_score == 100
        assert first.passed
        db_session.rollback()
