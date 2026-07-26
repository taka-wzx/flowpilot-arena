from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.schemas import (
    GradeResult,
    GraderPredicate,
    PredicateKind,
    PredicateResult,
    TaskSpec,
)
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)

PredicateCheck = Callable[[], tuple[bool, str]]
DownstreamFact = OnboardingTicket | IamAccount | AssetAssignment | Mailbox


def grade_task(session: Session, spec: TaskSpec) -> GradeResult:
    task_id = spec.task_id
    expected = spec.expected_final_state
    target_id = expected.employee.id

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

    expected_tickets = list(
        session.scalars(
            select(OnboardingTicket)
            .where(OnboardingTicket.title == expected.ticket.title)
            .order_by(OnboardingTicket.id)
        )
    )
    expected_accounts = list(
        session.scalars(
            select(IamAccount)
            .where(IamAccount.username == expected.iam_account.username)
            .order_by(IamAccount.id)
        )
    )
    expected_assets = list(
        session.scalars(
            select(AssetAssignment)
            .where(AssetAssignment.asset_tag == expected.asset.asset_tag)
            .order_by(AssetAssignment.id)
        )
    )
    expected_mailboxes = list(
        session.scalars(
            select(Mailbox).where(Mailbox.address == expected.mailbox.address).order_by(Mailbox.id)
        )
    )

    def employee_matches() -> tuple[bool, str]:
        matches = [item for item in employees if item.id == target_id]
        passed = len(matches) == 1
        if passed:
            item = matches[0]
            passed = (
                item.first_name == expected.employee.first_name
                and item.last_name == expected.employee.last_name
                and item.work_email == expected.employee.work_email
                and item.department == expected.employee.department
                and item.job_title == expected.employee.job_title
                and item.location == expected.employee.location
                and item.start_date == expected.employee.start_date
                and item.status == expected.employee.status
            )
        return passed, f"target_matches={int(passed)}; owned_employees={len(employees)}"

    def ticket_exactly_one_linked() -> tuple[bool, str]:
        passed = len(tickets) == 1 and len(expected_tickets) == 1
        if passed:
            item = tickets[0]
            passed = (
                item.id == expected_tickets[0].id
                and item.employee_id == target_id
                and item.title == expected.ticket.title
                and item.status == expected.ticket.status
            )
        return passed, f"owned_tickets={len(tickets)}; expected_title_rows={len(expected_tickets)}"

    def iam_exactly_one_linked() -> tuple[bool, str]:
        passed = len(accounts) == 1 and len(expected_accounts) == 1
        if passed:
            item = accounts[0]
            passed = (
                item.id == expected_accounts[0].id
                and item.employee_id == target_id
                and item.username == expected.iam_account.username
                and item.role == expected.iam_account.role
                and item.status == expected.iam_account.status
            )
        return (
            passed,
            f"owned_accounts={len(accounts)}; expected_username_rows={len(expected_accounts)}",
        )

    def iam_no_elevated_role() -> tuple[bool, str]:
        elevated = sum(item.role != "employee" for item in accounts)
        return elevated == 0, f"elevated_accounts={elevated}; owned_accounts={len(accounts)}"

    def asset_exactly_one_linked() -> tuple[bool, str]:
        passed = len(assets) == 1 and len(expected_assets) == 1
        if passed:
            item = assets[0]
            passed = (
                item.id == expected_assets[0].id
                and item.employee_id == target_id
                and item.asset_tag == expected.asset.asset_tag
                and item.device_type == expected.asset.device_type
                and item.model == expected.asset.model
                and item.status == expected.asset.status
            )
        return passed, f"owned_assets={len(assets)}; expected_tag_rows={len(expected_assets)}"

    def mailbox_exactly_one_linked() -> tuple[bool, str]:
        passed = len(mailboxes) == 1 and len(expected_mailboxes) == 1
        if passed:
            item = mailboxes[0]
            passed = (
                item.id == expected_mailboxes[0].id
                and item.employee_id == target_id
                and item.address == expected.mailbox.address
                and item.status == expected.mailbox.status
            )
        return (
            passed,
            f"owned_mailboxes={len(mailboxes)}; expected_address_rows={len(expected_mailboxes)}",
        )

    def no_wrong_associations() -> tuple[bool, str]:
        task_rows: list[DownstreamFact] = [*tickets, *accounts, *assets, *mailboxes]
        wrong_owned = sum(item.employee_id != target_id for item in task_rows)
        expected_rows: list[DownstreamFact] = [
            *expected_tickets,
            *expected_accounts,
            *expected_assets,
            *expected_mailboxes,
        ]
        wrong_expected = sum(
            item.employee_id != target_id or item.arena_task_id != task_id for item in expected_rows
        )
        wrong = wrong_owned + wrong_expected
        return wrong == 0, f"wrong_associations={wrong}; inspected_rows={len(task_rows)}"

    def no_duplicate_business_records() -> tuple[bool, str]:
        counts = (len(tickets), len(accounts), len(assets), len(mailboxes))
        passed = counts == (1, 1, 1, 1)
        return passed, "owned_counts=" + "/".join(str(count) for count in counts)

    checks: dict[PredicateKind, PredicateCheck] = {
        "employee_matches": employee_matches,
        "ticket_exactly_one_linked": ticket_exactly_one_linked,
        "iam_exactly_one_linked": iam_exactly_one_linked,
        "iam_no_elevated_role": iam_no_elevated_role,
        "asset_exactly_one_linked": asset_exactly_one_linked,
        "mailbox_exactly_one_linked": mailbox_exactly_one_linked,
        "no_wrong_associations": no_wrong_associations,
        "no_duplicate_business_records": no_duplicate_business_records,
    }

    results = tuple(_evaluate(predicate, checks) for predicate in spec.grader_predicates)
    total_score = sum(item.awarded_points for item in results)
    return GradeResult(
        task_id=task_id,
        spec_checksum=spec.canonical_checksum,
        total_score=total_score,
        passed=total_score == 100 and all(item.passed for item in results),
        predicates=results,
    )


def _evaluate(
    predicate: GraderPredicate, checks: dict[PredicateKind, PredicateCheck]
) -> PredicateResult:
    check = checks[predicate.kind]
    passed, fact = check()
    return PredicateResult(
        predicate_id=predicate.predicate_id,
        kind=predicate.kind,
        weight=predicate.weight,
        passed=passed,
        awarded_points=predicate.weight if passed else 0,
        fact=fact,
    )
