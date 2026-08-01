"""Closed W10 configuration trust roots."""

from dataclasses import dataclass, field
from os import environ
from urllib.parse import urlsplit

from flowpilot_control_api.schemas import ProductionRouteClass

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://flowpilot_control:flowpilot_control_local_only@"
    "control-postgres:5432/flowpilot_control"
)


@dataclass(frozen=True, slots=True)
class TokenBucketPolicy:
    actor_rate: int
    actor_burst: int
    organization_rate: int
    organization_burst: int


@dataclass(frozen=True, slots=True)
class ProductionPolicy:
    queue_total_capacity: int = 64
    queue_organization_capacity: int = 32
    queue_ttl_seconds: int = 300
    lease_ttl_seconds: int = 30
    heartbeat_seconds: int = 10
    drain_seconds: int = 25
    browser_slots: int = 4
    maximum_lease_attempts: int = 3
    retry_after_max_seconds: int = 30

    def bucket(self, route_class: ProductionRouteClass) -> TokenBucketPolicy:
        return {
            ProductionRouteClass.SUBMIT: TokenBucketPolicy(5, 10, 50, 100),
            ProductionRouteClass.READ: TokenBucketPolicy(10, 20, 200, 400),
            ProductionRouteClass.MUTATE: TokenBucketPolicy(2, 4, 25, 50),
        }[route_class]

    def validate(self) -> None:
        if (
            self.queue_total_capacity,
            self.queue_organization_capacity,
            self.queue_ttl_seconds,
            self.lease_ttl_seconds,
            self.heartbeat_seconds,
            self.drain_seconds,
            self.browser_slots,
            self.maximum_lease_attempts,
            self.retry_after_max_seconds,
        ) != (64, 32, 300, 30, 10, 25, 4, 3, 30):
            raise ValueError("W12 production policy differs from the frozen contract")
        expected = {
            ProductionRouteClass.SUBMIT: (5, 10, 50, 100),
            ProductionRouteClass.READ: (10, 20, 200, 400),
            ProductionRouteClass.MUTATE: (2, 4, 25, 50),
        }
        for route_class, values in expected.items():
            policy = self.bucket(route_class)
            if (
                policy.actor_rate,
                policy.actor_burst,
                policy.organization_rate,
                policy.organization_burst,
            ) != values:
                raise ValueError("W12 token bucket differs from the frozen contract")


@dataclass(frozen=True, slots=True)
class OidcPolicy:
    issuer_id: str = "local_keycloak"
    issuer: str = "http://127.0.0.1:8080/realms/flowpilot"
    jwks_url: str = "http://keycloak:8080/realms/flowpilot/protocol/openid-connect/certs"
    audience: str = "flowpilot-control-api"
    client_id: str = "flowpilot-control-web"
    algorithm: str = "RS256"
    header_type: str = "JWT"
    token_type: str = "Bearer"
    request_timeout_seconds: float = 3.0
    max_jwks_fetches: int = 2

    def validate(self) -> None:
        issuer = urlsplit(self.issuer)
        jwks = urlsplit(self.jwks_url)
        if (
            issuer.scheme != "http"
            or issuer.hostname not in {"127.0.0.1", "localhost"}
            or issuer.username
            or issuer.password
            or issuer.query
            or issuer.fragment
            or issuer.path != "/realms/flowpilot"
        ):
            raise ValueError("W10 issuer policy is not the frozen local realm")
        if (
            jwks.scheme != "http"
            or jwks.hostname not in {"keycloak", "127.0.0.1", "localhost"}
            or jwks.username
            or jwks.password
            or jwks.query
            or jwks.fragment
            or jwks.path != "/realms/flowpilot/protocol/openid-connect/certs"
        ):
            raise ValueError("W10 JWKS policy is not the frozen local endpoint")
        if (
            self.issuer_id != "local_keycloak"
            or self.audience != "flowpilot-control-api"
            or self.client_id != "flowpilot-control-web"
            or self.algorithm != "RS256"
            or self.header_type != "JWT"
            or self.token_type != "Bearer"
            or self.max_jwks_fetches != 2
            or self.request_timeout_seconds != 3.0
        ):
            raise ValueError("W10 OIDC policy differs from the frozen contract")


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    allowed_origin: str = "http://127.0.0.1:5173"
    seed_synthetic_identities: bool = False
    oidc: OidcPolicy = field(default_factory=OidcPolicy)
    production: ProductionPolicy = field(default_factory=ProductionPolicy)

    def validate(self) -> None:
        self.oidc.validate()
        self.production.validate()
        origin = urlsplit(self.allowed_origin)
        if (
            origin.scheme != "http"
            or origin.hostname not in {"127.0.0.1", "localhost"}
            or origin.username
            or origin.password
            or origin.path not in {"", "/"}
            or origin.query
            or origin.fragment
        ):
            raise ValueError("Control Web origin must be an exact local HTTP origin")
        if not (
            self.database_url.startswith("postgresql+psycopg://")
            or self.database_url.startswith("sqlite+pysqlite://")
        ):
            raise ValueError("Control database must be PostgreSQL or an explicit test SQLite URL")


def load_settings() -> Settings:
    settings = Settings(
        database_url=environ.get(
            "CONTROL_DATABASE_URL",
            DEFAULT_DATABASE_URL,
        ),
        seed_synthetic_identities=environ.get("W10_SYNTHETIC_SEED", "0") == "1",
    )
    settings.validate()
    return settings
