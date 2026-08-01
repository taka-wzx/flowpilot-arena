"""Closed W11 trusted server-side action classification."""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError

from flowpilot_control_api.schemas import (
    ApprovalRole,
    RiskLevel,
    SafeCode,
    StepReference,
    StrictModel,
    TaskReference,
    UserId,
    stable_hash,
)

EmployeeReference = Annotated[int, Field(ge=1, le=999_999)]
OpaqueReference = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_.:-]{2,79}$", max_length=80)
]


class RiskSchemaRejected(RuntimeError):
    pass


class InspectEmployeeParameters(StrictModel):
    schema_version: Literal["w11-inspect-employee-parameters/1.0"] = (
        "w11-inspect-employee-parameters/1.0"
    )
    employee_id: EmployeeReference


class TaskParameters(StrictModel):
    schema_version: Literal["w11-task-parameters/1.0"] = "w11-task-parameters/1.0"
    task_reference: TaskReference


class CreateTicketParameters(StrictModel):
    schema_version: Literal["w11-create-ticket-parameters/1.0"] = "w11-create-ticket-parameters/1.0"
    employee_id: EmployeeReference
    ticket_code: SafeCode


class CreateAccountParameters(StrictModel):
    schema_version: Literal["w11-create-account-parameters/1.0"] = (
        "w11-create-account-parameters/1.0"
    )
    target_user_id: UserId
    account_code: SafeCode


class AssignAssetParameters(StrictModel):
    schema_version: Literal["w11-assign-asset-parameters/1.0"] = "w11-assign-asset-parameters/1.0"
    employee_id: EmployeeReference
    asset_code: SafeCode


class CreateMailboxParameters(StrictModel):
    schema_version: Literal["w11-create-mailbox-parameters/1.0"] = (
        "w11-create-mailbox-parameters/1.0"
    )
    employee_id: EmployeeReference
    mailbox_code: SafeCode


class TransferEmployeeParameters(StrictModel):
    schema_version: Literal["w11-transfer-employee-parameters/1.0"] = (
        "w11-transfer-employee-parameters/1.0"
    )
    employee_id: EmployeeReference
    destination_code: SafeCode


class EmployeeMutationParameters(StrictModel):
    schema_version: Literal["w11-employee-mutation-parameters/1.0"] = (
        "w11-employee-mutation-parameters/1.0"
    )
    employee_id: EmployeeReference


class GrantAdminParameters(StrictModel):
    schema_version: Literal["w11-grant-admin-parameters/1.0"] = "w11-grant-admin-parameters/1.0"
    target_user_id: UserId
    permission_code: SafeCode


class TransferOwnershipParameters(StrictModel):
    schema_version: Literal["w11-transfer-ownership-parameters/1.0"] = (
        "w11-transfer-ownership-parameters/1.0"
    )
    source_reference: OpaqueReference
    target_user_id: UserId


class ForbiddenParameters(StrictModel):
    schema_version: Literal["w11-forbidden-parameters/1.0"] = "w11-forbidden-parameters/1.0"


ParameterModel = type[StrictModel]

ACTION_PARAMETER_MODELS: dict[str, ParameterModel] = {
    "inspect_employee": InspectEmployeeParameters,
    "inspect_task": TaskParameters,
    "create_draft": TaskParameters,
    "generate_plan": TaskParameters,
    "create_ticket": CreateTicketParameters,
    "create_account": CreateAccountParameters,
    "assign_asset": AssignAssetParameters,
    "create_mailbox": CreateMailboxParameters,
    "transfer_employee": TransferEmployeeParameters,
    "close_ticket": EmployeeMutationParameters,
    "release_asset": EmployeeMutationParameters,
    "grant_admin_privilege": GrantAdminParameters,
    "revoke_account": EmployeeMutationParameters,
    "disable_employee": EmployeeMutationParameters,
    "disable_mailbox": EmployeeMutationParameters,
    "transfer_file_ownership": TransferOwnershipParameters,
    "physical_delete": ForbiddenParameters,
    "bypass_approval": ForbiddenParameters,
    "modify_audit": ForbiddenParameters,
    "cross_tenant_operation": ForbiddenParameters,
    "arbitrary_code_execution": ForbiddenParameters,
}

ACTION_RISKS: dict[str, RiskLevel] = {
    "inspect_employee": RiskLevel.L0,
    "inspect_task": RiskLevel.L0,
    "create_draft": RiskLevel.L1,
    "generate_plan": RiskLevel.L1,
    "create_ticket": RiskLevel.L2,
    "create_account": RiskLevel.L2,
    "assign_asset": RiskLevel.L2,
    "create_mailbox": RiskLevel.L2,
    "transfer_employee": RiskLevel.L2,
    "close_ticket": RiskLevel.L2,
    "release_asset": RiskLevel.L2,
    "grant_admin_privilege": RiskLevel.L3,
    "revoke_account": RiskLevel.L3,
    "disable_employee": RiskLevel.L3,
    "disable_mailbox": RiskLevel.L3,
    "transfer_file_ownership": RiskLevel.L3,
    "physical_delete": RiskLevel.L4,
    "bypass_approval": RiskLevel.L4,
    "modify_audit": RiskLevel.L4,
    "cross_tenant_operation": RiskLevel.L4,
    "arbitrary_code_execution": RiskLevel.L4,
}


@dataclass(frozen=True, slots=True)
class RiskFacts:
    target_is_organization_administrator: bool = False


@dataclass(frozen=True, slots=True)
class RiskEvaluation:
    action_type: str
    risk_level: RiskLevel
    parameter_hash: str
    validated_parameters: dict[str, object]
    required_roles: tuple[ApprovalRole, ...]
    known_action: bool


def required_roles(level: RiskLevel) -> tuple[ApprovalRole, ...]:
    if level == RiskLevel.L2:
        return (ApprovalRole.MANAGER,)
    if level == RiskLevel.L3:
        return (ApprovalRole.MANAGER, ApprovalRole.SECURITY)
    return ()


def evaluate_risk(
    action_type: str,
    parameters: dict[str, object],
    facts: RiskFacts | None = None,
) -> RiskEvaluation:
    facts = facts or RiskFacts()
    model_type = ACTION_PARAMETER_MODELS.get(action_type)
    if model_type is None:
        binding: dict[str, object] = {
            "schema_version": "w11-action-binding/1.0",
            "action_type": action_type,
            "parameters": parameters,
        }
        return RiskEvaluation(
            action_type=action_type,
            risk_level=RiskLevel.L4,
            parameter_hash=stable_hash(binding),
            validated_parameters=dict(parameters),
            required_roles=(),
            known_action=False,
        )
    try:
        validated = model_type.model_validate(parameters).model_dump(mode="json")
    except ValidationError as exc:
        raise RiskSchemaRejected("known action parameters were rejected") from exc
    level = ACTION_RISKS[action_type]
    if (
        action_type == "create_account"
        and facts.target_is_organization_administrator
        and level < RiskLevel.L3
    ):
        level = RiskLevel.L3
    binding = {
        "schema_version": "w11-action-binding/1.0",
        "action_type": action_type,
        "parameters": validated,
    }
    return RiskEvaluation(
        action_type=action_type,
        risk_level=level,
        parameter_hash=stable_hash(binding),
        validated_parameters=validated,
        required_roles=required_roles(level),
        known_action=True,
    )


def recovery_binding_hash(
    *,
    task_id: TaskReference,
    step_id: StepReference,
    evaluation: RiskEvaluation,
) -> str:
    fields: dict[str, object] = {
        "schema_version": "w11-recovery-approval-binding/1.0",
        "task_id": task_id,
        "step_id": step_id,
        "action_type": evaluation.action_type,
        "parameter_hash": evaluation.parameter_hash,
        "risk_level": evaluation.risk_level,
    }
    return stable_hash(fields)
