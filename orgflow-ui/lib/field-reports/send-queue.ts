import type { SyncQueueRecord } from "@/lib/field-reports/db/schema";
import {
  clearSyncQueueForOrganization,
  enqueueSyncQueueRecord,
  listActiveSyncQueueForOrganization,
  removeSyncQueueRecord,
  updateSyncQueueRecord,
  type UpdateSyncQueueRecordInput,
} from "@/lib/field-reports/repositories/sync-queue-repository";
import { resolveReportQueueIdentity } from "@/lib/field-reports/send-queue-resolve";

import {
  ELAYOAI_FIELD_REPORTS_SEND_QUEUE_MIGRATED_PREFIX,
  ELAYOAI_FIELD_REPORTS_SEND_QUEUE_PREFIX,
  LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_MIGRATED_PREFIX,
  LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_PREFIX,
} from "@/lib/elayoai/keys";

const LEGACY_STORAGE_PREFIX = LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_PREFIX;

export type PendingSendSyncPhase =
  | "queued"
  | "upsert"
  | "metadata"
  | "photos"
  | "close"
  | "pdf"
  | "finalize"
  | "request_send";

export type PendingSendRequest = {
  /** מזהה ל-API - `server_report_id` אם קיים, אחרת `client_report_uuid`. */
  reportId: string;
  clientReportUuid: string;
  organizationId: string;
  requestedAt: string;
  idempotencyKey: string;
  syncPhase?: PendingSendSyncPhase;
  lastError?: string;
};

type LegacyPendingSendRequest = {
  reportId: string;
  organizationId: string;
  requestedAt: string;
  idempotencyKey: string;
  syncPhase?: PendingSendSyncPhase;
  lastError?: string;
};

function elayoStorageKey(organizationId: string) {
  return `${ELAYOAI_FIELD_REPORTS_SEND_QUEUE_PREFIX}:${organizationId}`;
}

function legacyStorageKey(organizationId: string) {
  return `${LEGACY_STORAGE_PREFIX}:${organizationId}`;
}

function migrationMarkerKey(organizationId: string) {
  return `${ELAYOAI_FIELD_REPORTS_SEND_QUEUE_MIGRATED_PREFIX}${organizationId}`;
}

function legacyMigrationMarkerKey(organizationId: string) {
  return `${LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_MIGRATED_PREFIX}${organizationId}`;
}

function readLegacyPendingSendRequests(
  organizationId: string
): LegacyPendingSendRequest[] {
  if (typeof window === "undefined" || !organizationId) {
    return [];
  }

  const raw = localStorage.getItem(legacyStorageKey(organizationId));
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as LegacyPendingSendRequest[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function syncQueueRecordToPendingSendRequest(
  record: SyncQueueRecord
): PendingSendRequest {
  return {
    reportId: record.server_report_id ?? record.client_report_uuid,
    clientReportUuid: record.client_report_uuid,
    organizationId: record.organization_id,
    requestedAt: record.requested_at,
    idempotencyKey: record.idempotency_key,
    syncPhase: record.sync_phase,
    lastError: record.last_error ?? undefined,
  };
}

export function pendingSendMatchesReportKey(
  entry: PendingSendRequest,
  reportKey: string
): boolean {
  if (!reportKey) {
    return false;
  }

  return (
    entry.reportId === reportKey
    || entry.clientReportUuid === reportKey
  );
}

async function migrateLegacySendQueueFromLocalStorage(
  organizationId: string
): Promise<void> {
  if (typeof window === "undefined" || !organizationId) {
    return;
  }

  if (
    localStorage.getItem(migrationMarkerKey(organizationId))
    || localStorage.getItem(legacyMigrationMarkerKey(organizationId))
  ) {
    return;
  }

  const legacyEntries = readLegacyPendingSendRequests(organizationId);
  for (const entry of legacyEntries) {
    const identity = await resolveReportQueueIdentity(entry.reportId);
    await enqueueSyncQueueRecord({
      client_report_uuid: identity.clientReportUuid,
      organization_id: organizationId,
      server_report_id: identity.serverReportId,
      idempotency_key: entry.idempotencyKey,
      sync_phase: entry.syncPhase ?? "queued",
      sync_status: "pending",
      last_error: entry.lastError ?? null,
    });
  }

  localStorage.removeItem(legacyStorageKey(organizationId));
  localStorage.removeItem(elayoStorageKey(organizationId));
  localStorage.setItem(migrationMarkerKey(organizationId), "1");
}

export async function loadPendingSendRequests(
  organizationId: string
): Promise<PendingSendRequest[]> {
  if (!organizationId) {
    return [];
  }

  await migrateLegacySendQueueFromLocalStorage(organizationId);
  const records = await listActiveSyncQueueForOrganization(
    organizationId
  );
  return records.map(syncQueueRecordToPendingSendRequest);
}

export async function isReportPendingSendLocally(
  organizationId: string,
  reportKey: string
): Promise<boolean> {
  const pending = await loadPendingSendRequests(organizationId);
  return pending.some((entry) =>
    pendingSendMatchesReportKey(entry, reportKey)
  );
}

export async function enqueuePendingSendRequest(
  organizationId: string,
  reportKey: string
): Promise<PendingSendRequest> {
  const identity = await resolveReportQueueIdentity(reportKey);
  const record = await enqueueSyncQueueRecord({
    client_report_uuid: identity.clientReportUuid,
    organization_id: organizationId,
    server_report_id: identity.serverReportId,
    sync_phase: "queued",
    sync_status: "pending",
    last_error: null,
  });

  return syncQueueRecordToPendingSendRequest(record);
}

export async function updatePendingSendRequest(
  organizationId: string,
  reportKey: string,
  patch: Partial<
    Pick<PendingSendRequest, "syncPhase" | "lastError" | "idempotencyKey">
  >
): Promise<PendingSendRequest | null> {
  const identity = await resolveReportQueueIdentity(reportKey);
  const queuePatch: UpdateSyncQueueRecordInput = {
    server_report_id: identity.serverReportId,
  };
  if (patch.syncPhase !== undefined) {
    queuePatch.sync_phase = patch.syncPhase;
  }
  if (patch.lastError !== undefined) {
    queuePatch.last_error = patch.lastError;
  }
  if (patch.idempotencyKey !== undefined) {
    queuePatch.idempotency_key = patch.idempotencyKey;
  }

  const updated = await updateSyncQueueRecord(
    identity.clientReportUuid,
    queuePatch
  );

  if (!updated) {
    return null;
  }

  if (updated.organization_id !== organizationId) {
    return null;
  }

  return syncQueueRecordToPendingSendRequest(updated);
}

export async function removePendingSendRequest(
  organizationId: string,
  reportKey: string
): Promise<void> {
  const identity = await resolveReportQueueIdentity(reportKey);
  const existing = await listActiveSyncQueueForOrganization(
    organizationId
  );
  const record = existing.find(
    (entry) =>
      entry.client_report_uuid === identity.clientReportUuid
  );

  if (!record) {
    return;
  }

  await removeSyncQueueRecord(record.client_report_uuid);
}

export async function clearAllPendingSendRequests(
  organizationId: string
): Promise<void> {
  if (typeof window === "undefined" || !organizationId) {
    return;
  }

  await clearSyncQueueForOrganization(organizationId);
  localStorage.removeItem(legacyStorageKey(organizationId));
  localStorage.setItem(migrationMarkerKey(organizationId), "1");
}

export function pendingSendPhaseLabelHe(
  phase?: PendingSendSyncPhase
): string {
  switch (phase) {
    case "upsert":
      return "מסנכרן דוח לשרת...";
    case "close":
      return "סוגר דוח בשרת...";
    case "metadata":
      return "מסנכרן פרטי דוח...";
    case "photos":
      return "מעלה תמונות...";
    case "pdf":
      return "מאמת PDF...";
    case "finalize":
      return "מעבד דוח ושולח במייל...";
    case "request_send":
      return "מעבד דוח ושולח במייל...";
    case "queued":
    default:
      return "ממתין לסנכרון";
  }
}
