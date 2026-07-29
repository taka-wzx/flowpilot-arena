from datetime import UTC, datetime, timedelta

import pytest

from flowpilot_planning_agent.context_schemas import MemoryMutation
from flowpilot_planning_agent.memory import OrganizationMemoryStore, ScopeViolation


def upsert(value: str, *, expires_at=None) -> MemoryMutation:
    return MemoryMutation(
        action="upsert",
        memory_id="memory.department",
        field="department",
        safe_value=value,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=expires_at,
    )


def test_memory_versions_reads_deletes_and_scope_rejection() -> None:
    store = OrganizationMemoryStore()
    first = store.mutate(
        actor_scope_id="syn_scope_alpha",
        scope_id="syn_scope_alpha",
        task_id="w7-jml-joiner-001-v1",
        mutation=upsert("engineering"),
    )
    second = store.mutate(
        actor_scope_id="syn_scope_alpha",
        scope_id="syn_scope_alpha",
        task_id="w7-jml-joiner-001-v1",
        mutation=upsert("security"),
    )
    assert (first.version, second.version) == (1, 2)
    assert store.read(
        actor_scope_id="syn_scope_alpha",
        scope_id="syn_scope_alpha",
        as_of=datetime(2026, 7, 29, tzinfo=UTC),
    ) == (second,)
    with pytest.raises(ScopeViolation, match="cross-scope"):
        store.read(
            actor_scope_id="syn_scope_beta",
            scope_id="syn_scope_alpha",
            as_of=datetime(2026, 7, 29, tzinfo=UTC),
        )
    tombstone = store.mutate(
        actor_scope_id="syn_scope_alpha",
        scope_id="syn_scope_alpha",
        task_id="w7-jml-joiner-001-v1",
        mutation=MemoryMutation(action="delete", memory_id="memory.department"),
    )
    assert tombstone.version == 3
    assert tombstone.status == "tombstone"
    assert (
        store.read(
            actor_scope_id="syn_scope_alpha",
            scope_id="syn_scope_alpha",
            as_of=datetime(2026, 7, 29, tzinfo=UTC),
        )
        == ()
    )


def test_memory_expiry_and_task_owned_reset() -> None:
    store = OrganizationMemoryStore()
    store.mutate(
        actor_scope_id="syn_scope_alpha",
        scope_id="syn_scope_alpha",
        task_id="w7-jml-joiner-001-v1",
        mutation=upsert(
            "engineering",
            expires_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=1),
        ),
    )
    assert (
        store.read(
            actor_scope_id="syn_scope_alpha",
            scope_id="syn_scope_alpha",
            as_of=datetime(2026, 7, 29, tzinfo=UTC),
        )
        == ()
    )
    assert (
        store.reset(
            actor_scope_id="syn_scope_alpha",
            scope_id="syn_scope_alpha",
            task_id="w7-jml-mover-001-v1",
        )
        == 0
    )
    assert (
        store.reset(
            actor_scope_id="syn_scope_alpha",
            scope_id="syn_scope_alpha",
            task_id="w7-jml-joiner-001-v1",
        )
        == 1
    )
