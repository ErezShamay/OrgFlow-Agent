import { deleteVisitReportPdfLocally } from "@/lib/field-reports/pdf/visit-report-pdf-store";
import { deleteAllBlobsForReport } from "@/lib/field-reports/repositories/blobs-repository";
import {
  deleteLocalReport,
  getLocalReportByServerId,
} from "@/lib/field-reports/repositories/reports-repository";
import { removeSyncQueueRecord } from "@/lib/field-reports/repositories/sync-queue-repository";
import { removePendingSendRequest } from "@/lib/field-reports/send-queue";
import { clearFieldReportSyncErrorsForReport } from "@/lib/field-reports/sync/sync-error-monitor";

async function deleteDeviceArtifactsForReportKey(reportKey: string) {
  await deleteAllBlobsForReport(reportKey);
  await deleteVisitReportPdfLocally(reportKey);
}

/**
 * אחרי שליחה מוצלחת לליבה - מסיר עותק מקומי, PDF, תמונות ותורים.
 */
export async function purgeFieldReportAfterCoreSend(options: {
  organizationId: string;
  serverReportId: string;
}): Promise<void> {
  const { organizationId, serverReportId } = options;
  if (!serverReportId) {
    return;
  }

  const local = await getLocalReportByServerId(serverReportId);
  const purgeKeys = new Set<string>([serverReportId]);

  if (local?.client_report_uuid) {
    purgeKeys.add(local.client_report_uuid);
  }

  for (const reportKey of purgeKeys) {
    await deleteDeviceArtifactsForReportKey(reportKey);
  }

  if (local) {
    await removeSyncQueueRecord(local.client_report_uuid);
    await deleteLocalReport(local.client_report_uuid);
    clearFieldReportSyncErrorsForReport(
      organizationId,
      local.client_report_uuid
    );
  }

  if (organizationId) {
    await removePendingSendRequest(organizationId, serverReportId);
  }
}
