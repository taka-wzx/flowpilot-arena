import base64

from fastapi.testclient import TestClient

from flowpilot_browser_worker.hybrid import dom_route_signals
from flowpilot_browser_worker.main import app
from flowpilot_browser_worker.schemas import (
    HybridActionEnvelope,
    HybridActionResult,
    HybridDomObservation,
    HybridObservation,
    HybridObservationRequest,
    HybridSessionClosed,
    HybridSessionCreated,
    Observation,
    RecoveryActionResult,
    RecoveryDomActionEnvelope,
    RecoveryObservationRequest,
    RecoverySessionClosed,
    RecoverySessionCreated,
    SessionClosed,
    SessionCreated,
    VisionActionResult,
    VisionBrowserAction,
    VisionSessionClosed,
    VisionSessionCreated,
)


class StubRuntime:
    async def create_session(self, _: str) -> SessionCreated:
        observation = Observation(
            session_id="bw_abcdefghijklmnop",
            observation_id="obs_abcdefgh",
            current_url="http://sandbox-web/hris",
            page_title="HRIS",
            semantic_nodes=(),
            interactive_elements=(),
            truncated=False,
        )
        return SessionCreated(session_id=observation.session_id, observation=observation)

    async def close_session(self, session_id: str) -> SessionClosed:
        return SessionClosed(session_id=session_id, closed=True)

    async def create_vision_session(self, _: str) -> VisionSessionCreated:
        return VisionSessionCreated(
            session_id="bw_abcdefghijklmnop",
            observation={
                "session_id": "bw_abcdefghijklmnop",
                "observation_id": "vobs_visual0001",
                "screenshot_ref": "shot_visual0001",
                "image_mime_type": "image/jpeg",
                "image_base64": base64.b64encode(b"\xff\xd8fake\xff\xd9").decode("ascii"),
                "image_width": 960,
                "image_height": 540,
                "image_bytes": 8,
                "capture_duration_ms": 1,
                "groundings": (),
                "truncated": False,
            },
        )

    async def execute_vision_action(
        self, session_id: str, action: VisionBrowserAction
    ) -> VisionActionResult:
        return VisionActionResult(
            session_id=session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=action.type == "finish",
            terminal=True,
            message="Visual Agent loop ended",
        )

    async def close_vision_session(self, session_id: str) -> VisionSessionClosed:
        return VisionSessionClosed(session_id=session_id, closed=True)

    async def create_hybrid_session(self, _: str) -> HybridSessionCreated:
        observation = Observation(
            session_id="bw_abcdefghijklmnop",
            observation_id="obs_abcdefgh",
            current_url="http://sandbox-web/hris",
            page_title="Synthetic",
            semantic_nodes=(),
            interactive_elements=(),
            truncated=False,
        )
        return HybridSessionCreated(
            session_id="bw_abcdefghijklmnop",
            observation=HybridDomObservation(
                session_id="bw_abcdefghijklmnop",
                generation=1,
                observation=observation,
                route_signals=dom_route_signals(observation),
            ),
        )

    async def request_hybrid_observation(
        self,
        _: str,
        __: HybridObservationRequest,
    ) -> HybridObservation:
        return (await self.create_hybrid_session("/hris")).observation

    async def execute_hybrid_action(
        self,
        session_id: str,
        action: HybridActionEnvelope,
    ) -> HybridActionResult:
        return HybridActionResult(
            session_id=session_id,
            action_id=action.action.action_id,
            modality=action.modality,
            action_type=action.action.type,
            success=action.action.type == "finish",
            terminal=True,
            message="Hybrid Agent loop ended",
        )

    async def close_hybrid_session(self, session_id: str) -> HybridSessionClosed:
        return HybridSessionClosed(session_id=session_id, closed=True)

    async def create_recovery_session(self, session_epoch: int, _: str) -> RecoverySessionCreated:
        created = await self.create_hybrid_session("/hris")
        return RecoverySessionCreated(
            session_id=created.session_id,
            session_epoch=session_epoch,
            observation=created.observation,
        )

    async def request_recovery_observation(
        self, _: str, __: RecoveryObservationRequest
    ) -> HybridObservation:
        return (await self.create_hybrid_session("/hris")).observation

    async def execute_recovery_action(
        self, session_id: str, action: RecoveryDomActionEnvelope
    ) -> RecoveryActionResult:
        return RecoveryActionResult(
            session_id=session_id,
            session_epoch=action.session_epoch,
            action_id=action.action.action_id,
            action_type=action.action.type,
            success=action.action.type == "finish",
            terminal=True,
            message="Recovery run ended",
        )

    async def close_recovery_session(self, session_id: str) -> RecoverySessionClosed:
        return RecoverySessionClosed(session_id=session_id, session_epoch=1, closed=True)

    async def close_all(self) -> None:
        pass


def test_api_health_strict_session_and_unknown_action_rejection() -> None:
    with TestClient(app) as client:
        app.state.runtime = StubRuntime()
        assert client.get("/healthz").json()["status"] == "ok"
        created = client.post(
            "/api/browser/sessions",
            json={"schema_version": "w4-browser-session/1.0", "initial_path": "/hris"},
        )
        assert created.status_code == 201
        unknown_field = client.post(
            "/api/browser/sessions",
            json={
                "schema_version": "w4-browser-session/1.0",
                "initial_path": "/hris",
                "selector": "#unsafe",
            },
        )
        assert unknown_field.status_code == 422
        unknown_action = client.post(
            "/api/browser/sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_bad",
                "type": "javascript",
                "code": "document.cookie",
            },
        )
        assert unknown_action.status_code == 422
        closed = client.delete("/api/browser/sessions/bw_abcdefghijklmnop")
        assert closed.status_code == 200 and closed.json()["closed"] is True
        vision_created = client.post(
            "/api/browser/vision-sessions",
            json={"schema_version": "w5-vision-session/1.0", "initial_path": "/hris"},
        )
        assert vision_created.status_code == 201
        assert "semantic_nodes" not in vision_created.json()["observation"]
        rejected_coordinate = client.post(
            "/api/browser/vision-sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w5-vision-action/1.0",
                "action_id": "act_vision_bad",
                "type": "read",
                "observation_id": "vobs_visual0001",
                "screenshot_ref": "shot_visual0001",
                "grounding_ref": "gref_visual0001_1",
                "x": 4,
            },
        )
        assert rejected_coordinate.status_code == 422
        vision_closed = client.delete("/api/browser/vision-sessions/bw_abcdefghijklmnop")
        assert vision_closed.status_code == 200 and vision_closed.json()["closed"] is True
        hybrid_created = client.post(
            "/api/browser/hybrid-sessions",
            json={"schema_version": "w6-hybrid-session/1.0", "initial_path": "/hris"},
        )
        assert hybrid_created.status_code == 201
        assert hybrid_created.json()["observation"]["modality"] == "dom"
        hybrid_unknown_field = client.post(
            "/api/browser/hybrid-sessions/bw_abcdefghijklmnop/observations",
            json={
                "schema_version": "w6-hybrid-observation-request/1.0",
                "modality": "vision",
                "selector": "#unsafe",
            },
        )
        assert hybrid_unknown_field.status_code == 422
        hybrid_action = client.post(
            "/api/browser/hybrid-sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w6-hybrid-action-envelope/1.0",
                "session_id": "bw_abcdefghijklmnop",
                "generation": 1,
                "modality": "dom",
                "action": {
                    "action_id": "act_hybrid_finish",
                    "type": "finish",
                    "summary": "Synthetic",
                },
            },
        )
        assert hybrid_action.status_code == 200
        hybrid_closed = client.delete("/api/browser/hybrid-sessions/bw_abcdefghijklmnop")
        assert hybrid_closed.status_code == 200 and hybrid_closed.json()["closed"] is True
        recovery_created = client.post(
            "/api/browser/recovery-sessions",
            json={
                "schema_version": "w8-recovery-session/1.0",
                "initial_path": "/hris",
                "session_epoch": 1,
            },
        )
        assert recovery_created.status_code == 201
        wrong_epoch = client.post(
            "/api/browser/recovery-sessions",
            json={
                "schema_version": "w8-recovery-session/1.0",
                "initial_path": "/hris",
                "session_epoch": 4,
            },
        )
        assert wrong_epoch.status_code == 422
        arbitrary_header = client.post(
            "/api/browser/recovery-sessions/bw_abcdefghijklmnop/actions",
            json={
                "schema_version": "w8-recovery-action-envelope/1.0",
                "session_id": "bw_abcdefghijklmnop",
                "session_epoch": 1,
                "generation": 1,
                "modality": "dom",
                "action": {"action_id": "act_w8_bad", "type": "wait", "duration_ms": 1},
                "headers": {"Authorization": "unsafe"},
            },
        )
        assert arbitrary_header.status_code == 422
        recovery_closed = client.delete("/api/browser/recovery-sessions/bw_abcdefghijklmnop")
        assert recovery_closed.status_code == 200
