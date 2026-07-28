from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from fastapi import FastAPI, Request

from flowpilot_hybrid_agent import __version__
from flowpilot_hybrid_agent.client import BrowserWorkerClient
from flowpilot_hybrid_agent.loop import HybridAgentLoop
from flowpilot_hybrid_agent.model import DeterministicFakeHybridModel
from flowpilot_hybrid_agent.schemas import HybridAgentRunRequest, HybridAgentRunResult


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.browser_client = BrowserWorkerClient(
        environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
    )
    yield
    await app.state.browser_client.close()


app = FastAPI(title="FlowPilot W6 Hybrid Agent", version=__version__, lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "hybrid-agent", "version": __version__}


@app.post("/api/hybrid-agent/runs", response_model=HybridAgentRunResult)
async def run_hybrid_agent(
    payload: HybridAgentRunRequest,
    request: Request,
) -> HybridAgentRunResult:
    model = DeterministicFakeHybridModel(payload.fake_scenario)
    loop = HybridAgentLoop(request.app.state.browser_client, model)
    return await loop.run(
        payload.task_id,
        payload.instruction,
        payload.route_category,
        payload.budget,
    )
