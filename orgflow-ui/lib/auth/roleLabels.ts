import {
  normalizeRole,
} from "@/lib/auth/role";

export const GLOBAL_ADMIN_ROLE = "PLATFORM_ADMIN";
export const CUSTOMER_ADMIN_ROLE = "ADMIN";

export const ROLE_LABELS: Record<string, string> = {
  PLATFORM_ADMIN: "מנהל גלובלי",
  ADMIN: "מנהל לקוח",
  SUPERVISOR: "מפקח",
  VIEWER: "משתמש כללי",
  MANAGER: "מנהל",
  ANALYST: "אנליסט",
};

export const ROLE_DESCRIPTIONS: Record<string, string> = {
  PLATFORM_ADMIN:
    "גישה לכל הלקוחות, יצירת לקוחות חדשים וניהול משתמשים בכל ארגון",
  ADMIN:
    "גישה רק ללקוח אחד, ניהול משתמשים והרשאות בתוך הארגון שלו בלבד",
  SUPERVISOR:
    "גישה לפרויקטים ודוחות, ללא הרשאות ניהול משתמשים",
  VIEWER:
    "צפייה בפרויקטים ודוחות בלבד, ללא הרשאות ניהול",
};

export function getRoleLabel(
  role?: string | null
): string {
  const normalized = normalizeRole(role);
  return ROLE_LABELS[normalized] || normalized || "—";
}

export function getRoleDescription(
  role?: string | null
): string | undefined {
  return ROLE_DESCRIPTIONS[normalizeRole(role)];
}

export function getRoleBadgeClass(
  role?: string | null
): string {
  const normalized = normalizeRole(role);

  if (normalized === GLOBAL_ADMIN_ROLE) {
    return "bg-brand-muted text-brand dark:bg-brand/15 dark:text-brand-light";
  }

  if (normalized === CUSTOMER_ADMIN_ROLE) {
    return "bg-brand-gold/15 text-brand-gold-dark dark:bg-brand-gold/10 dark:text-brand-gold";
  }

  if (normalized === "MANAGER" || normalized === "SUPERVISOR") {
    return "bg-brand-muted/80 text-brand-dark dark:bg-brand/10 dark:text-brand-light";
  }

  return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
}
