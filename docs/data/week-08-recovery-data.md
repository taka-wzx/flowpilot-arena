# W8 Checkpoint, idempotency, fault, and retention freeze

## Data classes

W8 introduces no new Task Spec, task template, expected state, grader
predicate, or Reporting result. It adds only:

- encrypted opaque Workflow input envelopes;
- safe deterministic Workflow state and Checkpoint hash lineage;
- task-owned operation receipts containing hashes and closed codes; and
- trusted acceptance fault scenario identifiers and safe counters.

## Prohibited durable content

Temporal, Checkpoints, receipts, logs, and evidence must not contain raw human
brief, objective/postcondition, supplied value, Task Spec, expected state,
grader predicate/checksum, DOM, screenshot, OCR/page/form content, model
output, browser reference/handle, Cookie/Local Storage, credential, encryption
key, token, endpoint, or machine path.

## Canonicalization and hashes

Canonical JSON uses UTF-8, sorted keys, no insignificant whitespace, and
unescaped Unicode. SHA-256 values are lowercase hexadecimal. A Checkpoint hash
excludes only `checkpoint_hash`; a revision hash excludes only
`revision_hash`; a request hash covers the fixed typed mutation projection; a
result hash covers a safe closed outcome projection only.

## Receipt freeze

Table name is `w8_operation_receipts`. Primary uniqueness is task ID plus
idempotency key. Key format is `op_` plus 64 lowercase hex characters. Stored
outcome is `committed`; replay and mismatch are response states, not new rows.
Rows retain task owner, request/plan/step/operation/result hashes or closed
values and database time only. Maximum receipt use per run is 24.

Reset/Seed removes only receipts whose `task_id` is the selected W3 or W7
synthetic task. It never clears another task or null-owned W2 record. The
independent Grader does not read receipts.

## Temporal and Checkpoint retention

The local W8 Temporal namespace retention is one day. Compose cleanup removes
the entire isolated Temporal PostgreSQL volume. No history export is retained
after the plaintext scan. Checkpoints exist only in Temporal history and
Workflow state; they are not copied to Sandbox or repository storage.

## Fault freeze

Faults are acceptance-only closed scenarios with fixed maximum one injection
per named `*_once` scenario and maximum two total injections per run. They are
synthetic control metadata, never derived from page/model content. Development
may run the matrix; Validation may run once after freeze; Reporting receives
no fault, recovery, Agent, Reset/Seed, grade, or result run.

## Immutable evaluation data

W3 retains ten specs, catalog checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`,
and 6/2/2 split. W7 retains 30 templates/90 instances, catalog checksum
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.
