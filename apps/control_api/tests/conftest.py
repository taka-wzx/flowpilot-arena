"""Runtime-only W10 identity fixtures; no private key or token is persisted."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from flowpilot_control_api.auth import AuthenticationError, OidcVerifier
from flowpilot_control_api.config import OidcPolicy, Settings
from flowpilot_control_api.database import build_engine, get_session
from flowpilot_control_api.main import create_app
from flowpilot_control_api.models import Base
from flowpilot_control_api.seed import seed_synthetic_identities


class StaticJwks:
    def __init__(self, keys: dict[str, object]) -> None:
        self.keys = keys

    async def get_key(self, kid: str) -> object:
        try:
            return self.keys[kid]
        except KeyError as exc:
            raise AuthenticationError("unknown_kid") from exc

    async def close(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class TokenFactory:
    private_key: rsa.RSAPrivateKey
    policy: OidcPolicy
    kid: str = "w10-runtime-test-key"

    def issue(
        self,
        *,
        subject: str = "10000000-0000-0000-0000-000000000001",
        role: str = "organization_admin",
        claims: dict[str, Any] | None = None,
        remove: frozenset[str] = frozenset(),
        headers: dict[str, object] | None = None,
        key: object | None = None,
        algorithm: str = "RS256",
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "iss": self.policy.issuer,
            "aud": self.policy.audience,
            "azp": self.policy.client_id,
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "typ": self.policy.token_type,
            "flowpilot_role": role,
        }
        if claims:
            payload.update(claims)
        for name in remove:
            payload.pop(name, None)
        token_headers: dict[str, object] = {"kid": self.kid, "typ": "JWT"}
        if headers:
            token_headers.update(headers)
        signing_key = self.private_key if key is None else key
        return jwt.encode(payload, signing_key, algorithm=algorithm, headers=token_headers)


@pytest.fixture
def policy() -> OidcPolicy:
    return OidcPolicy()


@pytest.fixture
def token_factory(policy: OidcPolicy) -> TokenFactory:
    return TokenFactory(
        private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048),
        policy=policy,
    )


@pytest.fixture
def database_engine(tmp_path: Path, policy: OidcPolicy) -> Iterator[Engine]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'w10-control.db').as_posix()}"
    database_engine = build_engine(database_url)
    Base.metadata.create_all(database_engine)
    with Session(database_engine) as session:
        seed_synthetic_identities(session, policy)
    yield database_engine
    database_engine.dispose()


@pytest.fixture
def client(
    database_engine: Engine,
    token_factory: TokenFactory,
    policy: OidcPolicy,
) -> Iterator[TestClient]:
    verifier = OidcVerifier(
        policy,
        StaticJwks({token_factory.kid: token_factory.private_key.public_key()}),
    )
    application = create_app(
        settings=Settings(
            database_url=str(database_engine.url),
            allowed_origin="http://127.0.0.1:5173",
            oidc=policy,
        ),
        verifier=verifier,
        run_startup=False,
    )

    def override_session() -> Iterator[Session]:
        with Session(database_engine) as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(token_factory: TokenFactory) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_factory.issue()}"}
