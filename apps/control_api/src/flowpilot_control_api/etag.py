"""Strong W10 resource ETags and closed If-Match validation."""

import hashlib
import hmac
import re

from flowpilot_control_api.schemas import ResourceKind

_ETAG_PATTERN = re.compile(
    r'^"(?P<generation>w10|w12)-'
    r"(?P<kind>organization|user|membership|memory|memory-collection|production-run)-"
    r'(?P<fingerprint>[0-9a-f]{24})-v(?P<version>[1-9][0-9]*)"$'
)


class PreconditionRequired(RuntimeError):
    pass


class PreconditionFailed(RuntimeError):
    pass


def _fingerprint(kind: ResourceKind, organization_id: str, resource_id: str) -> str:
    raw = f"{kind.value}|{organization_id}|{resource_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:24]


def strong_etag(
    kind: ResourceKind,
    organization_id: str,
    resource_id: str,
    version: int,
) -> str:
    if version < 1:
        raise ValueError("resource version must be positive")
    generation = "w12" if kind == ResourceKind.PRODUCTION_RUN else "w10"
    return (
        f'"{generation}-{kind.value}-{_fingerprint(kind, organization_id, resource_id)}-v{version}"'
    )


def expected_version(
    value: str | None,
    *,
    kind: ResourceKind,
    organization_id: str,
    resource_id: str,
) -> int:
    if value is None:
        raise PreconditionRequired("missing_if_match")
    if value.startswith("W/") or value == "*" or "," in value:
        raise PreconditionFailed("invalid_if_match")
    match = _ETAG_PATTERN.fullmatch(value)
    generation = "w12" if kind == ResourceKind.PRODUCTION_RUN else "w10"
    if (
        match is None
        or match.group("generation") != generation
        or match.group("kind") != kind.value
    ):
        raise PreconditionFailed("invalid_if_match")
    expected_fingerprint = _fingerprint(kind, organization_id, resource_id)
    if not hmac.compare_digest(match.group("fingerprint"), expected_fingerprint):
        raise PreconditionFailed("invalid_if_match")
    version = int(match.group("version"))
    if version > 2_147_483_647:
        raise PreconditionFailed("invalid_if_match")
    return version
