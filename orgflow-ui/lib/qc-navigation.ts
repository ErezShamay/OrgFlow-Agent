/**
 * Supervision platform navigation — PRODUCT-SPEC-LOCKED.md §11.
 * PR tag: [finalize-pipeline]
 */

import { isResidentRole } from "@/lib/auth/resident-access";
import { RESIDENT_POST_LOGIN_ROUTE } from "@/lib/auth/resident-route-guard";
import type { NavLink } from "@/lib/navigation";
import {
  hasQCPermission,
  resolveQCPersona,
} from "@/lib/quality-issues/permissions";
import { isPlatformAdmin } from "@/lib/auth/permissions";
import { normalizeRole } from "@/lib/auth/role";

export type SupervisionPrimaryNavId =
  | "field_reports"
  | "issues"
  | "supervision_portfolio"
  | "projects";

export type SupervisionProjectNavId = "overview" | "issues" | "apartments";

/** @deprecated Use SupervisionPrimaryNavId */
export type QCPrimaryNavId =
  | SupervisionPrimaryNavId
  | "operational_review"
  | "qc_portfolio";

/** @deprecated Use SupervisionProjectNavId */
export type QCProjectNavId = SupervisionProjectNavId | "reviews_ai";

export type SupervisionNavItem = NavLink & {
  id: SupervisionPrimaryNavId | SupervisionProjectNavId;
  requiredPermission?: string;
};

/** @deprecated Use SupervisionNavItem */
export type QCNavItem = SupervisionNavItem;

export const SUPERVISION_FIELD_REPORTS_ROUTE = {
  id: "field_reports" as const,
  href: "/field-reports",
  label: "דוחות שטח",
};

export const SUPERVISION_ISSUES_ROUTE = {
  id: "issues" as const,
  href: "/issues",
  label: "ליקויים",
};

export const SUPERVISION_PORTFOLIO_ROUTE = {
  id: "supervision_portfolio" as const,
  href: "/portfolio",
  label: "תיק פיקוח הנדסי",
};

export const SUPERVISION_PROJECTS_ROUTE = {
  id: "projects" as const,
  href: "/projects",
  label: "סקירת הפרויקטים",
};

/** @deprecated */
export const QC_FIELD_REPORTS_ROUTE = SUPERVISION_FIELD_REPORTS_ROUTE;
/** @deprecated */
export const QC_ISSUES_ROUTE = SUPERVISION_ISSUES_ROUTE;
/** @deprecated */
export const QC_PORTFOLIO_ROUTE = {
  id: "qc_portfolio" as const,
  href: "/portfolio",
  label: SUPERVISION_PORTFOLIO_ROUTE.label,
};
/** @deprecated */
export const QC_OPERATIONAL_REVIEW_ROUTE = {
  id: "operational_review" as const,
  href: "/operational-review",
  label: "סקירה תפעולית",
};
/** @deprecated */
export const QC_PROJECTS_ROUTE = SUPERVISION_PROJECTS_ROUTE;

export const FIELD_REPORTS_UPLOAD_ROUTE = {
  href: "/field-reports/upload",
  label: "העלאת מסמכים",
} as const;

export const TENANT_MANAGER_ROUTE = {
  href: "/tenants",
  label: "מנהל דיירים",
} as const;

export const TOOLS_NAV_LABEL = "כלים נוספים";

export const SUPERVISION_PRIMARY_NAV_ITEMS: ReadonlyArray<
  SupervisionNavItem & { id: SupervisionPrimaryNavId }
> = [
  {
    ...SUPERVISION_PROJECTS_ROUTE,
    requiredPermission: "projects:read",
  },
  {
    ...SUPERVISION_FIELD_REPORTS_ROUTE,
    requiredPermission: "field_reports:read",
  },
  {
    ...SUPERVISION_ISSUES_ROUTE,
    requiredPermission: "quality_issues:read",
  },
  {
    ...SUPERVISION_PORTFOLIO_ROUTE,
    requiredPermission: "quality_portfolio:read",
  },
];

/** @deprecated Use SUPERVISION_PRIMARY_NAV_ITEMS */
export const QC_PRIMARY_NAV_ITEMS = SUPERVISION_PRIMARY_NAV_ITEMS;

/** Hidden routes — OUT of scope v1 (still reachable by direct URL). */
export const SUPERVISION_DEPRECATED_PRIMARY_ROUTES: ReadonlyArray<NavLink> = [
  { href: "/upload", label: "העלאת דוח" },
  { href: "/reviews", label: "ביקורות AI" },
  { href: "/actions", label: "פעולות תפעוליות" },
  { href: "/escalations", label: "נקודות סיכון" },
  { href: "/alerts", label: "התראות" },
  { href: "/operational-review", label: "סקירה תפעולית" },
];

/** @deprecated Use SUPERVISION_DEPRECATED_PRIMARY_ROUTES */
export const QC_DEPRECATED_PRIMARY_ROUTES = SUPERVISION_DEPRECATED_PRIMARY_ROUTES;

const DISABLED_V1_PERSONAS = new Set(["CONTRACTOR", "DEVELOPER"]);

const PRIMARY_NAV_PERSONA_VISIBILITY: Record<
  SupervisionPrimaryNavId,
  ReadonlySet<string>
> = {
  field_reports: new Set(["SUPERVISOR", "ADMIN"]),
  issues: new Set(["SUPERVISOR", "ADMIN"]),
  supervision_portfolio: new Set(["SUPERVISOR", "ADMIN"]),
  projects: new Set(["SUPERVISOR", "ADMIN"]),
};

const APARTMENTS_NAV_ROLES = new Set([
  "PLATFORM_ADMIN",
  "ADMIN",
  "SUPERVISOR",
  "MANAGER",
  "VIEWER",
  "ANALYST",
]);

const PROJECT_NAV_PERSONA_VISIBILITY: Record<
  SupervisionProjectNavId,
  ReadonlySet<string>
> = {
  overview: new Set(["SUPERVISOR", "ADMIN"]),
  issues: new Set(["SUPERVISOR", "ADMIN"]),
  apartments: new Set(["SUPERVISOR", "ADMIN"]),
};

function buildSupervisionProjectNavItems(
  projectId: string
): Array<SupervisionNavItem & { id: SupervisionProjectNavId }> {
  return [
    {
      id: "overview",
      href: `/projects/${projectId}`,
      label: "סקירה",
    },
    {
      id: "issues",
      href: `/projects/${projectId}/issues`,
      label: "ליקויים",
      requiredPermission: "quality_issues:read",
    },
    {
      id: "apartments",
      href: `/projects/${projectId}/apartments`,
      label: "דיירים",
    },
  ];
}

function filterSupervisionProjectNavItems(
  items: Array<SupervisionNavItem & { id: SupervisionProjectNavId }>,
  role?: string | null
): Array<SupervisionNavItem & { id: SupervisionProjectNavId }> {
  const persona = resolveQCPersona(role);

  if (persona !== null && DISABLED_V1_PERSONAS.has(persona)) {
    return [];
  }

  return items.filter((item) => {
    if (item.id === "apartments") {
      return APARTMENTS_NAV_ROLES.has(normalizeRole(role));
    }

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

export type SupervisionPrimaryNavOptions = {
  role?: string | null;
  fieldReportsEnabled?: boolean;
};

/** @deprecated Use SupervisionPrimaryNavOptions */
export type QCPrimaryNavOptions = SupervisionPrimaryNavOptions;

function isVisibleForPersona(
  persona: string | null,
  allowedPersonas: ReadonlySet<string>
): boolean {
  return persona !== null && allowedPersonas.has(persona);
}

export function getSupervisionPrimaryNavLinks(
  options: SupervisionPrimaryNavOptions = {}
): NavLink[] {
  const persona = resolveQCPersona(options.role);

  if (persona !== null && DISABLED_V1_PERSONAS.has(persona)) {
    return [];
  }

  const fieldReportsEnabled = options.fieldReportsEnabled ?? true;

  return SUPERVISION_PRIMARY_NAV_ITEMS.filter((item) => {
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

/** @deprecated Use getSupervisionPrimaryNavLinks */
export const getQCPrimaryNavLinks = getSupervisionPrimaryNavLinks;

export function getSupervisionProjectNavLinks(
  projectId: string,
  role?: string | null
): NavLink[] {
  return filterSupervisionProjectNavItems(
    buildSupervisionProjectNavItems(projectId),
    role
  ).map(({ href, label }) => ({ href, label }));
}

/** @deprecated Use getSupervisionProjectNavLinks */
export const getQCProjectNavLinks = getSupervisionProjectNavLinks;

export function getSupervisionProjectPrimaryNavLinks(
  projectId: string,
  role?: string | null
): NavLink[] {
  return getSupervisionProjectNavLinks(projectId, role);
}

/** @deprecated Use getSupervisionProjectPrimaryNavLinks */
export const getQCProjectPrimaryNavLinks = getSupervisionProjectPrimaryNavLinks;

/** Reviews AI hidden in supervision v1 — no secondary project nav. */
export function getSupervisionProjectSecondaryNavLinks(
  _projectId: string,
  _role?: string | null
): NavLink[] {
  return [];
}

/** @deprecated Use getSupervisionProjectSecondaryNavLinks */
export const getQCProjectSecondaryNavLinks =
  getSupervisionProjectSecondaryNavLinks;

/** @deprecated Empty in supervision v1 */
export const QC_PROJECT_SECONDARY_NAV_IDS: ReadonlySet<QCProjectNavId> =
  new Set();

export function isSupervisionProjectNavActive(
  pathname: string,
  href: string
): boolean {
  if (/^\/projects\/[^/]+$/.test(href)) {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

/** @deprecated Use isSupervisionProjectNavActive */
export const isQCProjectNavActive = isSupervisionProjectNavActive;

export function isSupervisionPrimaryNavActive(
  pathname: string,
  href: string
): boolean {
  if (href === SUPERVISION_PORTFOLIO_ROUTE.href) {
    return pathname === href;
  }

  if (href === SUPERVISION_PROJECTS_ROUTE.href) {
    if (/^\/projects\/[^/]+\/reviews(?:\/|$)/.test(pathname)) {
      return false;
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

/** @deprecated Use isSupervisionPrimaryNavActive */
export const isQCPrimaryNavActive = isSupervisionPrimaryNavActive;

export function getToolsNavLinks(options: {
  tenantManagerEnabled?: boolean;
}): NavLink[] {
  const links: NavLink[] = [];

  if (options.tenantManagerEnabled) {
    links.push(TENANT_MANAGER_ROUTE);
  }

  return links;
}

export function isToolsNavActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function recommendedPostLoginRoute(role?: string | null): string {
  if (isResidentRole(role)) {
    return RESIDENT_POST_LOGIN_ROUTE;
  }

  if (isPlatformAdmin(role)) {
    return "/admin/platform";
  }

  if (normalizeRole(role) === "SUPERVISOR") {
    return SUPERVISION_PROJECTS_ROUTE.href;
  }

  return SUPERVISION_PROJECTS_ROUTE.href;
}
