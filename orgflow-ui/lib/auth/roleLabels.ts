import {
  normalizeRole,
} from "@/lib/auth/role";

export const GLOBAL_ADMIN_ROLE = "PLATFORM_ADMIN";
export const CUSTOMER_ADMIN_ROLE = "ADMIN";

export const ROLE_LABELS: Record<string, string> = {
  PLATFORM_ADMIN: "מנהל גלובלי",
  ADMIN: "מנהל לקוח",
  SUPERVISOR: "מפקח",
  CONTRACTOR: "קבלן",
  DEVELOPER: "יזם",
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
  CONTRACTOR:
    "צפייה בליקויים פתוחים והגשת תיקון - ללא גישה לדוחות שטח או תיק QC",
  DEVELOPER:
    "תיק QC וליקויים לקריאה בלבד - ללא עריכת דוחות או ליקויים",
  VIEWER:
    "צפייה בפרויקטים ודוחות בלבד, ללא הרשאות ניהול",
};

export function getRoleLabel(
  role?: string | null
): string {
  const normalized = normalizeRole(role);
  return ROLE_LABELS[normalized] || normalized || "-";
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

  if (normalized === "CONTRACTOR") {
    return "bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-200";
  }

  if (normalized === "DEVELOPER") {
    return "bg-sky-100 text-sky-900 dark:bg-sky-900/30 dark:text-sky-200";
  }

  return "bg-brand-muted/70 text-[var(--of-color-text-muted)] dark:bg-brand/10 dark:text-[var(--of-color-text-muted)]";
}
