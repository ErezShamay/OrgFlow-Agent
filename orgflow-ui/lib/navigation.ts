import {
  isPlatformAdmin,
} from "@/lib/auth/permissions";
import { recommendedPostLoginRoute } from "@/lib/qc-navigation";

export type NavLink = {
  href: string;
  label: string;
};

/** Legacy ingest route - hidden from primary nav (stage 5.2); direct URL still works. */
export const UPLOAD_LEGACY_ROUTE = {
  href: "/upload",
  label: "העלאת דוח",
} as const;

/** Legacy operational actions - hidden from primary nav (stage 5.3); merged into /issues. */
export const ACTIONS_LEGACY_ROUTE = {
  href: "/actions",
  label: "פעולות תפעוליות",
} as const;

/** Legacy escalations - hidden from primary nav (stage 5.3); merged into /issues. */
export const ESCALATIONS_LEGACY_ROUTE = {
  href: "/escalations",
  label: "נקודות סיכון",
} as const;

/** Global AI reviews - hidden from primary nav (stage 5.4); project tab only. */
export const REVIEWS_GLOBAL_LEGACY_ROUTE = {
  href: "/reviews",
  label: "ביקורות AI",
} as const;

/**
 * Routes removed from primary navigation (stage 5.2+).
 * See docs/PRODUCT-SPEC-LOCKED.md §7 — deprecated surfaces.
 */
export const PRIMARY_NAV_HIDDEN_ROUTES: readonly string[] = [
  UPLOAD_LEGACY_ROUTE.href,
  ACTIONS_LEGACY_ROUTE.href,
  ESCALATIONS_LEGACY_ROUTE.href,
  REVIEWS_GLOBAL_LEGACY_ROUTE.href,
];

export function filterPrimaryNavLinks(links: readonly NavLink[]): NavLink[] {
  const hidden = new Set(PRIMARY_NAV_HIDDEN_ROUTES);
  return links.filter((link) => !hidden.has(link.href));
}

export const SETTINGS_ROUTE = {
  href: "/settings",
  label: "הגדרות",
} as const;

export const ADMIN_USERS_ROUTE = {
  href: "/admin/users",
  label: "ניהול משתמשים",
} as const;

export const PLATFORM_ADMIN_HOME_ROUTE = {
  href: "/admin/platform",
  label: "דשבורד לקוחות",
} as const;

export const PLATFORM_ADMIN_NAV_LINKS: NavLink[] = [
  PLATFORM_ADMIN_HOME_ROUTE,
  ADMIN_USERS_ROUTE,
  SETTINGS_ROUTE,
];

export const AUTOMATION_ROUTE = {
  href: "/automation",
  label: "אוטומציה",
} as const;

export const DEAD_LETTERS_ROUTE = {
  href: "/automation/dead-letters",
  label: "Dead Letters",
} as const;

/** Admin-only system routes (stage 5.5) - hidden from non-admin system nav. */
export const ADMIN_ONLY_SYSTEM_ROUTES = [
  AUTOMATION_ROUTE.href,
  DEAD_LETTERS_ROUTE.href,
] as const;

export const ADMIN_SYSTEM_NAV_LINKS: NavLink[] = [
  DEAD_LETTERS_ROUTE,
  AUTOMATION_ROUTE,
];

export const SYSTEM_NAV_LABEL = "מערכת";

/** Settings visible to all authenticated dashboard users. */
export const SYSTEM_NAV_LINKS: NavLink[] = [SETTINGS_ROUTE];

export function isAdminOnlySystemRoute(href: string): boolean {
  const normalized = (href || "").trim().replace(/\/+$/, "") || "/";

  return ADMIN_ONLY_SYSTEM_ROUTES.some(
    (route) => normalized === route || normalized.startsWith(`${route}/`)
  );
}

export function getSystemNavLinks(
  isAdmin: boolean,
  options?: {
    platformAdmin?: boolean;
  }
): NavLink[] {
  if (options?.platformAdmin) {
    return [
      ...PLATFORM_ADMIN_NAV_LINKS,
      ...ADMIN_SYSTEM_NAV_LINKS,
    ];
  }

  if (isAdmin) {
    return [
      ADMIN_USERS_ROUTE,
      ...SYSTEM_NAV_LINKS,
      ...ADMIN_SYSTEM_NAV_LINKS,
    ];
  }

  return SYSTEM_NAV_LINKS;
}

export function resolvePostLoginRoute(
  role?: string | null
): string {
  return recommendedPostLoginRoute(role);
}

function matchesNavPath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isNavLinkActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  if (href === AUTOMATION_ROUTE.href) {
    return (
      pathname === href
      || (
        pathname.startsWith(`${href}/`)
        && !pathname.startsWith(DEAD_LETTERS_ROUTE.href)
      )
    );
  }

  if (href === DEAD_LETTERS_ROUTE.href) {
    return matchesNavPath(pathname, href);
  }

  return matchesNavPath(pathname, href);
}

export function isSystemNavActive(pathname: string, isAdmin: boolean) {
  return getSystemNavLinks(isAdmin).some((link) =>
    isNavLinkActive(pathname, link.href)
  );
}

export const LANDING_SECTION_LINKS = [
  { id: "features", label: "יכולות" },
  { id: "how-it-works", label: "איך זה עובד" },
  { id: "platform", label: "הפלטפורמה" },
] as const;

export function landingSectionHref(sectionId: string) {
  return `/#${sectionId}`;
}

export const PUBLIC_ROUTES = ["/"] as const;

export const POST_LOGIN_ROUTE = "/projects" as const;

export function isPublicRoute(pathname: string) {
  return (
    pathname === "/"
    || pathname.startsWith("/auth")
    || pathname.startsWith("/legal")
  );
}

export const FIELD_REPORTS_ROUTE = {
  href: "/field-reports",
  label: "דוחות שטח",
} as const;

/** Supervision primary nav — PRODUCT-SPEC-LOCKED §11. */
export const GLOBAL_NAV_LINKS: NavLink[] = filterPrimaryNavLinks([
  { href: "/projects", label: "סקירת הפרויקטים" },
  FIELD_REPORTS_ROUTE,
  { href: "/issues", label: "ליקויים" },
  { href: "/portfolio", label: "תיק פיקוח הנדסי" },
]);

/** Legacy PM navbar - public home until stage 5.8. Upload hidden in 5.2. */
const LEGACY_HOME_NAVBAR_LINKS_SOURCE: NavLink[] = [
  { href: "/", label: "דף הבית" },
  { href: "/portfolio", label: "תיק הפרויקטים" },
  { href: "/projects", label: "פרויקטים" },
  { href: "/tenants", label: "מנהל דיירים" },
  UPLOAD_LEGACY_ROUTE,
  REVIEWS_GLOBAL_LEGACY_ROUTE,
  ACTIONS_LEGACY_ROUTE,
  ESCALATIONS_LEGACY_ROUTE,
];

export const LEGACY_HOME_NAVBAR_LINKS: NavLink[] = filterPrimaryNavLinks(
  LEGACY_HOME_NAVBAR_LINKS_SOURCE
);

export const HOME_NAVBAR_LINKS: NavLink[] = [...LEGACY_HOME_NAVBAR_LINKS];
