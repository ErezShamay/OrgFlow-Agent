export type NavLink = {
  href: string;
  label: string;
};

export const SETTINGS_ROUTE = {
  href: "/settings",
  label: "הגדרות",
} as const;

export const LANDING_SECTION_LINKS = [
  { id: "features", label: "יכולות" },
  { id: "how-it-works", label: "איך זה עובד" },
  { id: "platform", label: "הפלטפורמה" },
] as const;

export function landingSectionHref(sectionId: string) {
  return `/#${sectionId}`;
}

export const PUBLIC_ROUTES = ["/", "/settings"] as const;

export function isPublicRoute(pathname: string) {
  return (
    pathname === "/"
    || pathname === "/settings"
    || pathname.startsWith("/auth")
  );
}

export const GLOBAL_NAV_LINKS: NavLink[] = [
  { href: "/", label: "דף הבית" },
  { href: "/portfolio", label: "תיק פרויקטים" },
  { href: "/projects", label: "פרויקטים" },
  { href: "/tenants", label: "מנהל דיירים" },
  { href: "/upload", label: "העלאת דוח" },
  { href: "/reviews", label: "ביקורות AI" },
  { href: "/actions", label: "פעולות תפעוליות" },
  { href: "/escalations", label: "נקודות סיכון" },
  { href: "/automation", label: "אוטומציה" },
  { href: "/automation/dead-letters", label: "Dead Letters" },
];
