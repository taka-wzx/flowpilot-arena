"""Frozen W10 OIDC authentication rejection matrix."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from conftest import StaticJwks, TokenFactory
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from flowpilot_control_api.auth import (
    AuthenticationError,
    HttpJwksSource,
    OidcVerifier,
    extract_bearer,
)
from flowpilot_control_api.config import OidcPolicy


@pytest.mark.anyio
async def test_valid_token_yields_only_hashed_closed_identity(
    policy: OidcPolicy, token_factory: TokenFactory
) -> None:
    verifier = OidcVerifier(
        policy,
        StaticJwks({token_factory.kid: token_factory.private_key.public_key()}),
    )

    verified = await verifier.verify(token_factory.issue())

    assert verified.issuer_id == "local_keycloak"
    assert verified.claimed_role.value == "organization_admin"
    assert len(verified.issuer_hash) == 64
    assert len(verified.subject_hash) == 64
    assert "10000000" not in repr(verified)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ({"claims": {"iss": "http://invalid.local/realms/flowpilot"}}, "token_validation_failed"),
        ({"claims": {"aud": "wrong-audience"}}, "token_validation_failed"),
        ({"claims": {"azp": "wrong-client"}}, "client_rejected"),
        ({"remove": frozenset({"sub"})}, "token_validation_failed"),
        (
            {"claims": {"exp": int((datetime.now(UTC) - timedelta(seconds=1)).timestamp())}},
            "token_validation_failed",
        ),
        (
            {"claims": {"nbf": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())}},
            "token_validation_failed",
        ),
        (
            {"claims": {"iat": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())}},
            "token_validation_failed",
        ),
        ({"claims": {"iat": "invalid"}}, "token_validation_failed"),
        ({"claims": {"typ": "ID"}}, "token_type_rejected"),
        ({"claims": {"flowpilot_role": "global_admin"}}, "role_claim_rejected"),
        ({"headers": {"typ": "JOSE"}}, "header_type_rejected"),
    ],
)
async def test_claim_and_type_rejection_matrix(
    policy: OidcPolicy,
    token_factory: TokenFactory,
    mutation: dict[str, object],
    reason: str,
) -> None:
    verifier = OidcVerifier(
        policy,
        StaticJwks({token_factory.kid: token_factory.private_key.public_key()}),
    )
    token = token_factory.issue(**mutation)  # type: ignore[arg-type]

    with pytest.raises(AuthenticationError, match=reason):
        await verifier.verify(token)


@pytest.mark.anyio
async def test_signature_kid_and_algorithm_rejection(
    policy: OidcPolicy, token_factory: TokenFactory
) -> None:
    verifier = OidcVerifier(
        policy,
        StaticJwks({token_factory.kid: token_factory.private_key.public_key()}),
    )
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(AuthenticationError, match="token_validation_failed"):
        await verifier.verify(token_factory.issue(key=other_key))
    with pytest.raises(AuthenticationError, match="unknown_kid"):
        await verifier.verify(token_factory.issue(headers={"kid": "unknown-runtime-kid"}))
    with pytest.raises(AuthenticationError, match="kid_rejected"):
        await verifier.verify(token_factory.issue(headers={"kid": ""}))
    with pytest.raises(AuthenticationError, match="algorithm_rejected"):
        await verifier.verify(
            token_factory.issue(
                algorithm="HS256",
                key=b"runtime-only-algorithm-confusion-key",
            )
        )
    with pytest.raises(AuthenticationError, match="algorithm_rejected"):
        await verifier.verify(token_factory.issue(algorithm="none", key=""))


def test_bearer_transport_is_header_only() -> None:
    assert (
        extract_bearer(
            "Bearer a.b.c",
            query_names=set(),
            cookie_names=set(),
        )
        == "a.b.c"
    )
    with pytest.raises(AuthenticationError, match="authentication_required"):
        extract_bearer(None, query_names=set(), cookie_names=set())
    with pytest.raises(AuthenticationError, match="malformed_bearer"):
        extract_bearer("bearer a.b.c", query_names=set(), cookie_names=set())
    with pytest.raises(AuthenticationError, match="token_transport_rejected"):
        extract_bearer(
            "Bearer a.b.c",
            query_names={"access_token"},
            cookie_names=set(),
        )
    with pytest.raises(AuthenticationError, match="token_transport_rejected"):
        extract_bearer(
            "Bearer a.b.c",
            query_names=set(),
            cookie_names={"id_token"},
        )


@pytest.mark.anyio
async def test_jwks_refresh_is_bounded_and_unknown_kid_fails_closed(
    policy: OidcPolicy, token_factory: TokenFactory
) -> None:
    jwk = json.loads(RSAAlgorithm.to_jwk(token_factory.private_key.public_key()))
    jwk.update({"kid": "known-key", "use": "sig", "alg": "RS256", "key_ops": ["verify"]})
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"keys": [jwk]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    source = HttpJwksSource(policy, client)

    with pytest.raises(AuthenticationError, match="unknown_kid"):
        await source.get_key("missing-key")

    assert calls == 2
    await client.aclose()
