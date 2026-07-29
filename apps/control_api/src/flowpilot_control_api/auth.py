"""Strict fixed-policy W10 OIDC access-token verification."""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any, Protocol, cast

import httpx
import jwt
from jwt import PyJWK
from jwt.exceptions import PyJWTError

from flowpilot_control_api.config import OidcPolicy
from flowpilot_control_api.schemas import Role

TOKEN_QUERY_NAMES = frozenset({"access_token", "id_token", "refresh_token", "token"})


class AuthenticationError(RuntimeError):
    def __init__(self, reason: str = "invalid_authentication") -> None:
        super().__init__(reason)
        self.reason = reason


class JwksSource(Protocol):
    async def get_key(self, kid: str) -> object: ...

    async def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    issuer_id: str
    issuer_hash: str
    subject_hash: str
    claimed_role: Role


def extract_bearer(
    authorization: str | None,
    *,
    query_names: set[str],
    cookie_names: set[str],
) -> str:
    if TOKEN_QUERY_NAMES & (query_names | cookie_names):
        raise AuthenticationError("token_transport_rejected")
    if authorization is None:
        raise AuthenticationError("authentication_required")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
        raise AuthenticationError("malformed_bearer")
    token = parts[1]
    if len(token) > 16_384 or token.count(".") != 2 or any(char.isspace() for char in token):
        raise AuthenticationError("malformed_bearer")
    return token


class HttpJwksSource:
    """Exact-endpoint JWKS cache with one initial fetch and one refresh."""

    def __init__(self, policy: OidcPolicy, client: httpx.AsyncClient | None = None) -> None:
        policy.validate()
        self._policy = policy
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(policy.request_timeout_seconds),
            follow_redirects=False,
        )
        self._owns_client = client is None
        self._keys: dict[str, object] = {}
        self._fetches = 0
        self._lock = asyncio.Lock()

    async def _refresh(self) -> None:
        if self._fetches >= self._policy.max_jwks_fetches:
            raise AuthenticationError("jwks_refresh_exhausted")
        self._fetches += 1
        try:
            response = await self._client.get(self._policy.jwks_url)
            response.raise_for_status()
            if len(response.content) > 65_536:
                raise AuthenticationError("jwks_invalid")
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AuthenticationError("jwks_unavailable") from exc
        if not isinstance(payload, dict) or set(payload) != {"keys"}:
            raise AuthenticationError("jwks_invalid")
        records = payload["keys"]
        if not isinstance(records, list) or not 1 <= len(records) <= 8:
            raise AuthenticationError("jwks_invalid")
        keys: dict[str, object] = {}
        try:
            for record in records:
                if not isinstance(record, dict):
                    raise AuthenticationError("jwks_invalid")
                kid = record.get("kid")
                if not isinstance(kid, str) or not 1 <= len(kid) <= 128 or kid in keys:
                    raise AuthenticationError("jwks_invalid")
                if (
                    record.get("kty") != "RSA"
                    or record.get("use") != "sig"
                    or record.get("alg") != self._policy.algorithm
                ):
                    continue
                key_ops = record.get("key_ops")
                if key_ops is not None and (
                    not isinstance(key_ops, list) or "verify" not in key_ops
                ):
                    continue
                keys[kid] = PyJWK.from_dict(record, algorithm=self._policy.algorithm).key
        except (PyJWTError, ValueError, TypeError) as exc:
            raise AuthenticationError("jwks_invalid") from exc
        if not keys:
            raise AuthenticationError("jwks_invalid")
        self._keys = keys

    async def get_key(self, kid: str) -> object:
        async with self._lock:
            if not self._keys:
                await self._refresh()
            key = self._keys.get(kid)
            if key is None and self._fetches < self._policy.max_jwks_fetches:
                await self._refresh()
                key = self._keys.get(kid)
            if key is None:
                raise AuthenticationError("unknown_kid")
            return key

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class OidcVerifier:
    def __init__(self, policy: OidcPolicy, jwks: JwksSource) -> None:
        policy.validate()
        self._policy = policy
        self._jwks = jwks

    async def verify(self, token: str) -> VerifiedIdentity:
        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:
            raise AuthenticationError("malformed_token") from exc
        if not isinstance(header, dict):
            raise AuthenticationError("malformed_token")
        if header.get("alg") != self._policy.algorithm:
            raise AuthenticationError("algorithm_rejected")
        if header.get("typ") != self._policy.header_type:
            raise AuthenticationError("header_type_rejected")
        kid = header.get("kid")
        if not isinstance(kid, str) or not 1 <= len(kid) <= 128:
            raise AuthenticationError("kid_rejected")
        key = await self._jwks.get_key(kid)
        try:
            claims = jwt.decode(
                token,
                key=cast(Any, key),
                algorithms=[self._policy.algorithm],
                audience=self._policy.audience,
                issuer=self._policy.issuer,
                options={
                    "require": ["iss", "aud", "sub", "exp", "iat", "azp", "typ", "flowpilot_role"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
                leeway=0,
            )
        except PyJWTError as exc:
            raise AuthenticationError("token_validation_failed") from exc
        if claims.get("azp") != self._policy.client_id:
            raise AuthenticationError("client_rejected")
        if claims.get("typ") != self._policy.token_type:
            raise AuthenticationError("token_type_rejected")
        subject = claims.get("sub")
        if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
            raise AuthenticationError("subject_rejected")
        role_claim = claims.get("flowpilot_role")
        if not isinstance(role_claim, str):
            raise AuthenticationError("role_claim_rejected")
        try:
            role = Role(role_claim)
        except ValueError as exc:
            raise AuthenticationError("role_claim_rejected") from exc
        return VerifiedIdentity(
            issuer_id=self._policy.issuer_id,
            issuer_hash=hashlib.sha256(self._policy.issuer.encode()).hexdigest(),
            subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
            claimed_role=role,
        )

    async def close(self) -> None:
        await self._jwks.close()
