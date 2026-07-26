import pytest

from flowpilot_browser_worker.config import WorkerConfig, WorkerLimits


@pytest.fixture
def worker_config() -> WorkerConfig:
    return WorkerConfig(
        sandbox_origin="http://sandbox-web",
        limits=WorkerLimits(browser_action_timeout_ms=250),
    )
