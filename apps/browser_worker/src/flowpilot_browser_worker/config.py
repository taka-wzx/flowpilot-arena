from dataclasses import dataclass
from os import environ


def _positive_int(name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class WorkerLimits:
    max_actions: int = 50
    max_navigations: int = 10
    max_wait_ms: int = 5_000
    max_fill_chars: int = 300
    max_session_seconds: int = 300
    max_semantic_nodes: int = 120
    max_interactive_elements: int = 80
    max_node_text_chars: int = 240
    max_page_title_chars: int = 200
    max_observation_bytes: int = 32_768
    browser_action_timeout_ms: int = 5_000


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    sandbox_origin: str
    limits: WorkerLimits

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        return cls(
            sandbox_origin=environ.get("SANDBOX_ORIGIN", "http://127.0.0.1:5174"),
            limits=WorkerLimits(
                max_actions=_positive_int("MAX_ACTIONS", 50),
                max_navigations=_positive_int("MAX_NAVIGATIONS", 10),
                max_wait_ms=_positive_int("MAX_WAIT_MS", 5_000),
                max_fill_chars=_positive_int("MAX_FILL_CHARS", 300),
                max_session_seconds=_positive_int("MAX_SESSION_SECONDS", 300),
                max_semantic_nodes=_positive_int("MAX_SEMANTIC_NODES", 120),
                max_interactive_elements=_positive_int("MAX_INTERACTIVE_ELEMENTS", 80),
                max_node_text_chars=_positive_int("MAX_NODE_TEXT_CHARS", 240),
                max_page_title_chars=_positive_int("MAX_PAGE_TITLE_CHARS", 200),
                max_observation_bytes=_positive_int("MAX_OBSERVATION_BYTES", 32_768),
                browser_action_timeout_ms=_positive_int("BROWSER_ACTION_TIMEOUT_MS", 5_000),
            ),
        )
