/**
 * QC Spec 0.3 - Personas and permissions (mirrors app/schemas/qc_permissions.py).
 * See docs/qc-spec/qc-personas-permissions.md.
 */

import type { QualityIssueStatus } from "@/lib/quality-issues/types";

export const QC_PERSONAS = [
  "SUPERVISOR",
  "CONTRACTOR",
  "DEVELOPER",
  "ADMIN",
] as const;

export type QCPersona = (typeof QC_PERSONAS)[number];

export const QC_PERSONA_LABELS_HE: Record<QCPersona, string> = {
  SUPERVISOR: "מפקח",
  CONTRACTOR: "קבלן",
  DEVELOPER: "יזם",
  ADMIN: "מנהל",
};

export const QC_PERMISSIONS = [
  "quality_issues:read",
  "quality_issues:write",
  "quality_issues:remediate",
  "quality_issues:verify",
  "quality_portfolio:read",
  "field_reports:read",
  "field_reports:write",
  "field_reports:admin",
  "projects:read",
  "projects:write",
  "users:read",
  "users:write",
  "audit:read",
] as const;

export type QCPermission = (typeof QC_PERMISSIONS)[number];

const SYSTEM_ROLE_TO_QC_PERSONA: Record<string, QCPersona> = {
  SUPERVISOR: "SUPERVISOR",
  CONTRACTOR: "CONTRACTOR",
  DEVELOPER: "DEVELOPER",
  ADMIN: "ADMIN",
  PLATFORM_ADMIN: "ADMIN",
  MANAGER: "SUPERVISOR",
  VIEWER: "DEVELOPER",
  ANALYST: "DEVELOPER",
};

const QC_PERMISSION_MATRIX: Record<QCPersona, ReadonlySet<QCPermission>> = {
  SUPERVISOR: new Set([
    "quality_issues:read",
    "quality_issues:write",
    "quality_issues:verify",
    "quality_portfolio:read",
    "field_reports:read",
    "field_reports:write",
    "projects:read",
    "projects:write",
    "audit:read",
  ]),
  CONTRACTOR: new Set([
    "quality_issues:read",
    "quality_issues:remediate",
    "projects:read",
  ]),
  DEVELOPER: new Set([
    "quality_issues:read",
    "quality_portfolio:read",
    "field_reports:read",
    "projects:read",
  ]),
  ADMIN: new Set([
    "quality_issues:read",
    "quality_issues:write",
    "quality_issues:verify",
    "quality_portfolio:read",
    "field_reports:read",
    "field_reports:write",
    "field_reports:admin",
    "projects:read",
    "projects:write",
    "users:read",
    "users:write",
    "audit:read",
  ]),
};

const CONTRACTOR_VISIBLE_STATUSES: ReadonlySet<QualityIssueStatus> = new Set([
  "OPEN",
  "IN_REMEDIATION",
]);

const CONTRACTOR_ALLOWED_TRANSITIONS: ReadonlySet<string> = new Set([
  "IN_REMEDIATION->PENDING_VERIFICATION",
]);

const VALID_STATUS_TRANSITIONS: ReadonlySet<string> = new Set([
  "OPEN->IN_REMEDIATION",
  "OPEN->CLOSED",
  "IN_REMEDIATION->PENDING_VERIFICATION",
  "PENDING_VERIFICATION->CLOSED",
  "PENDING_VERIFICATION->OPEN",
  "CLOSED->REOPENED",
  "REOPENED->IN_REMEDIATION",
  "REOPENED->CLOSED",
]);

export function normalizeSystemRole(role?: string | null): string {
  return (role || "").trim().toUpperCase();
}

export function resolveQCPersona(role?: string | null): QCPersona | null {
  return SYSTEM_ROLE_TO_QC_PERSONA[normalizeSystemRole(role)] ?? null;
}

export function resolveQCPermissions(role?: string | null): Set<QCPermission> {
  const persona = resolveQCPersona(role);
  if (!persona) {
    return new Set();
  }
  return new Set(QC_PERMISSION_MATRIX[persona]);
}

export function hasQCPermission(
  role: string | null | undefined,
  permission: QCPermission
): boolean {
  return resolveQCPermissions(role).has(permission);
}

export function visibleIssueStatusesForRole(
  role?: string | null
): ReadonlySet<QualityIssueStatus> | null {
  const persona = resolveQCPersona(role);
  if (persona === "CONTRACTOR") {
    return CONTRACTOR_VISIBLE_STATUSES;
  }
  if (persona === "SUPERVISOR" || persona === "ADMIN" || persona === "DEVELOPER") {
    return null;
  }
  return null;
}

function isValidStatusTransition(
  fromStatus: QualityIssueStatus,
  toStatus: QualityIssueStatus
): boolean {
  if (fromStatus === toStatus) {
    return true;
  }
  return VALID_STATUS_TRANSITIONS.has(`${fromStatus}->${toStatus}`);
}

export function canPerformIssueTransition(
  role: string | null | undefined,
  fromStatus: QualityIssueStatus,
  toStatus: QualityIssueStatus
): boolean {
  if (!isValidStatusTransition(fromStatus, toStatus)) {
    return false;
  }

  const persona = resolveQCPersona(role);
  if (!persona) {
    return false;
  }
  if (persona === "DEVELOPER") {
    return false;
  }
  if (persona === "CONTRACTOR") {
    return CONTRACTOR_ALLOWED_TRANSITIONS.has(
      `${fromStatus}->${toStatus}`
    );
  }
  if (persona === "SUPERVISOR" || persona === "ADMIN") {
    return true;
  }
  return false;
}

export function qcInviteableRoles(actorRole?: string | null): readonly string[] {
  const normalized = normalizeSystemRole(actorRole);
  if (normalized === "PLATFORM_ADMIN") {
    return [
      "ADMIN",
      "SUPERVISOR",
      "DEVELOPER",
      "CONTRACTOR",
      "VIEWER",
    ];
  }
  if (normalized === "ADMIN") {
    return ["SUPERVISOR", "DEVELOPER", "CONTRACTOR", "VIEWER"];
  }
  return [];
}
