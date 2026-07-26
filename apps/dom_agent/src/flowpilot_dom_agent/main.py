from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from fastapi import FastAPI, HTTPException, Request

from flowpilot_dom_agent import __version__
from flowpilot_dom_agent.client import BrowserWorkerClient
from flowpilot_dom_agent.loop import AgentLoop
from flowpilot_dom_agent.model import DeterministicFakeModel, ModelClient
from flowpilot_dom_agent.openai_model import OpenAIResponsesModel
from flowpilot_dom_agent.schemas import AgentRunRequest, AgentRunResult


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.browser_client = BrowserWorkerClient(
        environ.get("BROWSER_WORKER_URL", "http://127.0.0.1:8002")
    )
    yield
    await app.state.browser_client.close()


app = FastAPI(title="FlowPilot W4 DOM Agent", version=__version__, lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "dom-agent", "version": __version__}


@app.post("/api/agent/runs", response_model=AgentRunResult)
async def run_agent(payload: AgentRunRequest, request: Request) -> AgentRunResult:
    model: ModelClient
    if payload.model == "deterministic-fake":
        model = DeterministicFakeModel(payload.fake_scenario)
    else:
        api_key = environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=503, detail="Authorized model credential is unavailable"
            )
        model = OpenAIResponsesModel(api_key)
    loop = AgentLoop(request.app.state.browser_client, model)
    return await loop.run(payload.task_id, payload.instruction, payload.budget)
