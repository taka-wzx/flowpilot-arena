from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

from fastapi import Body, FastAPI, HTTPException, Request, status

from flowpilot_browser_worker import __version__
from flowpilot_browser_worker.config import WorkerConfig
from flowpilot_browser_worker.runtime import BrowserRuntime, UnknownSessionError
from flowpilot_browser_worker.schemas import (
    ActionResult,
    BrowserAction,
    SessionClosed,
    SessionCreate,
    SessionCreated,
    SessionId,
    VisionActionResult,
    VisionBrowserAction,
    VisionSessionClosed,
    VisionSessionCreate,
    VisionSessionCreated,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.runtime = BrowserRuntime(WorkerConfig.from_env())
    yield
    await app.state.runtime.close_all()


app = FastAPI(
    title="FlowPilot W5 Browser Worker",
    version=__version__,
    lifespan=lifespan,
)


def _runtime(request: Request) -> BrowserRuntime:
    return cast(BrowserRuntime, request.app.state.runtime)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "browser-worker", "version": __version__}


@app.post(
    "/api/browser/sessions",
    response_model=SessionCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(payload: SessionCreate, request: Request) -> SessionCreated:
    try:
        return await _runtime(request).create_session(payload.initial_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to start isolated browser session",
        ) from exc


@app.post("/api/browser/sessions/{session_id}/actions", response_model=ActionResult)
async def execute_action(
    session_id: SessionId,
    payload: Annotated[BrowserAction, Body(discriminator="type")],
    request: Request,
) -> ActionResult:
    try:
        return await _runtime(request).execute_action(session_id, payload)
    except UnknownSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Browser session not found or already closed",
        ) from exc


@app.delete("/api/browser/sessions/{session_id}", response_model=SessionClosed)
async def close_session(session_id: SessionId, request: Request) -> SessionClosed:
    return await _runtime(request).close_session(session_id)


@app.post(
    "/api/browser/vision-sessions",
    response_model=VisionSessionCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_vision_session(
    payload: VisionSessionCreate, request: Request
) -> VisionSessionCreated:
    try:
        return await _runtime(request).create_vision_session(payload.initial_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to start isolated visual browser session",
        ) from exc


@app.post(
    "/api/browser/vision-sessions/{session_id}/actions",
    response_model=VisionActionResult,
)
async def execute_vision_action(
    session_id: SessionId,
    payload: Annotated[VisionBrowserAction, Body(discriminator="type")],
    request: Request,
) -> VisionActionResult:
    try:
        return await _runtime(request).execute_vision_action(session_id, payload)
    except UnknownSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visual browser session not found or already closed",
        ) from exc


@app.delete("/api/browser/vision-sessions/{session_id}", response_model=VisionSessionClosed)
async def close_vision_session(session_id: SessionId, request: Request) -> VisionSessionClosed:
    try:
        return await _runtime(request).close_vision_session(session_id)
    except UnknownSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visual browser session not found or already closed",
        ) from exc
