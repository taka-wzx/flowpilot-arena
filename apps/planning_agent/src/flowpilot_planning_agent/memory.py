from datetime import datetime
from threading import RLock

from flowpilot_planning_agent.context_schemas import (
    MemoryMutation,
    OrganizationMemoryRecord,
    ScopeId,
    content_hash,
)
from flowpilot_planning_agent.schemas import TaskId


class ScopeViolation(ValueError):
    pass


class OrganizationMemoryStore:
    """Process-local deterministic fake store; not a W10 tenancy claim."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], OrganizationMemoryRecord] = {}
        self._lock = RLock()

    def clone(self) -> "OrganizationMemoryStore":
        clone = OrganizationMemoryStore()
        with self._lock:
            clone._records = self._records.copy()
        return clone

    @staticmethod
    def _authorize(*, actor_scope_id: ScopeId, scope_id: ScopeId) -> None:
        if actor_scope_id != scope_id:
            raise ScopeViolation("cross-scope organization memory access rejected")

    def mutate(
        self,
        *,
        actor_scope_id: ScopeId,
        scope_id: ScopeId,
        task_id: TaskId,
        mutation: MemoryMutation,
    ) -> OrganizationMemoryRecord:
        self._authorize(actor_scope_id=actor_scope_id, scope_id=scope_id)
        key = (scope_id, mutation.memory_id)
        with self._lock:
            current = self._records.get(key)
            if current is not None and current.owner_task_id != task_id:
                raise ScopeViolation("organization memory owner task mismatch")
            version = 1 if current is None else current.version + 1
            if mutation.action == "delete":
                if current is None:
                    raise ScopeViolation("organization memory delete target not found")
                record = current.model_copy(
                    update={
                        "version": version,
                        "status": "tombstone",
                        "content_hash": content_hash(f"tombstone.{mutation.memory_id}.{version}"),
                    }
                )
            else:
                if (
                    mutation.field is None
                    or mutation.safe_value is None
                    or mutation.valid_from is None
                ):
                    raise ValueError("validated memory upsert fields are missing")
                if current is not None and current.field != mutation.field:
                    raise ScopeViolation("organization memory field identity cannot change")
                record = OrganizationMemoryRecord(
                    memory_id=mutation.memory_id,
                    scope_id=scope_id,
                    owner_task_id=task_id,
                    field=mutation.field,
                    safe_value=mutation.safe_value,
                    version=version,
                    status="active",
                    valid_from=mutation.valid_from,
                    expires_at=mutation.expires_at,
                    content_hash=content_hash(mutation.safe_value),
                )
            self._records[key] = record
            return record

    def read(
        self,
        *,
        actor_scope_id: ScopeId,
        scope_id: ScopeId,
        as_of: datetime,
    ) -> tuple[OrganizationMemoryRecord, ...]:
        self._authorize(actor_scope_id=actor_scope_id, scope_id=scope_id)
        with self._lock:
            records = tuple(
                record
                for (record_scope, _), record in self._records.items()
                if record_scope == scope_id
                and record.status == "active"
                and record.valid_from <= as_of
                and (record.expires_at is None or as_of < record.expires_at)
            )
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.field,
                    record.memory_id,
                    -record.version,
                    record.content_hash,
                ),
            )[:6]
        )

    def reset(
        self,
        *,
        actor_scope_id: ScopeId,
        scope_id: ScopeId,
        task_id: TaskId,
    ) -> int:
        self._authorize(actor_scope_id=actor_scope_id, scope_id=scope_id)
        changed = 0
        with self._lock:
            for key in sorted(self._records):
                record = self._records[key]
                if (
                    record.scope_id == scope_id
                    and record.owner_task_id == task_id
                    and record.status == "active"
                ):
                    version = record.version + 1
                    self._records[key] = record.model_copy(
                        update={
                            "version": version,
                            "status": "tombstone",
                            "content_hash": content_hash(f"tombstone.{record.memory_id}.{version}"),
                        }
                    )
                    changed += 1
        return changed
