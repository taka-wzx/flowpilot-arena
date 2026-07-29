from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.schemas import (
    GradeResult,
    JmlInstance,
    PredicateKind,
    PredicateResult,
)
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)

Check = Callable[[], tuple[bool, str]]


def grade_task(session: Session, instance: JmlInstance) -> GradeResult:
    task_id = instance.task_id
    expected = instance.expected_state
    employees = list(
        session.scalars(
            select(Employee).where(Employee.arena_task_id == task_id).order_by(Employee.id)
        )
    )
    tickets = list(
        session.scalars(
            select(OnboardingTicket)
            .where(OnboardingTicket.arena_task_id == task_id)
            .order_by(OnboardingTicket.id)
        )
    )
    accounts = list(
        session.scalars(
            select(IamAccount).where(IamAccount.arena_task_id == task_id).order_by(IamAccount.id)
        )
    )
    assets = list(
        session.scalars(
            select(AssetAssignment)
            .where(AssetAssignment.arena_task_id == task_id)
            .order_by(AssetAssignment.id)
        )
    )
    mailboxes = list(
        session.scalars(
            select(Mailbox).where(Mailbox.arena_task_id == task_id).order_by(Mailbox.id)
        )
    )

    def employee_matches() -> tuple[bool, str]:
        by_id = {item.id: item for item in employees}
        target = by_id.get(expected.target.id)
        decoy = by_id.get(expected.decoy.id)
        passed = len(employees) == 2 and target is not None and decoy is not None
        if passed and target is not None and decoy is not None:
            passed = _employee_equal(target, expected.target) and _employee_equal(
                decoy, expected.decoy
            )
        expected_ids = int(target is not None) + int(decoy is not None)
        return passed, f"owned_employees={len(employees)}; expected_ids={expected_ids}"

    def ticket_matches() -> tuple[bool, str]:
        item = tickets[0] if len(tickets) == 1 else None
        expected_item = expected.ticket
        passed = item is not None and expected_item is not None
        if passed and item is not None and expected_item is not None:
            passed = (
                item.employee_id == expected_item.employee_id
                and item.title == expected_item.title
                and item.status == expected_item.status
            )
        return passed, f"owned_tickets={len(tickets)}"

    def account_matches() -> tuple[bool, str]:
        item = accounts[0] if len(accounts) == 1 else None
        expected_item = expected.account
        passed = item is not None and expected_item is not None
        if passed and item is not None and expected_item is not None:
            passed = (
                item.employee_id == expected_item.employee_id
                and item.username == expected_item.username
                and item.role == expected_item.role
                and item.status == expected_item.status
            )
        return passed, f"owned_accounts={len(accounts)}"

    def asset_matches() -> tuple[bool, str]:
        item = assets[0] if len(assets) == 1 else None
        expected_item = expected.asset
        passed = item is not None and expected_item is not None
        if passed and item is not None and expected_item is not None:
            passed = (
                item.employee_id == expected_item.employee_id
                and item.asset_tag == expected_item.asset_tag
                and item.device_type == expected_item.device_type
                and item.model == expected_item.model
                and item.status == expected_item.status
            )
        return passed, f"owned_assets={len(assets)}"

    def mailbox_matches() -> tuple[bool, str]:
        item = mailboxes[0] if len(mailboxes) == 1 else None
        expected_item = expected.mailbox
        passed = item is not None and expected_item is not None
        if passed and item is not None and expected_item is not None:
            passed = (
                item.employee_id == expected_item.employee_id
                and item.address == expected_item.address
                and item.status == expected_item.status
            )
        return passed, f"owned_mailboxes={len(mailboxes)}"

    checks: tuple[tuple[PredicateKind, Check], ...] = (
        ("employee_matches", employee_matches),
        ("ticket_matches", ticket_matches),
        ("account_matches", account_matches),
        ("asset_matches", asset_matches),
        ("mailbox_matches", mailbox_matches),
    )
    predicates = tuple(_evaluate(kind, check) for kind, check in checks)
    total_score: int = sum(int(item.awarded_points) for item in predicates)
    return GradeResult(
        task_id=task_id,
        instance_checksum=instance.canonical_checksum,
        total_score=total_score,
        passed=total_score == 100 and all(item.passed for item in predicates),
        predicates=predicates,  # type: ignore[arg-type]
    )


def _employee_equal(actual: Employee, expected: object) -> bool:
    return all(
        getattr(actual, field) == getattr(expected, field)
        for field in (
            "id",
            "first_name",
            "last_name",
            "work_email",
            "department",
            "job_title",
            "location",
            "start_date",
            "status",
        )
    )


def _evaluate(kind: PredicateKind, check: Check) -> PredicateResult:
    passed, fact = check()
    return PredicateResult(
        kind=kind,
        weight=20,
        passed=passed,
        awarded_points=20 if passed else 0,
        fact=fact,
    )
