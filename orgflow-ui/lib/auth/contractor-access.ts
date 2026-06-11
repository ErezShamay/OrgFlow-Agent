/**
 * QC Spec 4.2.1 - Contractor persona access profile (limited permissions).
 * See docs/qc-spec/qc-personas-permissions.md §2.2.
 */

import type { QCPermission } from "@/lib/quality-issues/permissions";
import {
  hasQCPermission,
  resolveQCPermissions,
  resolveQCPersona,
  visibleIssueStatusesForRole,
} from "@/lib/quality-issues/permissions";

export const CONTRACTOR_GRANTED_PERMISSIONS = [
  "quality_issues:read",
  "quality_issues:remediate",
  "projects:read",
] as const satisfies readonly QCPermission[];

export const CONTRACTOR_DENIED_PERMISSIONS = [
  "quality_issues:write",
  "quality_issues:verify",
  "quality_portfolio:read",
  "field_reports:read",
  "field_reports:write",
  "field_reports:admin",
  "reports:read",
  "reports:write",
  "users:read",
  "users:write",
  "audit:read",
] as const satisfies readonly QCPermission[];

export function isContractorRole(role?: string | null): boolean {
  return resolveQCPersona(role) === "CONTRACTOR";
}

export function getContractorAccessProfile(role?: string | null) {
  const permissions = resolveQCPermissions(role);
  const visibleStatuses = visibleIssueStatusesForRole(role);

  return {
    persona: resolveQCPersona(role),
    permissions: [...permissions],
    visibleIssueStatuses:
      visibleStatuses === null ? null : [...visibleStatuses],
    canReadIssues: hasQCPermission(role, "quality_issues:read"),
    canRemediateIssues: hasQCPermission(role, "quality_issues:remediate"),
    canAccessFieldReports: hasQCPermission(role, "field_reports:read"),
    canAccessPortfolio: hasQCPermission(role, "quality_portfolio:read"),
  };
}

export function contractorHasLimitedAccess(role?: string | null): boolean {
  if (!isContractorRole(role)) {
    return false;
  }

  const profile = getContractorAccessProfile(role);

  return (
    profile.canReadIssues
    && profile.canRemediateIssues
    && !profile.canAccessFieldReports
    && !profile.canAccessPortfolio
    && profile.visibleIssueStatuses !== null
    && profile.visibleIssueStatuses.includes("OPEN")
    && profile.visibleIssueStatuses.includes("IN_REMEDIATION")
    && !profile.visibleIssueStatuses.includes("CLOSED")
  );
}
