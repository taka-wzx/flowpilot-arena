"""Frozen Workflow Worker configuration tests."""

import base64
from dataclasses import replace

import pytest

from flowpilot_workflow_worker.config import WorkerSettings


def _key() -> str:
    return base64.urlsafe_b64encode(b"k" * 32).decode("ascii")


def test_frozen_policy_and_key_validation() -> None:
    settings = WorkerSettings(
        database_url="sqlite+pysqlite:///:memory:",
        worker_instance_id="worker_test_config_0001",
        envelope_key=_key(),
    )
    settings.validate()
    assert settings.decoded_key() == b"k" * 32

    for changed in (
        replace(settings, slots=5),
        replace(settings, lease_ttl_seconds=31),
        replace(settings, heartbeat_seconds=11),
        replace(settings, drain_seconds=26),
        replace(settings, maximum_attempts=4),
    ):
        with pytest.raises(ValueError, match="frozen W12 contract"):
            changed.validate()


def test_rejects_untrusted_routes_and_invalid_key() -> None:
    with pytest.raises(ValueError, match="fixed Control database"):
        WorkerSettings(
            database_url="postgresql+psycopg://user:pass@other:5432/flowpilot_control",
            worker_instance_id="worker_test_config_0001",
            envelope_key=_key(),
        ).validate()
    with pytest.raises(ValueError, match="decode to 32 bytes"):
        WorkerSettings(
            database_url="sqlite+pysqlite:///:memory:",
            worker_instance_id="worker_test_config_0001",
            envelope_key=base64.urlsafe_b64encode(b"short").decode("ascii"),
        ).validate()
