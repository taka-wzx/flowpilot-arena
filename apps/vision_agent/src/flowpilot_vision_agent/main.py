from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from fastapi import FastAPI, Request

from flowpilot_vision_agent import __version__
from flowpilot_vision_agent.client import BrowserWorkerClient
from flowpilot_vision_agent.loop import VisionAgentLoop
from flowpilot_vision_agent.model import DeterministicFakeVisionModel
from flowpilot_vision_agent.schemas import VisionAgentRunRequest, VisionAgentRunResult


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.browser_client = BrowserWorkerClient(
        environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
    )
    yield
    await app.state.browser_client.close()


app = FastAPI(title="FlowPilot W5 Vision Agent", version=__version__, lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "vision-agent", "version": __version__}


@app.post("/api/vision-agent/runs", response_model=VisionAgentRunResult)
async def run_vision_agent(
    payload: VisionAgentRunRequest, request: Request
) -> VisionAgentRunResult:
    model = DeterministicFakeVisionModel(payload.fake_scenario)
    loop = VisionAgentLoop(request.app.state.browser_client, model)
    return await loop.run(payload.task_id, payload.instruction, payload.budget)
