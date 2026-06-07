import {
  normalizeRole,
} from "@/lib/auth/role";

export const PLATFORM_ADMIN_ROLE = "PLATFORM_ADMIN";
export const ORG_ADMIN_ROLE = "ADMIN";

export function isPlatformAdmin(
  role?: string | null
) {
  return normalizeRole(role) === PLATFORM_ADMIN_ROLE;
}

export function isOrgAdmin(
  role?: string | null
) {
  return normalizeRole(role) === ORG_ADMIN_ROLE;
}

export function isAdmin(
  role?: string | null
) {
  return isPlatformAdmin(role) || isOrgAdmin(role);
}

export function canManageUsers(
  role?: string | null
) {
  return isAdmin(role);
}

export function canManageOrganizations(
  role?: string | null
) {
  return isPlatformAdmin(role);
}

export function inviteableRoles(
  role?: string | null,
  options?: {
    hasClientAdmin?: boolean;
  }
) {
  if (isPlatformAdmin(role)) {
    const roles = [
      ORG_ADMIN_ROLE,
      "SUPERVISOR",
      "VIEWER",
    ] as const;

    if (options?.hasClientAdmin) {
      return roles.filter(
        (item) => item !== ORG_ADMIN_ROLE
      );
    }

    return roles;
  }

  if (isOrgAdmin(role)) {
    return [
      "SUPERVISOR",
      "VIEWER",
    ] as const;
  }

  return [] as const;
}

export function organizationHasClientAdmin(
  users: Array<{ role?: string | null }>
) {
  return users.some(
    (user) => normalizeRole(user.role) === ORG_ADMIN_ROLE
  );
}

const OPERATIONAL_ROLES = [
  PLATFORM_ADMIN_ROLE,
  ORG_ADMIN_ROLE,
  "SUPERVISOR",
  "MANAGER",
] as const;

const PROJECT_WRITE_ROLES = OPERATIONAL_ROLES;

export function isManager(
  role?: string | null
) {

  return OPERATIONAL_ROLES.includes(
    normalizeRole(role) as typeof OPERATIONAL_ROLES[number]
  );
}

export function canManageActions(
  role?: string | null
) {

  return OPERATIONAL_ROLES.includes(
    normalizeRole(role) as typeof OPERATIONAL_ROLES[number]
  );
}

export function canEscalateActions(
  role?: string | null
) {

  return OPERATIONAL_ROLES.includes(
    normalizeRole(role) as typeof OPERATIONAL_ROLES[number]
  );
}

export function canReviewAI(
  role?: string | null
) {

  return OPERATIONAL_ROLES.includes(
    normalizeRole(role) as typeof OPERATIONAL_ROLES[number]
  );
}

export function canEditProjects(
  role?: string | null
) {
  return PROJECT_WRITE_ROLES.includes(
    normalizeRole(role) as typeof PROJECT_WRITE_ROLES[number]
  );
}
