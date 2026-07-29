from collections import Counter

from flowpilot_sandbox_api.arena.catalog import get_catalog as get_w3_catalog
from flowpilot_sandbox_api.arena.jml.catalog import JmlCatalog, get_catalog


def test_w7_catalog_freezes_30_templates_and_90_instances() -> None:
    catalog = get_catalog()
    summary = catalog.summary()
    assert len(catalog.templates) == 30
    assert len(catalog.instances) == 90
    assert Counter(item.process for item in catalog.templates) == {
        "joiner": 12,
        "mover": 8,
        "leaver": 10,
    }
    assert Counter(item.split for item in catalog.templates) == {
        "development": 18,
        "validation": 6,
        "reporting": 6,
    }
    assert len({item.task_id for item in catalog.instances}) == 90
    assert len({item.canonical_checksum for item in catalog.instances}) == 90
    assert (
        summary.catalog_checksum
        == "62737eb196ba1716cace8a3b286fd31fc3d4834c5f0b6660729c4b9261fe8f8f"
    )
    assert (
        summary.split_manifest_checksum
        == "1d4b09a00c69491cab02b594454a031112d86b771aba1b47dfa76acb86c164ee"
    )
    assert (
        summary.reporting_manifest_checksum
        == "c05bdf4fdc15344f93b88a403ceb4ae0e576270f50fcebdac59b953064b4f2b6"
    )


def test_variant_generation_and_checksums_are_stable() -> None:
    first = JmlCatalog.from_package()
    second = JmlCatalog.from_package()
    assert tuple(item.model_dump_json() for item in first.instances) == tuple(
        item.model_dump_json() for item in second.instances
    )
    assert all(item.fixture_version == "w7-jml-fixture/1.0" for item in first.instances)
    assert all(item.generator_version == "w7-jml-variant-generator/1.0" for item in first.instances)
    assert all(".invalid" in item.expected_state.target.work_email for item in first.instances)
    assert all(
        item.expected_state.asset is not None
        and item.expected_state.asset.asset_tag.startswith("SYN-W7-")
        for item in first.instances
    )


def test_w3_catalog_checksum_is_unchanged() -> None:
    assert (
        get_w3_catalog().canonical_checksum
        == "e48164caf7a3774965a16acc73c4b844661cfb8bf592aa9ba9c35a625d47abb9"
    )
