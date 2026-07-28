import hashlib
import json

from sqlalchemy import delete
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.schemas import FactCounts, JmlInstance, ResetSeedResult
from flowpilot_sandbox_api.arena.service import TASK_MODELS, task_fact_snapshot
from flowpilot_sandbox_api.models import (
    AssetAssignment,
    Employee,
    IamAccount,
    Mailbox,
    OnboardingTicket,
)


def _snapshot_checksum(snapshot: object) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def reset_seed(session: Session, instance: JmlInstance) -> ResetSeedResult:
    state = instance.initial_state
    with session.begin():
        for model in TASK_MODELS:
            session.execute(delete(model).where(model.arena_task_id == instance.task_id))
        for employee in (state.target, state.decoy):
            session.add(
                Employee(
                    **employee.model_dump(),
                    arena_task_id=instance.task_id,
                )
            )
        if state.ticket is not None:
            session.add(
                OnboardingTicket(
                    **state.ticket.model_dump(),
                    arena_task_id=instance.task_id,
                )
            )
        if state.account is not None:
            session.add(
                IamAccount(
                    **state.account.model_dump(),
                    arena_task_id=instance.task_id,
                )
            )
        if state.asset is not None:
            session.add(
                AssetAssignment(
                    **state.asset.model_dump(),
                    arena_task_id=instance.task_id,
                )
            )
        if state.mailbox is not None:
            session.add(
                Mailbox(
                    **state.mailbox.model_dump(),
                    arena_task_id=instance.task_id,
                )
            )

    snapshot = task_fact_snapshot(session, instance.task_id)
    return ResetSeedResult(
        task_id=instance.task_id,
        fixture_version=instance.fixture_version,
        instance_checksum=instance.canonical_checksum,
        fact_checksum=_snapshot_checksum(snapshot),
        counts=FactCounts(
            employees=len(snapshot["employees"]),
            tickets=len(snapshot["tickets"]),
            iam_accounts=len(snapshot["iam_accounts"]),
            assets=len(snapshot["assets"]),
            mailboxes=len(snapshot["mailboxes"]),
        ),
    )
