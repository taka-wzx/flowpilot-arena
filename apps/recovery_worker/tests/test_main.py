from types import SimpleNamespace

from flowpilot_recovery_worker import main


async def test_worker_bounds_planning_activities_before_activity_start(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class StubPlanningClient:
        async def close(self) -> None:
            return None

    class StubWorker:
        def __init__(self, _client: object, **kwargs: object) -> None:
            captured.update(kwargs)

        async def run(self) -> None:
            return None

    async def connect(*_args: object, **_kwargs: object) -> object:
        return object()

    planning = StubPlanningClient()
    monkeypatch.setenv("RECOVERY_ENVELOPE_KEY", "runtime-only")
    monkeypatch.setattr(main, "PlanningRecoveryClient", lambda _url: planning)
    monkeypatch.setattr(main, "Client", SimpleNamespace(connect=connect))
    monkeypatch.setattr(main, "decode_runtime_key", lambda _value: b"x" * 32)
    monkeypatch.setattr(main, "Worker", StubWorker)

    await main.run_worker()

    assert captured["max_concurrent_activities"] == 2
    assert captured["max_concurrent_workflow_tasks"] == 4
