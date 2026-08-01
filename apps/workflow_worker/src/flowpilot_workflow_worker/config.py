"""Closed W12 Workflow Worker configuration."""

import base64
import re
from dataclasses import dataclass
from os import environ
from urllib.parse import urlsplit

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://flowpilot_control:flowpilot_control_local_only@"
    "control-postgres:5432/flowpilot_control"
)
_INSTANCE_PATTERN = re.compile(r"^worker_[A-Za-z0-9_-]{8,64}$")


@dataclass(frozen=True, slots=True)
class WorkerSettings:
    database_url: str = DEFAULT_DATABASE_URL
    temporal_address: str = "temporal:7233"
    temporal_namespace: str = "flowpilot-w8"
    temporal_task_queue: str = "flowpilot-w8-recovery"
    worker_instance_id: str = "worker_w12_compose_0001"
    envelope_key: str = ""
    slots: int = 4
    lease_ttl_seconds: int = 30
    heartbeat_seconds: int = 10
    drain_seconds: int = 25
    maximum_attempts: int = 3
    poll_milliseconds: int = 250

    def decoded_key(self) -> bytes:
        try:
            key = base64.b64decode(self.envelope_key.encode("ascii"), altchars=b"-_", validate=True)
        except (ValueError, UnicodeEncodeError) as exc:
            raise ValueError("RECOVERY_ENVELOPE_KEY is invalid") from exc
        if len(key) != 32:
            raise ValueError("RECOVERY_ENVELOPE_KEY must decode to 32 bytes")
        return key

    def validate(self) -> None:
        parsed = urlsplit(self.database_url)
        if self.database_url.startswith("sqlite+pysqlite://"):
            pass
        elif (
            parsed.scheme != "postgresql+psycopg"
            or parsed.hostname != "control-postgres"
            or parsed.port != 5432
            or parsed.path != "/flowpilot_control"
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Workflow Worker database must be the fixed Control database")
        if (
            self.temporal_address != "temporal:7233"
            or self.temporal_namespace != "flowpilot-w8"
            or self.temporal_task_queue != "flowpilot-w8-recovery"
            or not _INSTANCE_PATTERN.fullmatch(self.worker_instance_id)
            or self.slots != 4
            or self.lease_ttl_seconds != 30
            or self.heartbeat_seconds != 10
            or self.drain_seconds != 25
            or self.maximum_attempts != 3
            or self.poll_milliseconds != 250
        ):
            raise ValueError("Workflow Worker policy differs from the frozen W12 contract")
        self.decoded_key()


def load_settings() -> WorkerSettings:
    settings = WorkerSettings(
        database_url=environ.get("CONTROL_DATABASE_URL", DEFAULT_DATABASE_URL),
        temporal_address=environ.get("TEMPORAL_ADDRESS", "temporal:7233"),
        worker_instance_id=environ.get("W12_WORKER_INSTANCE_ID", "worker_w12_compose_0001"),
        envelope_key=environ.get("RECOVERY_ENVELOPE_KEY", ""),
    )
    settings.validate()
    return settings
