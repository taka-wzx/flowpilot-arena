"""Locust users for the frozen 50-user W12 protected request sequence."""

import os
import time
from dataclasses import dataclass, field
from profile import FORMAL_SEQUENCE
from typing import Any

import gevent  # type: ignore[import-untyped]
from gevent.event import Event  # type: ignore[import-untyped]
from gevent.lock import Semaphore  # type: ignore[import-untyped]
from locust import HttpUser, task
from locust.exception import StopUser

ALPHA = "org_syn_alpha_0001"
BETA = "org_syn_beta_0001"
HTTP_CODES = (200, 202, 404, 409, 412, 429, 503)
TASKS: tuple[tuple[str, str, str, dict[str, object]], ...] = (
    (
        "w7-jml-joiner-001-v1",
        "joiner",
        "standard_joiner",
        {
            "action_type": "create_ticket",
            "parameters": {
                "schema_version": "w11-create-ticket-parameters/1.0",
                "employee_id": 41011,
                "ticket_code": "w7.joiner001v1",
            },
        },
    ),
    (
        "w7-jml-mover-001-v1",
        "mover",
        "standard_mover",
        {
            "action_type": "transfer_employee",
            "parameters": {
                "schema_version": "w11-transfer-employee-parameters/1.0",
                "employee_id": 41131,
                "destination_code": "w7.mover001v1",
            },
        },
    ),
    (
        "w7-jml-leaver-001-v1",
        "leaver",
        "standard_leaver",
        {
            "action_type": "disable_employee",
            "parameters": {
                "schema_version": "w11-employee-mutation-parameters/1.0",
                "employee_id": 41211,
            },
        },
    ),
)


@dataclass(frozen=True, slots=True)
class TokenPool:
    readers: dict[str, tuple[str, ...]]
    writers: dict[str, tuple[str, ...]]


@dataclass(slots=True)
class ProtectedRun:
    run_id: str
    etag: str
    body: dict[str, object]
    idempotency_key: str


@dataclass(slots=True)
class LoadCoordinator:
    users: int = 0
    steady_seconds: int = 0
    tokens: TokenPool | None = None
    next_user: int = 0
    arrived: int = 0
    released: int = 0
    task_started: int = 0
    finished: int = 0
    started_at: float = 0.0
    lock: Semaphore = field(default_factory=Semaphore)
    barrier: Event = field(default_factory=Event)
    completed: Event = field(default_factory=Event)
    latencies_us: list[int] = field(default_factory=list)
    expected_http: dict[str, int] = field(
        default_factory=lambda: {str(code): 0 for code in HTTP_CODES}
    )
    unexpected_http: dict[str, int] = field(
        default_factory=lambda: {str(code): 0 for code in HTTP_CODES}
    )
    unexpected_5xx: int = 0
    accepted_runs: dict[str, str] = field(default_factory=dict)

    def configure(self, *, users: int, steady_seconds: int, tokens: TokenPool) -> None:
        if users < 1 or steady_seconds < 1:
            raise ValueError("load coordinator bounds are invalid")
        self.users = users
        self.steady_seconds = steady_seconds
        self.tokens = tokens

    def register(self) -> int:
        with self.lock:
            index = self.next_user
            self.next_user += 1
            if index >= self.users:
                raise RuntimeError("more Locust users than the frozen profile")
            self.arrived += 1
            if self.arrived == self.users:
                self.started_at = time.perf_counter()
                self.barrier.set()
            return index

    def record(self, *, status: int, expected: int, latency_us: int) -> None:
        with self.lock:
            self.latencies_us.append(latency_us)
            target = self.expected_http if status == expected else self.unexpected_http
            key = str(status)
            if key in target:
                target[key] += 1
            else:
                self.unexpected_http["409"] += 1
            if status >= 500 and status != expected:
                self.unexpected_5xx += 1

    def release(self) -> None:
        with self.lock:
            self.released += 1

    def start_task(self) -> None:
        with self.lock:
            self.task_started += 1

    def accept(self, run_id: str, organization_id: str) -> None:
        with self.lock:
            previous = self.accepted_runs.setdefault(run_id, organization_id)
            if previous != organization_id:
                raise RuntimeError("one accepted run appeared in two organizations")

    def finish(self) -> None:
        with self.lock:
            self.finished += 1
            if self.finished == self.users:
                self.completed.set()


COORDINATOR = LoadCoordinator()


def configure_load(*, users: int, steady_seconds: int, tokens: TokenPool) -> None:
    global COORDINATOR
    COORDINATOR = LoadCoordinator()
    COORDINATOR.configure(users=users, steady_seconds=steady_seconds, tokens=tokens)


class FlowPilotLoadUser(HttpUser):
    host = os.environ.get("CONTROL_API_URL", "http://control-api:8000").rstrip("/")

    def on_start(self) -> None:
        self.user_index = COORDINATOR.register()
        formal_half = max(1, COORDINATOR.users // 2)
        self.organization_id = ALPHA if self.user_index < formal_half else BETA
        local_index = (
            self.user_index if self.organization_id == ALPHA else self.user_index - formal_half
        )
        tokens = COORDINATOR.tokens
        if tokens is None:
            raise RuntimeError("load tokens were not initialized")
        readers = tokens.readers[self.organization_id]
        writers = tokens.writers[self.organization_id]
        self.reader_token = readers[local_index % len(readers)]
        self.writer_token = writers[local_index % len(writers)]
        self.phase_seconds = (local_index // len(writers)) * 0.2
        if self.user_index < 20:
            self.task_binding = TASKS[0]
        elif self.user_index < 35:
            self.task_binding = TASKS[1]
        else:
            self.task_binding = TASKS[2]
        self.runs: list[ProtectedRun] = []
        COORDINATOR.barrier.wait()
        COORDINATOR.release()

    def _headers(self, *, writer: bool, extra: dict[str, str] | None = None) -> dict[str, str]:
        token = self.writer_token if writer else self.reader_token
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected: int,
        writer: bool,
        body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[Any, dict[str, Any] | None]:
        started = time.perf_counter_ns()
        with self.client.request(
            method,
            path,
            name=name,
            headers=self._headers(writer=writer, extra=headers),
            json=body,
            catch_response=True,
        ) as response:
            elapsed_us = (time.perf_counter_ns() - started) // 1_000
            COORDINATOR.record(
                status=response.status_code, expected=expected, latency_us=elapsed_us
            )
            if response.status_code == expected:
                response.success()
            else:
                response.failure(f"closed_status_{response.status_code}")
            payload: dict[str, Any] | None = None
            if response.status_code in {200, 202}:
                parsed = response.json()
                if isinstance(parsed, dict):
                    payload = parsed
            return response, payload

    def _body(self) -> dict[str, object]:
        task_id, process, category, binding = self.task_binding
        return {
            "schema_version": "w12-production-run-create/1.0",
            "task_id": task_id,
            "process": process,
            "category": category,
            "action_type": binding["action_type"],
            "parameters": binding["parameters"],
        }

    def _submit(self, slot: int) -> None:
        key = f"w12-load-20260801-{self.user_index:02d}-{slot:02d}"
        body = self._body()
        response, payload = self._request(
            "POST",
            f"/api/v1/organizations/{self.organization_id}/production-runs",
            name="protected_submit",
            expected=202,
            writer=True,
            body=body,
            headers={"Idempotency-Key": key},
        )
        if payload is None or not isinstance(payload.get("run_id"), str):
            return
        etag = response.headers.get("etag", "")
        reference = ProtectedRun(
            run_id=payload["run_id"],
            etag=etag,
            body=body,
            idempotency_key=key,
        )
        self.runs.append(reference)
        COORDINATOR.accept(reference.run_id, self.organization_id)

    def _replay(self, index: int) -> None:
        if len(self.runs) <= index:
            self._request(
                "GET",
                "/api/v1/identity/me",
                name="protected_missing_replay_fallback",
                expected=200,
                writer=False,
            )
            return
        run = self.runs[index]
        self._request(
            "POST",
            f"/api/v1/organizations/{self.organization_id}/production-runs",
            name="protected_idempotent_replay",
            expected=202,
            writer=True,
            body=run.body,
            headers={"Idempotency-Key": run.idempotency_key},
        )

    def _read_run(self, index: int) -> None:
        if len(self.runs) <= index:
            path = f"/api/v1/organizations/{self.organization_id}/production-runs/run_missing_0001"
            expected = 404
        else:
            path = (
                f"/api/v1/organizations/{self.organization_id}/production-runs/"
                f"{self.runs[index].run_id}"
            )
            expected = 200
        self._request(
            "GET",
            path,
            name="protected_run_read",
            expected=expected,
            writer=True,
        )

    def _mutate_first(self) -> None:
        if not self.runs:
            self._request(
                "GET",
                "/api/v1/identity/me",
                name="protected_missing_mutation_fallback",
                expected=200,
                writer=False,
            )
            return
        run = self.runs[0]
        self._request(
            "POST",
            (f"/api/v1/organizations/{self.organization_id}/production-runs/{run.run_id}/cancel"),
            name="protected_etag_mutation",
            expected=200,
            writer=True,
            headers={"If-Match": run.etag},
        )

    def _closed_probe(self) -> None:
        if self.user_index % 2:
            organization_id = self.organization_id
            run_id = "run_missing_0001"
        else:
            organization_id = BETA if self.organization_id == ALPHA else ALPHA
            run_id = self.runs[-1].run_id if self.runs else "run_missing_0001"
        self._request(
            "GET",
            f"/api/v1/organizations/{organization_id}/production-runs/{run_id}",
            name="protected_closed_probe",
            expected=404,
            writer=False,
        )

    def _execute(self, operation: str) -> None:
        if operation == "identity_read":
            self._request(
                "GET",
                "/api/v1/identity/me",
                name="protected_identity_read",
                expected=200,
                writer=False,
            )
        elif operation == "submit_first":
            self._submit(1)
        elif operation == "submit_second":
            self._submit(2)
        elif operation == "replay_first":
            self._replay(0)
        elif operation == "replay_second":
            self._replay(1)
        elif operation == "read_first":
            self._read_run(0)
        elif operation == "read_second":
            self._read_run(1)
        elif operation == "mutate_first":
            self._mutate_first()
        elif operation == "closed_probe":
            self._closed_probe()
        else:
            raise RuntimeError("unknown frozen load operation")

    @task
    def protected_sequence(self) -> None:
        COORDINATOR.start_task()
        interval = COORDINATOR.steady_seconds / len(FORMAL_SEQUENCE)
        for index, operation in enumerate(FORMAL_SEQUENCE):
            target = COORDINATOR.started_at + self.phase_seconds + index * interval
            gevent.sleep(max(0.0, target - time.perf_counter()))
            self._execute(operation)
            gevent.sleep(0.1)
        COORDINATOR.finish()
        raise StopUser()
