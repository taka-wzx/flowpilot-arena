import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

from flowpilot_browser_worker.config import WorkerLimits

ALLOWED_BUSINESS_PATHS = frozenset({"/hris", "/itsm", "/iam", "/assets", "/mail"})
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CARD_LIKE_NUMBER = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_SENSITIVE_WORDS = re.compile(r"(?i)\b(password|passwd|secret|api[_ -]?key|bearer|token)\b")


class PolicyViolation(ValueError):
    """Raised when untrusted input violates the W4 browser policy."""


@dataclass(frozen=True, slots=True)
class URLPolicy:
    origin: str

    def __post_init__(self) -> None:
        parsed = urlsplit(self.origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("SANDBOX_ORIGIN must be an absolute HTTP(S) origin")
        if parsed.hostname.lower() not in {"sandbox-web", "localhost", "127.0.0.1", "::1"}:
            raise ValueError("SANDBOX_ORIGIN must name the local Sandbox Web service")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("SANDBOX_ORIGIN must not contain credentials, query, or fragment")
        if parsed.path not in {"", "/"}:
            raise ValueError("SANDBOX_ORIGIN must not include a path")
        normalized = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), "", "", ""))
        object.__setattr__(self, "origin", normalized)

    @property
    def _parts(self) -> tuple[str, str]:
        parsed = urlsplit(self.origin)
        return parsed.scheme, parsed.netloc

    def resolve_navigation(self, value: str) -> str:
        candidate = urljoin(f"{self.origin}/", value)
        parsed = urlsplit(candidate)
        if parsed.username or parsed.password:
            raise PolicyViolation("URL credentials are forbidden")
        if parsed.scheme.lower() != self._parts[0] or parsed.netloc.lower() != self._parts[1]:
            raise PolicyViolation("Navigation must stay on the configured Sandbox origin")
        if parsed.query or parsed.fragment:
            raise PolicyViolation("Navigation query strings and fragments are forbidden")
        path = parsed.path.rstrip("/") or "/"
        if path not in ALLOWED_BUSINESS_PATHS:
            raise PolicyViolation("Navigation path is not an allowed Sandbox business page")
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))

    def allows_request(self, value: str) -> bool:
        parsed = urlsplit(value)
        if parsed.username or parsed.password:
            return False
        return (
            parsed.scheme.lower() == self._parts[0]
            and parsed.netloc.lower() == self._parts[1]
            and not parsed.fragment
        )

    def assert_final_navigation(self, value: str) -> None:
        self.resolve_navigation(value)


def validate_fill_text(text: str, input_type: str, limits: WorkerLimits) -> None:
    if len(text) > limits.max_fill_chars:
        raise PolicyViolation("Fill text exceeds the configured length limit")
    if input_type.lower() == "password":
        raise PolicyViolation("Password fields are forbidden")
    if _CONTROL_CHARACTERS.search(text) or "\r" in text or "\n" in text:
        raise PolicyViolation("Control characters and multiline input are forbidden")
    if _CARD_LIKE_NUMBER.search(text):
        raise PolicyViolation("Payment-account-like input is forbidden")
    if _SENSITIVE_WORDS.search(text):
        raise PolicyViolation("Credential-like input is forbidden")
    if "@" in text and not text.lower().endswith(".invalid"):
        raise PolicyViolation("Email input must use a non-deliverable .invalid domain")
