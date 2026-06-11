import { apiFetch } from "@/lib/api/client";
import type { SyncQueueRecord } from "@/lib/field-reports/db/schema";
import {
  loadVisitReportPdfLocally,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";
import { processPendingSendRequest } from "@/lib/field-reports/process-send-queue";
import { purgeFieldReportAfterCoreSend } from "@/lib/field-reports/purge-field-report-after-core-send";
import {
  getLocalReport,
  saveLocalReport,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  listActiveSyncQueueForOrganization,
  listActiveSyncQueueForUser,
  removeSyncQueueRecord,
  updateSyncQueueRecord,
} from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  syncQueueRecordToPendingSendRequest,
  type PendingSendSyncPhase,
} from "@/lib/field-reports/send-queue";
import { buildVisitReportSyncBody } from "@/lib/field-reports/sync/build-sync-body";
import {
  clearFieldReportSyncErrorsForReport,
  recordFieldReportSyncError,
} from "@/lib/field-reports/sync/sync-error-monitor";
import { syncPendingLinePhotosForReport } from "@/lib/field-reports/sync-pending-line-photos";

export type SyncManagerItemResult = {
  clientReportUuid: string;
  reportId: string;
  success: boolean;
  error?: string;
};

export type SyncManagerRunResult = {
  processed: SyncManagerItemResult[];
};

export type SyncManagerProgressEvent = {
  index: number;
  total: number;
  clientReportUuid: string;
  phase: PendingSendSyncPhase;
};

export type SyncManagerRunOptions = {
  onProgress?: (event: SyncManagerProgressEvent) => void;
};

type SyncVisitReportResponse = {
  id: string;
  report?: {
    id?: string;
    status?: string;
    lines?: Array<{
      id: string;
      client_line_uuid?: string;
    }>;
  };
};

function buildRequestSendErrorMessage(payload: unknown): string {
  const apiPayload = (payload || {}) as {
    error?: {
      message?: string;
      details?: {
        error_code?: string;
      };
    };
    message?: string;
  };
  const apiMessage =
    apiPayload.error?.message
    || apiPayload.message
    || "שליחה לליבה נכשלה";
  const apiErrorCode = apiPayload.error?.details?.error_code;
  if (!apiErrorCode) {
    return apiMessage;
  }
  return `${apiMessage} (${apiErrorCode})`;
}

function buildApiErrorMessage(payload: unknown, fallback: string): string {
  const apiPayload = (payload || {}) as {
    error?: { message?: string };
    message?: string;
  };
  return (
    apiPayload.error?.message
    || apiPayload.message
    || fallback
  );
}

async function requestSendToCore(
  serverReportId: string,
  idempotencyKey: string,
  pdf: { blob: Blob; filename: string }
) {
  const formData = new FormData();
  formData.set(
    "file",
    pdf.blob,
    pdf.filename || `${serverReportId}.pdf`
  );
  const response = await apiFetch(
    `/field-reports/visits/${serverReportId}/request-send`,
    {
      method: "POST",
      headers: {
        "X-Idempotency-Key": idempotencyKey,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(buildRequestSendErrorMessage(payload));
  }

  const payload = await response.json();
  if (payload?.status !== "LOCKED") {
    throw new Error("השרת לא אישר נעילת דוח לאחר שליחה לליבה");
  }
  return payload;
}

async function applyServerIdsFromSyncResponse(
  record: LocalVisitReportRecord,
  response: SyncVisitReportResponse
): Promise<LocalVisitReportRecord> {
  const serverReportId = String(response.id || response.report?.id || "");
  const serverLines = response.report?.lines ?? [];
  const serverLineByClient = new Map(
    serverLines
      .filter((line) => line.client_line_uuid)
      .map((line) => [line.client_line_uuid!, String(line.id)])
  );

  const lines = record.lines.map((line) => ({
    ...line,
    server_line_id:
      serverLineByClient.get(line.client_line_uuid)
      ?? line.server_line_id
      ?? null,
  }));

  return saveLocalReport({
    client_report_uuid: record.client_report_uuid,
    organization_id: record.organization_id,
    server_report_id: serverReportId || record.server_report_id,
    user_id: record.user_id,
    project_id: record.project_id,
    project_name: record.project_name,
    visit_type: record.visit_type,
    visit_type_label_he: record.visit_type_label_he,
    visit_date: record.visit_date,
    header_fields: record.header_fields,
    lines,
    local_status: record.local_status,
    sync_status: record.sync_status,
    catalog_version: record.catalog_version,
    organization_profile_snapshot: record.organization_profile_snapshot,
    closed_at: record.closed_at,
  });
}

async function upsertVisitReportOnServer(
  record: LocalVisitReportRecord
): Promise<{ record: LocalVisitReportRecord; serverReportId: string }> {
  const body = buildVisitReportSyncBody(record);
  const response = await apiFetch("/field-reports/visits/sync", {
    method: "PUT",
    headers: {
      "X-Idempotency-Key": record.client_report_uuid,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      buildApiErrorMessage(payload, "סנכרון דוח לשרת נכשל")
    );
  }

  const payload = (await response.json()) as SyncVisitReportResponse;
  const updated = await applyServerIdsFromSyncResponse(record, payload);
  const serverReportId = String(
    payload.id || payload.report?.id || updated.server_report_id || ""
  );

  if (!serverReportId) {
    throw new Error("השרת לא החזיר מזהה דוח לאחר סנכרון");
  }

  return { record: updated, serverReportId };
}

async function fetchServerReportStatus(
  serverReportId: string
): Promise<string | null> {
  const response = await apiFetch(`/field-reports/visits/${serverReportId}`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      buildApiErrorMessage(payload, "טעינת סטטוס דוח מהשרת נכשלה")
    );
  }

  const payload = (await response.json()) as { status?: string };
  return payload.status ?? null;
}

async function closeVisitReportOnServerIfNeeded(
  record: LocalVisitReportRecord,
  serverReportId: string
): Promise<void> {
  if (record.local_status !== "LOCAL_CLOSED") {
    return;
  }

  const serverStatus = await fetchServerReportStatus(serverReportId);
  if (serverStatus !== "IN_PROGRESS") {
    return;
  }

  const response = await apiFetch(
    `/field-reports/visits/${serverReportId}/close`,
    { method: "POST" }
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      buildApiErrorMessage(payload, "סגירת דוח בשרת נכשלה")
    );
  }
}

async function runPdfAndRequestSend(
  record: LocalVisitReportRecord,
  serverReportId: string,
  idempotencyKey: string,
  pdfReportKey: string
): Promise<void> {
  const storedPdf = await loadVisitReportPdfLocally(pdfReportKey);
  if (!storedPdf?.blob) {
    throw new Error("PDF לא נמצא במכשיר - יש להפיק מחדש לפני שליחה");
  }

  await requestSendToCore(serverReportId, idempotencyKey, {
    blob: storedPdf.blob,
    filename: storedPdf.filename || `${serverReportId}.pdf`,
  });
}

async function markSyncCompleted(
  record: LocalVisitReportRecord,
  clientReportUuid: string,
  serverReportId: string
): Promise<void> {
  await purgeFieldReportAfterCoreSend({
    organizationId: record.organization_id,
    serverReportId,
  });
}

async function processOfflineSyncQueueRecord(
  queueRecord: SyncQueueRecord,
  progress?: Pick<SyncManagerProgressEvent, "index" | "total">,
  options?: SyncManagerRunOptions
): Promise<SyncManagerItemResult> {
  const { client_report_uuid: clientReportUuid } = queueRecord;
  const idempotencyKey = queueRecord.idempotency_key;
  let currentPhase: PendingSendSyncPhase = queueRecord.sync_phase ?? "queued";

  const emitProgress = (phase: PendingSendSyncPhase) => {
    if (!progress || !options?.onProgress) {
      return;
    }

    options.onProgress({
      index: progress.index,
      total: progress.total,
      clientReportUuid,
      phase,
    });
  };

  const setPhase = async (phase: PendingSendSyncPhase, lastError?: string) => {
    currentPhase = phase;
    emitProgress(phase);
    await updateSyncQueueRecord(clientReportUuid, {
      sync_phase: phase,
      sync_status: lastError ? "failed" : "syncing",
      last_error: lastError ?? null,
    });
  };

  const local = await getLocalReport(clientReportUuid);
  if (!local) {
    throw new Error("דוח מקומי לא נמצא לסנכרון");
  }

  const reportId = queueRecord.server_report_id ?? clientReportUuid;

  try {
    await setPhase("upsert");
    const upserted = await upsertVisitReportOnServer(local);
    let workingRecord = upserted.record;
    const serverReportId = upserted.serverReportId;

    await updateSyncQueueRecord(clientReportUuid, {
      server_report_id: serverReportId,
    });

    await setPhase("photos");
    const photoResult = await syncPendingLinePhotosForReport(
      clientReportUuid
    );
    if (photoResult.failed.length) {
      throw new Error(
        `העלאת ${photoResult.failed.length} תמונות נכשלה`
      );
    }

    if (workingRecord.local_status !== "LOCAL_CLOSED") {
      await updateSyncQueueRecord(clientReportUuid, {
        sync_phase: "photos",
        sync_status: "pending",
        last_error: null,
      });
      return {
        clientReportUuid,
        reportId: serverReportId,
        success: true,
      };
    }

    await setPhase("close");
    await closeVisitReportOnServerIfNeeded(workingRecord, serverReportId);

    const refreshed =
      (await getLocalReport(clientReportUuid)) ?? workingRecord;

    await setPhase("pdf");
    await setPhase("request_send");
    await runPdfAndRequestSend(
      refreshed,
      serverReportId,
      idempotencyKey,
      clientReportUuid
    );

    await markSyncCompleted(refreshed, clientReportUuid, serverReportId);

    return {
      clientReportUuid,
      reportId: serverReportId,
      success: true,
    };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "סנכרון הדוח נכשל";
    await setPhase(currentPhase, message);
    recordFieldReportSyncError({
      organizationId: queueRecord.organization_id,
      clientReportUuid,
      serverReportId: queueRecord.server_report_id ?? null,
      phase: currentPhase,
      message,
    });
    return {
      clientReportUuid,
      reportId,
      success: false,
      error: message,
    };
  }
}

async function processSyncQueueRecord(
  queueRecord: SyncQueueRecord,
  progress?: Pick<SyncManagerProgressEvent, "index" | "total">,
  options?: SyncManagerRunOptions
): Promise<SyncManagerItemResult> {
  const local = await getLocalReport(queueRecord.client_report_uuid);

  if (!local) {
    const pending = syncQueueRecordToPendingSendRequest(queueRecord);
    const legacyResult = await processPendingSendRequest(pending);
    if (!legacyResult.success && legacyResult.error) {
      recordFieldReportSyncError({
        organizationId: queueRecord.organization_id,
        clientReportUuid: queueRecord.client_report_uuid,
        serverReportId: queueRecord.server_report_id ?? pending.reportId,
        phase: queueRecord.sync_phase ?? "queued",
        message: legacyResult.error,
      });
    }
    return {
      clientReportUuid: queueRecord.client_report_uuid,
      reportId: pending.reportId,
      success: legacyResult.success,
      error: legacyResult.error,
    };
  }

  return processOfflineSyncQueueRecord(queueRecord, progress, options);
}

async function runForOrganization(
  organizationId: string,
  userId?: string,
  options?: SyncManagerRunOptions
): Promise<SyncManagerRunResult> {
  if (!organizationId) {
    return { processed: [] };
  }

  const records = userId
    ? await listActiveSyncQueueForUser(organizationId, userId)
    : await listActiveSyncQueueForOrganization(organizationId);

  const processed: SyncManagerItemResult[] = [];
  const total = records.length;

  for (let index = 0; index < records.length; index += 1) {
    const record = records[index];
    const progress = { index: index + 1, total };
    options?.onProgress?.({
      ...progress,
      clientReportUuid: record.client_report_uuid,
      phase: record.sync_phase ?? "queued",
    });
    processed.push(
      await processSyncQueueRecord(record, progress, options)
    );
  }

  return { processed };
}

export const SyncManager = {
  runForOrganization,
  buildVisitReportSyncBody,
};

export {
  buildVisitReportSyncBody,
  processOfflineSyncQueueRecord,
  processSyncQueueRecord,
};
