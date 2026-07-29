"""Tenant-safe repository and optimistic-lock transaction tests."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.auth import VerifiedIdentity
from flowpilot_control_api.config import OidcPolicy
from flowpilot_control_api.etag import PreconditionFailed
from flowpilot_control_api.models import Organization, OrganizationMemory, User
from flowpilot_control_api.repository import (
    ResourceNotFound,
    count_memberships,
    count_users,
    create_membership,
    create_memory,
    create_user,
    get_user,
    list_users,
    resolve_actor,
    update_memory,
)
from flowpilot_control_api.schemas import (
    MembershipCreate,
    MemoryCreate,
    MemoryField,
    MemoryUpdate,
    Role,
    UserCreate,
)


def _verified(policy: OidcPolicy, subject: str, role: Role) -> VerifiedIdentity:
    return VerifiedIdentity(
        issuer_id=policy.issuer_id,
        issuer_hash=hashlib.sha256(policy.issuer.encode()).hexdigest(),
        subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
        claimed_role=role,
    )


def test_actor_resolution_and_every_tenant_query_are_organization_qualified(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    with Session(database_engine) as session:
        alpha = resolve_actor(
            session,
            _verified(
                policy,
                "10000000-0000-0000-0000-000000000001",
                Role.ORGANIZATION_ADMIN,
            ),
        )
        beta = resolve_actor(
            session,
            _verified(
                policy,
                "20000000-0000-0000-0000-000000000001",
                Role.ORGANIZATION_ADMIN,
            ),
        )

        assert len(list_users(session, alpha, alpha.organization_id)) == 8
        assert count_users(session, alpha, alpha.organization_id) == 8
        assert count_memberships(session, alpha, alpha.organization_id) == 8
        with pytest.raises(ResourceNotFound):
            list_users(session, alpha, beta.organization_id)
        with pytest.raises(ResourceNotFound):
            get_user(session, alpha, alpha.organization_id, beta.user_id)

        new_user = create_user(
            session,
            alpha,
            alpha.organization_id,
            UserCreate(profile_code="synthetic_new_operator"),
        )
        membership = create_membership(
            session,
            alpha,
            alpha.organization_id,
            MembershipCreate(user_id=new_user.user_id, role=Role.OPERATOR),
        )
        assert membership.organization_id == alpha.organization_id
        with pytest.raises(ResourceNotFound):
            create_membership(
                session,
                alpha,
                alpha.organization_id,
                MembershipCreate(user_id=beta.user_id, role=Role.OPERATOR),
            )


def test_stale_memory_write_rolls_back_collection_and_resource_state(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    now = datetime.now(UTC)
    with Session(database_engine) as session:
        actor = resolve_actor(
            session,
            _verified(
                policy,
                "10000000-0000-0000-0000-000000000001",
                Role.ORGANIZATION_ADMIN,
            ),
        )
        memory = create_memory(
            session,
            actor,
            actor.organization_id,
            MemoryCreate(
                field=MemoryField.LOCATION,
                safe_value="location_alpha",
                valid_from=now,
            ),
        )
        memory_id = memory.memory_id
        updated = update_memory(
            session,
            actor,
            actor.organization_id,
            memory_id,
            1,
            MemoryUpdate(safe_value="location_alpha_two", valid_from=now),
        )
        assert updated.version == 2

        with pytest.raises(PreconditionFailed):
            update_memory(
                session,
                actor,
                actor.organization_id,
                memory_id,
                1,
                MemoryUpdate(safe_value="stale_value", valid_from=now),
            )

    with Session(database_engine) as session:
        stored = session.scalar(
            select(OrganizationMemory).where(
                OrganizationMemory.organization_id == "org_syn_alpha_0001",
                OrganizationMemory.memory_id == memory_id,
            )
        )
        collection_version = session.scalar(
            select(Organization.memory_version).where(
                Organization.organization_id == "org_syn_alpha_0001"
            )
        )
        assert stored is not None
        assert stored.version == 2
        assert stored.safe_value == "location_alpha_two"
        assert collection_version == 3


def test_two_concurrent_writes_have_exactly_one_winner(
    database_engine: Engine, policy: OidcPolicy
) -> None:
    now = datetime.now(UTC)
    with Session(database_engine) as session:
        actor = resolve_actor(
            session,
            _verified(
                policy,
                "10000000-0000-0000-0000-000000000001",
                Role.ORGANIZATION_ADMIN,
            ),
        )
        memory = create_memory(
            session,
            actor,
            actor.organization_id,
            MemoryCreate(
                field=MemoryField.DEVICE_PREFERENCE,
                safe_value="device_standard_a",
                valid_from=now,
            ),
        )
        memory_id = memory.memory_id

    barrier = Barrier(2)

    def contender(value: str) -> str:
        with Session(database_engine) as session:
            actor = resolve_actor(
                session,
                _verified(
                    policy,
                    "10000000-0000-0000-0000-000000000001",
                    Role.ORGANIZATION_ADMIN,
                ),
            )
            barrier.wait()
            try:
                update_memory(
                    session,
                    actor,
                    actor.organization_id,
                    memory_id,
                    1,
                    MemoryUpdate(safe_value=value, valid_from=now),
                )
            except PreconditionFailed:
                return "stale"
            return "success"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(contender, ("device_standard_b", "device_standard_c")))

    assert sorted(outcomes) == ["stale", "success"]
    with Session(database_engine) as session:
        stored = session.scalar(
            select(OrganizationMemory).where(
                OrganizationMemory.organization_id == "org_syn_alpha_0001",
                OrganizationMemory.memory_id == memory_id,
            )
        )
        total_memories = session.scalar(select(func.count()).select_from(OrganizationMemory))
        total_users = session.scalar(select(func.count()).select_from(User))
        assert stored is not None
        assert stored.version == 2
        assert stored.safe_value in {"device_standard_b", "device_standard_c"}
        assert total_memories == 1
        assert total_users == 16
