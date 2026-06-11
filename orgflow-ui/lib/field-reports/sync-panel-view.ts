import type { PendingSendSyncPhase } from "@/lib/field-reports/send-queue";
import { pendingSendPhaseLabelHe } from "@/lib/field-reports/send-queue";
import type { SyncManagerItemResult } from "@/lib/field-reports/sync/sync-manager";

export type SyncPanelUploadDisabledInput = {
  canSync: boolean;
  pendingCount: number;
  syncing: boolean;
  checking?: boolean;
};

export type SyncRunSummary = {
  successCount: number;
  failedCount: number;
  total: number;
  messageHe: string;
};

export function pendingSendReadyBannerText(pendingCount: number): string | null {
  if (pendingCount <= 0) {
    return null;
  }

  if (pendingCount === 1) {
    return "דוח אחד מוכן לשליחה";
  }

  return `${pendingCount} דוחות מוכנים לשליחה`;
}

export function syncPanelUploadButtonLabel(syncing: boolean): string {
  return syncing ? "מעלה דוחות..." : "העלה דוחות ומסמכים";
}

export function syncPanelUploadDisabledReason(
  input: SyncPanelUploadDisabledInput
): string | null {
  if (input.syncing) {
    return "סנכרון פעיל";
  }

  if (input.checking) {
    return "בודק חיבור לשרת...";
  }

  if (input.pendingCount <= 0) {
    return "אין דוחות ממתינים לשליחה";
  }

  if (!input.canSync) {
    return "אין חיבור לשרת - נסה שוב כשהרשת זמינה";
  }

  return null;
}

export function isSyncPanelUploadEnabled(
  input: SyncPanelUploadDisabledInput
): boolean {
  return syncPanelUploadDisabledReason(input) === null;
}

export function buildSyncProgressLabel(
  activeIndex: number,
  total: number,
  phase?: PendingSendSyncPhase
): string {
  const phaseLabel = pendingSendPhaseLabelHe(phase);
  if (total <= 0 || activeIndex <= 0) {
    return phaseLabel;
  }

  return `דוח ${activeIndex} מתוך ${total} - ${phaseLabel}`;
}

export function buildSyncRunSummary(
  processed: SyncManagerItemResult[]
): SyncRunSummary | null {
  if (!processed.length) {
    return null;
  }

  const successCount = processed.filter((item) => item.success).length;
  const failedCount = processed.length - successCount;

  let messageHe: string;
  if (failedCount === 0) {
    messageHe =
      successCount === 1
        ? "דוח אחד הועלה בהצלחה"
        : `${successCount} דוחות הועלו בהצלחה`;
  } else if (successCount === 0) {
    messageHe =
      failedCount === 1
        ? "העלאת דוח אחד נכשלה"
        : `העלאת ${failedCount} דוחות נכשלה`;
  } else {
    messageHe = `${successCount} הועלו בהצלחה, ${failedCount} נכשלו`;
  }

  return {
    successCount,
    failedCount,
    total: processed.length,
    messageHe,
  };
}

export function queueEntriesWithErrors<
  T extends { lastError?: string },
>(entries: T[]): T[] {
  return entries.filter((entry) => Boolean(entry.lastError?.trim()));
}

export function shouldShowSyncPanel(input: {
  pendingCount: number;
  syncing: boolean;
  hasQueueErrors: boolean;
  lastRunSummary: SyncRunSummary | null;
}): boolean {
  return (
    input.pendingCount > 0
    || input.syncing
    || input.hasQueueErrors
    || input.lastRunSummary !== null
  );
}
