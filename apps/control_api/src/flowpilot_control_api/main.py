"""Minimal, side-effect-free FastAPI application for W1."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Static health response used only to verify the W1 startup path."""

    status: Literal["ok"] = "ok"
    service: Literal["control-api"] = "control-api"
    version: str = "0.1.0"


app = FastAPI(
    title="FlowPilot Control API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    """Return deterministic process metadata without touching external systems."""

    return HealthResponse()
