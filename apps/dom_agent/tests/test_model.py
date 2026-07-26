import json

import httpx
import pytest
from conftest import make_observation

from flowpilot_dom_agent.model import ModelContext
from flowpilot_dom_agent.openai_model import (
    MODEL_ID,
    PROMPT_CONFIG_VERSION,
    RESPONSES_URL,
    OpenAIModelError,
    OpenAIResponsesModel,
    _strict_decision_schema,
)


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
        "id": "resp_synthetic",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": content}],
            }
        ],
        "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
    }


async def test_openai_adapter_uses_fixed_strict_responses_request() -> None:
    decision = json.dumps(
        {
            "schema_version": "w4-model-decision/1.0",
            "action": {
                "schema_version": "w4-dom-action/1.0",
                "action_id": "act_finish",
                "type": "finish",
                "summary": "Synthetic task complete; grading remains external",
            },
        }
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == RESPONSES_URL
        assert request.headers["Authorization"] == "Bearer synthetic-test-key"
        payload = json.loads(request.content)
        assert payload["model"] == MODEL_ID
        assert payload["store"] is False
        assert payload["reasoning"] == {"effort": "medium"}
        assert payload["text"]["verbosity"] == "low"
        assert payload["text"]["format"]["strict"] is True
        assert "tools" not in payload
        model_input = json.loads(payload["input"][0]["content"][0]["text"])
        assert model_input["prompt_config_version"] == PROMPT_CONFIG_VERSION
        assert "grader" not in json.dumps(model_input).lower()
        return httpx.Response(200, json=completed_response(decision))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await OpenAIResponsesModel("synthetic-test-key", client=client).complete(
            make_context()
        )

    assert result.content == decision
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 2
    assert result.usage.cost_microusd == 62


def test_provider_schema_requires_every_property_and_has_no_defaults() -> None:
    schema = _strict_decision_schema()

    def inspect(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                inspect(item)
            return
        if not isinstance(value, dict):
            return
        assert "default" not in value
        assert "discriminator" not in value
        assert "oneOf" not in value
        assert "pattern" not in value
        properties = value.get("properties")
        if isinstance(properties, dict):
            assert value["additionalProperties"] is False
            assert set(value["required"]) == set(properties)
        for item in value.values():
            inspect(item)

    inspect(schema)


async def test_openai_adapter_rejects_unaffordable_call_before_network() -> None:
    called = False

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OpenAIModelError, match="cost budget"):
            await OpenAIResponsesModel("synthetic-test-key", client=client).complete(
                make_context(remaining_cost_microusd=1)
            )
    assert called is False


async def test_openai_adapter_rejects_refusal_and_invalid_usage() -> None:
    refusal = {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "refusal", "refusal": "synthetic refusal"}],
            }
        ],
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    invalid_usage = completed_response("{}").copy()
    invalid_usage["usage"] = {"input_tokens": True, "output_tokens": 1}
    responses = iter((refusal, invalid_usage))

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(responses))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = OpenAIResponsesModel("synthetic-test-key", client=client)
        with pytest.raises(OpenAIModelError, match="refused"):
            await model.complete(make_context())
        with pytest.raises(OpenAIModelError, match="usage"):
            await model.complete(make_context())
