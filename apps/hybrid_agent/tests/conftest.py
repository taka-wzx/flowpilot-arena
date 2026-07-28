import base64

from flowpilot_hybrid_agent.schemas import (
    DomObservation,
    HybridDomObservation,
    HybridRouteSignals,
    HybridVisionObservation,
    InteractiveElement,
    ObservationId,
    SemanticNode,
    VisualBounds,
    VisualGrounding,
    VisualObservation,
)


def supplied_values_brief() -> str:
    return (
        "Create synthetic joiner records. Supplied synthetic values: employee ID 101; "
        "ticket title Laptop request; username alex.chen; asset tag SYN-100; "
        "laptop model ThinkPad X1; mailbox alex.chen@flowpilot.invalid."
    )


def dom_observation(
    *,
    session_id: str = "bw_abcdefghijklmnop",
    observation_id: ObservationId = "obs_abcdefgh",
    truncated: bool = False,
    node_count: int = 0,
    element_count: int = 1,
) -> DomObservation:
    nodes = tuple(
        SemanticNode(role="paragraph", name=f"Node {index}", text=f"Synthetic node {index}")
        for index in range(node_count)
    )
    elements = tuple(
        InteractiveElement(
            element_ref=f"ref_element{index:04d}",
            role="textbox",
            name=f"Synthetic field {index}",
            state={},
            allowed_actions=("click", "fill", "select", "read", "scroll"),
            options=("Choice",),
        )
        for index in range(element_count)
    )
    return DomObservation(
        schema_version="w4-dom-observation/1.0",
        session_id=session_id,
        observation_id=observation_id,
        current_url="http://sandbox-web/hris",
        page_title="Synthetic",
        semantic_nodes=nodes,
        interactive_elements=elements,
        truncated=truncated,
    )


def hybrid_dom_observation(
    *,
    generation: int = 1,
    truncated: bool = False,
    node_count: int = 0,
    element_count: int = 1,
) -> HybridDomObservation:
    observation = dom_observation(
        observation_id=f"obs_test{generation:04d}",
        truncated=truncated,
        node_count=node_count,
        element_count=element_count,
    )
    return HybridDomObservation(
        schema_version="w6-hybrid-observation/1.0",
        session_id=observation.session_id,
        generation=generation,
        modality="dom",
        observation=observation,
        route_signals=HybridRouteSignals(
            dom_structure="truncated" if truncated else "usable",
            dom_interactive_count=len(observation.interactive_elements),
            dom_observation_bytes=len(observation.model_dump_json().encode("utf-8")),
        ),
    )


def visual_observation(
    *,
    session_id: str = "bw_abcdefghijklmnop",
    generation: int = 1,
    image_bytes: int = 20,
    capture_duration_ms: int = 1,
) -> VisualObservation:
    if image_bytes < 4:
        raise ValueError("synthetic JPEG requires at least four bytes")
    image = b"\xff\xd8" + (b"x" * (image_bytes - 4)) + b"\xff\xd9"
    nonce = f"visual{generation:04d}"
    return VisualObservation(
        schema_version="w5-vision-observation/1.0",
        session_id=session_id,
        observation_id=f"vobs_{nonce}",
        screenshot_ref=f"shot_{nonce}",
        image_mime_type="image/jpeg",
        image_base64=base64.b64encode(image).decode("ascii"),
        image_width=960,
        image_height=540,
        image_bytes=len(image),
        capture_duration_ms=capture_duration_ms,
        groundings=(
            VisualGrounding(
                grounding_ref=f"gref_{nonce}_1",
                bounds=VisualBounds(x=1, y=1, width=10, height=10),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
            VisualGrounding(
                grounding_ref=f"gref_{nonce}_2",
                bounds=VisualBounds(x=20, y=20, width=10, height=10),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
            VisualGrounding(
                grounding_ref=f"gref_{nonce}_3",
                bounds=VisualBounds(x=40, y=40, width=10, height=10),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
            VisualGrounding(
                grounding_ref=f"gref_{nonce}_4",
                bounds=VisualBounds(x=60, y=60, width=10, height=10),
                allowed_actions=("click", "fill", "select", "read", "scroll"),
            ),
        ),
        truncated=False,
    )


def hybrid_vision_observation(
    *,
    generation: int = 2,
    image_bytes: int = 20,
    capture_duration_ms: int = 1,
) -> HybridVisionObservation:
    observation = visual_observation(
        generation=generation,
        image_bytes=image_bytes,
        capture_duration_ms=capture_duration_ms,
    )
    return HybridVisionObservation(
        schema_version="w6-hybrid-observation/1.0",
        session_id=observation.session_id,
        generation=generation,
        modality="vision",
        observation=observation,
        route_signals=HybridRouteSignals(
            dom_structure="usable",
            dom_interactive_count=1,
            dom_observation_bytes=256,
        ),
    )
