# W10 identity, tenant, RBAC, and concurrency freeze

## OIDC realm freeze

- Keycloak image: `quay.io/keycloak/keycloak:26.3.2`
- Realm: `flowpilot`
- Issuer: `http://127.0.0.1:8080/realms/flowpilot`
- Internal JWKS: fixed `keycloak:8080` certs path for that realm
- Resource audience: `flowpilot-control-api`
- Browser client: `flowpilot-control-web`
- Algorithm/header/access-token type: `RS256` / `JWT` / `Bearer`
- Realm clients / roles / users: 1 / 3 / 6
- Realm import SHA-256:
  `38fb45f4c28ea3c5e2814cf6d413cdc036246ef81bed42cbd6b1bd529c77a5d8`

The import contains only fixed synthetic `.invalid` profiles and disposable
local test credentials. No real account, organization, subject, email,
password, token, authorization code, refresh token, session secret, or private
key is evidence data. Unit-test RSA keys exist only at runtime.

## Control Plane synthetic identity matrix

| Object | Count | State at seed |
|---|---:|---|
| organizations | 2 | active |
| users | 6 | active |
| OIDC identities | 6 | active |
| memberships | 6 | active |
| roles | 3 closed values | one each per organization |

Opaque IDs use `org_`, `usr_`, `idn_`, `mbr_`, and `mem_` prefixes. The
verified external key is issuer ID plus subject hash. Membership uniqueness is
organization plus user. Disable/tombstone transitions are retained; there is no
physical delete.

## RBAC freeze

| Permission | organization_admin | operator | auditor |
|---|---:|---:|---:|
| `organization.read` | yes | yes | yes |
| `organization.update` | yes | no | no |
| `user.read` | yes | yes | yes |
| `user.manage` | yes | no | no |
| `membership.read` | yes | no | yes |
| `membership.manage` | yes | no | no |
| `memory.read` | yes | yes | yes |
| `memory.write` | yes | yes | no |
| `memory.reset` | yes | yes | no |
| `context.project` | yes | yes | yes |

Unknown role/permission defaults to deny. No role has global or cross-
organization authority. A token role must exactly match the active database
membership but does not independently grant permission.

## Tenant and ETag freeze

Every tenant-owned record carries non-null organization ownership. Repository
get/list/count/create/update/disable/tombstone/reset and mutation predicates are
organization-qualified. Cross-organization and nonexistent resource responses
are identical and disclose no count, version, or ETag.

Mutable resources start at version 1. Strong ETags are:

~~~text
"w10-<closed-kind>-<24 lowercase hex owner/resource fingerprint>-v<version>"
~~~

The fingerprint is the first 24 hex characters of SHA-256 over closed resource
kind, organization ID, and resource ID. Missing If-Match is 428. Malformed,
weak, wildcard, cross-resource, cross-organization, and stale input is one 412.
Success increments exactly once; stale failure has no partial update, side
effect, tombstone, or version increase. Two concurrent writes using one old
version have exactly one winner.

## Preserved evaluation data

W3 remains 10 tasks with 6/2/2 split and checksum
`e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9`.
W7 remains 30 templates/90 instances, 12/8/10 processes and 18/6/6 split, with
catalog checksum
`62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f`,
split checksum
`1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee`,
and Reporting checksum
`c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6`.

W9 enterprise catalog remains 9 records with checksum
`4d63a24a57a54f9f7d94abe6b98d34453525dde13a6b100e336c8442c68bfb15`.
Its five ablation names, hashes, layer order, budgets, fake organization memory,
and Development Joiner/Mover/Leaver inputs remain unchanged. Reporting is not
executed before W15.
