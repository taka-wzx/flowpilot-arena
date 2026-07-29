from datetime import datetime

from flowpilot_planning_agent.context_catalog import (
    CATALOG_CHECKSUM,
    ENTERPRISE_CATALOG,
    GLOBAL_SCOPE,
    QUERY_TERMS,
)
from flowpilot_planning_agent.context_schemas import (
    EnterpriseKnowledgeRecord,
    KnowledgeCategory,
    RetrievalMatch,
    RetrievalResult,
    ScopeId,
)


class DeterministicEnterpriseRetriever:
    """Closed lexical lookup over the fixed W9 synthetic catalog."""

    def retrieve(
        self,
        *,
        category: KnowledgeCategory,
        scope_id: ScopeId,
        as_of: datetime,
    ) -> RetrievalResult:
        query_terms = frozenset(QUERY_TERMS[category])
        eligible = tuple(
            record
            for record in ENTERPRISE_CATALOG
            if record.category == category
            and record.scope_id in {GLOBAL_SCOPE, scope_id}
            and record.source == "enterprise_catalog"
            and record.trust == "enterprise_curated"
            and record.valid_from <= as_of
            and (record.expires_at is None or as_of < record.expires_at)
        )

        deduplicated: dict[str, EnterpriseKnowledgeRecord] = {}
        for record in sorted(
            eligible,
            key=lambda value: (
                value.content_hash,
                -value.version,
                value.knowledge_id,
            ),
        ):
            deduplicated.setdefault(record.content_hash, record)

        matches: list[RetrievalMatch] = []
        for record in deduplicated.values():
            score = len(query_terms.intersection(record.keywords))
            if score:
                matches.append(RetrievalMatch(record=record, lexical_score=score))
        matches.sort(
            key=lambda match: (
                -match.lexical_score,
                -match.record.version,
                match.record.content_hash,
                match.record.knowledge_id,
            )
        )
        return RetrievalResult(
            category=category,
            catalog_checksum=CATALOG_CHECKSUM,
            candidate_count=len(eligible),
            selected=tuple(matches[:3]),
        )
