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
            }
        ),
        Role.AUDITOR: frozenset(
            {
                Permission.ORGANIZATION_READ,
                Permission.USER_READ,
                Permission.MEMBERSHIP_READ,
                Permission.MEMORY_READ,
                Permission.CONTEXT_PROJECT,
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
