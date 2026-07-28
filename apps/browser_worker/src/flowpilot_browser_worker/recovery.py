import re
from urllib.parse import urlsplit

from flowpilot_browser_worker.schemas import RecoveryIdempotencyBinding, RecoveryReceiptResult

_MUTATIONS: dict[str, tuple[str, re.Pattern[str]]] = {
    "create_ticket": ("POST", re.compile(r"^/api/itsm/tickets$")),
    "create_account": ("POST", re.compile(r"^/api/iam/accounts$")),
    "assign_asset": ("POST", re.compile(r"^/api/assets/devices$")),
    "create_mailbox": ("POST", re.compile(r"^/api/mail/mailboxes$")),
    "transfer_employee": ("PATCH", re.compile(r"^/api/hris/employees/[1-9][0-9]*/transfer$")),
    "disable_employee": ("PATCH", re.compile(r"^/api/hris/employees/[1-9][0-9]*/disable$")),
    "close_ticket": ("PATCH", re.compile(r"^/api/itsm/employees/[1-9][0-9]*/close$")),
    "revoke_account": ("PATCH", re.compile(r"^/api/iam/employees/[1-9][0-9]*/revoke$")),
    "release_asset": ("PATCH", re.compile(r"^/api/assets/employees/[1-9][0-9]*/release$")),
    "disable_mailbox": ("PATCH", re.compile(r"^/api/mail/employees/[1-9][0-9]*/disable$")),
}


def mutation_matches(operation: str, method: str, url: str) -> bool:
    contract = _MUTATIONS.get(operation)
    if contract is None:
        return False
    expected_method, path_pattern = contract
    return (
        method.upper() == expected_method and path_pattern.fullmatch(urlsplit(url).path) is not None
    )


def fixed_headers(binding: RecoveryIdempotencyBinding) -> dict[str, str]:
    return {
        "X-FlowPilot-W8-Task-Id": binding.task_id,
        "X-FlowPilot-W8-Idempotency-Key": binding.idempotency_key,
        "X-FlowPilot-W8-Request-Hash": binding.request_hash,
        "X-FlowPilot-W8-Plan-Revision": str(binding.plan_revision),
        "X-FlowPilot-W8-Step-Id": binding.step_id,
        "X-FlowPilot-W8-Operation": binding.operation,
    }


def parse_receipt(status: int, headers: dict[str, str]) -> RecoveryReceiptResult:
    state = headers.get("x-flowpilot-w8-receipt-state")
    result_hash = headers.get("x-flowpilot-w8-result-hash")
    if status == 409:
        return RecoveryReceiptResult(state="mismatch")
    if state not in {"created", "replayed"} or result_hash is None:
        raise ValueError("fixed mutation response omitted a valid receipt result")
    if state == "created":
        return RecoveryReceiptResult(state="created", result_hash=result_hash)
    return RecoveryReceiptResult(state="replayed", result_hash=result_hash)
