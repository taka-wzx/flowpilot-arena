# Deterministic Demo

## Source and status

The source is the stdlib-only local runner at
[tests/integration/w16_demo.py](../tests/integration/w16_demo.py). It emits a
redacted event sequence with opaque references and no page, DOM, screenshot,
model, tool, token, cookie, DSN, machine path, or personal data. Run it with:

~~~powershell
python tests/integration/w16_demo_smoke.py
~~~

The runner covers:

1. observe and typed plan;
2. Joiner/Mover/Leaver synthetic story and contradiction follow-up;
3. cross-system planning;
4. DOM-to-Vision fallback;
5. high-risk approval gate;
6. Worker restart and recovery;
7. independent Verifier and database-fact Grader;
8. opaque trace/replay.

The output is an evidence-shaped local trace, not product authority. The Agent
remains finished_ungraded; only the independent Grader decides success.

## Media

A GIF/video is accepted only when captured from the command above or a real local
Compose deterministic run, then reviewed for redaction and licence/source
closure. No recording utility is installed in this environment. Therefore the
W16 media status is unavailable/recording-tool-not-installed, with this page
as the static fallback. No AI-generated image or fabricated screenshot is
submitted.

Suggested subtitle track for a later authorized recording:

~~~text
00:00 observe synthetic request
00:15 plan typed cross-system steps
00:30 follow up on contradiction
00:45 switch DOM to Vision
01:00 request high-risk approval
01:15 worker restart and deterministic recovery
01:30 verify with independent Grader
01:45 inspect opaque trace/replay
~~~

No cookie, Bearer, nonce, DSN, machine path, personal data, secret, or debug
console may appear in future media.
