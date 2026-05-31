from __future__ import annotations

from app.auth.permissions import PERMISSION_MATRIX, resolve_permissions


class PermissionsValidationService:
    def get_matrix(self) -> dict:
        roles = {}
        for role, permissions in PERMISSION_MATRIX.items():
            roles[role] = {
                "permissions": sorted(permissions),
                "count": len(permissions),
            }
        return {
            "roles": roles,
            "role_count": len(roles),
        }

    def validate_role_access(
        self,
        *,
        role: str,
        required_permission: str,
    ) -> dict:
        permissions = resolve_permissions(role)
        granted = required_permission in permissions
        return {
            "role": role.upper(),
            "required_permission": required_permission,
            "granted": granted,
            "permissions": sorted(permissions),
        }

    def validate_matrix_integrity(self) -> dict:
        issues: list[str] = []
        if "ADMIN" not in PERMISSION_MATRIX:
            issues.append("MISSING_ADMIN_ROLE")
        admin_perms = PERMISSION_MATRIX.get("ADMIN", set())
        if "projects:write" not in admin_perms:
            issues.append("ADMIN_MISSING_WRITE")

        viewer_perms = PERMISSION_MATRIX.get("VIEWER", set())
        if "users:write" in viewer_perms:
            issues.append("VIEWER_HAS_WRITE_ACCESS")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "roles_checked": len(PERMISSION_MATRIX),
        }
