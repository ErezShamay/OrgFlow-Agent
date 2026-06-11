/**
 * QC Spec 0.4 - Navigation structure for the QC platform.
 * See docs/qc-spec/qc-navigation.md.
 *
 * Wired into dashboard sidebar - stage 5.1.
 */

import type { NavLink } from "@/lib/navigation";
import {
  hasQCPermission,
  resolveQCPersona,
} from "@/lib/quality-issues/permissions";

export type QCPrimaryNavId =
  | "field_reports"
  | "issues"
  | "qc_portfolio"
  | "projects";

export type QCProjectNavId =
  | "overview"
  | "field_reports"
  | "issues"
  | "reviews_ai";

export type QCNavItem = NavLink & {
  id: QCPrimaryNavId | QCProjectNavId;
  requiredPermission?: string;
};

export const QC_FIELD_REPORTS_ROUTE = {
  id: "field_reports" as const,
  href: "/field-reports",
  label: "דוחות שטח",
};

export const QC_ISSUES_ROUTE = {
  id: "issues" as const,
  href: "/issues",
  label: "ליקויים",
};

export const QC_PORTFOLIO_ROUTE = {
  id: "qc_portfolio" as const,
  href: "/portfolio",
  label: "תיק QC",
};

export const QC_PROJECTS_ROUTE = {
  id: "projects" as const,
  href: "/projects",
  label: "פרויקטים",
};

export const QC_PRIMARY_NAV_ITEMS: ReadonlyArray<
  QCNavItem & { id: QCPrimaryNavId }
> = [
  {
    ...QC_FIELD_REPORTS_ROUTE,
    requiredPermission: "field_reports:read",
  },
  {
    ...QC_ISSUES_ROUTE,
    requiredPermission: "quality_issues:read",
  },
  {
    ...QC_PORTFOLIO_ROUTE,
    requiredPermission: "quality_portfolio:read",
  },
  {
    ...QC_PROJECTS_ROUTE,
    requiredPermission: "projects:read",
  },
];

/** Routes removed from primary nav in QC mode (still reachable by direct URL). */
export const QC_DEPRECATED_PRIMARY_ROUTES: ReadonlyArray<NavLink> = [
  { href: "/upload", label: "העלאת דוח" },
  { href: "/reviews", label: "ביקורות AI" },
  { href: "/actions", label: "פעולות תפעוליות" },
  { href: "/escalations", label: "נקודות סיכון" },
  { href: "/tenants", label: "מנהל דיירים" },
  { href: "/alerts", label: "התראות" },
];

const PRIMARY_NAV_PERSONA_VISIBILITY: Record<
  QCPrimaryNavId,
  ReadonlySet<string>
> = {
  field_reports: new Set(["SUPERVISOR", "ADMIN", "DEVELOPER"]),
  issues: new Set(["SUPERVISOR", "CONTRACTOR", "DEVELOPER", "ADMIN"]),
  qc_portfolio: new Set(["SUPERVISOR", "DEVELOPER", "ADMIN"]),
  projects: new Set(["SUPERVISOR", "CONTRACTOR", "DEVELOPER", "ADMIN"]),
};

const PROJECT_NAV_PERSONA_VISIBILITY: Record<
  QCProjectNavId,
  ReadonlySet<string>
> = {
  overview: new Set(["SUPERVISOR", "CONTRACTOR", "DEVELOPER", "ADMIN"]),
  field_reports: new Set(["SUPERVISOR", "DEVELOPER", "ADMIN"]),
  issues: new Set(["SUPERVISOR", "CONTRACTOR", "DEVELOPER", "ADMIN"]),
  reviews_ai: new Set(["SUPERVISOR", "ADMIN"]),
};

/** Project-scoped secondary nav (stage 5.4) - not in global primary nav. */
export const QC_PROJECT_SECONDARY_NAV_IDS: ReadonlySet<QCProjectNavId> =
  new Set(["reviews_ai"]);

function buildQCProjectNavItems(
  projectId: string
): Array<QCNavItem & { id: QCProjectNavId }> {
  return [
    {
      id: "overview",
      href: `/projects/${projectId}`,
      label: "סקירת הפרויקט",
    },
    {
      id: "field_reports",
      href: `/projects/${projectId}/field-reports`,
      label: "דוחות שטח",
      requiredPermission: "field_reports:read",
    },
    {
      id: "issues",
      href: `/projects/${projectId}/issues`,
      label: "ליקויים",
      requiredPermission: "quality_issues:read",
    },
    {
      id: "reviews_ai",
      href: `/projects/${projectId}/reviews`,
      label: "ביקורות AI",
    },
  ];
}

function filterQCProjectNavItems(
  items: Array<QCNavItem & { id: QCProjectNavId }>,
  role?: string | null
): Array<QCNavItem & { id: QCProjectNavId }> {
  const persona = resolveQCPersona(role);

  return items.filter((item) => {
    if (
      !isVisibleForPersona(
        persona,
        PROJECT_NAV_PERSONA_VISIBILITY[item.id]
      )
    ) {
      return false;
    }

    if (
      item.requiredPermission &&
      !hasQCPermission(role, item.requiredPermission as never)
    ) {
      return false;
    }

    return true;
  });
}

export type QCPrimaryNavOptions = {
  role?: string | null;
  fieldReportsEnabled?: boolean;
};

function isVisibleForPersona(
  persona: string | null,
  allowedPersonas: ReadonlySet<string>
): boolean {
  return persona !== null && allowedPersonas.has(persona);
}

export function getQCPrimaryNavLinks(
  options: QCPrimaryNavOptions = {}
): NavLink[] {
  const persona = resolveQCPersona(options.role);
  const fieldReportsEnabled = options.fieldReportsEnabled ?? true;

  return QC_PRIMARY_NAV_ITEMS.filter((item) => {
    if (item.id === "field_reports" && !fieldReportsEnabled) {
      return false;
    }

    if (!isVisibleForPersona(persona, PRIMARY_NAV_PERSONA_VISIBILITY[item.id])) {
      return false;
    }

    if (
      item.requiredPermission &&
      !hasQCPermission(options.role, item.requiredPermission as never)
    ) {
      return false;
    }

    return true;
  }).map(({ href, label }) => ({ href, label }));
}

export function getQCProjectPrimaryNavLinks(
  projectId: string,
  role?: string | null
): NavLink[] {
  return filterQCProjectNavItems(buildQCProjectNavItems(projectId), role)
    .filter((item) => !QC_PROJECT_SECONDARY_NAV_IDS.has(item.id))
    .map(({ href, label }) => ({ href, label }));
}

export function getQCProjectSecondaryNavLinks(
  projectId: string,
  role?: string | null
): NavLink[] {
  return filterQCProjectNavItems(buildQCProjectNavItems(projectId), role)
    .filter((item) => QC_PROJECT_SECONDARY_NAV_IDS.has(item.id))
    .map(({ href, label }) => ({ href, label }));
}

export function getQCProjectNavLinks(
  projectId: string,
  role?: string | null
): NavLink[] {
  return filterQCProjectNavItems(buildQCProjectNavItems(projectId), role).map(
    ({ href, label }) => ({ href, label })
  );
}

export function isQCProjectNavActive(pathname: string, href: string): boolean {
  if (/^\/projects\/[^/]+$/.test(href)) {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isQCPrimaryNavActive(pathname: string, href: string): boolean {
  if (href === QC_PORTFOLIO_ROUTE.href) {
    return pathname === href;
  }

  if (href === QC_PROJECTS_ROUTE.href) {
    if (/^\/projects\/[^/]+\/reviews(?:\/|$)/.test(pathname)) {
      return false;
    }

    return (
      pathname === href || pathname.startsWith(`${href}/`)
    );
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function recommendedPostLoginRoute(role?: string | null): string {
  const persona = resolveQCPersona(role);
  if (persona === "CONTRACTOR") {
    return QC_ISSUES_ROUTE.href;
  }
  return QC_PORTFOLIO_ROUTE.href;
}
