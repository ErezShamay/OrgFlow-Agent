/**
 * QC Spec 4.2.2 - Contractor filtered issues view (OPEN / IN_REMEDIATION only).
 */

import { isContractorRole } from "@/lib/auth/contractor-access";

export const CONTRACTOR_VISIBLE_STATUSES = ["OPEN", "IN_REMEDIATION"] as const;

export function isContractorIssuesView(role?: string | null): boolean {
  return isContractorRole(role);
}

export function contractorIssuesPageTitle(): string {
  return "ליקויים לתיקון";
}

export function contractorIssuesPageDescription(): string {
  return "ליקויים פתוחים או בטיפול שדורשים תיקון - ללא גישה לליקויים שנסגרו או ממתינים לאימות";
}

export function contractorIssuesEmptyMessage(filtersActive: boolean): string {
  if (filtersActive) {
    return "אין ליקויים פתוחים או בטיפול התואמים את הסינון";
  }

  return "אין כרגע ליקויים פתוחים או בטיפול";
}

export function contractorStatusFilterAllLabel(): string {
  return "פתוח ובטיפול";
}
