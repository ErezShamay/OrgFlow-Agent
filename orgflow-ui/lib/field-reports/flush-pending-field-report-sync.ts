import { SyncManager } from "@/lib/field-reports/sync/sync-manager";
import { pingFieldReportsApi } from "@/lib/field-reports/sync/network-status";

/**
 * מנסה להעלות דוחות ממתינים לפני בדיקות חסימה (יציאה / התנתקות).
 */
export async function flushPendingFieldReportSync(
  organizationId: string | null | undefined,
  userId: string | null | undefined
): Promise<void> {
  if (!organizationId || !userId) {
    return;
  }

  const online = await pingFieldReportsApi();
  if (!online) {
    return;
  }

  await SyncManager.runForOrganization(organizationId, userId);
}
