import json

import pytest
from pydantic import ValidationError

from flowpilot_sandbox_api.arena.catalog import TaskCatalog, get_catalog, parse_task_document

EXPECTED_CATALOG_CHECKSUM = "e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9"


def test_catalog_contains_ten_strict_checksums_and_frozen_splits() -> None:
    catalog = get_catalog()
    assert len(catalog.specs) == 10
    assert catalog.canonical_checksum == EXPECTED_CATALOG_CHECKSUM
    assert [spec.split for spec in catalog.specs] == [
        *("development" for _ in range(6)),
        "validation",
        "validation",
        "reporting",
        "reporting",
    ]
    for spec in catalog.specs:
        assert len(spec.canonical_checksum) == 64
        assert spec.fixture.fixture_version == "w3-fixture-v1"
        assert all(
            employee.work_email.endswith(".invalid") for employee in spec.initial_state.employees
        )
        assert spec.expected_final_state.asset.asset_tag.startswith("SYN-W3-")


def test_unknown_fields_and_non_synthetic_emails_are_rejected() -> None:
    payload = get_catalog().specs[0].model_dump(mode="json")
    payload["selector"] = "#forbidden"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        parse_task_document(json.dumps(payload))

    payload = get_catalog().specs[0].model_dump(mode="json")
    payload["initial_state"]["employees"][0]["work_email"] = "nova@example.com"
    with pytest.raises(ValidationError, match=".invalid"):
        parse_task_document(json.dumps(payload))


def test_invalid_references_predicates_and_checksum_are_rejected() -> None:
    payload = get_catalog().specs[0].model_dump(mode="json")
    payload["fixture"]["fixture_id"] = "w3-joiner-002-fixture"
    with pytest.raises(ValidationError, match="fixture_id"):
        parse_task_document(json.dumps(payload))

    payload = get_catalog().specs[0].model_dump(mode="json")
    payload["grader_predicates"][0]["predicate_id"] = payload["grader_predicates"][1][
        "predicate_id"
    ]
    with pytest.raises(ValidationError, match="predicate IDs"):
        parse_task_document(json.dumps(payload))

    payload = get_catalog().specs[0].model_dump(mode="json")
    payload["title"] = "Changed without updating the checksum"
    with pytest.raises(ValueError, match="Canonical checksum mismatch"):
        parse_task_document(json.dumps(payload))


def test_duplicate_and_missing_task_ids_are_rejected() -> None:
    first = get_catalog().specs[0]
    with pytest.raises(ValueError, match="duplicate task IDs"):
        TaskCatalog([first] * 10)
    with pytest.raises(ValueError, match="exactly"):
        TaskCatalog(get_catalog().specs[:-1])
