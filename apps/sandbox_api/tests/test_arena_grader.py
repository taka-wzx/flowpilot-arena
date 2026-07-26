from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.catalog import get_catalog
from flowpilot_sandbox_api.arena.grader import grade_task
from flowpilot_sandbox_api.arena.schemas import TaskSpec
from flowpilot_sandbox_api.arena.service import reset_seed, task_fact_snapshot
from flowpilot_sandbox_api.models import AssetAssignment, IamAccount, Mailbox, OnboardingTicket


def _complete(
    session: Session,
    spec: TaskSpec,
    *,
    ticket_employee_id: int | None = None,
    elevated_extra: bool = False,
    duplicate_extra: bool = False,
) -> None:
    expected = spec.expected_final_state
    target_id = expected.employee.id
    session.add_all(
        [
            OnboardingTicket(
                employee_id=ticket_employee_id or target_id,
                title=expected.ticket.title,
                status=expected.ticket.status,
                arena_task_id=spec.task_id,
            ),
            IamAccount(
                employee_id=target_id,
                username=expected.iam_account.username,
                role=expected.iam_account.role,
                status=expected.iam_account.status,
                arena_task_id=spec.task_id,
            ),
            AssetAssignment(
                employee_id=target_id,
                asset_tag=expected.asset.asset_tag,
                device_type=expected.asset.device_type,
                model=expected.asset.model,
                status=expected.asset.status,
                arena_task_id=spec.task_id,
            ),
            Mailbox(
                employee_id=target_id,
                address=expected.mailbox.address,
                status=expected.mailbox.status,
                arena_task_id=spec.task_id,
            ),
        ]
    )
    decoy_id = next(
        employee.id for employee in spec.initial_state.employees if employee.kind == "decoy"
    )
    if elevated_extra:
        session.add(
            IamAccount(
                employee_id=decoy_id,
                username=f"elevated.w3{target_id}",
                role="administrator",
                status="active",
                arena_task_id=spec.task_id,
            )
        )
    if duplicate_extra:
        session.add_all(
            [
                OnboardingTicket(
                    employee_id=target_id,
                    title="Extra synthetic onboarding record",
                    status="open",
                    arena_task_id=spec.task_id,
                ),
                AssetAssignment(
                    employee_id=target_id,
                    asset_tag=f"SYN-W3-{target_id - 31000:03d}-EXTRA",
                    device_type="laptop",
                    model="Duplicate Fiction Device",
                    status="assigned",
                    arena_task_id=spec.task_id,
                ),
            ]
        )
    session.commit()


def _fresh_task(session: Session, spec: TaskSpec) -> None:
    reset_seed(session, spec)
    session.rollback()


def test_all_ten_correct_states_score_100_and_grading_is_read_only(db_session: Session) -> None:
    for spec in get_catalog().specs:
        _fresh_task(db_session, spec)
        _complete(db_session, spec)
        before = task_fact_snapshot(db_session, spec.task_id)
        db_session.rollback()

        first = grade_task(db_session, spec)
        second = grade_task(db_session, spec)
        after = task_fact_snapshot(db_session, spec.task_id)
        db_session.rollback()

        assert first == second
        assert first.total_score == 100
        assert first.passed is True
        assert all(item.passed for item in first.predicates)
        assert before == after


def test_untouched_and_partial_states_do_not_pass(db_session: Session) -> None:
    spec = get_catalog().specs[0]
    _fresh_task(db_session, spec)
    untouched = grade_task(db_session, spec)
    db_session.rollback()
    assert untouched.total_score < 100
    assert untouched.passed is False

    db_session.add(
        OnboardingTicket(
            employee_id=spec.expected_final_state.employee.id,
            title=spec.expected_final_state.ticket.title,
            status="open",
            arena_task_id=spec.task_id,
        )
    )
    db_session.commit()
    partial = grade_task(db_session, spec)
    assert untouched.total_score < partial.total_score < 100
    assert partial.passed is False


def test_wrong_association_cannot_pass(db_session: Session) -> None:
    spec = get_catalog().specs[1]
    _fresh_task(db_session, spec)
    decoy_id = next(item.id for item in spec.initial_state.employees if item.kind == "decoy")
    _complete(db_session, spec, ticket_employee_id=decoy_id)

    result = grade_task(db_session, spec)
    failed_kinds = {item.kind for item in result.predicates if not item.passed}
    assert result.passed is False
    assert "ticket_exactly_one_linked" in failed_kinds
    assert "no_wrong_associations" in failed_kinds


def test_elevated_and_duplicate_records_cannot_pass(db_session: Session) -> None:
    elevated_spec = get_catalog().specs[2]
    _fresh_task(db_session, elevated_spec)
    _complete(db_session, elevated_spec, elevated_extra=True)
    elevated = grade_task(db_session, elevated_spec)
    assert elevated.passed is False
    assert (
        next(item for item in elevated.predicates if item.kind == "iam_no_elevated_role").passed
        is False
    )

    db_session.rollback()
    duplicate_spec = get_catalog().specs[3]
    _fresh_task(db_session, duplicate_spec)
    _complete(db_session, duplicate_spec, duplicate_extra=True)
    duplicate = grade_task(db_session, duplicate_spec)
    assert duplicate.passed is False
    assert (
        next(
            item for item in duplicate.predicates if item.kind == "no_duplicate_business_records"
        ).passed
        is False
    )
