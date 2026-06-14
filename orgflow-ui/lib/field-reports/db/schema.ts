import type { DBSchema } from "idb";

import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import type { PendingSendSyncPhase } from "@/lib/field-reports/send-queue";
import type { FindingRow } from "@/lib/field-reports/schema/types";
import type { QualityIssue } from "@/lib/quality-issues/types";

import { ELAYOAI_FIELD_REPORT_DB_NAME } from "@/lib/elayoai/keys";

/** שם מסד IndexedDB המאוחד לדוחות שטח (שלב א - Offline-First). */
export const FIELD_REPORT_DB_NAME = ELAYOAI_FIELD_REPORT_DB_NAME;

/** גרסת schema - העלאה ב-`field-report-db.ts` בלבד. */
export const FIELD_REPORT_DB_VERSION = 2;

export const FIELD_REPORT_STORES = {
  catalog: "catalog",
  reports: "reports",
  blobs: "blobs",
  sync_queue: "sync_queue",
  open_issues: "open_issues",
} as const;

export type FieldReportStoreName =
  (typeof FIELD_REPORT_STORES)[keyof typeof FIELD_REPORT_STORES];

/** סטטוס מקומי של דוח במכשיר (§4.1 בתוכנית). */
export type LocalReportStatus =
  | "LOCAL_DRAFT"
  | "LOCAL_IN_PROGRESS"
  | "LOCAL_CLOSED";

/** סטטוס רשומה בתור סנכרון. */
export type LocalSyncStatus = "pending" | "syncing" | "failed" | "done";

/** סוג blob ב-store המאוחד (תמונות שורה / צ'קליסט / PDF). */
export type FieldReportBlobKind = "line_photo" | "checklist_photo" | "pdf";

/**
 * חבילת הכנה לא מקוון - מחליף `offline-store` (FR-006).
 * מפתח: `organization_id`.
 */
export type CatalogRecord = OfflinePrepBundle;

/** snapshot של ליקויים פתוחים לפרויקט - לשימוש offline (roadmap 2.1.7). */
export type ProjectOpenIssuesSnapshot = {
  project_id: string;
  total: number;
  items: QualityIssue[];
};

/**
 * מטמון ליקויים פתוחים לפי ארגון - נשמר ב-IndexedDB בזמן «הכנה לא מקוון».
 * מפתח: `organization_id`.
 */
export type OpenIssuesCacheRecord = {
  organization_id: string;
  cached_at: string;
  expires_at: string;
  projects: Record<string, ProjectOpenIssuesSnapshot>;
};

/** שורת דוח מקומית - `client_line_uuid` ימולא ב-FR-005. */
export type LocalVisitReportLine = FindingRow & {
  client_line_uuid: string;
  server_line_id?: string | null;
};

/**
 * דוח ביקור מקומי - מקור אמת בשטח (§4.3).
 * מפתח: `client_report_uuid`.
 */
export type LocalVisitReportRecord = {
  client_report_uuid: string;
  server_report_id?: string | null;
  organization_id: string;
  user_id?: string | null;
  project_id: string;
  project_name?: string | null;
  visit_type: string;
  visit_type_label_he?: string | null;
  visit_date: string;
  header_fields: Record<string, unknown>;
  lines: LocalVisitReportLine[];
  local_status: LocalReportStatus;
  sync_status: LocalSyncStatus;
  catalog_version?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
};

/** blob בינארי (תמונה / PDF) - לא Base64 בתוך מסמך הדוח. */
export type BlobRecord = {
  id: string;
  kind: FieldReportBlobKind;
  report_id: string;
  /** מפתח משני לשאילתות לפי שורה (`report_id:line_id`). */
  report_line_key?: string | null;
  line_id?: string | null;
  photo_id?: string | null;
  blob: Blob;
  mime_type: string;
  filename?: string | null;
  updated_at: string;
  pending_upload?: boolean;
};

/** רשומת תור שליחה - מרחיב `send-queue.ts` (FR-024). */
export type SyncQueueRecord = {
  client_report_uuid: string;
  organization_id: string;
  user_id?: string | null;
  server_report_id?: string | null;
  requested_at: string;
  idempotency_key: string;
  sync_phase: PendingSendSyncPhase;
  sync_status: LocalSyncStatus;
  last_error?: string | null;
};

export function blobStorageKey(
  reportId: string,
  kind: FieldReportBlobKind,
  options?: {
    lineId?: string;
    photoId?: string;
    checklistItemId?: string;
  }
): string {
  if (kind === "pdf") {
    return `${reportId}:pdf`;
  }

  if (kind === "checklist_photo") {
    const checklistItemId = options?.checklistItemId ?? "";
    const photoId = options?.photoId ?? "primary";
    return `${reportId}:checklist-item:${checklistItemId}:${photoId}`;
  }

  const lineId = options?.lineId ?? "";
  const photoId = options?.photoId ?? "primary";
  return `${reportId}:line:${lineId}:${photoId}`;
}

export function reportChecklistItemIndexKey(
  reportId: string,
  checklistItemId: string
): string {
  return `${reportId}:checklist:${checklistItemId}`;
}

export function reportLineIndexKey(reportId: string, lineId: string): string {
  return `${reportId}:${lineId}`;
}

/** סכמת IndexedDB לספריית `idb` - ממופה ל-object stores. */
export interface FieldReportDBSchema extends DBSchema {
  [FIELD_REPORT_STORES.catalog]: {
    key: string;
    value: CatalogRecord;
  };
  [FIELD_REPORT_STORES.reports]: {
    key: string;
    value: LocalVisitReportRecord;
    indexes: {
      "by-organization": string;
      "by-server-id": string;
    };
  };
  [FIELD_REPORT_STORES.blobs]: {
    key: string;
    value: BlobRecord;
    indexes: {
      "by-report": string;
      "by-report-line": string;
    };
  };
  [FIELD_REPORT_STORES.sync_queue]: {
    key: string;
    value: SyncQueueRecord;
    indexes: {
      "by-organization": string;
    };
  };
  [FIELD_REPORT_STORES.open_issues]: {
    key: string;
    value: OpenIssuesCacheRecord;
  };
}
