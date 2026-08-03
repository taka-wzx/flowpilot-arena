"""Private four-slot W12 Workflow Worker process."""

import asyncio
import logging
import os
import signal
import sys
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from flowpilot_workflow_worker.config import WorkerSettings, load_settings
from flowpilot_workflow_worker.repository import WorkflowRepository
from flowpilot_workflow_worker.schemas import TemporalOutcome, WorkItem
from flowpilot_workflow_worker.temporal_client import TemporalGateway

_READY_PATH = Path("/tmp/flowpilot-workflow-worker.ready")
LOGGER = logging.getLogger("flowpilot_workflow_worker")


class Dispatcher:
    def __init__(
        self,
        repository: WorkflowRepository,
        temporal: TemporalGateway,
        settings: WorkerSettings,
    ) -> None:
        self._repository = repository
        self._temporal = temporal
        self._settings = settings
        self._active = 0
        self.max_active = 0
        self._active_lock = asyncio.Lock()
        self._slot_gate = asyncio.Semaphore(settings.slots)

    async def _heartbeat(self, item: WorkItem, done: asyncio.Event) -> None:
        while not done.is_set():
            try:
                await asyncio.wait_for(done.wait(), timeout=self._settings.heartbeat_seconds)
            except TimeoutError:
                current = await asyncio.to_thread(
                    self._repository.heartbeat,
                    item,
                    now=datetime.now(UTC),
                )
                if not current:
                    return

    async def process(self, item: WorkItem) -> None:
        await self._slot_gate.acquire()
        done = asyncio.Event()
        heartbeat_task: asyncio.Task[None] | None = None
        counted = False
        try:
            async with self._active_lock:
                self._active += 1
                counted = True
                self.max_active = max(self.max_active, self._active)
                if self._active > self._settings.slots:
                    raise RuntimeError("W12 production slot bound exceeded")
            binding_valid = await asyncio.to_thread(
                self._repository.binding_valid,
                item,
                now=datetime.now(UTC),
            )
            if not binding_valid:
                await asyncio.to_thread(
                    self._repository.fail,
                    item,
                    reason="authorization_invalid",
                    now=datetime.now(UTC),
                )
                return
            started = await asyncio.to_thread(
                self._repository.mark_started,
                item,
                now=datetime.now(UTC),
            )
            if not started:
                return
            heartbeat_task = asyncio.create_task(self._heartbeat(item, done))
            outcome: TemporalOutcome = await self._temporal.start_and_wait(item)
            if outcome.result.status != "finished_ungraded":
                LOGGER.warning(
                    "w12_workflow_terminal_failure run_id=%s task_id=%s "
                    "workflow_status=%s workflow_terminal_reason=%s "
                    "checkpoint_count=%s completed_step_count=%s "
                    "revision=%s session_epoch=%s latest_checkpoint_hash=%s",
                    item.run_id,
                    item.task_id,
                    outcome.result.status,
                    outcome.result.terminal_reason,
                    outcome.result.checkpoint_count,
                    len(outcome.result.completed_step_ids),
                    outcome.result.revision,
                    outcome.result.session_epoch,
                    outcome.result.latest_checkpoint_hash,
                )
            if outcome.deduplicated_start:
                await asyncio.to_thread(
                    self._repository.record_deduplicated,
                    item,
                    now=datetime.now(UTC),
                )
            await asyncio.to_thread(
                self._repository.complete,
                item,
                outcome,
                now=datetime.now(UTC),
            )
        except asyncio.CancelledError:
            await asyncio.to_thread(
                self._repository.release,
                item,
                now=datetime.now(UTC),
            )
            raise
        except Exception:
            await asyncio.to_thread(
                self._repository.fail,
                item,
                reason="workflow_rejected",
                now=datetime.now(UTC),
            )
        finally:
            done.set()
            if heartbeat_task is not None:
                heartbeat_task.cancel()
                with suppress(asyncio.CancelledError):
                    await heartbeat_task
            if counted:
                async with self._active_lock:
                    self._active -= 1
            self._slot_gate.release()

    async def run_slot(self, stop: asyncio.Event) -> None:
        poll_seconds = self._settings.poll_milliseconds / 1_000
        while not stop.is_set():
            item = await asyncio.to_thread(
                self._repository.claim_next,
                now=datetime.now(UTC),
            )
            if item is None:
                with suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
                continue
            await self.process(item)


def _touch_ready() -> None:
    _READY_PATH.touch(exist_ok=True)


def _healthcheck(settings: WorkerSettings) -> int:
    settings.validate()
    if not _READY_PATH.exists():
        return 1
    age = datetime.now(UTC).timestamp() - _READY_PATH.stat().st_mtime
    return 0 if 0 <= age <= 30 else 1


async def run_worker(settings: WorkerSettings) -> None:
    repository = WorkflowRepository.connect(settings)
    temporal = await TemporalGateway.connect(settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(name, stop.set)
    dispatcher = Dispatcher(repository, temporal, settings)
    tasks = [asyncio.create_task(dispatcher.run_slot(stop)) for _ in range(settings.slots)]
    try:
        if not await asyncio.to_thread(repository.ping):
            raise RuntimeError("Workflow Worker Control database is unavailable")
        _touch_ready()
        while not stop.is_set():
            await asyncio.sleep(5)
            _touch_ready()
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=settings.drain_seconds,
            )
        except TimeoutError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        stop.set()
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        repository.close()
        with suppress(OSError):
            _READY_PATH.unlink()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings()
    if len(sys.argv) == 2 and sys.argv[1] == "--healthcheck":
        return _healthcheck(settings)
    if len(sys.argv) != 1:
        return 2
    asyncio.run(run_worker(settings))
    return 0


if __name__ == "__main__":
    os._exit(main())
