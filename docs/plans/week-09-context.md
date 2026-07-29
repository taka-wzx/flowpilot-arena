# Week 09 plan - Context, Retrieval, Summary, and Organization Memory

## Objective

Preserve W1-W8 and add the smallest deterministic fake-only five-layer context
path, fixed retrieval, task-local summary, scoped organization memory, Context
Assembler, frozen ablations, and cumulative accounting. Exact authority is
`docs/agent-contract.md`.

## Frozen outcomes

| Area | W9 outcome | Deliberate limit |
|---|---|---|
| Task facts | Trusted DB safe projection is first and authoritative | No Agent DB/Arena/Grader route |
| Browser working | Current closed events with exclusive expiry | No DOM/image/OCR/page/form/raw text |
| Short term | Fixed priority/dedupe/caps/hash | No model or cross-task conversation history |
| Organization memory | Exact-scope fake versions/expiry/tombstones | Process-local; no W10 identity/locking |
| Enterprise knowledge | Nine fixed local records, six closed categories | No free query/vector/embedding/provider |
| Assembler | Fixed order/provenance/dedupe/budgets/hash | No context-driven budget expansion |
| Ledger | W9 counters in sole W7 ledger and W8 safe high water | No released cap increase |
| Evaluation | Five Development ablations plus J/M/L independent grade | No Validation by default or Reporting execution |

## Implementation phases

1. Verify official W8 main/tag/PR/Release/CI state, create
   `week/09-context`, read all W8 and roadmap authority, and update W9 contract/
   exact allowlist before code.
2. Add strict context schemas, canonicalization, fixed catalog/checksum,
   deterministic retrieval, summary, and organization-memory lifecycle.
3. Add the Context Assembler, frozen layer/total caps, provenance, precedence,
   expiry/trust/scope filtering, dedupe, hash, and five ablations.
4. Add W9 counters to the existing total ledger and W8 safe usage schema; add
   context and context-backed Planning endpoints without replacing old APIs.
5. Add unit/API/replay/scope/expiry/delete/budget/ablation tests and W9 Compose
   smoke for Development Joiner/Mover/Leaver plus independent Grader.
6. Update architecture, threat, evaluation, data, README, changelog, CI, and
   evidence while preserving W3/W7/W8 freezes and no-migration state.
7. Run every Python/frontend/data/Compose/Alembic/security/diff/path/cleanup
   gate, freeze observed evidence, stage exact allowlist paths, create one local
   W9 commit, and stop before W10.

## Frozen hard limits

- Layer order: task facts, browser working, short term, organization memory,
  enterprise knowledge.
- Total: 32 items, 16,384 canonical item bytes, 4,096 estimated tokens.
- Layer item caps: 8/6/8/6/6; layer byte caps: 4,096/3,072/4,096/3,072/4,096;
  layer token caps: 1,024/768/1,024/768/1,024.
- Summary: 12 inputs, 8 outputs, 4,096 bytes, 1,024 tokens.
- Retrieval: six closed categories, at most 6 candidates, fixed top 3.
- Organization memory per run: at most 6 reads, 6 writes, 6 deletes, and 6
  rejected operations.
- Context assemblies per task-backed run: 1.
- Every W6/W7/W8 action/model/token/image/cost/time/retry/recovery/receipt/
  Checkpoint/fault/replan cap remains unchanged.

## Frozen ablation matrix

`full_five_layer`, `task_facts_only`, `no_short_term`,
`no_enterprise_retrieval`, and `no_organization_memory`. No browser-working
ablation is admitted. All run only on deterministic synthetic Development.

## Handoff boundary

W9 stops after local deterministic evidence and one local commit. Default
delivery does not push, create a PR, merge, tag, release, trigger remote CI,
run Validation, execute Reporting, call a real provider, or begin W10.
