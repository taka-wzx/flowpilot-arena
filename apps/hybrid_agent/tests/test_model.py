import json

import pytest
from conftest import hybrid_dom_observation, hybrid_vision_observation, supplied_values_brief

from flowpilot_hybrid_agent.compressor import DeterministicDomCompressor
from flowpilot_hybrid_agent.model import (
    DeterministicFakeHybridModel,
    HybridModelContext,
    ModelCallError,
)
from flowpilot_hybrid_agent.schemas import CompressedVisualObservation


def context(observation: object) -> HybridModelContext:
    return HybridModelContext(
        task_id="w3-joiner-001",
        instruction=supplied_values_brief(),
        observation=observation,  # type: ignore[arg-type]
        prior_actions=(),
        remaining_steps=24,
        remaining_model_calls=24,
        remaining_switches=2,
        remaining_dom_observations=24,
        remaining_dom_observation_bytes=262_144,
        remaining_compressed_dom_bytes=147_456,
        remaining_images=24,
        remaining_image_bytes=4_423_680,
        remaining_image_pixels=12_441_600,
        remaining_capture_ms=72_000,
        remaining_input_tokens=100_000,
        remaining_output_tokens=20_000,
        remaining_cost_microusd=0,
    )


async def test_complete_joiner_requires_dom_then_vision_and_uses_current_references() -> None:
    model = DeterministicFakeHybridModel("complete_joiner_dom_to_vision")
    dom = DeterministicDomCompressor().compress(hybrid_dom_observation())

    first = json.loads((await model.complete(context(dom))).content)
    assert first["action"]["modality"] == "dom"
    assert first["action"]["action"]["type"] == "read"
    assert first["action"]["action"]["element_ref"] == dom.interactive_elements[0].element_ref

    visual = hybrid_vision_observation().observation
    compressed_visual = CompressedVisualObservation(
        modality="vision",
        session_id=visual.session_id,
        generation=2,
        observation_id=visual.observation_id,
        visual_observation=visual,
    )
    second = json.loads((await model.complete(context(compressed_visual))).content)
    assert second["action"]["modality"] == "vision"
    assert second["action"]["session_id"] == visual.session_id
    assert second["action"]["generation"] == 2
    assert second["action"]["action"] == {
        "action_id": "act_fake_2",
        "type": "navigate",
        "url": "/itsm",
    }


async def test_complete_joiner_rejects_a_second_dom_turn() -> None:
    model = DeterministicFakeHybridModel("complete_joiner_dom_to_vision")
    dom = DeterministicDomCompressor().compress(hybrid_dom_observation())
    await model.complete(context(dom))
    with pytest.raises(ModelCallError, match="Vision observation"):
        await model.complete(context(dom))
