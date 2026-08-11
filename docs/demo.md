# Synthetic Local Demo

## What this demo is

W17 turns the existing Control Web into a unified Portfolio Demo Console. It
is a synthetic, local, deterministic presentation surface—not a marketing
landing page, a production deployment, or a source of product authority.

- Control Web: `http://127.0.0.1:5173`
- Sandbox Web: `http://127.0.0.1:5174`

The API resource name `production-runs` is historical and does not mean real
production. The demo contains no real provider, personal data, production
identity, production certification, or public deployment. The completed cloud
check was a temporary Aliyun ECS single-node K3s validation of Web images, not
an ACK managed-cluster deployment.

## Start and stop

Requirements are Python 3.13, uv, Node.js 24/npm, and Docker Compose.

~~~powershell
$env:RECOVERY_ENVELOPE_KEY = '<runtime-only local key>'
docker compose -f deploy/compose/compose.yaml config
docker compose -f deploy/compose/compose.yaml up --build -d
docker compose -f deploy/compose/compose.yaml ps
~~~

Open Control Web, sign in through the fixed local OIDC realm, and keep the
Sandbox Web isolated in its own tab. The console uses a normal link to the
Sandbox; it does not embed it or bypass browser isolation.

Stop and reset only the local stack:

~~~powershell
docker compose -f deploy/compose/compose.yaml down -v --remove-orphans
Remove-Item Env:RECOVERY_ENVELOPE_KEY
~~~

The volume cleanup above is a local reset; it does not authorize product or
cloud deletion.

## Five-minute console walkthrough

1. Confirm the `SYNTHETIC LOCAL DEMO` badge.
2. In Overview, identify the current opaque user, organization, business role,
   approval authority, active/terminal run counts, pending approvals, and audit
   state.
3. Create one fixed Joiner, Mover, or Leaver task. The UI supplies the existing
   closed schema, current organization, `generate_plan` action, synthetic task
   reference, and an in-memory idempotency key. There is no arbitrary input.
4. Filter Synthetic Runs by all, active, or terminal status. Select a row using
   keyboard or pointer input.
5. Review Run Detail and the observe → plan → execute → recover → verify
   timeline. Missing phases say `Not observed`; they are not fabricated.
6. Expand bounded trace and replay. Only phase, status, reason, failure category,
   ordinal/sequence, and time are presented. Trace/span IDs, hashes, worker or
   lease data, raw attributes, browser payloads, secrets, and personal data are
   not rendered.
7. For a waiting high-risk run, use the existing approval decision surface.
   The client rereads the approval and sends its current strong ETag; a changed
   request reports stale state and requires reload.
8. Verify the audit chain if the current permission allows it.
9. Open Sandbox in a separate tab through the visible link.
10. In Result, confirm that Agent terminal status and independent grading are
    separate. `finished_ungraded` does not mean business success. This Control
    API surface has no independent verdict, so the UI says
    `Grader result unavailable from this surface`.

Polling uses a fixed five-second interval and stops after two minutes, on a
terminal run, page hiding, unmount, or request failure. A stale message and
manual refresh are provided instead of indefinite background traffic.

## Deterministic evidence runner

The stdlib-only local runner remains
[tests/integration/w16_demo.py](../tests/integration/w16_demo.py). It emits a
redacted event sequence with opaque references and no page, DOM, screenshot,
model, tool, token, cookie, nonce, DSN, machine path, or personal data. Run:

~~~powershell
python tests/integration/w16_demo_smoke.py
~~~

The runner covers the same evidence story at protocol level: observe, typed
plan, Joiner/Mover/Leaver, contradiction follow-up, DOM-to-Vision fallback,
high-risk approval, recovery, independent Verifier/database-fact Grader, and
opaque trace/replay. Its output is evidence-shaped local data, not product
authority or a claim about real model quality, SLO, ROI, significance, or
security certification.

## Media status

A GIF/video is accepted only when captured from the deterministic runner or a
real local Compose run and reviewed for cookie, bearer, nonce, DSN, machine
path, personal-data, secret, and debug-output redaction. No recording utility
is installed in this environment. Media therefore remains
`unavailable/recording-tool-not-installed`; this page is the static fallback.
No AI-generated image or fabricated screenshot is presented as product output.
