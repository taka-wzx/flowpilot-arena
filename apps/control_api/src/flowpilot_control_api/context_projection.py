"""Authorized closed-schema bridge from durable W10 memory to W9 context input."""

from datetime import datetime

from sqlalchemy.orm import Session

from flowpilot_control_api.repository import list_memories
from flowpilot_control_api.schemas import (
    ActorContext,
    AuthorizedContextProjection,
    AuthorizedMemoryProjection,
    MemoryField,
    stable_hash,
)


def build_context_projection(
    session: Session,
    actor: ActorContext,
    organization_id: str,
    as_of: datetime,
) -> AuthorizedContextProjection:
    memories, _ = list_memories(
        session,
        actor,
        organization_id,
        as_of=as_of,
    )
    items = tuple(
        AuthorizedMemoryProjection(
            memory_id=record.memory_id,
            field=MemoryField(record.field),
            safe_value=record.safe_value,
            version=record.version,
            valid_from=record.valid_from,
            expires_at=record.expires_at,
            content_hash=record.content_hash,
        )
        for record in memories[:6]
    )
    fields: dict[str, object] = {
        "schema_version": "w10-authorized-context-projection/1.0",
        "organization_hash": stable_hash(actor.organization_id),
        "actor_hash": stable_hash(
            {
                "schema_version": "w10-actor-projection/1.0",
                "user_id": actor.user_id,
                "membership_id": actor.membership_id,
            }
        ),
        "authorization_hash": actor.authorization_hash,
        "as_of": as_of,
        "memory_items": items,
    }
    return AuthorizedContextProjection.model_validate(
        {**fields, "projection_hash": stable_hash(fields)}
    )
