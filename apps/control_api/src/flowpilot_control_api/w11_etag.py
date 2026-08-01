"""Strong organization-bound W11 mutable-resource ETags."""

import hashlib
import hmac
import re
from enum import StrEnum

from flowpilot_control_api.etag import PreconditionFailed, PreconditionRequired


class W11ResourceKind(StrEnum):
    AUTHORITY = "authority"
    APPROVAL_REQUEST = "approval-request"
    GRANT = "grant"


_PATTERN = re.compile(
    r'^"w11-(?P<kind>authority|approval-request|grant)-'
    r'(?P<fingerprint>[0-9a-f]{24})-v(?P<version>[1-9][0-9]*)"$'
)


def _fingerprint(kind: W11ResourceKind, organization_id: str, resource_id: str) -> str:
    return hashlib.sha256(f"{kind.value}|{organization_id}|{resource_id}".encode()).hexdigest()[:24]


def strong_w11_etag(
    kind: W11ResourceKind,
    organization_id: str,
    resource_id: str,
    version: int,
) -> str:
    if version < 1:
        raise ValueError("resource version must be positive")
    return f'"w11-{kind.value}-{_fingerprint(kind, organization_id, resource_id)}-v{version}"'


def expected_w11_version(
    value: str | None,
    *,
    kind: W11ResourceKind,
    organization_id: str,
    resource_id: str,
) -> int:
    if value is None:
        raise PreconditionRequired("missing_if_match")
    if value.startswith("W/") or value == "*" or "," in value:
        raise PreconditionFailed("invalid_if_match")
    match = _PATTERN.fullmatch(value)
    if match is None or match.group("kind") != kind.value:
        raise PreconditionFailed("invalid_if_match")
    fingerprint = _fingerprint(kind, organization_id, resource_id)
    if not hmac.compare_digest(match.group("fingerprint"), fingerprint):
        raise PreconditionFailed("invalid_if_match")
    version = int(match.group("version"))
    if version > 2_147_483_647:
        raise PreconditionFailed("invalid_if_match")
    return version
