from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ
from typing import cast

from fastapi import FastAPI, HTTPException, Request, status

from flowpilot_planning_agent import __version__
from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.client import BrowserWorkerClient
from flowpilot_planning_agent.context import ContextAssembler
from flowpilot_planning_agent.context_schemas import (
    ContextAssembleRequest,
    ContextAssembleResult,
    ContextPlanningRunRequest,
    ContextPlanningRunResult,
)
from flowpilot_planning_agent.dag import validate_dag
from flowpilot_planning_agent.executor import PlanningExecutor
from flowpilot_planning_agent.memory import OrganizationMemoryStore, ScopeViolation
from flowpilot_planning_agent.recovery import RecoveryCoordinator
from flowpilot_planning_agent.recovery_schemas import (
    PlanningActivityResult,
    PlanningRecoveryActivity,
)
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
    app.state.recovery_coordinator = RecoveryCoordinator(app.state.browser_client)
    app.state.organization_memory = OrganizationMemoryStore()
    app.state.context_assembler = ContextAssembler(app.state.organization_memory)
    yield
    await app.state.recovery_coordinator.close_all()
    await app.state.browser_client.close()


app = FastAPI(title="FlowPilot W9 Context Planning Agent", version=__version__, lifespan=lifespan)


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


@app.post("/api/context/assemble", response_model=ContextAssembleResult)
def assemble_context(
    payload: ContextAssembleRequest,
    request: Request,
) -> ContextAssembleResult:
    try:
        assembler = cast(ContextAssembler, request.app.state.context_assembler)
        return assembler.assemble(payload, TotalBudgetLedger(payload.budget))
    except ScopeViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Synthetic context scope rejected",
        ) from exc
    except (BudgetExceeded, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Context schema, provenance, or budget rejected",
        ) from exc


@app.post(
    "/api/planning/context-runs",
    response_model=ContextPlanningRunResult,
)
async def run_context_planning_agent(
    payload: ContextPlanningRunRequest,
    request: Request,
) -> ContextPlanningRunResult:
    ledger = TotalBudgetLedger(payload.planning.budget)
    try:
        assembler = cast(ContextAssembler, request.app.state.context_assembler)
        context_result = assembler.assemble(payload.context, ledger)
    except ScopeViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Synthetic context scope rejected",
        ) from exc
    except (BudgetExceeded, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Context schema, provenance, or budget rejected",
        ) from exc
    executor = PlanningExecutor(request.app.state.browser_client)
    planning_result = await executor.run(payload.planning, ledger=ledger)
    return ContextPlanningRunResult(
        context=context_result.context,
        planning=planning_result,
    )


@app.post(
    "/api/planning/recovery/activities",
    response_model=PlanningActivityResult,
)
async def run_recovery_activity(
    payload: PlanningRecoveryActivity,
    request: Request,
) -> PlanningActivityResult:
    try:
        coordinator = cast(RecoveryCoordinator, request.app.state.recovery_coordinator)
        return await coordinator.invoke(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recovery activity state or Checkpoint rejected",
        ) from exc
