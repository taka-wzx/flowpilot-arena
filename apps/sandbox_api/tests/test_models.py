from sqlalchemy import Engine, inspect


def test_foundation_schema_contains_five_module_entities(db_engine: Engine) -> None:
    assert set(inspect(db_engine).get_table_names()) == {
        "asset_assignments",
        "employees",
        "human_baseline_records",
        "iam_accounts",
        "mailboxes",
        "onboarding_tickets",
    }


def test_every_downstream_entity_links_to_employee(db_engine: Engine) -> None:
    inspector = inspect(db_engine)
    for table in ("asset_assignments", "iam_accounts", "mailboxes", "onboarding_tickets"):
        foreign_keys = inspector.get_foreign_keys(table)
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "employees"


def test_w3_task_ownership_is_nullable_and_indexed(db_engine: Engine) -> None:
    inspector = inspect(db_engine)
    for table in (
        "asset_assignments",
        "employees",
        "iam_accounts",
        "mailboxes",
        "onboarding_tickets",
    ):
        columns = {column["name"]: column for column in inspector.get_columns(table)}
        assert columns["arena_task_id"]["nullable"] is True
        indexed_columns = {tuple(index["column_names"]) for index in inspector.get_indexes(table)}
        assert ("arena_task_id",) in indexed_columns
