import {
  listActiveSyncQueueForUser,
} from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  listLocalReportsForOrganization,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";

export type FieldReportLogoutBlockSummary = {
  /** מספר דוחות ייחודיים שחוסמים יציאה. */
  pendingReportCount: number;
  syncQueueCount: number;
  pendingSendCount: number;
  pendingLocalReportCount: number;
  total: number;
};

export type FieldReportLogoutBlock = {
  message: string;
  summary: FieldReportLogoutBlockSummary;
};

function matchesReportUser(
  report: LocalVisitReportRecord,
  userId: string
): boolean {
  return !report.user_id || report.user_id === userId;
}

function isPendingLocalReport(report: LocalVisitReportRecord): boolean {
  if (report.sync_status === "done") {
    return false;
  }

  if (report.sync_status === "failed" || report.sync_status === "syncing") {
    return true;
  }

  // טיוטה בעבודה — לא חוסמת יציאה; רק דוח סגור מקומית ממתין להעלאה.
  return report.local_status === "LOCAL_CLOSED";
}

async function collectPendingLogoutReportUuids(
  organizationId: string,
  userId: string
): Promise<{
  uuids: Set<string>;
  syncQueueCount: number;
  pendingLocalReportCount: number;
}> {
  const queueRecords = await listActiveSyncQueueForUser(
    organizationId,
    userId
  );
  const localReports = await listLocalReportsForOrganization(organizationId);

  const uuids = new Set<string>();
  for (const record of queueRecords) {
    uuids.add(record.client_report_uuid);
  }

  let pendingLocalReportCount = 0;
  for (const report of localReports) {
    if (!matchesReportUser(report, userId)) {
      continue;
    }

    if (!isPendingLocalReport(report)) {
      continue;
    }

    pendingLocalReportCount += 1;
    uuids.add(report.client_report_uuid);
  }

  return {
    uuids,
    syncQueueCount: queueRecords.length,
    pendingLocalReportCount,
  };
}

function buildLogoutBlockMessage(pendingReportCount: number): string {
  const countLabel =
    pendingReportCount === 1
      ? "דוח אחד ממתין להעלאה"
      : `${pendingReportCount} דוחות ממתינים להעלאה`;

  return `לא ניתן להתנתק — ${countLabel}. סנכרן או שלח לליבה לפני יציאה.`;
}

export async function summarizeFieldReportLogoutBlock(
  organizationId: string,
  userId: string
): Promise<FieldReportLogoutBlockSummary> {
  const { uuids, syncQueueCount, pendingLocalReportCount } =
    await collectPendingLogoutReportUuids(organizationId, userId);
  /** תור שליחה לליבה מאוחד ל-`sync_queue` (FR-024). */
  const pendingSendCount = 0;
  const pendingReportCount = uuids.size;

  return {
    pendingReportCount,
    syncQueueCount,
    pendingSendCount,
    pendingLocalReportCount,
    total: pendingReportCount,
  };
}

export async function getFieldReportLogoutBlock(
  organizationId: string | null | undefined,
  userId: string | null | undefined
): Promise<FieldReportLogoutBlock | null> {
  if (!organizationId || !userId) {
    return null;
  }

  const summary = await summarizeFieldReportLogoutBlock(
    organizationId,
    userId
  );

  if (summary.total === 0) {
    return null;
  }

  return {
    message: buildLogoutBlockMessage(summary.pendingReportCount),
    summary,
  };
}

export class FieldReportLogoutBlockedError extends Error {
  readonly block: FieldReportLogoutBlock;

  constructor(block: FieldReportLogoutBlock) {
    super(block.message);
    this.name = "FieldReportLogoutBlockedError";
    this.block = block;
  }
}

export async function assertFieldReportLogoutAllowed(
  organizationId: string | null | undefined,
  userId: string | null | undefined
): Promise<void> {
  const block = await getFieldReportLogoutBlock(organizationId, userId);
  if (block) {
    throw new FieldReportLogoutBlockedError(block);
  }
}
