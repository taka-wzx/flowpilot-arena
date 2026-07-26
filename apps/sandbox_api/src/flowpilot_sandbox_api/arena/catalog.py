import hashlib
import json
from collections.abc import Iterable
from functools import lru_cache
from importlib import resources

from flowpilot_sandbox_api.arena.schemas import TaskCatalogEntry, TaskSpec


def canonical_spec_bytes(spec: TaskSpec) -> bytes:
    payload = spec.model_dump(mode="json", exclude={"canonical_checksum"})
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def calculate_spec_checksum(spec: TaskSpec) -> str:
    return hashlib.sha256(canonical_spec_bytes(spec)).hexdigest()


def parse_task_document(document: str) -> TaskSpec:
    spec = TaskSpec.model_validate_json(document)
    actual = calculate_spec_checksum(spec)
    if actual != spec.canonical_checksum:
        raise ValueError(
            f"Canonical checksum mismatch for {spec.task_id}: "
            f"declared {spec.canonical_checksum}, calculated {actual}"
        )
    return spec


class TaskCatalog:
    def __init__(self, specs: Iterable[TaskSpec]) -> None:
        items = tuple(sorted(specs, key=lambda item: item.task_id))
        by_id = {item.task_id: item for item in items}
        if len(items) != len(by_id):
            raise ValueError("Task catalog contains duplicate task IDs")
        required = tuple(f"w3-joiner-{number:03d}" for number in range(1, 11))
        if tuple(by_id) != required:
            raise ValueError("Task catalog must contain exactly w3-joiner-001 through -010")
        self._specs = items
        self._by_id = by_id

    @classmethod
    def from_documents(cls, documents: Iterable[str]) -> "TaskCatalog":
        return cls(parse_task_document(document) for document in documents)

    @classmethod
    def from_package(cls) -> "TaskCatalog":
        root = resources.files("flowpilot_sandbox_api.arena").joinpath("tasks")
        task_files = sorted(
            (item for item in root.iterdir() if item.name.endswith(".json")),
            key=lambda item: item.name,
        )
        return cls.from_documents(item.read_text(encoding="utf-8") for item in task_files)

    @property
    def specs(self) -> tuple[TaskSpec, ...]:
        return self._specs

    def get(self, task_id: str) -> TaskSpec:
        try:
            return self._by_id[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown Arena task: {task_id}") from exc

    def entries(self) -> tuple[TaskCatalogEntry, ...]:
        return tuple(
            TaskCatalogEntry(
                task_id=spec.task_id,
                schema_version=spec.schema_version,
                title=spec.title,
                business_process=spec.business_process,
                split=spec.split,
                fixture_version=spec.fixture.fixture_version,
                canonical_checksum=spec.canonical_checksum,
            )
            for spec in self._specs
        )

    @property
    def canonical_checksum(self) -> str:
        pairs = [
            {"task_id": spec.task_id, "canonical_checksum": spec.canonical_checksum}
            for spec in self._specs
        ]
        payload = json.dumps(pairs, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()


@lru_cache
def get_catalog() -> TaskCatalog:
    return TaskCatalog.from_package()
