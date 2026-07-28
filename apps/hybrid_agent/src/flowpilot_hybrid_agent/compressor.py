import json

from flowpilot_hybrid_agent.schemas import (
    ActionSummary,
    CompressedDomObservation,
    CompressedInteractiveElement,
    CompressedSemanticNode,
    HybridDomObservation,
)

MAX_SEMANTIC_NODES = 32
MAX_INTERACTIVE_ELEMENTS = 40
MAX_COMPRESSED_DOM_BYTES = 12_288
MAX_ACTION_SUMMARIES = 12
MAX_ACTION_SUMMARY_BYTES = 2_048


class CompressionError(RuntimeError):
    pass


class DeterministicDomCompressor:
    def compress(self, source: HybridDomObservation) -> CompressedDomObservation:
        semantic = [
            CompressedSemanticNode(
                role=node.role,
                name=node.name,
                text=node.text,
            )
            for node in source.observation.semantic_nodes[:MAX_SEMANTIC_NODES]
        ]
        interactive = [
            CompressedInteractiveElement(
                element_ref=element.element_ref,
                role=element.role,
                name=element.name,
                state=element.state,
                allowed_actions=element.allowed_actions,
                options=element.options,
            )
            for element in source.observation.interactive_elements[:MAX_INTERACTIVE_ELEMENTS]
        ]
        truncated = (
            source.observation.truncated
            or len(source.observation.semantic_nodes) > len(semantic)
            or len(source.observation.interactive_elements) > len(interactive)
        )
        while True:
            candidate, serialized_bytes = self._candidate(
                source,
                semantic,
                interactive,
                truncated,
            )
            if serialized_bytes <= MAX_COMPRESSED_DOM_BYTES:
                return candidate
            truncated = True
            if semantic:
                semantic.pop()
                continue
            if interactive:
                interactive.pop()
                continue
            raise CompressionError("W6 compressed DOM observation exceeded its byte cap")

    @staticmethod
    def compact_action_history(actions: list[ActionSummary]) -> tuple[str, ...]:
        values = [
            json.dumps(
                {
                    "error_category": action.error_category,
                    "modality": action.modality,
                    "success": action.success,
                    "type": action.action_type,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            for action in actions[-MAX_ACTION_SUMMARIES:]
        ]
        while len(json.dumps(values, separators=(",", ":"), ensure_ascii=True).encode("utf-8")) > (
            MAX_ACTION_SUMMARY_BYTES
        ):
            if not values:
                raise CompressionError("W6 action summary cap cannot encode an empty history")
            values.pop(0)
        return tuple(values)

    @classmethod
    def _candidate(
        cls,
        source: HybridDomObservation,
        semantic: list[CompressedSemanticNode],
        interactive: list[CompressedInteractiveElement],
        truncated: bool,
    ) -> tuple[CompressedDomObservation, int]:
        candidate = CompressedDomObservation(
            modality="dom",
            session_id=source.session_id,
            generation=source.generation,
            observation_id=source.observation.observation_id,
            semantic_nodes=tuple(semantic),
            interactive_elements=tuple(interactive),
            truncated=truncated,
            serialized_bytes=1,
        )
        for _ in range(3):
            serialized_bytes = cls._serialized_bytes(candidate)
            candidate = candidate.model_copy(update={"serialized_bytes": serialized_bytes})
        serialized_bytes = cls._serialized_bytes(candidate)
        candidate = candidate.model_copy(update={"serialized_bytes": serialized_bytes})
        return candidate, cls._serialized_bytes(candidate)

    @staticmethod
    def _serialized_bytes(value: CompressedDomObservation) -> int:
        return len(
            json.dumps(
                value.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        )
