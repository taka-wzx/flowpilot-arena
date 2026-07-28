import json

from conftest import hybrid_dom_observation

from flowpilot_hybrid_agent.compressor import (
    MAX_ACTION_SUMMARIES,
    MAX_COMPRESSED_DOM_BYTES,
    MAX_INTERACTIVE_ELEMENTS,
    MAX_SEMANTIC_NODES,
    DeterministicDomCompressor,
)
from flowpilot_hybrid_agent.schemas import ActionSummary


def test_dom_compression_is_deterministic_and_within_all_fixed_caps() -> None:
    source = hybrid_dom_observation(node_count=80, element_count=70)
    compressor = DeterministicDomCompressor()
    first = compressor.compress(source)
    second = compressor.compress(source)

    assert first == second
    assert first.serialized_bytes <= MAX_COMPRESSED_DOM_BYTES
    assert len(first.semantic_nodes) <= MAX_SEMANTIC_NODES
    assert len(first.interactive_elements) <= MAX_INTERACTIVE_ELEMENTS
    assert first.truncated is True
    assert all("Synthetic field" in element.name for element in first.interactive_elements)
    encoded = json.dumps(
        first.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    assert first.serialized_bytes == len(encoded)
    if len(first.interactive_elements) < MAX_INTERACTIVE_ELEMENTS:
        assert first.semantic_nodes == ()


def test_action_history_is_generic_bounded_and_drops_oldest_entries() -> None:
    compressor = DeterministicDomCompressor()
    actions = [
        ActionSummary(
            modality="dom",
            action_type="fill",
            success=True,
        )
        for _ in range(MAX_ACTION_SUMMARIES + 5)
    ]
    history = compressor.compact_action_history(actions)

    assert len(history) == MAX_ACTION_SUMMARIES
    assert all("Synthetic" not in item for item in history)
    assert all("element_ref" not in item for item in history)
    assert len(json.dumps(history, separators=(",", ":")).encode("utf-8")) <= 2_048
