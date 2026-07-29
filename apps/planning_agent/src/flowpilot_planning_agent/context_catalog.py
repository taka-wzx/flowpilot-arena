from datetime import UTC, datetime

from flowpilot_planning_agent.context_schemas import (
    EnterpriseKnowledgeRecord,
    KnowledgeCategory,
    SafeValue,
    canonical_json_bytes,
    content_hash,
    sha256_hex,
)

GLOBAL_SCOPE = "syn_scope_global"
VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)
EXPIRES_AT = datetime(2027, 1, 1, tzinfo=UTC)

QUERY_TERMS: dict[KnowledgeCategory, tuple[SafeValue, ...]] = {
    "joiner_policy": ("joiner", "onboarding", "account", "asset"),
    "mover_policy": ("mover", "transfer", "department", "access"),
    "leaver_policy": ("leaver", "offboarding", "revoke", "release"),
    "permission_matrix": ("permission", "role", "access", "verify"),
    "device_standard": ("device", "asset", "laptop", "standard"),
    "operating_manual": ("operation", "workflow", "recovery", "step"),
}


def _record(
    knowledge_id: str,
    category: KnowledgeCategory,
    safe_value: str,
    keywords: tuple[str, ...],
    version: int,
) -> EnterpriseKnowledgeRecord:
    return EnterpriseKnowledgeRecord(
        knowledge_id=knowledge_id,
        scope_id=GLOBAL_SCOPE,
        category=category,
        safe_value=safe_value,
        keywords=keywords,
        source_id=f"catalog.{category}",
        version=version,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        content_hash=content_hash(safe_value),
    )


# Older duplicate versions are intentional: retrieval must deduplicate before ranking.
ENTERPRISE_CATALOG: tuple[EnterpriseKnowledgeRecord, ...] = (
    _record(
        "knowledge.joiner.v1",
        "joiner_policy",
        "policy.joiner.standard",
        ("joiner", "onboarding", "account"),
        1,
    ),
    _record(
        "knowledge.joiner.v2",
        "joiner_policy",
        "policy.joiner.standard",
        ("joiner", "onboarding", "account", "asset"),
        2,
    ),
    _record(
        "knowledge.mover.v1",
        "mover_policy",
        "policy.mover.standard",
        ("mover", "transfer", "department"),
        1,
    ),
    _record(
        "knowledge.mover.v2",
        "mover_policy",
        "policy.mover.standard",
        ("mover", "transfer", "department", "access"),
        2,
    ),
    _record(
        "knowledge.leaver.v1",
        "leaver_policy",
        "policy.leaver.standard",
        ("leaver", "offboarding", "revoke"),
        1,
    ),
    _record(
        "knowledge.leaver.v2",
        "leaver_policy",
        "policy.leaver.standard",
        ("leaver", "offboarding", "revoke", "release"),
        2,
    ),
    _record(
        "knowledge.permission.v1",
        "permission_matrix",
        "matrix.permission.standard",
        ("permission", "role", "access", "verify"),
        1,
    ),
    _record(
        "knowledge.device.v1",
        "device_standard",
        "standard.device.synthetic",
        ("device", "asset", "laptop", "standard"),
        1,
    ),
    _record(
        "knowledge.manual.v1",
        "operating_manual",
        "manual.operation.bounded",
        ("operation", "workflow", "recovery", "step"),
        1,
    ),
)

CATALOG_CHECKSUM = sha256_hex(
    canonical_json_bytes(
        {"schema_version": "w9-enterprise-catalog/1.0", "records": ENTERPRISE_CATALOG}
    )
)
