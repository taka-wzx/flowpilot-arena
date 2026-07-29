from datetime import UTC, datetime

from flowpilot_planning_agent.context_catalog import CATALOG_CHECKSUM
from flowpilot_planning_agent.retrieval import DeterministicEnterpriseRetriever


def test_retrieval_filters_deduplicates_versions_and_orders_deterministically() -> None:
    retriever = DeterministicEnterpriseRetriever()
    as_of = datetime(2026, 7, 29, tzinfo=UTC)
    first = retriever.retrieve(
        category="joiner_policy",
        scope_id="syn_scope_alpha",
        as_of=as_of,
    )
    second = retriever.retrieve(
        category="joiner_policy",
        scope_id="syn_scope_alpha",
        as_of=as_of,
    )
    assert first == second
    assert first.catalog_checksum == CATALOG_CHECKSUM
    assert len(CATALOG_CHECKSUM) == 64
    assert first.candidate_count == 2
    assert len(first.selected) == 1
    assert first.selected[0].record.version == 2
    assert first.selected[0].record.source == "enterprise_catalog"
    assert first.selected[0].record.trust == "enterprise_curated"


def test_retrieval_rejects_expired_catalog_entries() -> None:
    result = DeterministicEnterpriseRetriever().retrieve(
        category="joiner_policy",
        scope_id="syn_scope_alpha",
        as_of=datetime(2028, 1, 1, tzinfo=UTC),
    )
    assert result.candidate_count == 0
    assert result.selected == ()
