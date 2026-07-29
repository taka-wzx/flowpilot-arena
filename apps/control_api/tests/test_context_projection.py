"""W10 identity-bound durable-memory safe projection tests."""

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.auth import VerifiedIdentity
from flowpilot_control_api.config import OidcPolicy
from flowpilot_control_api.context_projection import build_context_projection
from flowpilot_control_api.repository import ResourceNotFound, create_memory, resolve_actor
from flowpilot_control_api.schemas import MemoryCreate, MemoryField, Role


def _admin(policy: OidcPolicy) -> VerifiedIdentity:
    return VerifiedIdentity(
        issuer_id=policy.issuer_id,
        issuer_hash=hashlib.sha256(policy.issuer.encode()).hexdigest(),
        subject_hash=hashlib.sha256(b"10000000-0000-0000-0000-000000000001").hexdigest(),
        claimed_role=Role.ORGANIZATION_ADMIN,
    )


def test_projection_contains_only_authorized_active_safe_memory(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    as_of = datetime.now(UTC)
    with Session(database_engine) as session:
        actor = resolve_actor(session, _admin(policy))
        create_memory(
            session,
            actor,
            actor.organization_id,
            MemoryCreate(
                field=MemoryField.DEPARTMENT,
                safe_value="synthetic_engineering",
                valid_from=as_of - timedelta(minutes=1),
            ),
        )
        create_memory(
            session,
            actor,
            actor.organization_id,
            MemoryCreate(
                field=MemoryField.LOCATION,
                safe_value="expired_location",
                valid_from=as_of - timedelta(hours=2),
                expires_at=as_of - timedelta(hours=1),
            ),
        )

        first = build_context_projection(session, actor, actor.organization_id, as_of)
        second = build_context_projection(session, actor, actor.organization_id, as_of)

        assert first == second
        assert len(first.memory_items) == 1
        assert first.memory_items[0].safe_value == "synthetic_engineering"
        assert first.projection_hash == second.projection_hash
        serialized = first.model_dump_json()
        assert actor.organization_id not in serialized
        assert actor.user_id not in serialized
        assert actor.membership_id not in serialized
        assert "10000000-0000" not in serialized
        assert "bearer" not in serialized.lower()
        assert "email" not in serialized.lower()

        with pytest.raises(ResourceNotFound):
            build_context_projection(
                session,
                actor,
                "org_syn_beta_0001",
                as_of,
            )
