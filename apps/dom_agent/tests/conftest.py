import pytest

from flowpilot_dom_agent.schemas import (
    ActionResult,
    BrowserAction,
    InteractiveElement,
    Observation,
    SessionCreated,
)


def make_observation(counter: int = 1) -> Observation:
    element = InteractiveElement(
        element_ref=f"ref_nonce{counter:04d}_1",
        role="link",
        name="HRIS",
        state={
            "disabled": False,
            "checked": None,
            "selected": None,
            "expanded": None,
            "readonly": False,
            "required": False,
        },
        allowed_actions=("click", "read", "scroll"),
    )
    return Observation(
        schema_version="w4-dom-observation/1.0",
        session_id="bw_abcdefghijklmnop",
        observation_id=f"obs_nonce{counter:04d}",
        current_url="http://sandbox-web/hris",
        page_title="HRIS",
        semantic_nodes=(),
        interactive_elements=(element,),
        truncated=False,
    )


class FakeBrowserClient:
    def __init__(self) -> None:
        self.counter = 1
        self.actions: list[BrowserAction] = []
        self.closed = False

    async def create_session(self) -> SessionCreated:
        observation = make_observation(self.counter)
        return SessionCreated(
            schema_version="w4-browser-session/1.0",
            session_id=observation.session_id,
            observation=observation,
        )

    async def execute_action(self, session_id: str, action: BrowserAction) -> ActionResult:
        assert session_id == "bw_abcdefghijklmnop"
        self.actions.append(action)
        if action.type in {"finish", "fail"}:
            self.closed = True
            return ActionResult(
                schema_version="w4-dom-action-result/1.0",
                session_id=session_id,
                action_id=action.action_id,
                action_type=action.type,
                success=action.type == "finish",
                terminal=True,
                message="terminal",
            )
        self.counter += 1
        return ActionResult(
            schema_version="w4-dom-action-result/1.0",
            session_id=session_id,
            action_id=action.action_id,
            action_type=action.type,
            success=True,
            terminal=False,
            message="ok",
            observation=make_observation(self.counter),
        )

    async def close_session(self, _: str) -> None:
        self.closed = True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_browser() -> FakeBrowserClient:
    return FakeBrowserClient()
