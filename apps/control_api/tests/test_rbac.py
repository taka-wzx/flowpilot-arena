"""Closed W10 role/permission matrix tests."""

import pytest

from flowpilot_control_api.rbac import AuthorizationDenied, require_permission
from flowpilot_control_api.schemas import Permission, Role

EXPECTED = {
    Role.ORGANIZATION_ADMIN: {
        Permission.ORGANIZATION_READ,
        Permission.ORGANIZATION_UPDATE,
        Permission.USER_READ,
        Permission.USER_MANAGE,
        Permission.MEMBERSHIP_READ,
        Permission.MEMBERSHIP_MANAGE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_RESET,
        Permission.CONTEXT_PROJECT,
    },
    Role.OPERATOR: {
        Permission.ORGANIZATION_READ,
        Permission.USER_READ,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_RESET,
        Permission.CONTEXT_PROJECT,
    },
    Role.AUDITOR: {
        Permission.ORGANIZATION_READ,
        Permission.USER_READ,
        Permission.MEMBERSHIP_READ,
        Permission.MEMORY_READ,
        Permission.CONTEXT_PROJECT,
    },
}


@pytest.mark.parametrize("role", tuple(Role))
def test_complete_allow_and_deny_matrix(role: Role) -> None:
    for permission in Permission:
        if permission in EXPECTED[role]:
            assert permission in require_permission(role, permission)
        else:
            with pytest.raises(AuthorizationDenied, match="permission_denied"):
                require_permission(role, permission)


def test_permission_enum_has_no_wildcard_or_global_bypass() -> None:
    values = {permission.value for permission in Permission}

    assert all("*" not in value for value in values)
    assert all("global" not in value for value in values)
    assert all("imperson" not in value for value in values)
