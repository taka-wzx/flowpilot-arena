import json

import httpx
import pytest
from conftest import make_observation

from flowpilot_dom_agent.glm_model import (
    CHAT_COMPLETIONS_URL,
    MAX_OUTPUT_TOKENS_PER_CALL,
    MODEL_ID,
    PROMPT_CONFIG_VERSION,
    GLMChatCompletionsModel,
    GLMModelError,
)
from flowpilot_dom_agent.model import ModelContext
from flowpilot_dom_agent.schemas import ModelDecision


def make_context(**overrides: int) -> ModelContext:
    values = {
        "remaining_steps": 25,
        "remaining_model_calls": 25,
        "remaining_input_tokens": 100_000,
        "remaining_output_tokens": 20_000,
        "remaining_cost_microusd": 650_000,
    }
    values.update(overrides)
    return ModelContext(
        task_id="w3-joiner-001",
        instruction="Complete the synthetic onboarding using supplied values.",
        observation=make_observation(),
        prior_actions=(),
        **values,
    )


def completed_response(content: str) -> dict[str, object]:
    return {
        "id": "glm_synthetic",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
    }


async def test_glm_adapter_uses_fixed_json_chat_completions_request() -> None:
    choice = json.dumps(
        {
            "action": {
                "type": "click",
                "element_ref": "ref_nonce0001_1",
            },
        }
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == CHAT_COMPLETIONS_URL
        assert request.headers["Authorization"] == "Bearer synthetic-test-key"
        payload = json.loads(request.content)
        assert payload["model"] == MODEL_ID
        assert payload["thinking"] == {"type": "enabled"}
        assert payload["reasoning_effort"] == "high"
        assert payload["do_sample"] is False
        assert payload["stream"] is False
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["max_tokens"] == MAX_OUTPUT_TOKENS_PER_CALL == 2_048
        assert "tools" not in payload
        assert "provider action-choice schema" in payload["messages"][0]["content"]
        assert "no Markdown" in payload["messages"][0]["content"]
        assert "refill a field already marked successful" in payload["messages"][0]["content"]
        assert "Do not return schema_version" in payload["messages"][0]["content"]
        model_input = json.loads(payload["messages"][1]["content"])
        assert model_input["prompt_config_version"] == PROMPT_CONFIG_VERSION
        assert "grader" not in json.dumps(model_input).lower()
        return httpx.Response(200, json=completed_response(choice))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GLMChatCompletionsModel(
            "synthetic-test-key",
            client=client,
            action_id_factory=lambda: "act_glm_test",
        ).complete(make_context())

    decision = ModelDecision.model_validate_json(result.content)
    assert decision.action.type == "click"
    assert decision.action.action_id == "act_glm_test"
    assert decision.action.schema_version == "w4-dom-action/1.0"
    assert decision.action.observation_id == "obs_nonce0001"
    assert decision.action.element_ref == "ref_nonce0001_1"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 2
    assert result.usage.cost_microusd == 34


async def test_glm_adapter_rejects_unaffordable_call_before_network() -> None:
    called = False

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GLMModelError, match="cost budget"):
            await GLMChatCompletionsModel("synthetic-test-key", client=client).complete(
                make_context(remaining_cost_microusd=1)
            )
    assert called is False


async def test_glm_adapter_exposes_only_sanitized_http_failure() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": {"code": 1113, "message": "provider detail must stay private"}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GLMModelError, match=r"HTTP 429 \(1113\)") as raised:
            await GLMChatCompletionsModel("synthetic-test-key", client=client).complete(
                make_context()
            )
    assert "provider detail" not in raised.value.safe_reason


@pytest.mark.parametrize(
    "choice",
    (
        {
            "type": "click",
            "element_ref": "ref_nonce0001_1",
        },
        {
            "schema_version": "w4-model-decision/1.0",
            "action": {
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_legacy_1",
                "type": "click",
                "observation_id": "obs_nonce0001",
                "element_ref": "ref_nonce0001_1",
            },
        },
        {
            "action": {
                "type": "click",
                "element_ref": "ref_nonce0001_1",
                "summary": "Non-executable compatibility metadata",
            },
        },
    ),
)
async def test_glm_adapter_accepts_strict_direct_and_legacy_transport_shapes(
    choice: dict[str, object],
) -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=completed_response(json.dumps(choice)))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GLMChatCompletionsModel(
            "synthetic-test-key",
            client=client,
            action_id_factory=lambda: "act_glm_normalized",
        ).complete(make_context())

    decision = ModelDecision.model_validate_json(result.content)
    assert decision.action.type == "click"
    assert decision.action.action_id == "act_glm_normalized"
    assert decision.action.observation_id == "obs_nonce0001"


async def test_glm_adapter_bounds_finish_summary_before_full_action_validation() -> None:
    choice = json.dumps({"action": {"type": "finish", "summary": "x" * 600}})

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=completed_response(choice))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GLMChatCompletionsModel(
            "synthetic-test-key",
            client=client,
            action_id_factory=lambda: "act_glm_finish",
        ).complete(make_context())

    decision = ModelDecision.model_validate_json(result.content)
    assert decision.action.type == "finish"
    assert decision.action.summary == "x" * 300


async def test_glm_adapter_rejects_invalid_non_action_summary_metadata() -> None:
    choice = json.dumps(
        {
            "action": {
                "type": "click",
                "element_ref": "ref_nonce0001_1",
                "summary": {"unsafe": "shape"},
            }
        }
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=completed_response(choice))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GLMModelError, match="invalid non-action summary") as raised:
            await GLMChatCompletionsModel("synthetic-test-key", client=client).complete(
                make_context()
            )
    assert raised.value.usage is not None


async def test_glm_adapter_rejects_stale_legacy_observation_with_usage() -> None:
    stale_choice = json.dumps(
        {
            "action": {
                "type": "click",
                "observation_id": "obs_stale0001",
                "element_ref": "ref_nonce0001_1",
            }
        }
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=completed_response(stale_choice))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GLMModelError, match="stale observation ID") as raised:
            await GLMChatCompletionsModel("synthetic-test-key", client=client).complete(
                make_context()
            )
    assert raised.value.usage is not None


async def test_glm_adapter_rejects_unknown_provider_choice_fields_with_usage() -> None:
    invalid_choice = json.dumps(
        {
            "action": {
                "type": "click",
                "element_ref": "ref_nonce0001_1",
                "selector": "#unsafe",
            }
        }
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=completed_response(invalid_choice))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GLMModelError, match="strict provider choice") as raised:
            await GLMChatCompletionsModel("synthetic-test-key", client=client).complete(
                make_context()
            )
    assert raised.value.usage is not None
    assert raised.value.usage.input_tokens == 10
    assert "extra_forbidden" in raised.value.safe_reason
    assert "selector" in raised.value.safe_reason
    assert "#unsafe" not in raised.value.safe_reason


async def test_glm_adapter_rejects_abnormal_finish_and_invalid_usage() -> None:
    truncated = completed_response("{}")
    choices = truncated["choices"]
    assert isinstance(choices, list)
    choice = choices[0]
    assert isinstance(choice, dict)
    choice["finish_reason"] = "length"
    invalid_usage = completed_response("{}")
    invalid_usage["usage"] = {"prompt_tokens": True, "completion_tokens": 1}
    responses = iter((truncated, invalid_usage))

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(responses))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = GLMChatCompletionsModel("synthetic-test-key", client=client)
        with pytest.raises(GLMModelError, match="finish normally") as abnormal:
            await model.complete(make_context())
        assert abnormal.value.usage is not None
        assert abnormal.value.usage.input_tokens == 10
        assert abnormal.value.usage.output_tokens == 2
        with pytest.raises(GLMModelError, match="usage"):
            await model.complete(make_context())
