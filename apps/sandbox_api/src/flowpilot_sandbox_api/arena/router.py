from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.baselines import (
    DuplicateBaselineRecordError,
    create_baseline_record,
    list_baseline_records,
)
from flowpilot_sandbox_api.arena.catalog import TaskCatalog, get_catalog
from flowpilot_sandbox_api.arena.grader import grade_task
from flowpilot_sandbox_api.arena.schemas import (
    EmptyArenaRequest,
    GradeResult,
    ManualBaselineCreate,
    ManualBaselineRead,
    ResetSeedResult,
    TaskCatalogEntry,
    TaskSpec,
)
from flowpilot_sandbox_api.arena.service import reset_seed
from flowpilot_sandbox_api.database import get_session

router = APIRouter(prefix="/api/arena", tags=["arena"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _task_or_404(catalog: TaskCatalog, task_id: str) -> TaskSpec:
    try:
        return catalog.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tasks", response_model=list[TaskCatalogEntry])
def list_tasks() -> list[TaskCatalogEntry]:
    return list(get_catalog().entries())


@router.get("/tasks/{task_id}", response_model=TaskSpec)
def get_task(task_id: str) -> TaskSpec:
    return _task_or_404(get_catalog(), task_id)


@router.post("/tasks/{task_id}/reset-seed", response_model=ResetSeedResult)
def reset_seed_task(
    task_id: str,
    session: SessionDependency,
    _request: Annotated[EmptyArenaRequest | None, Body()] = None,
) -> ResetSeedResult:
    spec = _task_or_404(get_catalog(), task_id)
    try:
        return reset_seed(session, spec)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task seed conflicts with non-task Sandbox data",
        ) from exc


@router.post("/tasks/{task_id}/grade", response_model=GradeResult)
def grade(
    task_id: str,
    session: SessionDependency,
    _request: Annotated[EmptyArenaRequest | None, Body()] = None,
) -> GradeResult:
    return grade_task(session, _task_or_404(get_catalog(), task_id))


@router.get("/baselines", response_model=list[ManualBaselineRead])
def list_baselines(session: SessionDependency) -> list[ManualBaselineRead]:
    return list_baseline_records(session)


@router.post(
    "/baselines",
    response_model=ManualBaselineRead,
    status_code=status.HTTP_201_CREATED,
)
def record_baseline(
    payload: ManualBaselineCreate, session: SessionDependency
) -> ManualBaselineRead:
    try:
        return create_baseline_record(session, get_catalog(), payload)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateBaselineRecordError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Baseline record ID already exists",
        ) from exc
