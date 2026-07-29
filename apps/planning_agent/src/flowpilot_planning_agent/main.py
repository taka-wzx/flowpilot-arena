from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from fastapi import FastAPI, Request

from flowpilot_planning_agent import __version__
from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.executor import PlanningExecutor
from flowpilot_planning_agent.schemas import (
    PlanningDag,
    PlanningRunRequest,
    PlanningRunResult,
    PlanValidationResult,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.browser_client = BrowserWorkerClient(
        environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
    )
    yield
    await app.state.browser_client.close()


app = FastAPI(title="FlowPilot W7 Planning Agent", version=__version__, lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "planning-agent", "version": __version__}


@app.post("/api/planning/plans/validate", response_model=PlanValidationResult)
def validate_plan(dag: PlanningDag) -> PlanValidationResult:
    return validate_dag(dag)


@app.post("/api/planning/runs", response_model=PlanningRunResult)
async def run_planning_agent(
    payload: PlanningRunRequest,
    request: Request,
) -> PlanningRunResult:
    executor = PlanningExecutor(request.app.state.browser_client)
    return await executor.run(payload)
