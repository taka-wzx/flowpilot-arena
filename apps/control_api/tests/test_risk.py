"""Frozen W11 L0-L4 risk policy and canonical parameter binding."""

import pytest

from flowpilot_control_api.risk import (
    ACTION_PARAMETER_MODELS,
    ACTION_RISKS,
    RiskFacts,
    RiskSchemaRejected,
    evaluate_risk,
)
from flowpilot_control_api.schemas import ApprovalRole, RiskLevel


def _parameters(action: str) -> dict[str, object]:
    values: dict[str, dict[str, object]] = {
        "inspect_employee": {"employee_id": 41001},
        "inspect_task": {"task_reference": "task_syn_alpha_0001"},
        "create_draft": {"task_reference": "task_syn_alpha_0001"},
        "generate_plan": {"task_reference": "task_syn_alpha_0001"},
        "create_ticket": {"employee_id": 41001, "ticket_code": "ticket.standard"},
        "create_account": {
            "target_user_id": "usr_syn_alpha_operator_0001",
            "account_code": "account.standard",
        },
        "assign_asset": {"employee_id": 41001, "asset_code": "asset.standard"},
        "create_mailbox": {"employee_id": 41001, "mailbox_code": "mailbox.standard"},
        "transfer_employee": {"employee_id": 41001, "destination_code": "dept.standard"},
        "close_ticket": {"employee_id": 41001},
        "release_asset": {"employee_id": 41001},
        "grant_admin_privilege": {
            "target_user_id": "usr_syn_alpha_operator_0001",
            "permission_code": "permission.admin",
        },
        "revoke_account": {"employee_id": 41001},
        "disable_employee": {"employee_id": 41001},
        "disable_mailbox": {"employee_id": 41001},
        "transfer_file_ownership": {
            "source_reference": "file.synthetic.0001",
            "target_user_id": "usr_syn_alpha_operator_0001",
        },
        "physical_delete": {},
        "bypass_approval": {},
        "modify_audit": {},
        "cross_tenant_operation": {},
        "arbitrary_code_execution": {},
    }
    return values[action]


def test_every_frozen_action_has_one_strict_schema_and_risk() -> None:
    assert set(ACTION_PARAMETER_MODELS) == set(ACTION_RISKS)
    counts = {level: sum(value == level for value in ACTION_RISKS.values()) for level in RiskLevel}
    assert counts == {
        RiskLevel.L0: 2,
        RiskLevel.L1: 2,
        RiskLevel.L2: 7,
        RiskLevel.L3: 5,
        RiskLevel.L4: 5,
    }
    for action, expected in ACTION_RISKS.items():
        result = evaluate_risk(action, _parameters(action))
        assert result.risk_level == expected
        assert result.known_action
        if expected == RiskLevel.L2:
            assert result.required_roles == (ApprovalRole.MANAGER,)
        elif expected == RiskLevel.L3:
            assert result.required_roles == (ApprovalRole.MANAGER, ApprovalRole.SECURITY)


def test_unknown_action_is_l4_and_known_unknown_parameters_fail_closed() -> None:
    unknown = evaluate_risk("unknown_action", {"model_risk": "L0"})
    assert unknown.risk_level == RiskLevel.L4
    assert not unknown.known_action

    with pytest.raises(RiskSchemaRejected):
        evaluate_risk("assign_asset", {"employee_id": 41001, "asset_code": "asset", "risk": "L0"})
    with pytest.raises(RiskSchemaRejected):
        evaluate_risk("assign_asset", {"employee_id": 41001})


def test_parameter_hash_is_order_independent_value_sensitive_and_replay_stable() -> None:
    first = evaluate_risk("assign_asset", {"employee_id": 41001, "asset_code": "asset.standard"})
    reordered = evaluate_risk(
        "assign_asset", {"asset_code": "asset.standard", "employee_id": 41001}
    )
    changed = evaluate_risk("assign_asset", {"employee_id": 41001, "asset_code": "asset.changed"})

    assert first.parameter_hash == reordered.parameter_hash
    assert first.parameter_hash != changed.parameter_hash
    assert first == evaluate_risk(
        "assign_asset", {"employee_id": 41001, "asset_code": "asset.standard"}
    )


def test_current_database_fact_can_only_promote_create_account() -> None:
    parameters = {
        "target_user_id": "usr_syn_alpha_admin_0001",
        "account_code": "account.standard",
    }
    ordinary = evaluate_risk("create_account", parameters, RiskFacts(False))
    privileged = evaluate_risk("create_account", parameters, RiskFacts(True))

    assert ordinary.risk_level == RiskLevel.L2
    assert privileged.risk_level == RiskLevel.L3
    assert ordinary.parameter_hash == privileged.parameter_hash
