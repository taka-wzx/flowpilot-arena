from collections.abc import Iterable
from datetime import datetime

from flowpilot_planning_agent.budget import BudgetExceeded, TotalBudgetLedger
from flowpilot_planning_agent.context_schemas import (
    AblationProfile,
    AssembledContext,
    BrowserWorkingInput,
    ContextAssembleRequest,
    ContextAssembleResult,
    ContextBudgetSnapshot,
    ContextCategory,
    ContextItem,
    ContextLayer,
    KnowledgeCategory,
    LayerCounts,
    MemoryMutation,
    SourceKind,
    TrustLevel,
    canonical_json_bytes,
    content_hash,
    sha256_hex,
)
from flowpilot_planning_agent.memory import OrganizationMemoryStore, ScopeViolation
from flowpilot_planning_agent.retrieval import DeterministicEnterpriseRetriever
from flowpilot_planning_agent.summary import DeterministicShortTermSummarizer

LAYER_ORDER: tuple[ContextLayer, ...] = (
    "task_facts",
    "browser_working",
    "short_term",
    "org_memory",
    "enterprise_knowledge",
)
LAYER_CAPS: dict[ContextLayer, tuple[int, int, int]] = {
    "task_facts": (8, 4_096, 1_024),
    "browser_working": (6, 3_072, 768),
    "short_term": (8, 4_096, 1_024),
    "org_memory": (6, 3_072, 768),
    "enterprise_knowledge": (6, 4_096, 1_024),
}
PROFILE_LAYERS: dict[AblationProfile, frozenset[ContextLayer]] = {
    "full_five_layer": frozenset(LAYER_ORDER),
    "task_facts_only": frozenset({"task_facts"}),
    "no_short_term": frozenset(
        {"task_facts", "browser_working", "org_memory", "enterprise_knowledge"}
    ),
    "no_enterprise_retrieval": frozenset(
        {"task_facts", "browser_working", "short_term", "org_memory"}
    ),
    "no_organization_memory": frozenset(
        {"task_facts", "browser_working", "short_term", "enterprise_knowledge"}
    ),
}


class ContextAssembler:
    def __init__(
        self,
        memory: OrganizationMemoryStore,
        *,
        retriever: DeterministicEnterpriseRetriever | None = None,
        summarizer: DeterministicShortTermSummarizer | None = None,
    ) -> None:
        self._memory = memory
        self._retriever = retriever or DeterministicEnterpriseRetriever()
        self._summarizer = summarizer or DeterministicShortTermSummarizer()

    def assemble(
        self,
        request: ContextAssembleRequest,
        ledger: TotalBudgetLedger,
    ) -> ContextAssembleResult:
        ledger.charge_context_assembly()
        enabled = PROFILE_LAYERS[request.ablation]
        layers: dict[ContextLayer, list[ContextItem]] = {layer: [] for layer in LAYER_ORDER}

        layers["task_facts"] = [
            self._item(
                layer="task_facts",
                item_id=fact.item_id,
                category=fact.category,
                safe_value=fact.safe_value,
                source_id="database.snapshot",
                source="sandbox_database",
                trust="authoritative",
                version=fact.snapshot_version,
                valid_from=request.as_of,
                expires_at=None,
            )
            for fact in sorted(
                request.task_facts,
                key=lambda value: (value.category, value.item_id, value.safe_value),
            )
        ]

        if "browser_working" in enabled:
            current_browser = tuple(
                entry
                for entry in request.browser_working
                if entry.observed_at <= request.as_of < entry.expires_at
            )
            layers["browser_working"] = [
                self._browser_item(entry)
                for entry in sorted(
                    current_browser,
                    key=lambda value: (-value.ordinal, value.category, value.item_id),
                )
            ]

        summary_hash: str | None = None
        pending_memory_mutations: tuple[MemoryMutation, ...] = ()
        if "short_term" in enabled:
            summary = self._summarizer.summarize(
                task_id=request.task_id,
                scope_id=request.scope_id,
                events=request.short_term_events,
            )
            ledger.charge_summary(
                inputs=summary.input_count,
                outputs=summary.emitted_count,
                dropped=summary.dropped_count,
            )
            summary_hash = summary.summary_hash
            layers["short_term"] = [
                self._item(
                    layer="short_term",
                    item_id=f"summary.{entry.kind}.{entry.ordinal}",
                    category=entry.kind,
                    safe_value=entry.safe_value,
                    source_id="summary.current_task",
                    source="task_session",
                    trust="task_supplied",
                    version=1,
                    valid_from=request.as_of,
                    expires_at=None,
                )
                for entry in summary.entries
            ]

        if "org_memory" in enabled:
            write_count = sum(mutation.action == "upsert" for mutation in request.memory_mutations)
            delete_count = sum(mutation.action == "delete" for mutation in request.memory_mutations)
            if (
                write_count > request.budget.max_memory_writes
                or delete_count > request.budget.max_memory_deletes
            ):
                raise BudgetExceeded("memory_budget_exhausted")
            preview = self._memory.clone()
            for mutation in request.memory_mutations:
                try:
                    preview.mutate(
                        actor_scope_id=request.actor_scope_id,
                        scope_id=request.scope_id,
                        task_id=request.task_id,
                        mutation=mutation,
                    )
                except ScopeViolation:
                    ledger.charge_memory(rejections=1)
                    raise
            memory_records = preview.read(
                actor_scope_id=request.actor_scope_id,
                scope_id=request.scope_id,
                as_of=request.as_of,
            )
            ledger.charge_memory(reads=len(memory_records))
            pending_memory_mutations = request.memory_mutations
            layers["org_memory"] = [
                self._item(
                    layer="org_memory",
                    item_id=record.memory_id,
                    category=record.field,
                    safe_value=record.safe_value,
                    source_id=record.memory_id,
                    source="organization_memory",
                    trust="organization_curated",
                    version=record.version,
                    valid_from=record.valid_from,
                    expires_at=record.expires_at,
                )
                for record in memory_records
            ]

        catalog_checksum: str | None = None
        if "enterprise_knowledge" in enabled:
            category = self._retrieval_category(request)
            retrieval = self._retriever.retrieve(
                category=category,
                scope_id=request.scope_id,
                as_of=request.as_of,
            )
            ledger.charge_retrieval(
                candidates=retrieval.candidate_count,
                selected=len(retrieval.selected),
            )
            catalog_checksum = retrieval.catalog_checksum
            layers["enterprise_knowledge"] = [
                self._item(
                    layer="enterprise_knowledge",
                    item_id=match.record.knowledge_id,
                    category=match.record.category,
                    safe_value=match.record.safe_value,
                    source_id=match.record.source_id,
                    source="enterprise_catalog",
                    trust="enterprise_curated",
                    version=match.record.version,
                    valid_from=match.record.valid_from,
                    expires_at=match.record.expires_at,
                )
                for match in retrieval.selected
            ]

        selected = self._budget_and_deduplicate(layers, enabled)
        if not selected or selected[0].layer != "task_facts":
            raise ValueError("authoritative task facts are required")
        for item in selected:
            ledger.charge_context_item(
                canonical_bytes=item.canonical_bytes,
                estimated_tokens=item.estimated_tokens,
            )
        if pending_memory_mutations:
            writes = sum(mutation.action == "upsert" for mutation in pending_memory_mutations)
            deletes = sum(mutation.action == "delete" for mutation in pending_memory_mutations)
            ledger.charge_memory(writes=writes, deletes=deletes)
            for mutation in pending_memory_mutations:
                self._memory.mutate(
                    actor_scope_id=request.actor_scope_id,
                    scope_id=request.scope_id,
                    task_id=request.task_id,
                    mutation=mutation,
                )

        counts = {layer: sum(item.layer == layer for item in selected) for layer in LAYER_ORDER}
        item_bytes = sum(item.canonical_bytes for item in selected)
        item_tokens = sum(item.estimated_tokens for item in selected)
        fields: dict[str, object] = {
            "schema_version": "w9-assembled-context/1.0",
            "run_id": request.run_id,
            "task_id": request.task_id,
            "scope_id": request.scope_id,
            "process": request.process,
            "phase": request.phase,
            "ablation": request.ablation,
            "as_of": request.as_of,
            "database_snapshot_hash": request.database_snapshot_hash,
            "layer_counts": LayerCounts(**counts),
            "budget": ContextBudgetSnapshot(
                item_count=len(selected),
                canonical_bytes=item_bytes,
                estimated_tokens=item_tokens,
            ),
            "summary_hash": summary_hash,
            "retrieval_catalog_checksum": catalog_checksum,
            "items": selected,
        }
        context = AssembledContext.model_validate({**fields, "context_hash": "0" * 64})
        context = context.model_copy(
            update={
                "context_hash": sha256_hex(
                    canonical_json_bytes(context.model_dump(mode="json", exclude={"context_hash"}))
                )
            }
        )
        return ContextAssembleResult(context=context, usage=ledger.snapshot())

    @staticmethod
    def _retrieval_category(request: ContextAssembleRequest) -> KnowledgeCategory:
        if request.phase == "planning":
            process_categories: dict[str, KnowledgeCategory] = {
                "joiner": "joiner_policy",
                "mover": "mover_policy",
                "leaver": "leaver_policy",
            }
            return process_categories[request.process]
        if request.phase == "verifying":
            return "permission_matrix"
        if request.phase == "recovering":
            return "operating_manual"
        return "device_standard"

    @staticmethod
    def _browser_item(entry: BrowserWorkingInput) -> ContextItem:
        return ContextAssembler._item(
            layer="browser_working",
            item_id=entry.item_id,
            category=entry.category,
            safe_value=entry.safe_value,
            source_id="browser.observation",
            source="browser_worker",
            trust="runtime_observed",
            version=entry.ordinal,
            valid_from=entry.observed_at,
            expires_at=entry.expires_at,
        )

    @staticmethod
    def _item(
        *,
        layer: ContextLayer,
        item_id: str,
        category: ContextCategory,
        safe_value: str,
        source_id: str,
        source: SourceKind,
        trust: TrustLevel,
        version: int,
        valid_from: datetime,
        expires_at: datetime | None,
    ) -> ContextItem:
        projection: dict[str, object] = {
            "layer": layer,
            "item_id": item_id,
            "category": category,
            "safe_value": safe_value,
            "source_id": source_id,
            "source": source,
            "trust": trust,
            "version": version,
            "valid_from": valid_from,
            "expires_at": expires_at,
            "content_hash": content_hash(safe_value),
        }
        byte_count = len(canonical_json_bytes(projection))
        return ContextItem.model_validate(
            {
                **projection,
                "canonical_bytes": byte_count,
                "estimated_tokens": (byte_count + 3) // 4,
            }
        )

    @staticmethod
    def _budget_and_deduplicate(
        layers: dict[ContextLayer, list[ContextItem]],
        enabled: frozenset[ContextLayer],
    ) -> tuple[ContextItem, ...]:
        selected: list[ContextItem] = []
        seen_hashes: set[str] = set()
        total_bytes = 0
        total_tokens = 0
        for layer in LAYER_ORDER:
            if layer not in enabled:
                continue
            item_cap, byte_cap, token_cap = LAYER_CAPS[layer]
            layer_items = 0
            layer_bytes = 0
            layer_tokens = 0
            for item in ContextAssembler._unique(layers[layer]):
                if item.content_hash in seen_hashes:
                    continue
                if item.canonical_bytes > byte_cap or item.estimated_tokens > token_cap:
                    raise ValueError("single context item exceeds frozen layer cap")
                if (
                    layer_items >= item_cap
                    or layer_bytes + item.canonical_bytes > byte_cap
                    or layer_tokens + item.estimated_tokens > token_cap
                ):
                    continue
                if (
                    len(selected) >= 32
                    or total_bytes + item.canonical_bytes > 16_384
                    or total_tokens + item.estimated_tokens > 4_096
                ):
                    continue
                selected.append(item)
                seen_hashes.add(item.content_hash)
                layer_items += 1
                layer_bytes += item.canonical_bytes
                layer_tokens += item.estimated_tokens
                total_bytes += item.canonical_bytes
                total_tokens += item.estimated_tokens
        return tuple(selected)

    @staticmethod
    def _unique(items: Iterable[ContextItem]) -> tuple[ContextItem, ...]:
        seen: set[tuple[str, str]] = set()
        result: list[ContextItem] = []
        for item in items:
            key = (item.item_id, item.content_hash)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return tuple(result)
