# FlowPilot Arena agent guide

## Repository purpose and current phase

FlowPilot Arena is a production-oriented computer-use Agent paired with a
separate resettable synthetic evaluation environment. The authoritative
roadmap is `docs/project-roadmap.md`; the exact and sole W15 implementation
authority is `docs/agent-contract.md`.

This branch is W15: Evaluation on `week/15-evaluation`. The following published
baselines are immutable and must not be modified, rewritten, rolled back,
retagged, or rereleased:

- W12: PR 35, merge `2c642a67341d0cd1c9c62b6bf883ad8df2853f40`,
  feature/head `b00dff77b1626a3f347abfba485ac5a197b627a7`, tag
  `w12-production`, Release `v0.3.0 - Production Control Plane`.
- W13: PR 36, merge `cedc5f26d41262c955b60854cc69ed4f28baded6`,
  feature/head `902e4078e1ece0f401f1c5c3010e56a7ae62acf5`, tag
  `w13-observability`, Release `v0.4.0 - Observability and Replay`.
- W14: PR 41, merge `6bd960a031069f262fe60fbbb8bf2c65a09e409b`,
  feature/head `2874cfb6c02d8dfcf18baac069157e0a073ddd02`, tag
  `w14-security`, Release `v0.5.0 - Security Suite and Threat Model`.

The expected later tag is `w15-evaluation`. Local authorization stops after
one commit `feat: add W15 evaluation and reporting`. It does not permit push,
PR, merge, tag, Release, workflow dispatch/rerun, W12 Validation, W16 work, or
any real provider, IdP, model, OCR, VLM, embedding, billing, benchmark, account,
personal-data, or egress call.

## W15 scope and authority boundary

W15 may add only deterministic local/CI evaluation protocol verification,
three pre-registered synthetic repetitions, the frozen baseline/ablation
matrix, strict attempt retention and aggregation, an unavailable external-
Benchmark record, and deterministic JSON reporting. The W7 Reporting split is
unblinded only after the protocol/configuration hashes are frozen.

Every W1-W14 API, migration, schema, catalog, split, identity, tenant, RBAC,
approval, audit, queue, rate, lease, fence, receipt, idempotency, trace/replay,
security, and independent-Grader boundary remains unchanged. Agent completion
is still `finished_ungraded`; only the Sandbox database-fact Grader determines
business success. Evaluation/reporting is observation-only and cannot
authorize work, select an organization, change policy, create a business
receipt, or write product state.

W15 adds no W16 Helm/cloud/publication, service, database expansion, dependency,
real data/account/approver, arbitrary URL/API/Shell/SQL/JavaScript capability,
generic benchmark framework, production certification, statistical-
significance claim, or real-cost claim. Security, identity, tenant isolation,
approval, browser isolation, and the Grader are never configurable ablations.

The preferred WorkArena benchmark is unavailable because no versioned local
asset, task subset, licence material, or content checksum exists in the
repository. Do not download, install, substitute, or execute an external
benchmark without new user authorization for the exact source, version,
checksum, licence, and download action. Report it as `unavailable`.

## File ownership and prohibited paths

Change only exact paths listed in `docs/agent-contract.md`. Add a path there
before changing it. Directory wildcards are forbidden. Any new service,
database, dependency, real network/data/provider, Benchmark download, physical
deletion, W16 feature, or generic abstraction requires user direction first.

The literal pre-existing `%SystemDrive%/` path is outside ownership. Do not
inspect, enumerate, copy, modify, stage, scan, ignore, or delete it. Do not
access any `code_review_agent` repository. Preserve unrelated `.tmp/` content.

## Engineering and evaluation conventions

- Python target is 3.13. Use uv; never hand-edit a lockfile. No frontend is in
  the W15 allowlist.
- Use strict/frozen Pydantic, `extra=forbid`, closed enums, canonical sorted-key
  compact UTF-8 JSON, stable SHA-256, and no unused dependency.
- Verify all W3/W7 catalog, split, instance, Reporting-manifest, protocol,
  configuration, schema, and report hashes before processing attempts. Any
  mismatch fails before a result is generated.
- Execute each frozen configuration in the exact task/seed order. Preserve
  every planned primary attempt, including failure, timeout, controlled stop,
  infrastructure error, and missing status. Infrastructure retry is append-only
  and never replaces its primary attempt. Do not selectively rerun or discard.
- Keep Development, Validation, Reporting, and external Benchmark records
  distinct. W12 Validation ordinal 3 is immutable evidence and is not rerun;
  ordinal 4 does not exist.
- The authoritative report is JSON. Markdown is evidence narrative only.
  Reports contain only versions, hashes, opaque references, closed codes,
  counts, aggregate metrics, bounded latencies, and security references. They
  contain no raw task/page/DOM/screenshot/model/tool content, Bearer/approval
  material, Cookie, password, key, DSN, personal data, real secret, URL query,
  or machine path.
- Three repetitions do not support inflated significance claims. Report raw
  repeat summaries, paired percentage-point differences, median/range, and
  explicit uncertainty/availability.
- Real provider/model/OCR/VLM/embedding/billing/egress calls and real cost stay
  exactly zero.

## Required local checks

Run the W15 files through the existing locked Sandbox/Arena development
toolchain (no W15 dependency or lockfile is added):

~~~powershell
Set-Location apps/sandbox_api
uv sync --locked --all-groups
uv run ruff check ../../tests/integration/w15_evaluation.py ../../tests/integration/test_w15_evaluation.py ../../tests/integration/w15_evaluation_smoke.py
uv run ruff format --check ../../tests/integration/w15_evaluation.py ../../tests/integration/test_w15_evaluation.py ../../tests/integration/w15_evaluation_smoke.py
uv run mypy --strict ../../tests/integration/w15_evaluation.py ../../tests/integration/w15_evaluation_smoke.py
uv run pytest ../../tests/integration/test_w15_evaluation.py
~~~

Also run available YAML/workflow policy validation; Compose config/build/up/
health; relevant migration empty upgrade/current/check/downgrade/upgrade;
W4-W14 regression; W13 observability smoke; W14 deterministic security smoke;
W15 Development evaluation smoke; the single W15 frozen Reporting final;
catalog/split/config/schema/report checksum gates; real-call-zero and sensitive-
field scans; exact allowlist/staged/unstaged review; and cleanup.

Finish with the locally available forms of:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
pre-commit run detect-private-key --all-files
gitleaks git --no-banner --redact --exit-code 1 .
git diff --check
git diff -- . ':(exclude)%SystemDrive%'
git status --short --untracked-files=all -- . ':(exclude)%SystemDrive%'
~~~

Record unavailable tooling without weakening a gate or claiming it passed.
Do not run an external Benchmark, W12 formal Validation, or W16 work.

## Git completion discipline

Work only on `week/15-evaluation`. Never develop on `main`, W12, W13, W14, or
another published branch. Development smokes may repeat. The Reporting final
may run once only after protocol freeze and all prerequisite gates pass.

After evidence reconciliation, explicitly stage only exact changed W15
allowlist paths, create the one local commit below, and stop:

~~~text
feat: add W15 evaluation and reporting
~~~

Do not push, open a PR, merge, tag, create a Release, dispatch/rerun CI, or call
a real provider or external Benchmark.
