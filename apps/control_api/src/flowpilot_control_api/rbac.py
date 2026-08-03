"""Closed, default-deny W10 RBAC."""

from types import MappingProxyType

from flowpilot_control_api.schemas import Permission, Role


class AuthorizationDenied(RuntimeError):
    pass


_ROLE_PERMISSIONS = MappingProxyType(
    {
        Role.ORGANIZATION_ADMIN: frozenset(
            {
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
                Permission.APPROVAL_AUTHORITY_READ,
                Permission.APPROVAL_AUTHORITY_MANAGE,
                Permission.APPROVAL_REQUEST_READ,
                Permission.APPROVAL_REQUEST_CREATE,
                Permission.APPROVAL_REQUEST_DECIDE,
                Permission.APPROVAL_REQUEST_CANCEL,
                Permission.APPROVAL_GRANT_CLAIM,
                Permission.AUDIT_READ,
                Permission.AUDIT_VERIFY,
                Permission.PRODUCTION_RUN_READ,
                Permission.PRODUCTION_RUN_SUBMIT,
                Permission.PRODUCTION_RUN_MUTATE,
                Permission.OBSERVABILITY_TRACE_READ,
            }
        ),
        Role.OPERATOR: frozenset(
            {
                Permission.ORGANIZATION_READ,
                Permission.USER_READ,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.MEMORY_RESET,
                Permission.CONTEXT_PROJECT,
                Permission.APPROVAL_REQUEST_READ,
                Permission.APPROVAL_REQUEST_CREATE,
                Permission.APPROVAL_REQUEST_DECIDE,
                Permission.APPROVAL_REQUEST_CANCEL,
                Permission.APPROVAL_GRANT_CLAIM,
                Permission.PRODUCTION_RUN_READ,
                Permission.PRODUCTION_RUN_SUBMIT,
                Permission.PRODUCTION_RUN_MUTATE,
                Permission.OBSERVABILITY_TRACE_READ,
            }
        ),
        Role.AUDITOR: frozenset(
            {
                Permission.ORGANIZATION_READ,
                Permission.USER_READ,
                Permission.MEMBERSHIP_READ,
                Permission.MEMORY_READ,
                Permission.CONTEXT_PROJECT,
                Permission.APPROVAL_REQUEST_READ,
                Permission.AUDIT_READ,
                Permission.AUDIT_VERIFY,
                Permission.PRODUCTION_RUN_READ,
                Permission.OBSERVABILITY_TRACE_READ,
            }
        ),
    }
)


def permissions_for_role(role: Role) -> tuple[Permission, ...]:
    permissions = _ROLE_PERMISSIONS.get(role)
    if permissions is None:
        raise AuthorizationDenied("unknown_role")
    return tuple(sorted(permissions, key=lambda item: item.value))


def require_permission(role: Role, permission: Permission) -> tuple[Permission, ...]:
    permissions = permissions_for_role(role)
    if permission not in permissions:
        raise AuthorizationDenied("permission_denied")
    return permissions
