"""Strong ETag and If-Match contract tests."""

import pytest

from flowpilot_control_api.etag import (
    PreconditionFailed,
    PreconditionRequired,
    expected_version,
    strong_etag,
)
from flowpilot_control_api.schemas import ResourceKind

ORG = "org_syn_alpha_0001"
RESOURCE = "mem_runtime_resource_0001"


def test_strong_etag_round_trip_is_stable_and_value_free() -> None:
    value = strong_etag(ResourceKind.MEMORY, ORG, RESOURCE, 7)

    assert value.startswith('"w10-memory-')
    assert ORG not in value
    assert RESOURCE not in value
    assert (
        expected_version(
            value,
            kind=ResourceKind.MEMORY,
            organization_id=ORG,
            resource_id=RESOURCE,
        )
        == 7
    )


def test_missing_malformed_weak_and_cross_resource_are_rejected() -> None:
    with pytest.raises(PreconditionRequired):
        expected_version(
            None,
            kind=ResourceKind.MEMORY,
            organization_id=ORG,
            resource_id=RESOURCE,
        )
    invalid = (
        "malformed",
        "*",
        'W/"w10-memory-000000000000000000000000-v1"',
        '"w10-memory-000000000000000000000000-v1", "other"',
        strong_etag(ResourceKind.USER, ORG, RESOURCE, 1),
        strong_etag(ResourceKind.MEMORY, ORG, "mem_other_resource_0001", 1),
        strong_etag(ResourceKind.MEMORY, "org_syn_beta_0001", RESOURCE, 1),
    )
    for value in invalid:
        with pytest.raises(PreconditionFailed):
            expected_version(
                value,
                kind=ResourceKind.MEMORY,
                organization_id=ORG,
                resource_id=RESOURCE,
            )
