import type { CatalogPayload } from "@/lib/field-reports/catalog-offline";
import { filterCatalogForVisitType } from "@/lib/field-reports/catalog-offline";
import {
  FIELD_REPORT_STORES,
  type CatalogRecord,
} from "@/lib/field-reports/db/schema";
import { getFieldReportDatabase } from "@/lib/field-reports/db/field-report-db";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import {
  clearLegacyOfflinePrepBundle,
  readLegacyOfflinePrepBundle,
} from "@/lib/field-reports/offline-prep-local-storage";

export type { CatalogPayload };

/**
 * שומר חבילת הכנה לא מקוון ב-IndexedDB (`catalog` store).
 * מחשב `prepared_at` / `expires_at` כמו `saveOfflinePrepBundle`.
 */
export async function saveFromOfflinePrep(
  organizationId: string,
  bundle: Omit<CatalogRecord, "prepared_at" | "expires_at" | "organization_id">
): Promise<CatalogRecord> {
  const preparedAt = new Date();
  const expiresAt = new Date(preparedAt);
  expiresAt.setDate(
    expiresAt.getDate() + (bundle.offline_max_days || 7)
  );

  const record: CatalogRecord = {
    ...bundle,
    organization_id: organizationId,
    prepared_at: preparedAt.toISOString(),
    expires_at: expiresAt.toISOString(),
  };

  const database = await getFieldReportDatabase();
  await database.put(FIELD_REPORT_STORES.catalog, record);
  return record;
}

export async function loadCatalogBundle(
  organizationId: string
): Promise<CatalogRecord | null> {
  if (!organizationId) {
    return null;
  }

  const database = await getFieldReportDatabase();
  const record = await database.get(
    FIELD_REPORT_STORES.catalog,
    organizationId
  );
  return record ?? null;
}

/** האם חבילת ההכנה פגה תוקף (מקביל ל-`isOfflinePrepValid` - הפוך). */
export function isExpired(bundle: CatalogRecord | null): boolean {
  if (!bundle?.expires_at) {
    return true;
  }

  return new Date(bundle.expires_at).getTime() <= Date.now();
}

/**
 * קטלוג מסונן לפי סוג ביקור - מ-IndexedDB בלבד.
 * מחזיר `null` אם אין חבילה, פג תוקף, או אין קטלוג.
 */
export async function getCatalogForVisitType(
  organizationId: string,
  visitType: string
): Promise<CatalogPayload | null> {
  const bundle = await loadCatalogBundle(organizationId);
  if (!bundle || isExpired(bundle)) {
    return null;
  }

  return filterCatalogForVisitType(bundle, visitType);
}

export async function clearCatalogBundle(
  organizationId: string
): Promise<void> {
  if (!organizationId) {
    return;
  }

  const database = await getFieldReportDatabase();
  await database.delete(FIELD_REPORT_STORES.catalog, organizationId);
}

/** שומר חבילה קיימת ללא חישוב מחדש של תאריכים (מיגרציה). */
export async function putCatalogRecord(
  record: CatalogRecord
): Promise<CatalogRecord> {
  const database = await getFieldReportDatabase();
  await database.put(FIELD_REPORT_STORES.catalog, record);
  return record;
}

/**
 * מעביר חבילה מ-localStorage ל-IndexedDB (חד-פעמי לכל ארגון).
 * אם כבר קיימת ב-IndexedDB - מוחק legacy מ-localStorage בלבד.
 */
export async function migrateOfflinePrepFromLocalStorage(
  organizationId: string
): Promise<CatalogRecord | null> {
  if (!organizationId) {
    return null;
  }

  const existing = await loadCatalogBundle(organizationId);
  if (existing) {
    clearLegacyOfflinePrepBundle(organizationId);
    return existing;
  }

  const legacy = readLegacyOfflinePrepBundle(organizationId);
  if (!legacy) {
    return null;
  }

  const record: CatalogRecord = {
    ...legacy,
    organization_id: organizationId,
  };
  await putCatalogRecord(record);
  clearLegacyOfflinePrepBundle(organizationId);
  return record;
}

/** טוען מ-IndexedDB; אם חסר - מנסה מיגרציה מ-localStorage. */
export async function resolveOfflinePrepBundle(
  organizationId: string
): Promise<CatalogRecord | null> {
  const fromIndexedDb = await loadCatalogBundle(organizationId);
  if (fromIndexedDb) {
    return fromIndexedDb;
  }

  return migrateOfflinePrepFromLocalStorage(organizationId);
}
