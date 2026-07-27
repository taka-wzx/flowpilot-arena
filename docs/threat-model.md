# W5 threat model — Vision Agent Foundation

## Scope and assets

W5 protects released W1-W4 source and locks; immutable W3 Task Specs/checksums;
task-owned synthetic state and deterministic grades; Browser Worker integrity;
bounded in-memory visual observations; opaque screenshot/grounding references;
typed visual actions; and Vision Agent budget/termination integrity.

The only new sensitive runtime asset is one current synthetic Sandbox viewport
JPEG. It is untrusted page content, not a trusted instruction. W5 stores no
image, OCR text, screenshot trace, image URL/path, real identity, enterprise
system data, or model credential. Default Compose/CI has no VLM/OCR network
call.

## Trust boundaries

~~~mermaid
flowchart LR
    Model["Untrusted fake vision output<br/>and untrusted visual/OCR inference"] --> Vision["Strict Vision Agent loop"]
    Vision --> Worker["Typed visual Browser Worker API"]
    Worker --> Page["Untrusted Sandbox page viewport"]
    Page --> Web["sandbox_web same origin"]
    Web --> API["W2 business API"]
    Caller["Trusted acceptance caller"] --> Arena["W3 Reset/Seed + Grader"]
    Caller --> Vision
    Arena --> DB["Synthetic PostgreSQL"]
    API --> DB
~~~

The screenshot does not cross a storage boundary: it is returned only in the
current Worker response and used by the current Vision Agent model call. The
Worker and Vision Agent are separate containers. Docker internal networks
enforce that the Worker lacks API/DB routes and Vision Agent lacks all Sandbox
routes. The caller is trusted test orchestration, not a model tool.

## Threats and W5 controls

| Threat | W5 impact | W5 control | Remaining limitation |
|---|---|---|---|
| Host desktop/browser UI capture | Personal or host data reaches model | Playwright viewport screenshot only; fresh headless context; no raw screenshot option/endpoint | Browser implementation is trusted; this is not a formal desktop-isolation proof |
| External/cross-origin capture | Arbitrary web content reaches model | Exact Sandbox origin/path policy, request interception, final URL validation, internal network, no iframe/image URL input | Malicious-page evaluation waits for W14 |
| Image persistence/leak | Screenshot or OCR retained in repository/log/store | In-memory current response/context only; no file/storage/trace/schema field for paths; generic errors/history | Process memory is not a forensic zeroization guarantee |
| Prompt injection in image/OCR | Page image controls Agent policy | Image/OCR tagged untrusted; fixed system policy; strict action schema; no tool promotion | W14 measures adversarial effectiveness |
| Arbitrary coordinate click | Model clicks unknown pixel/element | Coordinates output-only metadata; model returns opaque current grounding ref; Worker maps/validates internal locator | Current DOM may race after observation and fail safely |
| Forged/stale visual reference | Wrong-element action | Fresh screenshot/observation nonce and in-memory grounding map; reference/session/observation match before action | No recovery path is added in W5 |
| DOM fallback in Vision-only baseline | Misleading modality claim | Visual schemas/context omit DOM, AX, title, URL, element name/role/text, selector, and element_ref | Task brief still contains allowed immutable human instructions |
| Fake fixture/value lookup | Scripted fake silently receives task facts or grade logic | `complete_joiner` parses only the fixed supplied-values suffix supplied by the trusted caller; it has no fixture map, task-ID lookup, Task Spec, expected-state, or Grader input | This is still deterministic test policy, not visual understanding |
| Form/credential leak in image/action | Sensitive data exposure | Synthetic Sandbox only; released fill filters; no image persistence; no result message with names/OCR | Screenshot can show synthetic form values during active task |
| Resource exhaustion | Excess CPU/RAM/bytes/model cost | Fixed JPEG/viewport/quality, image byte/count/time caps, pids/shm/tmpfs limits, Agent image/call/token/cost/time/repetition/progress caps | Load/concurrency validation is W12 |
| Model credential/provider abuse | Unapproved spend or egress | W5 has no provider adapter/key/egress; fake only in CI/Compose | A later authorized provider needs a separate threat update |
| Direct Agent access to task facts/grade | Tuning/bypass | No DB/Arena/business/Grader client or network; caller owns management sequence | Caller remains trusted local test code |
| Model self-reported success | False pass | Result has no pass/score; finish is ungraded; unchanged W3 Grader is independent | Five Development tasks do not establish general reliability |
| Cross-task visual state | Prior screenshot/cookie/form leaks | Fresh Browser/Context/Page per task; current-only visual data; terminal cleanup | Crash recovery is W8, not W5 |
| Browser container breakout | Host compromise | Non-root, read-only root, no mounts/socket, dropped capabilities, no-new-privileges, internal networks | Development hardening, not a formal sandbox proof |
| Supply-chain drift | Reproducibility/compromise | Existing pinned Python/uv/Playwright locks, CI, Gitleaks, explicit image evidence | SBOM/signing waits for later release work |

## Deterministic data and control rules

- W3 task facts/checksums remain fixed. W5 never writes images, OCR, model
  outputs, visual references, or results into Task Specs.
- Session/observation/screenshot/grounding IDs use OS entropy only as runtime
  isolation tokens and never as task facts or model inputs.
- Wall-time budgets use monotonic time. Capture attempts count even on failure.
  Fake model responses are deterministic and have zero external cost.
- The fake completion scenario may retain parsed supplied values only in its
  task-local model instance. It does not persist them, use page text/image
  instructions as policy, or accept a caller-provided action sequence.
- Browser navigation reaches only Sandbox Web. Same-origin business writes are
  caused only by Worker-validated typed UI actions, never direct Agent/Worker
  business API calls.
- Reset/Seed and grading stay outside both Worker and Vision Agent. Grade reads
  database facts only and ignores model/Agent claims.

## Explicitly deferred threats

DOM/Vision routing and modality policy are W6; planner/verifier risks W7;
checkpoint/recovery/fault injection W8; context/retrieval W9; identity/RBAC
W10; approval/audit W11; production worker/monitoring/tracing/load W12+;
malicious-page evaluation W14; and external Reporting evaluation W15.

## Security operating rules

- Never expose local unauthenticated W1-W4 ports publicly.
- Never add a default network, host mount, Docker socket, database/API secret,
  external origin, generic image target, raw pixel action, selector, or
  arbitrary execution parameter to Worker or Vision Agent.
- Never commit images, OCR text, form contents, DOM trace, identity, account,
  credential, token, endpoint, or machine path.
- Call a real visual model only after exact disclosure and separate explicit
  approval; W4 authorization never carries forward.
- Keep W3 Validation/Reporting facts/checksums frozen and stop before W6.
