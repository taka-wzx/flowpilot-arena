# Model card — W16 local Demo

## Intended use

Describe the deterministic synthetic wiring and its reproducibility checks. This
is not a model-quality evaluation or a production certification.

## Current provider

The published local Demo uses deterministic-fake-provider/1.0. It emits closed
synthetic observations for tests only. Real provider, model, OCR, VLM, embedding,
billing, and egress calls are zero.

## Data

Only versioned synthetic JML Arena references and opaque event codes are used.
No real user, approver, enterprise page, screenshot, credential, or personal
data is included. WorkArena is unavailable/local_assets_absent.

## Limitations

The W15 frozen three-seed matrix is synthetic and must not be described as real
model quality, real cost, production SLO, ROI, statistical significance, or
security certification. The W16 demo trace validates wiring, redaction, and
replay shape only. The media recording tool is unavailable, so no GIF/video is
claimed.

## Reproduction

~~~powershell
python tests/integration/w16_demo_smoke.py
~~~

The independent Sandbox database-fact Grader remains the only business-success
authority, and the Agent terminal state remains finished_ungraded.
