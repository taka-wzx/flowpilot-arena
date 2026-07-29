# W9 context catalog, summary, memory, and ablation freeze

## Enterprise catalog

- Schema: `w9-enterprise-knowledge/1.0`
- Catalog schema: `w9-enterprise-catalog/1.0`
- Record count: 9
- Scope: `syn_scope_global`
- Source/trust: `enterprise_catalog` / `enterprise_curated`
- Validity: `[2026-01-01T00:00:00Z, 2027-01-01T00:00:00Z)`
- Categories: `joiner_policy`, `mover_policy`, `leaver_policy`,
  `permission_matrix`, `device_standard`, `operating_manual`
- Fixed top-k: 3
- Canonical checksum:
  `4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`

Joiner, Mover, and Leaver each contain an intentional version-1/version-2 pair
with equal safe content hash. Retrieval must filter validity, deduplicate the
content hash, retain version 2, and then rank. Other categories have one active
record. Query terms are fixed in code and are not accepted from a caller,
page, model, DOM, image, email, or PDF.

## Safe data classes

W9 adds no Task Spec, expected state, grader predicate, Reporting result,
business account, or personal data. Runtime context accepts only safe synthetic
IDs/codes plus source/trust/version/validity/hash metadata. Raw human brief,
objective, supplied/form value, DOM, screenshot, OCR, page/email/PDF content,
model output, credential, token, endpoint, Cookie, Local Storage, personal data,
and machine path are prohibited from context records, memory, durable usage,
logs, and evidence.

## Summary freeze

Kinds in priority order are unresolved issue, recent action, failure reason,
pending step, and user supplement. Sort within a kind is descending ordinal,
then source hash and event ID. Dedupe key is kind plus safe value. One present
entry from each of the first four kinds is selected before remaining entries.
Limits are 12 input events, 8 output entries, 4,096 canonical entry bytes, and
1,024 estimated tokens. Token estimate is `ceil(bytes / 4)`.

## Organization-memory freeze

Fields are department, role, location, device preference, and approval chain.
Records are keyed by trusted synthetic scope plus memory ID and contain owner
task, source/trust, version, active/tombstone status, validity/expiry, and safe
content hash. Upsert increments exactly one; delete/reset produces a tombstone;
reads omit tombstones and expired records. The store is process-local fake data,
not production persistence or W10 identity/tenant authorization.

## Context and ablation freeze

Layer order is task facts, browser working, short term, organization memory,
enterprise knowledge. Earlier equal content hash wins. Total cap is 32 items,
16,384 canonical item bytes, and 4,096 tokens. Per-layer limits are frozen in
the W9 contract.

Profiles are exactly full five-layer, task-facts-only, no short-term, no
enterprise retrieval, and no organization memory. All retain task facts. No
browser-working ablation is admitted.

## Preserved evaluation data

W3 remains 10 tasks with 6/2/2 split and checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
W7 remains 30 templates/90 instances with 12/8/10 processes and 18/6/6 split,
catalog checksum
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.

W9 Development may use `w7-jml-joiner-001-v1`,
`w7-jml-mover-001-v1`, and `w7-jml-leaver-001-v1`. Validation may run at most
once after freeze. Reporting receives load/schema/checksum validation only and
is not executed.
