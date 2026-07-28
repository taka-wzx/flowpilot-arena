from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot_sandbox_api.arena.jml.catalog import JmlCatalog, get_catalog
from flowpilot_sandbox_api.arena.jml.grader import grade_task
from flowpilot_sandbox_api.arena.jml.schemas import (
    CatalogEntry,
    CatalogSummary,
    EmptyRequest,
    GradeResult,
    JmlInstance,
    ResetSeedResult,
)
from flowpilot_sandbox_api.arena.jml.service import reset_seed
from flowpilot_sandbox_api.database import get_session

router = APIRouter(prefix="/api/arena/w7", tags=["w7-jml"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _task_or_404(catalog: JmlCatalog, task_id: str) -> JmlInstance:
    try:
        return catalog.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _reject_reporting(instance: JmlInstance) -> None:
    if instance.split == "reporting":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="W7 Reporting tasks are checksum-frozen and cannot be executed or graded",
        )


@router.get("/catalog", response_model=CatalogSummary)
def catalog_summary() -> CatalogSummary:
    return get_catalog().summary()


@router.get("/tasks", response_model=list[CatalogEntry])
def list_tasks() -> list[CatalogEntry]:
    return list(get_catalog().entries())


@router.get("/tasks/{task_id}", response_model=JmlInstance)
def get_task(task_id: str) -> JmlInstance:
    return _task_or_404(get_catalog(), task_id)


@router.post("/tasks/{task_id}/reset-seed", response_model=ResetSeedResult)
def reset_seed_task(
    task_id: str,
    session: SessionDependency,
    _request: Annotated[EmptyRequest | None, Body()] = None,
) -> ResetSeedResult:
    instance = _task_or_404(get_catalog(), task_id)
    _reject_reporting(instance)
    try:
        return reset_seed(session, instance)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="W7 task seed conflicts with non-task synthetic data",
        ) from exc


@router.post("/tasks/{task_id}/grade", response_model=GradeResult)
def grade(task_id: str, session: SessionDependency) -> GradeResult:
    instance = _task_or_404(get_catalog(), task_id)
    _reject_reporting(instance)
    return grade_task(session, instance)
