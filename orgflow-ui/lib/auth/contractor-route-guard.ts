/**
 * QC Spec 4.2.4 - Contractors must not access field reports or catalog routes.
 * See docs/qc-spec/qc-personas-permissions.md §2.2.
 */

import { recommendedPostLoginRoute } from "@/lib/qc-navigation";
import { isContractorRole } from "@/lib/auth/contractor-access";

/** Route prefixes blocked for CONTRACTOR persona (direct URL included). */
export const CONTRACTOR_DENIED_ROUTE_PREFIXES = [
  "/field-reports",
  "/portfolio",
  "/upload",
  "/reviews",
  "/actions",
  "/escalations",
  "/tenants",
  "/alerts",
  "/automation",
] as const;

const PROJECT_FIELD_REPORTS_PATTERN =
  /^\/projects\/[^/]+\/field-reports(?:\/|$)/;

const PROJECT_REVIEWS_PATTERN =
  /^\/projects\/[^/]+\/reviews(?:\/|$)/;

export function isContractorDeniedRoute(pathname: string): boolean {
  const normalized = pathname.trim() || "/";

  if (
    CONTRACTOR_DENIED_ROUTE_PREFIXES.some((prefix) =>
      normalized === prefix || normalized.startsWith(`${prefix}/`)
    )
  ) {
    return true;
  }

  if (PROJECT_FIELD_REPORTS_PATTERN.test(normalized)) {
    return true;
  }

  if (PROJECT_REVIEWS_PATTERN.test(normalized)) {
    return true;
  }

  return false;
}

export function canContractorAccessRoute(
  role: string | null | undefined,
  pathname: string
): boolean {
  if (!isContractorRole(role)) {
    return true;
  }

  return !isContractorDeniedRoute(pathname);
}

export function contractorDeniedRouteRedirect(
  role?: string | null
): string {
  return recommendedPostLoginRoute(role);
}
