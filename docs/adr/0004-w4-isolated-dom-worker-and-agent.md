# ADR 0004: Isolated DOM Browser Worker and separate bounded Agent

- Status: Accepted for W4
- Date: 2026-07-26

## Context

W4 must add Playwright DOM/accessibility observation, typed browser actions,
and a minimal DOM-only ReAct loop without weakening W1-W3 or introducing W5+
features. The Browser Worker must not share Sandbox database credentials,
repository files, a Docker socket, arbitrary external networking, or an
arbitrary code/selector interface. Model output must not directly reach a
browser, Reset/Seed, database, or Grader.

The roadmap has two ambiguities that require conservative resolution. Its W4
row clearly authorizes the DOM Agent milestone, while its final bootstrap
paragraph still says to start W1. The completed W1-W3 releases and explicit W4
brief make that paragraph historical, not a prohibition on the current branch.
Also, W3 task prose refers to “supplied synthetic identifiers” although several
exact target values live in structured expected state rather than the three
`instructions` strings. W4 must make those immutable inputs human-readable
without changing the specs/checksums or exposing grader execution to the model.

## Decision

Create two independent Python 3.13 applications and containers.

`apps/browser_worker` owns Playwright and exposes only session creation,
versioned typed action execution, session deletion, and health. It starts a new
Browser, Browser Context, and Page for every task. It uses an exact configured
Sandbox Web origin, request interception, final-URL validation, bounded waits,
and unconditional cleanup. It returns a normalized bounded semantic summary
and interactive elements with observation-scoped opaque references. It never
returns locators/selectors or accepts code/browser options.

`apps/dom_agent` owns the minimal ReAct loop. Its model interface receives a
human instruction brief, current observation, bounded prior-action summaries,
and remaining budgets, then returns JSON validated as the same typed action
shape. The loop can call only Browser Worker HTTP. It has no Sandbox API or
database network and no Reset/Seed/Grader client. Default runtime and all CI
paths use a deterministic fake model.

After the separately disclosed user authorization on 2026-07-26, one
profile-only real Agent instance may use the same image and loop. Its only code
path beyond the Browser Worker is a fixed HTTPS call to OpenAI Responses with
exact model `gpt-5.6-terra`, strict action JSON Schema, no provider tools, no
retries, and environment-only credentials. It never accepts a provider URL.

Keep task lifecycle management outside both components. An acceptance caller
uses W3 management APIs to load a fixed task, compare two Reset/Seed results,
render title/instructions plus the immutable supplied synthetic values into a
human-facing text brief, invoke the Agent, and call the W3 Grader afterward.
It never gives grader predicates, database access, or a success flag to the
model. A model `finish` only terminates the loop; only a separate 100/100 grade
is success.

Use versioned JSON HTTP rather than a shared in-process package. This preserves
the process/container boundary and makes unknown-field rejection testable at
both trust boundaries. Do not add a generic model gateway in W4.

Compose assigns explicit networks:

- `sandbox-backend`: PostgreSQL, Sandbox API, and Sandbox Web only;
- `browser-sandbox`: Sandbox Web and Browser Worker only;
- `agent-worker`: DOM Agent and Browser Worker only.

All three are internal networks. Host ports bind to loopback only. The Browser
Worker has no host bind mount or Docker socket, runs non-root with a read-only
root filesystem, drops capabilities, sets no-new-privileges, uses bounded
tmpfs storage, and receives no database environment variable. DOM Agent uses
equivalent non-root/read-only restrictions and receives only the Browser Worker
URL.

The authorized `real-acceptance` profile adds a non-internal `model-egress`
bridge only to the profile-only real Agent. The trusted acceptance caller still
owns Reset/Seed and Grader, reaches the real Agent over `agent-worker`, and
receives no key. Default services, CI, and fake smoke never attach to this
bridge. Compose cannot domain-allowlist an outbound bridge, so the fixed
application destination and profile-only lifecycle are the W4 containment.

Pin Playwright Python to `1.60.0`, matching its `148.0.7778.96` Chromium build,
and pin uv to `0.11.14`. Pin Python/container tags and record resolved image
digests and observed runtime versions in the W4 evidence report. Install only
Chromium, not Firefox or WebKit.

No database migration is necessary. W2/W3 schemas and migrations remain
unchanged.

## Consequences

- Browser compromise has no direct route or credential to PostgreSQL or the
  Sandbox API and no host/repository/Docker mount. Same-origin page JavaScript
  can reach W2 APIs only through Sandbox Web's existing reverse proxy.
- Agent/model compromise cannot call management or business APIs and cannot
  manufacture selectors or executable browser code.
- Ephemeral references make stale or forged model actions fail before browser
  execution, at the cost of requiring a fresh observation after every action.
- Per-task browser processes cost more startup time and memory than a shared
  browser but make cleanup and isolation explicit for this small fixed set.
- A host-side acceptance caller remains trusted for Reset/Seed, human-brief
  rendering, and Grader calls. It is not an Agent tool or production control
  plane.
- The human-readable supplied-value projection is deterministic and derived
  from immutable W3 inputs; it does not change W3 task contracts or leak
  Reporting results. Only tasks 001-005 are eligible in W4.
- Without separately authorized real-model calls, W4 can prove code, schema,
  fake-model, and Compose behaviour but cannot claim five-task Agent success.
- The authorized real profile introduces narrowly bounded provider egress at
  the application layer; it does not add a generic model gateway, provider URL,
  Sandbox API network, or persistent production configuration.

## Rejected alternatives

- **Embed Playwright in `sandbox_api`:** mixes browser compromise and resource
  lifecycle with the database-backed synthetic application.
- **Put Agent and Browser in one process:** removes the typed network boundary
  and gives model orchestration direct access to Playwright objects.
- **Give Agent the Arena API/database:** violates the model/tool boundary and
  lets task state or grade influence action selection directly.
- **Accept selectors or Playwright snippets:** creates an arbitrary browser
  execution interface and defeats ephemeral references.
- **Share one Browser across tasks:** weakens cleanup/isolation and introduces
  cross-task state.
- **Add screenshots or visual fallbacks:** belongs to W5/W6.
- **Add planner, verifier, retry recovery, or checkpoints:** belongs to W7/W8.
- **Modify W3 instructions/checksums to add identifiers:** breaks the frozen W3
  dataset; deterministic human-facing rendering preserves those inputs.
