# W7 JML synthetic catalog, licence, split, and checksum freeze

## Data statement

The W7 JML catalog is original synthetic FlowPilot test data licensed under
Apache-2.0. It contains no imported benchmark content, real person, real
mailbox, real account, credential, endpoint, or business record. Generated
names explicitly use synthetic labels; emails end in `.invalid`; asset tags
start `SYN-W7-`.

## Versioned artifacts

- Catalog schema: `w7-jml-catalog/1.0`
- Template schema: `w7-jml-template/1.0`
- Instance schema: `w7-jml-instance/1.0`
- Fixture version: `w7-jml-fixture/1.0`
- Variant generator: `w7-jml-variant-generator/1.0`
- Grader schema: `w7-jml-grade/1.0`
- Source: `FlowPilot W7 original synthetic fixture`
- Licence: `Apache-2.0`

The source JSON freezes 30 templates. The deterministic generator creates
exactly variants `v1`, `v2`, and `v3` for each template, for 90 instances.

## Frozen distribution

| Split | Joiner | Mover | Leaver | Total |
|---|---:|---:|---:|---:|
| Development | 8 | 4 | 6 | 18 |
| Validation | 2 | 2 | 2 | 6 |
| Reporting | 2 | 2 | 2 | 6 |
| Total | 12 | 8 | 10 | 30 |

Splits apply to templates, never random instances. Validation is not used for
repeated tuning. Reporting is generated, loaded, schema/checksum validated, and
frozen in W7; no Reporting Agent or Grader result is run or inspected before
W15.

## Canonicalization

Canonical JSON uses UTF-8, sorted keys, no insignificant whitespace, and
Unicode characters unescaped. The catalog checksum excludes only its declared
`catalog_checksum`. Each instance checksum excludes only its declared
`canonical_checksum`. Split and Reporting manifests contain sorted IDs and
checksums and use the same canonical serialization.

The packaged catalog gate currently freezes:

- catalog checksum:
  `62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`;
- split manifest checksum:
  `1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`;
- Reporting manifest checksum:
  `c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.

All 90 generated instance checksums are distinct and deterministically
reproduced by two independent catalog loads. The exact sorted 90-entry manifest
is the generated `CatalogEntry` sequence; it is not duplicated manually here.

## Runtime disclosure boundary

Trusted acceptance orchestration may load a task, Reset/Seed it, render the
human brief and strict supplied values, invoke Planning Agent, and independently
grade afterward. Planning Agent receives no Task Spec, expected state, fixture
map, predicate, canonical checksum, database fact, or Reporting result.
