import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

SECURITY_DECISION_SCHEMA_VERSION: Final[Literal["w14-security-decision/1.0"]] = (
    "w14-security-decision/1.0"
)
MAX_UNTRUSTED_TEXT_CHARS = 16_384

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
SecurityReference = Annotated[str, StringConstraints(pattern=r"^sec_[0-9a-f]{24}$")]


class SecuritySource(StrEnum):
    PAGE = "page"
    DOM = "dom"
    SCREENSHOT = "screenshot"
    TOOL_OUTPUT = "tool_output"
    MODEL_OUTPUT = "model_output"
    REQUEST_BODY = "request_body"
    URL = "url"
    FORWARDING_HEADER = "forwarding_header"


class SecurityCategory(StrEnum):
    NONE = "none"
    PROMPT_INJECTION = "prompt_injection"
    UNTRUSTED_INSTRUCTION = "untrusted_instruction"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CROSS_TENANT_ATTEMPT = "cross_tenant_attempt"
    APPROVAL_BYPASS = "approval_bypass"
    SECRET_EXPOSURE_REDACTION = "secret_exposure_redaction"
    FORBIDDEN_NAVIGATION = "forbidden_navigation"
    SANDBOX_VIOLATION = "sandbox_violation"
    BROWSER_ISOLATION_FAILURE = "browser_isolation_failure"
    CONTROLLED_SAFE_STOP = "controlled_safe_stop"


class SecurityReason(StrEnum):
    NO_RULE_MATCH = "no_rule_match"
    INSTRUCTION_OVERRIDE = "instruction_override"
    UNTRUSTED_POLICY_DIRECTIVE = "untrusted_policy_directive"
    ROLE_AUTHORITY_REQUEST = "role_authority_request"
    ORGANIZATION_BOUNDARY_REQUEST = "organization_boundary_request"
    APPROVAL_GATE_REQUEST = "approval_gate_request"
    SENSITIVE_MATERIAL_DETECTED = "sensitive_material_detected"
    NAVIGATION_BOUNDARY_REQUEST = "navigation_boundary_request"
    ARBITRARY_CAPABILITY_REQUEST = "arbitrary_capability_request"
    ISOLATION_BOUNDARY_REQUEST = "isolation_boundary_request"


class SecurityOutcome(StrEnum):
    ALLOW = "allow"
    REJECT = "reject"
    SAFE_STOP = "safe_stop"


class SecurityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["w14-security-decision/1.0"] = SECURITY_DECISION_SCHEMA_VERSION
    source: SecuritySource
    content_hash: Sha256Hex
    category: SecurityCategory
    reason: SecurityReason
    outcome: SecurityOutcome
    terminal_category: SecurityCategory | None
    security_reference: SecurityReference
    business_side_effects: Literal[0] = 0
    real_egress_calls: Literal[0] = 0
    sensitive_fields_present: Literal[False] = False
    raw_content_present: Literal[False] = False

    @model_validator(mode="after")
    def _validate_closed_state(self) -> "SecurityDecision":
        if self.outcome is SecurityOutcome.ALLOW:
            if (
                self.category is not SecurityCategory.NONE
                or self.reason is not SecurityReason.NO_RULE_MATCH
                or self.terminal_category is not None
            ):
                raise ValueError("allow decisions must retain the closed no-match state")
            return self
        if self.category in {SecurityCategory.NONE, SecurityCategory.CONTROLLED_SAFE_STOP}:
            raise ValueError("rejections require one closed threat category")
        if self.reason is SecurityReason.NO_RULE_MATCH:
            raise ValueError("rejections require one closed threat reason")
        if self.outcome is SecurityOutcome.SAFE_STOP:
            if self.terminal_category is not SecurityCategory.CONTROLLED_SAFE_STOP:
                raise ValueError("safe-stop decisions require the controlled terminal category")
        elif self.terminal_category is not None:
            raise ValueError("non-terminal rejections cannot select a terminal category")
        return self


@dataclass(frozen=True, slots=True)
class _Rule:
    category: SecurityCategory
    reason: SecurityReason
    pattern: re.Pattern[str]


_RULES: Final[tuple[_Rule, ...]] = (
    _Rule(
        SecurityCategory.PROMPT_INJECTION,
        SecurityReason.INSTRUCTION_OVERRIDE,
        re.compile(
            r"\b(?:ignore|disregard|override)\s+(?:all\s+|any\s+)?"
            r"(?:previous|prior|system|developer)\s+(?:instructions?|messages?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.UNTRUSTED_INSTRUCTION,
        SecurityReason.UNTRUSTED_POLICY_DIRECTIVE,
        re.compile(
            r"\b(?:page|tool|system|developer)\s+(?:instruction|directive|policy|message)\s*:",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.PRIVILEGE_ESCALATION,
        SecurityReason.ROLE_AUTHORITY_REQUEST,
        re.compile(
            r"\b(?:grant|make|set|promote|change)\b.{0,48}\b"
            r"(?:admin|administrator|owner|security[_ -]?admin|elevated\s+role)\b",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.CROSS_TENANT_ATTEMPT,
        SecurityReason.ORGANIZATION_BOUNDARY_REQUEST,
        re.compile(
            r"\b(?:cross[- ]tenant|(?:an)?other\s+organi[sz]ation|different\s+tenant|"
            r"switch\s+organi[sz]ation)\b",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.APPROVAL_BYPASS,
        SecurityReason.APPROVAL_GATE_REQUEST,
        re.compile(
            r"\b(?:skip|bypass|disable|forge|ignore)\b.{0,40}\b"
            r"(?:approval|approver|grant|nonce)\b",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.SECRET_EXPOSURE_REDACTION,
        SecurityReason.SENSITIVE_MATERIAL_DETECTED,
        re.compile(
            r"(?:\bauthorization\s*:\s*bearer\b|\bcookie\s*:|"
            r"\b(?:password|passwd|secret|api[_ -]?key|dsn)\s*[=:]|"
            r"\bw14[-_]canary[-_][a-z0-9_-]+)",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.FORBIDDEN_NAVIGATION,
        SecurityReason.NAVIGATION_BOUNDARY_REQUEST,
        re.compile(
            r"(?:\b(?:javascript|file|data|vbscript):|https?://(?:outside|external)\.invalid)",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.SANDBOX_VIOLATION,
        SecurityReason.ARBITRARY_CAPABILITY_REQUEST,
        re.compile(
            r"\b(?:run|execute|eval)\b.{0,36}\b(?:shell|sql|javascript|script|code|command)\b",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        SecurityCategory.BROWSER_ISOLATION_FAILURE,
        SecurityReason.ISOLATION_BOUNDARY_REQUEST,
        re.compile(
            r"\b(?:open\s+(?:a\s+)?new\s+(?:window|tab)|download\s+(?:a\s+)?file|"
            r"reuse\s+(?:another|other)\s+(?:browser\s+)?session)\b",
            re.IGNORECASE,
        ),
    ),
)

_AUTHORIZATION = re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[a-z0-9._~+/=-]+")
_BEARER = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{4,}")
_COOKIE = re.compile(r"(?i)\b(?:set-)?cookie\s*:[^|\r\n]{1,512}")
_ASSIGNMENT = re.compile(
    r"(?i)\b(?:password|passwd|secret|api[_ -]?key|dsn)\s*[=:]\s*[^\s,;]{1,512}"
)
_CANARY = re.compile(r"(?i)\bw14[-_]canary[-_][a-z0-9_-]+")
_EMAIL = re.compile(
    r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?![a-z0-9.-]+\.invalid\b)[a-z0-9.-]+\.[a-z]{2,}\b"
)
_DSN = re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?)://[^\s]+")
_URL_USERINFO = re.compile(r"(?i)\bhttps?://[^\s/@:]+(?::[^\s/@]*)?@[^\s]+")
_URL_SUFFIX = re.compile(r"(?i)(https?://[^\s?#]+)[?#][^\s]*")
_WINDOWS_PATH = re.compile(r"(?i)(?<![a-z0-9])(?:[a-z]:\\|\\\\)[^\s\"']+")
_POSIX_PATH = re.compile(r"(?<![:a-z0-9])/(?:users|home|root|etc|var|tmp)/[^\s\"']+")
_PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN\s+[A-Z ]*PRIVATE\s+KEY-----", re.IGNORECASE)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def redact_sensitive(value: str) -> str:
    redacted = value[:MAX_UNTRUSTED_TEXT_CHARS]
    replacement = "[REDACTED]"
    for pattern in (
        _AUTHORIZATION,
        _BEARER,
        _COOKIE,
        _ASSIGNMENT,
        _CANARY,
        _EMAIL,
        _DSN,
        _URL_USERINFO,
        _WINDOWS_PATH,
        _POSIX_PATH,
        _PRIVATE_KEY_MARKER,
    ):
        redacted = pattern.sub(replacement, redacted)
    redacted = _URL_SUFFIX.sub(r"\1[REDACTED]", redacted)
    return redacted


class SecurityViolation(ValueError):
    def __init__(self, decision: SecurityDecision) -> None:
        self.decision = decision
        super().__init__(f"Security boundary safe stop [{decision.security_reference}]")


class SecurityGuard:
    def evaluate(self, source: SecuritySource, value: str) -> SecurityDecision:
        bounded = value[:MAX_UNTRUSTED_TEXT_CHARS]
        normalized = " ".join(bounded.split()).casefold()
        content_hash = stable_sha256(normalized)
        category = SecurityCategory.NONE
        reason = SecurityReason.NO_RULE_MATCH
        outcome = SecurityOutcome.ALLOW
        terminal_category = None
        for rule in _RULES:
            if rule.pattern.search(normalized):
                category = rule.category
                reason = rule.reason
                outcome = SecurityOutcome.SAFE_STOP
                terminal_category = SecurityCategory.CONTROLLED_SAFE_STOP
                break
        reference_payload = {
            "category": category.value,
            "content_hash": content_hash,
            "reason": reason.value,
            "source": source.value,
        }
        security_reference = f"sec_{stable_sha256(canonical_json(reference_payload))[:24]}"
        return SecurityDecision(
            source=source,
            content_hash=content_hash,
            category=category,
            reason=reason,
            outcome=outcome,
            terminal_category=terminal_category,
            security_reference=security_reference,
        )

    def require_safe(self, source: SecuritySource, value: str) -> SecurityDecision:
        decision = self.evaluate(source, value)
        if decision.outcome is not SecurityOutcome.ALLOW:
            raise SecurityViolation(decision)
        return decision


SECURITY_GUARD: Final[SecurityGuard] = SecurityGuard()
